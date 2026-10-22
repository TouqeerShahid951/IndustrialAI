"""Verify this annotation batch against local footage and reviewed frame evidence."""
import json
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
from benchmark_data import file_sha256, load_manifest, validate_manifest
import cv2
from PIL import Image


def verify():
    clips = load_manifest(HERE / 'manifest.jsonl')
    errors = validate_manifest(clips)
    assert not errors, errors
    assert len(clips) == 23
    evidence = {r['clip_id']: r for r in json.loads((HERE / 'review-evidence.json').read_text())}
    counts = Counter(clips=len(clips))
    for c in clips:
        a = json.loads(Path(c['annotation_path']).read_text())
        assert a['review_status'] == 'single_reviewer' and not a['human_confirmed']
        assert c['split'] == 'development' and a['training_admission'] == 'not_admitted'
        assert a['source_sha256'] == c['source_sha256']
        assert a['duration_seconds'] == c['duration_seconds']
        e = evidence[c['clip_id']]
        assert file_sha256(e['review_sheet_path']) == e['review_sheet_sha256']
        samples = {r['frame_index']: r for r in e['samples']}
        for r in samples.values():
            assert file_sha256(r['path']) == r['image_sha256']
            with Image.open(r['path']) as im:
                assert im.size == (r['width'], r['height'])
        counts['review_samples'] += len(samples)
        for kind in ('fire', 'smoke'):
            windows = a['reviewed_intervals'][kind] + [
                [x['start_seconds'], x['end_seconds']]
                for x in a['excluded_intervals'] if x['kind'] == kind]
            cursor = 0
            for start, end in sorted(windows):
                assert abs(start - cursor) < 1e-6, (c['clip_id'], kind, 'gap/overlap')
                cursor = end
            assert abs(cursor - c['duration_seconds']) < 1e-6
            counts[f'{kind}_{a["assessment"][kind]}'] += 1
        assert len(a['frames']) == 3
        selected = {f['frame_index']: f for f in a['frames']}
        cap = cv2.VideoCapture(c['local_path'])
        frame_index = 0
        while frame_index <= max(selected):
            ok, source_frame = cap.read()
            assert ok, (c['clip_id'], frame_index, 'source decode failed')
            if frame_index in selected:
                f = selected[frame_index]
                pts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                assert abs(pts - f['time_seconds']) < 1e-6
                ok, jpeg = cv2.imencode('.jpg', source_frame, [cv2.IMWRITE_JPEG_QUALITY, 96])
                assert ok and hashlib.sha256(jpeg.tobytes()).hexdigest() == f['image_sha256']
                counts['source_frame_checks'] += 1
            frame_index += 1
        cap.release()
        for f in a['frames']:
            r = samples[f['frame_index']]
            assert f['time_seconds'] == r['time_seconds']
            assert f['image_sha256'] == r['image_sha256']
            assert f['image_path'] == r['path']
            assert Path(f['annotated_image_path']).is_file()
            for kind, state in f['class_assessment'].items():
                positive = any(x['kind'] == kind and x['start_seconds'] <= f['time_seconds'] < x['end_seconds'] for x in a['events'])
                assert (state == 'present') == positive
            if f['review_status'] == 'reviewed':
                assert 'uncertain' not in f['class_assessment'].values()
                for kind, state in f['class_assessment'].items():
                    assert (state == 'present') == any(o['class'] == kind for o in f['objects'])
            counts['sparse_frames'] += 1
            counts[f'frames_{f["review_status"]}'] += 1
            for obj in f['objects']:
                assert f['class_assessment'][obj['class']] == 'present'
                counts[f'{obj["class"]}_boxes'] += 1
                counts[f'boxes_{obj["review_status"]}'] += 1
    assert counts['review_samples'] == 492 and counts['sparse_frames'] == 69
    result = {'valid': True, 'manifest_sha256': file_sha256(HERE / 'manifest.jsonl'),
              'counts': dict(counts), 'all_clips_development_only': True,
              'training_started': False}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
