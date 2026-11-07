# Research for metric improvement with a modest RAP contribution

Date: 2026-10-12, Asia/Shanghai.
Status: **READ_ONLY_PRIMARY_SOURCE_RESEARCH_COMPLETE**.
Owner request: investigate how the current framework can gain further metrics and an appropriate amount of innovation; clarify details in a later conversation.

## Decision

Pursue a staged combination of a stronger measurement interface and one compact RAP-specific component. First test whether scan-level correction and measured registration constraints can improve system accuracy while retaining the present frontend. Then measure the incremental value of a bounded pose-residual module around frozen RAP predictions. Treat submap-level place recognition and multi-view proposal generation as a conditional ATE route, rather than immediately expanding every branch.

This recommendation is an inference from local evidence and primary literature, not an achieved gain. The most promising contribution is a well-controlled interface between a generative pose prior and physical measurements. New full-model training, more Euler steps, another confidence score, or a wholesale SLAM replacement has a weaker justification at present.

All proposals are **DESIGN_ONLY**. No new scientific protocol is frozen and no neural, optimizer, geometry, graph, raw-data or metric experiment ran. The incomplete NOC4 comparison, failed numerical gates and all previous stops remain unchanged.

## 1. What improvement must mean here

The current six-sequence complete-system means are RAP/KISS ter0.447167/0.478614% and aligned LiDAR ATE1.091072/0.699689m. The principal ATE deficit is on00/05. Current RAP ter is already competitive; its exposed-transfer ATE advantage depends on09, where physical scan/reference consistency remains unresolved. These are existing results, not new calculations.

The two metrics have different geometry. KITTI evaluates segment-relative translation/rotation, whereas aligned ATE measures global position agreement. The [official evaluation](https://www.cvlibs.net/datasets/kitti/eval_odometry.php) supports preserving their distinction. More accurate pairwise poses, lower plane residuals and additional loops do not automatically improve both.

For a future new family, my provisional recommendation is **ATE as primary, with explicit ter/rer safety**, because this addresses the largest current gap. This is a proposed future choice awaiting the user's priorities. It does not amend the earlier simultaneous gates or turn LC0/CV2 into a success. If the advisor instead prioritizes ter, the sequence of investments changes: local motion and scan-level correction become more important than additional global revisits.

Innovation should be proportional to the thesis scope: one mathematically defined component, a clear reason it addresses an observed failure, and an ablation that isolates its value. It does not require retraining a foundation model or inventing every subsystem. Generic GICP, pose graphs, submaps and residual networks must be credited accurately.

## 2. Findings that change the previous planning assumptions

**GLIM is not categorically excluded by missing IMU.** Its [official guide](https://koide3.github.io/glim/quickstart.html) exposes LiDAR-only odometry and disables IMU factors for mapping. Its direct scan-matching factors are therefore relevant as a design/control source. This corrects the older blanket exclusion, while leaving the applicability of published inertial numbers unproven.

**The current graph simplifies more than a scalar loop weight.** Source uses keyframe nodes, one fixed odometry noise model for every aggregated interval, complete Pose3 loops, and piecewise-constant correction for intermediate scans. This is a verified interface fact, not proof of harm. KISS-SLAM includes [fine-grained correction](https://arxiv.org/html/2503.12660v1), and [GLIM](https://arxiv.org/abs/2407.10344) demonstrates direct matching factors. These are stronger comparisons than simply changing the interpolation formula or a robust kernel.

**Information estimation has close recent prior art.** The [2026 information-aware/retroactive-loop paper](https://arxiv.org/html/2607.13516v1) uses a rematched local cost approximation, hierarchy and backend feedback. Copying that recipe with RAP substituted is not a sufficient algorithmic distinction. Its assumptions also do not supply our missing scan-to-map cross-correlations.

**New smooth registration objectives are available, but have limits.** [MMD-Reg](https://arxiv.org/html/2606.27818v1) avoids discrete nearest-neighbor assignments and supports implicit differentiation. Its low-overlap neural setting employs learned overlap masks. Consequently, unweighted MMD should be a conditional control, not presented as a proven solution to the shared-plane conflict.

**Replacing KISS-ICP is not automatically an improvement.** [GenZ-ICP](https://arxiv.org/html/2411.06766v1) is useful against degeneracy, but its KITTI comparison does not beat KISS-ICP and describes dataset tuning. A system swap could change scores, but would isolate neither the cause nor the RAP contribution.

## 3. Which bottlenecks are still open

| Bottleneck | Established evidence | What a distinct study must add |
|---|---|---|
| Neural numerical reliability | NOC4 P backward/update replay differs; V/P finite steps raise objectives | Reproducible upstream/per-parameter derivatives and functional step verification before native adapter fitting |
| Loss-to-pose mismatch | Teacher velocity MSE and pose can move oppositely; shared-plane residual can improve while reference error worsens | A metric residual target and independently checked observation model, rather than assuming a better surrogate means better pose |
| System correction model | Loops improve cohort ATE while worsening ter; current graph compresses scan motion | A direct intervention on graph resolution/measurement objective, separated from loop selection and native pose generation |
| Model-to-system contribution | Native sparse local motion and frozen-token readout lose to practical controls | A useful incremental RAP effect with identical optimizer, point support and compute controls |
| Revisit observations | LC0 shows strong ATE oracle opportunity on development but adverse ter | New physically supported submap observations and an executable detector, not redistributing old oracle edges |
| Physical/reference evidence | MF0 and09 discrepancy remain unresolved | Verified sensing/association or independent reference evidence; preserve official metrics and adverse cases |

## 4. Ranked routes

| Route | Main target | Engineering feasibility | Potential novelty | Priority |
|---|---|---|---|---|
| Scan-level correction with measured registration factors | ATE with ter safety | Uses current poses/GTSAM; direct factors add integration work | Low by itself; a necessary stronger baseline | First, bounded engineering test |
| Frozen RAP plus bounded metric pose residual and physical refinement | Pose accuracy/noise stability, then ATE | Compact head; no backbone backward required | Modest, conditional on RAP features and proposed interface adding value | Preferred contribution candidate after baseline feasibility |
| New submap retrieval plus joint RAP registration | Useful revisits and global ATE | New observation unit and banks; medium cost | Modest if joint RAP changes proposal capability beyond independent/direct controls | Conditional alternative after metric priorities are clarified |
| Rematched odometry information | Distribution of graph corrections | Needs new source observations; correlations limit calibration | Mostly engineering; strong close prior art | Support study, not the entire thesis contribution |
| Learned moving-object / static evidence | Observation quality and dynamic failures | Extra model and Blackwell dependency burden | Low as preprocessing; useful control if dynamics are demonstrated | Conditional on a causal observation diagnostic |
| BUFFER-X / MMD-Reg / alternate matcher | Registration basin/solver checks | New dependencies and weights | External baseline, not project innovation | One selected control if needed |
| Full backbone adaptation / SE(3) generative retraining | Native behavior | Data and numerical risks are high | Potentially higher, but ordinary adaptation itself is established | Defer |

Feasibility and priority are qualitative judgments. They are not estimated probabilities of success or promised percentage gains.

### Route A: change the actual correction problem

Keep the E0 frontend and existing loop measurements fixed at the beginning. Compare the present keyframe graph against a scan-level graph retaining the original consecutive motions, with a correctly matched aggregate information scale. This first isolates graph resolution rather than silently increasing odometry trust. For an independent small-noise chain, equal per-scan weights cannot simply duplicate the same keyframe factor strength; composition/transport must be derived and checked. Existing scan-to-map correlations prohibit calling that convenience model calibrated covariance.

A separate stage replaces compressed fixed-centre loop factors with measured matching residuals that can relinearize. Begin with a sparse CPU GICP/VGICP control on original points and retained centres/scale. [small_gicp](https://github.com/koide3/small_gicp) exposes a practical CPU/Python registration path, while [gtsam_points](https://github.com/koide3/gtsam_points) demonstrates direct factors. The current installed GTSAM and the library's supported versions need a compatibility audit; replacing the environment is not assumed.

Do not optimize the stopped equal-mass shared-plane construction again. New registration factors need support, association, basin and reference diagnostics before real refinement. A preliminary pair optimizer and a fixed BetweenFactor snapshot do not equal a fully relinearized direct factor; that distinction must appear in the report.

This route differs from E1's loop scalar/kernel variants, PFG1's information-shape changes at unchanged centres, and the stopped interpolation screen. It is still established geometric SLAM. Its job is to create a fair strong baseline and determine whether current correction compression actually costs accuracy. No innovation is claimed for ordinary scan-level PGO.

### Route B: make RAP a useful prior for a small metric correction

Use a frozen native RAP pose as the common baseline and learn a bounded local SE(3) residual, instead of relearning a global correspondence transport or changing every generated coordinate:

`T_corrected = T_RAP × Exp(D z)`.

The right/left convention and metric diagonal D must be fixed. A small head receives permitted frozen joint information plus measured residual/support summaries and predicts z. The first numerical control uses direct rigid transforms, so no gradients pass through the frozen RAP backbone or the old full soft-assignment/SVD construction. An optional later measured optimizer starts at this corrected pose. An output bound is a trust-region design choice, not a guarantee of physical accuracy or descent.

All learned controls share the same native pose baseline, active capacity, supervision, measured features, residual statistics and solver. Compare direct descriptors, separated-context tokens and joint-context information under that common base. This avoids unfairly asking the direct baseline to rediscover a pose that the RAP arm already receives. Include geometry-only residual correction, an unchanged native identity residual, and an equal-work geometry control. The final contribution must outperform the strongest relevant control, not merely the weakest token ablation.

The proposed distinction from RLP2 is the output family, baseline and task: bounded correction around an existing native estimate, rather than full pose formation through global soft point assignment. The distinction from NOC4 is a frozen-backbone residual interface, rather than neural velocity/P-objective adapter training. This does not rescue either old experiment.

[Deep Global Registration](https://openaccess.thecvf.com/content_CVPR_2020/html/Choy_Deep_Global_Registration_CVPR_2020_paper.html), [RPM-Net](https://openaccess.thecvf.com/content_CVPR_2020/html/Yew_RPM-Net_Robust_Point_Matching_Using_Learned_Features_CVPR_2020_paper.html) and [Point-TTA](https://openaccess.thecvf.com/content/ICCV2023/html/Hatem_Point-TTA_Test-Time_Adaptation_for_Point_Cloud_Registration_Using_Multitask_Meta-Auxiliary_ICCV_2023_paper.html) prevent a generic residual/refinement/adaptation novelty claim. A modest contribution would have to establish that frozen generative information yields a useful, metric-normalized correction when coupled to independent physical support, beyond descriptor and geometry controls. That claim remains conditional.

A frozen-feature head does not require NOC4 backbone backward to work. It does require exact extraction/runtime validation and independent head/pose gradients. Any route updating native adapters still requires the separate P reproducibility diagnosis first.

### Route C: use a different observation unit for loops

Single keyframes and fixed six-part neighbouring windows have already been screened. A distinct proposal uses compact odometry-bounded submaps for place retrieval, then retains their constituent scan identities when joint RAP predicts a registration hypothesis. Verify the hypothesis on original measured data and use a sparse set of physically supported loop factors. The model supplies a basin/topology proposal, not artificial observations.

[MapClosures](https://github.com/PRBonn/MapClosures) is a strong independent retrieval/proposal baseline. Direct geometry and independent pairwise RAP must receive the same raw support and end-to-end budget. A benefit only from adding more scans belongs to support/context, not specifically RAP's joint reasoning. [RAP](https://arxiv.org/html/2512.01850v2) already addresses multiview registration and [VGGT-SLAM2.0](https://arxiv.org/html/2601.19887v1) already demonstrates model-aware graph integration, so simply copying their architecture is insufficient.

LC0's fixed-keyframe placement decision remains negative. This route changes the measured observation unit and detector; it is not a larger candidate cap, favourable edge subset or old radius rescue. Its strongest local motivation is ATE opportunity. The existing oracle's ter regression is a warning that new constraints need a corrected backend and per-sequence safety. All pairwise relations from one joint generation are correlated: adding an all-pairs clique with independent noise would falsely multiply evidence. Begin with a fixed sparse tree or an explicitly correlated multi-node model, crediting both as existing graph concepts.

## 5. Numerical research and the NOC4 boundary

The correct next native diagnostic asks where equality first breaks. On immutable inputs, inspect repeated full backward before contrasting cache/full; compare upstream endpoint gradients, tail activations, per-tensor gradients and actual update directions. Record dtype, layout/stride, kernel backend, modes, RNG and geometry spectra. Equality of group norms is insufficient.

Version-matched [PyTorch2.7 SDPA](https://docs.pytorch.org/docs/2.7/generated/torch.nn.functional.scaled_dot_product_attention.html) and [SVD](https://docs.pytorch.org/docs/2.7/generated/torch.linalg.svd.html) documentation identify relevant numerical sensitivities. They do not identify the present cause. A prospective alternate-backend/precision diagnostic must preserve the original failed result and record changed operators explicitly; it cannot silently relax the original byte-equality validator.

For a later distinct optimization policy, verify a whole-parameter directional derivative and actual function movement, rather than using a coordinate update bound. [MinBackProp](https://arxiv.org/html/2404.17993v1) and [deep declarative layers](https://arxiv.org/abs/1909.04866) supply relevant derivative designs when an identifiable geometric solver is used. Implicit differentiation does not make ambiguous alignment identifiable or guarantee neural convergence.

The original P path checks rank/spectral separation; generic SVD warnings cannot overturn those gates or prove SVD caused the mismatch. NOC3 establishes feasible conditioned rigid control only. Loss-scale division does not change the intended objective but can affect finite-precision computation; it should be audited as such. No rates, seeds, scaling or step changes are proposed as a continuation of the stopped NOC4 pilot.

## 6. Where originality can be credible

The realistic thesis contribution is a measured algorithmic interface, supported by an explicit failure-mode analysis and full-system evidence. Suitable claim candidates are:

- A frozen generative registration prior combined with a bounded metric residual that improves pose and system behavior beyond equally trained direct/separated-context controls.
- A sparse physical measurement representation of jointly proposed revisits that improves system accuracy without treating generated points or correlated poses as independent observations.
- A demonstrably useful local-versus-global correction design, with a separate measured RAP increment.

None is claimed achieved or globally novel now. Direct GICP, trust regions, Lie residuals, graph hierarchy, learned confidence, attention verification and multiscale descriptors are existing components. The strongest novelty defence is a precise counterfactual: replace the RAP-specific input/operation with an equally capable non-RAP control while retaining the rest; show that both mechanism and final utility diminish. If that ablation does not hold, report a useful engineering result and do not invent a RAP-specific mechanism story.

The earlier originality relaxation makes these conventional combinations eligible for consideration. It does not require pretending their ingredients are new.

## 7. Data, computation and execution design

All six system sequences and the old local/loop cohorts are historically exposed. Fresh process repetitions are not independent scene confirmation; new noise draws test conditional noise robustness only. Future data roles should be grouped by physical sequence/session, with fit/development/confirmation fixed before results. Reserve one external session if available, without asserting its exclusion from local checkpoint training.

The RAP paper's [training description](https://arxiv.org/html/2512.01850v2) includes broad outdoor data and explicitly describes Boreas training use. Boreas is therefore not automatically an unseen-pretraining test, and the local 12-layer checkpoint binding remains unknown. Its KITTI pair threshold is also different from our strict diagnostic. A different dataset name does not resolve provenance.

For future screening, use staged budget envelopes rather than the expensive full-system process at every idea. Proposed starting envelopes, not frozen limits: CPU graph feasibility15min/4GiB; isolated frozen-RAP or tiny-head feasibility30min/3GiB GPU/4GiB RSS; later complete-system comparison at the separately declared system memory class, with all attempts and validations counted. The existing full-system GPU reserved peak differs greatly from tiny neural diagnostics, so their budgets must not be conflated. Profile before choosing any final cap, and retain host headroom/supervision safeguards without claiming continuous historical coverage.

No installation is justified just because a repository exists. Prefer a mathematical/CPU interface prototype and a pinned compatibility audit; use an isolated dependency runtime only under a later concrete execution scope. Do not replace installed GTSAM/PyTorch, acquire large data, or run full-model training during this research task.

## 8. Proposed progression and stopping logic

The [experiment blueprint](EXPERIMENT_BLUEPRINT.md) makes the recommendation reviewable, while remaining a draft.

1. Resolve metric priority and acceptable subsystem changes in the next conversation. Preserve the current baseline and all old decisions.
2. Validate scan-level graph strength/frames/no-op and one measured-factor interface. Stop if the small physical objective conflicts with trustworthy controls or if the engineering comparator fails safety.
3. Establish the new geometry baseline on fixed data. If it provides no useful headroom, do not automatically add a learned correction to conceal that result.
4. Only then test the compact residual component with equal active-capacity controls and varied held-out noises/windows. Require rotation/translation and safety, not loss alone.
5. Advance one surviving component to complete trajectories and a reserved confirmation session. Report odometry/full, ter/rer/ATE, loop counts and total cost together.

A failure retires the declared construction. Any distinct later hypothesis receives its own prospective scope; it is not an excuse for unlimited tuning. A material engineering baseline is useful even if the incremental RAP component fails, but it does not complete the intended RAP contribution.

## 9. Questions deferred to the next conversation

[NEXT_QUESTIONS.md](NEXT_QUESTIONS.md) records the unresolved choices and recommended defaults: primary metric, allowed graph/feature/head changes, experiment budget and timeline, confirmation data, and the required thesis/publication contribution level. None is needed to complete this research synthesis; their answers are needed before freezing execution.

## Evidence and preservation

The [literature matrix](LITERATURE_MATRIX.md) records27 research/concept entries and six implementation/metric entries with primary links and review depth. Local anchors include stage-review-01, E0/E0-H1, MC1/PFG1/LC0, RLP2, CV2/MF0 and NOC0–4. They are existing evidence, not repeated experiments. Current source hashes are checked against the existing benchmark freeze in SOURCE_AUDIT.json. The research does not re-audit every historical artifact or recertify old resources.

Both original Git HEADs/branches and existing dirty work remain. Changes are new research documents and mutable handoff records only. No production/default/backbone/manuscript/reference, scientific seal, numerical output, installation or Git synchronization changed. The next step is a scope decision and design/preflight preparation; research ranking is not execution authorization.
