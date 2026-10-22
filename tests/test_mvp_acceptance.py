import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.auth import configure
from backend.storage import Store
from backend.media import probe,capacity
from tests.test_mvp_media import video


class AcceptanceTests(unittest.TestCase):
    def test_cancel_is_atomic_with_claim_and_deletion_waits(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);configure(root,'password-12345')
            app=create_app(root);client=TestClient(app);store=app.state.store
            csrf=client.post('/api/session',json={'password':'password-12345'}).json()['csrf']
            upload=store.add_upload('fixture.mp4','fixture.mp4','x',1,{'duration':3})
            job=store.create_job(upload['id'],'prepare_upload',{},str(uuid4()))
            store.claim()
            cancelled=client.post('/api/jobs/'+job['id']+'/cancel',headers={'X-CSRF-Token':csrf})
            self.assertEqual(cancelled.json()['status'],'running')
            self.assertEqual(cancelled.json()['cancel'],1)
            self.assertEqual(client.delete('/api/uploads/'+upload['id'],headers={'X-CSRF-Token':csrf}).status_code,409)
            store.update_job(job['id'],status='cancelled')
            self.assertEqual(client.delete('/api/uploads/'+upload['id'],headers={'X-CSRF-Token':csrf}).status_code,200)

    def test_deleted_upload_cannot_accept_a_late_job(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder)
            upload=store.add_upload('fixture.mp4','fixture.mp4','x',1,{'duration':3})
            store.update_upload(upload['id'],'deleting')
            with self.assertRaises(ValueError):
                store.create_job(upload['id'],'analyze',{},str(uuid4()))

    def test_media_limits_and_disk_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fast.mp4';video(path,5,120)
            with self.assertRaises(ValueError):probe(path)
            with patch('backend.media.shutil.disk_usage',return_value=type('Usage',(),{'free':1})()):
                with self.assertRaises(OSError):capacity(folder)

    def test_logged_out_cookie_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);configure(root,'password-12345');app=create_app(root)
            client=TestClient(app);session=client.post('/api/session',json={'password':'password-12345'}).json()
            cookie=client.cookies.get('industrial_session')
            client.delete('/api/session',headers={'X-CSRF-Token':session['csrf']})
            client.cookies.set('industrial_session',cookie)
            self.assertEqual(client.get('/api/uploads').status_code,401)
            restarted=TestClient(create_app(root));restarted.cookies.set('industrial_session',cookie)
            self.assertEqual(restarted.get('/api/uploads').status_code,401)
