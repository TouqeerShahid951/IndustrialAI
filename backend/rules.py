"""Provisional, explicit person-association rules. Outputs are review candidates."""
import math
from collections import defaultdict
from scripts.benchmark_events import union_intervals


def cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def on_segment(p,a,b):
    return abs(cross(a,b,p))<1e-9 and min(a[0],b[0])-1e-9<=p[0]<=max(a[0],b[0])+1e-9 and min(a[1],b[1])-1e-9<=p[1]<=max(a[1],b[1])+1e-9


def validate_zone(points):
    if not 3<=len(points)<=32 or len(set(map(tuple,points)))!=len(points):
        raise ValueError('A zone needs 3–32 distinct points.')
    if any(not math.isfinite(v) or not 0<=v<=1 for p in points for v in p):
        raise ValueError('Keep every zone point inside the source image.')
    edges=list(zip(points,points[1:]+points[:1]))
    if abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in edges))<1e-6:
        raise ValueError('The zone must have a nonzero area.')
    for i,(a,b) in enumerate(edges):
        for j,(c,d) in enumerate(edges):
            if j<=i or j==i+1 or (i==0 and j==len(edges)-1):
                continue
            if (cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0) or any((on_segment(c,a,b),on_segment(d,a,b),on_segment(a,c,d),on_segment(b,c,d))):
                raise ValueError('Zone edges cannot cross or touch other edges.')


def inside(point,polygon):
    result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if on_segment(point,a,b):
            return True
        if (a[1]>point[1]) != (b[1]>point[1]) and point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]:
            result=not result
    return result


def keypoint(person,index):
    points=person.get('keypoints',[])
    if len(points)<=index or len(points[index])<3 or points[index][2]<.5:
        return None
    return points[index][:2]


def associate(box,people,mode):
    a,b,c,d=box['bbox']
    center=((a+c)/2,(b+d)/2)
    choices=[]
    for person in people:
        x1,y1,x2,y2=person['bbox']
        height=y2-y1
        if person.get('track') is None or height<=0 or not x1<=center[0]<=x2 or not y1<=center[1]<=y2:
            continue
        if mode=='head':
            if center[1]>y1+height/3:
                continue
            score=math.dist(center,((x1+x2)/2,y1+height/8))/height
        else:
            if height<80:
                continue
            landmarks=[p for i in (0,9,10) if (p:=keypoint(person,i)) is not None]
            if not landmarks:
                continue
            score=min(math.dist(center,p) for p in landmarks)/height
            if score>.20:
                continue
        choices.append((score,person))
    choices.sort(key=lambda x:x[0])
    if not choices or (len(choices)>1 and choices[1][0]-choices[0][0]<.05):
        return None
    return choices[0][1]


def timed_groups(observations):
    observations=sorted(set(observations))
    groups=[]
    for t in sorted(set(observations)):
        hits=[v for v in observations if t-2<=v<=t]
        if len(hits)>=3 and t-min(hits)>=1:
            groups.append((min(hits),t+.001))
    return union_intervals(groups,gap=2)


def helmet_events(raw,people):
    at=defaultdict(list)
    for p in people:
        at[p['time']].append(p)
    hits=defaultdict(list)
    for box in raw:
        x1,y1,x2,y2=box['bbox']
        if box['canonical']!='no_helmet' or min(x2-x1,y2-y1)<12:
            continue
        owner=associate(box,at[box['time']],'head')
        if owner:
            hits[owner['track']].append(box['time'])
    return [{'kind':'no_helmet','start':a,'end':b,'evidence':{'track':track,'level':'temporal','label':'no-helmet candidate','rule_version':'development-1'}} for track,times in hits.items() for a,b in timed_groups(times)]


def zone_events(people,zone,width,height):
    tracks=defaultdict(list)
    for person in people:
        if person.get('track') is not None:
            tracks[person['track']].append(person)
    events=[]
    for track,history in tracks.items():
        previous=None
        outside=None
        start=None
        samples=[]
        active=None
        entry='entry time unknown'
        for person in sorted(history,key=lambda p:p['time']):
            t=person['time']
            x1,y1,x2,y2=person['bbox']
            clipped=x1<=1 or y1<=1 or x2>=width-1 or y2>=height-1
            if clipped or (previous is not None and t-previous>1):
                samples=[];start=None;outside=None;active=None;entry='entry time unknown'
            previous=t
            if clipped:
                continue
            is_inside=inside(((x1+x2)/2/width,y2/height),zone['points'])
            if is_inside:
                if start is None:
                    start=t
                    entry='entry observed' if outside is not None else 'entry time unknown'
                outside=None
                samples.append(t)
                if active is None and len(samples)>=3 and t-start>=1:
                    active={'kind':'intrusion','start':start,'end':t,'evidence':{'track':track,'zone':zone['name'],'entry':entry,'level':'temporal','label':'restricted-area presence candidate','rule_version':'development-1'}}
                    events.append(active)
                if active:
                    active['end']=t+.001
            else:
                if outside is None:
                    outside=t
                if active is None or t-outside>=2:
                    start=None;samples=[];active=None
    return events


def smoking_events(raw,people):
    at=defaultdict(list)
    tracks=defaultdict(list)
    for p in people:
        at[p['time']].append(p)
        if p.get('track') is not None:
            tracks[p['track']].append(p)
    cigarette_hits=defaultdict(list)
    for box in raw:
        owner=associate(box,at[box['time']],'object')
        if owner:
            cigarette_hits[owner['track']].append(box['time'])
    events=[]
    for track,history in tracks.items():
        for wrist_index in (9,10):
            stage='unknown';cycle_start=None;near_time=None;last=None
            for p in sorted(history,key=lambda p:p['time']):
                t=p['time'];height=p['bbox'][3]-p['bbox'][1]
                nose,wrist=keypoint(p,0),keypoint(p,wrist_index)
                if not nose or not wrist or height<80 or (last is not None and t-last>1):
                    stage='unknown';cycle_start=None;near_time=None
                last=t
                if not nose or not wrist or height<80:
                    continue
                distance=math.dist(nose,wrist)/height
                if cycle_start is not None and t-cycle_start>8:
                    stage='unknown';cycle_start=None;near_time=None
                if distance>=.25:
                    if stage=='near' and cycle_start is not None:
                        hits=[v for v in cigarette_hits[track] if cycle_start<=v<=t]
                        if timed_groups(hits):
                            events.append({'kind':'smoking','start':cycle_start,'end':t+.001,'evidence':{'track':track,'level':'temporal','label':'suspected smoking','gesture':'away → near → away','cigarette_hits':hits,'rule_version':'development-1'}})
                    stage='away';cycle_start=t;near_time=None
                elif distance<=.15 and stage=='away':
                    stage='near';near_time=t
    # Two wrists can support the same interval; preserve track separation.
    unique={}
    for event in events:
        unique[(event['evidence']['track'],event['start'],event['end'])]=event
    return list(unique.values())


def person_incidents(rows,zones,selected,metadata):
    people=[dict(box,time=r['time'],frame=r['frame']) for r in rows.get('pose',[]) for box in r['boxes']]
    heads=[dict(box,time=r['time']) for r in rows.get('helmet',[]) for box in r['boxes']]
    cigarettes=[dict(box,time=r['time']) for r in rows.get('cigarette',[]) for box in r['boxes']]
    events=[]
    if 'no_helmet' in selected:
        events+=helmet_events(heads,people)
    if 'smoking' in selected:
        events+=smoking_events(cigarettes,people)
    if 'intrusion' in selected:
        for zone in zones:
            events+=zone_events(people,zone,metadata['width'],metadata['height'])
    for event in events:
        event['end']=min(metadata['duration'],event['end'])
    eligible=sum(1 for p in people if p.get('track') is not None and p['bbox'][3]-p['bbox'][1]>=80 and keypoint(p,0) and (keypoint(p,9) or keypoint(p,10)))
    uncertain=[]
    if 'smoking' in selected:
        frames=rows.get('pose',[])
        intervals=[]
        for index,row in enumerate(frames):
            end=frames[index+1]['time'] if index+1<len(frames) else metadata['duration']
            visible=[p for p in row['boxes'] if p.get('track') is not None and p['bbox'][3]-p['bbox'][1]>=80 and keypoint(p,0) and (keypoint(p,9) or keypoint(p,10))]
            if not visible or len(visible)<len(row['boxes']):
                intervals.append([row['time'],end])
        uncertain=[{'kind':'smoking','start':a,'end':b,'reason':'Missing, small or obscured person/face/wrist evidence'} for a,b in union_intervals(intervals)]
    return events,{'person_observations':len(people),'eligible_smoking_observations':eligible,
                   'uncertain_intervals':uncertain,
                   'smoking':'limited visibility / unassessable' if not eligible else 'provisional combined-evidence rules; review required',
                   'no_helmet':'only explicit, associated no-helmet evidence emits candidates',
                   'intrusion':'clipped or lost tracks do not establish entry/exit'}
