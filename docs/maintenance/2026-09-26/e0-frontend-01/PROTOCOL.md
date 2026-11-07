# E0-V1: bounded frontend alignment development experiment

Owner execution approval: 2026-09-26, following VGGT-SLAM discussion.
Freeze this protocol and runner/source/input identities before new inference.

## Recovered prior exposure

The 2026-09-20 meeting task, absent from the prior maintenance handoff, already
changed uncommitted CLI defaults and ran the combined correction/defaults arm.
Both repositories were on meeting_20260921 at entry, not main. Preserve all
meeting products. This experiment is an explicit development comparison and
engineering reproduction, never a first observation or independent confirmation.
Meeting numbers are not adopted without reevaluation. The original baseline
also used K=1 and NMS=0; the HC table prose claiming K=4/NMS=10 is inconsistent
with its actual frozen run configuration. Use run manifests as authority.

## Fixed arms and inputs

KITTI 00/05/06 complete source IDs 0..4540/2760/1100, respectively; same raw
scans, GT/calibration and corrected evaluation as core-baseline-v1.
Four arms, no additional tuning:

| Arm | 0.205 degree correction | max/min range m | map voxel m |
|---|---|---|---|
| O | off | 80/1.5 | 0.8 |
| A | on | 80/1.5 | 0.8 |
| B | off | 100/0 | 1.0 |
| C | on | 100/0 | 1.0 |

Fresh streaming odometry for all 12 arm/sequence cells. Same real_dataset
correction and KissOdometry implementation as the production pipeline; float32
scan reading/range filtering before optional correction. No deskew or fallback.
OMP/OPENBLAS threads 4; seed 42; no other KISS settings changed. Fixed sequence
order 00/05/06 and arm order O/A/B/C. Save every trajectory and exact frame IDs.
Verify O against frozen odometry (max absolute matrix delta <=1e-5); stop on
failure before selecting a configuration. No GT used by odometry.

## Selection and complete-system check

Primary selection metric: arithmetic sequence mean camera-frame KITTI ter.
Secondary: mean SE(3)-aligned LiDAR ATE. Eligible A/B/C must improve mean ter by
at least 0.02 percentage points versus O, have no sequence ter regression >0.05
points, and mean ATE <=1.10 times O. Choose minimum mean ter, then mean ATE,
then arm alphabetical order. No eligible arm means stop E0 with no successor.

Run the selected arm once per sequence through the full production pipeline,
fresh from raw scans; explicit CLI flags override the meeting defaults.
Retain baseline settings: K=1/five steps, cap 4000 per scan, voxel .4,
seed 42, candidate budget 12, proximity+SC, separation 200, keyframes 6m/12deg,
SC .25/10/20/60/80, overlap >=.7, distance <=2.5m, NMS=0, relfloor+Huber.
This phase tests a frontend configuration, not K4 research registration.
Record all attempted/accepted loop measurements, source IDs and geometry.
Evaluate unaligned/aligned LiDAR APE plus camera ter/rer; never mix frames.

Freeze a development successor config only if all correctness checks pass and
complete-system mean ter and ATE both improve over core-baseline-v1. Preserve
per-sequence regressions and odometry-to-full regressions even if mean improves.
No gate, candidate or PGO tuning. E1 is not executed here. No first-tier claim:
00/05/06 are development; 02/08 have prior research exposure too. Any independent
confirmation needs a separately selected/frozen cohort and exposure accounting.

## Validation, budget and preservation

Source snapshot and SHA256 freeze, raw/GT hashes checked against baseline
manifests; metric code frozen. Exact frame counts, finite SE(3) trajectories,
source IDs, baseline reproduction and independent metric recomputation required.
For full runs check measurement/edge identity and GT labels as evaluator-only
diagnostics; historical safe labels do not imply strict correctness or graph gain.
Caps: 2 hours wall, 20 GiB output, 30 minutes full-system GPU-process wall;
stop on invalid geometry, missing scans, changed sources or resource failure.
One run per cell, no retries to improve results. Correctness fixes need a named
amendment and retained failed outputs. Exclusive output directory; no overwrites.
Branches codex/e0-f1-20260926 retain prior dirty work; a source snapshot, not the
unchanged commit alone, identifies this development baseline. No Git sync.
