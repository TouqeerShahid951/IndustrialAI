# Public-footage smoke training — 23 October 2026

Public footage produced a useful development candidate, but it has not solved smoke detection. With the same frozen image encoder, fitting method and threshold, adding clear and smoky observations from one laboratory camera increased smoke-positive sample coverage on other cameras from **52/281 (18.5%) to 206/281 (73.3%)**. Most of that increase comes from one workshop video. Weak backlit smoke still fails temporal confirmation, and inspection outside the original labels found two false-positive stills. **The app and its default detector remain unchanged.**

## Data acquired and screened

| Public source | Downloaded | Inspection and role |
|---|---|---|
| [MEVA](https://mevadata.org/), [data documentation](https://mevadata.org/resources/README-meva-kf1-data.html), [CC BY 4.0 terms](https://mevadata.org/resources/MEVA-data-license.txt) | Six CCTV files, including two indoor recordings totaling about 9.5 minutes | Reviewed 286 stills at two-second intervals from the longer stairs/corridor recordings. Labeled those stills only as no visible smoke/fire. Selected eight clear training frames, four per view. All MEVA views stay together as `meva-kf1-all`. These are building interiors, not industrial process steam/dust. |
| [FIRESENSE smoke archive](https://zenodo.org/records/836749), CC BY 4.0 in publisher metadata | 22 videos: 13 source-positive, nine source-negative | Inspected four overview samples per file. Mostly outdoor footage; some repeats of existing public sources. No new fitting data. The indoor workshop clip was already reserved and remains held out for this experiment. It includes source-drawn contours. |
| [Indoor Fire Smoke](https://zenodo.org/records/15826133), CC BY 4.0 in publisher metadata; [upstream collection](https://universe.roboflow.com/object-detection-7qn6l/indoor-fire-smoke/dataset/1) | 5,000 images and YOLO labels | Audited all labels/filenames; visually inspected a 36-image screen and 144 diverse images. Reviewed 29 positive stills across nine approximate visual source families; capped fitting at three per family, leaving 18. Excluded uncertain device aerosols and all unreviewed material. This is a mixed-source image supplement, not 5,000 verified CCTV images. |

The indoor archive has **zero clean negative labels**, 89 images with explicit AI-related filenames, and class names only `0`/`1`. Publisher labels were not inherited as scene truth. No exact image-byte duplicates were found among its 5,000 files, but related frames/camera families appear across its supplied random folders; that split was not accepted as an independent camera test. Positive source-family names in `curate.py` are visual grouping aids, not independently verified provenance. Underlying third-party image rights and the pretrained encoder's source overlap remain unverified.

Download integrity: publisher MD5 and ZIP CRC checks passed for both archives. Six MEVA downloads have recorded sizes, SHA-256 values and S3 ETags; multipart ETags were checked using their part layout. Original files are retained under `data/public-training-footage-2026-10-23/` and are excluded from Git. OpenCV did not fully decode five FIRESENSE files, most severely negative clip 03 (182/748 reported frames); none entered fitting. MEVA files decode completely but report a timestamp reset on their final one or two frames. Those frames were excluded from still selection; no source retiming was performed.

Annotations are by one assistant reviewer. New MEVA labels apply only to the 286 inspected stills, not to unviewed intervals. Visible plume labels do not chemically establish smoke versus another aerosol. See `meva-frame-annotations.json`, `image-review.json`, the contact sheets and `supplemental-frame-review.json`.

## Experiments and camera allocation

**Small public-image addition:** retained the previous 176 FASDD training images and added the 18 screened positive images plus eight MEVA negatives. The 202-image head recovered only **1/19** positive frames on the previous sparse CCTV development check, versus 0/19 before; both had 0/36 known-negative flags. Its original 48-image internal validation result stayed 44/48. This addition was insufficient.

**New paired-camera experiment:** moved the **entire** `mmodalfire-xian-ch01` family, clips C01–C15, from development validation to training/exclusion for this candidate. Its previous results are historical diagnostics and cannot validate this head. Original manifests and prior reports were preserved. This explicit allocation change supersedes the earlier intention to keep MmodalFire reserved.

Selected 56 reviewed smoke-positive frames and 56 reviewed clear/documented-water-mist frames from that laboratory camera, producing **314 fitting images: 156 positive, 158 negative**. Unknown smoke intervals were excluded. The 112 additions are observations from one camera, not 112 independent scenes. The 48 original FASDD validation images were not fitted.

The recipe was fixed before the new evaluation: frozen Google SigLIP2 base patch16/224 encoder, L2-normalized features, ridge coefficient 0.1 and decision threshold zero. Only the linear scene head was fitted; this was not YOLO box-detector fine-tuning. Scores are uncalibrated decision values, not smoke probabilities. No localization boxes are invented for scene predictions.

The new comparison uses **20 other clips**: F01–F08, clip-001–007, W04/W08, B01/B02 and workshop-smoke. All **9,401 native frames** decoded with increasing source timestamps; inference sampled **949 frames at 2 Hz**. Of those, 281 are within reviewed smoke-positive windows, 466 within reviewed negative windows and 202 are unknown/excluded. The camera/source grouping differs from fitting, subject to the public-source provenance limits above. These are previously exposed development clips, not a new blind test. The 629-frame perceptual overlap screen found no close matches for the newly selected image families, but that cannot prove independence from every training or pretraining source.

## Results on the 20 development clips

| Head | Fitting rows | Smoke-positive hits / 281 | Known-negative flags / 466 |
|---|---:|---:|---:|
| Unpaired public-image control | 202 | 52 (18.5%) | 0 |
| Paired camera additions | 314 | 206 (73.3%) | 0 |
| Post-hoc control: same extra smoke frames, generic negatives repeated instead of matched clear/mist frames | 314 | 248 (88.3%) | 1 |

The last row is an **explanatory ablation designed after the first results**. It preserves fitting-row count and class balance by repeating 56 existing generic negatives. It is not 56 new negative images, an independent confirmation, or evidence that matched negatives are categorically superior. Matched negatives reduce one flag on clip-003 and improve B01 coverage, but also suppress many workshop positives. No threshold was selected on these results.

| Reviewed smoke clip | Positive samples | Unpaired hits | Paired hits | Post-hoc generic-negative control hits | Paired temporal event detected? |
|---|---:|---:|---:|---:|---|
| clip-007, reviewed core 34–40 s | 12 | 9 | 8 | 12 | Yes |
| B01, backlit plume | 33 | 12 | 21 | 15 | Yes |
| B02, weak backlit plume | 17 | 1 | 1 | 2 | **No** |
| workshop-smoke, source contours present | 219 | 30 | 176 | 219 | Yes, fragmented |

The workshop supplies 219/281 positive samples. **Excluding it**, paired coverage is **30/62 (48.4%)**, versus **22/62 (35.5%)** for the unpaired control. This is evidence of some transfer, not a universal 73% smoke recall claim. The clip count, correlated frames and single-reviewer labels are too limited for deployment accuracy claims.

### Event behavior

Scene temporal verification requires the current sample to be positive and at least three positive observations spanning one second within the preceding two seconds. Candidate spans are merged across gaps up to two seconds. The shared event scorer counts extra fragments of one labeled incident as false-positive events.

| Variant / policy | Matched incidents | Extra/unmatched events | Missed incidents |
|---|---:|---:|---:|
| Current app YOLO, raw native observations | 3 | 9 | 1 |
| Current app YOLO, native spatial temporal verification | 1 | 7 | 3 |
| Unpaired scene control, raw | 4 | 5 | 0 |
| Unpaired scene control, temporal | 3 | 3 | 1 |
| Paired scene head, raw | 4 | 0 | 0 |
| Paired scene head, temporal | 3 | 7 | 1 |
| Post-hoc generic-negative control, raw | 4 | 2 | 0 |
| Post-hoc generic-negative control, temporal | 3 | 0 | 1 |

All seven paired temporal extra events are **duplicate fragments within workshop-smoke**, not seven alarms on clear scenes. Raw event matching can succeed from a brief positive: B02 has just one paired hit, around 9.03 s, and then fails temporal confirmation. The current detector's native spatial votes and the scene head's 2 Hz binary votes are different representations/cadences; this table is not a controlled detector-architecture comparison or a localization benchmark. Positive alert spans can bridge short gaps, so they are not equivalent to frame-level coverage.

Only **230.15 seconds** have known-negative interval labels. None of the paired scene events intersects those intervals, but that is inadequate exposure to estimate operational nuisance alarms per hour.

## Failures found beyond the old labels

The zero flags in 466 negative samples **does not mean zero false positives overall**. Model-selected review of previously unknown clip-007 times found:

- **3.0 s:** a publisher title card with no visible smoke is flagged positive.
- **9.0 s:** a street frame with no visible smoke is flagged positive.
- **27.5 and 32.0 s:** visible gray plume appears before the original user-confirmed 34–40 s core. These stills were separately annotated; unreviewed neighboring times remain unknown.

These are post-hoc diagnostic stills, not an unbiased false-positive-rate sample. Original labels were not silently extended or changed. B02 remains mostly negative despite its visible backlit plume. See [inspected prediction frames](prediction-review.jpg).

## Decision and next work

**Do not promote this candidate to the app default.** The data result supports continuing scene-level smoke modeling, but neither this head nor threshold tuning has resolved faint smoke, out-of-distribution frames or reliable incident continuity. The matched-mist camera is now training data, so it cannot establish held-out steam/mist robustness.

Continue with public footage: acquire additional camera families with paired clear/smoky views and identifiable steam, mist or dust sources; inspect and label their uncertain intervals explicitly. Keep each family wholly in training, validation or a fresh blind test. Add clear backlit scenes, reflections and non-scene title cards to development negatives, while retaining a separate test family. Choose thresholds and event continuity rules on validation only, then rerun the unchanged blind evaluation. No deployment-site data is assumed available.

Before MVP integration, require repeatable improvement across several independent smoke sources, recovered weak-plume events, and a much longer separate steam/dust/normal-operation test. A scene alert should carry source time and evidence frames; it must not borrow object boxes or present an uncalibrated score as a probability.

## Reproduction and artifacts

Run from `/Users/tabbasi/Downloads/IndustrialAI` using the existing virtual environment. The encoder and isolated transformer runtime are those pinned and hashed in `reports/detector-root-cause-2026-10-22/scene-model.json`; app dependencies were not changed.

```sh
.venv/bin/python reports/public-training-footage-2026-10-23/curate.py --self-check
.venv/bin/python reports/public-training-footage-2026-10-23/train_probe.py --self-check
.venv/bin/python reports/public-training-footage-2026-10-23/paired_camera.py --self-check
.venv/bin/python reports/public-training-footage-2026-10-23/verify.py
```

To refit and repeat source-video inference using retained local downloads:

```sh
.venv/bin/python reports/public-training-footage-2026-10-23/curate.py
PYTHONPATH=outputs/detector-root-cause-2026-10-22/scene-runtime HF_HUB_OFFLINE=1 .venv/bin/python reports/public-training-footage-2026-10-23/train_probe.py
PYTHONPATH=outputs/detector-root-cause-2026-10-22/scene-runtime HF_HUB_OFFLINE=1 .venv/bin/python reports/public-training-footage-2026-10-23/paired_camera.py
```

`experiment-spec.json` and `paired-camera-spec.json` record the distinct protocols. `paired-training-manifest.json` records fitting images and hashes. `paired-camera-results.json` preserves every evaluated score, source-frame index, annotation hash and event. `ablation-spec.json` marks the post-hoc comparison. `verification.json` records fresh checks. Candidate weights and cached embeddings remain local under `outputs/public-training-footage-2026-10-23/`; they are not app defaults or committed binary dependencies.
