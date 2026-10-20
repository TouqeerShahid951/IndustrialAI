"""Descriptive metrics for the saved, manually reviewed CCTV frame audit."""
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from temporal import iou


def score_heads(truth, predictions, overlap=.5):
    used = set()
    matched = 0
    for pred in sorted(predictions, key=lambda p: p['confidence'], reverse=True):
        candidates = [(iou(pred['bbox'], gt['bbox']), index) for index, gt in enumerate(truth)
                      if index not in used and pred['class'] == gt['class']]
        best, index = max(candidates, default=(0, -1))
        if best >= overlap:
            used.add(index)
            matched += 1
    return matched, len(predictions) - matched, len(truth) - matched


def audit():
    folder = Path('data/cctv-audit')
    labels = json.loads((folder / 'frame-labels.json').read_text())
    heads = json.loads((folder / 'head-labels.json').read_text())['frames']
    metrics = []
    for spec in json.loads(Path('reports/cctv-audit-runs.json').read_text()):
        with (Path(spec['run']) / 'detections.csv').open() as f:
            rows = list(csv.DictReader(f))
        for threshold in (.05, .1, .15, .25, .4, .6):
            selected = [r for r in rows if float(r['confidence']) >= threshold]
            if spec['model'] == 'fire_smoke':
                smoke_hits = sum(any(Path(r['source']).name == label['image'] and r['class'] == 'smoke'
                                     for r in selected) for label in labels if label['smoke'])
                false_fire = sum(any(Path(r['source']).name == label['image'] and r['class'] == 'fire'
                                     for r in selected) for label in labels if not label['fire'])
                false_smoke = sum(any(Path(r['source']).name == label['image'] and r['class'] == 'smoke'
                                      for r in selected) for label in labels if not label['smoke'])
                metrics.append(dict(**spec, threshold=threshold, smoke_hits=smoke_hits, smoke_targets=22,
                                    false_fire_frames=false_fire, fire_negative_frames=37,
                                    false_smoke_frames=false_smoke, smoke_negative_frames=15))
            else:
                for overlap in (.3, .5):
                    for category in ('Hardhat', 'NO-Hardhat'):
                        tp = fp = fn = 0
                        for frame in heads:
                            predictions = [{'class': r['class'], 'confidence': float(r['confidence']),
                                            'bbox': [float(r[k]) for k in ('x1', 'y1', 'x2', 'y2')]}
                                           for r in selected if Path(r['source']).name == frame['image'] and r['class'] == category]
                            truth = [g for g in frame['boxes'] if g['class'] == category]
                            a, b, c = score_heads(truth, predictions, overlap)
                            tp += a; fp += b; fn += c
                        metrics.append(dict(**spec, threshold=threshold, overlap=overlap, category=category,
                                            tp=tp, fp=fp, fn=fn,
                                            precision=tp/(tp+fp) if tp+fp else None,
                                            recall=tp/(tp+fn) if tp+fn else None))
    Path('reports/cctv-frame-audit-metrics.json').write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == '__main__':
    for row in audit():
        if row['threshold'] in (.1, .25, .4) and row.get('overlap', .5) == .5:
            print({k:v for k,v in row.items() if k != 'run'})
