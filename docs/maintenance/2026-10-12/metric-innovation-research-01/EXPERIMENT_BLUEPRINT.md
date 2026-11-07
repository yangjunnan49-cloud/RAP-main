# Draft execution blueprint — not frozen or executed

This is a reviewable sequence, not an execution authorization or amendment of a historical gate. Final input identities, parameters, caps and acceptance rules require a later prospective scope.

## A. Measurement interface first

Proposed first study: graph-measurement-feasibility-01, starting with CPU synthetic fixtures and interface checks. No study runner or payload is created here.

Question: can explicit scan-level correction use existing RAP loops more effectively than the current compressed keyframe graph while preserving local motion? If it passes, can measured matching constraints improve loop centres beyond fixed BetweenFactor snapshots? Keep the questions separate rather than changing graph resolution, centres, information, retrieval and RAP together.

| Arm | Variables / observations | Purpose |
|---|---|---|
| B | Existing keyframe graph, original odometry relatives, loop poses/weights and constant propagation | Exact reference |
| S | Scan-pose variables, original consecutive motions, identical loop endpoints/poses | Explicit distribution of correction |
| K | Analytically marginalized synthetic scan chain at keyframe endpoints | Checks aggregate strength equivalence |

Derive the perturbation convention, transport and nominal aggregate information on a synthetic small-noise chain. Check no-loop no-op, perfect-loop recovery, common-frame invariance, scan order/direction, source IDs and equivalent limits. Include correlated-noise counterexamples. Real KISS scan-to-map errors are correlated; a convenience independent chain is not calibrated covariance. Do not substitute sqrt(scan span) for missing uncertainty, or duplicate both scan and keyframe factors for one observation.

The first real comparison reuses complete fixed historical bindings as exposed development, without GT-selected windows. Keep frontend, admissions, loop poses and weights fixed. Report per-sequence odometry/full ter/rer/ATE, factor counts, correction jumps and changed local motion. This is distinct from the stopped fixed interpolation test because it changes the optimization problem, but ordinary scan-level PGO remains prior art.

After numerical validity, a separate stage compares fixed loop-pose snapshots with one declared measured GICP/VGICP interface. Begin with a small count-selected set, then all prescribed attempts if admitted. Native RAP supplies an initialization; original physical points supply observations. Retain support failures in the denominator.

Characterize association, support distribution, covariance/normal validity, basin, rank and actual residual response before refinement. Include single-plane, nondegenerate and periodic fixtures; use whole physical patches/scans for held-out diagnostics while acknowledging correlation. Lower holdout residual alone cannot certify accuracy after CV2/MF0.

Use identical solver and support on RAP, odometry and independent geometric initializations. A saved pose/Hessian turned into a BetweenFactor is an approximation control, not a direct factor that rematches and relinearizes in the global solver. Start with a light CPU control, then justify direct-factor integration if useful. This does not repeat the stopped equal-mass shared-plane objective or PFG's fixed-centre shape-only change.

Stop the declared construction on invalid support, objective/reference conflict, failed metric/safety or budget gates. Do not rescue it with extra radius/kernel/point-count schedules.

## B. Compact residual contribution

Conditional on useful headroom and a later small-head fitting scope. This is not a continuation of stopped RLP2 or NOC4 updates.

Define a zero-initialized bounded local residual:

`T(z) = T_native Exp(D z)`.

Fix the frame convention and translation/rotation units; D sets numerical scale. Check independent relative-pose gradients and analytic rigid controls. An output bound is a design choice, not proof of descent or physical correctness. Near-pi and ambiguous geometries remain relevant even when a locally bounded Lie residual is used.

The head predicts a metric correction or a precisely defined prior for the measured solver. It does not relearn a global soft correspondence transport. Inference uses observed points/descriptors, frozen information and target-free residual/support features. GT, teacher coordinates and target-derived caches are restricted to training/evaluation. No gradients pass through the frozen RAP backbone.

| Arm | Distinct component over a common native pose | Purpose |
|---|---|---|
| N | Zero residual | Native identity reproduction |
| G | Fixed physical solver, no head | Geometry increment |
| D | Descriptor/statistic residual head | Equal active-capacity learning control |
| I | Separated-context frozen features | Context control |
| J | Joint frozen RAP information | Contribution candidate |
| W | Equal total work spent on direct geometry | Compute control |

All learned arms receive the same native pose, observations, residual statistics, loss, initialization rule, optimizer budget and downstream solver. Avoid inactive padding that changes effective capacity. Keep one predetermined family/solver and all seeds/noises. Validate cache extraction against full inference before use.

A known-transform numerical fit is a prerequisite, not efficacy. Copied descriptors may appear only in a labelled numerical fixture, not feature-generalization evidence. Real data roles are fixed by sequence/session before outcomes; fresh noise on one scene remains a conditional robustness test.

J must improve paired metric pose accuracy over G and D, retain context/tail/sequence safety, and later improve full trajectories versus the strongest declared control. J versus I alone is insufficient after RLP2. If D/G explains the benefit, report engineering improvement without RAP-specific evidence. Stop on mere loss reduction, rotation harm, noise/scene failure or budget exhaustion; no extra epochs/thresholds/seeds follow.

This new residual output/baseline/task differs from RLP2 global soft assignment and NOC4 native velocity/pose adapter training. Ordinary residual refinement is still established. Its modest contribution would require the joint generative input and metric/measurement coupling to add value under the above counterfactuals.

## C. Conditional submap observation alternative

Use only if ATE priority/headroom justifies new observations. It changes the detector and observation unit, rather than LC0's old radius/cap or the shared-plane objective.

Define compact submaps by observed distance/time/quality before outcomes; bound internal odometry distortion and retain all frame identities. Retrieve with a fixed independent density-map method. Compare joint RAP, independent pair RAP and direct measured registration with equal raw support and explicit total cost. Verify on original scans; connected generated clouds do not prove real overlap.

At graph insertion use a fixed sparse connected edge set or an explicitly correlated multi-node model. Do not multiply evidence through an independent all-pairs clique, duplicate shared observations, fabricate revisit-gap motion edges, or use GT selectors. Geometry/rigidity scores are not calibrated probabilities.

Keep the old gate initially for comparability; any distinct physically justified gate is a separate stage frozen before labels. Proposal, pose, acceptance and complete-system outcomes remain separate, including every false accept. Benefits merely from more scans belong to support/context, not automatically RAP joint reasoning.

## D. Example future metric choices

These are draft options, not historical gate amendments:

- ATE-primary: at least5% cohort ATE reduction versus the strongest declared baseline; mean ter nonworse; per-sequence ter harm at most0.01 percentage points and ATE harm at most5%; declare an explicit rer guard.
- ter-primary: at least0.01 percentage point mean ter reduction; cohort ATE nonworse; prespecified per-sequence ATE/rotation safety.
- Residual pilot: paired translation/rotation improvement, joint signs, tail safety and a physical output bound. Final thresholds are set from the declared task before outcomes, not fitted to an observed near-threshold case.

Preserve09 in the official table and separately describe its unresolved reference discrepancy. Do not replace truth or delete adverse sequences. If intervals are reported, respect sequence/session clusters; process or noise repeats do not establish independent scene/pretraining confirmation.

## E. Budget and evidence conditions

Draft feasibility envelopes: CPU graph15min/4GiB RSS; isolated frozen-feature/head feasibility30min/3GiB GPU/4GiB RSS. These are proposed caps, not measured runtime or frozen authorization. Include failures, replay and validators; profile before final declaration. Complete pipelines require their separate larger memory class.

Retain host headroom guards and durable child/Windows resource/exit records. No pagefile/driver/global WSL/environment replacement or unrelated process changes. gtsam_points compatibility needs investigation; availability is not permission to replace GTSAM/PyTorch.

Freeze sources, inputs, controls, roles, gates and resources before outputs; seal predictions before new evaluator errors; independently validate geometric derivatives, factor equivalence, frames and metric arithmetic. Use exclusive new outputs and retain all old failures/INCOMPLETE/seals. No small positive result automatically authorizes production or manuscript promotion.

## F. Progression

`Metric/scope choices → graph numerical feasibility → measured-factor validity → strong engineering baseline → one residual test → complete trajectories → reserved-session confirmation`.

Submap proposals are an alternative at the baseline decision, not a mandatory second campaign. Native adapter work remains separately conditional on NOC4 P reproducibility. A frozen-feature residual requires exact extraction and its own derivatives, without assuming the native adapter backward has been repaired.
