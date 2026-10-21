---
license: other
pipeline_tag: object-detection
base_model: PekingU/rtdetr_v2_r50vd
datasets:
- fireviewer/fire-smoke-detection-corpus-v1
tags:
- fireviewer
- fire
- smoke
- wildfire
- rtdetr-v2
- object-detection
library_name: transformers
license_name: fireviewer-model-use-license-v1.0
license_link: https://huggingface.co/fireviewer/rtdetr-v2-r50-fire-smoke/blob/b16bc79df05a69bfd90a7130d77fdbbd0d556465/CHECKPOINT_LICENSE.md
---

# FireViewer RT-DETRv2-R50 Fire/Smoke

## Quick card

| Field | Reference |
| --- | --- |
| Use | Inspect the historical visible smoke/flame reference detector. |
| Expected input | RGB images using the matching RT-DETR configuration and preprocessing. |
| Example | An image → scored visible smoke/flame boxes. |
| Limits | Recorded benchmark mAP is not current runtime promotion or geographic/fire-origin evidence. Checkpoint redistribution restrictions remain applicable. |
| Contract | [Pinned artifact access](#reproducibility-and-artifact-access) · [Evaluation protocol](#independent-evaluation-protocol-and-limits) |

[Choose a variant](https://huggingface.co/spaces/fireviewer/README/blob/main/docs/CHOOSING_VARIANTS.md) · [Resource navigation](https://huggingface.co/spaces/fireviewer/README/blob/main/docs/RESOURCE_INDEX.md) · [Update log](CHANGELOG.md)

Two-class visible smoke/flame detector based on `PekingU/rtdetr_v2_r50vd`.

## Status

**Conservative historical/reference detector.** On the retained independent FireViewer benchmark, COCO mAP50-95 is **0.3502**. It remains useful as a reproducible comparator and lower-false-alarm operating reference; public availability does not mean current runtime promotion.

## Intended use and limits

Research, evaluation and permitted commercial inference under the checkpoint terms. This model does not determine geographic coordinates, hidden fire origin, a fire perimeter or an emergency decision. Outputs must retain scores/provenance and remain subject to human review.

## Rights

The upstream base model is Apache-2.0. FireViewer checkpoint terms are separate from upstream code/base rights and from source-specific training-data rights. The [checkpoint licence](CHECKPOINT_LICENSE.md) permits the stated uses with attribution and does not grant redistribution, including converted or embedded weights. Read it alongside [rights and attribution](RIGHTS_AND_ATTRIBUTION.md) before reuse.

## Reproducibility and artifact access

```python
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="fireviewer/rtdetr-v2-r50-fire-smoke",
    repo_type="model",
    revision="b16bc79df05a69bfd90a7130d77fdbbd0d556465",
    filename="model.safetensors",
)
```
Hub artifact SHA-256 for `model.safetensors`: `75aa67a0ed2411d15fd14886932ab18ffa409666ac7b80bf285efb3224e083e0`. This identity was read from Hub metadata; the weights were not downloaded or rehashed during the documentation review.

The example downloads a pinned artifact; it does not execute or qualify inference. Preserve the matching configuration, labels, preprocessing and runtime dependencies from that revision. Keep raw outputs, scores, model revision and source provenance when integrating with `fireviewer-vision-runtime`.

Base revision: `282494075698cab9faa1096ae26856890030c817`. [Training provenance](training-provenance.json) retains historical source-manifest hashes; do not assume that the current strict corpus revision was used by this older training run. Labels are `0: smoke_visible`, `1: flame_visible`; use the matching [configuration](config.json) and [image processor](preprocessor_config.json).

## Recorded benchmark results

| Metric | Result |
| --- | ---: |
| COCO mAP50:95 | 0.3502 |
| COCO mAP50 | 0.6332 |
| Smoke / flame AP50:95 | 0.4544 / 0.2459 |
| Calibrated holdout precision / recall / F1 | 0.7385 / 0.4507 / 0.5598 |
| Calibrated holdout negative-image false-alarm rate | 0.0435 |

Values are rounded from the retained report. COCO AP and calibrated holdout
metrics cover different parts of the protocol described below.

## Independent evaluation protocol and limits

[Published independent report](benchmark/independent-evaluation.json): 512 images from `Hajorda/flameye-wildfire-detection`, `test`, revision `361a3dea8b877482af9f4ed80eff77ffd39926ef`. The retained common protocol uses 129 calibration images and 383 holdout images; its selection is dominated by D-Fire (508/512). Zero exact training overlap is a reported hash-based check, not proof of no semantic or domain overlap.

Evaluated model revision: `c177a12ccd9f0ed1c0ddadbc3e7ad2ac56ae0218`. The report-calibrated score threshold is **0.02**; it is specific to this protocol and is **not an operational threshold**. COCO AP over the 512-image selection and F1 on the calibrated holdout are different measurements. Do not compare them with RF-DETR training-validation scores or DINOv3 pointing metrics.

The report does not contain an explicit execution timestamp. Its original revision is the evidence reference; a documentation review date is not a new evaluation date. Multi-event and multi-camera external validation remains necessary.

Sensitive results require human validation. No image detection establishes geographic coordinates, a measured perimeter, absence of fire or future propagation.

## Documentation and revision

Card updated in English on **5 October 2026**, from the public repository at
[`b16bc79df05a69bfd90a7130d77fdbbd0d556465`](https://huggingface.co/fireviewer/rtdetr-v2-r50-fire-smoke/tree/b16bc79df05a69bfd90a7130d77fdbbd0d556465) and its retained reports.
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
