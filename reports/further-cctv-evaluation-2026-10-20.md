# Further CCTV evaluation — 2026-10-20

## Findings

- Threshold/resolution changes trade misses for false alerts; no setting in this small audit fixes fire/smoke detection.
- Original helmet detector recognizes the eight nearby helmets in the four annotated frames at default settings, but misses all four uncovered-head targets at size 640. At size 1280 and confidence 0.10, it matches three uncovered heads but also creates an unmatched no-helmet prediction.
- The earlier frame-count temporal rule was too fast at high source FPS. Fixed-rate sampling gives a more meaningful persistence interval. At 2 Hz, 3-of-5 voting removes the orange-workwear false event while retaining at least one detection on all five positive clips checked. Persistent headlights and white plumes remain false alerts.
- The user-selected smoking video remains pending because its media could not be retrieved. No results from another video are substituted.

## Audit data and limits

37 frames selected before running the new settings: 15 construction frames at one-second spacing (0–14s); 22 workshop frames at five-second spacing (0–105s). Visual frame labels: construction has no visible fire/smoke; workshop has visible smoke and no fire. These are descriptive counts on repeated frames from two public CCTV-style examples, not independent production accuracy estimates.
The workshop source already contains green contour overlays from another system; they may bias inference. Capture authenticity/provenance for the public construction demo is not independently verified. Earlier references to genuine CCTV were too strong; these are public fixed-camera/CCTV-style examples, not verified footage from your facility.
Four construction frames (3, 6, 9 and 12s) have 12 visible heads marked: 8 helmets, 4 uncovered heads. Nearby helmet boxes were seeded from baseline detections and visually adjusted, so annotation is not blind and can favor the baseline. Distant-head boxes are approximate manual labels. Other sample frames are not exhaustively annotated for heads and are excluded from head metrics.
Use these results to choose the next experiment, not to quote overall accuracy. Public-data overlap with original training remains unknown.

[Frame labels and images](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-audit) · [Head boxes](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-audit/head-labels.json)

## Fire/smoke setting comparison

Each row reports frame presence, not bounding-box localization. Every one of the 37 selected frames is labeled fire-negative; consequently fire recall cannot be estimated. Smoke misses are counted only within the 22 selected smoke-positive workshop frames. Higher thresholds are applied to predictions collected with confidence 0.05, with NMS held fixed.

| Size | Confidence | Smoke frames detected / 22 | False fire frames / 37 | False smoke frames / 15 negatives |
|---|---:|---:|---:|---:|
| 640 | 0.05 | 6 | 6 | 3 |
| 640 | 0.10 | 3 | 2 | 1 |
| 640 | 0.15 | 3 | 2 | 0 |
| 640 | 0.25 | 2 | 2 | 0 |
| 640 | 0.40 | 1 | 1 | 0 |
| 640 | 0.60 | 0 | 0 | 0 |
| 1280 | 0.05 | 17 | 13 | 2 |
| 1280 | 0.10 | 11 | 12 | 2 |
| 1280 | 0.15 | 11 | 11 | 1 |
| 1280 | 0.25 | 7 | 11 | 0 |
| 1280 | 0.40 | 4 | 4 | 0 |
| 1280 | 0.60 | 1 | 0 | 0 |

![Threshold tradeoff](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-threshold-audit.png)

At confidence 0.25, 1280 improves selected smoke hits from 2/22 to 7/22 but raises false fire frames from 2/37 to 11/37. Lowering confidence to 0.10 at 1280 detects 11/22 smoke frames while producing false fire boxes on 12/37 frames. This is a tradeoff, not a verified improvement.

## Helmet object audit

Greedy one-to-one matching in descending confidence order; class must match and IoU≥0.5. Unmatched predictions count as FP; unmatched targets as FN. Counts only apply to the four fully marked frames.

| Size | Confidence | Class | TP | FP | FN |
|---|---:|---|---:|---:|---:|
| 640 | 0.10 | Hardhat | 8 | 5 | 0 |
| 640 | 0.10 | NO-Hardhat | 0 | 1 | 4 |
| 640 | 0.25 | Hardhat | 8 | 0 | 0 |
| 640 | 0.25 | NO-Hardhat | 0 | 0 | 4 |
| 640 | 0.40 | Hardhat | 8 | 0 | 0 |
| 640 | 0.40 | NO-Hardhat | 0 | 0 | 4 |
| 1280 | 0.10 | Hardhat | 8 | 3 | 0 |
| 1280 | 0.10 | NO-Hardhat | 3 | 1 | 1 |
| 1280 | 0.25 | Hardhat | 8 | 0 | 0 |
| 1280 | 0.25 | NO-Hardhat | 1 | 0 | 3 |
| 1280 | 0.40 | Hardhat | 8 | 0 | 0 |
| 1280 | 0.40 | NO-Hardhat | 0 | 0 | 4 |

At default settings (640, 0.25), helmet recognition is successful in this small selected set, but no-helmet recognition fails. Raising input size and lowering only the no-helmet threshold is an experiment worth validating on more scenes; it is not promoted to a default here.
IoU≥0.3 results are also retained in the metrics JSON because tiny-box rounding can affect scores.

## Temporal sampling check

The original 3-of-5 rule can confirm after only 0.083s at 24 FPS, versus 0.426s at 4.6905 FPS. At 2 Hz the earliest three-hit span is about 1 second. Voting is causal, same-class, spatial IoU≥0.1; the current frame must have a detection. This filters candidate boxes, not a full alarm policy.
For this analysis, 12 existing videos were reused: five positive and seven negative. They include mixed research footage in addition to the two CCTV-style examples. Native-rate research logs were sampled every third source frame; fixed-rate re-sampling can therefore have timestamp rounding jitter. The 2-Hz analysis does not use future frames.

| Sampling | Positive clips retaining ≥1 confirmed detection | Negative clips with ≥1 false confirmation |
|---|---:|---:|
| Existing analyzed-frame rate | 5/5 | 3/7 |
| Capped at 5 Hz | 5/5 | 3/7 |
| Capped at 2 Hz | 5/5 | 2/7 |

At 2 Hz the construction fire false event disappears; headlights and the white-plume negative still trigger. Workshop first smoke confirmation shifts from 0.426s to 1.066s after the clip start (smoke is already visible at clip start). This is not latency from hazard onset. Retaining an event does not mean retaining every true hazard frame.

## Requested smoking video — pending

[Selected YouTube video](https://www.youtube.com/watch?v=1_0NMTqbAC0), extracted from the user’s Google video-result link. No source frames were retrieved, so its content, overlays and smoking interval have not been independently inspected.
Browser navigation timed out; YouTube web retrieval was throttled; downloading the yt-dlp tool from PyPI failed after retries with a connection timeout. The metadata output is empty and is not treated as a successful download. A local copy attached by the user is needed to run the exact requested test with current connectivity.

## Saved artifacts

- [Full frame/object metrics](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-frame-audit-metrics.json)
- [Temporal sampling results](/Users/tabbasi/Downloads/IndustrialAI/reports/time-sampling-audit.json)
- [Original audit prediction runs](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-audit-runs.json)
- [Smoke labeling contact sheet](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-audit-smoke-label-review.jpg)
- [Helmet labeling contact sheet](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-audit-helmet-label-review.jpg)

```bash
.venv/bin/python scripts/audit_metrics.py
.venv/bin/python scripts/time_sampling_audit.py
.venv/bin/python -m unittest discover -s tests -v
```

No model defaults changed. The next useful validation requires clean footage with different scenes and independent labels, including positive smoking CCTV.
