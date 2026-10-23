"""Apply the recorded visual review; keep uncertain aerosols and protected scenes out of fitting."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.prepare_fasdd_pilot import phash
from scripts.benchmark_data import file_sha256, load_manifest

# Single-assistant visual review of the unboxed diversity sheets and enlarged smoke examples.
# These are scene-presence annotations, not chemical measurements or object-localization truth.
POSITIVE_FAMILIES = {
    'indoor-coal-tray': [1, 41, 49, 51, 79, 90, 102, 112, 117, 126, 142],
    'incense-closeup': [37, 47, 87, 132],
    'nist-chair-demonstration': [14, 38, 59, 64, 137],
    'small-burning-fuel-closeup': [52],
    'fire-department-room': [57],
    'flashover-living-room': [83, 119],
    'furnished-room-demonstration': [96],
    'indoor-round-fuel-pot': [98, 103, 130],
    'retail-fire-demonstration': [133],
}
UNCERTAIN_DEVICE_IDS = {6, 11, 13, 22, 63, 69, 82, 91, 106, 108, 118, 128, 136}


def self_check():
    ids = [i for group in POSITIVE_FAMILIES.values() for i in group]
    assert len(ids) == len(set(ids)) and not set(ids) & UNCERTAIN_DEVICE_IDS
    assert len([i for group in POSITIVE_FAMILIES.values() for i in group[:3]]) == 18


def main():
    self_check()
    reviewed = json.loads((HERE / 'indoor-diversity.json').read_text())
    family = {i: group for group, ids in POSITIVE_FAMILIES.items() for i in ids}
    reviews = []
    for item in reviewed:
        group = family.get(item['id'])
        reviews.append(dict(item, smoke_assessment='present' if group else 'uncertain',
            source_family=group, review_status='assistant_reviewed',
            disposition='candidate_positive' if group else 'excluded_from_fitting',
            note='Visible plume/haze associated with burning fuel or an active fire scene' if group else
                 'Source, visible presence or physical nature insufficiently established; no inherited positive label'))
    # Retain the previously screened training split; its internal validation images remain protected.
    old = json.loads((ROOT / 'reports/fasdd-pilot-2026-10-22/curated-manifest.json').read_text())
    references = [(int(x['phash'], 16), 'fasdd_internal_validation', str(x['id'])) for x in old if x['split'] == 'val']
    inputs = json.loads((ROOT / 'reports/detector-root-cause-2026-10-22/inputs.json').read_text())['frames']
    for item in inputs:
        references.append((phash(np.asarray(Image.open(item['path']).convert('RGB'))), 'reserved_new_CCTV', item['id']))
    for manifest in [ROOT / 'benchmark/chat-review-manifest.jsonl',
                     ROOT / 'reports/smoke-improvement-2026-10-21/assistant-review-manifest.jsonl']:
        for clip in load_manifest(manifest):
            cap = cv2.VideoCapture(clip['local_path']); fps = cap.get(cv2.CAP_PROP_FPS); index = 0
            while True:
                ok, bgr = cap.read()
                if not ok:
                    break
                if index % max(1, round(fps / 2)) == 0:
                    references.append((phash(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)), 'reserved_older_CCTV', clip['clip_id']))
                index += 1
            cap.release()
    matches = []
    for item in reviews:
        if item['source_family']:
            value = int(item['phash'], 16)
            nearest = min(references, key=lambda r: (value ^ r[0]).bit_count())
            if (value ^ nearest[0]).bit_count() <= 12:
                matches.append(dict(id=item['id'], source_family=item['source_family'], distance=(value ^ nearest[0]).bit_count(),
                                    protected_set=nearest[1], reference_id=nearest[2]))
    blocked = {m['source_family'] for m in matches}
    selected = []
    for group, ids in POSITIVE_FAMILIES.items():
        if group not in blocked:
            selected += [dict(next(x for x in reviews if x['id'] == i), id='indoor-' + str(i),
                             path=next(x for x in reviews if x['id'] == i)['path'], target=1, group=group) for i in ids[:3]]
    meva = json.loads((HERE / 'meva-long-review.json').read_text())
    for camera, positions in [('G419', [0, 40, 80, 120]), ('G423', [0, 27, 64, 86])]:
        samples = [x for x in meva['samples'] if x['camera_id'] == camera]
        for i in positions:
            selected.append(dict(samples[i], id=camera + '-' + str(i), target=-1, group='meva-kf1-all',
                                 smoke_assessment='absent_visible', fire_assessment='absent_visible',
                                 review_status='assistant_reviewed', review_scope='This sampled still only'))
    training = [dict(id='fasdd-' + str(x['id']), path=x['image_path'], sha256=x['sha256'], group=x['scene_group'],
                     target=1 if x['category'] in ('smoke', 'bothFireAndSmoke') else -1) for x in old if x['split'] == 'train']
    old_hashes = {x['sha256'] for x in training}
    selected = [x for x in selected if x['sha256'] not in old_hashes]
    for x in training + selected:
        assert file_sha256(x['path']) == x['sha256']
    (HERE / 'image-review.json').write_text(json.dumps(reviews, indent=2) + '\n')
    (HERE / 'overlap-screen.json').write_text(json.dumps(dict(reference_frames=len(references), matches=matches,
        blocked_families=sorted(blocked), limitation='pHash plus manual source families is conservative screening, not verified independence'), indent=2) + '\n')
    (HERE / 'training-manifest.json').write_text(json.dumps(dict(base_training=training, additions=selected,
        reviewed_positive_images=len(family), approximate_positive_families=len(POSITIVE_FAMILIES),
        training_counts=dict(Counter(str(x['target']) for x in training + selected)),
        fitting_scope='Exploratory frozen-encoder scene-head comparison; no new detector training or model promotion',
        protected_CCTV_images_used_for_fitting=False), indent=2) + '\n')
    print('Base training', len(training), 'new selected', len(selected), 'blocked positive families', sorted(blocked), flush=True)


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Curation self-check passed: unique review IDs, uncertain devices excluded, per-family cap.')
    else:
        main()
