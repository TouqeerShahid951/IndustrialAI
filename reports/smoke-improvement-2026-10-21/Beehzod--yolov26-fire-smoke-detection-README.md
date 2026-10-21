---
license: cc-by-4.0
library_name: ultralytics
pipeline_tag: object-detection
base_model: "yolov26-fire-detection"
tags:
  - yolo
  - yolov26
  - fire-detection
  - smoke-detection
  - object-detection
  - ultralytics
model-index:
  - name: yolov26-fire-smoke-detection
    results:
      - task:
          type: object-detection
        metrics:
          - name: mAP50
            type: mAP
            value: 0.9177
          - name: mAP50-95
            type: mAP
            value: 0.8299
          - name: precision
            type: precision
            value: 0.9167
          - name: recall
            type: recall
            value: 0.8958
---

# yolov26-fire-smoke-detection

Fine-tuned from [`yolov26-fire-detection`](https://huggingface.co/'yolov26-fire-detection') (YOLOv26-S) using [Ultralytics](https://github.com/ultralytics/ultralytics).

## Classes

- `Fire`
- `Smoke`

## Dataset


- Images: 7673 train / 925 valid / 960 test
- Check the dataset page above for its license -- not necessarily the same as this repo's `license` field, which reflects the base model's license.

## Training

| Parameter | Value |
|---|---|
| Epochs | 100 |
| Image size | 640 |
| Batch size | 16 |
| Optimizer | AdamW |
| Initial LR (lr0) | 0.001 |
| Patience (early stop) | 20 |

## Results (held-out validation split)

| Metric | Value |
|---|---|
| mAP50 | 0.9177 |
| mAP50-95 | 0.8299 |
| Precision | 0.9167 |
| Recall | 0.8958 |

## Usage

```python
from ultralytics import YOLO

model = YOLO("best.pt")
results = model.predict("image.jpg", conf=0.25)
for r in results:
    for box in r.boxes:
        print(model.names[int(box.cls[0])], float(box.conf[0]))
```
