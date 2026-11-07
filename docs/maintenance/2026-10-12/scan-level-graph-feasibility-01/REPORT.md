# SGC0 — scan-level graph feasibility, 2026-10-12

**VALIDATED_EXPLORATORY_COMPLETE — NO_SAFE_MATERIAL_SCAN_GRAPH_SIGNAL.** The numerical construction is valid, but the fixed six-sequence experiment fails its prospective efficacy conjunction. Stop this exact covariance-allocation/scan-graph candidate without weight, initialization, iteration or gate rescue.

The owner authorized the first recommended study after metric-innovation-research-01. This is a complete CPU experiment on stored E0 A observations, not a new frontend/RAP run. All six sequences and all58 originally admitted loops were included. Both cohorts have already been exposed and are development evidence.

## Outcome

| Sequence | Keyframe B ATE m | Scan S ATE m | B ter % | S ter % | B rer deg100m | S rer deg100m |
|---|---:|---:|---:|---:|---:|---:|
| 00 | 2.754437 | 2.768429 | .518171 | .517783 | .178312 | .178528 |
| 05 | 1.294699 | 1.294299 | .320473 | .320017 | .120951 | .120875 |
| 06 | .332854 | .332858 | .327512 | .326723 | .071239 | .071198 |
| 07 | .326400 | .325927 | .394673 | .394433 | .151539 | .152044 |
| 09 | 1.074523 | 1.074633 | .593652 | .591892 | .106938 | .106778 |
| 10 | .763516 | .763516 | .528520 | .528520 | .204632 | .204632 |
| Mean, all six | **1.091072** | **1.093277** | **.447167** | **.446561** | **.138935** | **.139009** |

Mean ATE worsens by .00220517m (about .2021%), against the required >=5% improvement. Mean ter improves by only .000605472 percentage points (about .1354% relative). Mean rer increases by .0000737489deg100m, failing its nonworse condition. Four of61 tests fail: the ATE improvement and mean rer guards against each of B and native replay R. All per-sequence harm guards, input-normalization checks and sequence10 no-op pass. These are small effects, not severe per-sequence harm or zero numerical change.

Development mean ATE1.46066349->1.46519513m, ter.38871842->.38817425%; exposed07/09/10 ATE.72147982->.72135852m, ter.50561511->.50494833%. The slight exposed-cohort ATE improvement does not override the all-six prospective failure. No GT-conditioned sequence/edge selector or follow-up sweep was built.

S does reduce adjacent correction jumps. For00 the maximum correction translation twist drops .457411->.112986m and maximum rotation .111823->.026575deg; actual adjacent-motion translation change drops .037932->.009981m. For09 correction translation drops .060659->.010456m. S also changes optimized keyframes, including00 maximum B/S relative translation twist .123105m. This is a changed nonlinear graph objective, not merely interpolation of fixed keyframes. Smoother corrections did not yield material metric headroom in this construction.

## Fixed comparison and numerical validity

R exactly replays the current native keyframe graph on original saved matrices; P is the original saved output. B and S share a declared proper-SE3 SVD projection of rotations, preserving translations and all original files. R/P maximum matrix delta<=7.55102e-7; B/R maximum translation<=9.50861e-7m and rotation<=1.59038e-7deg. Thus input normalization does not explain the observed millimetre-level mean ATE change. P metrics independently reproduce the historical values within the frozen tolerance.

B has1800 nodes/1858 factors; S has12296 nodes/12354 factors. S retains every original loop centre/endpoint/Huber1/relfloor weight. Each keyframe odometry interval allocates its original information across the consecutive scan chain using right perturbations and suffix adjoints. No duplicate keyframe odometry factors are added to S. All scan covariances are positive definite and nominal endpoint covariance matches the existing diagonal interval covariance. This is an engineering allocation, not empirically calibrated KISS scan-to-map uncertainty. The correlation counterexample explicitly shows endpoint variance exceeding the independent-chain value.

Eight synthetic chains cover one/two/five/nine increments. Independent SciPy/analytic checks give central-difference Jacobian max2.40035e-10, endpoint Schur relative error7.32934e-11, composition derivative max4.30794e-10 and reverse-covariance relative error4.44248e-16. No-loop, perfect-consistent-measurement recovery and common-world-frame checks pass. Nominal local equivalence does not imply global nonlinear equivalence or correct real noise calibration.

Real S iterations00/05/06/07/09/10=5/5/4/3/5/0, with objective reduction in each loop-bearing sequence. Sequence10 stays unchanged within1e-5 and has zero optimization iterations. Native B/R iteration/objective internals are not separately stored; their full trajectories and factor counts are available. The study contains24 synthetic GTSAM calls,18 real graph construction calls and18 shared-source validation replays; no neural optimizer calls.

## Provenance and independent validation

1155 input/source identities froze before the numerical payload, incorporating the prior review's1107 distinct-file observations. Current benchmark71 sources/config/checkpoint identities and earlier delivered artifacts were rehashed without model/checkpoint deserialization. Both original repository HEADs/branches and two/nine tracked dirty sets matched throughout. Shared proper inputs are new experiment data, not edits to historical files.

The complete55-file all-six prediction bank sealed before numerical GT access. Construction consumes an explicit loop whitelist, excluding the saved GT error fields. GT and calibration files were first hashed, then read numerically only by evaluation after bank sealing. All source IDs/timestamps and complete keyframe coverage were verified.

The independent validator rebuilt every scan covariance with separate adjoint equations, independently computed Horn rigid-alignment ATE and all36990 KITTI segment records for O/P/R/B/S, recomputed diagnostics/cohort means and all61 gates. Metric max delta4.88082e-13; covariance relative max3.22689e-14; diagnostic max delta2.95223e-12. All18 R/B/S graph replays have maximum trajectory delta0. These replays share the existing/frozen GTSAM implementation; they are not independently implemented nonlinear optimizers. Synthetic optimized endpoints are checked against known fixtures, not independent LM implementations. No raw frontend, feature, RAP generation, descriptor, physical time/calibration or independent site replay.

## Resources and preservation

All six attempted processes succeeded; no scientific execution failure, source repair or numerical/gate relaxation. Combined child payload67.814944382s, full supervised process wall82.6395134s, maximum full-process RSS120012800bytes (about .112GiB), GPU calls0. All900s/4GiB/512MiB prospective caps pass. Artifact size before final documentation/seal was about20.46MiB; see RESOURCE_AUDIT.json for final closing size. Windows launch/exit and periodic headroom logs are present for every process; minimum observed headroom43163410432bytes (about40.2GiB). Sampling does not certify unsampled host peaks or future runtime. Initial imports/WSL startup and final documentation/identity bookkeeping are outside the payload figure; later validator/evaluator imports inside a stage are conservatively counted. This is offline graph timing, not full system latency.

Original sources, default behavior, checkpoint/config files, GT, old deliveries/seals/failures and historical resource gaps remain. NOC4 remains INCOMPLETE with P replay prerequisite; shared-plane and other native/geometry stops persist. No install, process restart, production/backbone/manuscript edit, commit or Git sync.

## Next judgment

This weakens the proposition that merely expanding variables and distributing the same admitted loop corrections is the next material metric lever. It does not prove every scan graph, information model or joint measured solver ineffective. Do not tune this construction. The next distinct DESIGN_ONLY question is whether an actual physically supported registration objective can improve loop measurements under a strong geometry control. Retain E0/KISS and the existing graph during that measurement study, so measurement quality and graph resolution are not changed together. See NEXT_ROUND_PLAN.md and INTERFACE_INVENTORY.md.

Ordinary covariance transport/scan PGO is prior art. This round establishes no novel mechanism, RAP-specific increment, physical accuracy, independent generalization or system improvement.
