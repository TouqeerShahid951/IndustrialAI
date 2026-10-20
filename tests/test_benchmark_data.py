import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.benchmark_data import load_manifest, validate_manifest, freeze_test, check_test_lock


class ManifestChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def clip(self, name='one', split='development'):
        media = self.root / f'{name}.avi'
        media.write_bytes(name.encode())
        labels = self.root / f'{name}.json'
        labels.write_text(json.dumps({'review_status': 'independent_reviewed',
                                     'events': [{'kind': 'smoke', 'start_seconds': 10, 'end_seconds': 20, 'review_status': 'reviewed'}],
                                     'reviewed_intervals': {'smoke': [[0, 30]]}, 'frames': []}))
        return dict(clip_id=name, local_path=str(media), annotation_path=str(labels),
                    source_sha256=hashlib.sha256(media.read_bytes()).hexdigest(),
                    camera_id='camera-'+name, site_id='site-'+name, source_event_id='event-'+name,
                    split=split, capture_origin='verified_cctv', permission_status='evaluation_allowed',
                    duration_seconds=30, conditions=['daylight'])

    def test_manifest_paths_hashes_and_annotations(self):
        clip = self.clip()
        self.assertEqual(validate_manifest([clip]), [])
        relative = dict(clip, local_path='one.avi', annotation_path='one.json')
        manifest = self.root/'manifest.jsonl'
        manifest.write_text(json.dumps(relative)+'\n')
        self.assertEqual(load_manifest(manifest)[0]['local_path'], str(Path(clip['local_path']).resolve()))
        for changed in (dict(clip, source_sha256='0'*64), dict(clip, local_path=str(self.root/'absent')),
                        dict(clip, duration_seconds=float('nan')), dict(clip, permission_status='not_allowed')):
            with self.subTest(changed=changed):
                self.assertTrue(validate_manifest([changed]))
        annotations = json.loads(Path(clip['annotation_path']).read_text())
        annotations['events'][0]['end_seconds'] = 31
        Path(clip['annotation_path']).write_text(json.dumps(annotations))
        self.assertTrue(validate_manifest([clip]))

    def test_group_leakage_and_duplicates(self):
        a, b = self.clip('a'), self.clip('b', 'validation')
        self.assertEqual(validate_manifest([a, b]), [])
        for field in ('source_sha256', 'camera_id', 'site_id', 'source_event_id', 'clip_id'):
            with self.subTest(field=field):
                changed = dict(b, **{field:a[field]})
                self.assertTrue(validate_manifest([a, changed]))
        self.assertTrue(validate_manifest([a, copy.deepcopy(a)]))

    def test_locked_test_quality_and_lock_changes(self):
        clip = self.clip(split='locked_test')
        self.assertTrue(validate_manifest([dict(clip, capture_origin='unverified_demo')]))
        self.assertTrue(validate_manifest([dict(clip, conditions=['source_overlays'])]))
        labels = Path(clip['annotation_path'])
        original = labels.read_text()
        labels.write_text(original.replace('independent_reviewed','single_reviewer'))
        self.assertTrue(validate_manifest([clip]))
        labels.write_text(original)
        lock = self.root/'lock.json'
        freeze_test([clip], lock)
        self.assertEqual(check_test_lock([clip], lock), [])
        labels.write_text(original+'\n')
        self.assertTrue(check_test_lock([clip], lock))
        with self.assertRaises(ValueError):
            freeze_test([self.clip('dev')], lock)

    def test_malformed_rows_and_frame_labels_are_reported(self):
        for bad in (None, {}, {'clip_id': []}):
            self.assertTrue(validate_manifest([bad]))
        clip = self.clip()
        labels = Path(clip['annotation_path'])
        data = json.loads(labels.read_text())
        data['frames'] = [{'time_seconds': 1, 'objects': [{'class': 'banana', 'bbox_xyxy':[10, 0, 0, 5]}]}]
        labels.write_text(json.dumps(data))
        self.assertTrue(validate_manifest([clip]))
        malformed = self.root/'bad.jsonl'
        malformed.write_text('{broken}\n')
        with self.assertRaisesRegex(ValueError, 'line 1'):
            load_manifest(malformed)

    def test_unreviewed_labels_and_invalid_exclusion_kinds_rejected(self):
        clip = self.clip()
        path = Path(clip['annotation_path'])
        labels = json.loads(path.read_text())
        labels['review_status'] = 'unreviewed'
        path.write_text(json.dumps(labels))
        self.assertTrue(validate_manifest([clip]))
        labels['review_status'] = 'single_reviewer'
        labels['excluded_intervals'] = [dict(kind='banana',start_seconds=0,end_seconds=1,reason='ambiguous')]
        path.write_text(json.dumps(labels))
        self.assertTrue(validate_manifest([clip]))
