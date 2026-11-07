# Causal local-motion source engineering feasibility

Decision: **PASS_CAUSAL_LOCAL_MOTION_FEASIBILITY** for the separately frozen
attempt-02 retry. Independent geometry validation and supplementary raw-input
binding validation both pass. No GT error, registration accuracy improvement,
trajectory gain or original RAP construction has been established.

## Scope and executed input

After explicit owner restart, both original269 and retry275 frozen identities
were checked exactly. A WSL process inventory confirmed no prior study process.
The first approval-service call was not executed because its review model was
at capacity; a normally approved read-only retry succeeded. No approval bypass.
Termination records remain preserved in owner-terminated-status.json and the
retry's corresponding snapshot; RESUME_RECORD.json records the new authorization.

The fixed-index census has58 windows on exposed00/05/06/07/09/10:
22/13/5/5/7/6 respectively. t=0,200,400,... selects anchors without GT ranking;
each sequence's t=0 is excluded for lack of two past scans, shared by all arms.
Engineering inference uses only t=200 per sequence, input order[199,200,198],
individual unposed LiDAR coordinates. No future scan, GT pose or KISS-derived
local-motion constraint enters RAP. All sequences are already exposed development
data; the exact local12-layer weight training membership remains unknown.

R3 uses native three-part RAP,1000 points/scan (3000 total), K1/five Euler steps,
per-part rigidity forcing. R2 uses the same first two point/feature blocks and
first2000 noise rows; it has lower compute and physical context. Geometry G3
gets the same three scans and3000 unique points as R3: independently register
oldest to previous, pool those2000 points, then register current1000 initialized
by G2. G2 uses only the two adjacent scans. Both use fixed identity-initialized
point-to-point ICP,3m gate,30-step limit and fixed convergence. No parameter sweep.
These are isolated maintenance helpers; production SLAM/model sources were not
edited. The later saved dense-map KISS reference is not an equal-input ablation.

## Loading and convention evidence

The exact F2 RAP SHA is
0c5b9f20ee4dfe2345c3cd47dd0632a3d807a3da69c7653900a755cd06564200.
C2's explicit reviewed OmegaConf/NumPy allowlist is used with weights_only=True,
fixed serialized-global checks and no unrestricted fallback. Only state_dict is
applied; checkpoint metadata config/RNG/optimizer are discarded. All344 RAP and
58 miniSpinNet expected keys, shapes, dtypes and finite tensors match, and both
load strict=True. This establishes local weight/model compatibility, not training
provenance or official paper reproduction.

Twelve analytic cases cover six input permutations, nontrivial transforms,
center/scale changes and common registered-frame gauges; a separate known ICP
case checks support transport. Independent Horn-quaternion fits and direct
normalization reproduce these and every local pose. Maximum known-transform
error is4.178e-8; maximum independent pose/control discrepancy5.462e-14.
Synthetic controls verify algebra; they do not prove learned order/rotation
invariance. Axis-dependent max normalization and global-z features have limits.
Census paths/times/IDs and future/duplicate/order rejection checks pass.

First original F2 N0 in00 and08 reproduce both raw and noisy trajectories
byte-exact, maximum delta0. All six complete seeded local pipelines repeat
exactly, including points/features/noise/R2/R3 endpoints and decoded/control
poses. For both RAP arms on every local window, arbitrary finite replacement
of pointclouds_gt leaves generation byte-exact. All decoded rotations are proper
and raw/state arrays finite. Inputs, features, noise, endpoints and poses were
sealed in a21-NPZ bank before the independent validator.

A separately frozen supplementary GT-free audit independently reconstructs all
18 raw scans using direct coordinate correction and Open3D preprocessing, then
calls miniSpinNet directly after strict safe loading. All18000 points,
576000 descriptor values and18000 noise rows match exactly. This avoids relying
solely on repeated execution of the same source loader. It was added after the
GT-free bank; it is engineering verification, not prospective accuracy evidence.

## Failure history and cost

Original attempt froze269 identities, saved12 synthetic cases, one synthetic ICP
case and two exact native replays, then stopped during the first local repeat:
Python scalar scale does not provide `.max()`. No local NPZ, complete bank/seal,
GT result or primary independent validation was produced by that attempt.
Original code/freeze/15 partial NPZ files and INCOMPLETE remain untouched.
AMENDMENT_01.md and FAILURE_01.json disclose the issue. V2 changes only scalar
aggregation to np.max and its output directory, with separately frozen275
identities. The previous owner pause/termination happened before retry inference;
this continuation begins from that unchanged freeze.

Successful retry bank24.052s, full primary validator6.200s, source supplement
7.329s: total37.580s. GPU allocated peak1.388GiB; RSS peak2.647GiB. All study
artifacts before reports10,581,362 bytes. Original1200s/12GiB-GPU/4GiB-RSS/100MB
caps pass. Primary validation.json sampled its total before the final identity
recheck; source_binding_validation.json uses its full recorded validator duration
and is the combined successful-stage cost reference. Earlier failed attempt
duration was not completely persisted;37.580s is not all-attempt cost.

Root INCOMPLETE belongs to the preserved failed original attempt; the validated
retry has its own seal/validation in attempt-02 and its INCOMPLETE is removed only
on finalization. Current root status points explicitly to that retry. Do not use
the original partial bank as a completed experiment.

## Consequence

The engineering path is ready for a separately frozen local-accuracy question
on the complete fixed58-window census, as specified in NEXT_ROUND_PLAN.md.
No such accuracy protocol, evaluator, freeze, complete58-window generation or
GT computation exists yet. No full trajectory rerun is licensed by executability
alone. Native multi-frame RAP and generic multi-scan estimation are prior art;
an original construction still requires additional evidence. The owner's
breakthrough requirement remains unresolved.

All old negative stops, official GT/strict labels/ter/rer/ATE and completed banks
remain. No training, download, environment installation, production/default or
manuscript edit, commit or Git sync. Original HEADs4055d92/6d3f2d2 and branches
codex/meeting-20260930 / codex/e0-f1-20260926, including dirty work, are preserved.
