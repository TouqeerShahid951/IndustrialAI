# Current-model test on new footage — 21 October 2026

Tested all **26 queued originals / 7,571 frames** on the Mac. The two overlapping traffic scenes were excluded. The model produces persistent smoke candidates over a factory floor/background, recognizes smoke in four of six staged smoke clips after temporal verification, and struggles with diffuse indoor haze. In one indoor clip it instead confirms fire around a bright doorway. These are measured model outputs and visual findings; the new fire/smoke labels remain unreviewed, so target-task precision, recall and false-alert rates are not claimed.

## Results at the unchanged settings

| Footage | Raw smoke flags | Smoke flags after timed verification | Other findings |
| --- | --- | --- | --- |
| 8 real factory CCTV clips | 2 clips (W04, W08) | Same 2 clips | No fire candidates; large smoke boxes over floor/background look suspicious on visual inspection |
| 6 staged smoke clips | 5 clips | 4 clips (B03–B06) | B01 has only one smoke detection; B02 has none. Bright doorway produces fire candidates in both; B02 survives confirmation |
| 12 industrial-emission time-lapses | 6 clips | Not applicable | Separate appearance-only comparison below |

A flag means at least one model candidate in a clip. A confirmation means the existing trailing-window rule accepted at least one box. Neither is a reviewed true incident. No labels, checkpoint or filter defaults were changed.

## Factory failure examples

W01, W02, W03, W05, W06 and W07 produced no fire/smoke boxes. The two flagged clips share the alternate factory view. W04 covers a mostly stationary scene; W08 includes a moving forklift. Their smoke boxes cover large parts of the floor and machinery rather than a distinct localized plume. The exact visual cause is not established; the evidence does not support blaming only the forklift or any particular object.

| Clip | Raw smoke boxes / frames containing smoke boxes | Timed frames | First confirmation from clip start |
| --- | --- | --- | --- |
| W04 | 75 boxes / 75 of 75 frames | 50 | 1.000 s |
| W08 | 53 boxes / 51 of 101 frames | 18 | 1.049 s |

The timed rule retains one merged smoke candidate event in each factory clip. Their persistence explains why temporal verification does not remove them. Full smoke-negative labels still need confirmation; these are suspected false alerts based on inspected frames, not counted benchmark false positives.

![Factory detections](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/factory-detections.jpg)

## Staged smoke clips

| Clip | Source scene | Smoke frames before → after timed verification | First confirmed smoke timestamp | Fire output |
| --- | --- | --- | --- | --- |
| B01 | Diffuse indoor haze | 1 → 0 / 483 total | — | 2 raw frames; 0 confirmed frames |
| B02 | Same room, person/bright doorway | 0 → 0 / 342 total | — | 24 raw frames; 14 confirmed frames |
| B03 | Plume beside a fence | 313 → 266 / 630 total | 6.200 | None |
| B04 | Longer sequence at the same fence | 767 → 706 / 1400 total | 6.300 | None |
| B05 | Faint plume near parked vehicles | 978 → 937 / 1726 total | 10.640 | None |
| B06 | Small plume beside waste container | 749 → 709 / 900 total | 2.500 | None |

B01 produced its only smoke candidate at **6.780 s**, score **0.329**, despite diffuse haze visible in inspected frames. Its two fire candidates fall at 8.400 and 8.880 s, around the bright opening, and are rejected by temporal verification.

B02 produced **zero smoke candidates** across 342 frames. Fire candidates occur at 8.050–10.220 s and first pass timed verification at **9.100 s**. Their boxes sit on the bright doorway. Distinct flames are not evident in the inspected frames, so this is a suspected light-confusion failure pending human review.

B03–B06 contain recognized plume regions in sampled detections. Detection remains intermittent: raw boxes merge into 15 smoke events across the six clips; timed boxes merge into 16. Filtering can remove connecting samples and split one candidate interval into more fragments. More event fragments do not mean more real smoke incidents. B03/B04 also share a view and must not be treated as independent camera evidence.

All first-confirmation timestamps above are measured from **clip start**, not from a reviewed smoke onset. No onset delay or incident recall is inferred.

![Staged smoke detections](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/smoke-detections.jpg)

Orange boxes are raw smoke candidates; red boxes are raw fire candidates. B06 at 31.400 s has a visible plume with no candidate on that particular frame, illustrating intermittent recognition despite a clip-level smoke flag.

## Time-lapse supplement: source-label agreement only

RISE has six publisher smoke-emission-positive and six publisher smoke-emission-negative clips in this batch. Using any raw smoke box as a clip appearance flag:

- Flagged **2 of 6 source positives**: R01 and R06. R02, R05, R09 and R10 received no smoke boxes.
- Flagged **4 of 6 source negatives**: R03, R04, R07 and R08. R11 and R12 received no smoke boxes.

The source-positive clips include distant or faint plumes the detector fails to recognize at confidence 0.25. Several source negatives contain pale plume-like emissions and still receive strong smoke scores. R03 also gets one broad background box. These findings suggest poor discrimination for this industrial-emission task, but the publisher labels describe **industrial smoke emissions**, not fire hazards. No fire-hazard conclusion follows from this clip-label comparison. The pending routine-emission alert-policy question remains unresolved.

Time-lapse clips are excluded from temporal verification results, real-time alert delay and camera-hour exposure. The following sheet shows the highest-scoring smoke frame per flagged clip, and the midpoint for unflagged clips; it is illustrative rather than a random frame sample.

![Time-lapse appearance flags](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/emission-appearance.jpg)

## Test settings and verification

- Same cached `rabahdev/fire-smoke-yolov8n` checkpoint as the seven-clip baseline; confidence **0.25**, image size **640**, stride **1**, maximum **2,000 frames per clip**, Apple **MPS**.
- All original files have strictly increasing container timestamps; every source frame was processed successfully. Largest clip is 1,726 frames, below the limit. Original source files were used, not transcoded review previews.
- Timed verification: at least **3 overlapping same-class hits**, spanning at least **1 second**, in the trailing **2 seconds**, IoU at least **0.10**. Candidate events merge gaps up to **2 seconds**. Legacy and fixed-2-Hz event records are also retained in the machine report.
- The source files, checkpoint, inference code, CSV logs, annotations and old baseline hashes were checked. The metadata records package versions. New source annotations remain unreviewed and unchanged.
- Model prediction/box-transfer latency: p50 **8.80 ms**, p95 **10.67 ms** on this replay. This is not live capture-to-alert latency or full application throughput.
- No paid services, uploads, model training, replacement checkpoint or configuration tuning.

This sample is short, drawn from one factory plus public staged/emission footage, and may overlap unknown pretrained training sources. It cannot establish production accuracy, a dependable false-alert rate or new fire-incident recall. No actual fire-positive incident labels are available in the new set.

## Practical finding

The current checkpoint remains a development model. A persistence rule alone cannot remove stable background/light misclassification, and cannot recover weak smoke candidates that the detector rarely emits. The next comparison should use reviewed labels for the factory background, bright-doorway and diffuse-haze examples, then evaluate a second checkpoint against the same fixed examples. No thresholds were selected using these unlabeled outputs.

## Open the annotated examples

- [W04 annotated video](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/annotated-previews/W04.mp4)
- [W08 annotated video](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/annotated-previews/W08.mp4)
- [B01 annotated video](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/annotated-previews/B01.mp4)
- [B02 annotated video](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/annotated-previews/B02.mp4)

- [Full per-clip statistics, event intervals and model provenance](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/results.json)
- [Completed inference run](/Users/tabbasi/Downloads/IndustrialAI/outputs/new-footage/run-c6drqth3)
- [Source/timestamp preflight](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/preflight.json)
- [Verification](/Users/tabbasi/Downloads/IndustrialAI/reports/new-footage-test-2026-10-21/verification.json)

## Reproduce

Rerun inference with the preserved source links and checkpoint below; this creates a fresh run directory. Labels remain separate.

```sh
.venv/bin/python evaluate.py /Users/tabbasi/Downloads/IndustrialAI/outputs/new-footage-source-links/batch-5ery6brt --output outputs/new-footage --models fire_smoke --checkpoint /Users/tabbasi/.cache/huggingface/hub/models--rabahdev--fire-smoke-yolov8n/snapshots/13017fe8af477c25f5298d168e2dfede4b000753/best.pt --device mps --conf 0.25 --imgsz 640 --stride 1 --max-frames 2000 --timestamp-source container
```

The source collection and attribution are in the [collection report](/Users/tabbasi/Downloads/IndustrialAI/reports/smoke-validation-collection-2026-10-20.md). The acquisition verification there is a historical pre-inference snapshot; the new run and checks are recorded here.
