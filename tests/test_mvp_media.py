import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from tests.test_mvp_api import APITests
from backend.media import prepare_preview, source_to_preview


def video(path, frames=35, fps=10):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (160, 120))
    for i in range(frames):
        frame = np.full((120,160,3), i % 255, np.uint8)
        writer.write(frame)
    writer.release()


class MediaTests(APITests):
    def upload(self):
        path = self.root/'fixture.mp4'
        video(path)
        return self.client.post('/api/uploads', content=path.read_bytes(), headers={**self.login(), 'X-Upload-Name': '../../clip.mp4'})

    def test_invalid_and_oversize_cleanup(self):
        headers = self.login()
        response = self.client.post('/api/uploads', content=b'not video', headers={**headers, 'X-Upload-Name': 'fake.mp4'})
        self.assertEqual(response.status_code, 422)
        with patch('backend.media.MAX_BYTES', 10):
            response = self.client.post('/api/uploads', content=b'12345678901', headers={**headers, 'X-Upload-Name': 'clip.mp4'})
            self.assertEqual(response.status_code, 413)
        self.assertFalse(list((self.root/'media').glob('*.part')))

    def test_preview_mapping_ranges_and_private_access(self):
        response = self.upload()
        self.assertEqual(response.status_code, 202, response.text)
        upload = response.json()
        store = self.client.app.state.store
        record = store.upload(upload['upload_id'])
        self.assertEqual(record['name'], 'clip.mp4')
        result = prepare_preview(store, record, lambda *args: None, lambda: False)
        self.assertEqual(len(result['frame_map']), 35)
        self.assertAlmostEqual(source_to_preview(1.7, result['frame_map']), 1.7)
        url = '/api/artifacts/'+result['preview_id']
        self.assertEqual(self.client.get(url, headers={'Range':'bytes=0-9'}).status_code, 206)
        self.assertEqual(self.client.get(url, headers={'Range':'bytes=999999999-'}).status_code, 416)
        self.client.cookies.clear()
        self.assertEqual(self.client.get(url, headers={'Range':'bytes=0-9'}).status_code, 401)

    def test_irregular_source_mapping(self):
        mapping = [[0,0],[.04,.1],[.2,.2],[.25,.3]]
        self.assertAlmostEqual(source_to_preview(.2,mapping), .2)
        self.assertAlmostEqual(source_to_preview(.12,mapping), .15)
