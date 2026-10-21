# Industrial AI — screen and interaction contracts

This handoff accompanies the refined option-2 mockups. It describes intended behavior; no frontend/backend code was implemented during this mockup pass. Read alongside the existing MVP design and implementation plan.

## Screen map

| Screen | Primary job | Primary action | Context preserved |
|---|---|---|---|
| 01 Sign in | Enter the local operator workspace | Sign in | Return destination after a session expires |
| 02 Video library | Find or upload recorded footage | Upload video | Search, filters, scroll and selected upload |
| 03 Upload sheet | Transfer a selected file | Cancel while transferring; Configure after validation | File identity, actual received bytes, preparation job |
| 04 Analysis setup | Choose the five capabilities and draw zones | Start analysis | Upload/source time, draft capability choices and normalized zone vertices |
| 05 Analysis progress | Understand asynchronous work | Cancel analysis; navigate away without cancellation | Persisted job ID, stage and successful/expected frames |
| 06 Incident review | Inspect a model flag and record a decision | Save review | Source interval, playback/frame position, unsaved review draft |
| 07 Incident history | Find saved decisions and evidence | Export history | Current filters determine export scope |
| 08 Incident details/export | Inspect source/review history and prepare evidence | Prepare export, then Download when ready | Saved source interval, origin, decision, notes and audit trail |
| 09 Narrow-screen review | Review evidence over a limited connection | Save review | The same source/decision state as desktop; Frames is an available low-bandwidth mode |
| 10 Fire review | Resolve an ambiguous fire flag | Save review | Same shared review components, actual source aspect ratio |
| 11 Smoking review | Explain insufficient or combined behavioral evidence | Save review | Person association, cigarette evidence and gesture assessment kept distinct |
| 12 Headwear review | Inspect explicit no-helmet evidence and visibility | Save review | Track association and head-detail limitations |
| 13 Zone review | Inspect restricted-area presence/entry evidence | Save review | Immutable saved zone; initial-inside versus observed crossing |
| 14 Add missed incident | Record an observation the model missed | Add incident | Canonical detection kind, original source interval, human judgment and notes |

These are pages, sheets and important review states within one product, not 14 unrelated routes or a requirement for separate per-capability implementations.

## Main flow

Sign in → Video library → native file choice → Upload sheet → preview preparation → Analysis setup → Analysis progress → Incident review → Incident history → Incident details/export.

Upload and analysis are separate operations. Before transfer completes the sheet can warn that leaving will cancel transfer. Once the server has the file and a persisted preparation/analysis job exists, navigating away does not cancel processing. The library always exposes the preparation/analysis state and an appropriate next action.

## Action decisions

| Control | Required behavior |
|---|---|
| Sign in | Empty password disables submission; wrong credentials produce a generic inline error and retain focus on Password; pending state prevents duplicates |
| Password eye | Toggle visibility without submitting; return to masked on leaving this view |
| Upload video | Open native single-file chooser; never imply that a URL/cloud camera was connected |
| Cancel upload / close sheet | While transfer is active, confirm cancellation and remove temporary data; cancel confirmation returns to the unchanged transfer |
| Configure | Open setup only once preview/timestamp validation succeeds |
| Detection switches | All five are available. If intrusion is selected with no valid zone, show the missing-zone requirement and disable Start analysis |
| Zone editing | Separate drawing/edit state from saved/read-only state. Undo removes the last vertex; deleting an existing named zone requires an explicit confirmation |
| Start analysis | Validate selection, zone and resource readiness; persist a configuration snapshot; return one job despite double-click/network retry |
| Cancel analysis | Explain that processing stops and partial evidence is retained; use a destructive Stop analysis action only in the confirmation |
| Back to library | Navigate without cancelling a server-side job; draft setup/review has an unsaved-change guard |
| Video / Frames | Keep the same original source time; change controls appropriately: Play/Pause belongs to video, Previous/Next frame to still mode |
| Play/Pause | Toggle only when media is ready. No volume button because analysis previews do not carry audio |
| Timeline/incident click | Seek using explicit source ↔ preview mapping; a paused source clock and slider position must agree |
| Review choices | No selection by default. Choosing a judgment does not save it; show Unsaved decision until Save succeeds |
| Save review | Require a choice; send expected version and request ID; append decision; show saved result only after persistence succeeds |
| Add missed incident | Open a clean manual form for the current upload, never inherit a previous incident's decision/notes |
| View zone | Read-only saved geometry. To change a zone, explicitly open a new analysis setup with a new snapshot |
| History filters | Preserve query state when opening/closing a detail sheet; debounce text search without moving focus |
| Edit review | Create a new review revision, preserve the previous note/decision in the audit trail |
| Prepare export | Queue export using visible format/scope. Evidence MP4 has a source-time/review manifest; CSV/JSON retain decisions and origin |
| Download | Enabled only for a completed artifact; preparation failure has an inline reason and retry path |
| Operator menu | Shows session identity and named Sign out; protect dirty drafts before leaving |

## Manual observation form

- Canonical kind: fire, smoke, smoking, no_helmet or restricted_entry, displayed in human-readable terms.
- Fields Start and End accept original source time, including milliseconds; require `0 <= start < end <= source duration`. A source-preview conversion is never silently applied to typed original times.
- Your assessment choices: Confirmed or Uncertain; no automatic initial choice. Confirmation means a human observation, not a verified model classification.
- Notes are optional, maximum 1,000 characters. Keep a draft on validation/server error; do not display an inaccurate counter.
- Add incident persists the manual incident and its initial review atomically with an idempotent request ID, so a half-created observation cannot appear as a reviewed model flag.
- A review conflict returns the latest saved revision and preserves the draft for deliberate reapplication, rather than silently replacing another result.

## Status language

Processing states: queued, preparing preview, analyzing, complete, partial, failed, cancelled, interrupted. These describe work, not safety.

Machine evidence: candidate flag, temporal evidence met, limited visibility, not assessable, not analyzed. Review decisions: unreviewed, confirmed, false alarm, uncertain. Do not collapse these into a single green/red status.

Use neutral Ready to configure/Complete treatment; amber belongs to Needs review, uncertainty or attention to unsaved decisions. A successful empty analysis says No candidates detected in analyzed footage, with coverage visible. It never says Safe or Compliant. Unassessable head/gesture evidence remains visible even if no event was emitted.

## Empty, loading, error and recovery states

| Condition | Screen response and recovery |
|---|---|
| Empty library | Concise explanation and Upload video action; no fake sample records in the running product |
| No filter matches | No matching videos/incidents plus Clear filters, not an empty-library prompt |
| File exceeds 250 MiB | Reject during receipt; explain the limit and retain a Choose another file action |
| Invalid/unsupported media | Show the format/decode reason; remove failed temporary data; do not enqueue analysis |
| Preview not ready | Preparing preview state, no enabled Configure/Analyze action |
| Missing/invalid zone | Inline guidance beside zone controls; focus zone editor, no misleading enabled Start button |
| Insufficient local storage | Explain required cleanup; existing evidence remains accessible; do not auto-delete user files |
| Failed capability | Mark analysis Partial, name failed capability, retain successful outputs and coverage |
| Lost connection | Cannot refresh status; last update time and Retry; do not change persisted job to completed or failed based only on browser disconnection |
| Worker interruption | Interrupted, partial coverage and explicit Start new analysis retry; never a zero-incident success |
| Save failure | Draft remains visible with Retry; navigating away asks whether to discard |
| Stale review version | Explain newer saved decision; preserve unsaved draft, offer reload/latest review |
| No incident selected | Whole-source playback/frame review remains available, with Add missed incident |
| Unsaved review/setup | Leave/discard confirmation uses Continue editing as the non-destructive choice; no silent loss |
| Export in progress/failure | Progress label or error/retry inside the export section; no dead Download button |
| Delete source while running | Require cancelling the job first; a later delete explicitly describes affected video/evidence, with irreversible action styled destructive |

These states share existing views/dialog components and have specified copy/behavior; not every combination needs a separate full-screen raster.

## Keyboard and touch contracts

- Tab order follows visible reading order; Enter activates buttons/forms where expected; Space activates a focused toggle/radio control.
- Space toggles the video only when focus is outside editable fields; source seeking and frame step controls have keyboard-accessible alternatives.
- Dialogs/sheets announce title and purpose; Escape invokes their safe close behavior, then restores invoking focus.
- Zone editor supports keyboard point selection, arrow movement, Undo and a named Finish drawing action; dragging is not its only input path.
- Touch targets are at least 44 px, even on icon controls; there is no hover-only essential action.
- Mobile review stacks evidence, assessment and notes. The Save area respects viewport/keyboard changes and never obscures the focused field. Wide history tables become readable list rows with the same essential information.
- Screen-reader labels use actual action meaning: Previous frame, Next frame, Close upload dialog, Show password, etc.; a color/symbol alone is insufficient.

## Visual review and remaining build checks

The mockup pass corrected active-nav color, a paused-player glyph, redundant note editing, B01 evidence aspect ratio, saved-zone edit controls leaking into review, and a manual dialog inheriting another source's background decision.

Generated raster details are not authoritative implementation values. During the build, normalize minor leftovers using the shared system: neutral Ready to configure marker, static x-circle for False alarm in every history view, no standalone inaccurate notes counter, and source-clock/slider positions derived from one value rather than independently copied graphics. Do not hard-code sample progress percentages or dates.

Interactive QA, actual color/zoom checks, media alignment and backend validation remain part of implementation. Passing a static visual review is not a statement that the MVP is built or its five detectors have passed a new accuracy test.
