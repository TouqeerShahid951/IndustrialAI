# Smoke sensitivity diagnosis — 22 October 2026

Yes: the current development configuration produces false-looking smoke detections in the selected video. Its 0.25 confidence floor contributes, but threshold adjustment alone is insufficient.

## Selected clip

Analysis: `3333b392-7637-41ce-a1fa-d8a188273038`, source `House-fire-caught-SnapYT.App.mp4`, 4,856 source frames, 161.867 s of file playback at 30 fps. The camera timestamp advances faster than file playback, and the video later cuts to a damaged interior. All timings below are file/source times, not real elapsed camera time.

Visual inspection of chronological samples shows a clear-looking room early on, followed by a dark plume spreading along the ceiling around 50–55 s and dense visible smoke later. Early predictions repeatedly cover the bright left wall. These are assistant visual judgments, not independently labeled ground truth; the exact smoke onset remains uncertain.

Offline replay reused every saved model observation and the existing temporal/event grouping code. No new model inference or application configuration change was needed.

| Confidence cutoff | Flagged frames in early 0–35 s (1,050 frames) | Flagged frames in established-smoke 65–125 s (1,800 frames) | Early event intervals |
| --- | ---: | ---: | --- |
| 0.25, current | 283 | 1,647 | 4 temporal + 1 raw |
| 0.35 | 7 | 1,510 | 0 temporal + 1 raw |
| 0.45 | 0 | 1,250 | 0 |
| 0.55 | 0 | 907 | 0 |
| 0.65 | 0 | 524 | 0 |

These are prediction counts within visually assessed windows, not precision/recall, detection probabilities or a calibrated operating threshold. Higher cutoffs reduce detections in the smoke-positive window too. Later scene-cut residual haze is ambiguous and was not accepted as a negative window.

## Root causes

1. `backend/pipeline.py` hard-codes a 0.25 inference cutoff across model passes. The profile also records 0.25. Scores near 0.25–0.40 account for the early wall detections in this clip.
2. The review queue retains raw flags as well as temporally verified candidates. A raw detection does not need to pass temporal verification to appear for review.
3. Temporal verification requires three overlapping hits spanning one second within two seconds; it does not require continuous or dense support. Persistent scene confusion can pass it. Four early intervals in this clip already pass the current temporal rule.
4. Event grouping merges hits separated by up to two seconds, so a displayed interval can include gaps without a box.
5. There is a model/domain problem too. Earlier W04 factory-floor footage, assessed as having no visible smoke, has smoke detections in all 75 frames at 0.45; scores reach 0.775. Raising the threshold to 0.35 or 0.45 does not fix that example.
6. A higher global cutoff loses weak positive evidence. B01's visible backlit plume has just one current-model smoke hit, score 0.329. A 0.35 cutoff removes even that hit; it already fails temporal verification at 0.25.

## Recommendation

Use a separate, explicitly evaluated smoke alert policy. A 0.35 cutoff plus temporal verification is a useful experimental comparison for this house clip, not an approved global default. Keep weaker detections accessible as possible smoke/raw evidence, and reserve stronger alert wording for the chosen verification policy. Evaluate sustained support rather than merely three sparse hits. Calibrate across the positive plumes and hard negatives before changing defaults, then improve the model with wall/backlight/floor/steam hard negatives. High-confidence factory false positives require more than a scalar threshold.

No saved labels, reviews, model weights or live thresholds were changed. No accuracy or readiness claim is made from these selected development examples.

## Reproduction evidence

- `threshold-sweep.json`: five cutoffs replayed through current event grouping.
- `cross-clip-check.json`: B01 and W04 counterexamples under those cutoffs.
- `contact.jpg`: chronological unannotated source frames with saved detector scores below each tile.
- `onset.jpg`: denser 36–60 s samples around smoke onset.

Checks assert the early-window counts, loss of the B01 hit at 0.35, and retention of all 75 W04 frames at 0.45. Runtime application tests were not rerun because application code was not modified.
