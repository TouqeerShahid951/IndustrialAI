"""Prepare a bounded, audited FASDD experiment; never edits the application's model."""
import argparse
import hashlib
import io
import json
import math
import random
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw


def remap_labels(text):
    lines=[]
    for line in text.splitlines():
        if not line.strip():
            continue
        fields=line.split()
        if len(fields)!=5 or fields[0] not in ('0','1'):
            raise ValueError('Expected fire/smoke YOLO detection boxes')
        x,y,w,h=map(float,fields[1:])
        if not all(math.isfinite(v) for v in (x,y,w,h)) or not (0<=x<=1 and 0<=y<=1 and 0<w<=1 and 0<h<=1):
            raise ValueError('Invalid normalized geometry')
        if min(x-w/2,y-h/2)<-.002 or max(x+w/2,y+h/2)>1.002:
            raise ValueError('Box outside image')
        lines.append(str(1-int(fields[0]))+' '+' '.join(fields[1:]))
    return '\n'.join(lines)+ ('\n' if lines else '')


def phash(image):
    gray=cv2.resize(cv2.cvtColor(image,cv2.COLOR_RGB2GRAY),(32,32)).astype(np.float32)
    values=cv2.dct(gray)[:8,:8].flatten()
    return int.from_bytes(np.packbits(values>np.median(values[1:])).tobytes(),'big')


def self_test():
    assert remap_labels('0 .5 .5 .2 .2\n1 .3 .3 .1 .1')=='1 .5 .5 .2 .2\n0 .3 .3 .1 .1\n'
    assert remap_labels('')==''
    for bad in ('2 .5 .5 .2 .2','0 nan .5 .2 .2','0 .99 .5 .5 .2'):
        try:
            remap_labels(bad)
        except ValueError:
            continue
        raise AssertionError('Invalid label accepted')
    image=np.zeros((100,100,3),dtype=np.uint8);image[10:60,20:40]=255
    assert phash(image)==phash(image.copy())
    print('label mapping, empty negatives, invalid geometry and image hashing checks passed')


def main(archive,destination,report):
    root=Path(destination);out=Path(report);out.mkdir(parents=True,exist_ok=True)
    if root.exists():
        raise ValueError('Use a new dataset directory; existing work is preserved')
    z=zipfile.ZipFile(archive);names=set(z.namelist());rng=random.Random(42)
    pools=defaultdict(list);invalid=[]
    # Reserve the forest-heavy later smoke IDs; this is a visual screening rule, not a source identity.
    for name in sorted(names):
        match=re.search(r'/images/(smoke|fire|bothFireAndSmoke|neitherFireNorSmoke)_CV(\d+)_',name)
        if not match or not name.endswith('.jpg'):
            continue
        category,identifier=match.group(1),int(match.group(2))
        if category=='smoke' and identifier>=8500:
            continue
        label=name.replace('/images/','/labels/').rsplit('.',1)[0]+'.txt'
        if label not in names:
            invalid.append({'entry':name,'reason':'missing label'});continue
        try:
            text=remap_labels(z.read(label).decode())
        except (ValueError,UnicodeDecodeError) as exc:
            invalid.append({'entry':name,'reason':str(exc)});continue
        if (category=='neitherFireNorSmoke')!= (not text):
            invalid.append({'entry':name,'reason':'category/empty-label mismatch'});continue
        pools[category].append((name,identifier,text))
    target={'neitherFireNorSmoke':200,'smoke':200,'fire':100,'bothFireAndSmoke':100}
    selected=[];rejected=Counter();seen=[]
    for category,items in pools.items():
        rng.shuffle(items)
        for name,identifier,text in items:
            raw=z.read(name)
            try:
                image=Image.open(io.BytesIO(raw)).convert('RGB');array=np.asarray(image)
            except Exception:
                rejected['unreadable image']+=1;continue
            w,h=image.size
            # ponytail: basic graphic/quality screening; contact-sheet review remains required.
            if min(w,h)<100 or max(w/h,h/w)>3 or np.mean(np.max(array,axis=2)<15)>.55 or np.mean(np.min(array,axis=2)>245)>.55:
                rejected['extreme crop, isolated graphic or tiny image']+=1;continue
            value=phash(array)
            if any((value^old).bit_count()<=8 for old in seen):
                rejected['near duplicate']+=1;continue
            seen.append(value)
            selected.append({'archive_entry':name,'category':category,'source_id':identifier,'labels':text,'sha256':hashlib.sha256(raw).hexdigest(),'phash':f'{value:016x}',
                             'scene_group':category+':block:'+str(identifier//500),'raw':raw})
            if sum(r['category']==category for r in selected)>=target[category]:
                break
    # Merge visually similar candidates into the same conservative filename block before splitting.
    parent={r['scene_group']:r['scene_group'] for r in selected}
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]];a=parent[a]
        return a
    for i,a in enumerate(selected):
        for b in selected[:i]:
            if (int(a['phash'],16)^int(b['phash'],16)).bit_count()<=14:
                parent[find(a['scene_group'])]=find(b['scene_group'])
    for row in selected:
        row['scene_group']=find(row['scene_group'])
        row['split']='val' if int(hashlib.sha256(row['scene_group'].encode()).hexdigest()[:8],16)%5==0 else 'train'
    root.mkdir(parents=True)
    for split in ('train','val'):
        (root/'images'/split).mkdir(parents=True);(root/'labels'/split).mkdir(parents=True)
    manifest=[]
    for i,row in enumerate(selected):
        stem=f'{i:04d}';split=row['split'];(root/'images'/split/(stem+'.jpg')).write_bytes(row.pop('raw'));(root/'labels'/split/(stem+'.txt')).write_text(row.pop('labels'));row['id']=i;row['image_path']=str((root/'images'/split/(stem+'.jpg')).resolve());manifest.append(row)
    (root/'data.yaml').write_text(f'path: {root.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: smoke\n  1: fire\n')
    (out/'pool-manifest.json').write_text(json.dumps(manifest,indent=2))
    counts=Counter((r['split'],r['category']) for r in manifest)
    summary={'archive_images':sum(n.endswith('.jpg') for n in names),'pool_images':len(manifest),'counts':{str(k):v for k,v in counts.items()},'rejected':dict(rejected),'invalid_count':len(invalid),'grouping':'Conservative category/ID blocks merged by perceptual similarity; original camera/incident identities unavailable. Internal development validation only.','manual_review':'pending','training_started':False}
    (out/'pool-summary.json').write_text(json.dumps(summary,indent=2));(out/'invalid-labels.json').write_text(json.dumps(invalid,indent=2))
    for category in target:
        items=[r for r in manifest if r['category']==category]
        # Every candidate is shown; IDs allow explicit exclusion and scene-group corrections.
        for page in range(math.ceil(len(items)/48)):
            sheet=Image.new('RGB',(1920,1280),'#17201b');draw=ImageDraw.Draw(sheet)
            for index,row in enumerate(items[page*48:(page+1)*48]):
                im=Image.open(row['image_path']).convert('RGB');im.thumbnail((318,138));x=index%6*320;y=index//6*160;sheet.paste(im,(x,y));draw.rectangle((x,y+140,x+319,y+159),fill='#17201b');draw.text((x+4,y+143),f'{row["id"]:04d} CV{row["source_id"]:06d} {row["split"]}',fill='white')
            sheet.save(out/f'pool-{category}-{page:02d}.jpg')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');parser.add_argument('--archive');parser.add_argument('--destination');parser.add_argument('--report');args=parser.parse_args()
    if args.self_test:self_test()
    else:main(args.archive,args.destination,args.report)
