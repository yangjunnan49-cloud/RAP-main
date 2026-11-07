# Continued breakthrough search: structured motion constraints during generation

2026-09-15. The owner explicitly rejected thesis scope convergence and requires
continued algorithmic breakthrough research. This supersedes the previous
scope-convergence recommendation, not any measured negative result. No promise
of a positive result or publication readiness is made.

## 1. Revised reasoning

The failed fixed distance selector, pooled proposal generation and consistency
diagnosis delimit specific routes. They do not justify ending the research
program or treating every richer observation representation as disproved. The
earlier suggestion to stop at thesis convergence did not meet the owner's
requirement. Continue with bounded mechanism tests and move between genuinely
different hypotheses when evidence warrants it.

The latest primary wrong accepts have no correct candidate among four repeated
generations. This motivates improving the generated pose, not only selecting
among existing poses. It does not establish model bias as the cause. Correct
pose rejection is a separate limitation; it must remain visible in every report.

## 2. Candidate comparison

| Candidate | New question relative to completed work | Main risk | Current priority |
|---|---|---|---|
| Structured short-motion constraints inside multiview generation | Does preserving scan-specific conditioning while coupling each visit's poses improve the generated cross-visit transform? | May be little better than pooling; short-motion error and off-distribution projected states | First feasibility study |
| Visibility-aware acceptance | Can a physically observed common region separate missing observations from conflicting observations? | Known idea, sensor/dynamic handling and dangerous-negative evidence still needed | Retain as separate unselected candidate |
| Small geometric residual adapter | Can point-level evidence correct shared pose error beyond fixed ICP? | Data/training cost; no evidence yet for a learnable transferable residual | Retain; needs a distinct training annex |

Do not run all three or train a head because the old score failed. The first
candidate has a specific source-level intervention that can be tested without
training or new downloads. Small adaptation remains possible in a later explicit
study; the prior selector's training stop is not a ban on every future model.

## 3. Literature boundary, checked 2026-09-15

This is a focused primary-source search, not an exhaustive novelty clearance.

- [Register Any Point](https://arxiv.org/html/2512.01850v1) already provides
  multiview generation, per-cloud rigid forcing and rigidity selection. Native
  multiview RAP alone is not a contribution.
- [Rectified Point Flow](https://rectified-pointflow.github.io/) already uses
  conditional point generation followed by rigid pose recovery. The Kabsch
  projection itself is established machinery.
- [FUSER author repository](https://github.com/Jiang-HB/FUSER) describes joint
  multiview pose estimation and SE(3)^N diffusion refinement. Generic joint
  generation plus refinement is not a sufficient distinction. This review used
  the author repository, not a full method-equivalence audit of its paper/code.
- [Multiway Point Cloud Mosaicking](https://openaccess.thecvf.com/content/CVPR2024/html/Jin_Multiway_Point_Cloud_Mosaicking_with_Diffusion_and_Global_Optimization_CVPR_2024_paper.html)
  combines learned pairwise registration with global pose optimization. Global
  consistency after registration is already established; only its primary
  abstract was available in this search, not a complete equivalence audit.
- [Huber and Hebert, 2001](https://www.cs.cmu.edu/~dhuber/papers/cvbvs2001.pdf)
  discusses visibility consistency and free-space violations. Visibility by
  itself is not a new contribution; full-text comparison remains necessary if
  that alternate route is selected.

The specific potential distinction to investigate is **using short, causal,
within-visit relative motion as a constraint on the clean pose estimate at each
generation step while retaining scan-specific conditioning**. Do not claim no
prior method does this. A closer paper/code audit is required before novelty
claims or an expensive campaign. Projected generative inference is also an
established general pattern; the application needs measurable causal value.

## 4. Concrete mechanism

For each of two visits g, keep three scans as separate parts: the anchor and its
two existing past support scans. Let L_gk map support scan k into that visit's
anchor frame, from saved local LiDAR odometry; L_g0=I. Do not use the accumulated
odometry transform across visits, GNSS or ground truth in generation.

Native multiview RAP predicts each part's clean points independently subject to
its own rigid fit. The proposal instead requires part poses to satisfy

    T_gk = G_g L_gk,
    T_loop = inverse(G_0) G_1.

For each predicted clean endpoint Y_gk at a sampling step, fit one proper rigid
transform per visit by minimizing the point-index-preserving sum

    sum_k sum_p || G_g (L_gk p) - Y_gk(p) ||^2.

These correspondences are between an input point and its own predicted endpoint,
not nearest-neighbor matches across visits. Use the resulting projected clean
points in the next noisy interpolation. Do not directly force noisy x_t itself
to be a rigid cloud. This is a constrained sampler hypothesis, not a claim to
sample the exact conditional posterior.

There are six input parts for local features/part attention but two motion
groups for the projection. Local scan normalization must be inverted before
applying L_gk. With scale s and visit center c_g, use q=(L_gk p-c_g)/s; a fitted
normalized pose (R,t) yields physical G=(R, s*t-R*c_g). Global output gauge
cancels in inverse(G_0)G_1. No world-frame truth is required.

**Important limitation:** the least-squares group projection is algebraically
a rigid fit of the corresponding pooled points. Its novelty cannot be the
projection alone. The testable difference from PG is preserving each scan's
feature/attention partition and imposing its local coupling repeatedly during
generation. If those choices provide no benefit beyond pooling or final-only
projection, this candidate fails its rationale.

Local motion is estimated, not exact. Hard constraints are a first mechanism
probe; they can encode motion error and dynamics. Sensitivity must be measured,
and a later soft constraint would be a separately specified method, not an
automatic strength sweep after a failed hard constraint.

## 5. Source feasibility and pitfalls

Read-only source inspection found:

- `sampler.py:flow_sampler` calls per-part rigid projection after predicting a
  clean endpoint at every Euler step. This is the intervention location.
- `layer.py` has separate part and global attention; six-part conditioning is
  not the same network execution as two pooled parts, even at equal point count.
- `rap_backend.py:register_multi` already prepares multiview batches, but caps
  points per scan. A six-scan experiment must explicitly enforce a total cap;
  multiplying the usual4000 by six would invalidate an equal-point comparison.
- `modeling.py:sample_rectified_flow` returns saved endpoint trajectories, which
  are recorded before projection. A new implementation must explicitly record
  raw and projected endpoints, declare which is decoded, and include final-only
  projection as a control. Otherwise an apparent gain may only be output repair.
- The anchor embedding does not mean hard world anchoring in the active Euler
  sampler. Maintain its gauge-free behavior and recover the relative pose.

Implement any eventual experimental sampler in RAP-SLAM with request-local
state and protected rigid fits. RAP-main inference/model files remain read-only.
Do not use a process-global hook while concurrent registrations could run.

## 6. Bounded next execution stages

### F0: equation and source feasibility (this turn)

Audit scale/centering, nontrivial transforms, within-group relative poses,
permutation, common-gauge invariance and single-part reduction on synthetic
data. This checks equations only, not the model, memory use or hypothesis.
Persist a source snapshot identity. No RAP output or new cohort is generated.

### F1: engineering preflight (next)

Before GPU execution, freeze a dedicated preflight protocol and implementation.
Use a fixed small subset from saved00 inputs chosen by stored order with explicit
stratum coverage; record exact IDs rather than choose successes. Preserve scan
IDs and the same raw points for six-part arms. Start with K=1, five Euler calls,
total8000 retained points: each anchor2000 and each support1000. Stop if any scan
cannot supply its allocation; do not duplicate or silently change the budget.
No point-density tuning from outcomes.

Compare native six-part inference, native plus final-only group projection, and
group projection at each step, using identical noise/points/normalization for
those arms. A two-pooled-part arm using those exact points is required to isolate
conditioning structure. Include an anchor-only reference and later KISS-Matcher
as a substantive external comparator. Original PG is a historical reference;
its preprocessing differs from the matched-point pooled control here.

Initially check only correct execution, shape/point budgets, numerical rigidity,
local-motion constraint residual, no cross-visit prior/GT access, disabled-hook
reproduction, elapsed time and peak memory. Do not infer efficacy from a few
preflight examples. Target one5070, <=12GiB allocated and <=30 GPU minutes for
the engineering preflight; no resource guarantee before measurement.

### F2: full development mechanism screen (conditional)

Only after engineering feasibility, freeze exact methods, K4 seeds, common
anchor-only gate, cost accounting, both existing100-pair cohorts and decision
rules BEFORE real method outcome inspection. Use all strata, no replacement
of unfavorable cases. Declare the scoring residual consistently across arms;
do not let forced low constraint residual become a confidence certificate.
Compare per-step versus final-only versus unconstrained multiview versus matched
pooling, and anchor-only RAP. Measure strict pose recall, clipped error, correct
accept coverage and incorrect accepts separately. Oracle is diagnostic only.

The prospective annex must specify useful improvement margins and tolerable
regressions for this different question. Do not copy PG's oracle-headroom gate
uncritically or replace failed gates after results. Include fixed local-motion
perturbations as sensitivity controls, not parameter tuning. Fresh confirmation
and strong comparators are required after a credible development signal.

F1/F2 are not reported as implemented or complete. No new training or full real
experiment is started in this memo. The next authorized work is bounded F1
preparation under the owner's renewed breakthrough instruction. A failed branch
ends that branch, not the requirement to continue seeking a viable contribution.
