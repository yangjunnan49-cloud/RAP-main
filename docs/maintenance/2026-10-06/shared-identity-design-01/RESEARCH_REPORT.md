# Shared-input identity feedback: design audit

Date:2026-10-06. Owner-authorized research and planning before execution.
Decision: SINGLE_SHARED_SCAN_DESIGN_REJECTED; TWO_SHARED_SCAN_FEEDBACK_CONDITIONAL.
This is a mathematical/source/literature assessment, not a validated experiment.
LMF1 remains the latest experimental result: NO_CAUSAL_LOCAL_MOTION_SIGNAL.

## Main conclusion

The conversational proposal needs two corrections. Sharing one rigid scan
between independent, unanchored registration windows only connects coordinate
gauges; it does not constrain their other relative poses. Synchronizing
overlapping generators, including their predicted clean endpoints, also has
strong prior art. The broad description supplies neither a sufficient
candidate-creation operation nor an originality argument.

Retain only a conditional construction: different context windows both contain
the same two anchors; at every native flow step, jointly fit their raw clean
predictions to one rigid pose per physical scan, estimate the window gauges,
return the constrained points to each window, then reevaluate the frozen model.
The hypothesis is whether feedback creates correct cross-visit candidates
unavailable from the same uncoupled windows with the identical final-only fit.

This adds no sensor observation or known cross-visit point correspondence.
It exposes conditional predictions to one another, and can synchronize a wrong
solution, average incompatible modes, or do nothing. No effectiveness,
originality, confidence calibration or trajectory gain is established. A
bounded search found no verified exact RAP implementation of this full
operator; absence from the search is not novelty clearance.
See [primary sources](PRIOR_ART.md) and [the staged plan](PLAN.md).

## Existing evidence and stops

| Evidence | Implication |
| --- | --- |
| LMF1 complete58 local windows: all primary material comparisons fail; nine/18 safety conjunctions fail | Stop native consecutive-three-scan motion before trajectory. R3/G3/KISS median translation0.094945/0.078036/0.018766m; KISS has a larger map, but matched G3 also defeats the material claim. |
| F2 per-step projection using saved within-visit odometry fails | Projection inside flow and fixed-noise reconstruction are already implemented; changing timing alone is no new construction. |
| M1 support transport recovers four strict/two interior hard08 cases, below five/three gates | Do not reuse this failed candidate bank for a selector or choose favorable part pairs. |
| FDI1 joint response fails uniqueness/00 safety; rigid-wrong2m has zero response | Agreement, rigidity and low response do not certify truth, calibrated uncertainty or graph usefulness. |
| Joint58-loop GT replacement has exposed-transfer ATE opportunity only, without mean-ter material gain | Better pair poses do not promise ter improvement; official09 physical discrepancy and official GT/labels persist. |

The immutable source reports are bound in SOURCE_AUDIT.json. No old GT or
scores were reevaluated here. All other negative stops remain.

## Correct meaning of identity

Use "same frozen processed-input array and row identity", not "raw LiDAR
return correspondence". Preprocessing voxelizes, removes outliers and caps
points; retained points can be voxel centroids. Different scans/visits have
no point-identity correspondence here.

RAPBackend.preprocess, rap_backend.py lines144-154, uses a seeded cap.
Cap1000 need not be a subset of cap2000. MiniSpinNet patch processing also
shuffles support points, so repeated extraction can change descriptors.
Within a comparison pair, obtain each unique scan's points/features once and
reuse identical arrays and row order in every window/control.

Both copies of each proposed anchor retain2000 points; supports retain1000.
F2 saved points and corresponding C1 descriptors are prospective cache
sources: C2 lines193-216 already verified their reconstruction. That prior
binding is not a newly performed cache validation. Future source checks must
bind actual hashes, raw scan identity, cap, recipe, feature seed and row IDs.
Cache identity includes the parent pair/bank: legacy features for the same
scan need not be identical across different pairs.

## Proposed metric operator

Let p_ij be the cached metric point of scan i and window w have native center
c_wi and known scale s_w:

$$q_{wij}=(p_{ij}-c_{wi})/s_w,\qquad y_{wij}=x_{wij}(t)-t\,v_{wij}(t).$$

Y_wij=s_w y_wij is the metric generated coordinate in the window frame.
Do not add c_wi to this generated output. A normalized rigid fit (R,tau)
decodes a physical pose with translation s_w tau - R c_wi.

G_w maps a window metric output frame to the common frame; Z_i maps original
scan coordinates to that frame. Propose:

$$
\min_{\{G_w,Z_i\}\subset SE(3),\,G_L=I}
\sum_{w,i\in W_w}\frac{1}{d_i n_i}
\sum_{j=1}^{n_i}\|G_wY_{wij}-Z_ip_{ij}\|^2 .
$$

d_i counts window copies; each unique scan has fixed total weight. This
point-space objective is not calibrated covariance or sensor likelihood.

Return clean endpoints and reconstruct the native next state:

$$
\widetilde y_{wij}=s_w^{-1}G_w^{-1}Z_ip_{ij},\qquad
x_{wij}(t-\Delta t)=(1-t+\Delta t)\widetilde y_{wij}
 +(t-\Delta t)\xi_{wij}.
$$

Then reevaluate the model. Fix only G_L=I: also hard fixing an anchor pose
adds a constraint rather than simply removing gauge. No odometry, GT or
cross-visit pose enters this operator. PLAN.md specifies a prospective
alternating proper-Kabsch solver; global optimum is not asserted.

After independent per-part rigidification, duplicate point constraints reduce
to agreement of shared SE(3) poses. Direct joint fitting to raw endpoints
also uses point means/cross-covariances, so it is not generally identical to
unweighted six-parameter pose averaging. It still creates no new physical match.

## Identifiability and counterexamples

For two windows sharing only A, let T_wi be their independent best rigid fits.
Choose G_w=Z_A T_wA^-1 and for unique scans Z_i=G_w T_wi. All factors attain
their independent minimum with arbitrary within-window relative predictions.
Returning to local coordinates recovers the native per-part projection.
Nonrigid raw residuals do not alter this proof: rigid left transforms preserve
the minimum residual. Thus the single-shared-scan design is rejected before GPU.

The same construction propagates through a tree of window-scan incidences.
Connectedness permits a common gauge; cycles supply repeated relative-relation
constraints. Two different shared scans A,B create the smallest four-cycle
and compare T_wA^-1 T_wB. Different nonshared contexts are needed; duplicate
contexts are only an ensemble. A cycle is necessary, not proof of useful
information or truth.

Known point identities with at least three noncollinear points (centered
covariance rank>=2) identify a proper rigid transform. Planar clouds are not
automatically degenerate. Coincident/collinear parts leave freedoms and must
fail explicitly instead of silently choosing a transform.

For any incorrect but consistent pose set Z_i_wrong, choose
Y_wij=G_w^-1 Z_i_wrong p_ij. Shared residual is zero, yet the anchor relative
pose can be wrong by2m. Repetitive geometry can produce this common alias.
The identity edges do not connect A's points to B's surfaces, so the operator
has no independent physical evidence to reject that solution.

A common left rigid transform of all Z_i is merely gauge and cancels from
Z_A^-1 Z_B; do not confuse gauge movement with relative-pose error.

Projection and nonlinear flow need not commute. Repeated projection followed
by new model evaluation may differ from terminal projection. This supplies a
computational hypothesis, not an accuracy theorem. It must affect subsequent
raw predictions and relative poses, not only a coordinate frame. Final-only
generalized Procrustes is the indispensable direct control.

## Source feasibility and claim boundary

Sampler.py lines56-60 already rigidifies raw clean endpoints and reconstructs
with original noise. Procrustes.py lines86-119 independently fits each part.
F2 structured_motion.py lines62-82 already reevaluates after group projection.
An isolated research wrapper can reuse frozen velocity calls without hooks,
monkeypatches or production sampler edits.

The proposed primary noise is independently drawn per window instance once,
retained throughout, and identical across C/I/F. Never dynamically rotate,
translate, rescale or average noise. Equal clean predictions do not imply
equal noisy states. Shared Gaussian rows are another correlation design, not
the chosen primary strategy or an available post-hoc rescue.

Axis-dependent positional embeddings prevent assuming exact SE(3) equivariance
of the network. The projector's gauge identities are separate from learned
model behavior. Strict safe344/58-key loading remains a verified dependency;
the local12-layer training split is unknown, and official10-layer recipe or
new held-out claims cannot be inferred.

Rejected: one shared scan/tree-only correction; enforced agreement as a truth
score; broad "synchronized generation" novelty; old point/seed/window/weight
rescue. Conditional: cycle-bearing unknown-gauge rigid-input feedback,
against identical terminal synchronization and native complete context.
This is admitted only for a future bounded equation/implementation audit,
not as an original thesis method.

Before efficacy, write the exact domain-specific construction and its reduction
to the nearest precedents. A standard-method migration cannot substitute for
the owner's original-breakthrough requirement. Neither success nor novelty is
promised; that requirement remains open.

No new synthetic/real experiment, protocol freeze, bank, GT computation,
trajectory, training, production/default/model/manuscript edit, dependency
installation, source/checkpoint download, commit or Git sync occurred here.
