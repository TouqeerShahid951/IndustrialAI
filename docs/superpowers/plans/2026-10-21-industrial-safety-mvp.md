# Industrial Safety MVP Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task in the current chat. No subagents are requested. Steps use checkbox syntax for tracking. This is a proposed plan; no product implementation has started.

**Goal:** Deliver a local browser application for uploaded CCTV analysis, operator review and evidence export across fire, smoke, smoking behavior, no helmet and restricted-area intrusion.

**Architecture:** One FastAPI API serving a React SPA, one SQLite-backed local worker and private filesystem evidence. Reuse the existing detectors, timestamp logs and temporal utilities; add one pose/tracking pass and explicit person/zone/gesture rules.

**Tech Stack:** Python 3.12, FastAPI/Uvicorn, sqlite3, existing Ultralytics/OpenCV/MPS, explicit ByteTrack, React/TypeScript/Vite, native macOS avconvert, unittest, Vitest/Testing Library and Playwright browser checks. Pin compatible versions and commit lockfiles during implementation.

**Spec:** `/Users/tabbasi/Downloads/IndustrialAI/docs/superpowers/specs/2026-10-21-industrial-safety-mvp-design.md`

**Visual handoff:** `/Users/tabbasi/Downloads/IndustrialAI/docs/design/2026-10-21-mvp-mockups/index.md`. Use the refined option-2 screen set plus its design-system and interaction contracts. The user requested mockups first; no application code has been written in that design pass. Use shared components for capability variants, not a separate implementation per mockup image.

## Global constraints

- All five capabilities belong to the final MVP; upload/review precedes live cameras.
- One operator, one local inference worker, models sequential on MPS; CPU only when explicitly selected. No cloud accounts, footage uploads to third parties or public deployment.
- Upload limits: 250 MiB, five minutes, 1920×1080 maximum, nominal 60 FPS maximum. MVP storage quota 4 GiB; minimum free disk 3 GiB.
- Preserve existing CLI default models, options, raw class strings and historical artifacts. Full admitted uploads must not inherit the CLI's 300-frame truncation.
- Fire/smoke start at confidence 0.25, size 640, stride one, original container timestamps; record every selected model/configuration and all temporal settings.
- Separate model flags, temporal evidence, operator confirmation and unassessable intervals. Never infer no-helmet from a missing helmet detection or smoking from a cigarette box alone.
- Runtime data is ignored `var/mvp/`; uploaded data and review edits never enter the benchmark/training set automatically.
- Original source timestamps and browser-preview timestamps are distinct and explicitly mapped.
- Commit only this work at implementation checkpoints; preserve existing uncommitted evaluation/report work. No model promotion or fine-tuning is included.

## Review focus

1. Oversized/malformed uploads, deceptive filenames and depleted disk must fail without orphaned files or exposing paths — Tasks 1–2.
2. A worker crash/cancel/model failure must not become a completed zero-incident result or duplicate incidents on retry — Tasks 3–4.
3. Re-encoded/VFR footage and letterboxed display must not shift incidents, overlays or zone geometry — Tasks 2 and 5–6.
4. Crossing people, hidden wrists/heads and cigarette/gesture-only cases must produce uncertainty rather than a false behavioral assertion — Tasks 5–7.
5. Preview/thumbnail/range/export endpoints must remain private; review updates and missed-event annotations must survive restart — Tasks 1, 6 and 8.

## File ownership

Create `backend/app.py` (HTTP/session/static frontend), `backend/storage.py` (schema and transactions), `backend/media.py` (admission/preview/time map), `backend/worker.py` (single-worker job lifecycle), `backend/pipeline.py` (detector passes/results), `backend/tracking.py` (person/pose evidence), `backend/rules.py` (association/zone/smoking events), `backend/schemas.py` (API contracts), and `backend/models.json` (server-only pinned registry). Avoid service/repository/adapter layers around these files.

Create `frontend/` with Vite React TypeScript, `src/App.tsx`, generated API types and `src/api.ts`, `src/pages/Uploads.tsx`, `src/pages/Review.tsx`, `src/pages/Incidents.tsx`, `src/components/EvidencePlayer.tsx`, `src/components/ZoneEditor.tsx` and `src/styles.css`. Share components only when two screens actually use them.

Modify `evaluate.py` only for optional progress/cancel/no-annotation hooks with unchanged defaults, `.gitignore`, `README.md` and a separate `requirements-mvp.txt`. Keep `temporal.py`/existing event utilities as the source for existing rules. Add focused `tests/test_mvp_*.py` and frontend/browser checks alongside the owning task.

## Task 1: Authenticated application and durable job records

**Files:** `backend/{app,storage,schemas}.py`, package initializer, `requirements-mvp.txt`, `.gitignore`, `tests/test_mvp_api.py`, `tests/test_mvp_storage.py`.

**Interfaces:** `create_app(data_dir: Path) -> FastAPI`; `create_job(upload_id, config: dict) -> dict`; `get_job(job_id) -> dict`. Public IDs are generated UUIDs, not filesystem paths. Persist the five tables from the spec and job/capability/review enums in one schema source.

- [ ] Write failing tests: login/logout; anonymous upload/job access is 401; cross-origin/invalid-CSRF writes fail; persisted job survives DB reopen; double job claim has one winner; repeated client request UUID returns the original job. Media endpoint tests belong to Task 2.
- [ ] Run `.venv/bin/python -m unittest tests.test_mvp_api tests.test_mvp_storage -v`; observe the intended missing implementation failures.
- [ ] Add minimal FastAPI/Uvicorn/upload/session dependencies, pin resolved versions, implement one-operator login and SQLite v1 with WAL/foreign keys. Store no plaintext passwords or tokens in logs. Use transactional claims and append-only reviews.
- [ ] Run the focused tests; all pass. Validate generated OpenAPI contains the exact API routes/enums in the spec.
- [ ] Commit only the Task 1 files after inspecting the diff.

## Task 2: Bounded upload and browser-playable media

**Files:** `backend/media.py`, upload/artifact routes in `backend/app.py`, `backend/storage.py`, `tests/test_mvp_media.py`.

**Interfaces:** `admit_upload(stream, display_name: str) -> UploadRecord`; `prepare_preview(upload_id: str) -> PreviewRecord`; `source_to_preview(source_seconds: float, frame_map) -> float`. Raw file-body uploads are counted directly through `Request.stream()`; no multipart dependency is needed. Admission persists a `prepare_upload` queue item and returns 202 with its ID; full decode/preparation runs in the worker after Task 3. An asynchronous decode error is visible through that job, not a late HTTP rejection.

- [ ] Write failing tests: byte count rejects at limit+1 even without Content-Length; invalid bytes disguised as `.mp4` fail; traversal names cannot escape storage; declared and actually decoded duration/resolution/FPS caps enforced; 507 disk/quota rejection removes temporary files; unready/failed previews cannot start analysis.
- [ ] Add a short VFR/timestamp fixture: original source times remain unchanged; preview mapping is monotonic; frame count mismatch during conversion fails rather than silently misaligns. Authentication must apply to full and partial media responses.
- [ ] Implement streaming admission, decoder preflight and native H.264 preparation with frame mapping. Bind all artifact paths to DB IDs. No arbitrary URL/path ingestion or full-file reads into memory.
- [ ] Run `.venv/bin/python -m unittest tests.test_mvp_media -v`; verify real native conversion on a tiny generated fixture and byte-range 206/416 behavior.
- [ ] Commit only the media slice and its checks.

## Task 3: One resumable queue and fire/smoke processing

**Files:** `backend/{worker,pipeline}.py`, `backend/models.json`, minimal hooks in `evaluate.py`, `tests/test_mvp_worker.py`, existing `tests/test_evaluate.py`.

**Interfaces:** `run_job(job_id: str) -> None`; `run_detection_pass(upload, checkpoint, model_alias, on_progress, should_cancel) -> RunRecord`. Add optional `on_progress`, `should_cancel`, `write_annotated=True` keyword parameters to `evaluate()` with existing behavior as defaults. Use a distinct cancellation exception and explicit terminal metadata; do not label an interrupted run complete.

- [ ] Write failing tests: 301-frame input is fully analyzed; requests remain responsive during a fake slow model; second worker cannot acquire the lock; cancellation/restart gives cancelled/interrupted status; explicit retry creates a new job without duplicating old incidents.
- [ ] Implement transactional queue polling for `prepare_upload`, `analyze` and later `export` kinds, one worker lock, per-stage frame progress and model registry preflight. Worker handles preview conversion and inference outside the API. Explicitly request full source frame count and disable redundant per-model annotated videos for web jobs.
- [ ] Reuse `confirm_timed` and existing event merging for fire/smoke; retain raw flags and hash-pinned observations. Store inference coverage and capability failures independently. Check cancellation between frames and conversion polls.
- [ ] Run `.venv/bin/python -m unittest tests.test_mvp_worker tests.test_evaluate -v`, then the existing complete suite. Existing CLI defaults/log formats must remain compatible.
- [ ] Run one short real fire/smoke job locally, verify complete source coverage, record timing and commit this slice. Do not assert the model's known false alarms were fixed.

## Task 4: First usable frontend slice

**Files:** frontend package/lock/config, `src/{App,api}.tsx/ts`, `src/pages/{Uploads,Review}.tsx`, `src/components/EvidencePlayer.tsx`, `src/styles.css`, frontend tests.

**Interfaces:** Generated TypeScript types from OpenAPI; upload → `upload_id`, analysis → `job_id`; status polling every two seconds stops on terminal states and resumes after a page reload. `EvidencePlayer` consumes authenticated preview URLs, source/preview mapping and bounded observation pages.

- [ ] Add failing component tests for queued/running/failed/partial states, rejected upload, cancel action and no-candidate versus unassessable copy. Avoid mocking a successful model to imply real detection accuracy.
- [ ] Build login, video library, upload/configuration and review playback around the real API. Generate contract types instead of inventing frontend-only shapes. Define frontend `test`, `test:e2e`, `typecheck`, `build` and `generate:api` scripts. Include thumbnail strip and text evidence as a low-bandwidth fallback.
- [ ] Add a browser flow: login → upload tiny fixture → start job → observe progress → open result → seek event → reload result. Test narrow and desktop layouts and keyboard control.
- [ ] Run `npm --prefix frontend run test -- --run`, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build` and `npm --prefix frontend run test:e2e`. Verify browser seeking and overlays on real converted media; pass means no component/type/build/browser failures.
- [ ] Serve the built frontend from FastAPI and commit this working fire/smoke upload/review milestone. It is an intermediate slice, not the final five-capability MVP.

## Task 5: Person tracking, no-helmet association and zones

**Files:** `backend/tracking.py`, `backend/rules.py`, model registry, pipeline, `frontend/src/components/ZoneEditor.tsx`, setup view, `tests/test_mvp_tracking.py`, `tests/test_mvp_rules.py`.

**Interfaces:** `track_people(upload, on_progress, should_cancel) -> TrackingRecord`; records contain source frame/time, per-job track ID, person bbox and keypoints/confidences. `build_incidents(observations, tracks, zones, profile) -> list[IncidentDraft]` produces canonical event kinds and evidence references without reviewer decisions.

- [ ] Pin/download the official proposed pose artifact, inspect class/keypoint semantics and run a bounded MPS compatibility check. Install/pin ByteTrack's actual required dependency. A missing/failed model has a visible capability error; no silent substitute.
- [ ] Write failing tests: tracks reset between uploads; crowded head association abstains; missing helmet detection does not imply no helmet; explicit head box under 12 px stays raw/unassessable; valid same-track no-helmet evidence meets the spec's timed rule.
- [ ] Write geometry/rule tests: reject crossed/out-of-bounds/duplicate/zero-area polygons; exact display-to-source mapping under letterboxing; boundary inside; one-second dwell/three samples; two-second outside exit; initial-inside entry time unknown; lost/clipped track cannot assert entry/exit; overlapping incidents on different people/zones do not merge.
- [ ] Implement shared pose tracking and exactly the spec's association/zone rules, normalized editor coordinates and immutable per-job zone/profile snapshots. Intrusion-selected jobs without valid zones receive 422 before queueing.
- [ ] Run `.venv/bin/python -m unittest tests.test_mvp_tracking tests.test_mvp_rules -v` plus editor component tests. Validate a short reviewed person-crossing clip; report any missing real data separately from passing synthetic rule checks. Commit this milestone.

## Task 6: Persistent incident decisions and missed-event annotation

**Files:** review endpoints/storage, `frontend/src/pages/{Review,Incidents}.tsx`, player/timeline, `tests/test_mvp_reviews.py`, frontend/browser review checks.

**Interfaces:** `POST /api/incidents/{id}/reviews` accepts `decision`, `note`, expected review version; returns appended review/version. `POST /api/jobs/{id}/incidents` accepts canonical kind, original source start/end and `initial_review` (human decision confirmed/uncertain plus note); creates `origin=manual` and the initial review atomically without changing machine outputs. Notes allow 1,000 characters. Both writes use client request UUIDs. Concurrent stale review versions return 409.

- [ ] Write failing tests: confirm/false-alarm/uncertain persists after restart; repeated requests cannot duplicate an intended review; stale edits conflict; invalid/out-of-range manual intervals and notes over 1,000 characters fail; manual incident/initial-review creation rolls back together on failure; corrected reviews preserve earlier audit entries and raw prediction.
- [ ] Implement timeline seeking through the frame map, filters, evidence/track details, append-only reviews and manual missed incidents. Keep temporal and human confirmation labels separate.
- [ ] Use W04/W08 to reject a real known false flag and B01/B02 to record a missed plume or uncertainty. These are application acceptance examples, not new model-accuracy improvements or independent labels.
- [ ] Run `.venv/bin/python -m unittest tests.test_mvp_reviews -v`, component tests and a browser flow that edits, reloads and exports a reviewed source interval.
- [ ] Commit the review/history workflow.

## Task 7: Smoking behavior candidate pipeline

**Files:** cigarette pass in pipeline, `backend/rules.py`, smoking evidence UI, `tests/test_mvp_smoking.py`.

**Interfaces:** Consume the same `TrackingRecord` and canonical cigarette observations. Emit `kind=smoking`, `label=suspected smoking`, track/evidence interval and explicit rule version only when the spec's combined evidence is met. Cigarette-only evidence remains a raw object flag.

- [ ] Write failing fixture tests for the exact positive sequence: eligible person/pose, three associated cigarette observations spanning one second within two seconds, away → near → away within eight seconds. Verify emitted event points to that same track and its supporting frames.
- [ ] Add difficult negatives: phone/food gesture without cigarette, isolated cigarette without gesture, cigarette assigned to a neighboring person, low-confidence/missing wrists, person below 80 px, and gaps over one second. None may become confirmed behavior automatically; preserve uncertainty/raw evidence.
- [ ] Implement the explicit 0.5 keypoint-confidence and 0.15/0.25/0.20 person-height thresholds from the spec. Save all values in the job's immutable rule profile. Do not introduce an LLM service or pretend the gesture rule is a trained smoking classifier.
- [ ] Run `.venv/bin/python -m unittest tests.test_mvp_smoking -v`; inspect a real reviewed smoking-positive sequence and eating/drinking/phone negatives if available. Missing footage leaves model-quality validation open and visible, not a fabricated pass.
- [ ] Commit the fifth-capability path and its evidence review. All five must be represented in the application's capability/status matrix.

## Task 8: Exports, recovery, remote access and final acceptance

**Files:** worker export tasks, artifact/history UI, startup instructions/scripts as needed, `README.md`, `tests/test_mvp_exports.py`, `tests/test_mvp_acceptance.py`, browser acceptance flow, a new implementation report.

**Interfaces:** Export requests return a worker task ID; completed export is an authenticated artifact. CSV/JSON contain original source times, origin, model/rule hashes, coverage, reviewer decisions and notes. A selected evidence clip uses two seconds of context on each side when available, with source interval and playback mapping. Deletion is state-checked and filesystem cleanup retryable.

- [ ] Write failing tests: anonymous full/range/export access denied; no arbitrary artifact paths; disk exhaustion mid-conversion cleans temporary files and reports failure; cancelled/failed/partial jobs retain correct coverage; export agrees with persisted reviews; running-source deletion is rejected until cancellation; failed cleanup can be retried.
- [ ] Implement bounded exports and explicit deletion, sanitized CSV cells, thumbnail fallback, storage reporting and startup preflight for models/codec/worker. Show no candidate, disabled, failed and unassessable as distinct outcomes.
- [ ] Run `.venv/bin/python -m unittest discover -s tests -v` and the four frontend verification commands from Task 4; all must pass. Browser acceptance covers all five enabled, polygon saved, real job processed, source-aligned seek, confirm/reject/uncertain/manual event, reload/restart, export, cancel and interrupted-job retry. Include Chromium/WebKit checks and 390/1440 px layouts; verify actual Safari playback if available and record any browser coverage gap. Measure Mac processing duration and API response while busy; report observations rather than a live-FPS guarantee.
- [ ] Document one-command development start and separate repeatable local start, operator credential setup and SSH/VPN browser-access instructions. Bind loopback by default; do not publish a service or create external accounts. Reconfirm no private media/credentials/weights entered Git.
- [ ] Save an implementation report distinguishing software acceptance from each capability's real-data validation. Record smoking/intrusion data gaps explicitly, preserve the existing model benchmark/defaults and commit only this work after verification.

## Definition of done

- [ ] A reviewer can complete upload/configure/analyze/review/export in a browser without opening Mac filesystem videos.
- [ ] All five capability paths exist with person/gesture/zone rules and separate evidence/visibility states; none is silently replaced by an object count.
- [ ] Real private video playback/seeking and frame fallback work; original timestamps and zone placement align correctly.
- [ ] Progress, failure, cancellation, restart, manual corrections and exports survive normal use and preserve provenance.
- [ ] Existing CLI behavior/tests remain compatible; new focused checks and complete browser flow pass.
- [ ] Measured limitations and remaining model-validation footage are recorded. No unsupported safety/accuracy claim, cloud deployment or model promotion is made.

## Proposed execution

Implement inline in this chat, task by task, with a working reviewable slice at Task 4, tracked PPE/zone events at Task 5, all five at Task 7 and final acceptance at Task 8. This turn delivers the design and implementation plan. The build phase starts when the user requests implementation.
