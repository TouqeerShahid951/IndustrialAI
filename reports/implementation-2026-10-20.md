# Improvement milestone implemented — 2026-10-20

Phases 1–2 software is implemented locally on this Mac. The original checkpoints are unchanged. No new dependencies, cloud services or live-camera application were added. Data collection/review gates remain open.

## Implemented

- JSONL dataset validation, source hashes, camera/site/event split checks and a non-overwriting test-lock mechanism.
- Reviewed event/negative intervals, ambiguity/offline exclusions, coverage, one-to-one event counts and per-camera/condition reports.
- Per-frame observations and latency, completed-run validation, checkpoint/source/annotation/scoring-code provenance.
- Causal elapsed-time verification with raw, legacy, fixed-2-Hz and timed comparisons; raw evidence remains intact.
- Head-object matching at IoU 0.5 and 0.3, separate from continuous no-helmet event assessment.

## Development replay

Two sources, 124.583 source seconds total, four complete model/video replays (1,748 analyzed model-frames), Apple MPS, confidence 0.25, image size 640, stride 1. Fire and smoke were reviewed for both clips. The workshop source has existing contours; construction capture provenance and permission review remain unresolved. Labels have one reviewer and are not independent of earlier model inspection.

| Capability | Policy | TP | FP / repeat alerts | FN | First confirmation delay |
|---|---|---:|---:|---:|---:|
| fire | raw | 0 | 1 | 0 | N/A (no positive event) |
| fire | legacy | 0 | 1 | 0 | N/A (no positive event) |
| fire | fixed_2hz | 0 | 0 | 0 | N/A (no positive event) |
| fire | timed | 0 | 0 | 0 | N/A (no positive event) |
| smoke | raw | 1 | 2 | 0 | 0.000 s |
| smoke | legacy | 1 | 2 | 0 | 0.426 s |
| smoke | fixed_2hz | 1 | 1 | 0 | 1.706 s |
| smoke | timed | 1 | 2 | 0 | 1.066 s |

The timed rule removes the construction clip’s brief false fire event. All policies find the one workshop smoke incident, already visible at clip start. Timed voting delays the first alert by 1.066 seconds and still generates two unmatched repeat alerts during that incident. This is not evidence of general recall or reliable false-alarm suppression.

Fire has only 124.583 reviewed negative seconds (0.0346 hours), with no positive fire incident. Smoke has only 15 negative seconds (0.00417 hours). The report’s rate includes all unmatched alerts, including duplicates during a positive incident: timed fire = 0/h and timed smoke = 480/h on those denominators. These short, reused examples cannot establish the proposed operating targets. Undefined rates/recall remain null.

| Head category | IoU | TP | FP | FN | Reviewed frames |
|---|---:|---:|---:|---:|---:|
| helmet | 0.5 | 8 | 0 | 0 | 4 |
| helmet | 0.3 | 8 | 0 | 0 | 4 |
| no_helmet | 0.5 | 0 | 0 | 4 | 4 |
| no_helmet | 0.3 | 0 | 0 | 4 | 4 |

Fire/smoke prediction latency over 874 observations: p50 11.14 ms; p95 14.81 ms, including box transfer and first-frame warmup. This excludes capture-to-alert latency and is not a live throughput qualification.

No-helmet event recall, smoking and restricted-entry event results are **not annotated**, rather than safe/passing. Helmet object tests show the distant-head failure remains.

## Verification and review

All **20 unittest checks pass**. Regression checks cover truncated footage coverage, capability-specific exclusions, unreviewed annotations, annotation/scoring provenance and isolation of models in the sampling audit. A separate read-only review found these five issues; all were corrected in one test-first pass. The integrated head test additionally distinguishes IoU 0.3 from 0.5. Manifest validation passes. The final benchmark rechecks all four completed inference runs and reports `gate_passed=false`.

- [Full benchmark JSON](benchmark-baseline.json)
- [Run directory inventory](benchmark-baseline-runs.json)
- [Dataset validation](benchmark-inventory.json)
- [Test output](implementation-tests.log)
- [Usage / scoring contract](../benchmark/README.md)
- [Execution ledger and plan rulings](../docs/superpowers/plans/2026-10-20-execution-log.md)

## Open gates

Authorized clean footage from independent camera/site groups, positive/confusing-negative sequences, independent label review, sufficient continuous negative exposure and accepted operating targets are still missing. No validation or locked test set has been fabricated. The selected smoking video (YouTube `1_0NMTqbAC0`) remains unavailable locally; this execution’s download-tool installation retry failed on network access. No smoking-video evaluation is claimed.

The next model experiment should address diffuse-smoke continuity and distant uncovered heads after those evidence gaps are filled. Phases 3–6 remain gated follow-on work; the software milestone does not certify production safety.
