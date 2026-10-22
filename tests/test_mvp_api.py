import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from backend.app import create_app
from backend.auth import configure


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        configure(self.root, 'test-password-1234')
        self.client = TestClient(create_app(self.root))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def login(self):
        response = self.client.post('/api/session', json={'password': 'test-password-1234'})
        self.assertEqual(response.status_code, 200)
        return {'X-CSRF-Token': response.json()['csrf']}

    def test_auth_csrf_origin_logout(self):
        self.client.cookies.clear()
        for path in ['/api/uploads', '/api/jobs/unknown', '/api/artifacts/unknown']:
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post('/api/session', json={'password': 'wrong'}).status_code, 401)
        headers = self.login()
        self.assertEqual(self.client.get('/api/uploads').status_code, 200)
        self.assertEqual(self.client.post('/api/uploads', content=b'bad').status_code, 403)
        self.assertEqual(self.client.post('/api/uploads', content=b'bad', headers={**headers, 'Origin': 'https://evil.example'}).status_code, 403)
        self.assertEqual(self.client.delete('/api/session', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/uploads').status_code, 401)

    def test_invalid_session_and_rate_limit(self):
        self.client.cookies.set('industrial_session', 'tampered')
        self.assertEqual(self.client.get('/api/uploads').status_code, 401)
        for _ in range(12):
            response = self.client.post('/api/session', json={'password': 'wrong'})
        self.assertEqual(response.status_code, 429)
