"""Validate local benchmark provenance, labels and split isolation (stdlib only)."""
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

KINDS = {'fire', 'smoke', 'smoking', 'no_helmet', 'restricted_entry'}
OBJECTS = {'fire', 'smoke', 'helmet', 'no_helmet', 'person', 'cigarette'}
SPLITS = {'development', 'validation', 'locked_test'}


def file_sha256(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def interval(pair, duration):
    _require(isinstance(pair, (list, tuple)) and len(pair) == 2 and all(number(v) for v in pair), 'invalid interval')
    _require(0 <= pair[0] < pair[1] <= duration, 'interval outside clip duration')


def load_manifest(path):
    path = Path(path).resolve()
    clips = []
    for index, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            clip = json.loads(line)
            _require(isinstance(clip, dict), 'row must be an object')
            for field in ('local_path', 'annotation_path'):
                if field in clip:
                    _require(isinstance(clip[field], str) and '://' not in clip[field], 'local file paths required')
                    clip[field] = str((path.parent / clip[field]).resolve())
            clips.append(clip)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'manifest line {index}: {exc}') from exc
    return clips


def _validate_labels(labels, duration, locked):
    _require(isinstance(labels, dict), 'annotation must be an object')
    status = labels.get('review_status')
    _require(status in ('single_reviewer', 'independent_reviewed', 'unreviewed'), 'annotation review_status required')
    _require(not locked or status == 'independent_reviewed', 'locked_test requires independent label review')
    reviewed = labels.get('reviewed_intervals', {})
    _require(isinstance(reviewed, dict), 'reviewed_intervals must be an object')
    _require(status != 'unreviewed' or not (any(reviewed.values()) or labels.get('events') or labels.get('frames')),
             'unreviewed annotations cannot contain scored labels or reviewed intervals')
    for kind, windows in reviewed.items():
        _require(kind in KINDS and isinstance(windows, list), 'invalid reviewed capability')
        for pair in windows:
            interval(pair, duration)
    for field in ('events', 'frames', 'excluded_intervals'):
        _require(isinstance(labels.get(field, []), list), f'{field} must be a list')
    for event in labels.get('events', []):
        _require(isinstance(event, dict) and event.get('kind') in KINDS, 'invalid event kind')
        interval([event.get('start_seconds'), event.get('end_seconds')], duration)
        _require(event.get('review_status') in ('reviewed', 'ambiguous'), 'event review_status required')
        if event['review_status'] == 'reviewed':
            start = event['start_seconds']
            for a, b in sorted(reviewed.get(event['kind'], [])):
                if a <= start <= b:
                    start = max(start, b)
            _require(start >= event['end_seconds'], 'event outside reviewed intervals')
    for item in labels.get('excluded_intervals', []):
        _require(isinstance(item, dict) and item.get('reason') in ('ambiguous', 'unmonitored'), 'invalid exclusion reason')
        _require('kind' not in item or item['kind'] in KINDS, 'invalid exclusion capability')
        interval([item.get('start_seconds'), item.get('end_seconds')], duration)
    for frame in labels.get('frames', []):
        _require(isinstance(frame, dict) and number(frame.get('time_seconds')), 'invalid frame time')
        _require(0 <= frame['time_seconds'] <= duration, 'frame outside clip')
        _require(frame.get('review_status') in ('reviewed', 'ambiguous'), 'frame review_status required')
        _require(isinstance(frame.get('objects'), list), 'frame objects required')
        if frame['objects']:
            _require(all(number(frame.get(k)) and frame[k] > 0 for k in ('image_width', 'image_height')), 'frame dimensions required')
        for obj in frame['objects']:
            _require(isinstance(obj, dict) and obj.get('class') in OBJECTS, 'invalid object class')
            box = obj.get('bbox_xyxy')
            _require(isinstance(box, list) and len(box) == 4 and all(number(x) for x in box), 'invalid object box')
            _require(0 <= box[0] < box[2] <= frame['image_width'] and 0 <= box[1] < box[3] <= frame['image_height'], 'object box outside frame')
    _require(not locked or any(reviewed.values()), 'locked_test requires reviewed time')


def validate_manifest(clips):
    if not isinstance(clips, list) or not clips:
        return ['manifest requires at least one clip']
    errors, seen = [], {k:{} for k in ('clip_id', 'source_sha256', 'camera_id', 'site_id', 'source_event_id')}
    for index, clip in enumerate(clips, 1):
        label = f'row {index}'
        try:
            _require(isinstance(clip, dict), 'clip must be an object')
            for field in ('clip_id', 'camera_id', 'site_id', 'source_event_id'):
                _require(isinstance(clip.get(field), str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', clip[field]), f'invalid {field}')
            label = clip['clip_id']
            _require(clip.get('split') in SPLITS, 'invalid split')
            _require(clip.get('capture_origin') in ('verified_cctv', 'research_capture', 'unverified_demo'), 'invalid capture_origin')
            _require(clip.get('permission_status') in ('evaluation_allowed', 'review_needed'), 'evaluation permission is missing or denied')
            _require(number(clip.get('duration_seconds')) and clip['duration_seconds'] > 0, 'invalid duration')
            _require(isinstance(clip.get('conditions'), list) and all(isinstance(x, str) for x in clip['conditions']), 'conditions must be a string list')
            locked = clip['split'] == 'locked_test'
            _require(not locked or (clip['capture_origin'] == 'verified_cctv' and clip['permission_status'] == 'evaluation_allowed' and 'source_overlays' not in clip['conditions']), 'locked_test requires verified clean CCTV and evaluation permission')
            for field in ('local_path', 'annotation_path'):
                _require(isinstance(clip.get(field), str) and '://' not in clip[field] and Path(clip[field]).is_file(), f'{field} must be an existing local file')
            _require(isinstance(clip.get('source_sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', clip['source_sha256']), 'invalid source_sha256')
            _require(file_sha256(clip['local_path']) == clip['source_sha256'], 'source hash mismatch')
            _validate_labels(json.loads(Path(clip['annotation_path']).read_text()), clip['duration_seconds'], locked)
            for field, groups in seen.items():
                previous = groups.get(clip[field])
                if previous is not None:
                    _require(field not in ('clip_id', 'source_sha256'), f'duplicate {field}')
                    _require(previous == clip['split'], f'{field} leakage across splits')
                groups[clip[field]] = clip['split']
        except (ValueError, TypeError, KeyError, OSError) as exc:
            errors.append(f'{label}: {exc}')
    return errors


def _test_fingerprint(clips):
    items = []
    for clip in sorted((c for c in clips if c['split'] == 'locked_test'), key=lambda c:c['clip_id']):
        item = {k:v for k,v in clip.items() if k not in ('local_path', 'annotation_path')}
        item['annotation_sha256'] = file_sha256(clip['annotation_path'])
        items.append(item)
    return hashlib.sha256(json.dumps(items, sort_keys=True, allow_nan=False).encode()).hexdigest()


def freeze_test(clips, path):
    errors = validate_manifest(clips)
    if errors or not any(c['split'] == 'locked_test' for c in clips):
        raise ValueError('; '.join(errors) or 'no locked_test clips to freeze')
    # Never overwrite an existing lock; check or deliberately create a new benchmark version.
    with Path(path).open('x') as handle:
        json.dump({'locked_test_sha256': _test_fingerprint(clips)}, handle, indent=2)


def check_test_lock(clips, path):
    errors = validate_manifest(clips)
    if errors:
        return errors
    try:
        if not any(c['split'] == 'locked_test' for c in clips):
            return ['no locked_test clips']
        expected = json.loads(Path(path).read_text())['locked_test_sha256']
        return [] if expected == _test_fingerprint(clips) else ['locked_test membership or labels changed']
    except (ValueError, KeyError, OSError) as exc:
        return [f'locked_test lock unavailable: {exc}']


def inventory(clips):
    return {'clips': len(clips), 'splits': dict(Counter(c['split'] for c in clips)),
            'duration_seconds': sum(c['duration_seconds'] for c in clips),
            'camera_groups': len({c['camera_id'] for c in clips}),
            'site_groups': len({c['site_id'] for c in clips}),
            'data_gaps': ['Clean, verified independent CCTV and independent labels required',
                          'No accepted operating targets or certified safety validation']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--freeze-test', type=Path)
    parser.add_argument('--check-lock', type=Path)
    args = parser.parse_args()
    try:
        clips = load_manifest(args.manifest)
        errors = validate_manifest(clips)
        if not errors and args.freeze_test:
            freeze_test(clips, args.freeze_test)
        if not errors and args.check_lock:
            errors = check_test_lock(clips, args.check_lock)
        report = {'valid': not errors, 'errors': errors, 'manifest_sha256': file_sha256(args.manifest)}
        if not errors:
            report['inventory'] = inventory(clips)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 1 if errors else 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'valid': False, 'errors': [str(exc)]}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
