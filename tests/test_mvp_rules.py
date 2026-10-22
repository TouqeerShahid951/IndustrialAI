import unittest
from backend.rules import validate_zone, inside, associate, zone_events, smoking_events, helmet_events


def person(t, x=10, wrist=90, track=1, confidence=.9):
    return {'time':t,'track':track,'bbox':[x,2,x+100,200], 'keypoints':[[x+50,20,confidence]]+[[0,0,0]]*8+[[x+50,wrist,confidence],[0,0,0]]}


class RuleTests(unittest.TestCase):
    def test_polygon_geometry(self):
        square=[(0,0),(1,0),(1,1),(0,1)]
        validate_zone(square)
        self.assertTrue(inside((0,.5),square))
        self.assertFalse(inside((1.1,.5),square))
        for points in [[(0,0),(1,1),(0,1),(1,0)],[(0,0),(1,0),(1,0)],[(0,0),(2,0),(1,1)],[(0,0),(.5,0),(1,0)]]:
            with self.assertRaises(ValueError): validate_zone(points)

    def test_ambiguous_association_and_explicit_helmet(self):
        p=person(0)
        head={'bbox':[45,2,65,22],'canonical':'no_helmet'}
        self.assertIsNotNone(associate(head,[p],'head'))
        self.assertIsNone(associate(head,[p,person(0,11,track=2)],'head'))
        self.assertEqual(helmet_events([], [person(t) for t in (0,.5,1)]),[])
        raw=[dict(head,time=t) for t in (0,.5,1)]
        self.assertEqual(len(helmet_events(raw,[person(t) for t in (0,.5,1)])),1)
        tiny=[{'bbox':[50,5,56,11],'canonical':'no_helmet','time':t} for t in (0,.5,1)]
        self.assertEqual(helmet_events(tiny,[person(t) for t in (0,.5,1)]),[])

    def test_zone_initial_inside_dwell_exit_and_gap(self):
        zone={'name':'bay','points':[(0,0),(1,0),(1,1),(0,1)]}
        events=zone_events([person(t) for t in (0,.5,1)],zone,200,250)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['evidence']['entry'],'entry time unknown')
        self.assertEqual(zone_events([person(0),person(.2)],zone,200,250),[])
        self.assertEqual(zone_events([person(0),person(2),person(4)],zone,200,250),[])
        clipped=[dict(person(t),bbox=[10,0,110,200]) for t in (0,.5,1)]
        self.assertEqual(zone_events(clipped,zone,200,250),[])

    def test_smoking_requires_combined_same_track_cycle(self):
        people=[person(t,wrist=w) for t,w in [(0,90),(.5,30),(1,30),(1.5,30),(2,90)]]
        cigarettes=[{'time':t,'bbox':[57,25,63,31],'canonical':'cigarette'} for t in (.5,1,1.5)]
        events=smoking_events(cigarettes,people)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['evidence']['track'],1)
        self.assertEqual(smoking_events([],people),[])
        self.assertEqual(smoking_events(cigarettes,[person(t,wrist=90) for t in (0,.5,1,1.5,2)]),[])
        self.assertEqual(smoking_events(cigarettes,[person(p['time'],confidence=.1) for p in people]),[])
        self.assertEqual(smoking_events(cigarettes,[person(0),person(2,wrist=30),person(4)]),[])
