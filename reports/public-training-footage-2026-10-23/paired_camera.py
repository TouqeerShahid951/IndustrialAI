"""Train with clear/smoke/mist observations from one retired camera; validate on other cameras."""
import json
import math
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREVIOUS = ROOT / 'reports/detector-root-cause-2026-10-22'
OUT = ROOT / 'outputs/public-training-footage-2026-10-23'
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(PREVIOUS))
from scripts.benchmark_data import file_sha256, load_manifest
from scripts.benchmark_events import subtract_intervals, union_intervals, seconds, score_events, merge_candidates
from scripts.run_benchmark import read_run
from scene_head import fit, self_check as numerical_check
from compare import analysis


def state_at(t, positive, negative):
    return 1 if any(a <= t < b for a, b in positive) else -1 if any(a <= t < b for a, b in negative) else 0


def timed_flags(times, flags):
    history, result = [], []
    for t, hit in zip(times, flags):
        history = [p for p in history if p >= t - 2]
        if hit:
            history.append(t)
        result.append(bool(hit and len(history) >= 3 and t - history[0] >= 1))
    return result


def event_spans(clip_id, times, flags, duration):
    return merge_candidates([dict(clip_id=clip_id, kind='smoke', start_seconds=t,
        end_seconds=times[i + 1] if i + 1 < len(times) else duration)
        for i, (t, hit) in enumerate(zip(times, flags)) if hit], 2)


def self_check():
    numerical_check()
    assert state_at(1, [[1, 2]], [[0, 1]]) == 1 and state_at(2, [[1, 2]], [[0, 1]]) == 0
    assert timed_flags([0, .5, 1, 4, 4.5, 5], [1, 1, 1, 1, 0, 1]) == [False, False, True, False, False, False]
    assert len(event_spans('x', [0, .5, 1], [0, 1, 1], 1.5)) == 1


def masks(clip, entry):
    labels = json.loads(Path(clip['annotation_path']).read_text())
    excluded = [[e['start_seconds'], e['end_seconds']] for e in entry['excluded']]
    covered = subtract_intervals(labels['reviewed_intervals']['smoke'], excluded)
    positive = analysis.intersection(covered, [[e['start_seconds'], e['end_seconds']] for e in entry['expected']])
    return positive, subtract_intervals(covered, positive)


def prepare_training(spec):
    import cv2
    clips = load_manifest(ROOT / 'reports/cctv-annotations-2026-10-22/manifest.jsonl')
    benchmark = json.loads((PREVIOUS / 'baseline-benchmark.json').read_text())
    run = json.loads((ROOT / 'reports/cctv-baseline-2026-10-22/runs.json').read_text())[0]
    _, _, _, observations = read_run(run)
    entries = {e['clip_id']: e for e in benchmark['clips'] if e['kind'] == 'smoke'}
    rows = []; directory = OUT / 'paired-training-frames'; directory.mkdir(exist_ok=True)
    for clip in clips:
        if clip['clip_id'] not in spec['retired_validation_clip_ids']:
            continue
        assert clip['camera_id'] == spec['training_camera_family']
        assert file_sha256(clip['local_path']) == clip['source_sha256']
        positive, negative = masks(clip, entries[clip['clip_id']])
        source = Path(clip['local_path']).resolve()
        obs = [o for o in observations if Path(o['source']).resolve() == source]
        chosen = {}
        for state, windows, limit in [(1, positive, spec['positive_frames_per_smoke_clip']),
                                      (-1, negative, spec['negative_frames_per_clear_or_documented_mist_clip'])]:
            candidates = [o for o in obs if any(a <= float(o['source_seconds']) < b for a, b in windows)]
            if candidates:
                for i in np.linspace(0, len(candidates) - 1, min(limit, len(candidates)), dtype=int):
                    o = candidates[i]; chosen[int(o['frame'])] = (state, float(o['source_seconds']))
        if not chosen:
            continue
        cap = cv2.VideoCapture(str(source)); index = 0
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            if index in chosen:
                target, t = chosen[index]
                assert abs(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 - t) < 1e-6
                path = directory / (clip['clip_id'] + f'-{index:06}.png'); assert cv2.imwrite(str(path), bgr)
                rows.append(dict(id=path.stem, path=str(path), sha256=file_sha256(path), target=target,
                    source_path=str(source), source_sha256=clip['source_sha256'], frame_index=index, seconds=t,
                    group=spec['training_camera_family'], annotation_sha256=file_sha256(clip['annotation_path'])))
            index += 1
        cap.release()
        assert sum(x['id'].startswith(clip['clip_id'] + '-') for x in rows) == len(chosen)
    base = json.loads((HERE / 'training-manifest.json').read_text())
    result = base['base_training'] + base['additions'] + rows
    assert sum(x['target'] == 1 for x in rows) == sum(x['target'] == -1 for x in rows) == 56
    (HERE / 'paired-training-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    self_check()
    import cv2
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor
    torch.set_num_threads(4); cv2.setNumThreads(2)
    spec = json.loads((HERE / 'paired-camera-spec.json').read_text())
    assert spec['frozen_before_training_and_heldout_inference'] and spec['threshold'] == 0
    training = prepare_training(spec)
    backbone = json.loads((PREVIOUS / 'scene-model.json').read_text())
    for f in backbone['files']:
        assert file_sha256(f['path']) == f['sha256']
    model = AutoModel.from_pretrained(backbone['local_path'], local_files_only=True, trust_remote_code=False).eval()
    processor = AutoProcessor.from_pretrained(backbone['local_path'], local_files_only=True, trust_remote_code=False)

    def encode(images):
        with torch.inference_mode():
            f = model.get_image_features(**processor(images=images, return_tensors='pt')).pooler_output
            return (f / f.norm(p=2, dim=-1, keepdim=True)).cpu().numpy().astype(np.float64)

    features = []
    for start in range(0, len(training), 8):
        batch = training[start:start + 8]
        for x in batch:
            assert file_sha256(x['path']) == x['sha256']
        images = [Image.open(x['path']).convert('RGB') for x in batch]
        features.extend(encode(images))
        for image in images:
            image.close()
    mean, weights, bias = fit(np.asarray(features), np.array([x['target'] for x in training]), spec['ridge_lambda'])
    weights_path = OUT / 'paired-scene-head.npz'; np.savez_compressed(weights_path, mean=mean, weights=weights, bias=bias)
    control = np.load(OUT / 'scene-head.npz', allow_pickle=False)
    # Match row count and class balance; change only where the extra negatives come from.
    base_count = 202
    generic_negative = sorted((i for i in range(base_count) if training[i]['target'] == -1),
                              key=lambda i: training[i]['sha256'])[:56]
    positive_camera = [i for i in range(base_count, len(training)) if training[i]['target'] == 1]
    ablation_indices = list(range(base_count)) + positive_camera + generic_negative
    assert len(ablation_indices) == len(training) == 314
    ablation = fit(np.asarray(features)[ablation_indices],
                   np.array([training[i]['target'] for i in ablation_indices]), spec['ridge_lambda'])
    heads = {'paired_camera': (mean, weights, bias), 'unpaired_control': (control['mean'], control['weights'], float(control['bias'])),
             'unmatched_negatives_control': ablation}
    manifests = [(ROOT / 'reports/cctv-annotations-2026-10-22/manifest.jsonl', PREVIOUS / 'baseline-benchmark.json'),
        (ROOT / 'benchmark/chat-review-manifest.jsonl', ROOT / 'reports/smoke-improvement-2026-10-21/current-human-development.json'),
        (ROOT / 'reports/smoke-improvement-2026-10-21/assistant-review-manifest.jsonl', ROOT / 'reports/smoke-improvement-2026-10-21/current-assistant-development.json'),
        (ROOT / 'benchmark/manifest.jsonl', ROOT / 'reports/benchmark-baseline.json')]
    records, heldout_features, heldout_ids = [], [], []
    for manifest, benchmark_path in manifests:
        benchmark = json.loads(benchmark_path.read_text())
        entries = {e['clip_id']: e for e in benchmark['clips'] if e['kind'] == 'smoke'}
        for clip in load_manifest(manifest):
            if clip['clip_id'] in spec['retired_validation_clip_ids'] or clip['clip_id'] not in entries or clip['clip_id'] == 'construction-demo':
                continue
            assert clip['camera_id'] != spec['training_camera_family']
            assert file_sha256(clip['local_path']) == clip['source_sha256']
            assert benchmark['scoring_provenance']['annotation_sha256'][clip['clip_id']] == file_sha256(clip['annotation_path'])
            cap = cv2.VideoCapture(clip['local_path']); expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            index = 0; bucket = None; previous = -1; images = []; pending = []; samples = []
            def flush():
                if images:
                    values = encode(images)
                    scores = {name: (values - m) @ w + b for name, (m, w, b) in heads.items()}
                    for j, (i, t) in enumerate(pending):
                        samples.append(dict(frame_index=i, seconds=t, candidate_score=float(scores['paired_camera'][j]),
                            control_score=float(scores['unpaired_control'][j]), ablation_score=float(scores['unmatched_negatives_control'][j])))
                        heldout_features.append(values[j]); heldout_ids.append(clip['clip_id'] + ':' + str(i))
                    for image in images:
                        image.close()
                    images.clear(); pending.clear()
            while True:
                ok, bgr = cap.read()
                if not ok:
                    break
                t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                assert previous < t < clip['duration_seconds'], (clip['clip_id'], index, previous, t)
                previous = t
                if math.floor(t * 2) != bucket:
                    bucket = math.floor(t * 2); images.append(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))); pending.append((index, t))
                    if len(images) == 8:
                        flush()
                index += 1
            flush(); cap.release(); assert index == expected
            entry = entries[clip['clip_id']]; positive, negative = masks(clip, entry)
            times = [s['seconds'] for s in samples]
            variants = {}
            for name, key in [('paired_camera', 'candidate_score'), ('unpaired_control', 'control_score'),
                              ('unmatched_negatives_control', 'ablation_score')]:
                hits = [s[key] >= 0 for s in samples]
                counts = dict(positive_frames=0, positive_hits=0, negative_frames=0, negative_hits=0, excluded_frames=0)
                for t, hit in zip(times, hits):
                    state = state_at(t, positive, negative)
                    if not state:
                        counts['excluded_frames'] += 1
                    else:
                        label = 'positive' if state == 1 else 'negative'
                        counts[label + '_frames'] += 1; counts[label + '_hits'] += hit
                policies = {}
                for policy, flags in [('raw', hits), ('scene_timed_2hz', timed_flags(times, hits))]:
                    events = event_spans(clip['clip_id'], times, flags, clip['duration_seconds'])
                    scored = score_events(entry['expected'], events, entry['negative_seconds'], excluded_intervals=entry['excluded'])
                    active = [[e['start_seconds'], e['end_seconds']] for e in events]
                    scored.update(positive_alert_seconds=seconds(analysis.intersection(active, positive)),
                                  negative_alert_seconds=seconds(analysis.intersection(active, negative)), events=events)
                    policies[policy] = scored
                variants[name] = dict(frame_counts=counts, policies=policies)
            records.append(dict(clip_id=clip['clip_id'], camera_id=clip['camera_id'], source_sha256=clip['source_sha256'],
                annotation_sha256=file_sha256(clip['annotation_path']), decoded_frames=index, sampled_frames=len(samples),
                positive_seconds=seconds(positive), negative_seconds=entry['negative_seconds'], samples=samples,
                expected=entry['expected'], exclusions=entry['excluded'], variants=variants,
                current_detector_native_timed_events=entry['predicted']['timed']))
            print(clip['clip_id'], {k: (v['frame_counts'], {p: (s['TP'], s['FP'], s['FN']) for p, s in v['policies'].items()}) for k, v in variants.items()}, flush=True)
            (HERE / 'paired-heldout-progress.json').write_text(json.dumps(records, indent=2) + '\n')
    assert len(records) == 20
    overall = {}
    for name in heads:
        overall[name] = dict(frame_counts={k: sum(r['variants'][name]['frame_counts'][k] for r in records)
            for k in records[0]['variants'][name]['frame_counts']}, policies={})
        for policy in ('raw', 'scene_timed_2hz'):
            scored = [r['variants'][name]['policies'][policy] for r in records]
            overall[name]['policies'][policy] = {k: sum(s[k] for s in scored) for k in ('TP', 'FP', 'FN', 'positive_alert_seconds', 'negative_alert_seconds')}
    result = dict(spec=spec, spec_sha256=file_sha256(HERE / 'paired-camera-spec.json'), script_sha256=file_sha256(__file__),
        training_manifest_sha256=file_sha256(HERE / 'paired-training-manifest.json'), training_images=len(training),
        weights_path=str(weights_path), weights_sha256=file_sha256(weights_path), overall=overall, clips=records,
        current_detector_policy_note='Stored native spatial-voting events; scene policies use binary 2-Hz observations without invented boxes',
        production_model_changed=False, gate_passed=False)
    initial = json.loads((HERE / 'paired-initial-summary.json').read_text())['overall']
    assert all(overall[name] == initial[name] for name in ('paired_camera', 'unpaired_control'))
    result['ablation_spec_sha256'] = file_sha256(HERE / 'ablation-spec.json')
    feature_path = OUT / 'paired-features.npz'
    np.savez_compressed(feature_path, training_features=features, heldout_features=heldout_features, heldout_ids=heldout_ids)
    result.update(feature_cache_path=str(feature_path), feature_cache_sha256=file_sha256(feature_path))
    (HERE / 'paired-camera-results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('OVERALL', json.dumps(overall), flush=True)


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Paired-camera checks passed: uncertainty boundaries, causal voting, event merging and fit.')
    else:
        main()
