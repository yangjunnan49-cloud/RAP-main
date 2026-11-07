# M2 first batch: F02 precision repair

Date: 2026-09-10. Status: bounded F02 implementation and GPU validation passed;
M2 remains in progress. F03 and the other M2 findings are not repaired yet.

## Changes

RAP-SLAM `rap_slam/rap_precision.py` scopes float32 matmul precision to `highest`
and restores the exact incoming policy in `finally`. An RLock serializes cooperating
registration calls and supports nesting. `RAPBackend.register` and `register_multi`
use the scope over preprocessing, the full sampler (including intermediate rigidity
forcing), and final fit. Constructor no longer forces global matmul/cuDNN settings.
FP16 neural autocast remains in use. RAP-main model source is unchanged.

This deliberately protects a broader region than only the final SVD: covariance,
rotation composition, translation, and rigidified point application all need precision.
It can change inference and preprocessing results; it is a new numerical protocol.
The lock cannot control unrelated PyTorch callers changing process-global settings.
Such callers must cooperate or use a separate process. No concurrency guarantee is
claimed for model initialization, random seeds, or unrelated feature-only calls.

## Executed validation

- Startup: RAP-main HEAD `4055d92`, RAP-SLAM HEAD `6d3f2d2`. M0/M1 changes were
  uncommitted, contrary to any inference that a maintenance commit already existed.
- Snapshot exists, `INCOMPLETE` absent, manifest SHA256 matches the recorded
  `d9f23fdde6871e4b765d0f76c765035091afdc48e6655d11bf6001fffa41d497`.
  This session did not rehash all 4.6 GB; prior full-copy validation remains historical.
  All seven archived golden edge files were individually rehashed against the
  registry and matched; see archived_edges_validation.json.
- `scripts/maintenance/validate_f02.py` ran with torch 2.7.0+cu128 on RTX 5070.
  Known two-part transforms under outer FP16 autocast passed for incoming highest,
  high and medium policies. All tested geometric errors were below 1e-5;
  maximum orthogonality error 1.122e-6, rigidification point error 1.908e-6.
  Exact policy restoration after success, nested scopes and exceptions passed.
  Evidence: [f02_geometry.json](f02_geometry.json).
- `scripts/maintenance/validate_f02_pairs.py` performed actual checkpoint inference
  for all four archived POSS offline pair identities, using explicitly selected raw
  source frame IDs (3850/5265, 3850/5268, 3871/5268, 3850/5244).
  Each pair used fresh seed 42 in both an explicitly unwrapped legacy TF32 arm and
  the repaired arm. These are fresh comparisons, not historical RNG reproductions.
  Maximum relative-rotation orthogonality error: legacy 1.13313e-3 versus repaired
  1.84977e-6. Repaired determinants passed the absolute 1e-5 error threshold.
  A three-part real scan registration also passed all per-part geometric checks.
  Original accepted_loops.json hash was unchanged after the run.
  Evidence, exact matrices, metrics, input hashes and source hashes:
  [f02-poss-pairs-01/results.json](f02-poss-pairs-01/results.json).
- RAP-SLAM `git diff --check` passed. No original output directory was reused.

The 1e-5 tolerance is a float32 numerical validity bound for these normalized
clouds, not an accuracy or registration acceptance threshold. No new GT accuracy,
PGO, KITTI metric, or thesis-effect claim is made. No old rotation was projected
and substituted. Tests are maintenance helpers in RAP-main; production repair
lives only in RAP-SLAM. The default backend/checkpoints were used; checkpoint
identity is in the M0 registry, and historical checkpoint membership remains unknown.

## State and next batch

No commit, push, pull, reset or clean was performed. RAP-main retains existing
M0/M1 changes plus this batch's helpers/evidence/handoff. RAP-SLAM has a modified
rap_backend.py and new rap_precision.py; original source HEADs are unchanged.
Independent backup and historical provenance remain unresolved.

Next: M2/F03 and F16. Read eval_paper_metrics.py and real_dataset.py plus their
callers; establish explicit source-frame/timestamp correspondence and compare
KITTI segment enumeration/aggregation with the official reference, including
camera/LiDAR convention. Preserve legacy values and use new run IDs. Do not
advance to S1/M3 until M2's remaining findings and rerun scope are resolved.
Cross-dataset RAP validation and broader performance impact remain pending;
the POSS checks above do not validate all seven historical runs.
