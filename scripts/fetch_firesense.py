"""Download selected FIRESENSE clips using HTTP ranges instead of full archives."""
import io
import json
import zipfile
from pathlib import Path
import requests


class RemoteZip(io.RawIOBase):
    def __init__(self, url):
        self.url, self.position = url, 0
        response = requests.get(url, headers={"Range": "bytes=0-0"}, timeout=30)
        response.raise_for_status()
        if response.status_code != 206:
            raise RuntimeError("Server must support HTTP Range requests")
        self.size = int(response.headers["Content-Range"].split("/")[-1])

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        return self.position

    def read(self, size=-1):
        end = self.size - 1 if size < 0 else min(self.size - 1, self.position + size - 1)
        if end < self.position:
            return b""
        response = requests.get(self.url, headers={"Range": f"bytes={self.position}-{end}"}, timeout=120)
        response.raise_for_status()
        if response.status_code != 206 or len(response.content) != end - self.position + 1:
            raise RuntimeError("Invalid partial response")
        self.position += len(response.content)
        return response.content


def fetch(archive, members):
    url = f"https://zenodo.org/records/836749/files/{archive}"
    folder = Path("data/cctv/firesense")
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RemoteZip(url)) as z:
        if not members:
            print(json.dumps([dict(name=f.filename, size=f.file_size) for f in z.infolist()], indent=2))
        for name in members:
            output = folder / (archive.split('_')[0] + '_' + name.replace('/', '_'))
            if not output.exists():
                output.write_bytes(z.read(name))  # zipfile validates CRC before returning
            print(output, flush=True)


if __name__ == "__main__":
    import sys
    fetch(sys.argv[1], sys.argv[2:])
