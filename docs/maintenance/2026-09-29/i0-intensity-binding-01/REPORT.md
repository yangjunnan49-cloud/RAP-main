# I0 raw LiDAR intensity binding preflight — complete

Decision: **PASS_INTENSITY_BINDING_PREFLIGHT**. The exact first four saved F2
pairs per sequence (00/08) and their two anchors each were fixed in
[PROTOCOL.md](PROTOCOL.md). Thirty source/input identities were SHA-frozen
before reading the real intensities. The GT-free 16-row bank was SHA-sealed;
separate recomputation passed 165 checks. Bank wall was 0.531s and artifacts
13,027 bytes, within those caps. Peak RSS was not instrumented, so the 2GiB
cap is unverified; the preflight result does not depend on a memory claim.

Every one of the 16 saved 2000-point anchors had **100%** of points within
0.5m of a vertically corrected original raw scan point. The largest
per-scan nearest-distance median was 0.033m and largest p95 was 0.136m.
Assigned anchor intensities were finite, within the raw scan's roughly
0–1 range, and every scan had at least 67 distinct values. Thus the
existing F2 points can be linked to the unused raw intensity channel
without changing the points or RAP model for a diagnostic audit.

The sample was selected by saved order, not labels. I0 did not read GT,
evaluator labels, C1 descriptors or model checkpoints, and it did not
evaluate cross-visit repeatability, correspondence, pose creation, or a
registration metric. Nearest raw intensity at a voxel centroid is a proxy;
local mixed-surface voxels could still limit it. Prior work already uses
LiDAR intensity for loop detection, including
[Intensity Scan Context](https://arxiv.org/abs/2003.05656) and
[intensity-image segment descriptors](https://arxiv.org/abs/2108.01383).
This is input feasibility, not an originality or efficacy signal.

Next boundary: separately freeze one matched cross-visit intensity-
information audit on fixed F2 anchors. Keep anchor coordinates and the
exact C1 1m geometric correspondence definition, seal intensity assignment
before evaluator GT, compare true geometric pairs with a range-matched
intensity shuffle, and predeclare pair-level margin, costs and an independent
validator. Do not train, alter model inputs or claim a method from I0.
All C1–C6 stops and E0 engineering reference persist. No defaults or Git
state changed.
