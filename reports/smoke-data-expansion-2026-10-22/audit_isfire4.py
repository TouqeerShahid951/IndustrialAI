"""Inspect the pinned archive without extracting or admitting images to training."""
import hashlib
import io
import json
import random
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.prepare_fasdd_pilot import phash, remap_labels

REPORT = Path(__file__).resolve().parent
ARCHIVE = Path('data/isfire4-audit-2026-10-22/Dataset.zip')
CLASSES = ['black smoke', 'blue fire', 'white-gray smoke', 'yellow-orange fire']


def checked_boxes(text):
    boxes = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5 or fields[0] not in ('0', '1', '2', '3'):
            raise ValueError('Expected four-class YOLO labels')
        remap_labels('0 ' + ' '.join(fields[1:]))  # Reuse normalized-geometry validation.
        boxes.append((int(fields[0]), *map(float, fields[1:])))
    return boxes


def main():
    with ARCHIVE.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    assert digest == 'fb90a9bfed10f3f00529e2a8d8c512d5f92d8d2e19baac8135e6bdb751722ce9'
    rows, errors = [], []
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = set(archive.namelist())
        (REPORT / 'archive-data.yaml').write_bytes(archive.read('Dataset/data.yaml'))
        images = sorted(n for n in names if '/images/' in n and Path(n).suffix.lower() in ('.jpg', '.jpeg', '.png'))
        for index, name in enumerate(images):
            label = name.replace('/images/', '/labels/').rsplit('.', 1)[0] + '.txt'
            try:
                if label not in names:
                    raise ValueError('Missing label')
                boxes = checked_boxes(archive.read(label).decode())
                raw = archive.read(name)
                image = Image.open(io.BytesIO(raw)).convert('RGB')
                rows.append(dict(id=index, entry=name, split=name.split('/')[1],
                                 original_stem=Path(name).stem.split('.rf.')[0],
                                 sha256=hashlib.sha256(raw).hexdigest(),
                                 phash=f'{phash(np.asarray(image)):016x}', size=image.size,
                                 boxes=boxes))
            except (ValueError, OSError, UnicodeDecodeError) as exc:
                errors.append(dict(entry=name, reason=str(exc)))
        # ponytail: filename identity only; camera/incident IDs are still unknown.
        duplicate_groups = {}
        for key in ('sha256', 'original_stem'):
            groups = defaultdict(list)
            for row in rows:
                groups[row[key]].append(row)
            duplicate_groups[key] = [dict(key=value, ids=[r['id'] for r in group],
                                         splits=sorted({r['split'] for r in group}))
                                     for value, group in groups.items() if len(group) > 1]
        samples = []
        for cls in range(4):
            candidates = [r for r in rows if any(b[0] == cls for b in r['boxes'])]
            random.Random(42 + cls).shuffle(candidates)
            chosen = candidates[:48]
            sheet = Image.new('RGB', (1920, 1280), '#17201b')
            draw = ImageDraw.Draw(sheet)
            for j, row in enumerate(chosen):
                image = Image.open(io.BytesIO(archive.read(row['entry']))).convert('RGB')
                w, h = image.size
                pen = ImageDraw.Draw(image)
                for kind, x, y, bw, bh in row['boxes']:
                    pen.rectangle(((x-bw/2)*w, (y-bh/2)*h, (x+bw/2)*w, (y+bh/2)*h),
                                  outline=['#67e8f9', '#ffffff', '#b7a4ff', '#ffffff'][kind], width=2)
                image.thumbnail((318, 138))
                x, y = j % 6 * 320, j // 6 * 160
                sheet.paste(image, (x, y))
                draw.text((x+4, y+141), f'{row["id"]:04d} {CLASSES[cls]}', fill='white')
            sheet.save(REPORT / f'sample-class-{cls}.jpg')
            samples.append(dict(class_id=cls, image_ids=[r['id'] for r in chosen]))
    summary = dict(archive_sha256=digest, images=len(images), readable_valid_labeled=len(rows),
                   splits=dict(Counter(r['split'] for r in rows)),
                   boxes_by_class={CLASSES[k]:sum(b[0] == k for r in rows for b in r['boxes']) for k in range(4)},
                   empty_label_images=sum(not r['boxes'] for r in rows),
                   unique_image_sha256=len({r['sha256'] for r in rows}),
                   unique_original_stems=len({r['original_stem'] for r in rows}),
                   cross_split_groups={k:sum(len(g['splits'])>1 for g in v) for k,v in duplicate_groups.items()},
                   invalid=errors, visual_sample=samples, admitted_to_training=0)
    (ARCHIVE.parent / 'archive-manifest.json').write_text(json.dumps(rows, indent=2))
    (REPORT / 'duplicate-groups.json').write_text(json.dumps(duplicate_groups, indent=2))
    (REPORT / 'archive-audit.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='visual_sample'}, indent=2))


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        assert checked_boxes('2 .5 .5 .2 .2') == [(2, .5, .5, .2, .2)]
        assert checked_boxes('') == []
        for bad in ('4 .5 .5 .2 .2', '0 nan .5 .2 .2', '3 .99 .5 .5 .2'):
            try:
                checked_boxes(bad)
            except ValueError:
                continue
            raise AssertionError('Invalid label accepted')
        print('Four-class parsing, empty labels and geometry checks passed')
    else:
        main()
