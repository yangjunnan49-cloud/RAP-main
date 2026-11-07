# Breaking the bottleneck: research strategy after the frozen-token failures

Date: 2026-10-09 (Asia/Shanghai).
Status: RESEARCH_AND_BRAINSTORMING_COMPLETE; no new experiment executed.
Decision: PRIORITIZE_MEASUREMENT_REOPTIMIZATION_AND_FIT_DIAGNOSIS.

The owner explicitly requested brainstorming and permitted relaxing originality
and logical-rigor thresholds. This changes the admission standard for future
exploration: established methods, practical combinations, limited development
tuning and initially incomplete causal explanations are eligible. The earlier
ordinary-adaptation rejection remains a historical design decision under the
earlier objective; it is not experimental evidence against adaptation.

My recommendation is to change the object we optimize, and change the order in
which we learn. First investigate joint optimization against measured geometry
at local-map/trajectory scale. In the learning branch, first establish that a
native-output adapter can fit a tiny task and function under actual inference.
Only then investigate a correction to a strong geometric estimate. Do not begin
another large frozen-token matching experiment or the old twelve-fit adaptation
draft. These recommendations are judgments about expected information value,
not demonstrated improvements or a guarantee of a breakthrough.

## 1. What the accumulated evidence actually says

| Evidence | Established result | What remains open |
| --- | --- | --- |
| E0/E0-H1 frontend correction | Development full mean ter fell from 0.761655% to 0.388718%; exposed-transfer O/A ter was 0.959528/0.505615%, ATE 1.217655/0.721480 m | This is a substantial engineering gain. It does not establish a new RAP mechanism. The premise that absolutely nothing improved is too broad. |
| RLP2 frozen readout | Joint J beats separated I under the full rule, but fails D and is far worse than G3/KISS | A common construction bottleneck is plausible. We have not separated fitting failure, transfer failure, weak-label limitations and representation mismatch. |
| RLP2 all-48 window medians | J 0.888431 m/0.552965 deg; G3 0.097115 m/0.238968 deg | Learning the complete local pose from this readout discards an already strong geometric solution. |
| RLP2 matched 36 KISS endpoints | J 0.888431 m/0.593314 deg; KISS 0.022371 m/0.049555 deg; J loses every paired R/t comparison | Adjacent-frame motion is an especially demanding task for an unposed generative model to replace. Dense-map KISS has different inputs and cost. |
| Joint current-edge GT replacement | Exposed-transfer ATE improves 16.0187%; ter gain 0.005883 pp; development does not pass either branch | Pair accuracy and system utility differ. The intervention is an evaluator counterfactual, not physically recoverable gain. |
| LC0 distributed ideal loops | Development ATE improves 55.241/56.005% for P/H, while ter worsens 0.065168/0.075811 pp | The frozen conjunction fails. ATE opportunity nevertheless exists in this particular counterfactual; it is not a practical method or general ceiling. |
| MDC0 accounting | Reduced component energies can coexist with increased ter through loss of signed cancellation | Better ATE need not produce better ter. This does not uniquely identify physical causes or a backend defect. |
| hard08 candidates | 37/41 missing-native-candidate positives fail translation only; 26 best translations are within 2 m | Translation ambiguity deserves targeted diagnosis. Those counts do not supply an executable correction. |
| 09 discrepancy | On all 12 online pairs, official-pose overlap median 2.5%, RAP 81.34375%, GeoTransformer 78.50625% | Physical aliasing, trajectory-reference error and missing sensor provenance remain distinguishable explanations. Neither model agreement nor low residual proves correctness. |

The historical HC comparison predates E0. Its weaker original frontend cannot be
used to claim that the current corrected system retains that entire gap to
KISS-SLAM. E0-H1 already gives a more relevant same-data comparison and shows
mixed metric outcomes. Likewise, F2 hard-loop cohorts and the actual online E0
distribution are different tasks; conclusions must not be transported silently.

Primary local records: [E0](../../2026-09-26/e0-frontend-01/REPORT.md),
[E0-H1](../../2026-09-27/e0-heldout-01/REPORT.md),
[RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md),
[joint-loop diagnostic](../../2026-10-05/joint-loop-oracle-01/REPORT.md),
[LC0](../../2026-10-07/retrieval-placement-audit-01/REPORT.md),
[MDC0](../../2026-10-07/metric-conflict-decomposition-01/REPORT.md),
[09 geometry](../../2026-10-05/online-geometry-consistency-01/REPORT.md).

## 2. The research process also needs a different operating mode

There is a distinction between a first development experiment and a final
confirmatory test. Our recent fixed experiments establish reliable narrow
negative results. A single configuration's failure is not enough to reject an
entire architecture family, and implementation correctness is not optimizer
convergence. Many recent branches changed inference around the same frozen
information source; the full model's task-adaptation capacity has barely been
tested. This is my inference from the experiment history.

RLP2 recorded nine fitting stages totaling 571.217675 s, nine complete replay
validators totaling 529.632832 s, and 6124.146614 s for the full process account.
Actual fitting stages therefore occupied about 9.33% of that account. Prediction,
prediction validation, binding freezes and other work consumed the remainder.
This does not prove that the accounting was wasteful or that more updates would
work. It does show why repeating the complete delivery workflow for every early
development idea would limit exploration. The old amended budget remains closed.

For new exploratory work, use one or two sensible controls, a tiny fit first,
fixed-checkpoint errors, selected gradient/pose crosschecks, a run log and a real
resource ceiling. Permit a declared limited learning-rate/supervision/conditioning
search on development data. Track every trial and keep failed outputs. Reserve
complete seed comparisons, full numerical replays and expensive scientific
closure for a promising final candidate. Old seals and old failures remain intact.

For mapping, I recommend ATE as the initial primary development objective, with
ter/rer, bad-loop events and runtime displayed as tradeoffs and safety measures.
For odometry, use ter as the primary objective. Fix that choice and acceptable
regression margins before new outcomes. An exploration may be worth continuing
without passing every old conjunction. It cannot retrospectively turn LC0 or
RLP2 into a PASS or justify hiding regressions. Relaxed logic means tolerating
an unproven mechanism during discovery; evidence honesty still matters.

## 3. Ranked directions

These ranks are qualitative priorities, not measured success probabilities.

| Rank | Direction | Why it deserves attention | First decisive question |
| --- | --- | --- | --- |
| 1 | Local-map/trajectory optimization against measured points | Changes the estimation problem rather than reweighting a saved pose; directly addresses local/global consistency | Can a conventional geometry-only construction improve the chosen system objective on the corrected frontend? |
| 2 | Native-output task adaptation, then geometry-conditioned residual learning | Ordinary adaptation was blocked by originality, not by an experiment; avoids RLP2's matching bottleneck | Can it fit 1 then 8 development windows and survive the actual sampler? |
| 3 | Relocalization/map merging with an explicit recovery objective | Better aligns unposed registration with a system need than replacing centimeter-scale ordinary odometry | Does RAP recover a pose when the same-data geometry baseline loses its basin? |
| 4 | Additional appearance/semantic observations for ambiguity | Could add information that repeated geometric scores cannot supply | Does the extra channel distinguish the actual confusing hypotheses before training a full model? |

### Direction 1: reoptimize measured geometry, not only saved relative poses

Keep corrected KISS motion as the initial estimate. Build bounded local maps from
causally available scans and retain their internal scan poses. Optimize recent
poses using direct scan/plane/GICP residuals; at revisits, re-evaluate point
associations as the maps move instead of representing all information by one
fixed six-dimensional loop pose. Begin with a conventional implementation and
small real windows. A successful geometry-only result would locate engineering
headroom; it would not be a RAP contribution.

The next RAP role would be supplying alternative initial alignments only where
ordinary geometry fails, followed by the same measured-point optimization used
by the geometry control. Evaluate how many additional useful alignments remain
after that common optimization. A union of candidate generators without an
executable, GT-blind admission rule is not a system improvement. Initial-pose
priors and temporally correlated evidence require explicit treatment.

This is technically different from PFG1: its loop centers and observations were
fixed while information shape changed. It also differs from O1/R0's final pair
ICP, PG's pooled unposed generation, D1's self-consistency feedback, and the
fixed dense-trajectory interpolation screen. Those negative results still weigh
against easy variants. Merely adding ICP or renaming pooled scans as a submap
would not implement the proposed change.

Direct measured-point global optimization has established prior art:
[Koide et al., global GICP cost factors](https://staff.aist.go.jp/k.koide/assets/projects/lidar_mapping/index.html).
[BALM](https://arxiv.org/abs/2010.08215) supplies another conventional local
multi-scan optimization reference. These sources support the estimation concept,
not improvement on our data. GLIM extends this family; its full range-inertial
results cannot be attributed to a LiDAR-only version of our system.
[GLIM paper](https://arxiv.org/abs/2407.10344).

The existing [KISS-SLAM paper](https://arxiv.org/html/2503.12660v1) also constructs
local maps and describes fine-grained optimization of scan poses. Our local HC
run already compared complete KISS-SLAM. The missing question is a controlled
measurement/optimization intervention on the corrected frontend, not another
uncontrolled whole-system comparison.

Main risks: computation, moving objects, poorly constrained directions,
correlated residuals and wrong repeated-scene associations. Small residuals do
not certify a physical location. A real geometry-only failure should direct the
investigation toward observability or new observations rather than immediately
adding a neural component.

### Direction 2: prove fitting first; learn a correction to strong geometry

The latest [adaptation design](../local-generative-adaptation-design-01/REPORT.md)
is source-feasible but unbenchmarked. Its 443904 trainable parameters and proposed
240-minute account are estimates/drafts, not existing runtime measurements or
authorization. Relaxing originality removes its previous novelty veto for
future engineering exploration. It does not validate the design or make the
large four-arm/twelve-fit draft the right first run.

Start with native original-point to generated-point decoding in an isolated
adapter, on one then eight development windows. Compare a simple direct-point
learner. Include known-transform same-scan fixtures with cropping/occlusion, and
real adjacent scans separately. Synthetic success only establishes a controlled
capability, not robustness to real motion or partial observations.

Measure initial/final fixed-checkpoint training R/t, teacher-forced states by
noise level, pure-noise inference and actual multi-step inference. If low-noise
teacher-forced loss improves but pure-noise/sampler poses do not, the working
diagnosis is inference-state mismatch, not successful registration. GT-derived
training states already contain target information. They are valid supervision
but must never be passed as inference observations. The production sampler
detaches outputs; a purported rollout gradient must not silently stop there.

If a tiny native adapter cannot fit, first isolate normalization, gradient
paths, objective scaling, noise nuisance, capacity and supervision. A small
development search is appropriate. If it fits but fails nearby unseen windows,
focus on sample coverage and regularization. Neither pattern justifies another
large frozen-token pilot.

If fitting and transfer are credible, move to a geometry-conditioned correction:

T_prediction = Exp(delta_theta(inputs, T_geometry)) * T_geometry.

The learner predicts the remaining pose error or an explicit abstention. Its
default zero correction is a defined policy, not a hidden rescue of invalid
outputs. Compare against unchanged geometry, conventional geometric refinement,
and a simple non-generative residual learner. Invalid outputs count as failures;
an explicit planned abstention leaves the baseline and is reported separately.

Important implementation issue: independently recentering each scan can erase
the translation cue supplied by the initial alignment. The prior must remain in
the conditioning or shared-frame coordinates. Adding T_geometry is a genuine
input-contract change and requires new adaptation; the old native model cannot
be assumed to understand it. A simple residual learner should establish signal
before a RAP-specific adapter is developed.

With KISS already near 2 cm/0.05 deg on the matched endpoints, weak short-baseline
reference error may dominate the remaining target. Use difficult segments
defined by causal geometric signals for a targeted system policy, while keeping
ordinary segments and the complete endpoint denominator. Do not define the
deployed trigger using GT error or select only favorable failures.

RAP's coordinate-generation contract motivates this route; its paper does not
train the extracted tokens as correspondence descriptors.
[RAP formulation](https://arxiv.org/html/2512.01850v2).
Diffusion-based task refinement and semantic odometry already have prior art in
[DiffLO](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_DiffLO_Semantic-Aware_LiDAR_Odometry_with_Diffusion-Based_Refinement_CVPR_2025_paper.html).
Borrowing them is eligible under the revised objective; engineering success
would come before any claim about a distinguished generative mechanism.

### Direction 3: evaluate recovery and map alignment where RAP may have a role

RAP's intended no-initial-guess registration task is closer to relocalization
and multi-session alignment than ordinary adjacent-frame odometry. Use a clear
system stress objective: time/distance to recover after a lost pose, recovery
success across initial-pose errors, or map-merge consistency with measured
geometry. Retain standard KITTI trajectory reporting when applicable.

A same-sequence scan transformed or cropped artificially is a useful controlled
diagnostic, but not independent evidence of cross-session deployment. Real
revisits, negatives and dissimilar scenes remain necessary. This task change
should be chosen for an application, not to manufacture a favorable benchmark.
It has not been validated by this turn.

First ask whether RAP contributes any successful alignment after a strong
common geometric optimizer. G0/G1 already tested KISS-Matcher configurations,
and the actual online GeoTransformer comparison also failed. Do not present
these matchers as untried remedies. A different accumulated-map input/task can
be a new question if its observation contract is genuinely changed and stated.

### Direction 4: add information rather than another score on the same geometry

Image features with verified synchronization/extrinsics, or actual semantic
observations, could resolve geometric ambiguity. Learned semantic channels may
derive from the same LiDAR and are not automatically independent sensors.
Assess information value on the confusing hypotheses before building a full
multimodal network. Then verify that any gain survives causal operation and
ordinary cases. Availability of local camera/semantic payloads was not audited
in this turn; IMU is not assumed available on KITTI benchmark exports.

V0 already tested a fixed sensor-ray proxy and I1 tested intensity information;
both were negative. C5 also tested a temporal-persistence mask. Another ray
tolerance, intensity bin or support mask is not a new observation source.
The [viewpoint-aware ICP authors](https://github.com/HMCL-UNIST/ViewpointAwareICP/blob/main/README.md)
document visibility scoring prior art. Full sensor-origin/firing-time contracts
would matter for stronger physical claims. This direction is lower priority
because data access, synchronization and model engineering are unresolved.

## 4. Details we still do not know, and how to resolve them

| Priority | Missing detail | Evidence we already have | Smallest useful next check |
| --- | --- | --- | --- |
| Immediate | Does a new native adapter solve even a tiny task? | Old design had no model instantiation or optimizer step | Fit 1 then 8 development windows; fixed-checkpoint R/t; direct learner control |
| Immediate | Fitting failure versus transfer failure in RLP2 | Online losses fell; no fixed-final fitting-accuracy study | A separately labeled retrospective read-only diagnostic of final fit errors if needed; no retuning or retroactive protocol change |
| Immediate | Teacher forcing versus real inference | Proposed training states use transformed targets; sampler detaches | Evaluate by noise level and pure-noise rollout; audit actual gradient graph |
| Immediate | Is strong geometric residual predictable? | G3/KISS dominate J; remaining KISS target is small | Simple geometry-conditioned residual learner and explicit zero-correction control |
| Immediate | Does geometry-level reoptimization add system value? | PFG1/E1 changed graph factors, not the entire observation objective | Small LiDAR-only local/map optimizer on corrected source-bound inputs |
| Immediate | Which errors matter to the chosen application? | ATE/ter conflict and signed cancellation are measured | Set mapping versus odometry objective before outcomes; report both and tail failures |
| High | Exact 12-layer checkpoint training provenance | Strict loading/replay succeeded; SHA is known | Author release metadata/checkpoint recipe binding; no inference from paper exclusion alone |
| High | Physical origin of 09 mismatch | Frame/path/time/calibration chain and local controls pass | Independent sensor/trajectory provenance or separately sourced reference; retain official labels |
| High | Reference error relative to centimeter-scale residuals | Short-baseline GT is weak; numerical pose conventions are checked | Quantify reference quality with available independent evidence; keep geometry and GT results distinct |
| High | Error concentration by motion/scene | Existing windows are count-selected and outcomes exposed | Descriptive full-coverage slices by speed, turning, range, dynamic content and geometric observability; no favorable-only claims |
| High | What native generation contributes after geometry optimization | Raw/row-binding reliance exists, not useful extra information | Shared optimizer from different initializers, same measured observations and cost report |
| High | Internal local-map distortion and observation correlation | MC1 found scan spans; no calibrated propagated covariance | Direct multi-frame residual/pose checks, including correlations and dynamics |
| Medium | Preservation of motion prior under canonicalization | Native paths center scans individually; old local task is unposed | Source/known-transform conditioning fixture before training residual models |
| Medium | Generalization to new sites/checkpoint-independent data | 07-10 are exposed; paper recipe uses multiple outdoor datasets | Verified new site roles and checkpoint provenance; dataset renaming is insufficient |
| Medium | Local camera/semantic/sensor payload availability | Not established by this review | Bounded metadata/access check only if direction 4 is selected |
| Medium | Adaptation memory and runtime | Static counts; inference peak is not training peak | One authorized forward/backward feasibility check; memory cap measured, not extrapolated |
| Medium | Native retrieval limits outside LC0's fixed contract | Near proxy coverage is high; 10 has no eligible near pairs under 15 m/200 frames | Task-specific observation/retrieval contract if recovery/map alignment is chosen |

Do not spend a new week re-verifying already established row/RNG/Horn bindings.
Reuse them with identity checks. Gross unloaded descriptors, an absent feature
channel, a simple ten-step fix, KITTI synthetic deskew and a generic ICP/KISS
replacement are not the leading unknowns. Their prior checks and negative
screens matter. The unknowns above concern capability, application alignment
and physical observations that those checks did not settle.

## 5. Concrete next development program

This is a proposed sequence, not an execution protocol, budget amendment or
training authorization. A follow-up instruction to execute should first make
the chosen scope, allowed changes, data roles and resource cap concrete.

1. Begin with a compact capability diagnosis: native-output adaptation on tiny
   development data, plus a simple direct learner. Use exact synthetic geometry
   and real weak supervision separately. One seed is adequate for debugging;
   it is not final efficacy evidence. Resolve fitting and inference mismatch
   before expanding data or fitting the old twelve-model design.
2. Pursue the highest-priority system branch: a geometry-only local/map
   reoptimization pilot on the corrected frontend. Start on a causal short
   window, then one complete development sequence with ATE/ter/rer and cost.
   Keep the frontend and comparison conditions matched. A local point error
   improvement alone is insufficient to declare a full-system benefit.
3. Choose one resulting research mechanism. If geometry has practical headroom,
   evaluate RAP initialization against the same optimizer. If adaptation fits
   and transfers, evaluate a geometry-conditioned residual. Do not combine
   both new mechanisms immediately and lose the ability to interpret failure.
4. Give a promising candidate a small declared development search. Save all
   trials, do not repeatedly inspect a reserved confirmation set, and freeze
   the selected implementation before final sequence/seed evaluation.
5. If no useful extra capability remains after strong geometry, select the
   recovery/map-alignment task or the additional-observation branch. Continuing
   to rename old confidence or frozen-token variants is lower-value work.

A practical first decision is therefore whether the new adapter can fit and
whether measured-map optimization has useful headroom. Those are answerable
questions with substantially different implications. Nothing in the current
record makes a particular new architecture certain to succeed.

## 6. Scope and integrity of this turn

Read AGENTS.md history, recent adaptation/RLP2 records, relevant prior stops,
local flow/sampler/readout source and primary literature. Eight current
source/config hashes and all nineteen adaptation-design delivery entries
matched. The opaque checkpoint digest is verified in CHECKS.json without tensor
deserialization. This is a bounded identity check, not a rerun of all historical
scientific validators or the 1994-file RLP2 closure audit.

Repository HEADs/branches and prior tracked dirty files are preserved. Only this
new research dossier and mutable AGENTS/phase handoffs are edited. No raw cloud
or numeric-GT payload calculation, model load, numerical preflight, inference,
optimizer, trajectory, acquisition/install, production/default/model/manuscript
edit, commit or Git synchronization occurred. All previous scientific decisions,
official metrics, source banks, failures and seals remain historical evidence.
The owner relaxation permits new exploratory recommendations; it does not
retroactively pass any failed experiment. The original breakthrough has not
been achieved in this brainstorming turn.
