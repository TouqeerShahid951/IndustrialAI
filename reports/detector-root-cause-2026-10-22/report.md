# Detector root-cause investigation — 22–23 October 2026

The current checkpoint fails before incident aggregation: it assigns strong smoke scores to clear factory floors and almost never detects the reviewed room haze. Raising its threshold cannot recover missing haze. This investigation tests input/runtime problems, input scale, alternative learned weights and whole-scene smoke representation separately. **The perception problem is confirmed; a reliable replacement has not been achieved.** No application model, thresholds, saved reviews or incident records were changed.

## What the controlled checks establish

- **Class mapping is correct.** The baseline checkpoint embeds `0: smoke, 1: fire`, matching the registry. Each alternative was checked against its own embedded names; class aliases were explicit.
- **No CPU/MPS or image/video discrepancy on the 69 sampled frames.** Baseline 640 MPS reproduces all 15 boxes from the saved native-video run at confidence 0.25: no missing/added boxes and identical scores. CPU reproduces the same boxes with maximum score difference 0.000001431. This rules out these explanations on the tested inputs, not every possible runtime fault.
- **Input scale matters for small flames.** Increasing baseline input from 640 to 1280 improves reliable-box flame matches from 4/15 to 8/15, but introduces fire candidates in 8/39 known-negative frames and worsens smoke false detections. Increasing resolution alone fails the test.
- **Checkpoint behavior changes sharply across scenes.** A FASDD-associated publisher checkpoint at 1280 confirms all six newer lab fires but loses both older user-labeled fire events under the same temporal rule. Camera/source diversity is necessary for selecting a replacement. Its exact training subset and public-footage overlap are unknown.
- **Localized boxes poorly cover the reviewed diffuse haze.** The baseline emits smoke in only 26/7,509 reviewed-positive video frames; the stronger flame checkpoint emits smoke in six. This supports testing whole-scene smoke classification; it does not establish the physical composition of visible aerosol.

The existing baseline had false-smoke scores up to 0.758 on clear floor, versus at most 0.417 during reviewed smoke-positive time. A blanket 0.5 threshold removes all those positive smoke candidates while retaining some floor errors. Temporal persistence also retains a persistent floor error. Neither is a root fix for perception.

## Same-frame probes

All variants processed the same 69 lossless native-resolution PNGs, input confidence floor 0.01; this table selects predictions at 0.25. Known-presence counts do **not** establish correct localization. Uncertain classes and draft boxes are excluded separately.

| Variant | Fire positive frames with candidate /18 | Fire negative frames with candidate /39 | Reliable fire boxes matched /15, IoU 0.5 | Smoke positive frames with candidate /19 | Smoke negative frames with candidate /36 |
|---|---:|---:|---:|---:|---:|
| Baseline 640, MPS | 7 | 0 | 4 | 0 | 4 |
| Baseline 640, CPU | 7 | 0 | 4 | 0 | 4 |
| Baseline 1280 | 12 | 8 | 8 | 4 | 13 |
| Early domestic 640 | 5 | 0 | 4 | 13 | 7 |
| YOLO26-S 640 | 16 | 2 | 10 | 0 | 0 |
| Strict YOLO11m 640 | 10 | 0 | 6 | 0 | 0 |
| Strict YOLO11m 960 | 14 | 0 | 10 | 0 | 0 |
| FASDD-associated YOLO26n 640 | 12 | 0 | 9 | 0 | 2 |
| FASDD-associated YOLO26n 1280 | 15 | 0 | 12 | 0 | 3 |

No variant matches any of the three accepted coarse smoke boxes at IoU 0.5 and confidence 0.25. These few spatial labels cannot measure general smoke-localization accuracy. Lower-threshold diagnostics are preserved in [probes.json](probes.json), including the FASDD-associated 640 variant's one smoke-box match at 0.05; no production threshold was selected from these observations.

Visual examples: [controlled-examples.jpg](controlled-examples.jpg). The cyan boxes in that sheet are actual selected model predictions; a missing box is preserved as a miss.

## Complete-video comparisons

Each variant processed all **23 clips / 20,400 frames / 815.71 seconds** at original source timestamps, confidence 0.25 and stride one. The baseline run is reused and hash-checked. Temporal confirmation requires three overlapping same-class hits spanning at least one second within two seconds. Event gaps up to two seconds are merged. Uncertain and unreviewed intervals remain excluded.

| Variant | Fire-positive frames hit | Temporal fire TP / FP / FN | Smoke-positive frames hit | Temporal smoke TP / FP / FN | Temporal smoke events touching known-negative time |
|---|---:|---|---:|---|---:|
| Baseline 640 | 2,137/7,882 (27.11%) | 5 / 2 / 1 | 26/7,509 (0.35%) | 1 / 2 / 6 | 2 |
| Early domestic 640 | 1,327/7,882 (16.84%) | 4 / 6 / 2 | 4,853/7,509 (64.63%) | 5 / 13 / 2 | 9 |
| FASDD-associated YOLO26n 1280 | 6,660/7,882 (84.50%) | 6 / 0 / 0 | 6/7,509 (0.08%) | 0 / 1 / 7 | 1 |

All unmatched event FP includes duplicate fragments inside a positive interval, so it differs from events touching known-negative time. The smoke-negative exposure is only **260.57 seconds**; no production camera-hour nuisance rate is inferred from it. Any candidate presence counts are distinct from spatial accuracy, temporal confirmation and human confirmation.

The FASDD-associated candidate confirms C03 only at 32.652 s, despite fire already being visible at clip start. Better aggregate recall does not mean timely early detection.

### Older regression footage

The FASDD-associated 1280 candidate also processed all **11 older clips / 6,130 frames**: seven user-labeled development clips plus four assistant-reviewed failures. On the user-labeled set, raw fire event TP/FP/FN is **2/2/0**, but temporal fire is **0/0/2**, versus the baseline's **2/0/0** temporal fire. Smoke temporal recall is zero. On the four assistant clips, it misses both temporal smoke events. This candidate is rejected as a default replacement, including for fire alone under the current policy.

The early domestic model was already tested on those older clips in the [previous review](../smoke-improvement-2026-10-21/outcome.md): it loses the user-labeled smoke event and one temporal fire event. Its newer haze gains do not override those regressions.

Exact records: [full comparison](full-video-comparison.json), [older human-label benchmark](fasdd-regression-human.json), [older assistant-label benchmark](fasdd-regression-assistant.json). Run metadata pins the input, model, raw detections, observations and inference code hashes.

## Whole-scene smoke experiment

The prompt specification and supervised-head specification were frozen before their inference. The official Google SigLIP2 base 224 checkpoint was pinned and its published weight SHA-256 verified. Its dependencies were installed into an ignored, isolated target directory; the application's environment and dependency specifications were not modified. Whole-scene predictions have no invented plume boxes and are not calibrated hazard probabilities.

| Scene method | Smoke-positive frames hit /19 | Known-negative frames flagged /36 | Decision |
|---|---:|---:|---|
| Fixed positive/negative text prompts, margin ≥0 | 18 | 11 | Reject as an unqualified replacement |
| Frozen image encoder + fixed ridge smoke head, score ≥0 | 0 | 0 | Reject; suppression accompanies complete smoke failure |

The fixed-prompt method rejects all 24 sampled clear-factory frames, including the floor failures. However, it flags 11 of 12 known-negative lab-room frames, including all three documented water-mist samples. It therefore moves the false-positive problem instead of solving it. The single missed smoke sample is C10's final frame. No prompt or threshold was tuned after observing these results.

The supervised experiment reused the **224 previously screened FASDD images**, with the existing 176 training /48 validation split and disjoint approximate scene groups. All input and label hashes were checked. A frozen image encoder provided normalized image features; a linear ridge head (λ=0.1, train-only centering, fixed zero threshold) was fitted only to the training split. **The detector and image encoder were not fine-tuned.** No reserved CCTV frames were used for fitting or threshold selection.

Internal validation was **22 TP /2 FP /22 TN /2 FN**, or 44/48 (91.67%) correct. On the separate CCTV diagnostic frames, the same head was **0 TP /0 FP /36 TN /19 FN**, excluding 14 uncertain frames. A high internal image-validation score is therefore insufficient evidence of useful CCTV smoke detection. This is a measured transfer failure, not justification to report an improved model or silently raise a threshold. The approximate source groups and previously exposed development frames do not constitute a locked external test.

Exact frozen specifications and per-frame scores: [prompt spec](scene-prompts.json), [prompt probe](scene-probe.json), [head spec](scene-head-spec.json), [trained-head results](scene-head.json). The scene probes are limited to sparse frames; no temporal or full-video success is claimed for them. Their failure already prevents promotion, so a larger video inference run was not performed.

## Required root fix and concrete regression gate

Further tuning needs representative, source-grouped CCTV training data: diffuse indoor haze and weak plumes, plus verified clear floors, glare, normal process aerosol, steam and dust. Presence/absence/uncertainty and approximate onset matter more than forcing a box around diffuse haze. Chemical/source context is needed where smoke and mist look similar. Normal-shift recordings from the intended facility would address the biggest remaining gap; availability has been asked of the user.

Keep the current reserved clips out of that training pool. Split by actual camera/site/incident before generating adjacent samples; audit labels and source rights. The present small image pool is not sufficient for another claim of successful domain adaptation. An accepted development candidate must:

1. Preserve both older user-labeled temporal fire detections and improve early small-flame evidence in C03/C07 without new known-negative fire events.
2. Recover diffuse smoke in the newer clips while retaining the older user-labeled smoke interval in clip-007 and the B01/B02 plumes.
3. Reject the F04/F08 floor cases and documented C11 mist without manually masking those evaluation scenes.
4. Pass the same class-specific uncertainty masks, native timestamps, full-video comparison and regression checks. Then evaluate on genuinely unseen cameras and longer negative recordings before any deployment claim.

The current evidence supports separating flame localization from a domain-trained smoke scene/clip signal. It does **not** establish that adding a generic vision-language model, combining checkpoints or changing a temporal threshold meets those gates. No such unvalidated combination was added to the MVP.

## Interpretation and limits

The confirmed fault is unreliable visual discrimination in the baseline weights. Small-object input scale and mismatch between localized plume boxes and diffuse room haze are supported contributors. The experiments cannot identify the exact defect in the original unpublished training process. Repeating the rejected small YOLO fine-tune or selecting a checkpoint from one camera group would not establish a fix.

The newer footage is development data with single-assistant-reviewer annotations: one factory family and one controlled-lab camera family. Older clips add different public scenes, not an independent industrial deployment test. Public training overlap is unknown. Water mist is a documented hard negative; uncertain dust/steam/haze remains uncertain. A model seeing aerosol cannot by itself establish combustion chemistry.

Software also retains raw flags for human review and labels temporal evidence separately. It does not repair missed perception. Shared application configuration is partially hardcoded in inference; values currently equal the recorded profile, so that drift risk does not explain these measured failures. No review history was rewritten to hide false positives.

## Reproduction and sources

From the repository root:

```sh
.venv/bin/python reports/detector-root-cause-2026-10-22/probe.py --self-check
.venv/bin/python reports/detector-root-cause-2026-10-22/compare.py --self-check
.venv/bin/python reports/detector-root-cause-2026-10-22/scene_probe.py --self-check
.venv/bin/python reports/detector-root-cause-2026-10-22/scene_head.py --self-check
.venv/bin/python reports/detector-root-cause-2026-10-22/compare.py
PYTHONPATH=outputs/detector-root-cause-2026-10-22/scene-runtime HF_HUB_OFFLINE=1 .venv/bin/python reports/detector-root-cause-2026-10-22/scene_probe.py
PYTHONPATH=outputs/detector-root-cause-2026-10-22/scene-runtime HF_HUB_OFFLINE=1 .venv/bin/python reports/detector-root-cause-2026-10-22/scene_head.py
```

Heavy model weights, native PNGs, raw inference runs and isolated experimental dependencies remain in ignored local storage. `inputs.json` records the selected frame indices, container PTS, original pixel hashes, source and annotation hashes. Sequential extraction was used: seeking by frame number produced three off-by-one decoded frames during preparation and was rejected before inference. The existing baseline and application decode sequentially; this extraction correction is not evidence of an app inference bug.

Primary model sources: [baseline model card](https://huggingface.co/rabahdev/fire-smoke-yolov8n), [early domestic model](https://huggingface.co/mfranzon/fire-smoke-yolov8), [strict YOLO11m](https://huggingface.co/fireviewer/fire-smoke-yolo11m-strict-v1), [FASDD-associated publisher model](https://huggingface.co/seawsurf/fire_yolo), [Google SigLIP2 model](https://huggingface.co/google/siglip2-base-patch16-224), [official SigLIP2 preprocessing documentation](https://huggingface.co/docs/transformers/model_doc/siglip2). Publisher metrics are not our results. License/provenance notes are preserved with each candidate; no experimental weights were redistributed or deployed.
