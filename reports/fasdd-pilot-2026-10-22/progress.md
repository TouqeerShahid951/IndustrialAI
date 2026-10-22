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

Current: archive download in progress. No training started.
