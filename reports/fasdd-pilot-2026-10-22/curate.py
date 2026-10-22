"""Apply the recorded assistant visual review, then screen reserved footage for overlap."""
import json,sys,cv2,hashlib,os,math
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.prepare_fasdd_pilot import phash,remap_labels

p=Path(__file__).resolve().parent;root=Path('data/fasdd-cv-2026-10-22/pool');dest=Path('data/fasdd-cv-2026-10-22/curated')
assert not dest.exists(),'Preserve existing curated dataset'
rows=json.loads((p/'pool-manifest.json').read_text())
neg={200,203,204,213,214,215,220,221,222,223,225,227,229,231,234,238,239,242,246,247,253,254,255,258,259,261,265,267,268,271,275,276,277,279,283,285,286,287,288,292,294,296,297,298,300,305,308,309,313,315,316,318,320,321,324,327,331,332,338,344,345,346,347,348,351,352,354,355,361,362,363,364,373,377,380,381,383,384,386,389,391,396}
fire={100,103,104,106,107,109,111,112,114,115,116,126,128,129,130,131,132,134,135,137,138,141,142,143,145,150,154,155,156,159,161,163,165,167,168,173,174,177,179,182,186,187,189,190,199}
both={0,2,6,11,12,13,14,15,16,17,20,22,23,26,28,29,31,32,33,35,39,41,45,46,47,48,50,51,52,53,55,57,58,60,68,69,70,71,72,75,77,80,84,85,86,87,89,93,95,96,97}
smoke={402,405,412,414,417,418,419,428,432,434,436,440,444,447,451,453,457,459,460,464,468,470,471,474,475,476,478,480,481,490,491,492,495,496,497,499,503,511,512,517,519,522,526,528,532,533,534,539,540,543,549,551,560,562,564,572,575,576,577,578,579,581,582,584,586,587,590,593,594}
keep=neg|fire|both|smoke
# Same controlled corridor, classroom source family and repeated news event views stay together.
overrides={i:'controlled-corridor' for i in (12,87,402,539,582)}
overrides.update({i:'classroom-family' for i in (200,231,255,271,313,320,321,324,331,344,351,352,361,363,396)})
for group,ids in [('wood-roof-fire',[104,154,33]),('night-car-fire',[100,103,168,190]),('street-car-fire',[15,85]),('road-car-fire',[51,68]),('wood-tower-fire',[47,86])]:
 overrides.update({i:group for i in ids})
# Block/near-duplicate groups are retained; manual families merge, never split, those groups.
parent={r['scene_group']:r['scene_group'] for r in rows}
def find(a):
 while parent[a]!=a:
  parent[a]=parent[parent[a]];a=parent[a]
 return a
families=defaultdict(list)
for row in rows:
 if row['id'] in overrides:families[overrides[row['id']]].append(row['scene_group'])
for groups in families.values():
 for g in groups[1:]:parent[find(g)]=find(groups[0])
chosen=[r.copy() for r in rows if r['id'] in keep]
for r in chosen:r['scene_group']=find(r['scene_group'])
# Protect all 33 comparison sources, original benchmark footage, and the new house clip.
sources={str(Path(s['path']).resolve()) for s in json.loads(Path('reports/smoke-improvement-2026-10-21/comparison-sources.json').read_text())['sources']}
for line in Path('benchmark/manifest.jsonl').read_text().splitlines():
 r=json.loads(line);sources.add(str((Path('benchmark')/r['local_path']).resolve()))
sources.add(str(Path('var/mvp/media/6cf614b3-eb97-41bb-8f9f-ba6f4b9a2170.mp4').resolve()))
references=[]
for source in sorted(sources):
 cap=cv2.VideoCapture(source);fps=cap.get(cv2.CAP_PROP_FPS);index=0
 if not cap.isOpened():raise ValueError('Reserved source missing: '+source)
 while True:
  ok,bgr=cap.read()
  if not ok:break
  if index%max(1,round(fps/2))==0:references.append((phash(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)),source,index))
  index+=1
 cap.release()
reserved_matches=[]
for row in chosen:
 value=int(row['phash'],16);best=min(references,key=lambda r:(value^r[0]).bit_count());distance=(value^best[0]).bit_count()
 if distance<=12:reserved_matches.append({'id':row['id'],'distance':distance,'source':best[1],'frame':best[2],'scene_group':row['scene_group']})
blocked={r['scene_group'] for r in reserved_matches};chosen=[r for r in chosen if r['scene_group'] not in blocked]
# Select whole groups to give each category some internal validation exposure.
groups=defaultdict(list)
for row in chosen:groups[row['scene_group']].append(row)
totals=Counter(r['category'] for r in chosen);val=Counter();valgroups=set()
for group,items in sorted(groups.items(),key=lambda kv:hashlib.sha256(kv[0].encode()).hexdigest()):
 counts=Counter(r['category'] for r in items)
 if sum(min(n,max(0,round(totals[k]*.2)-val[k])) for k,n in counts.items())>sum(max(0,n-max(0,round(totals[k]*.2)-val[k])) for k,n in counts.items()):
  valgroups.add(group);val.update(counts)
for split in ('train','val'):
 (dest/'images'/split).mkdir(parents=True);(dest/'labels'/split).mkdir(parents=True)
for row in chosen:
 oldimage=Path(row['image_path']);oldlabel=oldimage.parent.parent.parent/'labels'/row['split']/(oldimage.stem+'.txt');row['split']='val' if row['scene_group'] in valgroups else 'train';image=dest/'images'/row['split']/oldimage.name;label=dest/'labels'/row['split']/oldlabel.name;os.link(oldimage,image);label.write_text(oldlabel.read_text());row['image_path']=str(image.resolve());row['label_sha256']=hashlib.sha256(label.read_bytes()).hexdigest();row['review']='assistant single-reviewer screening; publisher boxes retained; not independently relabeled'
(dest/'data.yaml').write_text(f'path: {dest.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: smoke\n  1: fire\n')
assert not ({r['scene_group'] for r in chosen if r['split']=='train'}&{r['scene_group'] for r in chosen if r['split']=='val'})
assert len({r['sha256'] for r in chosen})==len(chosen)
assert all(not a['scene_group']==b['scene_group'] or a['split']==b['split'] for a in chosen for b in chosen)
(p/'curated-manifest.json').write_text(json.dumps(chosen,indent=2))
(p/'reserved-overlap.json').write_text(json.dumps({'sources':sorted(sources),'sampled_frames':len(references),'sample_hz':2,'matches':reserved_matches,'blocked_groups':sorted(blocked),'limitations':'Perceptual matches plus manual source-family exclusions; absence of a match is not proof of independent camera provenance.'},indent=2))
summary={'screened':600,'visually_selected':len(keep),'accepted_after_overlap_exclusion':len(chosen),'counts':{str(k):v for k,v in Counter((r['split'],r['category']) for r in chosen).items()},'groups':len(groups),'manual_source_families':dict(overrides),'rejected_specific_errors':{'274':'visible burning coals labeled negative','194':'no visible fire; positive label uncertain','196':'no visible fire; positive label uncertain','521':'reserved FIREsense workshop camera; excluded related controlled-lab families'},'training_ready':'exploratory pilot only; original source/incident IDs unavailable, broad scene-group internal validation not an independent deployment test'}
(p/'curation-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
# Display every accepted positive with its remapped boxes for a separate localization check.
positives=[r for r in chosen if r['category']!='neitherFireNorSmoke']
for page in range(math.ceil(len(positives)/36)):
 sheet=Image.new('RGB',(1920,1080),'#17201b');draw=ImageDraw.Draw(sheet)
 for j,row in enumerate(positives[page*36:(page+1)*36]):
  im=Image.open(row['image_path']).convert('RGB');w,h=im.size;d=ImageDraw.Draw(im);label=dest/'labels'/row['split']/(Path(row['image_path']).stem+'.txt')
  for line in label.read_text().splitlines():
   cls,x,y,bw,bh=map(float,line.split());d.rectangle(((x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h),outline='#67e8f9' if cls==0 else '#ffffff',width=2)
  im.thumbnail((318,152));x=j%6*320;y=j//6*180;sheet.paste(im,(x,y));draw.text((x+4,y+155),f'{row["id"]:04d} {row["split"]}',fill='white')
 sheet.save(p/f'accepted-boxes-{page:02d}.jpg')
