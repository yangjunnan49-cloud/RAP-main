# Amendment 01: native pose serialization before retry

The first frozen engineering bank stopped on its first00 J row at the exact
`pose` assertion against TR0. The writer used `solve(parts[0],parts[1])`; the
native saved TR0 pose uses `inv(parts[0]) @ parts[1]`. Raw inputs, descriptors,
noise, normalization, part fits and generated state/endpoints passed the
preceding exact checks. Different floating evaluation of the same matrix
relation is incompatible with the required byte-exact native replay.

Preserve the original runner/validator/common/helper, original engineering
freeze and INCOMPLETE, empty original bank directory, failure record and failed
resource accounting. No GT labels or fitting occurred. This is a writer
serialization defect, not a joint-context or accuracy result.

New rlp1_engineering_v2.py and validate_rlp1_engineering_v2.py use a separate
engineering-preflight/attempt-02 freeze/output. The writer restores native
inv(parts0)@parts1 serialization. Independent Horn reconstruction still uses
solve and the unchanged1e-8 tolerance. No model, input/window/seed/grouping,
sampling/gate/tolerance or scientific setting changes. Retry all four rows;
do not edit an original bank or call the failed original valid evidence.

The already approved repair-disclosure scope permits this implementation-only
correction. All failed and retry compute count toward the original60-minute cap.
