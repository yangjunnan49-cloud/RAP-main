# E0-H1: held-out-system confirmation of the frozen E0 frontend

Owner authorized the post-F2 action plan on 2026-09-27. This protocol is to
be hashed with all execution code and inputs before any E0-H1 trajectory is
generated. It tests whether E0's fixed arm A transfers beyond its selection
sequences. It does not create a new configuration or a novel RAP algorithm.

## Exposure and fixed cohort

Use complete KITTI odometry sequences 07 (1101 frames), 09 (1591), 10 (1201),
source IDs from zero to the listed count minus one at stride one. All raw
velodyne scans, camera GT pose files, calibration and timestamps are frozen.
These sequences did not participate in E0's 00/05/06 arm selection or in an
RAP-SLAM full-system outcome in the recorded project. They are **not fully
unseen data**: 07/10 were used in the SC-V1 data/old-odometry feasibility
screen and 09 in the PG-V1 data screen. All are KITTI, and pretrained RAP
checkpoint membership is unresolved. Do not call this independent training-
domain or novel-method confirmation. No resampling, sequence exclusion,
new query cohort, or inspection-based replacement is allowed.

## Frozen methods

For each sequence run full RAP-SLAM O and A, same input and all identical
settings except E0's 0.205 degree vertical correction: O off, A on. Both use
max/min range 80/1.5 m, odometry voxel 0.8 m, keyframe 6m/12deg,
proximity+SC, candidate budget 12, K1/five RAP steps, 4000 points, seed 42,
overlap>=0.7 and mean_dist<=2.5m, NMS0, relfloor+Huber. Use the exact
`command-00.json` E0 command with only sequence, end ID, correction flag and
exclusive output path substituted. Run order per sequence O then A, sequence
order 07/09/10, without adaptive retries. Do not change RAP-SLAM source.

As an external context, run installed KISS-SLAM 0.0.2 with its unmodified
defaults on exactly the same three sequences, using the HC-V1 environment
and command convention. It is a pipeline comparison, not a controlled
component ablation; record version/config identities and runtime. Evaluate
its camera poses in the same metric code/conventions as HC-V1.

## Metrics and prospective reading

Primary: full-system camera KITTI ter (%) and SE(3)-aligned LiDAR ATE (m),
reported for each sequence and arithmetic mean over all three. Also report
rer, unaligned APE, odometry-versus-PGO differences, accepted loop counts,
strict correct/incorrect accepted loop labels (evaluator-only), and runtime.
E0-A transfer is supported only if its mean full-system ter improves over O
by >=0.02 percentage points, mean aligned ATE is lower than O, and no
sequence ter regression exceeds 0.05 percentage points. Otherwise report
NO_HELDOUT_TRANSFER under this rule; no configuration selection follows.
KISS-SLAM is reported side by side without tuning or a post-hoc eligibility
rule. Do not hide sequences with no useful loop closures. No first-tier claim
is inferred from this three-sequence check alone.

## Freeze, execution and validation

Before runs, hash the protocol, runner/validator, E0 development baseline
and source freeze, all three sequences' raw files, GT, calibration, times,
current RAP-SLAM/RAP source and checkpoints. Verify current algorithmic
source hashes equal the E0 freeze (excluding E0's old orchestration files).
Record installed KISS default config and package identity. Preserve a source
snapshot or hash manifest. Each run has an exclusive directory and durable
log; never overwrite E0, HC-V1 or F2 artifacts. GT must not enter loop
proposal/scoring/optimization; evaluator labels are computed only after the
trajectory/edge outputs exist.

Independent validation checks frozen identities, exact frame/source IDs,
finite SE(3), actual config flags, measurement/edge identity, GT-free
algorithm fields, independent metric recomputation and decision arithmetic.
The validator must stop on any mismatch and retain INCOMPLETE. Budget: one
RTX 5070, no concurrent GPU inference, total process wall <=2 hours,
new artifacts <=20 GiB, no network or source/production change. If KISS
environment or all required data are unavailable, report INCONCLUSIVE_SETUP
without silently dropping the comparator.
