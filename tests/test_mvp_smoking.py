import unittest
from tests.test_mvp_rules import person
from backend.rules import smoking_events,helmet_events,person_incidents


class SmokingTests(unittest.TestCase):
    def test_unassessable_source_intervals_are_explicit(self):
        rows={'pose':[{'time':t,'frame':n,'boxes':[dict(person(t),keypoints=[])]} for n,t in enumerate((0,.5,1))]}
        events,assessment=person_incidents(rows,[],['smoking'],{'width':200,'height':250,'duration':1.5})
        self.assertEqual(events,[])
        self.assertTrue(assessment['uncertain_intervals'])
        self.assertEqual(assessment['uncertain_intervals'][0]['start'],0)
        self.assertEqual(assessment['uncertain_intervals'][0]['end'],1.5)

    def test_small_missing_ambiguous_and_duplicate_evidence_abstains(self):
        sequence=[person(t,wrist=w) for t,w in [(0,90),(.5,30),(1,30),(1.5,30),(2,90)]]
        raw=[{'time':t,'bbox':[57,25,63,31],'canonical':'cigarette'} for t in (.5,1,1.5)]
        self.assertEqual(smoking_events(raw,[dict(p,bbox=[10,2,110,70]) for p in sequence]),[])
        self.assertEqual(smoking_events(raw,[dict(p,keypoints=[]) for p in sequence]),[])
        neighbors=sequence+[dict(p,track=2) for p in sequence]
        self.assertEqual(smoking_events(raw,neighbors),[])
        cigarette_only=[person(t,wrist=30) for t in (0,.5,1,1.5,2)]
        self.assertEqual(smoking_events(raw,cigarette_only),[])
        duplicate_heads=[{'time':t,'bbox':[45,2,65,22],'canonical':'no_helmet'} for t in (0,0,1)]
        self.assertEqual(helmet_events(duplicate_heads,[person(t) for t in (0,1)]),[])

    def test_cigarette_in_other_hand_cannot_support_gesture(self):
        people=[person(t,wrist=w) for t,w in [(0,90),(.5,30),(1,30),(1.5,30),(2,90)]]
        for p in people:p['keypoints'][10]=[95,130,.9]
        raw=[{'time':t,'bbox':[92,127,98,133]} for t in (.5,1,1.5)]
        self.assertEqual(smoking_events(raw,people),[])

    def test_ambiguous_association_resets_cycle_and_records_uncertainty(self):
        people=[person(t,wrist=w) for t,w in [(0,90),(.5,30),(1,30),(1.5,30),(1.75,30),(2,90)]]
        people.append(person(1.75,x=11,wrist=30,track=2))
        raw=[{'time':t,'bbox':[57,25,63,31]} for t in (.5,1,1.5,1.75)]
        self.assertEqual(smoking_events(raw,people),[])
        rows={'pose':[{'time':t,'frame':n,'boxes':[p for p in people if p['time']==t]} for n,t in enumerate((0,.5,1,1.5,1.75,2))],
              'cigarette':[{'time':b['time'],'boxes':[b]} for b in raw]}
        _,assessment=person_incidents(rows,[],['smoking'],{'width':200,'height':250,'duration':2.5})
        self.assertTrue(any('ambiguous' in i['reason'].lower() for i in assessment['uncertain_intervals']))
