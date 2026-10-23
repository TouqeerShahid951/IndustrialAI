"""Check retained public downloads, camera allocation, cached fits and reported scores."""
import hashlib
import json
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from paired_camera import fit, file_sha256, load_manifest, masks, state_at, timed_flags, event_spans, score_events


def read(name):
    return json.loads((HERE / name).read_text())


def check_image(row):
    assert file_sha256(row['path']) == row['sha256'], row['path']


def main():
    commands = [[sys.executable, str(HERE / name), '--self-check']
                for name in ('curate.py', 'train_probe.py', 'paired_camera.py')]
    commands += [[sys.executable, '-m', 'compileall', '-q', str(HERE)],
                 [sys.executable, '-m', 'unittest', 'tests.test_benchmark_data',
                  'tests.test_benchmark_events', 'tests.test_run_benchmark', 'tests.test_evaluate']]
    checks = []
    for command in commands:
        run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        checks.append(dict(command=command, exit_code=run.returncode, output=(run.stdout + run.stderr).strip()))
    for metadata, filename, key in [
        ('firesense-metadata.json', 'smoke_videos.1407.zip', 'smoke_videos.1407.zip'),
        ('indoor-zenodo-metadata.json', 'Indoor-Fire-Smoke.zip', 'Indoor Fire Smoke.zip')]:
        row = next(f for f in read(metadata)['files'] if f['key'] == key)
        path = ROOT / 'data/public-training-footage-2026-10-23' / filename
        assert path.stat().st_size == row['size']
        assert hashlib.md5(path.read_bytes()).hexdigest() == row['checksum'].split(':')[1]
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
    for row in read('meva-files.json') + read('meva-long-files.json'):
        check_image(row)
        path = Path(row['path']); assert path.stat().st_size == row['bytes']
        parts = row['etag'].split('-')
        # S3 multipart ETags concatenate 8-MiB part MD5s; plain ETags hash the full file.
        with path.open('rb') as stream:
            hashes = []
            while block := stream.read(8 * 1024 * 1024):
                hashes.append(hashlib.md5(block).digest())
        actual = hashlib.md5(b''.join(hashes)).hexdigest() + '-' + str(len(hashes)) if len(parts) == 2 else hashlib.md5(path.read_bytes()).hexdigest()
        assert actual == row['etag'], path
    for row in read('firesense-files.json')['clips']:
        check_image(row)
    annotations = read('meva-frame-annotations.json')
    assert len(annotations['samples']) == 286
    for row in annotations['samples'] + read('prediction-review.json'):
        check_image(row)
    for row in annotations['samples']:
        assert row['smoke_assessment'] == row['fire_assessment'] == 'absent_visible'
    base = read('training-manifest.json')
    training = read('paired-training-manifest.json')
    assert len(base['base_training']) == 176 and len(base['additions']) == 26
    assert len(training) == 314 and Counter(r['target'] for r in training) == {1: 156, -1: 158}
    assert len({r['id'] for r in training}) == len(training)
    assert len({r['sha256'] for r in training}) == len(training)
    for row in training:
        check_image(row)
    for row in {r['source_path']: r for r in training[202:]}.values():
        assert file_sha256(row['source_path']) == row['source_sha256']
    result = read('paired-camera-results.json')
    assert result['script_sha256'] == file_sha256(HERE / 'paired_camera.py')
    assert result['spec_sha256'] == file_sha256(HERE / 'paired-camera-spec.json')
    assert result['ablation_spec_sha256'] == file_sha256(HERE / 'ablation-spec.json')
    assert result['training_manifest_sha256'] == file_sha256(HERE / 'paired-training-manifest.json')
    assert result['weights_sha256'] == file_sha256(result['weights_path'])
    assert result['feature_cache_sha256'] == file_sha256(result['feature_cache_path'])
    assert not result['gate_passed'] and not result['production_model_changed']
    initial = read('paired-initial-summary.json')['overall']
    assert all(result['overall'][k] == initial[k] for k in initial)
    cache = np.load(result['feature_cache_path'], allow_pickle=False)
    x = cache['training_features']; y = np.array([r['target'] for r in training])
    paired = fit(x, y, .1)
    saved = np.load(result['weights_path'], allow_pickle=False)
    for expected, key in zip(paired, ('mean', 'weights', 'bias')):
        np.testing.assert_allclose(expected, saved[key], rtol=1e-12, atol=1e-12)
    control = np.load(ROOT / 'outputs/public-training-footage-2026-10-23/scene-head.npz', allow_pickle=False)
    trial = read('experiment.json')
    assert trial['spec_sha256'] == file_sha256(HERE / 'experiment-spec.json')
    assert trial['script_sha256'] == file_sha256(HERE / 'train_probe.py')
    assert trial['spec']['training_manifest_sha256'] == file_sha256(HERE / 'training-manifest.json')
    assert trial['results'][1]['weights_sha256'] == file_sha256(trial['results'][1]['weights_path'])
    generic = sorted((i for i in range(202) if y[i] == -1), key=lambda i: training[i]['sha256'])[:56]
    indices = list(range(202)) + [i for i in range(202, 314) if y[i] == 1] + generic
    ablation = fit(x[indices], y[indices], .1)
    heads = dict(paired_camera=paired, unpaired_control=tuple(control[k] for k in ('mean', 'weights', 'bias')),
                 unmatched_negatives_control=ablation)
    clips = {r['clip_id']: r for name in ['reports/cctv-annotations-2026-10-22/manifest.jsonl',
        'benchmark/chat-review-manifest.jsonl', 'reports/smoke-improvement-2026-10-21/assistant-review-manifest.jsonl',
        'benchmark/manifest.jsonl'] for r in load_manifest(ROOT / name)}
    assert len(result['clips']) == 20
    assert sum(r['decoded_frames'] for r in result['clips']) == 9401
    assert sum(r['sampled_frames'] for r in result['clips']) == 949
    assert cache['heldout_ids'].tolist() == [r['clip_id'] + ':' + str(s['frame_index']) for r in result['clips'] for s in r['samples']]
    offset = 0
    for record in result['clips']:
        clip = clips[record['clip_id']]
        assert clip['camera_id'] != result['spec']['training_camera_family']
        assert clip['clip_id'] not in result['spec']['retired_validation_clip_ids']
        assert file_sha256(clip['local_path']) == record['source_sha256']
        assert file_sha256(clip['annotation_path']) == record['annotation_sha256']
        positive, negative = masks(clip, dict(excluded=record['exclusions'], expected=record['expected']))
        times = [s['seconds'] for s in record['samples']]
        assert all(a < b for a, b in zip(times, times[1:]))
        features = cache['heldout_features'][offset:offset + len(times)]; offset += len(times)
        for name, score_key in [('paired_camera', 'candidate_score'), ('unpaired_control', 'control_score'),
                                ('unmatched_negatives_control', 'ablation_score')]:
            mean, weights, bias = heads[name]
            scores = (features - mean) @ weights + bias
            np.testing.assert_allclose(scores, [s[score_key] for s in record['samples']], rtol=1e-10, atol=1e-10)
            flags = scores >= 0
            counts = dict(positive_frames=0, positive_hits=0, negative_frames=0, negative_hits=0, excluded_frames=0)
            for t, hit in zip(times, flags):
                state = state_at(t, positive, negative)
                if state == 0:
                    counts['excluded_frames'] += 1
                else:
                    label = 'positive' if state == 1 else 'negative'
                    counts[label + '_frames'] += 1; counts[label + '_hits'] += int(hit)
            assert counts == record['variants'][name]['frame_counts']
            for policy, flags_for_policy in [('raw', flags), ('scene_timed_2hz', timed_flags(times, flags))]:
                events = event_spans(clip['clip_id'], times, flags_for_policy, clip['duration_seconds'])
                stored = record['variants'][name]['policies'][policy]
                assert events == stored['events']
                scored = score_events(record['expected'], events, record['negative_seconds'], excluded_intervals=record['exclusions'])
                assert all(scored[k] == stored[k] for k in ('TP', 'FP', 'FN'))
    for name, overall in result['overall'].items():
        for key, value in overall['frame_counts'].items():
            assert value == sum(r['variants'][name]['frame_counts'][key] for r in result['clips'])
        for policy, values in overall['policies'].items():
            for key, value in values.items():
                assert np.isclose(value, sum(r['variants'][name]['policies'][policy][key] for r in result['clips']))
    benchmark_paths = ['reports/detector-root-cause-2026-10-22/baseline-benchmark.json',
        'reports/smoke-improvement-2026-10-21/current-human-development.json',
        'reports/smoke-improvement-2026-10-21/current-assistant-development.json', 'reports/benchmark-baseline.json']
    heldout_ids = {r['clip_id'] for r in result['clips']}
    baseline = [r for name in benchmark_paths for r in json.loads((ROOT / name).read_text())['clips']
                if r['kind'] == 'smoke' and r['clip_id'] in heldout_ids]
    assert len(baseline) == 20
    for stored in read('current-detector-heldout-events.json'):
        scored = [score_events(r['expected'], r['predicted'][stored['policy']], r['negative_seconds'],
                               excluded_intervals=r['excluded']) for r in baseline]
        assert all(stored[k] == sum(r[k] for r in scored) for k in ('TP', 'FP', 'FN'))
        assert np.isclose(stored['negative_seconds'], sum(r['negative_seconds'] for r in baseline))
    audit = dict(commands=checks, integrity_checks_passed=True, training_images=314, heldout_clips=20,
        decoded_frames=9401, sampled_frames=949, meva_reviewed_stills=286,
        main_result_reproduced_from_cached_features=True, original_pair_and_control_results_unchanged=True,
        camera_allocation='All C01-C15 retired to training/exclusion; no MmodalFire clip in held-out 20',
        artifacts_sha256={name: file_sha256(HERE / name) for name in ['paired_camera.py', 'train_probe.py',
            'curate.py', 'verify.py', 'paired-camera-results.json', 'paired-training-manifest.json', 'report.md']},
        production_model_changed=False, candidate_qualified_for_default=False)
    (HERE / 'verification.json').write_text(json.dumps(audit, indent=2) + '\n')
    print('Verified: 314 fitting images; 20 held-out clips; 949 scores for all three heads; source hashes, archive checks, camera split, self-checks and 14 unit tests.')


if __name__ == '__main__':
    main()
