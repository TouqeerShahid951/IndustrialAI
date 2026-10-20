# Industrial Safety AI Improvement Implementation Plan

**Execution status (2026-10-20):** Tasks 1–3 software implemented and tested; footage collection, independent review, validation/test freezing and policy acceptance remain open. See [execution ledger](2026-10-20-execution-log.md).
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Execution is local and sequential; no subagent delegation is assumed.

**Goal:** Establish trustworthy evaluation, improve the detector/alert pipeline, and graduate to an operator-reviewed single-camera prototype.

**MVP scope:** Fire, smoke, smoking behavior, no-helmet detection and restricted-area entry.

**Architecture:** Keep the current Python evaluation runner and original model checkpoints as the baseline. Add traceable annotations, a fixed benchmark and timestamp-based confirmation before changing models. Validate each later subsystem independently, then assemble a single-camera application.

**Tech Stack:** Existing Python 3.12, OpenCV, Ultralytics/PyTorch with Apple MPS, stdlib JSON/CSV/unittest. FastAPI, SQLite and a small React operator view are later additions only when live monitoring starts.

**Spec:** [Improvement brief](../specs/2026-10-20-industrial-safety-improvement-design.md).

## Global Constraints

- Local Python 3.12 and Apple MPS are the initial runtime; CPU remains an explicit fallback.
- Reuse OpenCV, Ultralytics, existing evaluation scripts and stdlib unittest.
- No paid compute, external deployment, cloud account creation or facility-footage uploads in this plan's first milestone.
- Preserve original checkpoints; experimental weights and configurations are separate artifacts.
- Keep original source timestamps, model versions and source identities in results.
- Split evaluation data by camera/site/source event, never randomly by neighboring frames.
- Keep candidate detections available immediately; temporal confirmation must not erase the original evidence.
- Unknown, unassessable and inference-offline states must never be reported as safe/compliant.
- The prototype remains an operator aid; passing an engineering gate is not fire-system certification.

## Review Focus

1. Neighboring clips or re-encoded copies leak across splits: detect shared source-event IDs, camera/site overlap and duplicate hashes. Task 1.
2. Ambiguous labels or missing inference inflate accuracy: exclude ambiguity explicitly and report lost coverage separately. Task 2.
3. Irregular FPS, timestamp regression or a long camera gap confirms stale detections: reset temporal state and require a new observation history. Task 3.
4. Distant people are missed before head classification: report person-stage misses, and never turn missing evidence into compliance. Phase 3.
5. Steam, glare, camera overlays and smoking-like gestures trigger persistent alerts: include hard negatives, source-quality flags and separate per-capability results. Tasks 1–2 and Phases 3–4.

## Roadmap and gates

| Phase | Deliverable | Exit gate |
|---|---|---|
| 1. Trusted benchmark | Traceable clips, reviewed labels, frozen split membership, baseline report | Data leakage checks pass; counts and limitations are explicit |
| 2. Alert timing | Timestamp-based candidate/confirmed events | Same elapsed-time behavior across FPS; compare delay and false events |
| 3. Fire/smoke and helmets | Candidate detector/configuration improvements | Better validation tradeoff without unacceptable per-condition regressions |
| 4. Smoking and intrusion | Person-associated smoking evidence and polygon rules | Independently reviewed positive and confusing negative sequences |
| 5. Single-camera operation | Local capture, monitoring health, incidents and operator view | Meets agreed evidence/performance gates; failure recovery demonstrated |
| 6. Controlled pilot | Longer day/night trial and deployment decision | Sufficient negative camera-hours and fresh unseen incidents; no unresolved critical failures |

**Next executable scope:** Phases 1–2. Phases 3–6 are gated follow-on milestones, not permission to build every subsystem at once.

## Phase 1 — trusted benchmark

### Task 1: Create a traceable, split-safe dataset

**Files:** Create `benchmark/manifest.jsonl`, `benchmark/annotations/`, `benchmark/README.md`, `scripts/benchmark_data.py`, `tests/test_benchmark_data.py`. Modify `.gitignore` to keep video and private footage out while allowing reviewed public metadata. Keep existing `data/cctv-audit/` and reports as exploratory evidence.

**Interfaces:** `load_manifest(path: Path) -> list[dict]` and `validate_manifest(clips: list[dict]) -> list[str]` in `scripts/benchmark_data.py`. Validation returns a list of concrete errors; the CLI exits nonzero when it is nonempty. Clip/annotation fields and canonical class/event names follow the spec.

- [x] Write tests for duplicate hashes, shared source events across splits, camera/site overlap, invalid time ranges, missing files and unverified-demo clips in locked_test.
- [x] Run `.venv/bin/python -m unittest discover -s tests -p test_benchmark_data.py -v`; observe the missing validation behavior fail.
- [x] Implement the manifest loader/validator with pathlib, hashlib and JSON. Store source hashes once and recheck on benchmark runs. Do not store credentials or RTSP URLs in public metadata.
- [x] Record existing clips as development examples. Mark the construction sample's capture provenance unverified; flag the workshop's source contours. Neither is a final accuracy test.
- [ ] Obtain authorized clean recordings. Start with at least three camera views from three independent site groups where available, so development, validation and locked_test can remain site-disjoint. Record any shortfall instead of claiming diversity.
- [ ] Initial collection target: ten positive clips per capability and ten confusing negatives per capability; clips may cover multiple capabilities. Include faint/diffuse smoke, verified steam, lights/welding/glare, orange clothing, distant and occluded heads, smoking, eating, drinking and phone use. No staging fires for collection.
- [ ] Obtain the user-selected smoking video as a local file when network access permits or the user attaches it. Record source overlays/editing; keep this already-selected example in development.
- [ ] Review event intervals and sampled object boxes independently of model predictions. Have a second reviewer adjudicate ambiguous labels; if unavailable, keep single-reviewer status and do not label it independent validation.
- [ ] Collect continuous negative footage, working toward at least 24 negative camera-hours across day/night conditions for a preliminary false-alert estimate. Report actual hours and uncertainty; this amount is not automatically a production-readiness gate.
- [ ] Assign development, validation and locked_test by grouped camera/site/source event, then freeze test membership and manifest hash.
- [x] Run `.venv/bin/python scripts/benchmark_data.py benchmark/manifest.jsonl` and the project unittest command. Save the validation report and dataset inventory.

**Done:** A reviewer can trace every label to a source, identify exclusions and verify split separation. Insufficient footage is a recorded data gap, not a passing score.

### Task 2: Measure events and failure conditions

**Files:** Extend `scripts/audit_metrics.py`; create `scripts/benchmark_events.py` and `tests/test_benchmark_events.py`. Reuse `evaluate.py` outputs and `temporal.iou`; retain the existing audit metrics unchanged.

**Interfaces:** `score_events(expected: list[dict], predicted: list[dict], negative_seconds: float) -> dict` in `scripts/benchmark_events.py`. Each event has clip_id, kind, start_seconds and end_seconds. Return TP, FP, FN, event_recall, false_events_per_camera_hour and confirmation_delays_seconds. Undefined denominators return null, never zero or a fabricated perfect score.

- [x] Write a test with one reviewed smoke event `[10, 20]` and one prediction `[12, 18]`: TP=1, FN=0, delay=2 seconds. Add a second prediction in that same reviewed event and require one unmatched duplicate alert.
- [x] Test a wrong-class prediction, zero negative observation time, ambiguous intervals and monitoring gaps. Require null rates when exposure is insufficient and separately reported excluded/unmonitored time.
- [x] Observe these tests fail, then implement one-to-one, class-aware interval matching and the spec's fixed two-second candidate-gap merging rule.
- [x] Produce counts and rates by camera, condition and capability. Include p50/p95 processing latency, confirmation delay and monitoring coverage. Keep confidence scores distinct from measured accuracy.
- [x] Generate a baseline using original checkpoints only. Pin model file hashes, manifest hash, device, confidence, image size, code version and sampling policy in each report.
- [ ] Agree provisional development targets before tuning. Suggested starting targets from the brief: ≥90% event recall, ≤1 false alert per eight negative camera-hours, and fire/smoke p95 confirmation delay ≤5 seconds from visually assessable evidence. Treat these as proposed engineering targets, not safety certification.
- [x] Run `.venv/bin/python -m unittest discover -s tests -v`, then benchmark development/validation data. Keep locked_test closed during repeated experiments. Completed on development data only; independent validation data is unavailable.

**Done:** A reproducible report explains which events were missed, which alerts were false, how long confirmation took and how much footage was actually monitored.

## Phase 2 — timestamp-based verification

### Task 3: Replace FPS-dependent confirmation in the experiment pipeline

**Files:** Extend `temporal.py` and `tests/test_temporal.py`; adapt `scripts/time_sampling_audit.py` and `scripts/compare_temporal.py`. Keep `confirm()` available so historical reports can be reproduced.

**Interface:** `confirm_timed(frames: list[list[dict]], timestamps: list[float], min_hits: int = 3, min_span_seconds: float = 1.0, window_seconds: float = 2.0, overlap: float = 0.1) -> list[list[dict]]` in `temporal.py`. It returns confirmed current-frame boxes, retaining the existing class/bbox schema.

- [x] Write tests using matching boxes at timestamps `[0, 0.5, 1.0]`: the first two frames are unconfirmed; the third confirms. Dense observations spanning less than one second must not confirm early.
- [x] Test different FPS, missing/empty frames, unrelated spatial boxes, timestamps moving backward and gaps longer than two seconds. Reject invalid timestamps; discard stale history after long gaps. A dropped frame must not fabricate positive evidence.
- [x] Observe failures, then implement causal timestamp-window voting: at least three same-class overlapping observations within two seconds, spanning at least one second, including the current detection. Keep these values configurable for validation.
- [x] Preserve immediate candidate detections and attach confirmation state separately. Describe state changes using observed timestamps, not playback or request-count time.
- [x] Compare raw predictions, legacy voting, fixed-rate voting and timed voting on development/validation data. Report event recall, false event rate and added delay; do not select a policy from locked_test results. Completed on development data only; independent validation data is unavailable.
- [x] Run the complete unittest suite and save the comparison report. Keep timed voting experimental until its validation tradeoff is accepted.

**Done:** Confirmation has documented elapsed-time semantics and measurable costs. The existing persistent-headlight/white-plume failures remain explicit if the filter does not solve them.

## Phase 3 — targeted detector improvements

Plan detailed implementation after Phases 1–2 establish a trustworthy baseline.

### Fire/smoke track

- [ ] Curate more positive diffuse-ceiling-smoke examples and matched hard negatives. Verify what is actually steam; do not relabel an unexplained white plume by appearance alone.
- [ ] Review all training annotations and class IDs. Include both early smoke and established hazards; balance negatives without overwhelming the small positive set.
- [ ] Compare camera-specific input size and crop/tiling configurations against full-frame inference, keeping coverage of the entire required detection area explicit.
- [ ] Run one bounded fine-tuning experiment using grouped training/validation splits, with a fixed compute budget and original checkpoint baseline. Retain the rejected pilot as historical evidence; do not overwrite it.
- [ ] Reject any candidate whose validation gains come from hiding hazards, losing early smoke, adding persistent false alerts or unacceptable latency. Choose configuration on validation, then evaluate once on fresh locked_test.

### Helmet track

- [ ] Measure person-detection coverage first, then associate head evidence with detected/tracked people. Reuse the existing YOLO runtime for a lightweight person detector; evaluate the extra model before committing to it.
- [ ] Compare full-frame resolution with person/head crops. Keep camera-specific usable head size and camera angle limitations explicit.
- [ ] Add uncovered heads, helmeted heads, occlusion and confusing objects such as cable reels. Score the whole selected scene, not only the worker whose result improved.
- [ ] Require a head prediction to be spatially associated with a person before proposing a PPE violation. Missing person/head evidence becomes unknown, not compliant.
- [ ] Promote a candidate only after matched validation metrics improve without unacceptable person-stage misses or false violations.

**Gate:** Demonstrated validation improvement with condition-level results; a tiny target-only improvement does not pass.

## Phase 4 — smoking and restricted-area capability

### Smoking

- [ ] Test the exact user-supplied video first as a development example, after inspecting its source quality and overlays.
- [ ] Create independently labeled positive/negative sequences from multiple viewpoints. Keep eating, drinking, phone use and face touching as explicit hard negatives.
- [ ] Associate visible cigarette evidence with a tracked person. Establish whether the camera provides enough detail before trying a larger model.
- [ ] Compare object-only, person-crop and short-sequence verification. Use operator-review candidates for ambiguity; do not equate a cigarette box with confirmed smoking.
- [ ] Measure event recall, false accusations/alerts and delay on held-out sequences. Mark the capability unavailable when the view cannot resolve the evidence.

### Restricted areas

- [ ] Add one polygon per camera using image coordinates and a person track's foot point for entry.
- [ ] Test boundaries, entry/exit, occlusion, ID switches and active hours. Document a boundary policy and suppress duplicate alerts for the same continued entry.
- [ ] Save event time, track reference, zone and evidence. Keep this capability's metrics separate from appearance-model accuracy.

**Gate:** Both capabilities have positive and confusing negative test sequences and documented limits. All five original MVP capabilities remain in scope.

## Phase 5 — one-camera operator prototype

- [ ] Add OpenCV capture for one file/RTSP source with a bounded latest-frame queue. Explicitly configure source credentials locally; do not include them in logs.
- [ ] Add camera-disconnected, stale-frame, inference-offline and unassessable statuses. Test camera reconnects and inference failure without falsely showing safe status.
- [ ] Persist local incidents and evidence using SQLite and the filesystem. Include camera, event kind, candidate/confirmed status, timestamps, model/configuration identity and operator review.
- [ ] Add FastAPI and one React operator view for video, status and incident review. Avoid multi-tenant accounts, multiple services and a separate database server for this local prototype.
- [ ] Define evidence retention and verify its bounded storage behavior before continuous runs. Do not delete existing user footage.
- [ ] Measure end-to-end capture-to-candidate and capture-to-confirmation latency, dropped frames, memory, CPU/MPS load and thermal behavior during a sustained run. Offline model FPS is not this measurement.

**Gate:** An operator can see an incident, inspect evidence, understand uncertainty and recognize when monitoring is offline.

## Phase 6 — controlled pilot and next decision

- [ ] Run longer authorized day/night trials with frozen thresholds and per-camera conditions recorded.
- [ ] Report per-capability counts, confidence intervals, false events per camera-hour, delays and monitoring coverage. Insufficient positives or observation time remain explicit limitations.
- [ ] Decide whether to continue with the Mac, improve camera placement, rent GPU compute or expand to multiple cameras using actual bottlenecks and data volume.
- [ ] Consider PostgreSQL, multi-camera workers or cloud inference only when concurrency, operational needs or measured throughput justify them.

## Stop / rollback rules

- A new checkpoint that regresses held-out behavior stays experimental.
- A threshold that reduces false alerts by missing required hazards does not pass.
- Missing labels, uncertain source provenance or leaked splits prevent accuracy claims.
- A lost stream or failed model is an unavailable capability, never a clean safety result.
- A failed gate leads to one bounded follow-up experiment with a stated hypothesis; it does not trigger a larger dashboard build.

## Immediate execution order

1. Obtain the exact smoking clip and clean facility-style recordings; inventory existing sources.
2. Complete Task 1, then Task 2: trustworthy data and event-level baseline.
3. Complete Task 3: timestamp-based confirmation, with measured delay/false-alert effects.
4. Use those results to write the narrower Phase 3 model-experiment plan.

Tasks 1–3 software was executed on 2026-10-20; open data/policy gates and later milestones remain unchecked. No calendar delivery date is promised before data access is known. If the project is later placed under Git, record each independently verified task as its own commit; do not initialize a repository solely to satisfy this plan.
