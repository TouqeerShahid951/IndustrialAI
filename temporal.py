"""Causal spatial voting over sampled detections; empty frames must be included."""


def iou(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area = max(0, a[2] - a[0]) * max(0, a[3] - a[1]) + max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    return intersection / (area - intersection) if area > intersection else 0


def confirm(frames, hits=3, window=5, overlap=0.1):
    if not 1 <= hits <= window or not 0 < overlap <= 1:
        raise ValueError("Require 1 <= hits <= window and 0 < overlap <= 1")
    # ponytail: bounded window scanning; use tracking if crowded/moving scenes need identity.
    confirmed = []
    for index, boxes in enumerate(frames):
        history = frames[max(0, index - window + 1):index + 1]
        confirmed.append([box for box in boxes if sum(
            any(previous['class'] == box['class'] and iou(previous['bbox'], box['bbox']) >= overlap
                for previous in past) for past in history) >= hits])
    return confirmed


def confirm_timed(frames, timestamps, min_hits=3, min_span_seconds=1.0,
                  window_seconds=2.0, overlap=0.1):
    """Causal votes in elapsed seconds; backward/duplicate timestamps are invalid."""
    import math
    from bisect import bisect_left
    finite = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if (len(frames) != len(timestamps) or any(not finite(t) or t < 0 for t in timestamps)
            or any(b <= a for a,b in zip(timestamps,timestamps[1:]))):
        raise ValueError('Require one strictly increasing, finite source timestamp per frame')
    if (not isinstance(min_hits,int) or isinstance(min_hits,bool) or min_hits < 1
            or not all(finite(v) for v in (min_span_seconds,window_seconds,overlap))
            or not 0 <= min_span_seconds <= window_seconds or window_seconds <= 0 or not 0 < overlap <= 1):
        raise ValueError('Invalid timed confirmation settings')
    output = []
    for index, boxes in enumerate(frames):
        start = bisect_left(timestamps, timestamps[index] - window_seconds)
        current = []
        for box in boxes:
            hits = [timestamps[j] for j in range(start,index+1)
                    if any(old['class']==box['class'] and iou(old['bbox'],box['bbox'])>=overlap for old in frames[j])]
            if len(hits) >= min_hits and timestamps[index]-hits[0] >= min_span_seconds:
                current.append(box)
        output.append(current)
    return output
