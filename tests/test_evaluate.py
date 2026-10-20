"""Run with: python -m unittest discover -s tests"""
import tempfile
import unittest
import csv
import json
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from evaluate import evaluate, media_files


class EvaluationChecks(unittest.TestCase):
    def test_media_discovery_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "nested").mkdir()
            image = root / "nested" / "frame.JPG"
            image.touch()
            (root / "ignore.txt").touch()
            self.assertEqual(media_files(root), [image])
            for kwargs in ({"stride": 0}, {"conf": 0}, {"conf": float("nan")},
                           {"max_frames": 0}, {"models": ["unknown"]}, {"models": []}):
                with self.assertRaises(ValueError):
                    evaluate(root, **kwargs)
            with self.assertRaises(ValueError):
                media_files(root / "missing")

    def test_checkpoint_requires_one_model_and_existing_file(self):
        with self.assertRaises(ValueError):
            evaluate("unused", models=["fire_smoke", "helmet"], checkpoint="missing.pt")
        with self.assertRaises(ValueError):
            evaluate("unused", models=["fire_smoke"], checkpoint="missing.pt")

    def test_image_video_and_csv_with_fake_detector(self):
        import cv2
        import numpy as np
        from unittest.mock import MagicMock
        box = SimpleNamespace(cls=np.array(0), conf=np.array(0.9),
                              xyxy=np.array([[1, 2, 10, 12]]))
        boxes = MagicMock()
        boxes.cpu.return_value = [box]
        result = SimpleNamespace(boxes=boxes, names={0: "fire"},
                                 plot=lambda: np.zeros((32, 32, 3), dtype=np.uint8))
        model = MagicMock()
        model.predict.return_value = [result]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = root / "inputs"
            inputs.mkdir()
            self.assertTrue(cv2.imwrite(str(inputs / "sample.jpg"), result.plot()))
            video = cv2.VideoWriter(str(inputs / "sample.avi"),
                                    cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 32))
            self.assertTrue(video.isOpened())
            for _ in range(5):
                video.write(result.plot())
            video.release()
            weights = root / "fake.pt"
            weights.write_bytes(b"test checkpoint")
            with patch("huggingface_hub.hf_hub_download", return_value=str(weights)), \
                 patch("ultralytics.YOLO", return_value=model):
                run = evaluate(inputs, output=root / "outputs", models=["fire_smoke"],
                               stride=2, max_frames=2)
            summary = json.loads((run / "summary.json").read_text())
            self.assertEqual([row["frames"] for row in summary], [2, 1])
            with (run / "frames.csv").open() as handle:
                observations = list(csv.DictReader(handle))
            self.assertEqual(len(observations), 3)
            self.assertEqual([float(r['source_seconds']) for r in observations], [0,.2,0])
            metadata = json.loads((run / 'metadata.json').read_text())
            self.assertEqual(metadata['status'], 'complete')
            self.assertEqual(len(metadata['checkpoints']['fire_smoke']['sha256']), 64)
            self.assertEqual(set(metadata['artifacts']), {'detections.csv','frames.csv','summary.json'})
            model.predict.side_effect = RuntimeError('inference unavailable')
            with patch("huggingface_hub.hf_hub_download", return_value=str(weights)), patch("ultralytics.YOLO", return_value=model):
                with self.assertRaises(RuntimeError):
                    evaluate(inputs, output=root / 'failed', models=['fire_smoke'])
            failed = next((root/'failed').glob('run-*/metadata.json'))
            self.assertNotEqual(json.loads(failed.read_text())['status'], 'complete')
            with (run / "detections.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertEqual([row["frame"] for row in rows], ["0", "2", "0"])
            self.assertTrue(list(run.rglob("*.jpg")))
            annotated = next(run.rglob("*.mp4"))
            cap = cv2.VideoCapture(str(annotated))
            self.assertTrue(cap.read()[0])
            cap.release()


if __name__ == "__main__":
    unittest.main()
