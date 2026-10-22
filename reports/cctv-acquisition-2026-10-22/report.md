# New CCTV clip acquisition — 22 October 2026

Prepared **23 short review clips**: eight additional operating-factory recordings and 15 excerpts from newly acquired laboratory CCTV. These are candidate annotation material, not an admitted training set. The application model, thresholds and saved user reviews are unchanged.

## Sources and what was actually acquired

1. **Operating-factory footage:** [Video Dataset for Safe and Unsafe Behaviours, Önal and Dandıl](https://data.mendeley.com/datasets/xjmtb22pff/1), CC BY 4.0. Downloaded eight additional files from the pinned [Voxel51 mirror](https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours), revision `7369ff1830b5f6c00f7d7383eeeaa90704bfc5b5`. All file SHA-256 hashes match repository LFS metadata. The source documents two fixed IP cameras in an operating production facility in Eskişehir, Turkey. The selected clips show machine areas, workers, forklift movement and reflective floors. These are new files from the **same facility/camera families as our previous factory development clips**, not independent sites. Sampled inspection found no visible fire or smoke; their fire/smoke intervals still need final review.

2. **New smoke/fire/nuisance CCTV:** [MmodalFire, Jia et al.](https://doi.org/10.6084/m9.figshare.28804448.v1), [publisher description](https://doi.org/10.1038/s41597-026-06810-6), CC BY 4.0. Acquired nine complete raw MP4 recordings, totaling approximately **350.7 minutes**, plus the experiment worksheet and README. The selected recordings are real monitoring-camera footage from a controlled laboratory, not rendered or pasted smoke. Fifteen short excerpts cover clear rooms, people moving, small flames, fire growth, developing/dense/residual smoke, a water-mist test and a blank-control interval. **All selected laboratory clips share the same camera family (`ch01`).** They supplement the industrial CCTV problem; they do not establish field performance at factories.

The MmodalFire release is a 4,929,210,010-byte RAR. To avoid downloading unrelated hours, indexed its real headers with CRC checks, fetched selected non-solid file byte ranges, extracted with macOS `bsdtar`, checked each selected file's CRC32 and recorded SHA-256 hashes. **The complete archive was not downloaded, so its published whole-archive MD5 was not verified.** The local sparse archive is an extraction aid, not a complete downloaded archive. Files used below are complete and individually verified. No new packages were installed.

## Short review clips

The 15 laboratory excerpts total approximately 705 seconds; the eight factory clips total approximately 111 seconds. The 23 files represent about **13.6 minutes of review material**, not 23 independent incidents. Original raw recordings and derived excerpts are not counted twice.

| Clip | Content / candidate use | Duration | Source group |
| --- | --- | ---: | --- |
| [F01](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/0_tr16.mp4) | Factory machinery/workers; negative candidate | 17.0 s | Existing Eskişehir facility; development only |
| [F02](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/1_tr20.mp4) | Factory machinery/workers; negative candidate | 20.8 s | Existing Eskişehir facility; development only |
| [F03](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/2_tr125.mp4) | Factory machinery/workers; negative candidate | 11.0 s | Existing Eskişehir facility; development only |
| [F04](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/3_tr1.mp4) | Factory forklift/reflective floor | 13.0 s | Existing Eskişehir facility; development only |
| [F05](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/4_tr47.mp4) | Factory machinery/workers; negative candidate | 15.6 s | Existing Eskişehir facility; development only |
| [F06](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/5_tr21.mp4) | Factory machinery/workers; negative candidate | 15.0 s | Existing Eskişehir facility; development only |
| [F07](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/6_tr1.mp4) | Factory machinery/workers; negative candidate | 6.0 s | Existing Eskişehir facility; development only |
| [F08](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/factory/7_tr17.mp4) | Factory forklift/reflective floor | 12.1 s | Existing Eskişehir facility; development only |
| [C01](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C01.mp4) | Clear room and bright doorway | 30.0 s | M01; shared laboratory ch01 |
| [C02](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C02.mp4) | People moving in a clear room | 30.0 s | M04; shared laboratory ch01 |
| [C03](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C03.mp4) | Small flame ignition and growth | 60.0 s | M05; shared laboratory ch01 |
| [C04](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C04.mp4) | Early smoke and developing haze | 60.0 s | M05; shared laboratory ch01 |
| [C05](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C05.mp4) | Smoke spreading through room | 45.0 s | M05; shared laboratory ch01 |
| [C06](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C06.mp4) | Dense smoke and backlight | 45.0 s | M05; shared laboratory ch01 |
| [C07](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C07.mp4) | Second experiment: small flame growth | 60.0 s | M06; shared laboratory ch01 |
| [C08](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C08.mp4) | Second experiment: flame and early smoke | 45.0 s | M06; shared laboratory ch01 |
| [C09](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C09.mp4) | Second experiment: smoke obscuring flame | 45.0 s | M06; shared laboratory ch01 |
| [C10](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C10.mp4) | Residual smoke and bright doorway | 45.0 s | M06; shared laboratory ch01 |
| [C11](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C11.mp4) | Water-mist experiment; non-combustion aerosol | 45.0 s | M08; shared laboratory ch01 |
| [C12](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C12.mp4) | Blank-control interval after mist experiment | 45.0 s | M08; shared laboratory ch01 |
| [C13](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C13.mp4) | Additional experiment: residual smoke | 45.0 s | M09; shared laboratory ch01 |
| [C14](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C14.mp4) | N-heptane timing window: active fire | 60.0 s | M09; shared laboratory ch01 |
| [C15](/Users/tabbasi/Downloads/IndustrialAI/data/cctv-acquisition-2026-10-22/review-clips/C15.mp4) | Later N-heptane timing window: active fire | 45.0 s | M09; shared laboratory ch01 |

The excerpt descriptions are triage observations, not frame-by-frame ground truth. The same burn's ignition, smoke growth and residual haze remain one incident family. Laboratory phases from M05, M06 and M09 must not be split across training and evaluation. More strongly, keep the whole selected laboratory camera family in one dataset role. Keep the factory facility with its existing development footage rather than using these adjacent scenes to train against that evaluation.

The water-mist excerpt C11 corresponds to the worksheet's Mist4 window (10 August, 16:31–16:37); its retained camera clock shows approximately 16:33. C12 falls in the worksheet's following blank-control window. Mist is a known non-combustion aerosol, not combustion smoke. Residual haze and uncertain plume chemistry should remain explicitly uncertain during annotation. The later, camera-obstructed part of M08 was excluded from the short excerpts. The study also includes dry-ice experiments, but **no selected excerpt is claimed to be a verified dry-ice example**.

Exact event onsets, offsets and bounding boxes remain to be annotated. Native `avconvert` trimmed 30–60-second laboratory excerpts at recorded source-file offsets to 1280×720 H.264 MP4. Burned-in camera clocks are retained; source hashes, offsets and actual decoded durations are in `review-clips.json`. Do not infer an exact event onset from an excerpt title.

## Further source-specific footage found

- [Chevron Richmond refinery surveillance, CSB](https://www.csb.gov/videos/surveillance-video-from-the-august-6-accident-at-the-chevron-refinery-in-richmond-ca/) — actual industrial incident footage. The official page embeds [this video](https://www.youtube.com/watch?v=hewMRcrOI0s).
- [CITGO Corpus Christi refinery surveillance, CSB](https://www.csb.gov/videos/surveillance-video-from-july-19-2009-fire-and-explosion-at-the-citgo-corpus-christi-refinery/) — refinery release, ignition and fire. A pre-ignition vapor cloud must not be casually labeled as smoke or as a harmless negative.
- [NIST electrical cabinet/cable Test 10](https://www.nist.gov/el/fcd/nrc-electrical-cabinet-experiments/test10) and [closed-cabinet Test 11](https://www.nist.gov/el/fcd/nrc-electrical-cabinet-experiments/test11) — controlled scenarios relevant to industrial electrical fires. Published players are timelapses with plots; they cannot measure real-time alarm latency.

These four additional items are verified source-page leads, **not local downloads or training-cleared footage** in this batch. Direct programmatic access returned 403 for some pages; no access restrictions were bypassed. Their reuse permission and actual video segments require checking before training.

Other leads ruled out for this batch: SteelBench currently returns HTTP 401 and its published terms restrict surveillance-product training; NVIDIA AMC warehouse sample terms restrict its purpose to testing NVIDIA technologies; IPAD mixes synthetic/real process footage and does not supply smoke-negative labels; the industrial-hall multi-sensor dataset is time-series data rather than CCTV. None was silently substituted for usable real smoke clips. No accounts were created, forms submitted, emails sent or paid datasets purchased.

## Evidence and next use

`factory-selection.json` and `mmodalfire-selection.json` identify every complete acquired source file. `mmodalfire-metadata.json` records publisher terms and the expected archive checksum; `mmodalfire-archive-index.json` records header offsets, sizes and per-file CRCs. `review-clips.json` identifies the derived clips and source-time offsets. `verification.json` records full decoding of all 23 short clips, unique recorded hashes and no exact file-hash matches with the previous 33 comparison sources. Hash uniqueness does not establish scene, camera or pretraining independence.

Visual screening used source contact sheets, focused ignition/mist sheets and the final preview. It is a single-assistant sampled review, not an independent or exhaustive annotation audit of all 350.7 minutes. No accuracy measurement or training improvement is claimed. The useful next action is interval/box annotation and explicit source-group assignment; a broader set of unseen operating-factory cameras remains a data gap.
