import io
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import patch
from scripts.fetch_firesense import RemoteZip


class RangeZipCheck(unittest.TestCase):
    def test_partial_archive_reads(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("sample.txt", "range check")
        payload = buffer.getvalue()

        def response(url, headers, timeout):
            start, end = map(int, headers["Range"][6:].split("-"))
            return SimpleNamespace(status_code=206,
                                   headers={"Content-Range": f"bytes {start}-{end}/{len(payload)}"},
                                   content=payload[start:end + 1], raise_for_status=lambda: None)

        with patch("scripts.fetch_firesense.requests.get", side_effect=response):
            with zipfile.ZipFile(RemoteZip("https://example.invalid/test.zip")) as z:
                self.assertEqual(z.read("sample.txt"), b"range check")
