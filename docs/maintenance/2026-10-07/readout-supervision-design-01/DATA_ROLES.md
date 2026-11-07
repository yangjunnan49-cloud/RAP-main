# DS0 data roles for one bounded exploratory pilot

These are proposed readout roles, not a claim of new independent data. Exact
204 indices are in WINDOW_MANIFEST_DRAFT.json and are chosen from frame counts,
not GT motion, overlap, model output or error. Fit144:24 per00-05. Development12
on06. Exposed evaluation48:12 per07-10. Three scan IDs[t-1,t,t-2], no shared raw
frame across windows. All frames remain in their sequence role; no neighboring
window random split. Physical site overlap across sequences is unconfirmed.

| Source | Observed availability | Proposed role | Exposure / provenance limit |
|---|---|---|---|
| KITTI00-05 |Raw .bin,poses,calib,times; schema audit in DATA_AUDIT|144 fit windows|00/05 have E0 exposure;02 has historical M3 calibration;01/03/04 cannot be presumed unseen to checkpoint or all old studies|
| KITTI06 |Same sources|12 development windows; no epoch or threshold search|E0 and other diagnostics exposed|
| KITTI07-10 |Same sources|48 readout sequence-held-out, historically exposed evaluation windows|07/09/10 E0 and08 pair studies exposed; not independent confirmation|
| KITTI11-21 |Sequence directories observed; this audit does not process their raw payloads|None|Official GT withheld; not an immediately available supervised/local evaluation role|
| Oxford Spires |Five numeric TUM files; expected scan/calibration directories absent|None now|Incomplete local payload; paper includes Oxford in training; actual local checkpoint/site membership unknown|
| part2 |Immediate entries have no relevant data archive/directory observed|None|Unrelated items excluded; no deeper/content inspection|

The published RAP paper lists KITTI19/22 training scenes and Oxford5/6, and says
KITTI08-10 are excluded from its training. These are publication facts, not a
cryptographic binding of our local344-key checkpoint to that training manifest.
[RAP, training data and split](https://arxiv.org/html/2512.01850v1).
Do not retroactively call Oxford zero-shot or local08-10 confirmed unseen.

Official KITTI provides GT on00-10 and withholds11-21. Its metric documentation
warns about GT error on very short subsequences; these adjacent-frame targets
are particularly unsuitable for claiming millimetre physical accuracy from
GT alone. The proposed small-pilot comparison uses common weak supervision
and common reference poses, discloses that limit, and cannot replace full
100-800m segment ter/rotation and aligned ATE.
[KITTI odometry specification](https://www.cvlibs.net/datasets/kitti/eval_odometry.php).

Oxford GT describes the base frame in world coordinates, not automatically the
LiDAR frame. The existing local loader skips the extrinsic. If T_WB is the
reported pose and X=T_BL is the fixed sensor extrinsic, the LiDAR relative motion
is X^-1(T_WB,i^-1 T_WB,j)X. First-pose anchoring does not generally cancel that
conjugation or its rotation-dependent lever arm. No loader edit or new result
is made here; missing scans/calibration already preclude a current supervised
role. [Oxford official GT convention](https://dynamic.robots.ox.ac.uk/datasets/oxford-spires/).

Use DATA_AUDIT only for file/schema readiness. It reads numeric pose files for
shape/finiteness, retains no pose values, and computes no relative labels/error.
It establishes neither physical GT quality nor point identity. Label-plausibility
preflight, complete bank sealing and independent validation are prerequisites
for a future fit. Missing external confirmation does not prohibit a honestly
declared exploratory master's-thesis pilot, but limits its claims. No new data
acquisition or automatic training authorization follows this role table.
