# Weekly strategy discussion — 2026-10-20

Status: PLANNING_ONLY. This is a reviewable strategy, not a frozen scientific protocol, execution authorization, or amendment of an old stop. The owner explicitly selected **system metrics and deliverable results** as this week's priority. The broader research objective remains unresolved.

## Recommendation

Keep the corrected E0 frontend and the existing RAP checkpoint fixed. Focus on the large aligned-ATE deficit on 00/05 while protecting the useful KITTI drift performance. First make one bounded decision about which system component is worth changing; then invest in one engineering candidate. Direct point-cloud matching factors are the preferred conditional backend candidate, with mature local-map loop integration as an alternative if the evidence points to missing or differently supported observations.

Do not require a new neural mechanism before recognizing useful engineering. Evaluate any incremental RAP contribution separately. This priority does not imply abandoning the original research objective or declaring the thesis complete.

## Established context

The latest complete-system comparison is still October 11: six sequences, two pipelines, three process repetitions, 36 admitted runs. The October 18 presentation, delivered October 20, synthesizes results documented through October 17; it contains no later system experiment.

| Sequence | RAP ter % | KISS-SLAM ter % | RAP aligned ATE m | KISS-SLAM aligned ATE m |
| --- | ---: | ---: | ---: | ---: |
| 00 | 0.518171 | 0.575272 | 2.754437 | 0.916513 |
| 05 | 0.320473 | 0.517250 | 1.294699 | 0.661035 |
| All six | 0.447167 | 0.478614 | 1.091072 | 0.699689 |

Values are quoted from the existing broad review's saved-scalar table, not newly evaluated trajectories. KISS here means the complete KISS-SLAM pipeline, not KISS-ICP odometry. These are different pipelines, not a controlled RAP-on/off ablation.

E0's intrinsic correction is a demonstrated engineering gain. Existing RAP loops improve ATE relative to E0 odometry, with mixed drift effects. The saved online ledger contains 12 accepted loops each on 00/05; strict correctness is 10/12 and 12/12 respectively. Correct pairwise poses therefore do not by themselves establish optimal sequence trajectories. Those counts are not retrieval recall estimates.

C0 is complete for its explicitly custom input/serialization/inverse-transform contract. It creates no new observation, model prediction, registration result, or independent scene. The canonical-source query and exact issue-reply query are closed. Resource polling, further source inventories, and replaying C0 do not resolve this week's system question.

## Candidate ranking

| Priority | Candidate | Reason to consider it | Main limitation | Discriminating outcome |
| --- | --- | --- | --- | --- |
| First decision | Component comparison using the existing KISS-SLAM and E0 archives | The stronger ATE system is already locally available; establish what can be compared before building another solver | Source frames, map anchors, preprocessing, support, topology and frontend differ | Decide whether a fixed-observation backend test is justified or a distinct observation-unit change is more plausible |
| Main conditional implementation | Joint direct matching factors at the existing loop endpoints | Changes how observations participate in the global solve instead of merely changing a pose's scalar weight | Pairwise GICP has little translation gain; previous geometry/reference conflicts may persist | A useful global trajectory gain over both the current graph and a matched frozen approximation |
| Alternative | Mature local-map loop observation/integration | KISS-SLAM already supplies a successful full-system engineering reference | This changes support/retrieval and requires its own scope; cannot be mixed into the backend experiment | A complete system improvement attributable to the new observation unit, with an honest geometry control |
| Later | Bounded RAP contribution study | Valuable if the engineering platform supplies a real metric opportunity | Prior heads, native/shadow fitting and joint generation do not supply that opportunity automatically | Additional utility versus the strongest geometry and total-work control |

The first row is a short decision stage, not another broad audit campaign. Existing E1, LC0, SGC0 and opportunity/oracle diagnostics must be reused as evidence, not replayed. A saved KISS graph is not itself a deployable prediction on an E0 frontend.

## First decision: locate an actionable difference

Use the existing complete-system outputs and their actual source manifests. The inspected 00 KISS output directory contains configuration, a trajectory graph, a local-map graph and map PLYs. This establishes file availability only; graph conventions, node/source bindings, sufficient raw lineage, and replayability have not been newly validated.

Compare three concrete interfaces: local odometry/configuration; loop observation support and endpoints; and graph/dense-trajectory construction. Separate the current system comparison from a causal component claim. Reuse saved error/segment results rather than rerunning leave-one-out or oracle work.

If an isolated component replay is proposed, require an explicit source-frame and anchor transform for every imported observation. Do not equate graph node numbers, align nodes with GT, or treat a KISS local-map registration as a single-scan measurement. Rebuilding a local map with E0 can change its geometry, so an archived KISS measurement is not automatically valid for that rebuilt map. A component interchange may be unidentifiable from available archives; report that limitation rather than inventing a full factorial causal result.

Time-box this decision to roughly half an engineering day. Its deliverable is one component-difference table and a choice of the next comparison, or a precise reason why the archives cannot support that choice. No repetitive census, cryptographic recertification of all history, or fresh oracle study is needed. This estimate is a planning allocation, not an execution cap.

## Preferred conditional question: compression versus joint measurement

Question: **With E0 odometry, graph nodes, admitted loop endpoints, physical support and solver budget held fixed, does allowing loop geometry to relinearize with the global poses improve complete-trajectory ATE over representing it once?**

The mechanism is a changed coupling between observations and the global pose estimates. It adds no new sensor information. Direct factors are a mature engineering approach, and there is currently no evidence that the fixed pose representation is the cause of the 00/05 deficit.

| Arm | Loop representation | Purpose |
| --- | --- | --- |
| B | Existing admitted RAP pose constraints and current graph | Reproduce the existing system output |
| Q | A single frozen local quadratic approximation to the declared physical matching cost | Separate an initial local information change from subsequent nonlinear measurement updates |
| D | The same declared physical cost and support, relinearized/rematched during joint optimization | Test the practical direct-factor package |

Q and D must start from the same declared state and share initial residuals, gradient, curvature convention, normalization and robust loss. Q is a local quadratic factor with its linear term; a covariance alone is not an equivalent approximation. D combines relinearization and rematching in this first comparison; do not claim to identify their individual causal shares.

Use the current keyframe variables initially. Do not combine this with SGC0's scan-graph allocation, new retrieval, new point budgets, a shared-plane objective, or a per-pair GICP sweep. Replace the representation of a given loop observation; do not add a full-strength matching factor alongside its derived pose factor and count the same evidence twice. The E0 motion prior and points also share observations, so engineering weighting must not be described as independent calibrated Bayesian fusion.

This question differs from E1's weights/NMS/GNC, SGC0's expanded graph with unchanged loop centres, PFG's fixed-centre information shapes, MGR0's independent pair refinement/selection, and MMR/SMP/CV/MF shared-plane constructions. That distinction is necessary but not sufficient for admission. If implementation reduces to one of those exact stopped constructions, stop the proposal before payload. No existing negative result changes status.

The realistic counterevidence is substantial: MGR0's translation gain is only about 0.3%; MMR/CV/MF show lower geometry costs can accompany worse reference poses. Consequently, a lower direct-factor objective or a smoother map is insufficient. A distinct global coupling must earn its implementation cost through trajectory metrics.

For the first real screen, a whole-sequence 00/05 graph replay using all their admitted loops is more relevant than selecting attractive local windows. These two sequences are deliberately chosen exposed development targets, not independent confirmation. The remaining four sequences, including 09 and the no-loop 10 case, are required before claiming a general system successor. This is a new engineering question, not permission to choose 00/05 to rescue NJE0 or another failed all-sequence gate.

## Metric decision and RAP role

Proposed new decision rule, to be finalized before new predictions: ATE is primary; require at least 5% relative reduction in the 00/05 mean against B and the strongest matched approximation control, with improvement on both targets. Preserve mean ter relative to the current RAP system; proposed per-sequence harm limits are 0.01 percentage point ter, 5% ATE, and 0.01 degree/100m rer, with mean rer nonworse. Keep all absolute values, including failures. These are discussion thresholds, not a protocol freeze or a change to any historical gate.

Report the remaining absolute ATE gap to KISS-SLAM. A 5% gain against our own weaker ATE baseline does not establish competitive superiority. Runtime and peak memory are part of the deliverable; compare saved-graph cost separately from new complete-pipeline cost. Only a promising fixed candidate earns one complete-system comparison; do not start with three repetitions of every speculative arm.

If D beats B but not Q, there is no demonstrated need for the more expensive direct package. If neither is useful, stop this exact candidate without weight/radius/point/iteration rescue. If D works under ordinary geometric initialization, recognize its engineering value. If RAP improves success, robustness, or work under the same observations and solver, assess that increment separately.

An initializer ablation on the RAP-admitted loop set is conditional on that set; it is not an end-to-end no-RAP system. A complete RAP contribution claim requires accounting for the proposal/admission path and RAP's full inference cost. Joint shared-pose cycle closure and locally active features are not substitute outcomes.

## Implementation economy and proposed weekly delivery

Use existing numerical tooling for a bounded factor feasibility test where possible. Check only the failure modes relevant to this factor: transform direction/units/gauge, no-loop/no-op behavior, known-transform recovery and an independent derivative check. Reuse established evaluators and source-binding tools. New infrastructure should be justified by a named decision.

GLIM provides established direct submap matching in a global optimization objective; its published sensor setup and scores are not a local performance guarantee. The author-maintained gtsam_points library lists integrated ICP/GICP/VGICP factors. Its documented GTSAM/CUDA version combinations require compatibility checks; availability on the web does not establish an installed compatible API. Do not turn the first screen into a GTSAM replacement, CUDA build or environment migration campaign. A later integration would need pinned sources, an isolated dependency plan and a concrete benefit.

Suggested order, contingent on results rather than a promise of completion by a particular date:

1. First half-day: finish the component decision and one prospective comparison specification.
2. Next one to two workdays: a bounded valid implementation and the complete 00/05 development decision table.
3. If promising: retain the exact candidate, test the other four existing sequences, and run a complete-pipeline comparison under its own resource scope.
4. Weekly output: a runnable isolated candidate or a precise stop decision, complete metric/cost tables, trajectory/map figures, and a short explanation of which component supplied any gain. An unchanged baseline rerun alone is not method progress.

All six KITTI sequences are exposed development evidence. Any later reserved session needs explicit data roles and an untouched selection procedure; process repeats and a new dataset name do not establish independent scenes or RAP pretraining exclusion.

## Evidence consulted and limits

This discussion read the current handoff and governing sections of AGENTS, navigated historical family topics, and inspected the following primary local reports. It is not a new all-history artifact verification or numerical replay.

- [Meeting delivery and candidate next step](../../../meeting_20261018/HANDOFF.md)
- [Latest phase record](../PHASE_RECORD.md)
- [Broad review](../../2026-10-16/broad-state-review-01/REPORT.md) and [family map](../../2026-10-16/broad-state-review-01/ATTEMPT_MAP.md)
- [Stop index](../../2026-10-16/strategy-revision-02/STOP_INDEX.md)
- [Latest benchmark](../../../meeting_20261011/benchmark/REPORT.md)
- [E0](../../2026-09-26/e0-frontend-01/REPORT.md), [E1](../../2026-09-27/e1-backend-01/REPORT.md), and [system opportunity](../../2026-09-29/system-opportunity-audit-01/REPORT.md)
- [SGC0](../../2026-10-12/scan-level-graph-feasibility-01/REPORT.md), [MGR0](../../2026-10-12/measured-gicp-registration-01/REPORT.md)
- [MMR0](../../2026-10-09/measured-map-reoptimization-01/REPORT.md), [CV1](../../2026-10-09/cross-visit-map-pilot-01/REPORT.md), [MF0](../../2026-10-10/membership-formation-diagnosis-01/REPORT.md)
- [NJE0 next decision](../../2026-10-15/nonlocal-joint-comparison-01/NEXT_DESIGN.md)
- [C0 numeric report](../../2026-10-16/regx-interface-contract-01/NUMERIC_REPORT.md), [post-C0 decision](../../2026-10-17/autonomous-continuation-05/POST_C0_DECISION.md), and [latest mechanism assessment](../../2026-10-17/autonomous-continuation-06/MECHANISM_DECISION_CN.md)
- [Existing literature matrix](../../2026-10-12/metric-innovation-research-01/LITERATURE_MATRIX.md) and [conditional blueprint](../../2026-10-12/metric-innovation-research-01/EXPERIMENT_BLUEPRINT.md)

Primary sources checked online on October 20 for the limited planning claims above: [GLIM](https://arxiv.org/abs/2407.10344), [gtsam_points author documentation](https://github.com/koide3/gtsam_points), and [KISS-SLAM](https://arxiv.org/html/2503.12660v1). KISS-SLAM combines local maps, density-image loop detection/registration and fine-grained correction; its whole-system result does not isolate one interchangeable component. These page reads are not a new model/data/package acquisition, canonical-runtime authentication, or exhaustive literature search.

This turn creates only this planning document. No model, solver, pose metric, new benchmark, dependency install, outreach, scheduler, Git action or goal-status change is made. Existing seals, caps, stopped families, incomplete fits/archives, official references and the owner's outreach decline remain intact. AGENTS and the latest phase handoff are not rewritten to imply an admitted next experiment.
