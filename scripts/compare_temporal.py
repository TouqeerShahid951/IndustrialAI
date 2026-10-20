"""Compare raw and causal confirmed boxes from saved evaluation runs."""
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from temporal import confirm, confirm_timed


def compare(run, policy="legacy"):
    import cv2
    run = Path(run)
    with (run / 'detections.csv').open() as f:
        detections = list(csv.DictReader(f))
    if policy not in ('legacy','timed'):
        raise ValueError('policy must be legacy or timed')
    observations = []
    if (run/'frames.csv').exists():
        with (run/'frames.csv').open() as handle:
            observations = list(csv.DictReader(handle))
    results = []
    for summary in json.loads((run / 'summary.json').read_text()):
        frames = [[] for _ in range(summary['frames'])]
        for row in detections:
            if row['source'] == summary['source'] and row['model'] == summary['model']:
                index = int(row['frame']) // summary['stride']
                frames[index].append(dict(**{'class': row['class']}, bbox=[float(row[k]) for k in ('x1', 'y1', 'x2', 'y2')]))
        cap = cv2.VideoCapture(summary['source'])
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        if fps <= 0:
            raise ValueError('Temporal comparison requires a video with valid FPS')
        observed = [r for r in observations if r['source']==summary['source'] and r['model']==summary['model']]
        if observed and len(observed)!=len(frames):
            raise ValueError('Observation count does not match the summary')
        times = [float(r['source_seconds']) for r in observed] if observed else [i*summary['stride']/fps for i in range(len(frames))]
        filtered = confirm_timed(frames,times) if policy=='timed' else confirm(frames)
        first_raw = next((times[i] for i, boxes in enumerate(frames) if boxes), None)
        first_confirmed = next((times[i] for i, boxes in enumerate(filtered) if boxes), None)
        results.append(dict(policy=policy, timestamp_basis='recorded' if observed else 'nominal_legacy', clip=Path(summary['source']).name, model=summary['model'],
                            frames=len(frames), raw_frames=sum(bool(x) for x in frames),
                            confirmed_frames=sum(bool(x) for x in filtered),
                            first_raw_seconds=first_raw, first_confirmed_seconds=first_confirmed,
                            confirmation_delay_seconds=None if first_confirmed is None else first_confirmed - first_raw,
                            run=str(run)))
    return results


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs',nargs='+')
    parser.add_argument('--policy',choices=('legacy','timed'),default='legacy')
    args=parser.parse_args()
    print(json.dumps([row for run in args.runs for row in compare(run,args.policy)],indent=2))
