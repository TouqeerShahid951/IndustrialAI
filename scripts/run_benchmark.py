"""Score reviewed local clips against completed, hash-pinned inference runs."""
import argparse
import csv
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.benchmark_data import KINDS, load_manifest, validate_manifest, check_test_lock, file_sha256, number
from scripts.benchmark_events import score_events, merge_candidates, union_intervals, subtract_intervals, seconds, percentiles
from scripts.audit_metrics import score_heads
from temporal import confirm, confirm_timed

LABELS = {'fire':'fire', 'smoke':'smoke', 'Hardhat':'helmet', 'NO-Hardhat':'no_helmet',
          'helmet':'helmet', 'no_helmet':'no_helmet', 'cigarette':'cigarette', 'person':'person'}
MODELS = {'fire':'fire_smoke', 'smoke':'fire_smoke', 'no_helmet':'helmet'}
POLICIES = ('raw', 'legacy', 'fixed_2hz', 'timed')
PARAMETERS = dict(legacy=dict(hits=3,window=5,overlap=.1),
                  timed=dict(min_hits=3,min_span_seconds=1.0,window_seconds=2.0,overlap=.1),
                  fixed_hz=2,merge_gap_seconds=2,maximum_coverage_gap_seconds=2,head_iou_thresholds=[.5,.3])


def read_run(path):
    path = Path(path)
    metadata = json.loads((path/'metadata.json').read_text())
    if metadata.get('status') != 'complete':
        raise ValueError('inference run is not complete')
    if not metadata.get('code_hashes') or not metadata.get('checkpoints'):
        raise ValueError('run requires model and code provenance')
    for name in ('summary.json','detections.csv','frames.csv'):
        if metadata.get('artifacts',{}).get(name) != file_sha256(path/name):
            raise ValueError(f'run artifact hash mismatch: {name}')
    for model in metadata['checkpoints'].values():
        if file_sha256(model['path']) != model['sha256']:
            raise ValueError('checkpoint hash mismatch')
    with (path/'detections.csv').open() as handle:
        boxes = list(csv.DictReader(handle))
    with (path/'frames.csv').open() as handle:
        observations = list(csv.DictReader(handle))
    return metadata, json.loads((path/'summary.json').read_text()), boxes, observations


def recording(clip, summary, rows, observations):
    source = Path(clip['local_path']).resolve()
    matches = lambda r: Path(r['source']).resolve()==source and r['model']==summary['model']
    obs = [r for r in observations if matches(r)]
    if len(obs) != summary['frames'] or summary['stride'] < 1 or not number(summary.get('source_fps')) or summary['source_fps'] <= 0:
        raise ValueError('observation count or sampling metadata mismatch')
    times = [float(r['source_seconds']) for r in obs]
    if any(not number(t) or not 0 <= t < clip['duration_seconds'] for t in times) or any(b<=a for a,b in zip(times,times[1:])):
        raise ValueError('invalid observation timestamps')
    indices = [int(r['frame']) for r in obs]
    if any(i<0 for i in indices) or any(b<=a for a,b in zip(indices,indices[1:])):
        raise ValueError('duplicate/invalid observed frames')
    frames = [[] for _ in obs]
    lookup = {frame:i for i,frame in enumerate(indices)}
    for row in rows:
        if not matches(row):
            continue
        index = lookup.get(int(row['frame']))
        if index is None or abs(float(row['source_seconds'])-times[index])>1e-6 or obs[index]['status']!='ok':
            raise ValueError('detection has no successful matching observation')
        box = [float(row[k]) for k in ('x1','y1','x2','y2')]
        confidence = float(row['confidence'])
        if (not all(number(v) for v in box) or not 0<=box[0]<box[2] or not 0<=box[1]<box[3]
                or not number(confidence) or not 0<=confidence<=1 or row['class'] not in LABELS):
            raise ValueError('invalid detection geometry, confidence or class')
        frames[index].append({'class':LABELS[row['class']], 'bbox':box, 'confidence':confidence})
    cadence = min(PARAMETERS['maximum_coverage_gap_seconds'], summary['stride']/summary['source_fps'])
    spans, latencies = [], []
    for index, (t,row) in enumerate(zip(times,obs)):
        if row['status'] not in ('ok','error') or row['timestamp_basis'] not in ('container','nominal'):
            raise ValueError('invalid observation status or timestamp basis')
        latency = float(row['predict_seconds'])
        if not number(latency) or latency < 0:
            raise ValueError('invalid processing latency')
        next_t = times[index+1] if index+1<len(times) else min(t+cadence,clip['duration_seconds'])
        end = next_t if next_t-t<=PARAMETERS['maximum_coverage_gap_seconds'] else min(t+cadence,clip['duration_seconds'])
        if row['status']=='ok':
            spans.append([t,end]);latencies.append(latency)
        else:
            frames[index] = []
            spans.append(None)
    filtered = {'raw':frames,'legacy':confirm(frames,**PARAMETERS['legacy']),'timed':confirm_timed(frames,times,**PARAMETERS['timed'])}
    selected, bucket = [], None
    for index,t in enumerate(times):
        if math.floor(t*PARAMETERS['fixed_hz']) != bucket:
            selected.append(index);bucket=math.floor(t*PARAMETERS['fixed_hz'])
    fixed = confirm([frames[i] for i in selected],**PARAMETERS['legacy'])
    filtered['fixed_2hz'] = [[] for _ in frames]
    for index,boxes in zip(selected,fixed):
        filtered['fixed_2hz'][index]=boxes
    events = {}
    for policy in POLICIES:
        candidates = []
        for boxes,span in zip(filtered[policy],spans):
            if span:
                for kind in {b['class'] for b in boxes} & KINDS:
                    candidates.append(dict(clip_id=clip['clip_id'],kind=kind,start_seconds=span[0],end_seconds=span[1]))
        events[policy] = merge_candidates(candidates,PARAMETERS['merge_gap_seconds'])
    return dict(frames=frames,times=times,events=events,coverage=union_intervals([s for s in spans if s]),
                latencies=latencies,timestamp_bases=sorted({r['timestamp_basis'] for r in obs}))


def aggregate(entries):
    reviewed = sum(e['reviewed_seconds'] for e in entries)
    coverage = sum(e['coverage_seconds'] for e in entries)
    result = dict(status='scored' if coverage else 'unmonitored', reviewed_seconds=reviewed,
                  coverage_seconds=coverage, monitoring_coverage=coverage/reviewed if reviewed else None,
                  negative_seconds=sum(e['negative_seconds'] for e in entries),
                  prediction_latency_seconds=percentiles([x for e in entries for x in e['latencies']]),
                  policies={})
    for policy in POLICIES:
        result['policies'][policy] = score_events([x for e in entries for x in e['expected']],
            [x for e in entries for x in e['predicted'][policy]],result['negative_seconds'],
            excluded_intervals=[x for e in entries for x in e['excluded']])
    return result


def build_report(manifest, runs, split='development', test_lock=None):
    clips = load_manifest(manifest)
    errors = validate_manifest(clips)
    if errors:
        raise ValueError('; '.join(errors))
    if split not in ('development','validation','locked_test'):
        raise ValueError('invalid benchmark split')
    if split=='locked_test':
        if test_lock is None or check_test_lock(clips,test_lock):
            raise ValueError('locked_test requires a matching frozen test lock')
    clips = [c for c in clips if c['split']==split]
    if not clips:
        raise ValueError(f'no {split} clips registered')
    loaded = [read_run(path) for path in runs]
    entries, head_scores = [], []
    for clip in clips:
        labels = json.loads(Path(clip['annotation_path']).read_text())
        recordings = {}
        for metadata,summaries,boxes,observations in loaded:
            for summary in summaries:
                if Path(summary['source']).resolve() != Path(clip['local_path']).resolve():
                    continue
                model = summary['model']
                if model in recordings:
                    raise ValueError('duplicate run for the same clip/model; compare variants separately')
                if metadata['source_hashes'].get(str(Path(clip['local_path']).resolve())) != clip['source_sha256']:
                    raise ValueError('inference source hash mismatch')
                recordings[model] = recording(clip,summary,boxes,observations)
        for kind, reviewed in labels.get('reviewed_intervals',{}).items():
            rec = recordings.get(MODELS.get(kind),dict(coverage=[],latencies=[],events={p:[] for p in POLICIES}))
            expected = [dict(e,clip_id=clip['clip_id']) for e in labels.get('events',[]) if e['kind']==kind]
            exclusions = [dict(e,clip_id=clip['clip_id'],kind=kind) for e in labels.get('excluded_intervals',[]) if e.get('kind',kind)==kind]
            exclusions += [dict(e,clip_id=clip['clip_id'],reason='ambiguous') for e in expected if e.get('review_status')=='ambiguous']
            ambiguous = [[e['start_seconds'],e['end_seconds']] for e in exclusions]
            observable = subtract_intervals(reviewed,ambiguous)
            missing = subtract_intervals(observable,rec['coverage'])
            # Outside reviewed windows is unknown, not a negative example.
            outside = subtract_intervals([[0,clip['duration_seconds']]],reviewed)
            exclusions += [dict(clip_id=clip['clip_id'],kind=kind,start_seconds=a,end_seconds=b,reason='unmonitored') for a,b in [*missing,*outside]]
            covered = subtract_intervals(observable,missing)
            positives = [[e['start_seconds'],e['end_seconds']] for e in expected if e.get('review_status')=='reviewed']
            negative = subtract_intervals(covered,positives)
            entries.append(dict(clip_id=clip['clip_id'],kind=kind,camera_id=clip['camera_id'],conditions=clip['conditions'],
                                reviewed_seconds=seconds(observable),coverage_seconds=seconds(covered),negative_seconds=seconds(negative),
                                expected=expected,predicted={p:[e for e in rec['events'][p] if e['kind']==kind] for p in POLICIES},
                                excluded=exclusions,latencies=rec['latencies']))
        if 'helmet' in recordings:
            rec = recordings['helmet']
            for category,threshold in ((c,t) for c in ('helmet','no_helmet') for t in PARAMETERS['head_iou_thresholds']):
                tp=fp=fn=frames_scored=0
                for frame in labels.get('frames',[]):
                    if frame['review_status']!='reviewed':
                        continue
                    index = next((i for i,t in enumerate(rec['times']) if abs(t-frame['time_seconds'])<1e-3),None)
                    if index is None:
                        continue
                    truth = [{'class':b['class'],'bbox':b['bbox_xyxy']} for b in frame['objects'] if b['class']==category]
                    predictions = [b for b in rec['frames'][index] if b['class']==category]
                    a,b,c=score_heads(truth,predictions,threshold);tp+=a;fp+=b;fn+=c;frames_scored+=1
                head_scores.append(dict(clip_id=clip['clip_id'],category=category,iou_threshold=threshold,annotated_frames_scored=frames_scored,TP=tp,FP=fp,FN=fn))
    per_capability={kind:aggregate([e for e in entries if e['kind']==kind]) if any(e['kind']==kind for e in entries)
                    else {'status':'not_annotated'} for kind in sorted(KINDS)}
    groups={}
    for field in ('camera_id','conditions'):
        keys={key for e in entries for key in (e[field] if field=='conditions' else [e[field]])}
        groups[field]={key:{kind:aggregate([e for e in entries if e['kind']==kind and (key in e[field] if field=='conditions' else key==e[field])])
                          for kind in sorted({e['kind'] for e in entries})} for key in sorted(keys)}
    scoring_root = Path(__file__).resolve().parents[1]
    provenance = dict(annotation_sha256={c['clip_id']:file_sha256(c['annotation_path']) for c in clips},
                      parameters=PARAMETERS,
                      code_hashes={name:file_sha256(scoring_root/name) for name in
                                   ('scripts/run_benchmark.py','scripts/benchmark_data.py','scripts/benchmark_events.py',
                                    'scripts/audit_metrics.py','temporal.py')})
    return dict(manifest_sha256=file_sha256(manifest),scoring_provenance=provenance,split=split,gate_passed=False,
                gate_status='Metrics only; no automatic model promotion or production qualification',
                limitations=['Public development clips and single-reviewer labels are not independent validation',
                             'Insufficient independent footage, negative exposure and accepted operating policy',
                             'Latency measures model prediction/box transfer, not live capture-to-alert latency',
                             'Cigarette boxes are not confirmed smoking events'],
                per_capability=per_capability,head_objects=head_scores,groups=groups,clips=entries,
                run_provenance=[dict(path=str(Path(path).resolve()),metadata=data[0]) for path,data in zip(runs,loaded)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    sources=parser.add_mutually_exclusive_group(required=True)
    sources.add_argument('--runs',nargs='+',type=Path)
    sources.add_argument('--runs-json',type=Path,help='JSON list of run directories')
    parser.add_argument('--split',default='development',choices=('development','validation','locked_test'))
    parser.add_argument('--test-lock',type=Path)
    parser.add_argument('--output',type=Path,default=Path('reports/benchmark-report.json'))
    args=parser.parse_args()
    try:
        runs = json.loads(args.runs_json.read_text()) if args.runs_json else args.runs
        if not isinstance(runs,list) or not runs or not all(isinstance(p,(str,Path)) for p in runs):
            raise ValueError('Provide a nonempty list of run paths')
        report=build_report(args.manifest,runs,args.split,args.test_lock)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(f'Report: {args.output.resolve()}\nGate passed: {report["gate_passed"]}')
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(1,f'Benchmark rejected: {exc}\n')


if __name__=='__main__':
    raise SystemExit(main())
