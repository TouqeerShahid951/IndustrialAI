"""Sequential, hash-pinned inference; original frames and timestamps only."""
import hashlib
import json
import time
from pathlib import Path
import cv2
from temporal import confirm_timed
from scripts.benchmark_events import union_intervals
from .media import Cancelled, capacity

REGISTRY = json.loads(Path(__file__).with_name('models.json').read_text())
PROFILE = {'version':'development-1','confidence':.25,'imgsz':640,'stride':1,'min_hits':3,'min_span_seconds':1.0,
           'window_seconds':2.0,'overlap':.1,'merge_gap':2.0,'min_head_px':12,'min_person_px':80,
           'keypoint_confidence':.5,'near_height':.15,'away_height':.25,'object_height':.20,
           'gesture_seconds':8,'track_gap_seconds':1,'zone_dwell_seconds':1,'zone_exit_seconds':2}


def checkpoint(alias, root):
    entry=REGISTRY[alias]
    if alias=='pose':
        return Path(root)/'models'/entry['filename']
    return Path.home()/'.cache/huggingface/hub'/('models--'+entry['repository'].replace('/','--'))/'snapshots'/entry['revision']/'best.pt'


def load_model(alias, root=None):
    from ultralytics import YOLO
    entry=REGISTRY[alias]
    path=checkpoint(alias,root or 'var/mvp')
    if not path.is_file():
        raise RuntimeError(f'{alias} checkpoint is missing. Run the local model setup command.')
    with path.open('rb') as handle:
        actual=hashlib.file_digest(handle,'sha256').hexdigest()
    if actual!=entry['sha256']:
        raise RuntimeError(f'{alias} checkpoint hash mismatch. Analysis stopped without substituting a model.')
    model=YOLO(str(path))
    if set(model.names.values()) != set(entry['classes']):
        raise RuntimeError(f'{alias} classes do not match the pinned model registry.')
    return model,entry


def run_detection_pass(source, destination, alias, device, on_progress, should_cancel, root=None):
    model,entry=load_model(alias,root)
    capture=cv2.VideoCapture(str(source))
    expected=int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    count,started,previous=0,time.monotonic(),None
    try:
        with Path(destination).open('w') as output:
            while True:
                if should_cancel():
                    raise Cancelled()
                ok,image=capture.read()
                if not ok:
                    break
                stamp=capture.get(cv2.CAP_PROP_POS_MSEC)/1000
                if previous is not None and stamp<=previous:
                    raise ValueError('Source timestamps changed after preparation.')
                previous=stamp
                if alias=='pose':
                    prediction=model.track(image,device=device,conf=.25,imgsz=640,tracker='bytetrack.yaml',persist=True,verbose=False)[0]
                else:
                    prediction=model.predict(image,device=device,conf=.25,imgsz=640,verbose=False)[0]
                boxes=[]
                for index,box in enumerate(prediction.boxes.cpu()):
                    raw=prediction.names[int(box.cls.item())]
                    item={'class':raw,'canonical':entry['classes'][raw],'confidence':float(box.conf.item()),'bbox':box.xyxy[0].tolist()}
                    if alias=='pose':
                        item['track']=int(box.id.item()) if box.id is not None else None
                        item['keypoints']=prediction.keypoints.data[index].cpu().tolist() if prediction.keypoints is not None else []
                    boxes.append(item)
                output.write(json.dumps({'frame':count,'time':stamp,'model':alias,'boxes':boxes},allow_nan=False)+'\n')
                count+=1
                if count%10==0 or count==expected:
                    if root:
                        capacity(root)
                    on_progress(alias,count,expected)
        if count!=expected:
            raise RuntimeError('Inference did not cover every source frame.')
        return {'frames':count,'expected':expected,'elapsed_seconds':time.monotonic()-started,'sha256':entry['sha256']}
    finally:
        capture.release()
        del model


def fire_incidents(rows, selected, duration):
    times=[r['time'] for r in rows]
    boxes=[[b for b in r['boxes'] if b['canonical'] in selected] for r in rows]
    votes=confirm_timed(boxes,times)
    events=[]
    step=duration/max(1,len(rows))
    for kind in ('fire','smoke'):
        if kind not in selected:
            continue
        raw=[(r['time'],min(duration,r['time']+step)) for r in rows if any(b['canonical']==kind for b in r['boxes'])]
        for a,b in union_intervals(raw,gap=2):
            temporal=any(a<=t<=b and any(x['canonical']==kind for x in confirmed) for t,confirmed in zip(times,votes))
            first=next(x for r in rows if a<=r['time']<=b for x in r['boxes'] if x['canonical']==kind)
            events.append({'kind':kind,'start':a,'end':b,'evidence':{'level':'temporal' if temporal else 'raw','label':kind+' candidate','bbox':first['bbox'],'rule_version':PROFILE['version']}})
    return events


def analyze(store, job, progress, cancelled):
    upload=store.upload(job['upload_id'])
    config=job['config']
    selected=config['capabilities']
    directory=store.root/'analysis'/job['id']
    directory.mkdir(parents=True,exist_ok=True)
    passes=[]
    if any(k in selected for k in ('no_helmet','smoking','intrusion')):
        passes.append('pose')
    if any(k in selected for k in ('fire','smoke')):
        passes.append('fire_smoke')
    if 'no_helmet' in selected:
        passes.append('helmet')
    if 'smoking' in selected:
        passes.append('cigarette')
    result={'profile':PROFILE,'capabilities':{k:{'status':'disabled' if k not in selected else 'pending','assessability':'not assessed'} for k in ('fire','smoke','smoking','no_helmet','intrusion')},'passes':{},'raw_artifacts':{}}
    rows={}
    for alias in passes:
        affected={'pose':['no_helmet','smoking','intrusion'],'fire_smoke':['fire','smoke'],'helmet':['no_helmet'],'cigarette':['smoking']}[alias]
        target=directory/(alias+'.jsonl')
        try:
            result['passes'][alias]=run_detection_pass(store.root/upload['path'],target,alias,config['device'],progress,cancelled,store.root)
            result['raw_artifacts'][alias]=store.add_artifact(upload['id'],'observations',target,'application/x-ndjson',alias+'.jsonl',job['id'])
            rows[alias]=[json.loads(line) for line in target.read_text().splitlines()]
            for kind in affected:
                if kind in selected:
                    result['capabilities'][kind]={'status':'completed','assessability':'scene/person visibility requires review' if kind in ('fire','smoke') else 'provisional rules; inspect evidence'}
        except Cancelled:
            store.update_job(job['id'],result=result)
            raise
        except Exception as exc:
            for kind in affected:
                if kind in selected:
                    result['capabilities'][kind]={'status':'failed','assessability':'unassessable','error':str(exc)[:250]}
        store.update_job(job['id'],result=result)
    events=fire_incidents(rows.get('fire_smoke',[]),selected,upload['metadata']['duration'])
    if 'pose' in rows:
        from .rules import person_incidents
        more,assessment=person_incidents(rows,config['zones'],selected,upload['metadata'])
        events+=more
        result['assessment']=assessment
    if 'pose' not in rows:
        for kind in ('smoking','no_helmet','intrusion'):
            if kind in selected:
                result['capabilities'][kind]={'status':'failed','assessability':'unassessable','error':'Person tracking did not complete'}
    if cancelled():
        raise Cancelled()
    for event in events:
        store.add_incident(job['id'],event['kind'],event['start'],event['end'],event['evidence'])
    statuses=[result['capabilities'][k]['status'] for k in selected]
    result['incident_count']=len(events)
    return ('completed' if all(s=='completed' for s in statuses) else 'partial' if any(s=='completed' for s in statuses) else 'failed'),result
