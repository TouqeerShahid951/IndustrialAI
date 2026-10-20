# Direct CCTV alternatives — 2026-10-20

CMOT remains blocked by Alipan authentication. No account was created, and no verified public CMOT mirror was found. Public direct downloads were used for this batch.

Acquired three UCF-Crime Arson-category videos from the [MTEB public mirror](https://huggingface.co/datasets/mteb/ucf-crime), cross-referenced to the [original UCF dataset](https://www.crcv.ucf.edu/research/real-world-anomaly-detection-in-surveillance-videos/). All three downloads match upstream file sizes/LFS SHA-256 where supplied, and all frames decode. No login or model inference was used. Access does not establish commercial reuse permission; mirror/original rights and training overlap remain review items.

| File | Duration | Source review |
|---|---:|---|
| [Arson012_x264.mp4](../data/cctv-direct-2026-10-20/ucf-crime/Arson012_x264.mp4) | 29.80 s | Fixed CCTV-style parking area at night; visible bright incident and edited ending. Exact event times need human review. |
| [Arson017_x264.mp4](../data/cctv-direct-2026-10-20/ucf-crime/Arson017_x264.mp4) | 46.07 s | Fixed roadside CCTV excerpt with Telegraph watermark and ITN/Telegraph end card. Positive evidence not established by sparse screening; edited source. |
| [Arson049_x264.mp4](../data/cctv-direct-2026-10-20/ucf-crime/Arson049_x264.mp4) | 12.87 s | Fixed night CCTV/playback view with visible flames in sampled frames; timestamp and playback OSD; no detector boxes seen. Specific facility/industrial provenance unverified. |
| [hardhat.mp4](../data/cctv-direct-2026-10-20/ppe-source/hardhat.mp4) | 60.93 s | KARAM-branded edited PPE demonstration/advertisement with multiple camera angles, rather than fixed surveillance. No claim of new representative PPE CCTV. |

Only the three UCF clips enter the development-candidate pool. The downloaded PPE video is excluded from the CCTV review queue because it is an edited advertisement. CCTV examples here are property/parking/roadside scenes; factory-camera provenance is not verified. These files improve surveillance realism but do not complete the site-matched industrial dataset.

Human review of **clip-005** (Arson049_x264.mp4): fire 3–12 seconds; smoke ambiguous across the entire clip and excluded from scoring. The final 0.867 seconds remain unreviewed for fire because the supplied endpoint is approximate. Single-reviewer labels are saved in review/annotations/clip-005.json. Human review of **clip-006** (Arson012_x264.mp4): fire begins approximately at 8 seconds and continues through clip end, 29.8 seconds. The user subsequently marked smoke uncertain across the entire clip; it is excluded from smoke scoring. No records were added to benchmark/manifest.jsonl and no locked-test membership changed.

- [Download provenance / SHA-256 / full decode results](../data/cctv-direct-2026-10-20/downloads.json)
- [Screening contact sheet](../data/cctv-direct-2026-10-20/ucf-contact.jpg)
- [Review clip 005](../data/cctv-candidates-2026-10-20/review/clip-005.mp4)

Human review of **clip-007** (Arson017_x264.mp4), 46.067 seconds: no fire in reviewed CCTV [0,43] seconds; smoke approximately 34–40 seconds. Other smoke intervals remain unreviewed. CCTV is visible at 43.0s and the news end card by 43.5s; conservatively exclude 43 seconds through clip end from all reviewed exposure. Independent adjudication is pending.
