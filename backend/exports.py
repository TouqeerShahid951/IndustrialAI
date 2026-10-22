"""Worker-owned evidence exports, preserving source times and the review audit."""
import csv
import json
import shutil
from pathlib import Path
import cv2
from .media import capacity, convert, Cancelled


def cell(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r')):
        return "'"+value
    return value


def export_job(store,job,progress,cancelled):
    config=job['config']
    source_job=store.job(config['source_job'])
    upload=store.upload(job['upload_id'])
    incidents=store.incidents(source_job['id'])
    if config.get('incident_id'):
        incidents=[i for i in incidents if i['id']==config['incident_id']]
    if config['format']=='mp4' and len(incidents)!=1:
        raise ValueError('Select one existing incident for an evidence clip.')
    for incident in incidents:
        incident['reviews']=store.query('SELECT decision,note,version,created FROM reviews WHERE incident_id=? ORDER BY version',(incident['id'],))
    payload={'source':{k:upload[k] for k in ('id','name','sha256')},'source_duration':upload['metadata']['duration'],
             'job':source_job,'incidents':incidents,'timestamp_basis':'original source seconds','model_quality':'development models; review required'}
    directory=store.root/'exports'/job['id']
    directory.mkdir(parents=True,exist_ok=True)
    suffix=config['format']
    output=directory/('evidence.'+suffix)
    try:
        capacity(store.root)
        if cancelled():
            raise Cancelled()
        if suffix=='json':
            output.write_text(json.dumps(payload,indent=2,allow_nan=False))
        elif suffix=='csv':
            fields=['source','source_sha256','job','kind','origin','source_start','source_end','evidence_level','decision','note','review_version','reviewed_at','configuration','coverage']
            with output.open('w',newline='') as handle:
                writer=csv.DictWriter(handle,fieldnames=fields)
                writer.writeheader()
                for i in incidents:
                    if cancelled():
                        raise Cancelled()
                    row=dict(source=upload['name'],source_sha256=upload['sha256'],job=source_job['id'],kind=i['kind'],origin=i['origin'],source_start=i['start'],source_end=i['end'],evidence_level=i['evidence'].get('level'),decision=i['decision'] or 'unreviewed',note=i['note'] or '',review_version=i['version'] or 0,reviewed_at=i['reviewed_at'] or '',configuration=json.dumps(source_job['config']),coverage=json.dumps(source_job['result'].get('passes',{})))
                    writer.writerow({k:cell(v) for k,v in row.items()})
        else:
            incident=incidents[0]
            start=max(0,incident['start']-2)
            end=min(upload['metadata']['duration'],incident['end']+2)
            intermediate=directory/'intermediate.mp4'
            cap=cv2.VideoCapture(str(store.root/upload['path']))
            meta=upload['metadata']
            writer=cv2.VideoWriter(str(intermediate),cv2.VideoWriter_fourcc(*'mp4v'),meta['fps'],(meta['width'],meta['height']))
            mapping=[]
            try:
                if not writer.isOpened():
                    raise RuntimeError('Evidence writer unavailable')
                while True:
                    if cancelled():
                        raise Cancelled()
                    ok,frame=cap.read()
                    if not ok:
                        break
                    t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                    if t>end:
                        break
                    if t>=start:
                        mapping.append([t,len(mapping)/meta['fps']])
                        writer.write(frame)
                        if len(mapping)%30==0:
                            capacity(store.root)
                            progress('Preparing evidence clip',len(mapping),max(1,int((end-start)*meta['fps'])))
            finally:
                cap.release();writer.release()
            if not mapping:
                raise ValueError('No decodable frames in the chosen interval')
            convert(intermediate,output,cancelled,store.root)
            check=cv2.VideoCapture(str(output))
            converted=[]
            try:
                while True:
                    ok,_=check.read()
                    if not ok: break
                    converted.append(check.get(cv2.CAP_PROP_POS_MSEC)/1000)
            finally:
                check.release()
            if len(converted)!=len(mapping):
                raise ValueError('Evidence conversion changed frame count')
            intermediate.unlink()
            payload['clip']={'source_start':mapping[0][0],'source_end':mapping[-1][0],'frame_map':[[a[0],b] for a,b in zip(mapping,converted)]}
            manifest=directory/'manifest.json'
            manifest.write_text(json.dumps(payload,indent=2,allow_nan=False))
            manifest_id=store.add_artifact(upload['id'],'export_manifest',manifest,'application/json','evidence-manifest.json',job['id'])
        capacity(store.root)
        if cancelled():
            raise Cancelled()
        aid=store.add_artifact(upload['id'],'export',output,{'json':'application/json','csv':'text/csv','mp4':'video/mp4'}[suffix],output.name,job['id'])
        progress('Evidence ready' if suffix=='mp4' else 'Report ready',len(mapping) if suffix=='mp4' else 1,len(mapping) if suffix=='mp4' else 1)
        return {'artifact_id':aid,**({'manifest_id':manifest_id} if suffix=='mp4' else {})}
    except BaseException:
        shutil.rmtree(directory,ignore_errors=True)
        raise
