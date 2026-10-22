"""Reproduce the annotated-clip baseline, including the application's actual event policy."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from backend.pipeline import fire_incidents, REGISTRY, PROFILE
from scripts.benchmark_data import load_manifest, file_sha256
from scripts.benchmark_events import score_events, subtract_intervals, union_intervals, seconds
from scripts.run_benchmark import build_report, read_run, recording
from scripts.audit_metrics import score_heads


def intersection(a, b):
    return union_intervals([[max(x, u), min(y, v)] for x, y in a for u, v in b if max(x, u) < min(y, v)])


def scorable_objects(frame, kind):
    objects = [o for o in frame['objects'] if o['class'] == kind]
    state = frame['class_assessment'][kind]
    if state == 'absent_visible':
        assert not objects
        return []
    if state == 'present' and objects and all(o['review_status'] == 'reviewed' for o in objects):
        return [{'class': kind, 'bbox': o['bbox_xyxy']} for o in objects]
    return None


def self_check():
    assert intersection([[0, 5]], [[2, 7]]) == [[2, 5]]
    assert intersection([[0, 1]], [[1, 2]]) == []
    f = {'class_assessment': {'fire': 'present', 'smoke': 'uncertain'},
         'objects': [{'class': 'fire', 'bbox_xyxy': [0, 0, 10, 10], 'review_status': 'reviewed'}]}
    assert scorable_objects(f, 'fire') == [{'class': 'fire', 'bbox': [0, 0, 10, 10]}]
    assert scorable_objects(f, 'smoke') is None
    f['objects'][0]['review_status'] = 'ambiguous'
    assert scorable_objects(f, 'fire') is None
    f['class_assessment']['smoke'] = 'absent_visible'
    assert scorable_objects(f, 'smoke') == []
    prediction = {'clip_id': 'x', 'kind': 'smoke', 'start_seconds': 0, 'end_seconds': 10}
    scored = score_events([], [prediction], 0, excluded_intervals=[dict(prediction, reason='ambiguous')])
    assert scored['FP'] == 0 and scored['excluded_predictions'] == 1


def main():
    self_check()
    manifest = ROOT / 'reports/cctv-annotations-2026-10-22/manifest.jsonl'
    clips = load_manifest(manifest)
    runs = json.loads((HERE / 'runs.json').read_text())
    assert len(runs) == 1
    metadata, summaries, detections, observations = read_run(runs[0])
    assert metadata['checkpoints']['fire_smoke']['sha256'] == REGISTRY['fire_smoke']['sha256']
    assert metadata['configuration']['stride'] == 1
    assert metadata['configuration']['confidence'] == PROFILE['confidence'] == .25
    assert metadata['configuration']['imgsz'] == PROFILE['imgsz'] == 640
    spec = json.loads((HERE / 'inference-spec.json').read_text())
    assert file_sha256(manifest) == spec['manifest_sha256']
    assert all(file_sha256(ROOT / p) == h for p, h in spec['code_hashes'].items())
    assert len(summaries) == len(clips) == 23
    benchmark = build_report(manifest, runs)
    (HERE / 'benchmark.json').write_text(json.dumps(benchmark, indent=2, allow_nan=False) + '\n')
    expected_counts = {x['clip_id']: x['decoded_frames'] for x in json.loads(
        (ROOT / 'reports/cctv-annotations-2026-10-22/review-evidence.json').read_text())}
    entries = {(e['clip_id'], e['kind']): e for e in benchmark['clips']}
    rows, app_events, frame_stats, spot_checks = [], [], [], []
    total_frames = 0
    for clip in clips:
        labels = json.loads(Path(clip['annotation_path']).read_text())
        summary = next(s for s in summaries if Path(s['source']).resolve() == Path(clip['local_path']).resolve())
        assert summary['frames'] == expected_counts[clip['clip_id']]
        total_frames += summary['frames']
        rec = recording(clip, summary, detections, observations)
        application_rows = [{'time': t, 'boxes': [dict(b, canonical=b['class']) for b in boxes]}
                            for t, boxes in zip(rec['times'], rec['frames'])]
        application = fire_incidents(application_rows, ['fire', 'smoke'], clip['duration_seconds'])
        app_events.extend(dict(e, clip_id=clip['clip_id']) for e in application)
        frame_indices = [int(r['frame']) for r in observations if Path(r['source']).resolve() == Path(clip['local_path']).resolve()]
        by_frame = dict(zip(frame_indices, rec['frames']))
        for kind in ('fire', 'smoke'):
            entry = entries[clip['clip_id'], kind]
            excluded = [[x['start_seconds'], x['end_seconds']] for x in entry['excluded']]
            covered = subtract_intervals(labels['reviewed_intervals'][kind], excluded)
            positive = intersection(covered, [[e['start_seconds'], e['end_seconds']] for e in entry['expected']])
            negative = subtract_intervals(covered, positive)
            assert abs(seconds(negative) - entry['negative_seconds']) < 1e-6
            stats = dict(clip_id=clip['clip_id'], kind=kind, positive_frames=0, positive_hit_frames=0,
                         negative_frames=0, negative_hit_frames=0, excluded_frames=0)
            for state in ('positive', 'negative'):
                stats[state + '_box_count'] = 0
                stats[state + '_max_confidence'] = None
            for t, boxes in zip(rec['times'], rec['frames']):
                state = 'positive' if any(a <= t < b for a, b in positive) else 'negative' if any(a <= t < b for a, b in negative) else 'excluded'
                stats[state + '_frames'] += 1
                if state != 'excluded':
                    matching = [b for b in boxes if b['class'] == kind]
                    stats[state + '_hit_frames'] += bool(matching)
                    stats[state + '_box_count'] += len(matching)
                    if matching:
                        stats[state + '_max_confidence'] = max(stats[state + '_max_confidence'] or 0, max(b['confidence'] for b in matching))
            frame_stats.append(stats)
            policies = dict(entry['predicted'])
            policies['application'] = [dict(clip_id=clip['clip_id'], kind=kind, start_seconds=e['start'], end_seconds=e['end']) for e in application if e['kind'] == kind]
            for policy, predicted in policies.items():
                score = score_events(entry['expected'], predicted, entry['negative_seconds'], excluded_intervals=entry['excluded'])
                observable = [subtract_intervals([[p['start_seconds'], p['end_seconds']]], excluded) for p in predicted]
                active = union_intervals([w for pieces in observable for w in pieces])
                false_on_negative = sum(bool(intersection(pieces, negative)) for pieces in observable)
                rows.append(dict(clip_id=clip['clip_id'], kind=kind, camera_id=clip['camera_id'], policy=policy,
                                 reviewed_seconds=entry['reviewed_seconds'], coverage_seconds=entry['coverage_seconds'],
                                 positive_seconds=seconds(positive), **score,
                                 negative_scene_false_events=false_on_negative,
                                 negative_scene_false_events_per_minute=false_on_negative * 60 / entry['negative_seconds'] if entry['negative_seconds'] else None,
                                 negative_alert_span_seconds=seconds(intersection(active, negative)),
                                 positive_alert_span_seconds=seconds(intersection(active, positive))))
            for threshold in (.5, .3):
                tp = fp = fn = count = positives = 0
                for frame in labels['frames']:
                    truth = scorable_objects(frame, kind)
                    if truth is None:
                        continue
                    prediction = [b for b in by_frame[frame['frame_index']] if b['class'] == kind]
                    a, b, c = score_heads(truth, prediction, threshold)
                    tp += a; fp += b; fn += c; count += 1; positives += bool(truth)
                spot_checks.append(dict(clip_id=clip['clip_id'], kind=kind, iou_threshold=threshold,
                                        frames=count, positive_frames=positives, TP=tp, FP=fp, FN=fn))
    overall = {}
    for kind in ('fire', 'smoke'):
        overall[kind] = {}
        for policy in ('raw', 'legacy', 'fixed_2hz', 'timed', 'application'):
            selected = [r for r in rows if r['kind'] == kind and r['policy'] == policy]
            sums = {k: sum(r[k] for r in selected) for k in ('TP', 'FP', 'FN', 'negative_seconds', 'positive_seconds',
                    'reviewed_seconds', 'coverage_seconds', 'negative_scene_false_events', 'excluded_predictions',
                    'negative_alert_span_seconds', 'positive_alert_span_seconds')}
            sums.update(event_recall=sums['TP'] / (sums['TP'] + sums['FN']) if sums['TP'] + sums['FN'] else None,
                        unmatched_events_per_negative_minute=sums['FP'] * 60 / sums['negative_seconds'] if sums['negative_seconds'] else None,
                        negative_scene_false_events_per_minute=sums['negative_scene_false_events'] * 60 / sums['negative_seconds'] if sums['negative_seconds'] else None)
            if policy != 'application':
                assert all(sums[k] == benchmark['per_capability'][kind]['policies'][policy][k] for k in ('TP', 'FP', 'FN'))
            overall[kind][policy] = sums
    confidences = {}
    for kind in ('fire', 'smoke'):
        selected = [r for r in frame_stats if r['kind'] == kind]
        confidences[kind] = {}
        for state in ('positive', 'negative'):
            confidences[kind][state + '_interval_boxes'] = sum(r[state + '_box_count'] for r in selected)
            confidences[kind][state + '_interval_max_confidence'] = max(
                (r[state + '_max_confidence'] for r in selected if r[state + '_max_confidence'] is not None), default=None)
    (HERE / 'confidence-observations.json').write_text(json.dumps(confidences, indent=2) + '\n')
    result = dict(checkpoint_sha256=REGISTRY['fire_smoke']['sha256'], manifest_sha256=file_sha256(manifest),
                  analyzed_frames=total_frames, clips=len(clips), overall=overall, per_clip=rows,
                  raw_frame_stats=frame_stats, object_spot_checks=spot_checks, application_events=app_events,
                  provenance=dict(code_hashes={p: file_sha256(ROOT / p) for p in ('backend/pipeline.py', 'temporal.py')},
                                  analysis_sha256=file_sha256(__file__)),
                  training_started=False, gate_passed=False)
    (HERE / 'metrics.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    columns = ['clip_id', 'kind', 'policy', 'TP', 'FP', 'FN', 'event_recall', 'negative_seconds',
               'negative_scene_false_events', 'negative_scene_false_events_per_minute', 'positive_alert_span_seconds', 'positive_seconds']
    with (HERE / 'per-clip.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore', lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps(dict(clips=len(clips), analyzed_frames=total_frames, overall=overall), indent=2))


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check()
        print('Analysis self-check passed: interval edges, partial labels, draft boxes and excluded predictions.')
    else:
        main()
