# Execution ledger — plan: 2026-10-20-industrial-safety-improvement-plan.md

## Scope and pre-flight

Implement Tasks 1–3 (Phases 1–2), the plan's explicitly executable scope. Phases 3–6 remain gated by credible evaluation evidence.

- Baseline: six existing unittest checks pass.
- Task 1 produces validated manifests/annotations; Task 2 consumes them and saved prediction logs. Task 3 preserves the existing class/bbox schema. Interfaces are compatible.
- Ruling: no Git/worktree/commit helper runs because this workspace is not a Git repository and the plan explicitly forbids initializing one solely for process. Keep this ledger as the durable record. Cost: no commit-based rollback/history.
- Ruling: merge per-frame candidates into events before scoring; score_events treats event records as distinct so duplicate alerts remain false positives. This resolves the plan's candidate-merging versus duplicate-alert test ambiguity. Cost: callers must not submit raw frame boxes as final events.
- Ruling: existing clips remain development data. Independent cameras, permission/provenance review, second-review labels, long negative exposure and clean smoking footage are evidence gaps, not fabricated completed tasks. Cost: production/data-quality gates remain unmet.

## Tasks

- Task 1: software/inventory complete — 4 validator tests pass; two development clips registered with source hashes and annotations. Independent collection/review/test freezing remains open.
- Task 2: core event scorer complete — 4 tests pass; candidate merging stays separate from duplicate event scoring. Run provenance/coverage integration test passes.
- Task 3: timed filter implemented — elapsed-time, high-FPS, empty-frame, stale-window, geometry and invalid-timestamp checks pass. Legacy filter retained.
- Ruling: add optional excluded_intervals to score_events; negative_seconds is already reviewed/monitored exposure. This lets ambiguity and monitoring gaps be represented without silently scoring them as negatives. Cost: callers must supply correctly reviewed exposure; the benchmark runner computes it.
- Ruling: add frames.csv and metadata.json to evaluate.py and use container timestamps by default, with an explicit nominal option. Legacy logs lack per-frame latency/provenance and are diagnostic only; rerun original checkpoints for the benchmark. Cost: old runs cannot establish a new trusted baseline without rerunning.


## Final review and verification

- A fresh-context read-only reviewer found five issues: truncated-tail coverage inflation; cross-capability exclusion leakage; unreviewed labels scored as reviewed; missing annotation/scorer/temporal provenance; and sampling-audit model mixing. All were corrected in one test-first pass, with regression checks. No unresolved review findings remain in this scope.
- Spec follow-through: sampled head matching is reported at both IoU 0.5 and 0.3, with a regression example whose result changes between thresholds.
- Final verification: 20 unittest checks pass (`reports/implementation-tests.log`); manifest validation passes (`reports/benchmark-inventory.json`); four original-checkpoint MPS replays are rescored in `reports/benchmark-baseline.json`.
- Observed timed-voting result: construction false fire event 1 → 0; workshop smoke first confirmation 1.066 s, with two repeat alerts retained as unmatched FP. Nearby helmet TP=8; uncovered-head TP=0, FN=4 at both reported IoUs.
- Ruling: false-event rate counts all unmatched alerts (including repeats in positive incidents) over reviewed monitored negative hours, matching the explicit duplicate-alert contract. Cost: this is not a negative-scene-only false-alarm estimate; report numerator semantics and the tiny 15-second smoke denominator explicitly.
- Ruling: coverage uses observed timestamps; final samples cover at most the sampling cadence, never the unseen tail of a truncated run. Gaps over two seconds do not bridge coverage. Cost: small residual tails can remain unmonitored rather than falsely counted.
- Source acquisition: selected smoking video remains unavailable; the attempted download-tool installation failed due to network timeout. No local test of that video is claimed.
- No further detector training or dashboard build: current footage and single-reviewer labels do not satisfy evidence gates. This is the plan's explicit phased scope, not a new approval requirement.

## Completion boundary

Tasks 1–3 software complete. Data collection, independent review, validation/locked-test creation and accepted target policy remain incomplete and visible in the plan. Phases 3–6 remain gated. Run instructions and scoring limitations are in `benchmark/README.md`; measured results are in `reports/implementation-2026-10-20.md`.

## Seven human-reviewed public clips: additional development replay

- Registered a separate `benchmark/chat-review-manifest.jsonl`; original two-clip baseline unchanged. Preserved uncertain/unreviewed windows; all labels remain single-reviewer development labels. Unknown provider camera/site groups do not establish independence.
- Replayed the original cached fire/smoke checkpoint over all 5,129 source frames on MPS, confidence 0.25, size 640, stride 1. Seven completed runs; source/checkpoint/artifact/annotation/code hashes and full frame counts verified in `reports/chat-review-verification.json`.
- Fire raw TP/FP/FN=2/3/0; timed=2/0/0. Smoke raw=1/2/0; timed=0/1/1. Smoke at 35.10–35.50 s is rejected by the one-second span rule; a false smoke event survives. Fire event recall does not capture late missing detections in clip 006.
- Result: no model/filter defaults changed. Smoke-specific validation and detector evidence are the next priority, alongside permissioned target-camera footage and independent labels. No training or production qualification. Report: `reports/chat-review-evaluation-2026-10-20.md`.

## Focused smoke failure inspection

- Visually examined original clip 003 and clip 007 sequences with recorded box overlays. Persistent false smoke boxes surround a moving person; a later short event is on television content. Labeled CCTV smoke has only ten above-cutoff matching frames spanning 0.367 s, so the one-second confirmation requirement rejects it.
- Reproduced original timed smoke event records exactly for all seven clips. One-factor log replays show span 0.25 s recovers the smoke but increases unmatched smoke events from 1 to 2; confidence 0.50 still retains a false event.
- Two completed diagnostic inference runs at confidence 0.10, same original checkpoint and all 2,244 frames, permit true smoke confirmation at 36 s but two false events in the room clip. Hashes/frame counts checked. An initial extensionless-cache-path load attempt was incomplete and excluded.
- No defaults changed. Detailed evidence and selected frame sheets: `reports/smoke-failure-inspection/inspection.md`. Next evidence need remains separate smoke validation footage with faint smoke and people/monitor/steam/dust negatives.

## Additional smoke-validation footage acquisition and screening

- Acquired 28 source videos / 88,116,966 bytes; decoded all 7,886 frames. Eight real factory CCTV samples from Önal/Dandıl (CC BY 4.0, revision-pinned Voxel51 mirror, upstream LFS hashes verified), eight Bilkent library samples, and twelve RISE industrial-emission time-lapses (CC0).
- Retained 26 candidates: fourteen primary (eight factory negative candidates and six staged smoke candidates) plus twelve time-lapse appearance supplements. Excluded two traffic clips because their camera scenes already appear in older FIRESENSE downloads, despite different hashes. All related views/sites/unknown incidents conservatively grouped.
- Kept RISE emission labels separate from fire-hazard labels; time-lapse clips cannot establish real-time confirmation, alert latency or camera-hour exposure. Routine-emission alert policy was asked asynchronously; current working target remains fire-related smoke.
- Source access audit: SteelBench HTTP 401; NVIDIA warehouse archive listing accessible but EULA purpose unsuitable for this Mac detector evaluation, so no warehouse videos acquired. Generic/synthetic alternatives not substituted for target footage.
- Prepared six H.264 previews with original frame counts and 28 explicitly unreviewed annotation records; 26-item queue starts with smoke. No new detector inference, training, threshold selection, reviewed hazard ground truth or model ranking claimed. New source pool remains candidate-only until semantic labels and independence checks are complete.
- Verification: all 28 source hashes, eight upstream LFS hashes, six preview hashes/frame counts and all prior baseline/label hashes pass. Collection report and runnable integrity check: `reports/smoke-validation-collection-2026-10-20.md`; verification: `data/smoke-validation-candidates-2026-10-20/verification.json`.

## 21 October 2026 — test of all new queued footage

- Replayed the unchanged cached fire/smoke checkpoint over all 26 queued original sources / 7,571 frames, MPS, confidence 0.25, size 640, stride 1, max 2,000 per clip. The two overlapping traffic clips stayed excluded. All observations succeeded with valid increasing container timestamps.
- Factory: no candidates in six of eight clips; W04/W08 produce persistent smoke boxes over broad floor/background regions, retained by timed verification. These are visually suspicious candidates; full smoke-negative labels remain unreviewed, so no benchmark FP rate is claimed.
- Staged smoke: raw smoke in five of six clips, timed smoke in four (B03–B06). B01 has a single smoke candidate; B02 has none and instead retains a fire candidate around the bright doorway. Raw/timed merged smoke event counts 15/16 illustrate fragmentation, not incident count.
- RISE appearance-only check flags two of six publisher smoke-emission positives and four of six negatives. Emission labels do not establish fire hazards. No time-lapse temporal performance, latency or negative exposure is reported.
- Verified source/checkpoint/code/CSV/annotation hashes, all frame sequences and reproduction of temporal event records from saved logs. Four H.264 annotated previews retain original frame counts. Original baselines, candidate labels and model/filter defaults unchanged. No training or production qualification.
- Report: `reports/new-footage-test-2026-10-21.md`; machine results and verification: `reports/new-footage-test-2026-10-21/`. Acquisition verification remains a historical snapshot from before this inference run.
