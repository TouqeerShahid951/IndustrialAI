"""Compare the existing 3-of-5 spatial rule at fixed sample rates on full-frame logs."""
import csv
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from temporal import confirm, confirm_timed


def audit(paths=None):
    import cv2
    paths = paths or [json.loads(Path('reports/cctv-only-runs.json').read_text())['fire_smoke'],
             'outputs/run-1gteobj4', 'outputs/run-y_2p0nue']
    inputs = []
    for folder in paths:
        run = Path(folder)
        with (run/'detections.csv').open() as handle:
            rows = list(csv.DictReader(handle))
        observations = []
        if (run/'frames.csv').exists():
            with (run/'frames.csv').open() as handle:
                observations = list(csv.DictReader(handle))
        inputs.extend((summary, rows, observations) for summary in json.loads((run / 'summary.json').read_text()))
    results = []
    for summary, rows, observations in inputs:
        cap = cv2.VideoCapture(summary['source'])
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        effective_fps = fps / summary['stride']
        frames = [[] for _ in range(summary['frames'])]
        for row in rows:
            if row['source'] == summary['source'] and row['model'] == summary['model']:
                frames[int(row['frame']) // summary['stride']].append({'class': row['class'], 'bbox': [float(row[k]) for k in ('x1', 'y1', 'x2', 'y2')]})
        observed = [r for r in observations if r['source']==summary['source'] and r['model']==summary['model']]
        if observed and len(observed)!=len(frames):
            raise ValueError('Observation count mismatch')
        times = [float(r['source_seconds']) for r in observed] if observed else [i/effective_fps for i in range(len(frames))]
        timed = confirm_timed(frames,times)
        for category in ('fire','smoke'):
            active = [any(b['class']==category for b in boxes) for boxes in timed]
            results.append(dict(clip=Path(summary['source']).name, model=summary['model'], category=category, requested_hz='timed',
                                timestamp_basis='recorded' if observed else 'nominal_legacy',
                                actual_hz=effective_fps, sampled_frames=len(frames), minimum_three_hit_span_seconds=1.0,
                                confirmed=any(active), confirmed_frames=sum(active),
                                first_confirmed_seconds=next((times[i] for i,yes in enumerate(active) if yes),None)))
        for requested_rate in (None, 5, 2):
            rate = effective_fps if requested_rate is None else min(effective_fps, requested_rate)
            indices = [round(i * effective_fps / rate) for i in range(math.ceil(len(frames) * rate / effective_fps))]
            indices = [i for i in indices if i < len(frames)]
            assert len(set(indices)) == len(indices)
            sampled = [frames[i] for i in indices]
            filtered = confirm(sampled)
            for category in ('fire', 'smoke'):
                active = [any(box['class'] == category for box in boxes) for boxes in filtered]
                results.append(dict(clip=Path(summary['source']).name, model=summary['model'], category=category,
                                    requested_hz=requested_rate, actual_hz=rate, sampled_frames=len(indices),
                                    minimum_three_hit_span_seconds=2/rate,
                                    confirmed=any(active), confirmed_frames=sum(active),
                                    first_confirmed_seconds=next((times[indices[i]] for i, yes in enumerate(active) if yes), None)))
    Path('reports/time-sampling-audit.json').write_text(json.dumps(results, indent=2))
    return results


if __name__ == '__main__':
    for row in audit(sys.argv[1:] or None):
        if row['category'] == ('fire' if row['clip'] == 'helmet.mp4' else 'smoke'):
            print(row)
