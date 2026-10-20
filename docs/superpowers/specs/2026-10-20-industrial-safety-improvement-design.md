# Industrial Safety AI improvement brief

## Objective

Turn the current offline model-evaluation project into a measurable, operator-reviewed single-camera prototype. Improve detection quality before adding a multi-camera product. The eventual MVP retains five capabilities: fire, smoke, smoking behavior, no-helmet detection and restricted-area entry.

## Starting evidence

The original checkpoints run on this Mac's Apple MPS backend. Current evidence is exploratory: two public CCTV-style examples, mixed research clips, repeated evaluation on the same sources, an overlaid workshop video, and approximate single-reviewer annotations. Nearby helmets are easier than distant uncovered heads. Higher input resolution improves some detections while increasing false alerts. Tiny fire fine-tuning regressed. Frame-count temporal voting behaves differently at different source frame rates. Clean positive smoking CCTV is untested; the user-selected YouTube video could not be retrieved.

## Constraints

- Local Python 3.12 and Apple MPS are the initial runtime; CPU remains an explicit fallback.
- Reuse OpenCV, Ultralytics, existing evaluation scripts and stdlib unittest.
- No paid compute, external deployment, cloud account creation or facility-footage uploads in this plan's first milestone.
- Preserve original checkpoints; experimental weights and configurations are separate artifacts.
- Keep original source timestamps, model versions and source identities in results.
- Split evaluation data by camera/site/source event, never randomly by neighboring frames.
- Keep candidate detections available immediately; temporal confirmation must not erase the original evidence.
- Unknown, unassessable and inference-offline states must never be reported as safe/compliant.
- The prototype remains an operator aid; passing an engineering gate is not fire-system certification.

## First milestone

A repeatable offline benchmark with traceable data, event-level metrics and timestamp-based confirmation. It must compare the original detector, temporal variants and future candidate models without changing test membership or alert definitions. Source footage, annotations and split metadata are separate so private video is not accidentally included in version control.

Use a JSONL clip manifest with: clip_id, local_path, source_sha256, camera_id, site_id, source_event_id, split, capture_origin, permission_status, duration_seconds, conditions and annotation_path. Splits are development, validation and locked_test. Unknown capture provenance is capture_origin=unverified_demo and excluded from locked_test. Clips from the same camera/site/source event stay in one split. Permission must allow the intended evaluation use.

Annotations contain events with kind, start_seconds, end_seconds and review_status; optional sampled frames contain class, bbox_xyxy and review_status. Canonical objects: fire, smoke, helmet, no_helmet, person, cigarette. Canonical events: fire, smoke, smoking, no_helmet, restricted_entry. Raw model labels remain in the original logs and are mapped explicitly for scoring. Ambiguous regions/intervals are excluded from scoring and counted separately.

## Measurement and decisions

Report per-capability event recall, false alert events per annotated negative camera-hour, first-confirmation delay from first visually assessable evidence, monitoring coverage and p50/p95 processing latency. Head/object scoring uses one-to-one class-aware matching at IoU 0.5, with IoU 0.3 reported separately for tiny objects. Smoking requires person/temporal evidence; a cigarette box is a candidate only.

A predicted event matches at most one reviewed event of the same kind and clip when their intervals overlap. Match the earliest eligible prediction; duplicates are unmatched alerts. Merge candidate intervals separated by at most two seconds before scoring, record that choice, and keep it identical across variants. Negative camera-hours include only explicitly reviewed negative intervals; missing inference is reported as lost coverage.

Provisional development targets, to be agreed before locking validation policy: at least 90% event recall for each supported capability, at most one false alert per eight negative camera-hours, and p95 confirmation delay at most five seconds from visually assessable evidence for fire/smoke. Report counts, uncertainty and observation time; insufficient data cannot pass. These are proposed engineering targets, not established safety requirements.

## Later milestones

Use the benchmark to assess person/head association, camera-specific input size and smoke-focused retraining. Then validate smoking sequences and polygon intrusion rules. Only after those evidence gates, add local live capture, health status, incident evidence and one operator view. Multi-camera support and cloud inference follow measured demand.
