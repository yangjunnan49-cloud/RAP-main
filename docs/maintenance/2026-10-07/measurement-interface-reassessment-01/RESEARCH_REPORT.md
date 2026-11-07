# Research reassessment: from generated geometry to physical measurements

Date: 2026-10-07 (Asia/Shanghai). Status: READ_ONLY_RESEARCH_COMPLETE;
all proposed methods and experiments are CONDITIONAL_UNTESTED.

The owner requested context recovery, brainstorming, primary-source research
and a practical plan that connects a RAP-specific contribution with trajectory
improvement. This turn inspected records and source and searched primary
literature. It ran no model, synthetic experiment, evaluator, graph replay or
new data/feature computation. This document is a research memo, not a frozen
experimental protocol or a positive result.

## Decision

Prioritize one new question: **does the final, pre-rigidification point output
of frozen RAP contain cross-visit association information that is lost when
each scan is independently decoded into a pose?** Use generated coordinates
to propose associations, then estimate the relative pose from the associated
original measured points. Keep this hypothesis conditional: an association
derived from an incorrect generated scene can also be wrong.

Keep the graph measurement model as a separate, bounded engineering question.
Source confirms that aggregated keyframe odometry receives one constant noise
model and loop measurements are complete Pose3 factors. Neither choice is
proven to cause regression. A successful graph change alone would not meet
the owner's original RAP contribution requirement.

The recommendation is a changed measurement interface, rather than another
attempt to make generated windows agree. Novelty is NOT_ESTABLISHED. Generic
correspondence generation, robust fitting, partial constraints and bundle
adjustment have strong prior art. The proposed distinction needs a direct
counterfactual and an actual metric benefit.

## What the evidence establishes

| Evidence | Consequence | Limit |
| --- | --- | --- |
| F2/M1: 41 hard08 positives lack a strict native K4 pose; 37 have a best candidate within the rotation tolerance but outside the translation tolerance | Creating additional translations matters more than choosing another existing candidate on that cohort | This balanced cohort is different from online E0; no causal feature diagnosis follows |
| D1: exact inputs/controls and independent validation, feedback response only 2/4 | Stop its fixed dual-anchor clean-projection route | Response is not accuracy; this does not disprove every use of point outputs |
| E0 audit: exposed-transfer odometry/full ter 0.477262/0.505615%, ATE 0.778065/0.721480 m | Loop correction has conflicting global and segment effects | No general front-end deficit or individual-edge causal shares |
| Joint current-edge GT diagnostic: transfer ATE 0.721480 -> 0.605908 m, ter 0.505615 -> 0.499732% | Current-edge pose opportunity exists primarily for ATE | Even perfect current poses leave ter above odometry in that graph; 09's physical discrepancy remains unresolved |
| Fixed interpolation, E1 and all-online GeoTransformer screens fail | A matcher replacement or routine backend variant has low demonstrated value | Their fixed negative arms do not establish universal impossibility |
| C1/P0 top-1 information and C2 reliance results | Neither an absent feature channel nor a causal descriptor defect has been established | A global top-1 statistic is not a necessary condition for a small, well-conditioned set of correct matches |

Sources: [F2 postmortem](../../2026-09-27/f2-postmortem-01/REPORT.md),
[M1](../../2026-09-29/m1-support-pose-hypotheses-01/REPORT.md),
[D1](../../2026-10-06/shared-identity-engineering-01/REPORT.md),
[system audit](../../2026-09-29/system-opportunity-audit-01/REPORT.md),
[joint diagnostic](../../2026-10-05/joint-loop-oracle-01/REPORT.md),
[FDI1](../../2026-10-05/flow-directional-information-01/REPORT.md),
[online comparator](../../2026-10-05/online-geotransformer-01/REPORT.md).
These are existing outcomes; no metrics were newly recomputed.

## The overlooked interface

Local `sampler.py:56-64` predicts clean endpoints, projects them for the next
state, and stores the **raw** endpoints separately. `procrustes.py:6-37`
fits every input row to its own generated endpoint with unweighted Kabsch.
The active SLAM backend at `rap_backend.py:265-283` takes the final raw
endpoints, fits each part, then returns inverse(T_a) T_b. Its multiview path
uses the same decoding pattern at lines419-442.

Thus final raw output is already used to estimate the native pose. The
untested operation is **cross-view association between raw endpoint rows**,
followed by a fit between original points. It is inaccurate to say the raw
output was entirely ignored. D0 studied earlier-step poses; FDI1 studied
response matrices; neither tested this association decoder.

For original point sets X and Y and final generated coordinates Q_X and Q_Y,
the native decoder fits X->Q_X and Y->Q_Y independently. The candidate
instead constructs a sparse set M of cross-view row pairs using Q_X/Q_Y,
checks rigid spatial compatibility using X/Y, and solves

    min over R in SO(3), t: sum_(i,j in M) rho(||R Y_j + t - X_i||^2).

Generated positions propose where to look. They do not become physical target
points and do not certify a correspondence. Original-cloud distances,
noncollinear spatial support and unused measured points supply additional
tests of those proposals. These are previously unused cross-visit observation
constraints in this decoder, not new sensor observations.

The centroid form of the native translation is mean(Q)-R mean(X). Different
view-specific prediction distortions can therefore affect translation. This
is an algebraic susceptibility, **not** a demonstrated explanation of F2.
Solving on genuine original-point associations could remove that dependence
if useful associations survive in the raw output.

### Essential counterexample and controls

If Q_X and Q_Y are exactly rigid images under the native poses, their
cross-view nearest-neighbor associations equal those obtained after applying
the native relative pose to the original clouds (up to numerical/tie policy).
The method then reduces to RAP-initialized geometric matching. This identity
must be proved and checked in a later synthetic preflight. It prevents an
ICP variant from being misreported as a unique point-flow contribution.

Use the identical robust solver, correspondence count cap, candidate count
cap and final selection rule for:

1. Raw final generated-coordinate associations (candidate).
2. Rigidly projected generated-coordinate associations (critical control).
3. Existing miniSpinNet associations on the same original points.
4. A raw-coordinate/row-identity permutation control (diagnostic only).

Also retain native RAP and the stopped R0 result as references; a fair direct
control must use the new solver and budget, not rely only on R0's old numbers.
No step selection, extra noise samples, favorable generation selection,
sampler feedback or D1 window repair is part of this proposal.

The selected pose must be chosen without evaluator GT. Use a predeclared
physical consensus rule and maintain the original common admission gate in
the first accuracy screen. All generated candidates and selected poses seal
before labels. Correspondence truth/coverage and best-of-candidate recovery
are explanatory outputs; executable selected/accepted performance decides.

### Consistent-wrong limitation

Identity agreement cannot expose a rigid-but-wrong2m pose. Cross-view original
point constraints can falsify some such hypotheses in an identifiable scene,
but not an exactly repetitive scene admitting an alternative rigid alignment.
Wrong correspondences can remain rigidly consistent. Dense geometric support
can also be high for an alias, as earlier diagnostics show. The new method
must include irregular-scene and periodic-scene counterexamples and must not
claim that physical consensus proves pose correctness.

## Brainstorm ranking

| Direction | Practical opportunity | RAP-specific contribution | Priority |
| --- | --- | --- | --- |
| Raw-output associations -> original-point pose solve | New translations using existing saved output; inexpensive first screen | Conditional if raw output beats projected-output and descriptor controls | First mechanism question |
| Measurement-supported point/plane or partial loop factors | Avoid forcing unsupported directions while retaining useful constraints | Conditional only if RAP associations improve factors beyond direct geometry | Subsequent system stage after useful associations |
| Odometry factor aggregation and graph information audit | Directly related to ter/ATE conflict; uses existing graph metadata first | Engineering | Small separate diagnosis; do not begin a parameter sweep |
| Complete retrieval-opportunity ledger | Distinguish absent useful revisits from registration failures | Mainly engineering; generative scheduling needs separate evidence | Conditional if current edges lack adequate opportunity |
| Small correspondence head on frozen RAP tokens | Could learn cross-visit associations rather than repeat a weak pose | Possible but unproven; requires direct same-label adapter baseline | Deferred; no training authorized |
| Camera or semantic evidence | Independent cue for geometric aliases | Broad multimodal prior art and changed thesis scope | Optional scope change, not current default |

Uniformly increasing point counts, steps, candidate budgets or temporal
context is low priority under the existing stops. Ground/BEV registration
may be a useful comparator for a future distinct mechanism, but was already
identified in prior planning and is not a newly discovered innovation.

### Graph direction: what is actually untested

`pose_graph.py:265-268` creates one odometry noise object for every chained
keyframe relative. This differs from propagating individual scan measurement
uncertainties with coordinate transport and correlations. Keyframe selection
uses motion thresholds, so spans may be fairly similar; actual span/correction
metadata must be audited before claiming this is important. Arbitrary sqrt(n)
scaling is not a justified covariance model. Fixed sigmas are a modeling
choice, not automatically a bug.

Complete six-DOF loop factors also differ from direct measured point/plane
residuals or factors retaining only supported directions. An eventual partial
factor should use original measured geometry, model nuisance correspondences
and avoid counting the same data twice as independent pose and point factors.
It must be compared with the same physical-factor construction using direct
geometric/descriptor associations. This is not FDI1 matrix/confidence rescue:
no response-derived confidence, temporal-only matrix or error-axis mask is
proposed. Geometric curvature itself is not calibrated uncertainty and does
not resolve aliases.

The fixed SE(3) correction interpolation stop remains. Changing the graph
measurement objective is different from interpolating its existing output.

## Primary prior-art audit

Accessed 2026-10-07. Focused comparison, not exhaustive novelty clearance.

| Primary source | Relevant established idea | Proposed boundary |
| --- | --- | --- |
| [RAP v2](https://arxiv.org/html/2512.01850v2), sections3.2-3.4 | Joint generated coordinates, per-view rigid forcing and pose recovery | Native generation and Kabsch are inherited; proposed change is the cross-view physical decoder |
| [Regor, CVPR2025](https://arxiv.org/html/2502.02163v1), section3 | Prior-guided local grouping, rematching and spatial correspondence correction | RAP pose -> Regor alone is integration; compare raw-output proposals with projected-output proposals |
| [PointDSC, CVPR2021](https://openaccess.thecvf.com/content/CVPR2021/html/Bai_PointDSC_Robust_Point_Cloud_Registration_Using_Deep_Spatial_Consistency_CVPR_2021_paper.html) | Spatially consistent correspondence pruning | Pair-distance tests are established tools |
| [MAC, CVPR2023](https://openaccess.thecvf.com/content/CVPR2023/html/Zhang_3D_Registration_With_Maximal_Cliques_CVPR_2023_paper.html) | Multiple rigid hypotheses from compatible correspondence cliques | Robust hypothesis enumeration is a control, not originality |
| [Diff-Reg v2](https://arxiv.org/html/2503.04127v1), sectionsIII-D/E | Trained diffusion over matching matrices with matching-to-warp encoding | Proposed frozen coordinate-output -> measured correspondence direction differs operationally; generative matching is already established |
| [Wednesday/ODIN](https://arxiv.org/html/2404.00429v1), section3 | Diffusion overlap/correlation refinement and global registration | No first generative matching or generative global registration claim |
| [VCR-Net](https://arxiv.org/abs/2011.14579) | Learned virtual correspondences followed by SVD | Generated correspondences plus SVD is not new; keep actual measured targets and frozen RAP provenance explicit |
| [BALM2](https://arxiv.org/abs/2209.08854) | Physical point-to-feature residuals and LiDAR bundle adjustment | Direct point/plane optimization is established |
| [X-ICP](https://arxiv.org/abs/2211.16335) | Localizability-aware constrained registration | Partial/degeneracy-aware constraints are established |
| [Information-aware/retroactive-loop SLAM](https://arxiv.org/html/2607.13516v1), sectionIII-B | Geometry-aware ICP objective curvature and graph feedback | Generic information-weighted PGO/retroactive loops cannot be the contribution |

No external method was downloaded, installed or reproduced. No source paper's
benchmark score is transferred to this project's pairs.

## Practical research discipline

Preserve old negative decisions. Improve the design of the **new** screen:
after minimum geometry/source checks, measure actual selected pose outcomes
with its indispensable controls. Do not make a large mean descriptor recall
gain or a material change on every easy pair a universal admission condition
for all future mechanisms. A good method may leave solved cases unchanged.
This observation does not revise D1/P0/C1 gates or license their rescue.

Reuse sealed arrays where appropriate. A bounded independent geometry and
decision check is enough for the first screen; do not build another lengthy
chain of proxy-only studies. Evaluate on both exposed200-pair development
data and, conditionally, all71 actual online attempts. Pair and system claims
must remain separate, and later independent confirmation requires honestly
declared data/checkpoint exposure.

See [NEXT_ROUND_PLAN.md](NEXT_ROUND_PLAN.md) for the conditional schedule,
direct outcomes and proposed stopping criteria. No execution follows from
this brainstorming request.

## Preservation

RAP-main: `codex/meeting-20260930`, HEAD4055d929c594b0033aafc6eed339c910369eef55.
RAP-SLAM: `codex/e0-f1-20260926`, HEAD6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6.
Both have existing dirty work. No code/default/model/manuscript or frozen bank
changed, no GT evaluation, training, data acquisition, installation, commit or
Git synchronization. The local12-layer checkpoint's training membership and
09's physical discrepancy remain unresolved. Preservation manifest SHA matches
the recorded M0 identity; archive payload was not rehashed.
