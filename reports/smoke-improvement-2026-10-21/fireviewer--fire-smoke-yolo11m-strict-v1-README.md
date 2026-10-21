---
license: agpl-3.0
pipeline_tag: object-detection
datasets:
- fireviewer/fire-smoke-detection-corpus-v1
tags:
- fireviewer
- fire
- smoke
- wildfire
- yolo11
- object-detection
- onnx
library_name: ultralytics
---

# FireViewer YOLO11-M strict v1

## Quick card

| Field | Reference |
| --- | --- |
| Use | Use the retained visible smoke/flame baseline as a preannotation helper. |
| Expected input | Images with the exact Ultralytics configuration and matching labels. |
| Example | An image → scored smoke/flame boxes, then human review. |
| Limits | Weak flame AP and recall; no pointing qualification. Upstream AGPL / enterprise terms remain applicable. |
| Contract | [Pinned artifact access](#reproducibility-and-artifact-access) · [Evaluation protocol](#independent-evaluation-protocol-and-limits) |

[Choose a variant](https://huggingface.co/spaces/fireviewer/README/blob/main/docs/CHOOSING_VARIANTS.md) · [Resource navigation](https://huggingface.co/spaces/fireviewer/README/blob/main/docs/RESOURCE_INDEX.md) · [Update log](CHANGELOG.md)

Reproducible two-class visible smoke/flame baseline trained on the strict-clean FireViewer detection corpus.

## Status

**Reference baseline.** Retained independent benchmark results:

| Metric | Result |
|---|---:|
| COCO mAP50-95 | 0.1491 |
| COCO mAP50 | 0.2784 |
| Smoke AP50-95 | 0.2790 |
| Flame AP50-95 | 0.0193 |
| Holdout precision / recall / F1 | 0.4274 / 0.2488 / 0.3145 |
| Negative-image false-alarm rate | 0.3391 |

Its weak flame AP and recall are explicitly documented; this checkpoint is retained as a reproducible iteration artifact with documented use as a local preannotation helper. It is not a qualified pointing model.

## Rights

Ultralytics code and models are distributed under **AGPL-3.0** unless covered by a separate Ultralytics enterprise licence. Do **not** add the FireViewer non-redistribution checkpoint licence to this repository unless an upstream commercial licence and rights analysis expressly support it.

Training-source rights and attribution remain separately applicable.

## Reproducibility and artifact access

```python
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="fireviewer/fire-smoke-yolo11m-strict-v1",
    repo_type="model",
    revision="065979cd2300c27eeb355ab1e1524d8223d0b276",
    filename="model.pt",
)
```
Hub artifact SHA-256 for `model.pt`: `4428ee4c17980d8f1995bbe624a593f63326ead85ec76f2f0cd480195bab2a4d`. This identity was read from Hub metadata; the weights were not downloaded or rehashed during the documentation review.

The example downloads a pinned artifact; it does not execute or qualify inference. Preserve the matching configuration, labels, preprocessing and runtime dependencies from that revision. Keep raw outputs, scores, model revision and source provenance when integrating with `fireviewer-vision-runtime`.

Training corpus: `fireviewer/fire-smoke-detection-corpus-v1` at `8e3cb52e86e15debdff7d37a3ce9eac39fbe1835` (see [run receipt](run-receipt.json) and [source manifest](provenance/source-manifest.json)). Base recipe and implementation are recorded with the training artifacts; a family name alone is not an immutable upstream revision.

The included [inference helper](inference.py) consumes an RGB image and returns class ID/name, confidence and `xyxy` image boxes; its documented image size is 960. `--confidence 0.25` is the helper default, not a calibrated deployment threshold.

## Independent evaluation protocol and limits

[Published independent report](benchmark/independent-evaluation.json): 512 images from `Hajorda/flameye-wildfire-detection`, `test`, revision `361a3dea8b877482af9f4ed80eff77ffd39926ef`. The retained common protocol uses 129 calibration images and 383 holdout images; its selection is dominated by D-Fire (508/512). Zero exact training overlap is a reported hash-based check, not proof of no semantic or domain overlap.

Evaluated model revision: `a75aa44716658f02eb85b4e7bba6a358040e6f86`. The report-calibrated score threshold is **0.1**; it is specific to this protocol and is **not an operational threshold**. COCO AP over the 512-image selection and F1 on the calibrated holdout are different measurements. Do not compare them with RF-DETR training-validation scores or DINOv3 pointing metrics.

The report does not contain an explicit execution timestamp. Its original revision is the evidence reference; a documentation review date is not a new evaluation date. Multi-event and multi-camera external validation remains necessary.

Sensitive results require human validation. No image detection establishes geographic coordinates, a measured perimeter, absence of fire or future propagation.

## Documentation and revision

Card updated in English on **5 October 2026**, from the public repository at
[`065979cd2300c27eeb355ab1e1524d8223d0b276`](https://huggingface.co/fireviewer/fire-smoke-yolo11m-strict-v1/tree/065979cd2300c27eeb355ab1e1524d8223d0b276) and its retained reports.
This update checks documentation, repository metadata and small evidence files;
it does not rerun training, inference, dataset payload verification or device qualification.
Historical receipts keep their original dates, revisions and scope. Earlier README
hashes in artifact manifests refer to those earlier releases.

The association FIRE-VIEWER provides administrative and financial stewardship for
resources under its control. Technical governance is maintainer-led. Upstream,
source-specific and pre-association rights remain separate; repository placement
does not transfer ownership or grant additional rights.

[Project documentation](https://github.com/fireviewer/Fireviewer_doc/blob/main/docs/public/HUGGINGFACE.md)
· [Institutional website](https://fire-viewer.fr). Contact: **contact@fire-viewer.fr**.

**Likes are always welcome! ❤️** If these resources help you, a little heart makes our day and helps others discover the work. Thank you!
