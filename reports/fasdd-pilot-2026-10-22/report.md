# FASDD fire/smoke fine-tuning pilot — 22 October 2026

**Decision: reject this candidate and retain the application's pinned baseline.** The pilot suppresses one wall false alarm, but loses useful smoke detections and creates a new temporally verified fire false alarm. No application model, threshold, saved review or incident was changed.

## Data and training

Downloaded the 3,410,626,268-byte [FASDD_CV mirror](https://huggingface.co/datasets/seawsurf/fire_smoke_dataset_fasdd_cv), revision `896dec1`, and verified SHA-256 `c7d34d3511fd3a4bd16fdf5412e974d3e31b8f1b400bc566d1f115a807f36152`. The archive contains 95,126 images with YOLO labels. The [publisher record](https://doi.org/10.57760/sciencedb.j00104.00103) specifies CC BY-SA 4.0; the mirror card differs. Publisher terms were retained for this local experiment; weights were not redistributed or deployed.

Screened 600 candidates visually, selected 247, then conservatively excluded matching scene groups against reserved footage, leaving **224 images: 176 training and 48 internal validation**. The final set contains 80 negatives, 55 smoke-only, 38 fire-only and 51 both-class images. Every accepted positive was inspected with its boxes. The archive's `0=fire, 1=smoke` labels were remapped to the model's `0=smoke, 1=fire`.

Rejected graphics, irrelevant or ambiguous images, repeated scenes, a negative containing burning coals, uncertain positive labels and known evaluation-source families. Overlap screening used 2,049 sampled frames from 36 reserved sources. There are 89 conservative scene groups, no recorded group crosses training/validation, all 224 image hashes are unique, and the minimum cross-split perceptual-hash distance is 16.

This is an exploratory subset, not a production industrial CCTV dataset. Original camera and incident IDs are unavailable. Filename blocks, perceptual grouping and manual family exclusions reduce leakage but cannot prove independence, especially from the baseline's unknown pretraining data. Labels received a single assistant review; publisher boxes were retained rather than independently redrawn.

Trained for **10 epochs on the Mac's MPS device**, image size 640, batch 4, AdamW learning rate 0.0001, seed 42, mosaic/mixup disabled. Training's epoch timer reached 107.1 seconds. Configuration and results are in `training-config.yaml` and `training-results.csv`. MPS emitted nondeterministic-operation warnings despite the requested deterministic mode, so bitwise repeatability is not guaranteed.

## Results

Fresh image validation used the same 48 images and settings for both models. These are internal development metrics, not independent qualification.

| Image metric | Baseline | Candidate |
| --- | ---: | ---: |
| mAP50 | 0.5094 | 0.4633 |
| mAP50–95 | 0.2867 | 0.2731 |
| Precision | 0.6828 | 0.6659 |
| Recall | 0.4384 | 0.4152 |

The candidate was also run on **34 video sources, 17,556 frames**, including the complete uploaded house clip. Both models' comparable outputs use confidence 0.25, image size 640 and every frame. Existing baseline inference was reused and benchmark scoring recomputed; the candidate's inference and artifact identities were checked. Only the annotated portions of the existing development clips support event counts. Running inference on all 34 sources does not make them a fully labeled benchmark.

| House-video window, source-file time | Baseline smoke-hit frames | Candidate smoke-hit frames |
| --- | ---: | ---: |
| 0–35 s: clear-looking room, 1,050 frames | 283 | 0 |
| 65–125 s: established visible smoke, 1,800 frames | 1,647 | 750 |

The early wall false detections disappear, but the candidate also detects smoke in far fewer frames during the visible-smoke window. These counts are a diagnostic, not frame-level recall: the windows received visual review rather than exhaustive frame annotation. The video is accelerated and includes a later cut; source-file seconds are not real camera exposure time.

Existing event benchmark comparisons, shown as **TP / FP / FN**:

| Development labels and policy | Baseline | Candidate |
| --- | ---: | ---: |
| Human-reviewed 7 clips: raw smoke | 1 / 2 / 0 | 0 / 2 / 1 |
| Human-reviewed 7 clips: temporal smoke | 0 / 1 / 1 | 0 / 0 / 1 |
| Human-reviewed 7 clips: temporal fire | 2 / 0 / 0 | 2 / 0 / 0 |
| Assistant-reviewed 4 clips: raw smoke | 1 / 2 / 1 | 1 / 1 / 1 |
| Assistant-reviewed 4 clips: temporal smoke | 0 / 2 / 2 | 0 / 1 / 2 |
| Assistant-reviewed 4 clips: temporal fire | 0 / 0 / 0 | 0 / 1 / 0 |

The candidate loses the raw smoke detection in human-reviewed `clip-007` (34–40 s). It removes W08's smoke false alarm, but W04's smoke false alarm persists and W04 gains a fire event that survives temporal verification. Both models still fail to temporally verify the faint B01/B02 smoke events. B01/B02's uncertain fire labels remain excluded from scoring. Temporal verification uses at least three overlapping detections spanning one second within two seconds; it is evidence persistence, not human confirmation.

The clips are small, previously inspected development sets, including selected known failures. Their counts cannot establish general accuracy or a reliable false-alarm-per-hour rate. They are sufficient to reject this candidate's regressions.

## Artifacts and next training requirements

- `curated-manifest.json`, `curation-summary.json`, `reserved-overlap.json`, `class-consistency.json` and `provenance.json`: data identities, exclusions and split audit.
- `internal-validation.json`, `comparison-summary.json` and the four `*-development.json` reports: metrics, scoring provenance and event details.
- Candidate: `outputs/industrial-smoke-pilot/fasdd-curated-2026-10-22/weights/best.pt`, SHA-256 `54fc90c9ea43dfb95fc9c630e3292c2d6fdfaa3ae62e6245681e248a02bb1c66`.
- Baseline remains pinned in `backend/models.json`, SHA-256 `b91633799ceb052c814b4f8b77a37efc9a40f002d528df97d74463585fa4f28f`.
- Candidate video run: `outputs/fasdd-pilot-video-evaluation/run-_8y0iew7`; full logs and local dataset remain outside Git.

Before another candidate, expand the training material with source-identified industrial CCTV: early/faint smoke positives and confusing negatives such as bright walls, backlight, steam, dust and moving equipment. Keep fire examples to prevent regressions, and reserve whole cameras/incidents for evaluation. Collect similar new training scenes rather than moving these evaluation clips into training. Fix those data gaps before spending time on a longer run or tuning against this repeatedly inspected test set.

Verification: label-mapping self-check, all curated image/label hashes against archive bytes, unique-image and group separation checks, class consistency, model/run artifact hashes and fresh benchmark scoring passed. A fresh read-only reviewer found no material preparation/curation defect. This verifies the experiment's bookkeeping; it does not qualify the model for deployment.
