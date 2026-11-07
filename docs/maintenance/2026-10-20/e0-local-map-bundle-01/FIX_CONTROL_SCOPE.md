# Coarse-anchor implementation control — synthetic only

The native contract diagnosis produced anchors[0,3,6] at x[0,3.1,6.2] instead of the prescribed[0,3.3,6.0]. The source fixes id_-1 near interval ends and does not set the shared boundary vertex to the next coarse keypose. Real recovered coarse anchors also move under native fine optimization. This is a demonstrated contract mismatch, not an author-confirmed defect or the established cause of00 ter regression: before-fine00 ter is already0.572513%, versus0.571054% after fine.

Implement a small isolated fine-graph control: keep all dense E0 relative motions and unit information, set actual source-frame coarse-anchor vertices to their coarse poses and fix those exact vertices. Use the same native PoseGraphOptimizer and max_iterations10. No library/production modification, new geometry, extra loop, weight tuning or map change.

This stage executes synthetic inputs only. Require exact anchor preservation, the analytic piecewise translation solution for the known three-map fixture, no-op for consistent coarse anchors and a common-world rigid transform check. Freeze helper/scope before execution. Retain native counterexample and original LMB0 negative; no corrected real candidate, metric or all-six expansion is admitted here. Future metric priority is pending the owner's asynchronous choice.

Use the original remaining LMB0 cumulative1800s/4GiB/128MiB/GPU0 scope and12GiB Windows launch guard. Parent/native clocks overlap. No cap reset, reference change, Git mutation or goal-status action.
