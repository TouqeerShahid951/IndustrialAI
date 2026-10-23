"""Hold the frozen scene-head recipe constant and test the reviewed public-data additions."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREVIOUS = ROOT / 'reports/detector-root-cause-2026-10-22'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PREVIOUS))
from scripts.benchmark_data import file_sha256
from scene_head import fit, self_check
from scene_probe import summarize


def main():
    self_check()
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor
    torch.set_num_threads(4)
    spec = json.loads((HERE / 'experiment-spec.json').read_text())
    assert spec['training_manifest_sha256'] == file_sha256(HERE / 'training-manifest.json')
    assert spec['frozen_before_candidate_evaluation'] and spec['threshold'] == 0
    data = json.loads((HERE / 'training-manifest.json').read_text())
    old = json.loads((ROOT / 'reports/fasdd-pilot-2026-10-22/curated-manifest.json').read_text())
    validation = [dict(id='validation-' + str(x['id']), path=x['image_path'], sha256=x['sha256'],
                      target=1 if x['category'] in ('smoke', 'bothFireAndSmoke') else -1) for x in old if x['split'] == 'val']
    training = data['base_training'] + data['additions']
    items = training + validation
    assert len(data['base_training']) == 176 and len(validation) == 48
    assert not {x['sha256'] for x in training} & {x['sha256'] for x in validation}
    backbone = json.loads((PREVIOUS / 'scene-model.json').read_text())
    for f in backbone['files']:
        assert file_sha256(f['path']) == f['sha256']
    model = AutoModel.from_pretrained(backbone['local_path'], local_files_only=True, trust_remote_code=False).eval()
    processor = AutoProcessor.from_pretrained(backbone['local_path'], local_files_only=True, trust_remote_code=False)
    features = []
    for start in range(0, len(items), 8):
        batch = items[start:start + 8]
        for item in batch:
            assert file_sha256(item['path']) == item['sha256']
        images = [Image.open(item['path']).convert('RGB') for item in batch]
        with torch.inference_mode():
            f = model.get_image_features(**processor(images=images, return_tensors='pt')).pooler_output
            features.extend((f / f.norm(p=2, dim=-1, keepdim=True)).cpu().tolist())
        for image in images:
            image.close()
        print('Encoded', len(features), '/', len(items), flush=True)
    features = np.asarray(features, dtype=np.float64)
    targets = np.array([x['target'] for x in items])
    evaluation = np.load(ROOT / 'outputs/detector-root-cause-2026-10-22/scene-evaluation-features.npz', allow_pickle=False)
    truth = json.loads((PREVIOUS / 'scene-probe.json').read_text())['rows']
    assert evaluation['ids'].tolist() == [x['id'] for x in truth]
    results = []
    for name, count in [('unchanged_recipe_baseline', 176), ('public_data_addition', len(training))]:
        mean, weights, bias = fit(features[:count], targets[:count], spec['ridge_lambda'])
        scores = (evaluation['features'] - mean) @ weights + bias
        rows = [dict(id=x['id'], smoke_assessment=x['smoke_assessment'], margin=float(s)) for x, s in zip(truth, scores)]
        val_scores = (features[len(training):] - mean) @ weights + bias
        val_rows = [dict(smoke_assessment='present' if x['target'] == 1 else 'absent_visible', margin=float(s)) for x, s in zip(validation, val_scores)]
        result = dict(name=name, training_examples=count, CCTV_scores=summarize(rows, 0),
                      internal_validation_scores=summarize(val_rows, 0), rows=rows)
        if name == 'unchanged_recipe_baseline':
            assert result['CCTV_scores'] == json.loads((PREVIOUS / 'scene-head.json').read_text())['evaluation_scores']
        else:
            output = ROOT / 'outputs/public-training-footage-2026-10-23/scene-head.npz'
            np.savez_compressed(output, mean=mean, weights=weights, bias=bias)
            result.update(weights_path=str(output), weights_sha256=file_sha256(output))
        results.append(result)
        print(name, result['CCTV_scores'], result['internal_validation_scores'], flush=True)
    output = dict(spec=spec, script_sha256=file_sha256(__file__), spec_sha256=file_sha256(HERE / 'experiment-spec.json'),
                  backbone_spec_sha256=file_sha256(PREVIOUS / 'scene-model.json'), results=results,
                  training_scope='Frozen-encoder linear head only', production_model_changed=False, gate_passed=False)
    (HERE / 'experiment.json').write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        self_check(); print('Reused scene-head numerical self-check passed.')
    else:
        main()
