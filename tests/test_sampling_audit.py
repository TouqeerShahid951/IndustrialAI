import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from scripts.time_sampling_audit import audit


class SamplingAuditChecks(unittest.TestCase):
    def test_models_do_not_share_detections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'reports').mkdir()
            (root/'summary.json').write_text(json.dumps([
                dict(source='clip.mp4',model=model,frames=5,stride=1) for model in ('fire_smoke','helmet')]))
            with (root/'detections.csv').open('w',newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['source','model','frame','class','x1','y1','x2','y2'])
                for index in range(5):
                    writer.writerow(['clip.mp4','fire_smoke',index,'fire',0,0,10,10])
            previous = Path.cwd()
            try:
                os.chdir(root)
                with patch('cv2.VideoCapture',return_value=Mock(get=Mock(return_value=2))):
                    result = audit([root])
            finally:
                os.chdir(previous)
            self.assertTrue(any(row['confirmed'] for row in result if row['model']=='fire_smoke'))
            self.assertFalse(any(row['confirmed'] for row in result if row['model']=='helmet'))
