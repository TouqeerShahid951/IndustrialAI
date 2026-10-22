# Fine-tuning dataset shortlist — 22 October 2026

Recommendation: inspect FASDD_CV first as the broad fire/smoke detection pool, supplement with verified industrial hard negatives, and reserve unseen cameras/incidents for evaluation. LFDN is a strong additional negative-data candidate, pending access and terms. IJmond is an optional industrial-plume supplement; its outdoor emissions domain is different from indoor factory fire safety.

No training run started and no application model changed. This search verified publisher descriptions and limited anonymous archive access; it did not audit image quality, all annotations, duplication or source grouping.

## 1. FASDD_CV — preferred broad detection pool

- Publisher dataset: https://doi.org/10.57760/sciencedb.j00104.00103
- Author paper: https://doi.org/10.1080/10095020.2024.2347922
- Publisher describes 95,314 CV images, with fire, smoke and confusing negative scenes across indoor/outdoor and day/night settings. Sensors across the full FASDD collection also include surveillance, UAV and satellites; select CV and inspect viewpoint relevance rather than importing aerial/satellite subsets.
- Labels: YOLO, VOC, COCO and TDML. Published splits are random; build our own camera/incident/scene isolation rather than assuming the provided split is an independent CCTV test.
- Publisher record lists CC BY-SA 4.0. The readily accessible seawsurf mirror lists CC BY 4.0; preserve the publisher's terms and resolve the discrepancy before product training/distribution. Do not treat a mirror as granting broader rights.
- Public mirror: https://huggingface.co/datasets/seawsurf/fire_smoke_dataset_fasdd_cv
- Verified anonymous HTTP Range 206 for its 3,410,626,268-byte ZIP and ZIP magic. No archive downloaded. Mirror file metadata saved separately. Publisher and mirror counts may differ; count and inspect actual labels before claiming an accepted training size.

## 2. LFDN — useful hard-negative candidate

- Publisher: https://mivia.unisa.it/large-fire-dataset-with-negative-samples-lfdn/
- Publisher description: 36,554 images: 8,070 flame-only, 15,330 smoke-only, 9,000 both, 4,154 negatives. Box annotations for flame/smoke.
- Explicit difficult negatives include sunlight, clouds, fog, reflections, glare, headlights, dust, clothing and flags. This targets important false-alarm categories in our project; relevance of actual indoor factory samples remains to be inspected.
- Download goes through https://mivia.unisa.it/datasets-request/ . That request endpoint timed out in this check. Immediate archive access and a commercial training grant were not established. No form submitted or author contacted.

## 3. IJmond Industrial Smoke Segmentation — optional industrial supplement

- Publisher dataset: https://doi.org/10.21942/uva.31847188
- Author report: https://arxiv.org/html/2603.23754v1
- 900 original images / 1,209 smoke polygons; 2,074 derived crops, 1,109 containing smoke. Derived crops are not independent scenes.
- Three stationary cameras monitor industrial emissions. Authors refined segmentation polygons and checked masks. The report distinguishes low/high opacity masks.
- CC BY 4.0 in both the author report and Figshare metadata. Direct publisher API access succeeded without an account, with a public 266,159,976-byte archive; a range request returned HTTP 206 and gzip magic. Full archive not downloaded.
- Polygons/masks need conversion and visual checking for our bounding-box detector. Preserve original-image/camera groups across splits. Outdoor process-emission smoke is not automatically a positive example of indoor combustion hazard; define taxonomy before use.

## Previously considered / less suitable as the primary answer

- D-Fire: https://github.com/gaia-solutions-on-demand/DFireDataset — 21,527 images and YOLO boxes, including 9,838 negatives. Already investigated locally. Its current publisher README explicitly says third-party images remain under original-provider terms. Camera/incident grouping and overlap with our existing evaluation footage remain unresolved; do not blindly mix it with FASDD or label the collection universally cleared for commercial use.
- SmokeBench (Jin et al., 2025): https://github.com/QianfengY/SmokeBench — paired clean/smoky surveillance images for desmoking, rather than ready fire/smoke detection boxes. Could support a future relabeling effort, but not the first detection training set.
- Synthetic CCTV samples: not a replacement for real-camera validation or a primary cure for current factory-floor false positives.
- RISE industrial emissions and IPAD factory-process footage were examined earlier. Emission time-lapses and generic factory anomalies should not be silently treated as fire-safety smoke labels or empty-label negatives.

## Concrete first experiment

1. Download and visually audit a small FASDD_CV subset, its class mapping and negatives before selecting a few thousand diverse images for a bounded Mac pilot. Actual selection size follows the quality audit, not a promise from publisher totals.
2. Add manually checked industrial negatives (walls, factory floors, glare, steam/dust where distinguishable). Keep uncertain process aerosol out of empty-label negative training.
3. Preserve faint/backlit smoke positives and both smoke/fire classes. Existing comparison clips and their neighboring camera scenes remain evaluation-only.
4. Deduplicate across datasets and record scene/incident groups before splitting. Where source IDs are absent, establish conservative scene groups and document unresolved overlap.
5. Compare the trained candidate with the pinned baseline at the same source-frame sampling and operating policy. Measure missed events as well as false alarms; fewer detections alone is not a successful model.

Access evidence: `access-checks.json`, `fasdd-mirror-files.json`, `ijmond-metadata.json`.
