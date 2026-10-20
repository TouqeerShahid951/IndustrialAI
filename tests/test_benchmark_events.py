import unittest
from scripts.benchmark_events import score_events, merge_candidates, subtract_intervals


def event(start=10, end=20, kind='smoke', clip='one', **extra):
    return dict(clip_id=clip, kind=kind, start_seconds=start, end_seconds=end, **extra)


class EventScoringChecks(unittest.TestCase):
    def test_matches_delay_duplicates_and_wrong_class(self):
        expected = [event()]
        metrics = score_events(expected, [event(12,18)], 3600)
        self.assertEqual((metrics['TP'],metrics['FP'],metrics['FN']), (1,0,0))
        self.assertEqual(metrics['confirmation_delays_seconds'], [2])
        self.assertEqual(metrics['event_recall'], 1)
        metrics = score_events(expected, [event(12,14),event(16,18)], 3600)
        self.assertEqual((metrics['TP'],metrics['FP'],metrics['FN']), (1,1,0))
        metrics = score_events(expected, [event(12,18,kind='fire')], 3600)
        self.assertEqual((metrics['TP'],metrics['FP'],metrics['FN']), (0,1,1))
        self.assertEqual(metrics['false_events_per_camera_hour'], 1)

    def test_undefined_rates_and_validation(self):
        metrics = score_events([], [], 0)
        self.assertIsNone(metrics['event_recall'])
        self.assertIsNone(metrics['false_events_per_camera_hour'])
        for expected, predicted, seconds in [([event(3,2)],[],1),([],[],float('nan')),([],[],-1),([], [event(kind='cigarette')],1)]:
            with self.subTest(expected=expected,predicted=predicted,seconds=seconds), self.assertRaises(ValueError):
                score_events(expected,predicted,seconds)

    def test_ambiguous_and_unmonitored_intervals_do_not_hide_observable_errors(self):
        ignored = [event(10,20,review_status='ambiguous')]
        metrics = score_events(ignored, [event(12,18)], 10)
        self.assertEqual((metrics['TP'],metrics['FP'],metrics['FN']), (0,0,0))
        self.assertEqual(metrics['excluded_predictions'],1)
        metrics = score_events(ignored,[event(8,22)],10)
        self.assertEqual(metrics['FP'],1)  # observable pieces remain false
        metrics = score_events([], [event(5,6)], 8,
                               excluded_intervals=[dict(clip_id='one',start_seconds=4,end_seconds=6,reason='unmonitored')])
        self.assertEqual(metrics['FP'],0)
        self.assertEqual(metrics['unmonitored_seconds'],2)
        self.assertEqual(subtract_intervals([[0,10]],[[2,4],[3,6]]), [[0,2],[6,10]])

    def test_candidate_merging_is_separate_from_event_scoring(self):
        merged = merge_candidates([event(1,2),event(4,5),event(8,9),event(1,3,kind='fire')])
        smoke = [e for e in merged if e['kind']=='smoke']
        self.assertEqual([(e['start_seconds'],e['end_seconds']) for e in smoke], [(1,5),(8,9)])
        self.assertEqual(len(merge_candidates([event(1,2),event(1,2,clip='two')])),2)
