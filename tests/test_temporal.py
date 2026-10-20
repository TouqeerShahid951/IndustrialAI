import unittest
from temporal import confirm


class TemporalCheck(unittest.TestCase):
    def test_spatial_persistence_and_empty_frames(self):
        box = {'class': 'fire', 'bbox': [0, 0, 10, 10]}
        other = {'class': 'fire', 'bbox': [100, 100, 110, 110]}
        frames = [[box], [other], [box], [], [box], [], [], [], [], [box]]
        result = confirm(frames, hits=3, window=5)
        self.assertEqual([i for i, boxes in enumerate(result) if boxes], [4])
        self.assertEqual(confirm([[box]] * 3, hits=3, window=5)[2], [box])
        with self.assertRaises(ValueError):
            confirm(frames, hits=6, window=5)


class TimedTemporalChecks(unittest.TestCase):
    def test_elapsed_time_and_causal_confirmation(self):
        from temporal import confirm_timed
        box = {'class':'smoke','bbox':[0,0,10,10]}
        self.assertEqual(confirm_timed([[box]]*3,[0,.5,1]), [[],[],[box]])
        self.assertEqual(confirm_timed([[box]]*3,[0,.04,.08]), [[],[],[]])
        self.assertEqual(confirm_timed([[box]]*4,[0,.5,1,4])[-1], [])
        self.assertEqual(confirm_timed([[box],[],[box],[box]],[0,.5,1,1.5]), [[],[],[],[box]])
        self.assertEqual(confirm_timed([[box]]*25,[i/24 for i in range(25)])[-1], [box])

    def test_timestamp_validation_and_spatial_identity(self):
        from temporal import confirm_timed
        box = {'class':'fire','bbox':[0,0,10,10]}
        other = {'class':'fire','bbox':[30,30,40,40]}
        self.assertEqual(confirm_timed([[box],[other],[box]],[0,.5,1]),[[],[],[]])
        for times in ([0,0,1],[0,1,.5],[0,float('nan'),1],[0,float('inf'),2],[0,1],[-1,0,1]):
            with self.subTest(times=times), self.assertRaises(ValueError):
                confirm_timed([[box]]*3,times)
        with self.assertRaises(ValueError):
            confirm_timed([[box]]*3,[0,.5,1],window_seconds=.5,min_span_seconds=1)
