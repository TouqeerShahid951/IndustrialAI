# Industrial Safety AI — local upload-and-review MVP

The Mac MVP provides authenticated CCTV upload, full-video analysis, source-timestamp playback, incident review and evidence export. Its five capabilities are fire, smoke, suspected smoking behavior, explicit no-helmet evidence and restricted-area intrusion. The frontend follows the selected Soft Graphite and Sage mockups.

## Run on this Mac

The configured workspace already has dependencies and verified model weights. Start the API and single worker together:

```bash
./scripts/start_mvp.sh
```

Open **http://127.0.0.1:8008**. On first run, the generated operator password is stored privately at `var/mvp/operator-password.txt`; it is never logged. To change it, stop the application, run `.venv/bin/python -m backend.manage password`, then restart. Sessions expire after 12 hours; signing out revokes existing sessions. Runtime uploads, database, model files and exports remain in ignored `var/mvp/`.

For remote access, forward the loopback port from your own computer (replace `user@mac` with your Mac SSH address):

```bash
ssh -N -L 8008:127.0.0.1:8008 user@mac
```

Then open the same localhost URL on that computer. The startup script binds locally; there is no public deployment.

Fresh environment setup:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-mvp.txt
npm --prefix frontend ci
.venv/bin/python -m backend.manage models
npm --prefix frontend run generate:api
npm --prefix frontend run build
./scripts/start_mvp.sh
```

`models` explicitly retrieves pinned publisher checkpoints; runtime verifies hashes and class names. macOS `/usr/bin/avconvert` prepares browser-compatible previews. MPS is selected explicitly in analysis configuration; choose CPU if required. There is no automatic CPU/model substitution.

## Workflow and limits

Upload a video, wait for preview preparation, select detections and draw a restricted polygon if intrusion is enabled. Start analysis, inspect machine candidates in the review workspace and save a confirmed, false-alarm or uncertain decision. Add missed observations manually. Incident history retains the append-only review trail. Export JSON details, CSV summaries or a selected MP4 clip with a separate source-frame manifest.

Uploads are limited to 250 MiB, five minutes, 1920×1080 and nominal 60 FPS. Workspace quota is 4 GiB with a 3 GiB free-disk guard. Models process every admitted source frame sequentially in one separate worker, keeping the API responsive. A stopped worker marks running jobs interrupted on restart; retry explicitly creates a new job. Delete is blocked until active jobs stop and removes the upload's associated files and reviews permanently.

These are development detectors and provisional temporal rules. A machine candidate is not a confirmed incident; no candidates does not establish safety. Smoking requires cigarette evidence and a same-person hand-to-face cycle, with ambiguity/visibility intervals recorded. No-helmet requires explicit associated evidence; intrusion depends on the configured zone and visible tracks. Preview time maps to original source time. The frame fallback uses available stills, approximately one per second. MP4 evidence exports omit audio.

## Verification

```bash
.venv/bin/python -m unittest discover -s tests -v
npm --prefix frontend test -- --run
npm --prefix frontend run typecheck
npm --prefix frontend run build
# With the application running and its initial local credential file available:
npm --prefix frontend run test:e2e
```

The last command exercises the real API, worker and all four pinned models with a disposable local fixture; it does not measure detection accuracy. Browser interaction checks and selected real development clips are documented in [implementation results](reports/mvp-implementation-2026-10-21/results.md). [Visual verification](design-qa.md) records the source mockup comparison. Safari/WebKit and a remotely connected client still require independent testing. A labeled, representative holdout set is required before deployment decisions.

The original CLI evaluation workflow below remains available.

---

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
