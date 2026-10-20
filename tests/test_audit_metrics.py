import unittest
from scripts.audit_metrics import score_heads


class MatchingCheck(unittest.TestCase):
    def test_duplicate_and_wrong_class_do_not_inflate_matches(self):
        truth = [{'class': 'Hardhat', 'bbox': [0, 0, 10, 10]}]
        correct = {'class': 'Hardhat', 'bbox': [0, 0, 10, 10], 'confidence': .9}
        duplicate = dict(correct, confidence=.8)
        wrong = dict(correct, **{'class': 'NO-Hardhat'})
        self.assertEqual(score_heads(truth, [correct, duplicate], .5), (1, 1, 0))
        self.assertEqual(score_heads(truth, [wrong], .5), (0, 1, 1))
        self.assertEqual(score_heads(truth, [], .5), (0, 0, 1))
        self.assertEqual(score_heads([], [correct], .5), (0, 1, 0))
