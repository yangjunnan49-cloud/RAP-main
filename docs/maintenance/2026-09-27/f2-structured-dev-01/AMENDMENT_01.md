# F2-AMENDMENT-01: validator independent-decode center convention fix (2026-09-27)

Named correctness amendment per PROTOCOL.md. No generation rerun; no record,
gate, metric, or decision artifact is modified by this amendment.

## Failure

The frozen validator `scripts/maintenance/validate_f2_structured.py` (SHA256
recorded in freeze.json `sources`) stopped at its line 247 assertion on the
first checked generation (pair 00_24_629, arm N, generation 0):

```
assert d < 1e-3, (row['key'], arm, k, d)
AssertionError: ('00_24_629', 'N', 0, 3.9543162905113007)
```

The failed run wrote no output files: every write in the validator occurs
after the checks, so there are no partial artifacts to retain. This document
retains the failure record.

## Diagnosis (measured)

The validator's independent float64 reimplementation of per-part pose decoding
(`decode_part_poses`) was fed GROUP-convention centers (`centers[0 if k < 3
else 3]`, the anchor-part center of each visit) instead of the per-part
centers returned by `_normalize_parts` and used by the frozen runner's
`decode_parts`. Recomputed on pair 00_24_629 N0:

- group-center convention (buggy): max pose delta 3.9543162905113007 — exactly
  the observed assertion value;
- per-part convention (correct): max pose delta 6.554599266905825e-06, inside
  the 1e-3 tolerance.

The saved artifacts are self-consistent under the per-part convention: both
the runner's generation-time roundtrip assertion and the validator's own
cond/points roundtrip check (which uses per-part centers via
`np.repeat(centers, counts)`) passed for every pair before the failure point.
This is a defect in the validator's independent crosscheck, not in saved
trajectories, poses, scores, gates, or evaluation code.

## Fix

Amended copy `scripts/maintenance/validate_f2_structured_v2.py` (its SHA256 is
recorded in validation.json as `validator_sha256`): the independent per-part
decode now uses per-part centers at both call sites (arm N/F/S pose
crosscheck and the F/S constraint-residual recomputation). Group-convention
centers remain used only where group poses are decoded, matching
`group_coordinates`/`decode_groups`. Tolerances and all other logic unchanged;
`AMENDMENT_01.md` added to the post-manifest exclusion set. The original
frozen validator file is unchanged and its recorded hash identity remains
valid.

## Effect on results

None. The amended crosscheck is an independent numerical confirmation; the
runner's own enforced checks (inputs roundtrip 1e-4, per-pair constraint
residual <= 1e-4, native reproduction delta 0.0, replay delta 0.0) all passed
during generation before this amendment.
