"""Frozen whole-scene smoke hypothesis; no box coordinates or calibrated probabilities."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.benchmark_data import file_sha256


def margin(logits, positives):
    return max(logits[:positives]) - max(logits[positives:])


def summarize(rows, threshold):
    result = dict(TP=0, FP=0, TN=0, FN=0, excluded=0)
    for row in rows:
        state = row['smoke_assessment']
        if state == 'uncertain':
            result['excluded'] += 1
            continue
        assert state in ('present', 'absent_visible')
        predicted = row['margin'] >= threshold
        result[('T' if predicted == (state == 'present') else 'F') + ('P' if predicted else 'N')] += 1
    return result


def self_check():
    assert margin([2, 4, 3, 1], 2) == 1
    rows = [dict(smoke_assessment='present', margin=0), dict(smoke_assessment='absent_visible', margin=-1),
            dict(smoke_assessment='uncertain', margin=1), dict(smoke_assessment='absent_visible', margin=1)]
    assert summarize(rows, 0) == dict(TP=1, FP=1, TN=1, FN=0, excluded=1)


def main():
    self_check()
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor
    torch.set_num_threads(4)
    spec = json.loads((HERE / 'scene-prompts.json').read_text())
    assert spec['frozen_before_inference'] and spec['margin_threshold'] == 0
    model_spec = json.loads((HERE / 'scene-model.json').read_text())
    # ponytail: 69-frame diagnostic on CPU; batch four avoids competing with the running MPS video experiment.
    device = 'cpu'
    source = model_spec.get('local_path', model_spec['repository'])
    model = AutoModel.from_pretrained(source, revision=model_spec['revision'],
        local_files_only=True, trust_remote_code=False).eval().to(device)
    processor = AutoProcessor.from_pretrained(source, revision=model_spec['revision'],
        local_files_only=True, trust_remote_code=False)
    items = json.loads((HERE / 'inputs.json').read_text())['frames']
    texts = [spec['template'].format(t) for t in spec['positive'] + spec['negative']]
    for item in items:
        assert file_sha256(item['path']) == item['sha256']
    rows, features = [], []
    started = time.monotonic()
    for first in range(0, len(items), 4):
        batch = items[first:first + 4]
        images = [Image.open(item['path']).convert('RGB') for item in batch]
        inputs = processor(text=texts, images=images, padding='max_length', max_length=64,
                           truncation=True, return_tensors='pt').to(device)
        assert inputs['input_ids'].shape[-1] == 64
        assert 0 <= inputs['input_ids'].min() <= inputs['input_ids'].max() < model.text_model.embeddings.token_embedding.num_embeddings
        with torch.inference_mode():
            output = model(**inputs)
            logits = output.logits_per_image.cpu().tolist()
            features.extend(output.image_embeds.cpu().tolist())
        for item, values in zip(batch, logits):
            rows.append(dict(id=item['id'], input_sha256=item['sha256'],
                smoke_assessment=item['frame_annotation']['class_assessment']['smoke'],
                logits=values, margin=margin(values, len(spec['positive']))))
        for im in images:
            im.close()
        print('Scored', len(rows), '/', len(items), flush=True)
    result = dict(model=model_spec, prompt_spec=spec, prompt_spec_sha256=file_sha256(HERE / 'scene-prompts.json'),
        input_manifest_sha256=file_sha256(HERE / 'inputs.json'), script_sha256=file_sha256(__file__),
        device=device, wall_seconds=time.monotonic() - started, rows=rows,
        scores=summarize(rows, spec['margin_threshold']), training_started=False,
        limitations=['Scene presence only; no localization', 'Development samples; not independent validation',
                     'Prompt similarity margin is not a calibrated hazard probability'])
    (HERE / 'scene-probe.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    import numpy as np
    np.savez_compressed(ROOT / 'outputs/detector-root-cause-2026-10-22/scene-evaluation-features.npz',
                        features=features, ids=[item['id'] for item in items])
    print(json.dumps(result['scores']), flush=True)


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Scene self-check passed: margin, exact threshold and uncertain labels.')
    else:
        main()
