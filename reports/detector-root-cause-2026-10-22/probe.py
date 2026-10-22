"""Controlled detector/input probes on the same lossless, manually reviewed source frames."""
import contextlib
import csv
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from evaluate import evaluate
from backend.pipeline import checkpoint
from scripts.benchmark_data import file_sha256
from scripts.audit_metrics import score_heads
from scripts.run_benchmark import read_run
from temporal import iou

module_spec = importlib.util.spec_from_file_location('baseline_analysis', ROOT / 'reports/cctv-baseline-2026-10-22/analyze.py')
baseline_analysis = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(baseline_analysis)
CANONICAL = {'fire': 'fire', 'smoke': 'smoke', 'Fire': 'fire', 'Smoke': 'smoke', 'flame': 'fire', 'Flame': 'fire',
             'smoke_visible': 'smoke', 'flame_visible': 'fire'}


def summarize(items, predictions, threshold):
    scores = {}
    for kind in ('fire', 'smoke'):
        s = dict(positive_frames=0, positive_with_candidate=0, negative_frames=0,
                 negative_with_candidate=0, uncertain_frames=0, boxed_positive_frames=0, box_TP=0, box_FP=0, box_FN=0)
        for item in items:
            f = item['frame_annotation']
            selected = [b for b in predictions.get(item['id'], []) if b['class'] == kind and b['confidence'] >= threshold]
            state = f['class_assessment'][kind]
            if state == 'uncertain':
                s['uncertain_frames'] += 1
            else:
                prefix = 'positive' if state == 'present' else 'negative'
                s[prefix + '_frames'] += 1
                s[prefix + '_with_candidate'] += bool(selected)
            truth = baseline_analysis.scorable_objects(f, kind)
            if truth is not None:
                tp, fp, fn = score_heads(truth, selected, .5)
                s['box_TP'] += tp; s['box_FP'] += fp; s['box_FN'] += fn
                s['boxed_positive_frames'] += bool(truth)
        scores[kind] = s
    return scores


def self_check():
    items = [dict(id='positive', frame_annotation=dict(class_assessment={'fire': 'present', 'smoke': 'uncertain'},
             objects=[{'class': 'fire', 'bbox_xyxy': [0, 0, 10, 10], 'review_status': 'reviewed'}])),
             dict(id='negative', frame_annotation=dict(class_assessment={'fire': 'absent_visible', 'smoke': 'absent_visible'}, objects=[])),
             dict(id='ambiguous_box', frame_annotation=dict(class_assessment={'fire': 'uncertain', 'smoke': 'present'},
             objects=[{'class': 'smoke', 'bbox_xyxy': [0, 0, 10, 10], 'review_status': 'ambiguous'}]))]
    predictions = {'positive': [{'class': 'fire', 'bbox': [0, 0, 10, 10], 'confidence': .9}],
                   'negative': [{'class': 'smoke', 'bbox': [0, 0, 10, 10], 'confidence': .7}],
                   'ambiguous_box': [{'class': 'smoke', 'bbox': [0, 0, 10, 10], 'confidence': .2}]}
    r = summarize(items, predictions, .25)
    assert r['fire']['positive_with_candidate'] == r['fire']['box_TP'] == 1
    assert r['smoke']['positive_with_candidate'] == r['smoke']['box_FN'] == 0
    assert r['smoke']['negative_with_candidate'] == r['smoke']['box_FP'] == 1
    assert summarize(items, predictions, .1)['smoke']['positive_with_candidate'] == 1


def load_predictions(run):
    _, _, rows, _ = read_run(run)
    predictions = {}
    for r in rows:
        predictions.setdefault(Path(r['source']).stem, []).append(dict(
            **{'class': CANONICAL[r['class']]}, confidence=float(r['confidence']),
            bbox=[float(r[k]) for k in ('x1', 'y1', 'x2', 'y2')]))
    return predictions


def main():
    self_check()
    import cv2
    import torch
    from ultralytics import YOLO
    cv2.setNumThreads(2); torch.set_num_threads(4)
    inputs = json.loads((HERE / 'inputs.json').read_text())
    items = inputs['frames']
    assert len(items) == 69
    for item in items:
        assert file_sha256(item['path']) == item['sha256']
        assert file_sha256(item['annotation_path']) == item['annotation_sha256']
    early = json.loads((ROOT / 'reports/smoke-improvement-2026-10-21/alternative-models.json').read_text())[0]
    strict = json.loads((HERE / 'new-candidate.json').read_text())
    fasdd = json.loads((HERE / 'full-fasdd-candidate.json').read_text())
    checkpoints = {'baseline': (str(checkpoint('fire_smoke', 'var/mvp')), 'b91633799ceb052c814b4f8b77a37efc9a40f002d528df97d74463585fa4f28f'),
                   'early': (early['path'], early['sha256']),
                   'yolo26s': (str(ROOT / 'outputs/model-candidates-2026-10-21/yolo26s-alternative.pt'), '283c996482e26013f6e60559ad25c49f38f3aa9937961c8c33aaa7d0fc8d1d59'),
                   'strict': (strict['path'], strict['sha256']),
                   'fasdd': (fasdd['path'], fasdd['sha256'])}
    variants = [('baseline-640-mps', 'baseline', 640, 'mps'), ('baseline-640-cpu', 'baseline', 640, 'cpu'),
                ('baseline-1280-mps', 'baseline', 1280, 'mps'), ('early-640-mps', 'early', 640, 'mps'),
                ('yolo26s-640-mps', 'yolo26s', 640, 'mps'), ('strict-640-mps', 'strict', 640, 'mps'),
                ('strict-960-mps', 'strict', 960, 'mps'), ('fasdd-640-mps', 'fasdd', 640, 'mps'),
                ('fasdd-1280-mps', 'fasdd', 1280, 'mps')]
    root = ROOT / 'outputs/detector-root-cause-2026-10-22'
    cached = {r['variant']: r for r in json.loads((HERE / 'probes.json').read_text())} if (HERE / 'probes.json').exists() else {}
    records, audits = [], []
    for variant, key, size, device in variants:
        path, digest = checkpoints[key]
        assert file_sha256(path) == digest
        model = YOLO(path)
        assert {CANONICAL[name] for name in model.names.values()} == {'fire', 'smoke'}
        audits.append(dict(variant=variant, sha256=digest, classes=model.names,
                           parameters=sum(p.numel() for p in model.model.parameters()),
                           training_args={k: model.ckpt.get('train_args', {}).get(k) for k in ('imgsz', 'epochs')}))
        del model
        directory = root / variant; directory.mkdir(exist_ok=True)
        if variant in cached:
            previous = cached[variant]
            assert (previous['checkpoint_sha256'], previous['imgsz'], previous['device']) == (digest, size, device)
            run = previous['run']
            meta, summaries, _, _ = read_run(run)
            assert len(summaries) == len(items)
            assert meta['source_hashes'] == {str(Path(item['path']).resolve()): item['sha256'] for item in items}
        else:
            with (directory / 'inference.log').open('w') as log, contextlib.redirect_stdout(log):
                run = evaluate(root / 'images', output=directory, models=['fire_smoke'], device=device,
                               conf=.01, imgsz=size, stride=1, max_frames=1, checkpoint=path)
        predictions = load_predictions(run)
        record = dict(variant=variant, checkpoint_sha256=digest, imgsz=size, device=device, confidence_floor=.01,
                      run=str(run), thresholds={str(t): summarize(items, predictions, t) for t in (.05, .1, .25, .5)})
        records.append(record)
        (HERE / 'probes.json').write_text(json.dumps(records, indent=2) + '\n')
        print(variant, json.dumps(record['thresholds']['0.25']), flush=True)
    (HERE / 'checkpoint-audit.json').write_text(json.dumps(audits, indent=2) + '\n')
    reference = Path(json.loads((ROOT / 'reports/cctv-baseline-2026-10-22/runs.json').read_text())[0])
    _, _, rows, _ = read_run(reference)
    prior = {}
    for r in rows:
        identity = f"{Path(r['source']).stem}-{int(r['frame']):06}"
        prior.setdefault(identity, []).append({'class': r['class'], 'confidence': float(r['confidence']),
                                              'bbox': [float(r[k]) for k in ('x1', 'y1', 'x2', 'y2')]})
    parity = []
    for record in records[:2]:
        predictions = load_predictions(record['run']); matched = missing = added = 0; max_confidence_delta = 0
        for item in items:
            truth = prior.get(item['id'], [])
            selected = [b for b in predictions.get(item['id'], []) if b['confidence'] >= .25]
            tp, fp, fn = score_heads(truth, selected, .99)
            matched += tp; missing += fn; added += fp
            for b in selected:
                similar = [old for old in truth if old['class'] == b['class'] and iou(old['bbox'], b['bbox']) >= .99]
                if similar:
                    max_confidence_delta = max(max_confidence_delta, min(abs(b['confidence'] - old['confidence']) for old in similar))
        parity.append(dict(variant=record['variant'], matched_boxes=matched, missing_boxes=missing, added_boxes=added,
                           max_matched_confidence_delta=max_confidence_delta))
    (HERE / 'runtime-parity.json').write_text(json.dumps(parity, indent=2) + '\n')
    print('Runtime parity:', json.dumps(parity), flush=True)


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Probe self-check passed: class uncertainty, score thresholds and ambiguous localization.')
    else:
        main()
