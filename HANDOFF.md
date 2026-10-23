# Agent handoff — Industrial Safety AI

Updated 23 October 2026. This is the technical context and decision history from the project chat, with links to the evidence. It is a continuation brief, not a verbatim transcript. Start here before interpreting older plans or selecting another model.

## Current position

The **Mac upload-and-review MVP is implemented and demo-tested**. Model accuracy, especially smoke, is the unresolved priority. The latest work is offline dataset screening and controlled perception experiments; it did not change application defaults, thresholds, saved reviews or the local database.

The user's latest decision is explicit: **there is no footage from the intended deployment site; continue with public footage**. Do not stall waiting for private-site footage or an Alipan account. The user has already authorized finding public clips, inspecting/annotating them, investigating root causes and running development experiments. The user cannot reliably view video over their remote connection and explicitly delegated visual inspection to the assistant. Record assistant labels as such, rather than calling them independently human-confirmed truth.

Repository: `https://github.com/TouqeerShahid951/IndustrialAI`.
Continue on **`codex/industrial-mvp`**, not an assumed up-to-date default branch. Research checkpoint commits: `373ec89` (rejected FASDD pilot), `76ef623` (additional-data audit), `27dd724` (public CCTV acquisition), `e52fdd5` (annotations), `54ea5d2` (baseline), `7ee61cc` (root causes), `9b6372b` (latest public-data training comparison).

## Product scope and durable decisions

- First workflow: **upload recorded CCTV and review incidents**. Include all five capabilities: fire, smoke, suspected smoking behavior, explicit no-helmet evidence and restricted-area intrusion.
- Design: selected Evidence Focus layout, theme 3 **Soft Graphite and Sage**, with meticulous restrained UI, clear hierarchy and system typography. The user invoked Product Design and selected mockups before implementation. Read [frontend instructions](frontend/AGENTS.md), [design system](docs/design/2026-10-21-mvp-mockups/design-system.md) and the [14 selected screens](docs/design/2026-10-21-mvp-mockups/screens-graphite-sage/).
- User specifically questioned warm-colored bounding boxes over flames and two mismatching timelines. These were addressed with cyan candidate boxes, dark contrast outlines/readable labels, aligned source-time tracks and a shared playhead. Preserve that behavior. See [player UX verification](reports/player-ux-2026-10-22/report.md), commit `b023061`.
- Saved human/assistant decisions, raw model candidates, temporal confirmation and uncertainty are separate evidence. Do not rewrite prior reviews to hide model errors or assume every unreviewed interval is negative.
- Local demo first; live RTSP streams, cloud inference/deployment, external alerts, team accounts and production acceptance are not implemented milestones. Do not expand into them while smoke perception is unresolved.
- Prefer a small, tested change, reuse existing helpers and keep experimental dependencies isolated. Make progress without repeated confirmation when the work is already authorized. Another agent was requested to continue via this handoff; no new chat or agent has been dispatched automatically.

## Implemented architecture and operation

| Area | Entry points / behavior |
|---|---|
| API and persistence | `backend/app.py`, `auth.py`, `storage.py`, `schemas.py`; FastAPI, SQLite durable jobs/reviews, one local operator |
| Analysis | `backend/worker.py`, `pipeline.py`, `rules.py`; one separate worker, sequential full-source-frame processing, tracking/temporal evidence |
| Model registry | `backend/models.json`; four pinned/hash-verified models support the five capabilities: fire/smoke, helmet, cigarette and person pose |
| Media/evidence | `backend/media.py`, `exports.py`; source-aligned previews, authenticated artifacts, JSON/CSV and selected MP4 plus frame manifest |
| UI | React/TypeScript in `frontend/src/`; review in `pages/Review.tsx`, playback/overlay/timeline in `components/EvidencePlayer.tsx` |
| Evaluation | `evaluate.py`, `temporal.py`, `scripts/benchmark_data.py`, `benchmark_events.py`, `run_benchmark.py`; retain provenance, timestamps and uncertainty |

On the existing Mac, working directory is `/Users/tabbasi/Downloads/IndustrialAI`, Python is `.venv/bin/python`, and hardware is an Apple M4 with 16 GB RAM. Run `./scripts/start_mvp.sh`; it rebuilds the frontend and starts the API/worker at `http://127.0.0.1:8008`. MPS is explicit; do not silently substitute a device or checkpoint.

Login uses the generated operator password in ignored `var/mvp/operator-password.txt`, with no username. Change it using `.venv/bin/python -m backend.manage password` while stopped. Never commit that file, session tokens, environment secrets or the local database. Remote access uses the SSH tunnel in [README](README.md); do not expose the service publicly as part of continuing this research.

Upload limits: 250 MiB, five minutes, 1920×1080, nominal 60 FPS; workspace quota 4 GiB, free-disk guard 3 GiB. Frames fallback is approximately one still per second. Evidence MP4 omits audio. Smoking requires same-person cigarette/hand-to-face evidence; no-helmet requires explicit associated evidence; intrusion requires a configured zone. Completed processing does not mean a hazard was confirmed or a scene was safe.

The [demo audit](reports/demo-readiness-2026-10-22/report.md) and [five-minute runbook](reports/demo-readiness-2026-10-22/demo-runbook.md) document verified workflows and known limitations. Saved demo job IDs exist only in this Mac's database, not automatically in a clone. Actual remote-client/Safari/WebKit testing remains open. Older README sections describing a future MVP refer to the original CLI milestone; the implemented workflow at the top is current.

## Why smoke work is still open

The default fire/smoke checkpoint remains `rabahdev/fire-smoke-yolov8n`, revision `13017fe8af477c25f5298d168e2dfede4b000753`, SHA-256 `b91633799ceb052c814b4f8b77a37efc9a40f002d528df97d74463585fa4f28f`, classes **0 smoke / 1 fire**. Exact app pins for every capability are in `backend/models.json`.

The user noticed smoke alerts without visible smoke and asked to solve the root cause. [Threshold audit](reports/smoke-sensitivity-2026-10-22/report.md) and [root-cause experiments](reports/detector-root-cause-2026-10-22/report.md) establish:

- Clear factory floors receive strong smoke scores, while diffuse backlit room haze is often missed. Raising the smoke threshold suppresses positives without eliminating all floor errors; persistent false evidence can also survive temporal voting.
- Embedded class mapping is correct. On 69 controlled native PNGs, image/video inference and CPU/MPS agree to numerical tolerance. This supports a perception/representation problem on the checked cases, rather than those proposed software explanations.
- Higher input resolution helps small flames but adds false detections. Alternative publisher models regress older fire/smoke events. No universal replacement passed.
- The original small YOLO fine-tune and later bounded FASDD pilot were rejected. High internal image validation did not transfer to CCTV. Do not repeat the same weak-data experiment or describe it as successful retraining.
- Whole-scene/clip smoke modeling is worth continuing because diffuse haze is poorly represented by tight boxes. Scene classification has **no localization box** and its raw decision score is **not a probability**.

## Latest measured experiment — read this before quoting an improvement

Authoritative [23 October report](reports/public-training-footage-2026-10-23/report.md), [fixed main specification](reports/public-training-footage-2026-10-23/paired-camera-spec.json), [results](reports/public-training-footage-2026-10-23/paired-camera-results.json) and [verification](reports/public-training-footage-2026-10-23/verification.json).

Frozen Google SigLIP2 base patch16/224 image encoder, normalized embeddings, linear ridge smoke head (coefficient 0.1, threshold zero). **Only the head was fitted; neither YOLO nor the encoder was fine-tuned.** Encoder pin and hashes: [scene-model.json](reports/detector-root-cause-2026-10-22/scene-model.json). Experimental transformer dependencies live in an isolated local directory, not the app requirements.

1. Previous FASDD pool: 176 fitting images / 48 validation images. Adding 18 reviewed public positive images and eight clear MEVA frames produced 202 fitting images, but recovered just **1/19** positives in the old sparse CCTV check, versus 0/19 previously, both with 0/36 known-negative flags. Internal validation remained 44/48.
2. **Explicit split change:** for a new experiment, retired the entire MmodalFire `mmodalfire-xian-ch01` camera, clips **C01–C15**, from validation to fitting/exclusion. Sampled 56 smoke-positive and 56 clear/documented-mist frames. Together with the 202-image pool: **314 fitting images, 156 positive / 158 negative**. The old MmodalFire scores are no longer validation for this head. Original manifests/reports were preserved.
3. Evaluated on **20 other development clips**, fully decoding 9,401 native frames and classifying 949 samples at 2 Hz: **281 reviewed positive, 466 reviewed negative, 202 unknown/excluded**. No Cxx/MmodalFire clip enters this comparison. These are already-exposed development scenes, not a fresh blind test.

| Head | Positive hits / 281 | Known-negative flags / 466 | Temporal incidents found / four |
|---|---:|---:|---:|
| 202-image unpaired control | 52 (18.5%) | 0 | 3 |
| 314-image paired-camera head | 206 (73.3%) | 0 | 3 |
| Post-hoc explanatory control, replacing matched negatives with repeated generic negatives | 248 (88.3%) | 1 | 3 |

**Do not promote based on this table.** Workshop-smoke supplies 219/281 positive samples; excluding it, paired coverage is 30/62 (48.4%) versus 22/62 (35.5%) for the unpaired control. B02 has only one brief paired hit and still fails temporal confirmation. All heads miss that temporal event. Matched negatives trade sensitivity against one clear-scene flag; the post-hoc control does not establish they are categorically best.

Model-selected review outside the original labels also found a **false positive on a title card at clip-007 3.0 s and a clear street still at 9.0 s**. Thus 0/466 does not mean no false positives overall. Visible plume at 27.5/32.0 s predates the original confirmed core; separate still annotations record that without extending unreviewed neighboring intervals. See [failure evidence](reports/public-training-footage-2026-10-23/prediction-review.jpg) and [supplemental annotations](reports/public-training-footage-2026-10-23/supplemental-frame-review.json).

Only 230.15 seconds have known-negative interval labels in this comparison. Do not infer deployment nuisance alarms per hour from it. Paired temporal events fragment the workshop incident into eight events (one match, seven duplicate-fragment false positives), despite zero overlap with known-negative time. Raw event recall from a brief hit does not establish reliable incident detection. Scene temporal voting at 2 Hz differs from the app's native spatial voting.

**Current decision: retain the original application detector; the experimental head is unqualified for default integration.**

## Footage, labels and leakage boundaries

| Collection | Role and caveats |
|---|---|
| Seven original user-reviewed clips | `benchmark/chat-review-manifest.jsonl`; preserve reviewed intervals and uncertainty. clip-007 has user-confirmed smoke core 34–40 s. Other times were not automatically labeled clear. |
| W04/W08 and B01/B02 | [assistant manifest](reports/smoke-improvement-2026-10-21/assistant-review-manifest.jsonl): factory negatives; backlit plume positives with uncertain onset/tail. Assistant review, not independent truth. B01/B02 fire visibility is uncertain, not established negative. |
| 23 later CCTV clips | [manifest](reports/cctv-annotations-2026-10-22/manifest.jsonl): F01–F08 one factory family; C01–C15 one MmodalFire lab camera. [Baseline](reports/cctv-baseline-2026-10-22/report.md) processed all 20,400 frames, 815.71 s. C11 is documented water mist, now part of fitting for the latest head. **It cannot test that head's mist rejection.** |
| FASDD curated pool | [224-image manifest](reports/fasdd-pilot-2026-10-22/curated-manifest.json): approximate visual source groups, 176 train/48 val. Public source/pretraining overlap remains unknown. Small detector fine-tune rejected. |
| MEVA | Six public CCTV files; two longer interior videos total about 9.5 minutes. 286 sampled stills annotated, eight selected for fitting. All grouped as `meva-kf1-all`, not separate train/test cameras. Building interiors, not verified industrial process negatives. |
| FIRESENSE | Downloaded 22 smoke-archive videos, including existing-source repeats. No new fitting data. Reserved workshop source has drawn contours. Five videos have incomplete OpenCV decoding; exclude/flag defects. |
| Indoor Fire Smoke 5,000-image archive | All images publisher-positive; 89 have explicit AI-related filenames; unknown device aerosols excluded. Only 18 manually reviewed positives from nine approximate source families fitted. Do not call it 5,000 real CCTV images or adopt its random folder split. |
| Other candidate datasets | [ISFire-4 audit](reports/smoke-data-expansion-2026-10-22/report.md) found overlap/provenance problems; excluded. Earlier Alipan/CMOT access needed an account the user lacks. Do not count inaccessible sources as acquired footage. |

Keep adjacent frames, camera/site/incident families and all their reused public versions together. A perceptual hash screen reduces obvious contamination but cannot prove source independence. Unknown aerosol composition stays uncertain; a visible white plume alone does not prove steam, dust or combustion. Frame/sample counts are not independent event counts.

Primary public sources and acquisition metadata are linked in the latest report: [MEVA](https://mevadata.org/), [FIRESENSE](https://zenodo.org/records/836749), [Indoor Fire Smoke](https://zenodo.org/records/15826133), [MmodalFire](https://springernature.figshare.com/articles/dataset/MmodalFire_A_Multimodal_Dataset_Comprising_Video_and_Physical_Sensing_Data_for_Detecting_Indoor_Fires/28804448). Publisher CC BY 4.0 metadata is recorded; mixed-source images still have unverified underlying provenance. Model licensing, including AGPL considerations, is documented in README; no commercial deployment clearance is implied.

## What to do next

1. **Acquire additional public camera families** with identifiable normal operation, faint/backlit smoke and known steam/mist/dust sources. Seek paired clear/aerosol views and longer normal-operation recordings. Save source URLs, terms, camera/site/incident groups, hashes, original FPS/PTS and decode defects before counting footage as usable. Do not substitute a random image collection for industrial CCTV or assume every public plume is fire smoke.
2. **Freeze a new source-group split before frame sampling.** Existing Cxx and all MEVA views are fitting data for the latest candidate; the existing 20 evaluation clips are development/regression data. Reserve genuinely new families for a blind test, especially a separate documented mist/steam family. Preserve historical artifacts; record allocation changes explicitly.
3. **Annotate the relevant evidence.** Presence/absence/uncertain, rough onset/offset, source context and visibility. Use scene labels for diffuse haze; annotate boxes only where meaningful. Record reviewer identity and sampled-still versus interval scope. Add hard negatives such as clear backlit rooms, reflections, normal process aerosol and non-scene frames to development data without fitting the reserved test scenes.
4. **Run one controlled data/representation comparison.** Reuse the frozen-head code and fixed controls before choosing a larger fine-tune. Hold the recipe fixed when testing data additions. Tune thresholds and temporal continuity only on validation; compare faint smoke, clear/mist rejection and per-source performance, rather than selecting on an aggregate dominated by workshop-smoke.
5. **Run regression and a separate blind evaluation.** Preserve the older fire detections, clip-007 smoke and B01/B02; assess delays, misses, fragments and actual negative-time alarms separately. Evaluate enough independent events and negative exposure to support any proposed operating targets. No production sensitivity or nuisance-rate target has been accepted yet.
6. **Integrate only a qualified candidate.** Keep source timestamps, evidence exports and raw candidates intact. If a scene classifier is added, show scene evidence without invented boxes or probability wording. Re-run backend/UI/type/build/E2E checks and verify the actual player on bright flame footage and remote/browser layouts. Product expansion comes after this perception milestone.

The first actionable task for the next agent is **additional public-source acquisition and a camera-disjoint dataset manifest**, not another threshold sweep, UI redesign or live-camera feature. Continue independently with public sources; ask only for information genuinely needed to proceed.

## Local artifacts versus a fresh GitHub checkout

Git contains the application, mockups, reports/contact sheets, annotations, specifications, score records, hashes and research scripts. It deliberately does **not** contain raw footage, `.pt` checkpoints, experimental encoder/head binaries, cached embeddings, uploads, SQLite state, passwords or installed dependencies.

On the original Mac, relevant ignored paths are:

```text
data/public-training-footage-2026-10-23/
outputs/public-training-footage-2026-10-23/paired-scene-head.npz
outputs/public-training-footage-2026-10-23/scene-head.npz
outputs/public-training-footage-2026-10-23/paired-features.npz
outputs/detector-root-cause-2026-10-22/scene-download/
outputs/detector-root-cause-2026-10-22/scene-runtime/
var/mvp/
```

Research manifests retain original absolute Mac paths as provenance. A fresh agent on another machine must reacquire permitted files using recorded URLs/revisions, verify hashes and regenerate or create rebased working manifests before rerunning file-dependent experiments. Do not rewrite historical hashed manifests in place or assume `verify.py` can pass from Git alone. Old baseline run outputs and native extracted frames are also local dependencies. The reports allow result inspection without those downloads.

For a fresh app installation follow [README setup](README.md), including `.venv/bin/python -m backend.manage models` for the pinned application models. For the experimental encoder use the exact revision/files in `scene-model.json`; isolated runtime pins are in `reports/detector-root-cause-2026-10-22/scene-runtime-pins.json`. Do not upgrade/downgrade the shared environment blindly.

Untracked `codex-offline-export.zip` and `codex-offline-export/` exist on the original Mac. They are user artifacts, not part of this push; leave them untouched and do not publish an unreviewed archive as chat context.

## Verification commands and reading order

The latest research verification reproduced all three heads' 949 cached scores, checked original main/control results, source hashes, archive MD5/CRC/ETags, camera allocation and 314 fitting-image hashes; three script self-checks and 14 benchmark/evaluator unit tests passed. Details are in the dated `verification.json`. The demo audit records historical browser and full application checks; those are not a fresh production sign-off.

During preparation of this handoff, `.venv/bin/python -m unittest discover -s tests` passed **all 65 backend/evaluation tests**. Local links in this handoff and README were checked, and Git whitespace checks passed. No frontend behavior changed in this handoff.

```sh
# Existing Mac, with the ignored research dependencies retained:
.venv/bin/python reports/public-training-footage-2026-10-23/verify.py
# Application checks appropriate after code changes:
.venv/bin/python -m unittest discover -s tests -v
npm --prefix frontend test -- --run
npm --prefix frontend run typecheck
npm --prefix frontend run build
# Running local app, disposable E2E data; use the private configured password:
npm --prefix frontend run test:e2e
```

Read in order: this handoff → [latest experiment](reports/public-training-footage-2026-10-23/report.md) → [root causes](reports/detector-root-cause-2026-10-22/report.md) → [baseline](reports/cctv-baseline-2026-10-22/report.md) → [annotations](reports/cctv-annotations-2026-10-22/report.md). For product work, then read the demo audit/runbook, player UX report, selected design and applicable `frontend/AGENTS.md`.

Earlier history is preserved in [initial improvement plan](docs/superpowers/plans/2026-10-20-industrial-safety-improvement-plan.md), [MVP plan](docs/superpowers/plans/2026-10-21-industrial-safety-mvp.md), [21 October smoke review](reports/smoke-improvement-2026-10-21/outcome.md) and [FASDD pilot](reports/fasdd-pilot-2026-10-22/report.md). Their older statements about not-yet-started training or camera reservation are superseded only by the explicitly dated experiments above. The original shared project conversation is linked in README; this checked-in handoff and reports are the working continuation context.
