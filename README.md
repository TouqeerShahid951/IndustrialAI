# Industrial Safety AI — model evaluation

First milestone from the [project conversation](https://chatgpt.com/share/6ad64fa3-2d70-83ee-ac73-196c3818ca55): evaluate pretrained fire/smoke, hard-hat and cigarette detectors on images and recorded CCTV before building the live monitoring platform.

## Start in Colab or Kaggle (recommended)

Upload `notebooks/industrial_safety_model_test.ipynb` to [Colab](https://colab.research.google.com/) or [Kaggle Code](https://www.kaggle.com/code). Select a GPU if available; Kaggle also needs internet enabled to install dependencies and download weights. Run the cells in order. The notebook includes its own runner; no repository upload is needed.

Set `SOURCE` to an attached video/image/directory, or use the Colab upload cell. Start with 10–20 second clips and `MODELS = ["fire_smoke"]`, then test helmet and cigarette separately. Finally select all three to compare costs. The notebook defaults to CPU when CUDA is unavailable; it never selects the Mac GPU automatically.

Results include annotated images/video, `detections.csv`, `frames.csv`, `metadata.json`, `summary.json`, and a downloadable ZIP. Each run uses a new directory. Videos contain sampled frames at adjusted playback FPS and no audio. `max_frames` limits analyzed frames per input per model; `stride` controls sampling. It does not limit the number of files in a directory—use a small sample folder.

## Local setup (optional inference)

Python 3.12 is recommended; Python 3.14 is not used for this environment.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
python evaluate.py --help
python -m unittest discover -s tests
python evaluate.py data/example.mp4 --models fire_smoke --device cpu --max-frames 60
```

If `uv` is unavailable, use Python 3.12's `python3.12 -m venv .venv` and `.venv/bin/python -m pip install -r requirements.txt`.

No inference runs until you explicitly invoke the script or notebook. Models download into Hugging Face's cache at first use. To use Apple acceleration explicitly, pass `--device mps`; CUDA uses `--device 0`.

## Models

| Name | Repository | Checkpoint |
|---|---|---|
| fire_smoke | [D-Fire YOLOv8n](https://huggingface.co/rabahdev/fire-smoke-yolov8n) | best.pt |
| helmet | [Hard Hat YOLOv8n](https://huggingface.co/keremberke/yolov8n-hard-hat-detection) | best.pt |
| cigarette | [Smoking detector](https://huggingface.co/Enos-123/smoking-detection) | best.pt |

The helmet publisher documents Ultralytics 8.0.23; this project uses modern Ultralytics for the newer cigarette model. All three checkpoints loaded and ran successfully on this Mac using MPS on 2026-10-20; other runtimes still need checking. A failure stops the experiment with an error; no motorcycle-helmet substitute is used. Do not downgrade the shared environment blindly. Only load trusted model checkpoints: `.pt` files may contain executable serialized objects.

## Sample datasets

- [D-Fire original dataset and surveillance video links](https://github.com/gaia-solutions-on-demand/DFireDataset)
- [D-Fire on Kaggle](https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo): optional notebook download cell; may be large.
- [Hard Hat Workers](https://public.roboflow.com/object-detection/hard-hat-workers/)
- [Smoking Detection V3](https://universe.roboflow.com/alt-f4-dom2z/smoking_detection_v3_noisefree)
- [HMDB51 action videos](https://serre.lab.brown.edu/hmdb51.html): smoking plus confusing actions such as eating and drinking.

Download a small subset into `data/` or attach it in Kaggle. Dataset access may require an account and acceptance of its terms. No datasets or weights are bundled. Check dataset licensing and training overlap before claiming independent accuracy.

## Interpret results

`inference_fps` measures prediction and copying boxes to CPU, including first-frame warmup. `pipeline_fps` includes decoding, annotation and writing, but excludes model download/load. Models run sequentially: these are per-model offline throughput figures, not combined live-camera FPS or end-to-end cloud latency. Detection confidence is not measured accuracy. Precision/recall requires ground-truth annotations and a separate evaluation.

Include fire vs bright lights, smoke vs steam, helmet vs uncovered heads, and cigarettes vs eating/phone use. Cigarette boxes alone do not establish smoking behavior. Empty CSV detections can be valid; summary frame counts distinguish them from unreadable media.

## MVP scope after evaluation

The planned platform includes fire, smoke, smoking behavior, no-helmet and restricted-area intrusion; local capture, cloud inference, temporal verification/person tracking, zone rules, FastAPI/WebSocket alerts, React incident history and evidence. These are future implementation milestones, not features of this evaluation runner. Cloud accounts and deployment are not created, and no footage is uploaded by the local runner.

Ultralytics and the D-Fire checkpoint have AGPL licensing considerations; review all upstream terms before commercial deployment. This experiment is supplementary visual research, not a certified fire alarm or production safety system.

## Verified Mac run (2026-10-20)

All three detectors ran on Apple MPS against three publisher example montages: nine model/image combinations, with CSV, summary JSON and nine annotated images saved to `outputs/run-crgq858k/`. Inputs and their source URLs are in `data/samples/`. These examples may contain existing labels and dataset overlap; they are an inference smoke test, not an accuracy benchmark. Fire/smoke also produced detections on the cigarette example, so outputs need review for false positives.

Repeat locally:

```bash
.venv/bin/python evaluate.py data/samples --device mps --max-frames 1
```

For useful performance and false-alarm testing, replace the sample folder with independent CCTV images or a video, and increase `--max-frames` for video.

## Improvement experiments

See [labeled-data, temporal and fine-tuning pilot](reports/improvement-pilot-2026-10-20.md). The default checkpoints are unchanged; both five-epoch pilots remain experimental. `temporal.confirm()` provides causal spatial voting over sampled frames (including empty frames). `scripts/compare_temporal.py` compares saved detection logs. Local candidate weights can be evaluated using `--checkpoint PATH` with exactly one model selected.


## Implemented improvement milestone (Mac)

Phases 1–2 now provide manifest/annotation validation, event scoring with coverage accounting, and timestamp-based temporal confirmation. Raw detections remain intact. Original checkpoints were replayed on both registered development videos using Apple MPS.

```bash
.venv/bin/python scripts/benchmark_data.py benchmark/manifest.jsonl
.venv/bin/python scripts/run_benchmark.py benchmark/manifest.jsonl \
  --runs-json reports/benchmark-baseline-runs.json --output reports/benchmark-baseline.json
.venv/bin/python -m unittest discover -s tests -v
```

See [benchmark usage and data format](benchmark/README.md) and [implementation results](reports/implementation-2026-10-20.md). New CLI runs preserve container timestamps by default; select `--timestamp-source nominal` explicitly only when that fallback is appropriate. Existing historical logs remain exploratory until replayed with per-frame observations and provenance.

The timed filter suppresses this development sample's brief false fire alert, but repeat smoke alerts and distant uncovered-head misses remain. The current dataset does not qualify any production gate; independent recordings, reviewed labels and accepted operating targets are still needed before the later model/live-camera phases.
