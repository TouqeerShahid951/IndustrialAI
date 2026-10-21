"""Bounded local media admission and frame-preserving browser previews."""
import bisect
import hashlib
import math
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4
import cv2
from fastapi import HTTPException

MAX_BYTES = 250*1024**2
QUOTA = 4*1024**3
MIN_FREE = 3*1024**3


class Cancelled(Exception):
    pass


def capacity(root, reserve=0):
    used = sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())
    if used+reserve > QUOTA or shutil.disk_usage(root).free-reserve < MIN_FREE:
        raise OSError('Storage limit reached. Remove unused uploads or free disk space.')
    return used


def probe(path):
    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        width, height = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if not cap.isOpened() or not all(math.isfinite(x) and x > 0 for x in (fps,width,height,count)):
            raise ValueError('Cannot decode this video. Try an MP4, MOV, AVI or MKV file.')
        if fps > 60.01 or width > 1920 or height > 1080 or count/fps > 300.1:
            raise ValueError('Video exceeds the limit: five minutes, 1920×1080, 60 FPS.')
        ok, _ = cap.read()
        if not ok:
            raise ValueError('The video contains no decodable frames.')
        return {'fps': fps, 'width': int(width), 'height': int(height), 'frames': int(count), 'duration': count/fps}
    finally:
        cap.release()


async def admit_upload(store, stream, display_name):
    directory = store.root/'media'
    directory.mkdir(exist_ok=True)
    name = Path(unquote(display_name).replace('\\','/')).name[:160]
    suffix = Path(name).suffix.lower()
    if suffix not in ('.mp4','.mov','.avi','.mkv') or not name or any(ord(c)<32 for c in name):
        raise HTTPException(422, 'Choose an MP4, MOV, AVI or MKV video.')
    path = directory/(str(uuid4())+suffix)
    temporary = path.with_suffix('.part')
    digest, total = hashlib.sha256(), 0
    try:
        capacity(store.root)
        with temporary.open('xb') as handle:
            async for chunk in stream:
                total += len(chunk)
                if total > MAX_BYTES:
                    raise HTTPException(413, 'Video exceeds the 250 MiB upload limit.')
                capacity(store.root, len(chunk))
                digest.update(chunk)
                handle.write(chunk)
        temporary.rename(path)
        metadata = probe(path)
        upload = store.add_upload(name, str(path.relative_to(store.root)), digest.hexdigest(), total, metadata)
        job = store.create_job(upload['id'], 'prepare_upload', {}, str(uuid4()))
        return {'upload_id': upload['id'], 'preparation_job_id': job['id']}
    except BaseException as exc:
        temporary.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
        if isinstance(exc, ValueError):
            raise HTTPException(422, str(exc)) from exc
        if isinstance(exc, OSError):
            raise HTTPException(507, 'Insufficient local storage. Free space and try again.') from exc
        raise


def source_to_preview(seconds, frame_map):
    if not frame_map:
        return 0.0
    i = bisect.bisect_right([p[0] for p in frame_map], seconds)-1
    if i < 0:
        return frame_map[0][1]
    if i >= len(frame_map)-1:
        return frame_map[-1][1]
    a,b = frame_map[i],frame_map[i+1]
    return a[1]+(seconds-a[0])/(b[0]-a[0])*(b[1]-a[1])


def convert(source, target, should_cancel, root):
    log = target.with_suffix('.conversion.log')
    try:
        with log.open('wb') as output:
            process = subprocess.Popen(['/usr/bin/avconvert','--source',str(source),'--output',str(target),
                                        '--preset','PresetHighestQuality','--replace'], stdout=output, stderr=output)
            started = time.monotonic()
            try:
                while process.poll() is None:
                    if should_cancel():
                        raise Cancelled()
                    capacity(root)
                    if time.monotonic()-started > 600:
                        raise RuntimeError('Preview conversion timed out. Try a shorter clip.')
                    time.sleep(.15)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        if process.returncode or not target.is_file():
            raise RuntimeError('Native H.264 conversion failed. Try exporting the source as MP4.')
    finally:
        log.unlink(missing_ok=True)


def prepare_preview(store, upload, progress, should_cancel):
    source = store.root/upload['path']
    metadata = probe(source)
    parent = store.root/'previews'
    parent.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=upload['id']+'-',dir=parent))
    intermediate, preview = directory/'intermediate.mp4',directory/'preview.mp4'
    cap = cv2.VideoCapture(str(source))
    writer = cv2.VideoWriter(str(intermediate), cv2.VideoWriter_fourcc(*'mp4v'),metadata['fps'],(metadata['width'],metadata['height']))
    mapping, frames = [], []
    try:
        if not writer.isOpened():
            raise RuntimeError('Video writer is unavailable.')
        while True:
            if should_cancel():
                raise Cancelled()
            ok, image = cap.read()
            if not ok:
                break
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            i = len(mapping)
            if not math.isfinite(timestamp) or timestamp < 0 or (mapping and timestamp <= mapping[-1][0]):
                raise ValueError('Video timestamps are missing or non-monotonic. Re-export this clip with valid timestamps.')
            if image.shape[1]>1920 or image.shape[0]>1080 or timestamp>300 or i>=18001:
                raise ValueError('Decoded video exceeds the supported limits.')
            mapping.append([timestamp,i/metadata['fps']])
            writer.write(image)
            if i % max(1,round(metadata['fps'])) == 0:
                thumb = directory/f'frame-{i}.jpg'
                scale = min(1,640/image.shape[1])
                if not cv2.imwrite(str(thumb),cv2.resize(image,(round(image.shape[1]*scale),round(image.shape[0]*scale)))):
                    raise OSError('Could not write a preview frame')
                frames.append((timestamp,thumb))
            if i%30==0:
                capacity(store.root)
                progress('Preparing frames',i+1,metadata['frames'])
        cap.release()
        writer.release()
        if len(mapping)!=metadata['frames']:
            raise ValueError('Decoded frame count does not match the container. Re-export this video.')
        progress('Converting browser preview',len(mapping),len(mapping))
        convert(intermediate,preview,should_cancel,store.root)
        check = cv2.VideoCapture(str(preview))
        converted_times=[]
        try:
            while True:
                ok,_=check.read()
                if not ok:
                    break
                converted_times.append(check.get(cv2.CAP_PROP_POS_MSEC)/1000)
        finally:
            check.release()
        if len(converted_times)!=len(mapping) or any(b<=a for a,b in zip(converted_times,converted_times[1:])):
            raise ValueError('Conversion changed the frame sequence. Preview alignment could not be verified.')
        mapping = [[source_time,converted] for (source_time,_),converted in zip(mapping,converted_times)]
        intermediate.unlink()
        capacity(store.root)
        result={**metadata,'frame_map':mapping,'preview_id':store.add_artifact(upload['id'],'preview',preview,'video/mp4','preview.mp4'),
                'frames_preview':[{'source':t,'artifact_id':store.add_artifact(upload['id'],'frame',p,'image/jpeg',p.name)} for t,p in frames]}
        result['thumbnail_id']=result['frames_preview'][0]['artifact_id']
        store.update_upload(upload['id'],'ready',result)
        return result
    except BaseException:
        cap.release()
        writer.release()
        shutil.rmtree(directory,ignore_errors=True)
        raise
