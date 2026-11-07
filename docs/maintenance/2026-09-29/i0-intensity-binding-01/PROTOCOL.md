# I0: raw LiDAR intensity to fixed F2 anchor binding preflight

This is a GT-free input feasibility check only. It does not evaluate descriptor
information, loop detection, registration, or novelty. KITTI raw scans contain
XYZI, while the current RAP-SLAM F2 loader explicitly selects XYZ and RAP's
preprocessor accepts `(N,3)` only. Existing LiDAR intensity loop methods,
including [Intensity Scan Context](https://arxiv.org/abs/2003.05656), mean
intensity itself is prior art. A later method would need a distinct use and
matched comparator.

## Frozen sample and procedure

Use the first four saved-order F2 pairs in each of 00 and 08; use only their
two anchor scans, `scans[0]` and `scans[3]`, and the corresponding saved
2000-point anchor arrays in `inputs.npz`. Verify every raw scan SHA against
`inputs_{seq}.json`. Parse raw float32 `(x,y,z,intensity)`; keep range>=1.5m;
apply the exact saved +0.205-degree KITTI vertical correction to XYZ, without
changing intensity. For each F2 anchor point find the nearest corrected raw
XYZ with a CPU cKDTree and copy its intensity for this preflight only.

Before real reads, freeze this protocol, runner, validator, source correction,
the eight saved F2 point archives and all sixteen raw scan identities. No GT,
F2 evaluator labels, feature bank, checkpoint or model is an input. Save all
16 scan-level distance/intensity summaries; SHA-seal them. Binding is viable
only if every scan has finite raw intensities, at least 95% of its anchor
points have a nearest corrected raw point within 0.5m, and at least eight
distinct finite intensity values among assigned anchor points. Report
per-scan median/p95 nearest distance, assigned intensity range and distinct
counts. Failure stops a naive nearest-raw intensity binding; no threshold
rescue. Passing permits a separately frozen intensity information audit, not
training or a method claim.

Wall cap 120s; RSS cap 2GiB; output cap 1MB. Preserve completed F2/C1-C6
artifacts, algorithm/default source and Git state.
