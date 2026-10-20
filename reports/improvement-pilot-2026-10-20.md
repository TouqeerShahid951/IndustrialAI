# Labeled data, temporal verification and fine-tuning pilot — 2026-10-20

## Decision

Keep the original checkpoints as defaults. Causal temporal voting reduces noisy frames but does not remove persistent false events. The small fire fine-tune regressed. The helmet fine-tune plus higher input resolution improved four targeted head probes, but introduced a false head on a cable reel and missed a nearby helmet; it is not an overall accuracy improvement. All experiments ran locally on Apple M4/MPS.

## Labeled data created

- Fire/smoke: 20 training images (8 manually boxed positive frames from four additional source clips; 12 reviewed negatives from construction orange workwear and headlights). Fourteen validation images from different clips. Manual boxes are approximate single-reviewer annotations, not expert audited.
- Fire/smoke event test: 7 clips excluded from the new fine-tuning and validation: 2 positive, 5 negative. Includes a nighttime street, clouds/trees, reeds/wind, a second clouds clip and a white-plume negative. The white plume resembles steam visually, but its physical source is unverified; it is labeled non-smoke by FIRESENSE. This is not proof of performance on industrial steam.
- Helmet: 40 published training images, including 6 images with small uncovered heads; 10 validation images. Source: keremberke/hard-hat-detection, CC BY 4.0. The original model already used this dataset, so its validation split is not an independent benchmark.
- Helmet target test: four manually marked views of one bareheaded worker in one construction CCTV clip, excluded from helmet training/validation. IoU ≥ 0.3, confidence ≥ 0.25. Only the target is marked; other workers and false positives are not comprehensively labeled. These correlated probes are not an overall recall or precision estimate.
- Construction footage is a training negative for fire/smoke but a test clip for helmet. Task-specific splits are intentional. Pretraining overlap with public clips remains unknown.

Data: [clip labels](/Users/tabbasi/Downloads/IndustrialAI/data/labeled/clips.csv), [fire dataset](/Users/tabbasi/Downloads/IndustrialAI/data/labeled/fire_smoke), [helmet dataset](/Users/tabbasi/Downloads/IndustrialAI/data/labeled/helmet), [manual head boxes](/Users/tabbasi/Downloads/IndustrialAI/data/labeled/helmet/target-test-boxes.json).

## Temporal verification

Fixed before the comparison: current detection needs overlapping boxes of the same class (IoU ≥ 0.1) in 3 of the last 5 sampled frames. Empty frames count; no future frames are used. Spatial voting does not establish identity, fire growth or smoking behavior. It is an offline alert-candidate filter, not yet wired into a live CCTV service.

On the original model across seven negative clips: 49 raw false-detection frames became 31 confirmed frames (36.7% fewer). All three negative clips that triggered originally still triggered after filtering. Shortening a false alert is not eliminating it.

All four positive development/holdout clips retained at least one confirmed detection. First confirmation was 0.2–2.1 seconds after the first raw detection; this is additional sampled-video confirmation delay, not latency from true hazard onset or a live camera. Some real hazard frames were suppressed.

| Negative clip | Original raw frames | Original confirmed frames | Pilot raw frames | Pilot confirmed frames | Role |
|---|---:|---:|---:|---:|---|
| fire_neg_negsVideo2.859.avi | 10 | 8 | 13 | 11 | train |
| fire_neg_negsVideo3.860.avi | 0 | 0 | 0 | 0 | holdout |
| smoke_neg_testneg01.807.avi | 0 | 0 | 0 | 0 | holdout |
| smoke_neg_testneg05.811.avi | 0 | 0 | 5 | 0 | holdout |
| helmet.mp4 | 6 | 2 | 6 | 2 | train |
| clouds-negative.avi | 0 | 0 | 0 | 0 | holdout |
| white-plume-negative.mp4 | 33 | 21 | 48 | 45 | holdout |

![False-detection frame comparison](/Users/tabbasi/Downloads/IndustrialAI/reports/fire-pilot-comparison.png)

## Fine-tuning results

Both pilots: five epochs, AdamW lr=0.0005, frozen first 10 layers, batch=4, training size=640, seed=0. Inference confidence stayed at 0.25. Used final-epoch weights rather than selecting an epoch on the test clips. Configurations and training logs are retained. Apple MPS warned that some operations are nondeterministic, so the seed does not ensure bit-for-bit reproduction.

Fire: original model triggered on 1/5 held-out negative clips; pilot triggered on 2/5. With temporal voting both triggered on 1/5, but pilot white-plume false frames increased from 21 to 45. Both retained detections on 2/2 held-out positive clips, though the pilot had fewer raw smoke-positive frames (70 → 66). Training on a few coarse labels and negatives did not improve generalization. Reject this pilot.

| Helmet input size | Original target matches | Pilot target matches |
|---|---:|---:|
| 640 | 0/4 | 0/4 |
| 1280 | 1/4 | 3/4 |

At 9 seconds, the pilot recognizes the distant worker but also labels a cable reel NO-Hardhat and misses the right-side worker’s visible yellow helmet, while the original recognizes both nearby helmets. The four-target score therefore cannot establish an overall improvement. Higher-resolution tests are exploratory, not a pre-registered generalization result.

![Targeted comparison at 9 seconds](/Users/tabbasi/Downloads/IndustrialAI/reports/helmet-pilot-comparison.jpg)

![Full pilot frame showing false head on cable reel](/Users/tabbasi/Downloads/IndustrialAI/reports/helmet-tuned-1280-9s.jpg)

## Artifacts and reproduction

- [Original-versus-pilot metrics](/Users/tabbasi/Downloads/IndustrialAI/reports/fire-pilot-metrics.json)
- [Helmet target results](/Users/tabbasi/Downloads/IndustrialAI/reports/helmet-pilot-targets.json)
- [Fire pilot weights, experimental](/Users/tabbasi/Downloads/IndustrialAI/outputs/training/fire-pilot/weights/last.pt)
- [Helmet pilot weights, experimental](/Users/tabbasi/Downloads/IndustrialAI/runs/detect/outputs/training/helmet-pilot/weights/last.pt)
- [Fire training log](/Users/tabbasi/Downloads/IndustrialAI/outputs/fire-pilot-train.log)
- [Helmet training log](/Users/tabbasi/Downloads/IndustrialAI/outputs/helmet-pilot-train.log)
- [Fire tuned video outputs](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-06vbtmt1)
- [Helmet tuned 1280 video outputs](/Users/tabbasi/Downloads/IndustrialAI/outputs/run-k6kkdw9h)

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/compare_temporal.py outputs/run-lwd4y8qk outputs/run-1gteobj4
.venv/bin/python evaluate.py data/cctv/helmet.mp4 --models helmet --device mps --imgsz 1280 --stride 4 --checkpoint runs/detect/outputs/training/helmet-pilot/weights/last.pt
```

## What this establishes

Temporal verification is worth retaining as a candidate filter, but persistent headlights, clothing and white plumes need better visual discrimination. The helmet result justifies a larger task-specific dataset with both uncovered heads and confusing objects such as reels. These tiny runs do not justify switching model defaults or claiming production readiness.

## Sources

- [FIRESENSE, original research dataset](https://zenodo.org/records/836749), Grammalidis, Dimitropoulos and Cetin (2017). Additional source AVI testneg03 reports 748 frames but only 182 decode; the valid prefix was re-encoded, and that limitation is recorded in the data sources.
- [CosmoEdge construction CCTV sample](https://raw.githubusercontent.com/cosmo-wander-ai/cosmo-edge/v1.1.0/data/test-video/Safety%20Helmet.mp4).
- [Hard Hat dataset and publisher annotations](https://huggingface.co/datasets/keremberke/hard-hat-detection).
