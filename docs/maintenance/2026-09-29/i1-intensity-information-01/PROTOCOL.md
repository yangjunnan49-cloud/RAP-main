# I1: fixed cross-visit LiDAR intensity information audit

I0 established only a raw-intensity-to-saved-anchor binding. I1 asks whether
intensity of *geometrically corresponding* anchor points is more consistent
than a range-matched assignment control on the exact F2 observed-development
cohort. This is a diagnostic, not executable matching or a method gain.
Intensity-assisted LiDAR loop methods already exist (e.g.
[Intensity Scan Context](https://arxiv.org/abs/2003.05656)); no novelty is
inferred from a positive information test.

## Inputs and bank separation

Use all saved-order F2 pairs, 100 each on KITTI00/08, and only their two
unchanged 2000-point anchors (part0 target, part3 source). For each raw anchor
scan, verify the frozen SHA/size, parse float32 XYZI, retain range>=1.5m,
apply the saved +0.205-degree KITTI vertical correction to XYZ, then assign
to every saved F2 anchor point the intensity of its nearest corrected raw
point. Save target/source intensity and nearest-distance arrays per pair.
The assignment uses no GT, other pair, model feature, or evaluator label.

Before real bank generation, freeze this protocol, runner, separate validator,
correction source, F2 point archives, input metadata, every referenced raw
anchor scan, C1 pair/validation files, and evaluator GT/label identities.
Those evaluator files may be hashed for identity but not parsed before the
**complete 200-pair intensity bank** and its manifest are SHA-sealed. Leave
`INCOMPLETE` on partial work. Binding adequacy requires >=95% of assigned
points within0.5m and >=8 distinct intensity values in *every* anchor scan.
Failure yields `INCONCLUSIVE_INTENSITY_BINDING` without efficacy selection.

## Fixed evaluator and control

Use C1's exact source-to-target pose `inv(GT_i) @ GT_j` and cKDTree float64
nearest target point. Eligible source points have geometric nearest distance
<=1.0m. With saved assigned intensity values in the raw [0,1] scale, compute
the mean absolute target-source intensity difference over eligible points.
Zero-eligible pairs have null differences. For each pair, make 16 deterministic
controls by shuffling *target* intensity among target points within the
fixed sensor-range bins `[0,20),[20,40),[40,60),[60,80),[80,inf)` meters.
Seed each PCG64 permutation with the first 16 hex digits of
`SHA256("I1|{pair}|{k}")`, k=0..15. Source intensity, geometry and eligible
indices remain fixed. Pair advantage is mean(control mean absolute
difference) minus true mean absolute difference; positive is informative.
Report all pairs, all16 controls, sequence, stratum, native K4 candidate
availability and coverage. No threshold, bin or score fitting.

Primary group is the same 08 positive native-K4-unavailable pairs with >=10%
geometrically eligible source points as C1 (33 known pairs). Use **pair** as
the sampling unit. `INTENSITY_INFORMATION_SIGNAL` requires binding adequacy,
>=20 primary pairs, median pair advantage >=0.03 on [0,1] intensity, and
positive advantage on >=2/3 of primary pairs. If support is below20, decide
`INCONCLUSIVE_CORRESPONDENCE_SUPPORT`; otherwise failing an effect condition
is `NO_INTENSITY_INFORMATION_SIGNAL`. Report 00 and available groups as
secondary. A positive result permits only a separately frozen constructive
candidate mechanism with a matched geometry-only comparator, fixed common
gate and safety stops. A negative result stops this exact intensity proxy;
no range-bin, raw-assignment or threshold sweep.

Bank wall cap 10min, peak RSS cap2GiB, artifacts cap100MB. The validator
independently rehashes identities and all200 assignments, recomputes all
pair metrics/controls and the decision. No GPU, training, model/default edit,
earlier product overwrite, or Git synchronization.
