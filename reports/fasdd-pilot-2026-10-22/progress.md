# FASDD smoke fine-tuning pilot — execution ledger

Authorized: download and inspect FASDD_CV, curate source-separated fire/smoke training data, run a bounded local candidate experiment when checks pass, and compare with the existing model. Preserve the app's pinned default and all user reviews.

1. Download pinned archive and verify publisher-mirror SHA-256.
2. Inspect file structure, label mapping, representative images, negative quality and split/duplicate risks.
3. Prepare a bounded balanced subset with conservative scene grouping, evaluation exclusions and checked annotations.
4. Run Mac/MPS fine-tuning in a separate output directory; record config/model/data identities.
5. Compare with baseline on held-out data and existing reserved footage, including false-positive and faint-smoke cases. Report regressions without automatic promotion.

Ruling: reuse the existing non-main development checkout — this work concerns local data and a separate training artifact; a second large checkout is unnecessary and would consume constrained disk space.
Ruling: publisher FASDD terms (CC BY-SA 4.0) override the mirror's more permissive card for this experiment. Local experimental training is authorized; redistribution/deployment of resulting weights is outside this run.
Ruling: the current 0.25 baseline remains pinned in the app. A candidate only becomes a separate experimental artifact.

Final status: download, curation, training and evaluation complete. Candidate rejected; the application's pinned baseline is retained.

Download verified: archive SHA-256 c7d34d3511fd3a4bd16fdf5412e974d3e31b8f1b400bc566d1f115a807f36152, 3,410,626,268 bytes, 95,126 images. Mirror data.yaml names fire=0/smoke=1; remapped to the current model's smoke=0/fire=1.

Data audit: inspected representative archive samples, then all 600 pool candidates and every accepted positive with its boxes. Rejected graphics, irrelevant scenes, uncertain labels and known controlled-lab/test-source families. Recorded a negative containing burning coals and fire-labeled road images with no visible flame. Perceptual screening sampled 2,049 frames at approximately 2 Hz from 36 reserved sources and conservatively excluded matching candidate scene groups. Final pool: 176 training / 48 internal validation images across 89 conservative groups.

Ruling: cap the first pilot at 224 accepted images — the broad collection contains far more forest, stock and ambiguous material than useful checked CCTV scenes. This is a data/overfit sanity experiment before scaling, not the proposed full multi-thousand-image training set.
Ruling: original camera and incident IDs are absent. Use conservative filename blocks merged by perceptual similarity and manual scene families, and label validation as INTERNAL DEVELOPMENT ONLY. This does not establish full source isolation or production readiness. Reserved test footage remains outside training/optimizer validation; unknown web-source overlap remains a limitation.

Training: ten epochs on MPS, fixed seed 42, batch four, size 640, AdamW lr=0.0001; app default unchanged. Candidate promotion prohibited by this experiment's scope.

Evaluation complete: candidate inference on 34 sources / 17,556 frames, plus fresh comparison scoring against the existing baseline. Internal image mAP50 declined from 0.5094 to 0.4633. House-video smoke hits fell from 283 to zero in the clear-looking first 35 seconds, but also from 1,647 to 750 in the established-smoke 65–125-second window. Human-reviewed clip-007 loses its raw smoke detection; W04 retains its smoke false alarm and gains a temporally verified fire false alarm. Candidate rejected without any model/threshold/review changes.

Fresh read-only reviewer: no material findings; verified all 224 archive/image/label identities and remapping, 176/48 split counts, group separation, minimum cross-split pHash distance 16, curation replay and model hashes. Camera independence remains explicitly unproven. Final evidence and next data requirements are recorded in report.md. No further training or deployment is part of this pilot.
