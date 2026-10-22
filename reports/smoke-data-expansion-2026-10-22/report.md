# Smoke training-data expansion — 22 October 2026

**Result: audited another 7,370-image collection, but admitted zero images to training.** ISFire-4 is not a suitable wholesale replacement for the rejected FASDD pilot. It contains the reserved house-video scene, almost no empty-label negatives, repeated scenes and synthetic-looking smoke examples. The app remains on its existing baseline. No second training run was started.

## Sources checked

| Source | Verified finding | Disposition |
| --- | --- | --- |
| [IFireSmoke](https://huggingface.co/datasets/shahriar-5/IFireSmoke) | Public paper links to it and indexed README states CC BY 4.0. Anonymous API request returned HTTP 401 today. The [paper](https://doi.org/10.1371/journal.pone.0322052) describes a mixture of local, web and synthetic images. | Access unavailable in this check; do not assume an Alipan account would help. |
| [ISFire-4](https://huggingface.co/datasets/shahriar-5/ISFire-4) | Public, ungated archive downloaded and inspected. Four classes: black smoke, blue fire, white-gray smoke, yellow-orange fire. | Quarantined for inspection; not added to training. |
| [Home-fire](https://github.com/PengBo0/Home-fire-dataset) | Author describes 6,500 indoor images, early smoke and video-source references. README explicitly states CC BY-NC 4.0. | Research lead; not selected for this product training batch. No archive downloaded. |
| [LFDN](https://mivia.unisa.it/large-fire-dataset-with-negative-samples-lfdn/lost-password/?template=default) | Publisher describes flame/smoke boxes and challenging negatives including glare, headlights and dust. Download/request endpoint timed out again. | Useful lead, access and actual sample relevance still unverified. No form submitted or email sent. |
| [FireAndSmoke](https://github.com/CostiCatargiu/NEWFireSmokeDataset_YoloModels) | Publisher links to two Roboflow projects marked CC BY 4.0 and describes fire, smoke and an `other` class for confusing lights/reflections. The collection also includes aerial and forest imagery. | Additional broad pool to inspect selectively; no archive or quality claim in this pass. Publisher downloader was inspected as text, never executed. |

## ISFire-4 archive audit

- Repository revision: `c64ae7a50883446eeaf700496a206a54087a67b8`.
- Archive: `data/isfire4-audit-2026-10-22/Dataset.zip`, 245,388,412 bytes.
- Verified SHA-256 against the repository's LFS metadata: `fb90a9bfed10f3f00529e2a8d8c512d5f92d8d2e19baac8135e6bdb751722ce9`.
- All **7,370 images** decode and have parseable, geometrically valid YOLO labels. No archive files were unpacked into training directories.
- Provided split: 5,186 training / 1,481 validation / 703 test images.
- Instance counts: 2,665 black smoke; 2,693 blue fire; 2,712 white-gray smoke; 2,940 yellow-orange fire. Total 11,010.
- **Only one empty-label image.** This collection cannot by itself supply the clear walls, glare and normal factory activity needed to teach the detector what to ignore. An empty label also does not prove a visually clear scene.
- There are 7,366 unique image SHA-256 hashes and 7,063 original filename stems. **150 original-filename groups cross the provided splits.** These are source/variant grouping flags; they are not 150 independently verified cameras. Exact-byte duplicate groups do not cross those splits.
- The public dataset card has no explicit license field; embedded `data.yaml` includes Roboflow `license: MIT`. This metadata is recorded rather than silently borrowing IFireSmoke's CC BY license. No standalone license or camera/incident identity file was found in the archive.

Inspected 48 images per class with boxes (192 sample selections, not an exhaustive visual audit). Samples contain repeated kitchen/burner views, stock watermarks, outdoor incidents and conspicuous pasted/composited-looking smoke. Four larger provenance examples are saved separately. Their appearance is a screening observation; it does not establish the origin of every image in the archive.

## Reserved-footage overlap

Compared all 7,370 image perceptual hashes with 2,049 sampled frames from the existing 36 reserved video sources. At Hamming distance at most 6, **259 images match the reserved house-clip family**, and one other image matches an Arson017 frame. At distance at most 12, there are 308 flags in total. Similarity flags are not all individually confirmed source identities.

Visual inspection of ISFire-4 image 596 against house-video frame 1785 confirms the same room, WYZE camera view and incident family. The images show different camera timestamps and aspect ratios, so this is a scene-family overlap, not an assertion of identical pixels or an exact timestamp match. See `confirmed-house-overlap.jpg`.

Training on this family and evaluating on the house clip would contaminate that comparison. The full collection is excluded from this batch, so no automatic near-match filtering is being presented as proof that the remainder is independent. A future carefully curated subset would still require scene-family exclusion, manual review and a fresh split.

## Next useful data batch

Prioritize source-identified real industrial CCTV over another large mixed image archive. Assemble separate groups of clear normal activity (bright walls, backlight, moving equipment), known non-combustion aerosols (steam/dust), early faint smoke, established smoke and real fire. Keep uncertain aerosol labels separate; an unexplained plume must not become an empty-label negative. Keep controlled burner flames distinguishable from unwanted fire hazards.

For each source clip, record original source URL/file hash, permission evidence, site/camera/incident ID, source-file duration, capture type and whether it is accelerated or edited. Label fire/smoke intervals as present/absent/uncertain, then annotate boxes on a sparse set of representative frames. Split by whole site/camera/incident before sampling frames. Keep the existing house, W04/W08, B01/B02 and other reserved families outside training; collect similar new scenes to address their failure modes.

The next training run should wait for that data improvement. The previous 224-image pilot remains rejected; neither extra epochs nor the inflated public image count addresses its lack of realistic, independent negatives and faint-smoke positives.

## Reproduction and verification

From the repository root, run `.venv/bin/python reports/smoke-data-expansion-2026-10-22/audit_isfire4.py --self-test`, then the same command without `--self-test` to rebuild archive counts, manifest, filename/byte duplicate groups and the four sample sheets. The script verifies the pinned archive hash, validates all labels and never copies data into the training set.

`download.json`, `ISFire-4-metadata.json`, `archive-data.yaml`, `archive-audit.json`, `duplicate-groups.json` and `reserved-overlap.json` preserve audit evidence. The larger per-image manifest stays with the ignored local archive at `data/isfire4-audit-2026-10-22/archive-manifest.json`; it is reproducible from the script and is not checked into Git. Perceptual matching used the existing `phash` helper and reserved source list from the FASDD pilot, sampling approximately two frames per second. Similarity flags and source-family confirmation have the limitations described above. No model accuracy improvement is claimed.
