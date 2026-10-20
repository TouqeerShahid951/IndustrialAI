"""Class-aware event scoring; predictions are event records, not raw frame boxes."""
import json
import statistics
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.benchmark_data import KINDS, number


def union_intervals(intervals, gap=0):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + gap:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return merged


def subtract_intervals(intervals, exclusions):
    remaining = union_intervals(intervals)
    for a, b in union_intervals(exclusions):
        pieces = []
        for start, end in remaining:
            if b <= start or a >= end:
                pieces.append([start, end])
            else:
                if start < a:
                    pieces.append([start, a])
                if b < end:
                    pieces.append([b, end])
        remaining = pieces
    return remaining


def seconds(intervals):
    return sum(b-a for a,b in union_intervals(intervals))


def percentiles(values):
    if not values:
        return {'p50': None, 'p95': None}
    if len(values) == 1:
        return {'p50': values[0], 'p95': values[0]}
    quantiles = statistics.quantiles(values, n=100, method='inclusive')
    return {'p50': quantiles[49], 'p95': quantiles[94]}


def _validate_event(event):
    if not isinstance(event, dict) or not isinstance(event.get('clip_id'), str) or not event['clip_id']:
        raise ValueError('event clip_id required')
    if event.get('kind') not in KINDS:
        raise ValueError('event must use a canonical capability, not an object candidate')
    start, end = event.get('start_seconds'), event.get('end_seconds')
    if not number(start) or not number(end) or not 0 <= start < end:
        raise ValueError('invalid event interval')
    if event.get('review_status', 'reviewed') not in ('reviewed', 'ambiguous'):
        raise ValueError('invalid event review_status')


def merge_candidates(events, gap_seconds=2):
    if not number(gap_seconds) or gap_seconds < 0:
        raise ValueError('invalid merge gap')
    groups = {}
    for event in events:
        _validate_event(event)
        groups.setdefault((event['clip_id'], event['kind']), []).append([event['start_seconds'], event['end_seconds']])
    return [dict(clip_id=clip, kind=kind, start_seconds=a, end_seconds=b)
            for (clip, kind), intervals in sorted(groups.items())
            for a, b in union_intervals(intervals, gap_seconds)]


def score_events(expected, predicted, negative_seconds, *, excluded_intervals=None):
    """negative_seconds is reviewed, monitored negative exposure after exclusions.

    All unmatched observable event records count as FP, including duplicate alerts.
    The rate is FP divided by the supplied negative camera-hours, not a confidence score.
    """
    if not number(negative_seconds) or negative_seconds < 0:
        raise ValueError('negative_seconds must be finite and nonnegative')
    for event in [*expected, *predicted]:
        _validate_event(event)
    excluded = list(excluded_intervals or [])
    for event in expected:
        if event.get('review_status') == 'ambiguous':
            excluded.append(dict(event, reason='ambiguous'))
    for item in excluded:
        if not isinstance(item, dict) or not isinstance(item.get('clip_id'), str) or item.get('reason') not in ('ambiguous','unmonitored'):
            raise ValueError('invalid excluded interval')
        a, b = item.get('start_seconds'), item.get('end_seconds')
        if not number(a) or not number(b) or not 0 <= a < b:
            raise ValueError('invalid excluded interval time')
        if item.get('kind') is not None and item['kind'] not in KINDS:
            raise ValueError('invalid excluded capability')

    def observable(event):
        exclusions = [[x['start_seconds'],x['end_seconds']] for x in excluded
                      if x['clip_id']==event['clip_id'] and x.get('kind',event['kind'])==event['kind']]
        return subtract_intervals([[event['start_seconds'],event['end_seconds']]], exclusions)

    reviewed = [(event, observable(event)) for event in expected if event.get('review_status','reviewed')=='reviewed']
    reviewed = [(event, pieces) for event, pieces in reviewed if pieces]
    matched, delays, fp, skipped = set(), [], 0, 0
    for prediction in sorted(predicted, key=lambda e:e['start_seconds']):
        pieces = observable(prediction)
        if not pieces:
            skipped += 1
            continue
        eligible = [(event['start_seconds'], index) for index,(event,truth) in enumerate(reviewed)
                    if index not in matched and event['clip_id']==prediction['clip_id'] and event['kind']==prediction['kind']
                    and any(max(a,c)<min(b,d) for a,b in pieces for c,d in truth)]
        if eligible:
            _, index = min(eligible)
            matched.add(index)
            delays.append(max(0, pieces[0][0] - reviewed[index][1][0][0]))
        else:
            fp += 1
    def excluded_time(reason=None):
        return sum(seconds([[x['start_seconds'],x['end_seconds']] for x in excluded
                            if x['clip_id']==clip and (reason is None or x['reason']==reason)])
                   for clip in {x['clip_id'] for x in excluded})
    tp = len(matched)
    return dict(TP=tp, FP=fp, FN=len(reviewed)-tp, event_recall=tp/len(reviewed) if reviewed else None,
                event_precision=tp/(tp+fp) if tp+fp else None,
                negative_seconds=negative_seconds,
                false_events_per_camera_hour=fp*3600/negative_seconds if negative_seconds else None,
                confirmation_delays_seconds=delays, confirmation_delay_seconds=percentiles(delays),
                excluded_predictions=skipped, excluded_seconds=excluded_time(),
                ambiguous_seconds=excluded_time('ambiguous'), unmonitored_seconds=excluded_time('unmonitored'))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/benchmark_events.py scoring-input.json')
    data = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(score_events(**data), indent=2, allow_nan=False))
