# Next mainline design: shared map structure before another point-plane sweep

Status: RECOMMENDED_DISTINCT_DESIGN_ONLY. Not a frozen or implemented experiment.
No complete-sequence run or new shared-map optimization follows automatically
from MMR0. The current neighboring point-plane construction is closed as a narrow
zero-of-four declared signal result; its partial aligned-ATE gains remain visible.

## A. The mechanism to test

Represent a static local map feature by a shared plane and its contributing scan
point clusters. For point p from scan i, transformed point x=T_i p has residual
n dot(x-q), where n and q belong to the common map, not one scan's PCA patch.
Estimate all contributing poses and the common plane. The optimal plane can be
eliminated through the minimum eigenvalue of the pooled point covariance. That
specific technique is established BALM prior art, and should be credited rather
than presented as a new RAP mechanism.
[BALM](https://arxiv.org/abs/2209.08854).

Keep compact per-scan point count, mean and second-moment statistics for each
shared patch. Account visibly for highly uneven scan contributions; a repeated
wall observed by many neighboring scans does not provide independent repeated
absolute measurements. Reject tiny/one-scan/nonplanar patches and record rejected
coverage. Do not turn eigenvalue curvature into calibrated covariance.

Use a motion constraint from the corrected frontend, with strength fixed before
its trial. It limits free orientation changes when geometric measurements are
biased. It is an engineering regularizer correlated with the geometric input,
not a proven independent sensor likelihood. Shared-map fitting with such a
constraint is a distinct construction, not a hidden retuning of MMR0 F/R.

## B. Ordered exploratory stages

1. **Shared-surface compatibility.** Start with the existing four exposed windows
   and point identities to isolate the structural change. Construct multi-scan
   plane groups without GT, report spatial coverage, individual scan offsets and
   held-out-scan predictions. Check selected derivatives and exact rigid/gauge
   cases. Inspect whether the new objective still conflicts with the reference;
   reference costs are diagnostic only and never optimize candidate poses.

2. **Small distinct optimizer.** Test common planes and a declared motion
   constraint using the strong E0 initial poses. Use the unchanged initial pose
   as the control and show all R/t, aligned local ATE and independent scan/region
   geometry. Allow at most two declared representation variants on development
   windows, for example patch scale, with every trial retained. This is discovery
   after exposure, not independent validation. Stop this specific design if
   success depends solely on favorable GT-selected memberships or gates.

3. **A real revisit with internal poses.** Use two eight-scan submaps around an
   existing admitted development revisit; initial candidate/measurement identity
   comes from the old GT-blind E0 bank. Retain all internal scan poses and joint
   structure across the two visits. Compare the existing fixed measurement graph
   with direct shared-geometry refinement at the same starting alignment. Do
   not introduce retrieval tuning, oracle edges or new RAP initialization yet.

4. **Whole-sequence mapping test, if warranted.** Develop a sparse or hierarchical
   point-cluster optimization with a fixed correction placement rule. Evaluate
   complete 00/05/06 trajectories, not pasted individually GT-aligned windows.
   This stage needs its own concrete implementation, runtime estimate and frozen
   resource cap. Existing initial paths and official metrics remain the controls.

5. **Incremental RAP value.** Only after the geometry backend is useful, compare
   geometric and RAP alternative initialization under exactly the same shared-map
   refinement on specified difficult revisits. Record added useful recoveries,
   false admissions, cost and trajectory effect. RAP self-consistency is not an
   admission rule, and generation does not become physical point identity.

## C. Proposed system criterion and finite effort

For the future mapping test, use aligned full-sequence ATE as the primary declared
development objective. A draft criterion is mean ATE reduction >=10%, no sequence
ATE regression >5%, mean official ter regression <=0.01 percentage points and no
sequence ter regression >0.02 pp. Display official rer, catastrophic loop events
and measured additional runtime; do not select a favorable metric after outcomes.
These numbers are a reviewable proposal, not a new frozen gate or an amendment to
LC0/PFG/RLP2/MMR0. A pure odometry task would require a different ter-primary test.

The first shared-surface/optimizer discovery stage can be designed under 30 min
CPU, 2 GiB RSS and 512 MiB artifacts using existing NumPy/SciPy. Static feasibility
is not a benchmark or authorization for installations or full-sequence execution.
Reserve complete optimizer replays/seed studies for a promising final method.
Retain failed outputs and correct implementation errors with visible source
binding rather than introducing another large certification workflow.

## D. Details that must be settled before scale-up

- Feature membership must follow observations and be independent of reference GT.
- Nearby surfaces, foreground occlusion and moving objects can share a voxel;
  voxel identity is not plane identity. Check normal separation and scan support.
- Reassociation changes selected support and cost; report coverage, not only a
  smaller objective evaluated on a different selected set.
- All old corrected points and saved trajectories remain unchanged; any new
  preprocessing is an explicitly distinct variant.
- Verify frame/reference-time provenance with available metadata. CT-ICP authors
  distinguish motion-compensated KITTI benchmark scans from timestamped raw
  scans. Do not revive synthesized point-time deskew as an unverified repair.
  [CT-ICP README](https://github.com/jedeschaud/ct_icp/blob/master/readme.md).
- Full sequence optimization must choose how internal corrections affect ordinary
  frames and preserve meaningful odometry evaluation. Existing fixed interpolation
  negatives are not solved by renaming the same interpolation.
- Runtime, actual revisit overlap, sparse optimization scaling and an executable
  GT-blind admission rule are still unknown; no real-time/system-gain claim yet.
