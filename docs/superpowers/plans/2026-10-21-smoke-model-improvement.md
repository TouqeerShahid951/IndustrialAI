# Smoke model improvement execution plan

> **For agentic workers:** Execute inline using superpowers:executing-plans. The user explicitly requested all four steps. Keep data, checkpoint artifacts and reports separate from the existing defaults.

**Goal:** Review four smoke failures, compare the existing checkpoint with two distinct alternatives, expand industrial negative footage, and run one justified local fine-tuning experiment.

**Architecture:** Reuse evaluate.py, temporal.py and the existing hash-pinned recording/scoring helpers. New artifacts are data, model weights and comparison reports; no live-service or application behavior changes are planned.

**Tech Stack:** Existing Python 3.12, Ultralytics, OpenCV, Apple MPS, requests, and stdlib.

**Spec:** 2026-10-20-industrial-safety-improvement-design.md, plus the user's 2026-10-21 request to execute the four-step smoke improvement sequence.

## Global constraints

- Local Mac compute only; no paid services, uploads, account creation or deployment.
- Preserve current checkpoints, historical reports, old labels and default settings.
- Keep raw candidates and source container timestamps; use confidence 0.25, image size 640 and stride 1 for comparisons.
- Keep training separate by source camera/site/incident; never split neighboring frames randomly.
- Assistant annotations are explicitly single-reviewer drafts until independently confirmed. No production accuracy or locked-test claim.
- RISE time-lapse remains appearance-only, separate from fire-hazard and temporal metrics.
- No application implementation is planned, so work uses ignored data/artifact directories in the shared checkout; no Git resets, commits or worktree copies of footage.

## Review focus

- Alternative checkpoints must have distinct hashes and canonical fire/smoke classes; label order must be read, not assumed.
- Unknown plume composition must stay uncertain; diffuse haze cannot be equated with verified combustion.
- Factory clips from one site remain grouped; stitched clips do not become continuous camera exposure.
- Training must not use comparison scenes or their near-duplicates. Record pretraining overlap as unknown.
- Fine-tuning can regress; compare the exact same held-out examples and retain the original default regardless of this pilot outcome.

## Tasks

- [x] Reviewed W04/W08 and B01/B02 using chronological unannotated sequences and denser onset samples; saved source hashes and validated separate assistant single-reviewer annotations. The user delegated assessment because remote video playback was unavailable. Human independent review is not claimed.
- [x] Pin and inspect two accessible alternative checkpoints. Run the same sources/settings as the baseline, confirm completed logs/hashes/full frame coverage, and report raw/timed behavior and available reviewed-label scores. Keep provisional-label comparisons identified.
- [ ] Find longer real industrial recordings with suitable access/reuse terms. Download a bounded sample, fully decode, screen for source realism, and preserve actual camera duration. If long industrial CCTV remains inaccessible, record the verified gap and do not replace it with stitched short clips or synthetic footage.
- [ ] If comparison failures remain and adequate training labels can be obtained, fine-tune the strongest candidate once, locally: at most 10 epochs, 640 input, bounded batch for MPS, fixed seed, no external logging. Use a new checkpoint directory and leave the production/default configuration untouched. Compare before/after against a fixed evaluation set. If labels are too weak or split leakage cannot be excluded, prepare a runnable training configuration and record the unmet condition rather than fabricate a successful improvement.
- [ ] Verify source/model/annotation/log hashes, full frame counts and source split isolation. Save an outcome report that distinguishes completed work, experimental results and genuine remaining dependencies.

## Rulings

- The user's “Lets do it all” authorizes this sequence and local experimental training. No further plan-approval round is needed.
- Earlier tiny fine-tuning regressed; reusing that 20-image training set alone is not a justified new experiment. Seek additional published boxes and reviewed negatives first.
- Independently confirmed labels are not inferred from silence on the asynchronous review question.

## Outcome at 2026-10-21

- Four delegated assistant reviews and all three-model comparisons complete: 33 original sources/12,700 frames per model, plus two longer factory clips/1,038 frames per model. Current default unchanged.
- Longer-source search produced two additional real factory clips totaling 41.64 seconds, still far short of hours; process haze labels remain uncertain. Access/usage/timing gaps are recorded rather than hidden. Long-duration negative validation remains open.
- Inspected 600 published training row/box records. Adequate source-isolated industrial labels were not established, so no fine-tune was run. A bounded ten-epoch recipe and precise data conditions were prepared. Fine-tuning remains open.
- The user's latest instruction authorizes assistant visual labels without further playback confirmation. Labels remain identified as assistant single-reviewer, and unresolved fire/late-haze windows remain uncertain.
- Detailed evidence: reports/smoke-improvement-2026-10-21/outcome.md.
