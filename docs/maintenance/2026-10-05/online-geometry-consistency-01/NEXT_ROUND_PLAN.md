# Next bounded question: identity and temporal consistency, planned only

Do not resume the stopped equal-point GeoTransformer arm or modify official GT.
Mainline uncertainty is now whether09 cross-visit pair-label discrepancy is
physically recoverable by a matcher. Two models agree geometrically; both fail
official labels. Generic matcher replacement and interpolation already failed.

First read the exact E0 loader, scan/GT/frame/timestamp manifests and calibration
chain. Trace absolute scan filename->source_frame_ids->GT row->LiDAR transform,
including raw dataset archive provenance if available. Checksums and a working
loader alone do not establish correct timestamp correspondence. Record any
missing independent timing/archive evidence rather than infer its correctness.

Then separately freeze ONE GT-free input bank for local controls at every unique
endpoint across ALL98 online scans: previous/next10 absolute frames where in
range. Use the same exact range/correction/voxel/outlier/seed4000 recipe; fixed
offset10, no offset/correction/calibration sweep. Mark future-frame diagnostic
controls noncausal; this is data/label audit, not a deployment policy. No RAP
or Geo inference. Seal before evaluator poses, independently validate clouds.
Compare GT and saved odometry local relative poses geometrically; compare the
cross-visit discrepancy pattern against these local controls. Predeclare cost,
calibration/identity assertions and discrepancy thresholds before output.

Local agreement plus cross-visit disagreement narrows the hypotheses but still
does not establish GT drift versus repeated-scene alias. Only if needed, use
an independently verified sequence-level map/physical correspondence check
with fixed locations and recorded assumptions; no manual choice of a favorable
pose to improve official metrics. Keep official benchmark results unchanged.

Once identity/physical consistency is resolved, select one RAP-centred system
question on reliable revisits. 07 demonstrates that strict pair correctness
does not guarantee graph utility: direction-sensitive uncertainty and jointly
generated point structure are plausible questions, with substantial prior art.
A distinct mechanism must be specified against direct-matcher and equal-budget
geometric controls, with prospective trajectory gates and reserved eligible
confirmation data. Do not call generic covariance/graph weighting a RAP novelty.

This plan has no frozen protocol, runner, input bank or result. No training,
default/production edit, manuscript claim, commit or Git sync. All old negative
stops, frozen evidence and dirty work persist; novel RAP gain remains unproven.
