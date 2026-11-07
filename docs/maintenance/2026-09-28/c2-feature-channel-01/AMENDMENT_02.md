# C2 amendment 02 — generation-0 acceptance binding

After amended v2 validation, report review found that `true_accepted`
in the evaluator-only outcomes was copied from F2's selected N/R4 method,
which may select a generation other than0. C2 compares true-feature N0
to shuffled-feature generation0. `true_strict` was correctly recomputed
from N0 pose and GT; all raw/pose response calculations, frozen decision
threshold, bank and POSE_LEVEL_FEATURE_RELIANCE decision are unaffected.
The v2 summary's `true_accepted` counts, and prose based on them, must
not be used as a paired acceptance comparison.

Preserve the original/v2 artifacts. The v3 evaluator-only correction
uses F2's frozen `gates.json[pair][N][0].accepted` for the true N0 arm
and the sealed C2 bank's gate for shuffled Q0. It writes distinct
`outcomes_v3.json` and `summary_v3.json`, retains all28 pairs, all
previous response/strict labels and the original >=6 absolute decision
margin. A separate validator independently checks all28 gate bindings,
GT strict labels, corrected group arithmetic and unchanged decision.
No new inference, points, descriptors, GT convention or method tuning.
Hash-freeze this amendment, original/v2 result identities and v3
sources before writing corrected outputs.
