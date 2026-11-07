# E0-AMENDMENT-01: validator numerical crosscheck fix (2026-09-27)

Named correctness amendment per PROTOCOL.md ("Correctness fixes need a named
amendment and retained failed outputs"). No experiment rerun; no trajectory,
selection, or full-system output is modified by this amendment.

## Failure

The frozen validator `scripts/maintenance/validate_e0_frontend.py`
(SHA256 15b94edd..., identity recorded in resume_freeze.json) stopped at its
line 48 assertion on the first odometry cell (00-O):

```
assert abs(numpy_ate(gt,poses)-saved['lidar']['ape_aligned_rmse'])<1e-8
AssertionError
```

The failed run wrote no output files: every write in the validator occurs
after the checks, so there are no partial artifacts to retain. This document
retains the failure record.

## Diagnosis (measured)

- Frozen metric-code recomputation (`eval_paper_metrics.evaluate_pair`,
  evo-backed) reproduces the saved metrics exactly: 00-O aligned LiDAR ATE
  3.938480860600035 saved vs 3.938480860600035 recomputed.
- The validator's independent NumPy Umeyama crosscheck received UNANCHORED
  trajectories (KITTI world-frame coordinates of hundreds of meters). The
  gauge transformation is exact in real arithmetic but loses precision in
  float64 at that coordinate magnitude: unanchored NumPy ATE
  3.9384814435195534 vs saved 3.938480860600035 (delta 5.83e-7 > 1e-8).
- The identical crosscheck on first-pose-anchored trajectories agrees to
  4.4e-12, well inside the tolerance.

This is a numerical-conditioning defect in the validator's independent
crosscheck, not a defect in saved trajectories, metrics, or evaluation code.

## Fix

Amended copy `scripts/maintenance/validate_e0_frontend_v2.py` (its SHA256 is
recorded in validation.json as validator_sha256): both numpy_ate call sites
(odometry cells and full-system products) now anchor both trajectories to the
first pose before the crosscheck. Tolerance unchanged (1e-8). No other logic
changed. The original frozen validator file is unchanged and its recorded
hash identity remains valid.

## Effect on results

None. The NumPy crosscheck is an independent numerical confirmation; the
authoritative frozen-code recomputation already matched every saved metric
exactly before this amendment.
