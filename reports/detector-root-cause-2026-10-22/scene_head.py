"""Exploratory frozen-encoder smoke head, trained only on the previously screened FASDD pool."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scene_probe import summarize
sys.path.insert(0, str(ROOT))
from scripts.benchmark_data import file_sha256


def fit(features, targets, ridge):
    mean, bias = features.mean(axis=0), float(targets.mean())
    x = features - mean
    weights = x.T @ np.linalg.solve(x @ x.T + ridge * np.eye(len(x)), targets - bias)
    return mean, weights, bias


def self_check():
    x = np.array([[-2.], [-1.], [1.], [2.]])
    y = np.array([-1., -1., 1., 1.])
    mean, weights, bias = fit(x, y, .1)
    assert ((x - mean) @ weights + bias >= 0).tolist() == [False, False, True, True]
    shifted_mean, shifted_weights, shifted_bias = fit(x + 50, y, .1)
    assert np.allclose((x - mean) @ weights + bias, (x + 50 - shifted_mean) @ shifted_weights + shifted_bias)


def main():
    self_check()
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor
    torch.set_num_threads(4)
    spec = json.loads((HERE / 'scene-head-spec.json').read_text())
    assert spec['frozen_before_inference'] and spec['threshold'] == 0
    manifest = ROOT / spec['training_manifest']
    items = json.loads(manifest.read_text())
    assert len(items) == 224
    groups = {s: {x['scene_group'] for x in items if x['split'] == s} for s in ('train', 'val')}
    assert not groups['train'] & groups['val']
    for item in items:
        assert file_sha256(item['image_path']) == item['sha256']
        image = Path(item['image_path'])
        assert file_sha256(image.parents[2] / 'labels' / item['split'] / (image.stem + '.txt')) == item['label_sha256']
    source = json.loads((HERE / 'scene-model.json').read_text())['local_path']
    model = AutoModel.from_pretrained(source, local_files_only=True, trust_remote_code=False).eval()
    processor = AutoProcessor.from_pretrained(source, local_files_only=True, trust_remote_code=False)
    features = []
    for first in range(0, len(items), 8):
        images = [Image.open(item['image_path']).convert('RGB') for item in items[first:first + 8]]
        inputs = processor(images=images, return_tensors='pt')
        with torch.inference_mode():
            f = model.get_image_features(**inputs).pooler_output
            f = f / f.norm(p=2, dim=-1, keepdim=True)
            features.extend(f.cpu().tolist())
        for image in images:
            image.close()
        print('Encoded training pool', len(features), '/', len(items), flush=True)
    features = np.asarray(features, dtype=np.float64)
    targets = np.array([1. if x['category'] in spec['smoke_positive_categories'] else -1. for x in items])
    train = np.array([x['split'] == 'train' for x in items])
    assert train.sum() == spec['training_examples'] and (~train).sum() == spec['validation_examples']
    mean, weights, bias = fit(features[train], targets[train], spec['ridge_lambda'])
    pool_rows = [dict(id=str(x['id']), split=x['split'], smoke_assessment='present' if y > 0 else 'absent_visible', margin=float(s))
                 for x, y, s in zip(items, targets, (features - mean) @ weights + bias)]
    # ponytail: one fixed linear head, no threshold search on the reserved CCTV scenes.
    evaluation = np.load(ROOT / 'outputs/detector-root-cause-2026-10-22/scene-evaluation-features.npz', allow_pickle=False)
    labels = json.loads((HERE / 'scene-probe.json').read_text())['rows']
    assert evaluation['ids'].tolist() == [x['id'] for x in labels]
    scores = (evaluation['features'] - mean) @ weights + bias
    rows = [dict(id=x['id'], smoke_assessment=x['smoke_assessment'], margin=float(score)) for x, score in zip(labels, scores)]
    out = ROOT / 'outputs/detector-root-cause-2026-10-22/scene-head.npz'
    np.savez_compressed(out, mean=mean, weights=weights, bias=bias)
    result = dict(spec=spec, script_sha256=file_sha256(__file__), training_manifest_sha256=file_sha256(manifest),
        spec_sha256=file_sha256(HERE / 'scene-head-spec.json'), backbone_frozen=True, training_started=True,
        training_scope='Linear scene head only; no detector or encoder fine-tuning',
        training_scores=summarize([x for x in pool_rows if x['split'] == 'train'], 0),
        validation_scores=summarize([x for x in pool_rows if x['split'] == 'val'], 0),
        evaluation_scores=summarize(rows, 0), rows=rows, pool_rows=pool_rows,
        weights_path=str(out), weights_sha256=file_sha256(out), production_model_changed=False)
    (HERE / 'scene-head.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Validation', result['validation_scores'], 'CCTV diagnostic', result['evaluation_scores'], flush=True)


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Scene-head self-check passed: separable classes and train-only centering.')
    else:
        main()
