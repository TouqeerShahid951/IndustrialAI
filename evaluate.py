"""Offline pretrained-detector comparison; no camera or cloud service required."""
import argparse
import csv
import json
import math
import hashlib
from importlib.metadata import version
import tempfile
from pathlib import Path
from time import perf_counter

MODELS = {
    "fire_smoke": "rabahdev/fire-smoke-yolov8n",
    "helmet": "keremberke/yolov8n-hard-hat-detection",
    "cigarette": "Enos-123/smoking-detection",
}
IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEOS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def media_files(source):
    path = Path(source)
    if not path.exists():
        raise ValueError(f"Source does not exist: {path}")
    files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    files = [p for p in files if p.suffix.lower() in IMAGES | VIDEOS]
    if not files:
        raise ValueError("No supported images or videos found")
    return files


def _sha256(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def evaluate(source, output="outputs", models=None, device="cpu", conf=0.25,
             stride=1, max_frames=300, imgsz=640, checkpoint=None, timestamp_source="container"):
    if not 0 < conf <= 1 or min(stride, max_frames, imgsz) < 1:
        raise ValueError("Confidence must be in (0, 1]; stride, frame limit and size must be positive")
    if timestamp_source not in ("container", "nominal"):
        raise ValueError("timestamp_source must be container or nominal")
    selected = list(MODELS) if models is None else models
    if not selected or any(name not in MODELS for name in selected):
        raise ValueError(f"Choose models from {list(MODELS)}")
    if checkpoint is not None and (len(selected) != 1 or not Path(checkpoint).is_file()):
        raise ValueError("A local checkpoint requires exactly one model and an existing file")
    files = media_files(source)
    import cv2
    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO

    # ponytail: sequential models bound GPU memory; batch only if benchmarks justify it.
    run = Path(output)
    run.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="run-", dir=run))
    summaries = []
    script = Path(__file__).resolve() if '__file__' in globals() else None
    metadata = dict(status='running', configuration=dict(device=device, confidence=conf, imgsz=imgsz,
                    stride=stride, max_frames=max_frames, timestamp_source=timestamp_source),
                    source_hashes={str(p.resolve()):_sha256(p) for p in files}, checkpoints={},
                    code_hashes={str(script):_sha256(script)} if script else {},
                    versions={name:version(name) for name in ('ultralytics','torch','opencv-python')})
    metadata_path = run / 'metadata.json'
    metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False))
    with (run / "detections.csv").open("w", newline="") as log, (run / 'frames.csv').open('w', newline='') as frame_log:
        writer = csv.writer(log)
        writer.writerow(["source", "model", "frame", "source_seconds", "class", "confidence", "x1", "y1", "x2", "y2"])
        frame_writer = csv.writer(frame_log)
        frame_writer.writerow(['source','model','frame','source_seconds','predict_seconds','status','timestamp_basis'])
        for name in selected:
            weights = checkpoint or hf_hub_download(MODELS[name], filename="best.pt")
            metadata['checkpoints'][name] = dict(path=str(Path(weights).resolve()), sha256=_sha256(weights))
            metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False))
            try:
                model = YOLO(weights)
            except Exception as exc:
                raise RuntimeError(f"Cannot load {name}; checkpoint compatibility must be checked. No substitute model was used.") from exc
            for index, path in enumerate(files):
                is_image = path.suffix.lower() in IMAGES
                cap = None if is_image else cv2.VideoCapture(str(path))
                video = None
                count = detections = 0
                predict_seconds = 0.0
                started = perf_counter()
                fps = 0.0 if is_image else cap.get(cv2.CAP_PROP_FPS)
                if not is_image and (not cap.isOpened() or not math.isfinite(fps) or fps <= 0):
                    cap.release()
                    raise ValueError(f"Unreadable video or invalid FPS: {path}")
                dest = run / name
                dest.mkdir(exist_ok=True)
                try:
                    frame_index = 0
                    previous_timestamp = None
                    while count < max_frames:
                        if is_image:
                            frame = cv2.imread(str(path))
                            ok = frame is not None
                        else:
                            ok, frame = cap.read()
                        if not ok:
                            if count == 0:
                                raise ValueError(f"Cannot decode media: {path}")
                            break
                        if frame_index % stride == 0:
                            timestamp = 0.0 if is_image else (cap.get(cv2.CAP_PROP_POS_MSEC)/1000 if timestamp_source=='container' else frame_index/fps)
                            if not math.isfinite(timestamp) or timestamp < 0 or (previous_timestamp is not None and timestamp <= previous_timestamp):
                                raise ValueError('Invalid source timestamps; inspect video or explicitly select nominal timestamps')
                            previous_timestamp = timestamp
                            tick = perf_counter()
                            result = model.predict(frame, device=device, conf=conf, imgsz=imgsz, verbose=False)[0]
                            boxes = result.boxes.cpu()  # synchronizes device before timing ends
                            latency = perf_counter() - tick
                            predict_seconds += latency
                            frame_writer.writerow([str(path), name, frame_index, timestamp, latency, 'ok', 'image' if is_image else timestamp_source])
                            for box in boxes:
                                writer.writerow([str(path), name, frame_index,
                                                 timestamp,
                                                 result.names[int(box.cls.item())], float(box.conf.item()),
                                                 *box.xyxy[0].tolist()])
                                detections += 1
                            annotated = result.plot()
                            if is_image:
                                if not cv2.imwrite(str(dest / f"{index}-{path.stem}.jpg"), annotated):
                                    raise OSError("Could not write annotated image")
                            else:
                                if video is None:
                                    h, w = frame.shape[:2]
                                    video = cv2.VideoWriter(str(dest / f"{index}-{path.stem}.mp4"),
                                                            cv2.VideoWriter_fourcc(*"mp4v"), fps / stride, (w, h))
                                    if not video.isOpened():
                                        raise OSError("MP4 writer unavailable")
                                video.write(annotated)
                            count += 1
                        frame_index += 1
                        if is_image:
                            break
                finally:
                    if cap is not None:
                        cap.release()
                    if video is not None:
                        video.release()
                elapsed = perf_counter() - started
                summaries.append(dict(source=str(path), model=name, repository=MODELS[name],
                                      checkpoint=str(weights), device=device, frames=count, detections=detections,
                                      inference_fps=count / predict_seconds if predict_seconds else 0,
                                      pipeline_fps=count / elapsed if elapsed else 0,
                                      elapsed_seconds=elapsed, stride=stride, confidence=conf, source_fps=fps, timestamp_source=timestamp_source))
                (run / "summary.json").write_text(json.dumps(summaries, indent=2))
                print(f"{name}: {path.name}: {count} frames, {detections} detections")
    metadata['artifacts'] = {name:_sha256(run/name) for name in ('detections.csv','frames.csv','summary.json')}
    metadata['status'] = 'complete'
    metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False))
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Image, video, or directory (local files only)")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--device", default="cpu", help="cpu, mps, or CUDA device 0")
    parser.add_argument("--checkpoint", help="Local weights; requires exactly one --models choice")
    parser.add_argument("--timestamp-source", choices=("container", "nominal"), default="container")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--max-frames", type=int, default=300)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    try:
        print(f"Results: {evaluate(**vars(args))}")
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f"Evaluation failed: {exc}\n")


if __name__ == "__main__":
    main()
