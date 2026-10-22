# Local MVP implementation results

Completed on this Mac, 22 October 2026, on branch `codex/industrial-mvp`. Local application: http://127.0.0.1:8008. React/TypeScript frontend, FastAPI, SQLite and one independent inference worker. The selected Soft Graphite and Sage design is implemented across login, library, upload, detection setup, zone editor, progress, incident review, manual annotation, history and exports. Capability variants reuse these screens.

## Verification results

- Backend and existing CLI suite: **61 tests passed** (`python -m unittest discover -s tests -v`).
- Frontend: **8 tests passed**, TypeScript checking and production build passed.
- Live API/worker journey: **passed** in 14.8 seconds after restart, with actual pinned models on MPS. Exercises authenticated upload, preparation, all-five job, request idempotency, append-only review corrections, JSON/CSV/MP4+manifest, private range requests, cancel, retry and cleanup of its disposable fixture.
- Browser: login/upload/configure/analyze/review/reload, keyboard polygon, actual playback and source seek, fallback stills, manual uncertain observation, history/audit, download and mobile sign-out. Desktop 1440×1024 and narrow 389×843; no horizontal overflow or console errors. Browser checks used the in-app browser; `test:e2e` is the complementary native API/worker test, not a second browser engine.
- Startup script preflight and actual restart verified. Logout cookie revocation survives restart. Application remains bound to loopback port 8008; an unrelated service on port 8000 was left alone.
- [Visual verification](../../design-qa.md): passed, with source, screenshot, density normalization and comparison history.

## Actual model execution, without accuracy claims

A 75-frame W04 sample completed all passes: pose 2.474s, fire/smoke 1.312s, helmet 1.263s and cigarette 4.865s. During inference, 93 API probes had a maximum observed response of 0.011s. These are small local measurements, not throughput guarantees.

W04 factory-floor footage produced a smoke false alarm and an initial-inside restricted-area presence candidate. The smoke candidate was saved as false alarm and persisted after reload. B01 backlit-room footage was processed separately; a manual smoke/plume observation covering 5–22s was saved as **uncertain**, with a note that the substance/source was unclear. Its MP4 evidence export and separate manifest completed. These are developer application acceptance examples, not independent human ground-truth annotations.

| Capability | Software evidence | Remaining real-data validation |
|---|---|---|
| Fire / smoke | Pinned model, complete source coverage, temporal vs raw flags, real W04/B01 review | Known false alarms and missed plumes remain; labeled industrial holdout required |
| No helmet | Explicit associated class, minimum head size, same-track timing and ambiguity tests | Distant/occluded heads and crowded PPE footage |
| Smoking | Same-person and relevant-hand cigarette evidence plus away→near→away cycle; ambiguity resets and uncertainty | Reviewed smoking positives plus eating/drinking/phone negatives; no accuracy claim |
| Intrusion | Normalized zone, keyboard editing, dwell, track gaps and initial-inside semantics; real W04 presence | Independently labeled boundary-crossing/occlusion footage; entry accuracy not established |

No new fine-tuning, model promotion, live camera ingestion or public deployment occurred. Safari/WebKit and a remote-client browser session remain untested. Existing CLI defaults and historical evaluation artifacts were preserved.

## Final independent review and fixes

A fresh reviewer identified five P2 issues. All were reproduced with failing regression tests and fixed in one pass:

1. Cigarette evidence now supports the relevant wrist/nose cycle, not any hand on the track.
2. Ambiguous cigarette/person associations reset affected gesture cycles and produce uncertainty intervals.
3. Shared frontend mutation handling retains intent IDs and payloads across lost responses/reloads, for manual incidents, reviews, exports, analysis and job retry.
4. Delete removes unregistered preview files left by an interrupted worker, scoped to that upload.
5. Keyboard zone selection stays valid after Undo and at the 32-point limit.

Additional checked corrections: subsecond intervals retain precision; logout is available on mobile; mobile review actions stay visible. Source footage and runtime credentials/weights are ignored, not committed.

## Rulings made

1. Use the requested checkout on a new local feature branch instead of another checkout. Reason: implement here and preserve existing design edits. Cost if wrong: less checkout isolation.
2. Keep `evaluate.py` unchanged; a web full-frame iterator reuses temporal/event utilities. Cost if wrong: two decoding callers to maintain.
3. Wire geometry and all-five contracts before the first UI slice. Cost if wrong: a later first visible slice; avoids replacing mock API contracts.
4. Consolidate Tasks 4–8 into the shared frontend/pipeline milestone and final fixes; pose tracking stays inside the shared pipeline rather than a separate single-purpose module. Native API/worker automation plus actual browser checks covers the journey. Cost if wrong: coarser commit/task boundaries and no unattended browser regression runner.
5. The reviewer declined independent judgments on accuracy and unperformed devices. Keep these as explicit validation gaps rather than infer quality from synthetic checks. Cost if wrong: deployment readiness remains unknown until real holdout/device evaluation.
6. Preserve the completed local feature branch and running workspace; do not push, merge or publish without a request. Cost if wrong: integration is still a separate step.

## Deferred minor

Completed MP4 export progress can retain its last periodic frame count (for example 330/350), while the explicit status and downloadable export are completed and verified. Refreshing that cosmetic final counter remains follow-up polish; it does not change output frame coverage.
