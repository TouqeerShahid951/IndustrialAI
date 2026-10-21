# Smoke failure inspection — 20 October 2026

The missed event has weak, intermittent smoke detections that cannot satisfy the elapsed-time requirement. The false event is persistent misclassification of a moving person, which temporal persistence cannot distinguish from actual smoke. These are two interacting detector/confirmation limitations; the saved observations reproduce the filter behavior without evidence of a timestamp or frame-skipping failure.

![Two representative failures](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-failure-inspection/comparison.jpg)

Orange: raw smoke candidate rejected by the timed rule. Green: smoke candidate accepted by the timed rule. Scores are model outputs, not calibrated probabilities. Both source videos are 320 × 240; images are enlarged for inspection.

## Missed labeled smoke: clip 007, Arson017

- Human label: smoke approximately 34–40 s. Examined frames show a faint diffuse plume near the foreground wall, partly blending into the background. Low contrast and limited source detail are plausible contributors; this inspection does not establish which training deficiency caused the weak scores.
- Original confidence cutoff 0.25: ten smoke boxes across ten of the 180 frames in the labeled six-second interval. Candidate timestamps run from 35.100 to 35.467 s; merged event coverage ends at 35.500 s.
- Scores range from 0.257 to 0.340. Boxes consistently cover a narrow portion near the right side of the plume.
- Maximum matching-box support is ten frames spanning **0.367 s**, below the required **1.0 s**. The count threshold is satisfied; the time-span threshold blocks every candidate. The 3-of-5 legacy rule accepts the event at 35.233 s.
- A diagnostic replay of the same checkpoint at confidence 0.10 finds smoke in 30 frames across the entire clip and permits a timed event at 36.000–36.267 s. Cutoffs 0.15 and 0.20 still fail the one-second timed rule. This establishes that some useful weak predictions were suppressed by the original cutoff, but does not prove a lower cutoff generalizes safely.

## False smoke: clip 003, indoor room

- Human label: no fire or smoke. The main false event boxes surround the foreground person in a dark/purple shirt, sometimes expanding over much of the room. A later event around 24 s surrounds content on the television. The retained event is primarily person confusion, rather than a localized plume.
- Original replay produces 72 smoke boxes across 65 frames, in two merged raw events. Scores range from 0.251 to 0.694, exceeding the strongest score on the labeled CCTV smoke.
- At the first timed confirmation, **14.833 s**, the current box has score **0.492**, with **25 matching frames spanning 1.0 s**. Its box is approximately `[56.5, 34.6, 221.5, 240.0]` in the 320 × 240 source frame. This meets the configured rule exactly.
- Timed output continues through a merged event ending at 16.083 s. Persistent wrong predictions pass a persistence filter. The IoU requirement is only 0.10; broad boxes retain enough overlap as the person moves. A spatial consistency rule alone is not evidence of smoke appearance or plume motion.
- Raising the cutoff to 0.50 still retains one false event. Lowering it to 0.10 retains two timed false events, including the television event. A single confidence cutoff cannot separate these two examples cleanly.

## Controlled diagnostic checks

No application, detector or filter defaults were changed. The following are development-data probes, not selected settings or independent validation. Hits=3, trailing window=2 s and IoU=0.10 remain fixed.

**Original logs, all seven clips, varying only minimum span or confidence:**

| Confidence | Required span | Smoke events detected | False/repeat smoke events | Missed smoke events |
| --- | --- | --- | --- | --- |
| 0.25 | 1.00 s (baseline) | 0 | 1 | 1 |
| 0.25 | 0.75 s | 0 | 1 | 1 |
| 0.25 | 0.50 s | 0 | 2 | 1 |
| 0.25 | 0.25 s | 1 | 2 | 0 |
| 0.30 | 1.00 s | 0 | 1 | 1 |
| 0.35 | 1.00 s | 0 | 1 | 1 |
| 0.50 | 1.00 s | 0 | 1 | 1 |

**New low-confidence inference on the two inspected clips only, one-second span:**

| Confidence | Clip 007: labeled smoke detected | Clip 003: false smoke events |
| --- | --- | --- |
| 0.10 | Yes, first confirmation 36.000 s | 2 |
| 0.15 | No | 2 |
| 0.20 | No | 1 |
| 0.25 | No | 1 |

The original seven-clip default smoke event records were reproduced exactly before the probes. Both diagnostic runs processed all source frames: 862 + 1,382 = 2,244. Source, original checkpoint and completed CSV artifact hashes were checked. Container timestamps, full-frame processing, image size 640 and MPS were retained. The diagnostic checkpoint was loaded through its cached `best.pt` snapshot path with the same SHA-256 as the original runs; an initial incomplete attempt using the resolved extensionless cache blob could not load for inference and is excluded from results.

## Recommended next step

Build a separate smoke validation set containing faint plumes plus moving people, changing television/monitor content, steam and dust. Include intended industrial cameras, independent labels, and reviewed negative exposure. Use it to compare smoke-specific thresholds and verification options against this unchanged baseline. The evidence favors improving smoke discrimination as well as confirmation: a shorter wait recovers this event while also admitting more false events. Training on this tiny inspected set or hiding a person/monitor region would not establish general performance and could suppress smoke that overlaps those regions.

## Evidence

- [Clip 003 frame sequence](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-failure-inspection/clip-003-contact.jpg)
- [Clip 007 frame sequence](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-failure-inspection/clip-007-contact.jpg)
- [Per-detection temporal support](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-failure-inspection/support-trace.json)
- [Diagnostic settings, event records and scores](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-failure-inspection/diagnostics.json)
- [Completed low-confidence run directories](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-failure-inspection/low-confidence-runs.json)
- [Original seven-clip evaluation](/Users/tabbasi/Downloads/IndustrialAI/reports/chat-review-evaluation-2026-10-20.md)
