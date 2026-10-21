# Bounded local training recipe — pending data

No new fine-tuning run has been started. The current model remains the most useful starting point on the small reviewed development set: both alternative models lose a temporally confirmed fire event. This is a starting-point choice, not independent model qualification.

The prepared YAML caps training at ten epochs on this Mac, batch four, 640 input, fixed seed and a separate output directory. Dataset class IDs match the current checkpoint: 0 smoke, 1 fire. D-Fire uses this same order; the two alternative checkpoints use the opposite order and must not be substituted without remapping labels.

Before running, populate the pending dataset from source cameras/incidents whose rights and identities are recorded. Keep every camera/site/incident in one split and reserve all 33 comparison sources and their neighboring frames from training and optimizer validation. Include checked industrial steam, dust, reflections, machinery, workers and difficult distant positives. The two new factory clips have uncertain process haze and cannot simply receive empty smoke labels. The four assistant review clips are evaluation examples; their diffuse boxes are ambiguous localization drafts, not training truth.

D-Fire row metadata currently provides filenames and boxes but no usable camera/incident groups; WEB source rights and scene overlap need review. The inspected AoF subset has only four fire-containing examples. The earlier twenty-image pilot regressed. These are data conditions, not a request for renewed permission.

Once the data and source split audit pass, run from the project directory:

```sh
YOLO_AUTOINSTALL=false .venv/bin/yolo detect train cfg=reports/smoke-improvement-2026-10-21/training-config-pending.yaml
```

Then rerun evaluate.py on the exact comparison sources at confidence 0.25, size 640, stride one and max_frames 2000, using the new best.pt explicitly. Rebuild both development reports separately (human and assistant labels), compare missed events and false events, and retain the existing default. Do not reuse these development numbers as a locked test.
