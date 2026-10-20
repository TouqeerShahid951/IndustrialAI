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
