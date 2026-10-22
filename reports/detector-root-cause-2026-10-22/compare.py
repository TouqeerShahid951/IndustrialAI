"""Reuse the pinned benchmark and interval masks for complete-video candidate comparisons."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.benchmark_data import load_manifest, file_sha256
from scripts.benchmark_events import seconds, subtract_intervals, union_intervals
from scripts.run_benchmark import build_report, read_run, recording

spec = importlib.util.spec_from_file_location('baseline_analysis', ROOT / 'reports/cctv-baseline-2026-10-22/analyze.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def frame_counts(times, frames, positive, negative, kind):
    result = dict(positive_frames=0, positive_hit_frames=0, negative_frames=0, negative_hit_frames=0, excluded_frames=0)
    for t, boxes in zip(times, frames):
        state = 'positive' if any(a <= t < b for a, b in positive) else 'negative' if any(a <= t < b for a, b in negative) else 'excluded'
        result[state + '_frames'] += 1
        if state != 'excluded':
            result[state + '_hit_frames'] += any(b['class'] == kind for b in boxes)
    return result


def self_check():
    boxes = [[{'class': 'smoke'}]] * 4
    assert frame_counts([0, 1, 2, 3], boxes, [[1, 2]], [[0, 1], [3, 4]], 'smoke') == dict(
        positive_frames=1, positive_hit_frames=1, negative_frames=2, negative_hit_frames=2, excluded_frames=1)


def compare(name, runs, manifest):
    report = build_report(manifest, runs)
    (HERE / (name + '-benchmark.json')).write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    assert len(runs) == 1
    meta, summaries, detections, observations = read_run(runs[0])
    clips = {c['clip_id']: c for c in load_manifest(manifest)}
    recordings = {}
    for clip_id, clip in clips.items():
        source = Path(clip['local_path']).resolve()
        summary = next(s for s in summaries if Path(s['source']).resolve() == source)
        recordings[clip_id] = recording(clip, summary, detections, observations)
    frames, events = [], []
    for entry in report['clips']:
        clip_id, kind = entry['clip_id'], entry['kind']
        labels = json.loads(Path(clips[clip_id]['annotation_path']).read_text())
        excluded = [[e['start_seconds'], e['end_seconds']] for e in entry['excluded']]
        covered = subtract_intervals(labels['reviewed_intervals'][kind], excluded)
        positive = analysis.intersection(covered, [[e['start_seconds'], e['end_seconds']] for e in entry['expected']])
        negative = subtract_intervals(covered, positive)
        rec = recordings[clip_id]
        frames.append(dict(clip_id=clip_id, kind=kind, **frame_counts(rec['times'], rec['frames'], positive, negative, kind)))
        for policy in ('raw', 'timed'):
            pieces = [subtract_intervals([[e['start_seconds'], e['end_seconds']]], excluded) for e in entry['predicted'][policy]]
            active = union_intervals([w for p in pieces for w in p])
            events.append(dict(clip_id=clip_id, kind=kind, policy=policy,
                negative_scene_false_events=sum(bool(analysis.intersection(p, negative)) for p in pieces),
                negative_alert_span_seconds=seconds(analysis.intersection(active, negative)),
                positive_alert_span_seconds=seconds(analysis.intersection(active, positive)), positive_seconds=seconds(positive)))
    overall = {}
    for kind in ('fire', 'smoke'):
        chosen = [r for r in frames if r['kind'] == kind]
        counts = {k: sum(r[k] for r in chosen) for k in chosen[0] if k.endswith('_frames')}
        overall[kind] = dict(frame_counts=counts, policies={})
        for policy in ('raw', 'timed'):
            chosen = [r for r in events if r['kind'] == kind and r['policy'] == policy]
            extra = {k: sum(r[k] for r in chosen) for k in ('negative_scene_false_events', 'negative_alert_span_seconds',
                     'positive_alert_span_seconds', 'positive_seconds')}
            overall[kind]['policies'][policy] = dict(report['per_capability'][kind]['policies'][policy], **extra)
    return dict(name=name, overall=overall, per_clip_frames=frames, per_clip_events=events,
                checkpoint=meta['checkpoints'], configuration=meta['configuration'], runs=runs,
                analyzed_frames=sum(s['frames'] for s in summaries))


def main():
    self_check()
    manifest = ROOT / 'reports/cctv-annotations-2026-10-22/manifest.jsonl'
    paths = [('baseline', ROOT / 'reports/cctv-baseline-2026-10-22/runs.json'),
             ('early-domestic-full', HERE / 'early-domestic-full-run.json'),
             ('fasdd-1280-full', HERE / 'fasdd-1280-full-run.json')]
    result = dict(manifest_sha256=file_sha256(manifest), analysis_sha256=file_sha256(__file__),
                  variants=[compare(name, json.loads(path.read_text()), manifest) for name, path in paths if path.exists()],
                  gate_passed=False, production_model_changed=False)
    (HERE / 'full-video-comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    for variant in result['variants']:
        print(variant['name'], json.dumps(variant['overall']), flush=True)


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Comparison self-check passed: exact boundaries and excluded time.')
    else:
        main()
