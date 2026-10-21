# Seven-clip development evaluation — 20 October 2026

The current checkpoint detected both labeled fire incidents. The timed rule removed all three unmatched fire alerts, but rejected the only labeled smoke incident and retained one false smoke alert. Keep the checkpoint for development; this evidence does not support adopting the same confirmation rule for both classes or promoting the system to production.

## Measured event results

Each cell is **detected incidents / unmatched alerts / missed incidents**. These are event counts, not frame accuracy.

| Policy | Fire (2 labeled incidents) | Smoke (1 labeled incident) |
| --- | --- | --- |
| Raw detections, merged into events | 2 / 3 / 0 | 1 / 2 / 0 |
| Legacy 3-of-5 frames | 2 / 2 / 0 | 1 / 2 / 0 |
| 2 Hz sampling + legacy rule | 2 / 1 / 0 | 0 / 1 / 1 |
| Timed confirmation | 2 / 0 / 0 | 0 / 1 / 1 |

Timed confirmation requires at least three spatially overlapping same-class hits spanning at least one second within a trailing two-second window. Events merge gaps of up to two seconds. A predicted event matches a labeled incident if their observable intervals overlap; a repeat event after a gap counts as an unmatched alert. Event detection does not establish continuous tracking throughout an incident.

## Findings by clip

| Clip | Your label | Result |
| --- | --- | --- |
| 001: red clothing | No fire, no smoke | No raw candidates or confirmed alerts. |
| 002: night signs/traffic | No fire, no smoke | Two raw fire events at approximately 0.46–1.00 s and 7.21–7.25 s; timed confirmation removed both. |
| 003: indoor screen/motion | No fire, no smoke | Two raw smoke events at 13.83–16.08 s and 24.04–24.67 s; timed confirmation retained one at 14.83–16.08 s. |
| 004: cloudy landscape | No fire, no smoke | No raw candidates or confirmed alerts. |
| 005: Arson049 | Fire approximately 3–12 s; smoke uncertain | First raw fire at 4.30 s, timed confirmation at 5.30 s: approximately 2.30 s after your labeled start. |
| 006: Arson012 | Fire approximately 8 s through end; smoke uncertain | First raw fire at 7.23 s, timed confirmation at 8.27 s. The timed merged event ended at 20.13 s despite the label continuing to 29.80 s. Raw/legacy had a later repeat fire event, counted as an unmatched alert. |
| 007: Arson017 | Smoke approximately 34–40 s; no fire | Raw smoke only at 35.10–35.50 s; legacy confirmation at 35.23 s. Timed and 2 Hz policies missed this event. A brief raw fire candidate at 43.10 s lies outside reviewed CCTV time and is excluded. |

Intervals above are bounds of merged events and can contain gaps. Clip 006's raw onset precedes your approximate label; the scorer clips negative onset delay to zero, so that number does not establish exact onset accuracy. The missing late fire detections remain a weakness even though event recall is 2/2.

## Review coverage and provenance

- Seven original files, **5,129 frames**, **191.525 seconds** of media, all frames processed successfully on Apple MPS. No frame stride or truncated runs; container timestamps used.
- Fire: 187.592 seconds reviewed and monitored, including 156.792 seconds labeled negative.
- Smoke: 108.792 seconds reviewed and monitored, including 102.792 seconds labeled negative and the six-second positive interval.
- Smoke in clips 005–006 is ambiguous and excluded: 42.667 seconds. Smoke outside 34–40 s in clip 007 remains unreviewed. Fire after 12 s in clip 005 and after 43 s in clip 007 remains unreviewed. Unknown periods never become negative labels.
- Reviewed-time monitoring coverage is 100%; that describes replay coverage, not detector accuracy.
- Checkpoint: `rabahdev/fire-smoke-yolov8n`, cached snapshot `13017fe8af477c25f5298d168e2dfede4b000753`, original weights. Confidence 0.25, image size 640, stride 1, maximum 2,000 frames per clip. Settings were unchanged during this evaluation.
- Manifest, original source files, annotations, checkpoint, inference code, scoring code and CSV artifacts have SHA-256 provenance. Completed runs and all source frame counts were checked. No detector or application behavior was changed.

The machine report includes unmatched alerts divided by negative camera-hours, including repeat alerts during positive incidents. The negative exposure is only 2.61 minutes for fire and 1.71 minutes for smoke; these rates are unstable and cannot establish an operational false-alarm rate. Zero observed fire false alarms after filtering is not evidence of zero risk.

## Next work

1. Review smoke boxes around 35.1–35.5 s and the false smoke event around 14.8–16.1 s, then collect additional faint/intermittent smoke and steam/dust negatives from the intended camera setting. Temporal filtering cannot recover smoke the detector never recognizes.
2. Compare smoke-specific confidence and confirmation settings on a separate validation set. Keep fire and smoke settings separately assessable. Preserve this report as the baseline; do not select settings and report their accuracy on the same seven clips.
3. Obtain permissioned industrial CCTV from multiple cameras, including extended negative periods, day/night conditions, steam, headlights, workwear and distant subjects. Independently review labels and split by camera/site/incident before fine-tuning or testing a replacement model. PPE and smoking need their own labeled footage; this replay did not evaluate them.

All seven clips remain development data with single-user review and approximate event boundaries. The four KMU lookalike clips are supplementary negatives; the three UCF examples depict property/parking/roadside surveillance, not verified factory cameras. Source overlays/editing, commercial-use permission and possible training overlap remain unresolved. The two manifest camera/site groups are conservative unknown-provider groups, not two verified independent cameras. Production/locked-test gates remain unmet.

## Reproduce and inspect

```sh
.venv/bin/python scripts/run_benchmark.py benchmark/chat-review-manifest.jsonl \
  --runs-json reports/chat-review-runs.json \
  --output reports/chat-review-benchmark.json
```

- [Manifest](/Users/tabbasi/Downloads/IndustrialAI/benchmark/chat-review-manifest.jsonl)
- [Full metrics and inference provenance](/Users/tabbasi/Downloads/IndustrialAI/reports/chat-review-benchmark.json)
- [Completed inference run directories](/Users/tabbasi/Downloads/IndustrialAI/reports/chat-review-runs.json)
- [Verified inventory](/Users/tabbasi/Downloads/IndustrialAI/reports/chat-review-inventory.json)
- [Final replay verification](/Users/tabbasi/Downloads/IndustrialAI/reports/chat-review-verification.json)
