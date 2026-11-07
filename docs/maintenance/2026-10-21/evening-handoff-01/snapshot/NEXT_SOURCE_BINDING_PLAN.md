# Next source-binding decision: actual RAP interface, before inference

Planning only. No new model, feature extraction, fit, dataset/canonical batch construction, point/GT decode or efficacy run is admitted by this document. Existing retired-family and default/install/production/outreach/Git/scheduler stops remain. Manuscript remains paused and original research objective unresolved.

Use the exact locally hashed files in SOURCE_POINTERS.json: RAP-SLAM/rap_slam/rap_backend.py, RAP-main/demo.py, rectified_point_flow/data/dataset.py, rectified_point_flow/procrustes.py and sample.py. Read actual call arguments and return directions, not comments alone. Preserve their hashes and effective source/config provenance before deciding whether any isolated interface control is necessary.

Partial static reading is recorded in STATIC_OBSERVATION.md: the current two-part backend already has an original-frame recovery consistent with the conditional CN1 equation. Do not assume this path is missing or rebuild it. That observation does not authenticate custom/N-way batch behavior or the full runtime/evaluator path.

Required questions:

1. Which actual public arrays form model cond? Trace primary part, uniform scale, per-part centers and anchor offsets; record each normalization/inverse as equations tied to source lines. CN1's public-centroid/max-centered-coordinate convention is CUSTOM, not this implementation's certified normalization. A passing CN1 cannot authenticate it.
2. Does fit_transformations receive predicted endpoint or cond as source/target? Determine whether each returned transform maps normalized input to predicted common coordinates or the inverse. Bind rotation row/column convention, translation units, scale restoration, original-frame offsets, relative view direction and reference gauge. Do not infer these from T_rel naming.
3. Can the cooperating adapter construct its public model batch without reading private references or using loader-produced internal pointclouds_gt as externally authenticated truth? C0 public/private separation and old default-loader hazard remain. Disabling displayed metrics does not solve this question.
4. What would a complete synthetic source-interface check prove? It may validate coordinate bookkeeping, part identity, gauge and public reader paths; it cannot prove model output quality, physical common-world truth, pretraining exclusion or a RAP scientific gain. No new fit/projection is allowed to repair an invalid transform merely to pass a contract.

Only after these questions have evidence may a separate complete resource/source/strong-control protocol be considered. Any actual model comparison must retain exposed-scene limitations and an appropriate matched non-RAP baseline, avoid tuning on known failures, and keep all prior negatives. Do not use spare C0 budget or the recent small ICP variation as automatic authorization or causal explanation.
