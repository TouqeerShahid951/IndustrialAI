---
tags:
- object-detection
- yolov8
- ultralytics
- fire-detection
- smoke-detection
- computer-vision
- pytorch
- onnx
library_name: ultralytics
pipeline_tag: object-detection
---

# YOLOv8 Fire & Smoke Detection

A YOLOv8s object detection model fine-tuned to detect **fire** and **smoke** in images and video, trained via transfer learning on a public Roboflow dataset. Built as part of a hands-on deep learning / object detection learning project — full pipeline from raw dataset to real-time webcam inference.

## Model Details

- **Base model:** `yolov8s.pt` (Ultralytics, pretrained on COCO)
- **Task:** Object Detection
- **Classes (2):** `fire`, `smoke`
- **Framework:** Ultralytics YOLOv8
- **Formats provided:** `best.pt` (PyTorch) and `best.onnx` (ONNX, for cross-platform/faster inference)

## Training Details

| Setting | Value |
|---|---|
| Base weights | yolov8s.pt (transfer learning) |
| Epochs | 20 |
| Image size | 416x416 |
| Batch size | 16 |
| Optimizer | AdamW (auto-selected) |
| Early stopping patience | 5 |
| Training environment | Google Colab (T4 GPU) |

## Dataset

Trained on the **Fire and Smoke Detection** dataset from Roboflow Universe (~5,957 images, 2 classes, pre-annotated in YOLO format).
Source: [Roboflow Universe](https://universe.roboflow.com/fire-detection-5id9d/fire-and-smoke-detection-0t7wg)

## Evaluation Metrics

| Metric | Score |
|---|---|
| mAP50 | 0.506 |
| mAP50-95 | 0.231 |
| Precision | 0.542 |
| Recall | 0.540 |

## Limitations

- Trained for only 20 epochs at reduced image size (416) as a first-pass proof of concept — confidence scores on real detections are moderate (~0.45–0.56), not yet production-grade.
- Confusion matrix shows the model rarely confuses fire vs smoke directly, but has a meaningful false positive/negative rate against "background" — meaning it sometimes misses real fire/smoke or flags none-existent detections in ambiguous scenes (e.g., motion blur, hazy lighting).
- Not trained on negative examples like humans, pets, or general indoor motion — may misclassify unrelated blurry/diffuse objects as smoke.
- For production use, retraining with more epochs (50+), full resolution (imgsz=640), and a broader negative-example dataset is recommended.

## Usage

```python
from ultralytics import YOLO

# load the model
model = YOLO("best.pt")  # or "best.onnx"

# run inference on an image
results = model.predict("your_image.jpg", conf=0.4)
results[0].show()
```

For real-time webcam inference:

```python
import cv2
from ultralytics import YOLO

model = YOLO("best.pt")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    results = model.predict(source=frame, conf=0.4, verbose=False)
    annotated = results[0].plot()
    cv2.imshow("Fire & Smoke Detection", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Author

Trained and documented as part of a self-directed deep learning learning journey — architecture theory, from-scratch math, full training pipeline, and real-time deployment.