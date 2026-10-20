# Local benchmark

The first improvement milestone is implemented: source/label validation, reproducible event scoring and elapsed-time confirmation. The current two clips are **development examples only**. There is no validation or locked test set, independent label review, or accepted operating policy.

## Run

From the project directory:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/benchmark_data.py benchmark/manifest.jsonl
.venv/bin/python scripts/run_benchmark.py benchmark/manifest.jsonl \
  --runs-json reports/benchmark-baseline-runs.json \
  --output reports/benchmark-baseline.json
```

The saved baseline uses four full-video replays of the original fire/smoke and helmet checkpoints on Apple MPS. Run directories are local artifacts; the benchmark rechecks their logs, checkpoint hashes and source identity. To produce a fresh inference run:

```bash
.venv/bin/python evaluate.py data/cctv/helmet.mp4 --models fire_smoke helmet \
  --device mps --stride 1 --max-frames 2000
```

Pass fresh directories with `--runs PATH ...`, or save them as a JSON list for `--runs-json`. Supply at most one run per source/model. Runs made before `frames.csv` and `metadata.json` were introduced need replaying for this benchmark. Standalone notebook runs without code provenance remain exploratory.

## Data contract

`manifest.jsonl` contains one object per clip:

| Field | Meaning |
|---|---|
| `clip_id` | Stable clip identifier |
| `local_path`, `annotation_path` | Local paths relative to the manifest, or absolute paths |
| `source_sha256` | SHA-256 of the exact source bytes |
| `camera_id`, `site_id`, `source_event_id` | Groups that must stay within one split |
| `split` | `development`, `validation`, `locked_test` |
| `capture_origin` | `verified_cctv`, `research_capture`, `unverified_demo` |
| `permission_status` | `evaluation_allowed`, or development/research `review_needed` |
| `duration_seconds` | Positive finite source duration |
| `conditions` | List of condition tags, including `source_overlays` when applicable |

Duplicate clip IDs/source hashes and group leakage across splits are rejected. Group identities must be assigned correctly: hashes alone cannot recognize re-encoded footage. Locked test clips require verified capture, allowed evaluation, no source overlays and independently reviewed labels. Permission marked `review_needed` records an unresolved restriction; it does not grant permission.

Annotation JSON has:

- `review_status`: `single_reviewer`, `independent_reviewed`, or `unreviewed`. Unreviewed files cannot contain scored labels or reviewed time.
- `reviewed_intervals`: event kind → list of `[start_seconds, end_seconds]`. Only this time can contribute reviewed exposure. An empty list means no reviewed time.
- `events`: objects containing `kind`, `start_seconds`, `end_seconds`, and `review_status` (`reviewed` or `ambiguous`). Reviewed positives must lie inside reviewed time.
- Optional `excluded_intervals`: start/end, `reason` (`ambiguous` or `unmonitored`), and optional `kind`. Omit `kind` to apply to every capability; a specified kind applies only to that capability.
- Optional `frames`: `time_seconds`, `review_status`, `image_width`, `image_height`, and `objects` with `class` and `bbox_xyxy` in source-image pixels. Empty object lists are valid reviewed negative frames.

Canonical events: `fire`, `smoke`, `smoking`, `no_helmet`, `restricted_entry`. Canonical objects additionally include `helmet`, `person`, `cigarette`. Cigarette detections are retained as objects; the benchmark does not invent smoking behavior from them. No-helmet object scores are separate from event scores; four labeled frames do not establish continuous violation-event annotations.

When an independent test set exists, freeze its membership/source/annotation fingerprints once:

```bash
.venv/bin/python scripts/benchmark_data.py benchmark/manifest.jsonl --freeze-test benchmark/test-lock.json
.venv/bin/python scripts/benchmark_data.py benchmark/manifest.jsonl --check-lock benchmark/test-lock.json
.venv/bin/python scripts/run_benchmark.py benchmark/manifest.jsonl \
  --split locked_test --test-lock benchmark/test-lock.json --runs PATH ...
```

Lock creation refuses overwrite. Current development-only data cannot produce a test lock. Keep test footage closed during repeated policy tuning.

## Measurement contract

`evaluate.py` preserves raw boxes in `detections.csv`. `frames.csv` includes every analyzed frame, including successful empty detections, with source time, model latency and timestamp basis. `metadata.json` records configuration, source/checkpoint/code hashes, library versions and artifact hashes. A failed run never reaches `status=complete` and is rejected by the benchmark.

Container timestamps are the default. Invalid/non-increasing times fail explicitly; `--timestamp-source nominal` is an explicit fallback based on frame number/FPS and is identified in provenance. Container times can still be inaccurate if the original container metadata is wrong.

The report compares:

| Policy | Rule |
|---|---|
| `raw` | Immediate candidates |
| `legacy` | Three overlapping same-class hits in five analyzed frames |
| `fixed_2hz` | First observation in each source-time half-second bucket, then legacy voting |
| `timed` | At least three overlapping same-class observations in the last two seconds, spanning at least one second, including the current detection |

Spatial overlap is IoU ≥0.1. The timed rule is causal; invalid timestamps fail, empty frames add no evidence and stale observations expire. It is a spatial heuristic, not person identity tracking. Confirmation stays in derived report records; raw detections remain available immediately.

An observation covers time until the next analyzed observation when the gap is at most two seconds. Longer gaps and the last sample cover at most the nominal sampling cadence (capped at two seconds and clip end). A truncated run therefore cannot claim the unseen tail. This is sampled monitoring coverage, not a claim that every decoded frame was analyzed.

Per clip/capability, merge candidate intervals separated by at most two seconds before event scoring. Final events are distinct: earliest eligible same-kind overlap matches one reviewed event, and duplicate alerts count as unmatched false events. Ambiguous/unmonitored time is excluded, retaining any observable part of partially excluded events. Negative exposure is reviewed monitored time outside reviewed positive intervals.

`false_events_per_camera_hour` divides **all unmatched alerts, including repeat alerts during a positive incident**, by negative camera-hours. This matches the duplicate-alert scoring contract; it is not a calibrated negative-scene-only false-alarm estimate. In this tiny dataset the smoke denominator is just 15 seconds. Null means an undefined denominator, never a passing zero. Event delay begins at the first observable labeled evidence; an incident already present at clip start does not measure ignition-to-detection delay.

Outputs include per-capability/camera/condition counts, coverage/exclusions, event delays, p50/p95 prediction latency, and sampled head-object scores at IoU 0.5 and 0.3. Prediction latency includes box transfer and warmup; it excludes live capture, queuing, rendering and alert delivery. Conditions overlap, so their rows must not be added together as independent footage.

Report provenance includes manifest and annotation hashes, inference configuration/checkpoints, scoring/temporal code hashes and applied parameters. `policy.json` contains proposed discussion targets, not accepted thresholds. `gate_passed` remains false: no automatic promotion or production qualification is implemented.

## Remaining evidence

Collect authorized, clean, independent camera/site groups; label positives and confusing negatives; obtain second review and adequate continuous negative hours. The selected smoking video remains unavailable locally. Only then freeze validation policy/test membership and evaluate detector changes. See the [execution results](../reports/implementation-2026-10-20.md) and [plan ledger](../docs/superpowers/plans/2026-10-20-execution-log.md).
