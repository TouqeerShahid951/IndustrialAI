import tempfile
import unittest
from pathlib import Path

from backend.storage import Store


class StorageTests(unittest.TestCase):
    def test_persistence_idempotency_and_single_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            upload = store.add_upload('clip.mp4', 'source.mp4', 'abc', 30, {'duration': 3})
            job = store.create_job(upload['id'], 'analyze', {'capabilities': ['smoke']}, 'request-1')
            same = store.create_job(upload['id'], 'analyze', {'capabilities': ['smoke']}, 'request-1')
            self.assertEqual(job['id'], same['id'])
            with self.assertRaises(ValueError):
                store.create_job(upload['id'], 'analyze', {'capabilities': ['fire']}, 'request-1')
            self.assertEqual(Store(root).job(job['id'])['status'], 'queued')
            self.assertEqual(store.claim()['id'], job['id'])
            self.assertIsNone(Store(root).claim())
            store.recover()
            self.assertEqual(store.job(job['id'])['status'], 'interrupted')

