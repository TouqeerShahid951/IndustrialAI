# Smoke improvement review — 21 October 2026

Keep the current checkpoint for development. Neither alternative is a clear replacement across the reviewed examples. The persistent factory smoke alerts and missed backlit plumes remain unresolved. No default model or application behavior was changed; no new fine-tuning run was started.

## Assistant visual review

The user cannot play videos through their remote connection and explicitly delegated visual assessment to the assistant. These are assistant single-reviewer annotations, not human-confirmed or independent ground truth. Original queue annotations and previously confirmed user labels remain unchanged.

| Clip | Fire assessment | Smoke assessment | Reviewed timing |
|---|---|---|---|
| W04, stationary factory floor | No visible flame | No visible smoke plume | Entire 3.00 s clip |
| W08, moving forklift | No visible flame | No visible smoke plume | Entire approximately 4.01 s clip |
| B01, backlit room | Uncertain: saturated/occluded doorway | Moving smoke-like plume and diffuse haze present | Clear positive core 4.6–21.5 s; onset bracket 4.2–4.6 s; late residual haze uncertain |
| B02, backlit room | Uncertain: saturated/occluded doorway | Moving smoke-like plume present | Clear positive core 6.5–15.0 s; onset bracket 5.6–6.5 s; late residual haze uncertain |

No distinct flame contour can be reliably resolved in B01/B02. Their fire predictions are therefore not counted as confirmed false fire alarms. Visible plume appearance does not establish its chemical composition or an industrial fire hazard.

The review used unannotated chronological sequences: every third factory frame, approximately one-second plume samples, denser 0.2-second onset samples, and 0.5-second doorway samples. Full source decoding was checked. The examples were already selected from detector failures, so this is not a blinded review. Coarse plume boxes remain ambiguous localization drafts and are excluded from training and object-accuracy claims.

Validated annotations and manifest: [assistant annotations](assistant-annotations/), [manifest](assistant-review-manifest.jsonl). The annotations can be checked again from the project directory with `.venv/bin/python -m scripts.benchmark_data reports/smoke-improvement-2026-10-21/assistant-review-manifest.jsonl`.

## Three-model comparison

All three checkpoints processed the same 33 source clips and all 12,700 frames per checkpoint: the seven previously user-labeled development clips plus the 26 newly collected clips. Confidence 0.25, input size 640, stride one, original container timestamps and local Apple MPS were held fixed. Separate experimental weights were selected explicitly. Raw CSV class strings were preserved; `Fire`/`Smoke` were mapped to lowercase only during analysis. The evaluator's `fire_smoke` alias does not identify the actual checkpoint; the hash and external model record do.

| Model | Checkpoint SHA-256 | Pinned revision |
|---|---|---|
| Current: rabahdev/fire-smoke-yolov8n | b91633799ceb052c814b4f8b77a37efc9a40f002d528df97d74463585fa4f28f | 13017fe8af477c25f5298d168e2dfede4b000753 |
| Early domestic: mfranzon/fire-smoke-yolov8 | ac0a10257b2bc1f20c9d957f8adeeb61dd6140322fc19d0b4a116cb491776d16 | f1c6426b069c1849cbf13b1ef5d2a260289286db |
| YOLO26-S: Beehzod/yolov26-fire-smoke-detection | 283c996482e26013f6e60559ad25c49f38f3aa9937961c8c33aaa7d0fc8d1d59 | 6443bc2577f92db13ee3301a34224f6b87f2415e |

Public model cards: [current](https://huggingface.co/rabahdev/fire-smoke-yolov8n), [early domestic](https://huggingface.co/mfranzon/fire-smoke-yolov8), [YOLO26-S](https://huggingface.co/Beehzod/yolov26-fire-smoke-detection). Publisher-reported validation metrics are not treated as results on our footage. Pretraining overlap with public footage remains unknown. The early domestic checkpoint required dill 0.4.0 in the local experimental environment; no application dependency specification was changed.

Another candidate, aryantyagiase/yolov8-fire-smoke-detection, was excluded because the exact published payload failed to load despite matching the publisher's LFS SHA. TommyNgx's candidate was gated. Neither was silently substituted or counted as evaluated.

### Seven previously user-labeled development clips

Cells are event **TP / FP / FN**, not frame accuracy. Raw and temporal results use the existing event scorer. Temporal verification requires at least three same-class overlapping hits spanning at least one second within a two-second window; event gaps up to two seconds are merged. Ambiguous and unreviewed windows are excluded.

| Model | Raw fire | Temporal fire | Raw smoke | Temporal smoke |
|---|---|---|---|---|
| Current | 2 / 3 / 0 | 2 / 0 / 0 | 1 / 2 / 0 | 0 / 1 / 1 |
| Early domestic | 2 / 3 / 0 | 1 / 0 / 1 | 0 / 2 / 1 | 0 / 2 / 1 |
| YOLO26-S | 2 / 8 / 0 | 1 / 6 / 1 | 0 / 0 / 1 | 0 / 0 / 1 |

Both alternatives lose one temporally confirmed fire event. Fewer smoke alarms from YOLO26-S also accompany missed smoke, so suppression alone is not an improvement in detection.

### Four assistant-reviewed failure clips

The smoke column below counts temporally retained smoke frames, not detection accuracy. The two room clips have uncertain fire labels, so their fire results are diagnostic only.

| Clip | Current smoke frames | Early domestic smoke frames | YOLO26-S smoke frames |
|---|---:|---:|---:|
| W04, 75 frames | 50 | 50 | 0 |
| W08, 101 frames | 18 | 0 | 0 |
| B01, 483 frames | 0 | 9 | 0 |
| B02, 342 frames | 0 | 0 | 0 |

On these four provisional assistant labels, temporal smoke event TP/FP/FN is **0/2/2** for current, **1/1/1** for early domestic, and **0/0/2** for YOLO26-S. The early domestic model partially addresses B01 but retains the W04 floor alert and misses B02. YOLO26-S suppresses both factory alerts but misses both plumes. Its doorway fire detections must not be relabeled as smoke to improve the score.

The other newly collected clips remain diagnostics, not a labeled accuracy benchmark. RISE industrial-emission time-lapses have raw appearance counts only; their playback duration is not real-time exposure, and they are excluded from temporal and hazard-latency scoring. No new confirmed fire-positive set was created.

Detailed records: [comparison](comparison.json), [human-label reports](current-human-development.json), [assistant-label reports](current-assistant-development.json). Corresponding early-domestic and yolo26s reports are in this folder. Source/model/CSV hashes and full frame counts were verified. No operating threshold or production acceptance gate has been established.

## Longer industrial footage

Downloaded and fully decoded two additional real factory clips from the same published facility: L01, 522 frames/20.84 s, and L02, 516 frames/20.81 s. Their LFS SHA hashes match the pinned mirror. Together they add **41.64 s**, bringing this factory collection to **108.82 s** across ten short clips. They remain conservatively grouped as one factory source, not independent sites or continuous camera-hours.

Both show real machinery and workers with diffuse process haze. No visible flame was found in approximately one-second chronological samples. Smoke versus dust/steam/process aerosol remains uncertain, so neither is accepted as an empty smoke-label training negative. All three checkpoints processed all 1,038 frames from the additional clips. The current model produced no raw detections; early domestic flagged smoke in 119 L01 frames and four L02 frames; YOLO26-S flagged smoke in 41 L01 frames and fire in one L02 frame. These are prediction counts, not confirmed false-alarm rates.

Source: [Önal/Dandıl real-factory dataset, CC BY 4.0](https://data.mendeley.com/datasets/xjmtb22pff/1), pinned mirror [Voxel51/Safe_and_Unsafe_Behaviours](https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours). Exact records: [longer-footage.json](longer-footage.json), [longer-diagnostics.json](longer-diagnostics.json).

Hours of suitable industrial CCTV remain missing. The access/usage checks found:

- NVIDIA warehouse sample terms limit use to evaluating NVIDIA technologies, so it was not used for this Mac experiment.
- SteelBench artifacts required access not available in this session; no account was created.
- The official D-Fire video share returned an authorization failure; it was not bypassed.
- IPAD's accessible archive contains industrial frame sequences, but verified per-sequence timing and dataset reuse terms were missing. Its paper includes synthetic cases; these were not substituted for real CCTV or reconstructed at a guessed FPS.
- CMOT's Alipan source still requires an account the user does not have.

These sources were not counted as downloaded usable long footage. The local access findings and source metadata are preserved in this folder. The minimum remaining acquisition is continuous, permissioned industrial recordings with known camera IDs and examples of steam, dust, reflections, workers and genuine smoke, including negatives long enough to measure nuisance alerts.

## Fine-tuning status

**Not started: the training-data condition is unmet.** This is a data/split problem, not missing user permission. A second weak-data pilot would not resolve it.

The inspected D-Fire mirror pool contains 600 row/box records: 304 negative, 19 fire-only, 152 smoke-only and 125 both. The 300 AoF-prefix rows include only four fire-containing examples. Camera/incident groups are absent from the inspected rows; WEB-source rights and scene overlap need review, and industrial relevance of the image pool has not been visually established. Training on randomly split neighboring frames or the comparison scenes would make the result misleading. The original twenty-image pilot had already regressed.

Prepared a separate ten-epoch, batch-four MPS recipe using the current checkpoint's class order (0 smoke, 1 fire). It deliberately points to an unpopulated training dataset until source groups and labels are accepted. The current 33 comparison sources and their neighboring scenes remain reserved from training. The two new hazy factory clips are also not accepted as negative training truth. No new trained best.pt or improved-accuracy claim is being reported.

See [training readiness](training-readiness.json), [bounded training configuration](training-config-pending.yaml) and [exact next step](fine-tuning-next-step.md). Once source-isolated training/validation data is ready, run the prepared local recipe, repeat this exact comparison and preserve the default unless a separate acceptance review supports a change.

## Remaining work

1. Acquire continuous industrial footage with permission, camera/incident IDs and known timing; identify steam/dust where possible.
2. Obtain a source-isolated positive/negative training set with checked boxes; independently audit a subset of the assistant labels when a reviewer can view it.
3. Run the bounded local fine-tuning experiment and evaluate before/after on reserved footage. Retain explicit uncertainty and all failure examples.

This report completes the delegated four-clip visual assessment and two-alternative comparison. Long-duration validation and new fine-tuning remain open.
