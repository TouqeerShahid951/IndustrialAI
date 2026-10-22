# Industrial AI — five-minute local demo

This demonstrates the upload-and-review workflow. It is not a detector-accuracy benchmark or an autonomous safety system.

## Before presenting

1. From the project root run `./scripts/start_mvp.sh`. This checks the pinned models, builds the current UI, and starts the API and one worker on port 8008.
2. Open http://127.0.0.1:8008. Use the operator password in `var/mvp/operator-password.txt`; no username is required. Keep this file and password out of shared screenshots.
3. Keep the Mac awake. If presenting remotely, use the SSH tunnel described in README.md. Do not expose the service publicly.
4. Use the existing library samples for a repeatable demo. A new upload can use `data/smoke-validation-candidates-2026-10-20/workplace/3_te8.mp4` (three seconds), or `data/smoke-validation-candidates-2026-10-20/bilkent/sEmptyR1.avi` (28 seconds).

## Presentation sequence

1. **Video library:** Search `Factory`. Explain that CCTV remains on the Mac. Expand Activity to open previous analyses and exports. “New analysis” reuses the existing upload.
2. **Set up analysis:** Show all five options: fire, smoke, smoking behavior, no helmet, and restricted-area intrusion. Draw at least three noncollinear points on the source image, finish the zone, and name the camera. Choose MPS on this Mac. The zone is a demo configuration, not an assertion about the site's real restricted areas.
3. **Process:** Start analysis. Every admitted source frame is processed by the local worker. On the audited W04 run all 75 frames and all five capabilities completed. Leave and return through the library to demonstrate persistence.
4. **Review:** Open the W04 smoke candidate. Play the source, switch to Frames if useful, and inspect the box and original source times. The broad floor detection is a false alarm in this short development sample. Show the saved false-alarm decision and note. Machine evidence remains visible and distinct from the human decision. Editing a review requires Save; leaving with a draft asks before discarding it.
5. **Uncertainty and history:** Search `sEmptyR1` in Incident history and filter Uncertain. Open the manual smoke observation from 00:05–00:22. It records visible plume/haze with unclear substance; it is not independently verified fire smoke. Show the review history and the link back to the source workspace.
6. **Export:** Export JSON for the full audit trail, CSV for a summary, or an MP4 for one selected incident plus its separate manifest. The MP4 contains source imagery, not a burned-in overlay, and omits audio. Export progress provides download links and Back to review. Saved exports remain reachable from library Activity.

## Ready-made review links

- W04 all-five audit run, saved false alarm: http://127.0.0.1:8008/#/review/c7c921a4-87fb-44f0-8690-7df070a16fdc
- B01 plume/haze and manual uncertainty: http://127.0.0.1:8008/#/review/5cdfb7c8-3951-47ae-90cc-6e29708ea5c8

These IDs refer to this Mac's existing local database; they are not seeded automatically on a new installation.

## Explain the limits accurately

- All five pipelines are integrated. Their completion means processing finished, not that an incident was proven or the scene was safe.
- Smoking behavior remains visibility-dependent and is explicitly unassessable in the W04 sample. A missing detection is not a negative label.
- False alarms remain, including the W04 smoke example. Representative labeled industrial CCTV and independent evaluation are still required.
- This is one local operator and one sequential worker. Live camera streams, external alerts, team accounts, public hosting and production accuracy validation are outside this MVP.
- Upload limits: 250 MiB, five minutes, 1920×1080, nominal 60 FPS. Local storage quota: 4 GiB.
- If a worker stops, start it again and retry interrupted jobs explicitly. Cancellation and retry retain separate job records. If playback is unavailable, use the Frames view (approximately one source still per second).
