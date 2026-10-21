# Smoke validation footage — screened candidate batch, 20 October 2026

Collected **28 videos (88.12 MB decimal)** and decoded all **7,886 frames**. Kept **26 candidates**: eight real factory CCTV clips, six staged smoke clips, and twelve industrial-emission time-lapses. Two traffic clips repeat scenes already present in the old FIRESENSE collection and are excluded from the new review queue. These counts describe acquisition and screening, not reviewed ground truth or independent model validation.

## Most relevant new source

The eight factory videos are from [Önal and Dandıl’s Safe and Unsafe Behaviours dataset](https://data.mendeley.com/datasets/xjmtb22pff/1), acquired through a [revision-pinned public mirror](https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours). The original publisher documents security-camera collection at a production facility in Eskişehir, Turkey, company/employee permissions and CC BY 4.0 licensing. The sample contains machinery, walkways, moving workers, high-visibility clothing and forklift movement. It is substantially closer to the project setting than the earlier city/landscape negatives.

The eight videos provide **67.17 seconds** of source playback, from one facility. The original corpus uses two cameras, but exact per-file camera and parent-incident IDs are unavailable here; all eight stay in one conservative site/camera/event group. They must not be split into training and validation individually. The publisher’s safe/unsafe behavior classes are not smoke labels. Four sampled positions per video show no obvious fire or smoke; this remains a proposal requiring full review.

## Source roles and limits

| Source | Acquired | Screened use | Main limit |
| --- | ---: | --- | --- |
| Real factory CCTV | 8 / 67.17 s | Primary worker/machine/forklift negative candidates | Short, single-site examples; smoke absence not yet reviewed |
| [Bilkent VisiFire](http://signal.ee.bilkent.edu.tr/VisiFire/Demo/SampleClips.html) | 8 / 446.46 s | Six primary smoke candidates, 414.96 s total; two traffic scenes excluded | Staged/research footage at 320×240, not verified industrial incidents; license not stated on accessed index |
| [Project RISE](https://github.com/CMU-CREATE-Lab/deep-smoke-machine) | 12 / 36 s playback | Separate industrial-emission appearance supplement: six source positives, six source negatives | Time-lapse; process emissions are not fire-hazard labels |

The RISE supplement is released as CC0 in the [author’s data deposit](https://doi.org/10.21942/uva.31752271). Selection used strong source labels and different dates/views across three camera/site IDs, before any detector inference. Several source-negative examples still show large pale plumes. They are useful smoke/steam lookalikes, but white appearance alone cannot establish composition, and “no industrial smoke emission” is not “no visible plume.” No steam-negative hazard label has been invented. All views from one panoramic source camera remain grouped.

RISE files contain 36 frames at 12 fps: **3 seconds of accelerated playback each**. Their original capture timestamps span much longer periods. They are excluded from real-time confirmation, alert-delay and camera-hour calculations. Fire-related smoke remains the working target; the pending question about routine emissions affects only how this separate supplement is ultimately used.

## Start review with smoke, then actual factory negatives

No detector has run on this new batch. Screening used source descriptions and images, avoiding model-selected examples. Below are the primary candidates in review order. Clip names are new review IDs, separate from the previous seven clips. All annotation files are explicitly **unreviewed**, with empty scored events/frames/intervals.

| ID | Seconds | Review cue | Video |
| --- | ---: | --- | --- |
| B01 | 28.98 | Indoor haze spreads through a mostly empty room; bright doorway and low contrast. Physical smoke source not verified. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B01.mp4) |
| B06 | 90.00 | Small white/gray plume near a red waste container and brick wall. The source library calls this a smoke clip. Not a verified industrial fire incident. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B06.mp4) |
| B05 | 69.04 | Faint diffuse plume near parked vehicles; fixed low camera view outdoors; factory provenance not established. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B05.mp4) |
| W01 | 10.48 | Real factory CCTV: Safe Walkway Violation. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/0_te23.mp4) |
| W08 | 4.01 | Real factory CCTV: Safe Carrying. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/7_te4.mp4) |
| B02 | 23.94 | Same empty-room view as B01, with people crossing the bright doorway and visible haze. Keep grouped with B01. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B02.mp4) |
| B03 | 63.00 | Staged outdoor plume beside a fence, with a person near the source; not a verified factory incident. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B03.mp4) |
| B04 | 140.00 | Same fence view as B03; longer plume sequence. Keep grouped with B03. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B04.mp4) |
| W02 | 7.95 | Real factory CCTV: Unauthorized Intervention. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/1_te11.mp4) |
| W03 | 10.41 | Real factory CCTV: Opened Panel Cover. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/2_te12.mp4) |
| W04 | 3.00 | Real factory CCTV: Carrying Overload with Forklift. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/3_te8.mp4) |
| W05 | 10.44 | Real factory CCTV: Safe Walkway. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/4_te5.mp4) |
| W06 | 10.45 | Real factory CCTV: Authorized Intervention. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/5_te13.mp4) |
| W07 | 10.44 | Real factory CCTV: Closed Panel Cover. No obvious fire/smoke in four screened samples; full smoke-negative label needs review. | [Play](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace/6_te12.mp4) |

First clip, B01 — indoor haze:
![B01 review video](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/B01.mp4)

For each clip, give smoke as **present, absent or uncertain**, then the visible start/end times. Include fire separately, even if absent. If smoke is present, mark its location on representative frames as well; I can extract a frame for an indicated time. Distinguish a plume’s visible extent from its source. Record steam/dust separately when known; unknown plume composition stays uncertain. A full-clip negative label requires reviewing the full clip. Partial review applies only to the stated interval.

Example response: `B01: smoke 4–18 s, fire absent; smoke near the doorway and upper left.` This is a format example, not a proposed label. Independent review is still needed before the resulting annotations can become a locked test set.

## What was excluded or inaccessible

- B07/B08 reproduce the street camera scenes in older FIRESENSE files `fire_neg_negsVideo2.859.avi` / `fire_neg_negsVideo3.860.avi`. Their byte hashes differ, which does not make the scenes independent. Originals are retained for provenance; both are removed from the new queue.
- [NVIDIA AMC NV Warehouse](https://catalog.ngc.nvidia.com/orgs/nvidia/resources/amc-nv-warehouse): public access worked, but the [Sample Data License](https://developer.nvidia.com/downloads/amc-nv-warehouse-eula) limits the stated use to evaluating NVIDIA technologies. No warehouse videos were downloaded or used.
- [SteelBench](https://huggingface.co/datasets/steelbench/SteelBench): HTTP 401 on metadata/raw access, no media acquired. No account was created.
- SmokeBench image pairs, synthetic CCTV, and generic MEVA activity footage were not substituted for target industrial footage. No paid datasets or services were used.

## Validation boundary and remaining work

The original baseline manifests, seven user labels, inference outputs and benchmark reports remain unchanged. This collection is a **validation candidate pool**; it has not been promoted to validation or locked test. Possible overlap with pretrained detector training data remains unknown. No thresholds were selected, alternative detector ranked, fine-tuning performed or production claim made.

The next dependent work is to confirm fire/smoke time intervals and smoke locations, resolve ambiguous plume types, and independently review the labels. Then compare the current and an alternative detector on a fixed validation partition, with camera/site/incident grouping. This batch adds relevant scenes but does not provide long negative exposure, dust examples, many factories or verified real industrial fire incidents. Those are explicit collection gaps.

## Evidence and checks

- [Factory contact sheet](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/workplace-contact.jpg)
- [Smoke contact sheet](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/bilkent-contact.jpg)
- [Industrial-emission contact sheet](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/rise-contact.jpg)
- [All 28 source records, media counts, hashes and screening notes](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/candidates.json)
- [26-item annotation queue](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/queue.json)
- [Source/license/access audit](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/source-audit.json)
- [Preview provenance and frame-count checks](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/review/previews.json)
- [Final verification](/Users/tabbasi/Downloads/IndustrialAI/data/smoke-validation-candidates-2026-10-20/verification.json)

Original source SHA-256 and completed frame counts are retained for every file. Factory downloads match upstream file sizes and LFS SHA-256. Previews use H.264 and retain the source frame count; encoder frame-rate rounding changes duration by under 0.05 seconds. Score originals, not preview copies. Metadata and publisher label files are stored alongside the media.

Attribution: Oğuzhan Önal and Emre Dandıl, Video Dataset for Safe and Unsafe Behaviours, Mendeley Data V1, 2024, DOI 10.17632/xjmtb22pff.1 (CC BY 4.0). Project RISE: Yen-Chia Hsu et al., AAAI 2021 (dataset CC0). Bilkent VisiFire source library: A. Enis Cetin and collaborators; citation/reuse requirements must be resolved before treating those samples as permissioned evaluation data.

Run the integrity check from the project directory:

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from scripts.benchmark_data import file_sha256, _validate_labels
root=Path('data/smoke-validation-candidates-2026-10-20')
data=json.loads((root/'candidates.json').read_text())
assert len(data['items']) == len({x['source_sha256'] for x in data['items']}) == 28
for item in data['items']:
    assert file_sha256(item['source_path']) == item['source_sha256']
    assert item['media']['frames'] == item['media']['decoded_frames'] > 0
    labels=json.loads(Path(item['annotation_path']).read_text())
    _validate_labels(labels,item['duration_seconds'],False)
    assert labels['source_sha256'] == item['source_sha256']
for path,sha in data['baseline_hashes'].items():
    assert file_sha256(path) == sha
queue=json.loads((root/'review/queue.json').read_text())['items']
assert len(queue)==26 and all(i['priority']!='excluded' for i in queue)
for preview in json.loads((root/'review/previews.json').read_text()):
    assert file_sha256(preview['preview_path']) == preview['preview_sha256']
    assert preview['source_frames'] == preview['preview_frames']
print('28 sources verified; 26 queued; preview hashes and baseline unchanged')
PY
```
