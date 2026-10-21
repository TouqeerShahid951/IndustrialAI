import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.test_mvp_media import video
from backend.storage import Store
from backend.worker import Worker
from backend.pipeline import run_detection_pass
from backend.media import Cancelled


class FakeBoxes:
    def cpu(self): return self
    def __iter__(self): return iter([])


class FakeModel:
    def predict(self, *args, **kwargs):
        return [type('Result', (), {'boxes': FakeBoxes(), 'names': {0:'smoke'}})()]


class WorkerTests(unittest.TestCase):
    def test_full_source_and_cancel(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/'source.mp4'
            video(source,301,30)
            frames=[]
            with patch('backend.pipeline.load_model', return_value=(FakeModel(),{'sha256':'fixture'})):
                result=run_detection_pass(source,root/'raw.jsonl','fire_smoke','cpu',lambda stage,n,total:frames.append(n),lambda:False)
                self.assertEqual(result['frames'],301)
                self.assertEqual(len((root/'raw.jsonl').read_text().splitlines()),301)
                with self.assertRaises(Cancelled):
                    run_detection_pass(source,root/'cancel.jsonl','fire_smoke','cpu',lambda *args:None,lambda:True)

    def test_worker_exclusion_failure_and_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp)
            first=Worker(store)
            with self.assertRaises(RuntimeError):
                Worker(store)
            upload=store.add_upload('missing.mp4','missing.mp4','hash',1,{'duration':2})
            job=store.create_job(upload['id'],'prepare_upload',{},'one')
            first.run_once()
            self.assertEqual(store.job(job['id'])['status'],'failed')
            first.close()
            next_job=store.create_job(upload['id'],'prepare_upload',{},'two')
            store.claim()
            second=Worker(store)
            self.assertEqual(store.job(next_job['id'])['status'],'interrupted')
            second.close()
