import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import torch
from tests.test_mvp_media import video
from backend.pipeline import run_detection_pass


class TrackingTests(unittest.TestCase):
    def test_explicit_bytetrack_and_fresh_upload_state(self):
        calls=[]
        class Model:
            def __init__(self): self.frame=0
            def track(self,image,**options):
                calls.append(options)
                self.frame+=1
                box=SimpleNamespace(cls=torch.tensor(0),conf=torch.tensor(.9),xyxy=torch.tensor([[5,5,100,110]]),id=torch.tensor(self.frame))
                class Boxes(list):
                    def cpu(self):return self
                return [SimpleNamespace(boxes=Boxes([box]),names={0:'person'},keypoints=SimpleNamespace(data=torch.zeros((1,17,3))))]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source.mp4';video(source,3)
            with patch('backend.pipeline.load_model',side_effect=lambda *a:(Model(),{'sha256':'fixture','classes':{'person':'person'}})):
                for n in range(2):
                    output=root/f'{n}.jsonl'
                    run_detection_pass(source,output,'pose','cpu',lambda *a:None,lambda:False)
                    rows=[json.loads(line) for line in output.read_text().splitlines()]
                    self.assertEqual(rows[0]['boxes'][0]['track'],1)
        self.assertTrue(all(c['persist'] and c['tracker']=='bytetrack.yaml' for c in calls))
