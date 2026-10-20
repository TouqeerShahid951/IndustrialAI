# Footage search and source-quality review — 2026-10-20

Found new sources and downloaded **18 candidate videos**, totaling **19.88 minutes / 68.56 MB**. All 29,149 reported frames decoded successfully. These are source candidates, not new benchmark results. No detector inference, training or test-set promotion was performed.

## Best sources for the project

| Source | Useful material | Verified access / current status |
|---|---|---|
| [CMOT — author repository](https://github.com/XZ-YAN/CMOT-Dataset) | 100 construction videos; worker helmet/no-helmet categories, machinery, fixed/high-angle, night and rain sequences | Author-linked [Alipan share](https://www.alipan.com/s/bJnzTju4Ra8) lists actual MP4s. Previewing 0077.mp4 opens a login requirement. No account was used and no CMOT video was downloaded. Publisher restricts use to noncommercial research (CC BY-NC 4.0). |
| [D-Fire surveillance videos — author repository](https://github.com/gaia-solutions-on-demand/DFireDataset) | Actual surveillance examples in the publisher’s separate video folder | Public OneDrive folder opens without login. FP1.mp4 preview shows a timestamped fixed-camera dusk landscape and bright light. Browser download did not produce a usable local file. Source overlap with the current D-Fire checkpoint is unresolved, so keep exploratory. |
| [KMU Fire & Smoke Database](https://cvpr.kmu.ac.kr/Dataset/Dataset.htm) | Indoor plumes plus confusing outdoor/indoor scenes | Downloaded 10 publisher-negative clips (17.72 min) and 2 publisher-labeled smoke clips. Research/lab/exterior material, not a factory CCTV collection. Publisher permits free download only for academic research; commercial-use permission is not established. |
| [SARD construction video dataset](https://zenodo.org/records/19926448) | Construction activities, workwear, ladders, scaffolding and welding | Downloaded six small CoreSet clips using HTTP ranges, without downloading the 8.25 GB archive. Zenodo metadata declares CC BY 4.0. Selected clips are mostly close-up/edited instructional or social video, so supplement development only. Underlying third-party source provenance still needs review. |
| [Exact user-selected smoking CCTV](https://www.youtube.com/watch?v=1_0NMTqbAC0) | Smoking in a security-camera view, according to publisher title | Exact title resolved through YouTube oEmbed: “Security Camera Captures Guy Farting Loudly While Smoking - 1259434”, RM Videos. Automated download returned HTTP 429 / sign-in bot check. No local video or smoking result is claimed. |

## CMOT sequences to obtain first

From the publisher’s training partition: **0011, 0013, 0039** list both helmeted and non-helmeted workers under static high-angle cameras; **0023 and 0031** provide static night machinery scenes. The share’s train folder was verified in the browser. Sequence 0077 was also present but is marked shaky in the publisher table. Those scene attributes come from the publisher; exact target visibility still needs video review. Labels identify whole workers, so they cannot be compared directly to our head-box annotations without reconciliation.

## Downloaded files: source review

| File | Seconds | Candidate use / limitation |
|---|---:|---|
| [smoke_or_flame_like_object_1.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_1.avi) | 7.12 | Person moving in red clothing; research-room camera; no detector boxes seen in sampled frames. |
| [smoke_or_flame_like_object_10.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_10.avi) | 76.25 | Outdoor city/landscape with clouds. |
| [smoke_or_flame_like_object_2.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_2.avi) | 22.08 | Illuminated Las Vegas sign and traffic; useful bright-light negative, not an industrial site. |
| [smoke_or_flame_like_object_3.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_3.avi) | 35.92 | Moving person and changing television/monitor imagery in a room. |
| [smoke_or_flame_like_object_4.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_4.avi) | 37.67 | Outdoor landscape and clouds. |
| [smoke_or_flame_like_object_5.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_5.avi) | 342.88 | Hazy outdoor roof/campus scene; plume cause not independently verified. |
| [smoke_or_flame_like_object_6.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_6.avi) | 304.88 | Low-visibility outdoor scene; publisher negative, environmental cause not independently verified. |
| [smoke_or_flame_like_object_7.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_7.avi) | 83.83 | Low-visibility trees/building scene; publisher negative. |
| [smoke_or_flame_like_object_8.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_8.avi) | 35.38 | Outdoor clouds/sky with distant buildings. |
| [smoke_or_flame_like_object_9.avi](../data/cctv-candidates-2026-10-20/kmu-hard-negatives/smoke_or_flame_like_object_9.avi) | 116.96 | Distant city/landscape and haze. |
| [indoor_daytime_smoke.avi](../data/cctv-candidates-2026-10-20/kmu-smoke/indoor_daytime_smoke.avi) | 26.17 | Visible plume from a floor appliance. Publisher calls it smoke; combustion origin is unverified. Do not label verified fire smoke or verified steam by appearance alone. |
| [indoor_night_smoke.avi](../data/cctv-candidates-2026-10-20/kmu-smoke/indoor_night_smoke.avi) | 39.33 | Same type of room/appliance plume under low light; camera settings menu obscures the source throughout sampled frames. Exclude from clean test set. |
| [Carry-object__9i1BAqRDS4g_0_06_0_11.mp4](../data/cctv-candidates-2026-10-20/sard/Carry-object__9i1BAqRDS4g_0_06_0_11.mp4) | 5.00 | Portrait handheld/social-video view of workers carrying sacks; not verified fixed CCTV. |
| [Climb-ladders__119_new.mp4](../data/cctv-candidates-2026-10-20/sard/Climb-ladders__119_new.mp4) | 6.17 | Helmeted workers on ladders at a construction site; multiple camera angles/cuts. |
| [Climb-ladders__13_new_09.mp4](../data/cctv-candidates-2026-10-20/sard/Climb-ladders__13_new_09.mp4) | 9.00 | Helmeted worker climbing a ladder beside a house; close view, not verified surveillance. |
| [Install-scaffolding__5uXSwxx50Tw_cut_2.mp4](../data/cctv-candidates-2026-10-20/sard/Install-scaffolding__5uXSwxx50Tw_cut_2.mp4) | 19.00 | Orange workwear, helmets and scaffolding inside a warehouse; edited instructional views, not fixed CCTV. |
| [Weld__0_9686.mp4](../data/cctv-candidates-2026-10-20/sard/Weld__0_9686.mp4) | 9.71 | Portrait close-up of active welding and sparks; supplementary fire-confounder material, not confirmed hazard-free or fixed CCTV. |
| [Weld__1025369_1040917.mp4](../data/cctv-candidates-2026-10-20/sard/Weld__1025369_1040917.mp4) | 15.55 | Close-up of a worker welding a pipe; bright arc/sparks, edited views. Visible process smoke must be labeled separately from unintended fire smoke. |

## Saved evidence

- [Local candidate inventory with source/member names, SHA-256, duration and quality flags](../data/cctv-candidates-2026-10-20/candidates.json)
- [Hard-negative contact sheet](../data/cctv-candidates-2026-10-20/kmu-contact.jpg)
- [Construction / indoor-plume contact sheet](../data/cctv-candidates-2026-10-20/construction-smoke-contact.jpg)
- [Full decode check](../data/cctv-candidates-2026-10-20/decode-check.json)
- [Smoking access result](../data/cctv-candidates-2026-10-20/smoking-download-status.json)

All media originals are retained. Visual screening used three sample positions per clip; full decoding checks readability, not semantic labels. At acquisition no clip had reviewed event labels; see subsequent chat-review progress below. Independent adjudication is still pending. No candidates were inserted into benchmark/manifest.jsonl, so existing baseline/test membership remains intact.

## Acquisition decision

CMOT is the strongest newly located construction CCTV source. The downloaded KMU negatives can broaden exploratory false-alert testing; the SARD welding/orange-workwear clips can probe confounders. The appliance plumes must stay ambiguous until their physical source is established, and the night camera-menu overlay excludes that clip from a clean test set. These downloads do not close the clean industrial fire/smoking or independent-site validation gaps.


## Subsequent chat-review progress

The user reviewed clips 001–004 (KMU lookalike files 1–4): no fire and no smoke across all four clips, totaling 102.792 seconds. Labels are saved under `data/cctv-candidates-2026-10-20/review/annotations/` with single-reviewer status. They remain outside the scored benchmark.

Relevance: these four are background/false-alert examples, not positive hazard examples or representative industrial validation. The first four review selections over-emphasized generic negatives. Prioritize target-camera industrial/construction scenes, visible positive events and matched operational negatives for subsequent review. CMOT is a closer PPE source but its footage has not been acquired; the six SARD downloads are mostly edited views.
