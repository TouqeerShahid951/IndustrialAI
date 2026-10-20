# CCTV-only model test — 2026-10-20

Ran all three original models locally on the Mac M4/MPS, on every decoded frame of two previously downloaded CCTV clips. No fine-tuned pilot weights were used. Confidence 0.25, size 640, stride 1. This is a qualitative CCTV test, not a labeled accuracy benchmark.

## Findings

- Construction CCTV (15 seconds): fire detector produced 23 false fire boxes on 23/360 frames. The source has no visible fire; review from the prior run locates the boxes on orange workwear. Helmet detector found helmets, but the prior manually marked distant-head probes remain a known weakness. Cigarette model produced no boxes.
- Indoor workshop CCTV (about 109.6 seconds): smoke detector returned boxes on only 25/514 frames. Visual review at 20, 60 and 95 seconds shows spreading ceiling smoke without a smoke box in those selected frames. The source already contains green contours from an older detector; they are not our detections and may bias the model, so this cannot establish raw-video accuracy.
- Workshop cigarette model produced three low-confidence false candidates on ceiling regions, not visible cigarettes. A reviewed frame is included below. All three were removed by the existing 3-of-5 spatial filter.
- Temporal verification reduced construction fire-positive frames from 23 to 13 but did not eliminate the false event. Workshop smoke-positive frames fell from 25 to 17. A filter cannot recover smoke the visual model misses.
- Neither clip provides a clean positive test of cigarette smoking. No claim is made about smoking recall.

## Source clips

- [Construction sample source](https://raw.githubusercontent.com/cosmo-wander-ai/cosmo-edge/v1.1.0/data/test-video/Safety%20Helmet.mp4): fixed construction-site camera, 1920×1080, 24 FPS. This is the same clean CCTV clip used earlier, now tested on all 360 frames.
- [FIRESENSE original dataset](https://zenodo.org/records/836749), smoke_videos.1407.zip → pos/testpos05.821.avi: fixed indoor industrial/workshop camera, 320×240, 514 frames, reported 4.6905 FPS. Existing contour overlays are present in the source. Excluded from the fine-tuning pilots.
- Attempts to download additional clean CCTV clips failed with local DNS/connection errors. No new external video was obtained in this run. This report uses existing local files, and does not substitute movie footage.

## Measured outputs

Frames with boxes are detection coverage, not accuracy, incident count, worker count or recall. Confirmed frames use the existing causal 3-of-5, same-class, IoU≥0.1 rule. Because source FPS differs, this frame-based window has different durations across clips; it is not a calibrated time-based alarm policy.

| Clip | Model | Decoded frames | Frames with boxes | Confirmed frames | Box labels |
|---|---|---:|---:|---:|---|
| helmet.mp4 | fire_smoke | 360 | 23 | 13 | fire: 23 |
| smoke_pos_testpos05.821.avi | fire_smoke | 514 | 25 | 17 | smoke: 25 |
| helmet.mp4 | helmet | 360 | 360 | 358 | Hardhat: 875, NO-Hardhat: 14 |
| smoke_pos_testpos05.821.avi | helmet | 514 | 177 | 120 | NO-Hardhat: 181, Hardhat: 34 |
| helmet.mp4 | cigarette | 360 | 0 | 0 | none |
| smoke_pos_testpos05.821.avi | cigarette | 514 | 3 | 0 | cigarette: 3 |

![Workshop smoke review: source contours are not our boxes](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-only-smoke-review.jpg)

![False cigarette candidate on the ceiling](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-only-cigarette-candidate.jpg)

## Annotated videos

- [helmet.mp4 — fire_smoke](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-99ywekzj/fire_smoke/0-helmet.mp4)
- [smoke_pos_testpos05.821.avi — fire_smoke](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-99ywekzj/fire_smoke/1-smoke_pos_testpos05.821.mp4)
- [helmet.mp4 — helmet](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-dp63bd9x/helmet/0-helmet.mp4)
- [smoke_pos_testpos05.821.avi — helmet](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-dp63bd9x/helmet/1-smoke_pos_testpos05.821.mp4)
- [helmet.mp4 — cigarette](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-9cxby6ku/cigarette/0-helmet.mp4)
- [smoke_pos_testpos05.821.avi — cigarette](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-9cxby6ku/cigarette/1-smoke_pos_testpos05.821.mp4)

[Metrics JSON](/Users/tabbasi/Downloads/IndustrialAI/reports/cctv-only-metrics.json) · [Source notes](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-only/SOURCES.md)

## Assessment

The current fire/smoke model is not dependable on these CCTV examples: orange workwear triggers false fire detections, while diffuse ceiling smoke is detected intermittently. Helmet recognition works for some visible helmets but does not establish reliable no-helmet detection. Cigarette detection remains unvalidated on clean positive CCTV. Keep the results as development evidence, not deployment validation.
