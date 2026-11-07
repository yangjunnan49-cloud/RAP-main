# Attempt map by mechanism and evidence role

Read together with [REPORT.md](REPORT.md). This is a family-level navigation map,
not a summed count of runs or a replay certificate. Historical details below
come from the full current AGENTS and linked reports. "Stop" always refers to
the exact recorded construction, not a universal impossibility result. Frozen
scientific decisions, original failed sources and partial artifacts stay intact.

## Foundations, legacy work and system comparison

| Attempt/family | What was tried | What survives | Interpretation now |
|---|---|---|---|
| Legacy RC/P0-P4/S0-S1 | Robust weighting/NMS, yaw/odometry hints, uncertainty, verifier swap, hierarchical N-way, maps, correction, conformal | Seven saved PGO baselines replay; mixed N-way outcomes; correction signal; source artifacts | Historical claims require September audit qualifications; no blanket adoption of old DONE/PASS or "only lever left" prose |
| Legacy edge-cover trimming | Preserve both endpoints when trimming joint batches | Specific bipartite-layout failure and engineering repair recorded | Useful structural lesson; no general N-way accuracy claim; new NJE0 is separately negative |
| M0/M1 | Preserve and index legacy state | 1,568-file, 4.63 GB same-volume snapshot; registry | Preservation positive; independent backup and historical identities remain limited |
| M2/F02/F03/F11/F18 | Protect fits, fix metrics/frame IDs/map exclusions/empty fallbacks | Representative numerical and source-chain checks pass | Correctness gains; no retroactive repair of old numerical results |
| M3 | Same-generation measurements, causal features, grouped pairs, full candidate logging | Fresh pilot, 40-edge replay and clean-cohort comparators | Traceable measurement chain; cohort has no dangerous accepted examples, so no population risk calibration |
| Initial full core runs | POSS and KITTI00/05/06 from raw scans | Corrected core baseline; loops often lower first-pose APE | Metric tradeoffs already visible, particularly 06 ter |
| O1 | RAP-initialized ICP | Improves 05 first APE, harms others | Complete negative practical screen; no default promotion |
| O2 | Increase candidate budget 12 to 40 | More accepted safe edges, greater verification work | Complete negative; more edges do not ensure better trajectories |
| O3 | Balanced six proximity/six SC slots | 00/05 partial improvements; common-edge diagnostic preserves directions | Complete negative practical conjunction; 05 aligned APE/ter worsen |
| Matched ICP comparators | Identity/odometry initialization on common candidates | RAP beats these on several first-APE rows; ICP better on 05 | Bounded registrar comparison, not universal superiority |
| HC-V1 | Literature table and same-data KISS-SLAM | Initial KISS defaults outperform old full baseline | Motivated E0; old K4/NMS10 table prose corrected to actual K1/NMS0 |
| E0 / E0-H1 | KITTI correction versus ranges/voxel and combination | Large correction-only drift improvement, later fixed-system transfer | Strongest engineering positive; no new RAP mechanism, no unseen-domain claim |
| October 11 benchmark | Six sequences, two full systems, three processes each | 36 complete admitted runs; RAP lower all-six ter, higher ATE | Latest complete system result; repetition is not scene independence; old resource/supervision gaps retained |

Sources: [audit](../../audit-2026-09-09/AUDIT_REPORT.md),
[O1-O3](../../2026-09-13/OPTIMIZATION_SYNTHESIS.md),
[E0](../../2026-09-26/e0-frontend-01/REPORT.md),
[E0-H1](../../2026-09-27/e0-heldout-01/REPORT.md),
[benchmark](../../../meeting_20261011/benchmark/REPORT.md).

## Hypothesis availability, support and acceptance

| Attempt/family | Question | Actual result | Consequence |
|---|---|---|---|
| HL0 / original HL1 | Engineering feasibility and hard-pair cohort | Engineering passes; original 05/06 cohort inadequate before inference | HL1 is inconclusive data, not a model negative |
| HL-V2 | Four native hypotheses and causal support ranking | Confirmation oracle H1 passes; support H2 fails | Candidate headroom exists, fixed support score cannot recover it; stop neural expansion from that result |
| SC-V1 | Isolate support observations from score/budget | New discovery cohort inadequate | Data stop; do not report efficacy failure |
| SC-V1.1 | Matched support/pooled/query-budget/rigidity controls | Fixed support score fails confirmation; ordinary control not beaten | Complete negative exact selector family |
| PG-V1 | Pooled short-submap proposal context on 09 | Positive strata absent before inference | Data stop, no model result |
| Boreas access | Public cross-session access and metadata feasibility | Two raw scans/ten objects; position overlap | Access positive, not point overlap or adequate experimental cohort |
| PG-DEV | Pooled proposal context on observed 00/08 | Modest gains, required oracle/executable gains fail | Complete negative; no expansion or favorable P1 promotion |
| Rejection diagnosis | Does consistency identify incorrect accepts? | Consistent wrong candidates, low scalar separation; many correct rejections | Additional rejector cannot recover rejected correct poses or manufacture missing candidates |
| F1 | Implement structured six-part generation safely | Native replay and projection controls pass | Engineering only |
| F2 | Per-step short-motion group projection versus native/final/pooling/anchor | No mechanism conjunction; pooled 00 recall partial positive | Complete negative; no S/P/gate rescue |
| F2 postmortem | Locate availability/selection/rejection failures | 08 missing good candidates dominates; wrong accepts often have none | Diagnostic, not a physical cause or selector |
| R0 | Fixed local ICP from native poses | No material recovery/safety conjunction | Complete negative fixed refinement |
| G0/G1 | KISS-Matcher on same anchor/full raw clouds | No missing-candidate recovery; native wins strict counts | Complete negatives at fixed configurations; unequal full-scan budgets disclosed |
| V0 | Fixed ray score and translation grid | Adequate proxy coverage, no useful recovery | Complete negative; visibility-guided rescue stopped |
| RVC0 | Fixed stored-pose batch ranking with radial contradiction/support and NN controls | Three additional correct plus two incorrect per sequence; gates fail | Numerical negative plus late scope-selection correction; not newly discovered ray evidence |

Sources: AGENTS historical HL/SC/PG/F2 sections,
[V0](../../2026-09-28/v0-ray-visibility-01/REPORT.md),
[F2](../../2026-09-27/f2-structured-dev-01/REPORT.md),
[RVC0](../ray-consistency-ranking-01/REPORT.md),
[stop navigation](../strategy-revision-02/STOP_INDEX.md).

## Features, sampling and flow information

| Attempt/family | Question | Actual result | Consequence |
|---|---|---|---|
| D0 | Earlier native flow poses as candidates | Too few hard recoveries; penultimate selection worse on 00 | Complete negative saved-step route |
| S0/S1 | Five versus ten native steps | Reproduction passes; complete 800-generation comparison fails useful gates | Executability positive, efficacy negative; no step-count sweep |
| September C0 | Was the descriptor checkpoint absent/all zero? | Strict descriptor keys load, finite nonzero features | Rules out that concrete fallback explanation, not weak information |
| C1 | Descriptor true-versus-shuffled top-1 information | Hard08 median signal below material gate | Diagnostic negative; not a theorem of no useful model information |
| C2 | Feature-to-point shuffle intervention | Material pose responses and degraded strict outcomes | Feature reliance positive; destructive OOD intervention is not an improvement |
| C3 | Fixed FPFH comparator | No material advantage over miniSpinNet signal | Complete negative fixed descriptor comparator; support context differs |
| C4 | Anchor versus support descriptor shuffles | Anchor control responds; support ordinary gate fails, other pairs respond | Heterogeneous model use, not proof of irrelevant support |
| C5 | Causal persistence feature mask | No hard08 recoveries; loses one previous 00 success | Complete negative fixed mask |
| C6 | Transport an earlier loop through local odometry | No hard-pair strict recovery; incorrect donors on hard08 | Complete negative fixed donor policy |
| I0/I1 | Bind and test raw intensity | Binding passes; fixed cross-visit information gate fails | Available channel, no measured matching/pose gain; no intensity fusion rescue |
| Input convention audit / P0 | 0.25 m/FPS/full-voxel descriptor support versus F2 recipe | Initial RNG defect retained; corrected bank complete, coverage improves, information gate fails | No P0 RAP generation was admitted; no causal sampling explanation |
| M1 | Support-derived poses from saved part poses | Four hard08 strict recoveries versus required five | Complete negative candidate screen; no selector/graph result |
| FDI preflight/screen | Joint flow response versus independent/temporal/geometry | Engineering passes; unique joint information and 00 safety fail | Complete negative exact response route; not calibrated uncertainty |
| SID0 / D1 | Shared-identity feedback within sampling | Algebra/toy preflight passes; real response only 2/4 versus 4/4 | Exact feedback construction stopped before accuracy evaluation |
| RAD1 | Original-point associations from final raw endpoints | Degeneracy repair retained; complete retry fails hard recovery/safety | Complete negative decoder; no graph promotion |

Source: AGENTS complete September 28-29 and October 5-7 sections; linked reports
remain governing. No neural or numerical result in this table was replayed here.

## System placement, geometry, physical discrepancy and mapping

| Attempt/family | Question | Actual result | Consequence |
|---|---|---|---|
| E1 | NMS, GNC and loop weighting on frozen graphs | No >=5% mean ATE successor; GNC rejects no loops | Complete negative fixed backend comparison |
| System opportunity / joint-loop oracle | Where can current edges affect metrics? | ATE headroom, little ter headroom; joint oracle still mixed | Evaluator-only opportunity, not executable method or global ceiling |
| Fixed dense propagation | Interpolate keyframe corrections | Mean ter increments too small | Complete negative fixed interpolation |
| GeoTransformer feasibility / online swap | Official checkpoint on all 71 online attempts | Engineering passes; RAP46/Geo44 strict poses; system gains/safety fail | Complete negative swap; no universal matcher ranking |
| Temporal identity / RPC0 | Source, convention and raw geometry behind 09 conflict | Available bindings/local controls pass; broad cross-visit discrepancy persists | Physical cause unknown; no reference edit or removal of 09 |
| PFG0/PFG1 | Geometry-derived loop information shape | Synthetic blind spots explicit; six-sequence material/safety gates fail | Complete negative fixed information-shape system screen |
| LC0 / MDC0 | Retrieval placement and ter/ATE decomposition | Idealized ATE gains fail full ter/safety conditions; cancellation explains arithmetic | Evaluator diagnostic only; no cap/radius/redistribution rescue |
| MMR0 | Joint measured point-plane local map reoptimization | Partial ATE gains, failed coupled pose criteria; reference cost conflicts | Complete negative exact objective; not proof reference wrong |
| SMP1 | Shared-plane map representation | Support failure and unregularized instability; small regularized gains | No eligible revisit candidate |
| SMP2 | Hold out complete patches and preserve support | Support repaired; mean ATE gain 1.14%, below material gate | Complete negative exact support-preserving local construction |
| CV1 | Rigid versus joint cross-visit map refinement | Translation/ATE partial gains; rotation safety fails; little joint increment | Complete negative full-pose conjunction |
| CV2 | Protect rotations and refine translation | Mean ATE gain 4.11% versus 5%; 05 harm; 06 benefits from free rotation | Complete negative; no universal rotation lock |
| MF0 | Change where patch memberships are formed | Costs still prefer original poses even with reference-formed sets | Formation location alone does not explain objective/reference conflict |
| SGC0 | Scan graph and covariance allocation | Small ter change, ATE/rer conjunction fails | Complete negative exact graph allocation |
| MGR0 | GICP with RAP/odom/identity/FGR initializers and selectors | Rotation improvement, about 0.3% translation gain, joint gates fail | Complete negative; no demonstrated useful RAP increment |
| CCR0 | Three-frame causal physical-return context | Complete 58-loop bank; small paired changes, useful conjunction fails | Complete negative exact context; no dependent graph/residual expansion |
| NJC0/NJE0 | Nonlocal loop-connected joint generation | Topology passes; full four-group comparison fails all three gates | Topology prerequisite positive, joint efficacy negative |

Representative sources:
[RPC0](../../2026-10-12/reference-physical-consistency-01/REPORT.md),
[CCR0](../../2026-10-12/causal-context-registration-01/REPORT.md),
[NJE0](../../2026-10-15/nonlocal-joint-comparison-01/REPORT.md),
and AGENTS mapping/system sections.

## Learned readout and native/shadow adaptation

| Attempt/family | Question | Actual result | Consequence |
|---|---|---|---|
| TR0 | Export joint tokens without changing native inference | Exact extraction/bindings/invariance pass | Interface only |
| RLP1 | Weak correspondence-label readout | Engineering passes; 06 has only 15 positives versus 20 required | Prerequisite stop; no trained head or model error result |
| RLP2 | Continuous pose-supervised D/I/J matching head | Nine fixed fits/replays complete; J beats I but fails D and strong G3/KISS controls | Complete negative useful readout comparison |
| Adaptation design | Last-two-layer adapters/velocity head | Initial novelty rejection was a design decision | Superseded as a universal admission rule by owner's engineering relaxation; not a failed experiment |
| NOC0 | Tiny native-output capacity and real-window capability | Fixed-noise fit positive; fresh noise unstable; original fp16 gradient underflow repaired separately | Capacity witness, not robustness or a new physical method |
| NOC1 | Zero-update fresh-noise census | Four means improve; only one full cell passes | Complete negative conjunction, not universal no-learning claim |
| NOC2 | Metric relative-pose objective with affine control | Affine target representable; optimization ends near 20 mm, fails 5 mm gate | Control convergence negative; native V/P fits not executed |
| NOC3 | Proper rigid metric control, conditioning and gauge | All four rigid controls fit; scaling improves Hessian condition | Numerical control positive, several factors changed, no unique cause |
| NOC4 original / runtime recovery | Native V/P fit preflight and external exits | Original comparison incomplete; targeted authorized overlay recovery verifies runtime | Runtime positive does not supply fit result |
| NOC4 attempt02 | Restored optimizer probes and full/cache validation | Loss rises; P repeat mismatch; zero retained fit updates | Incomplete dependent comparison, failed preflight |
| NBR/AOD | Locate repeated gradient differences and attention behavior | Forward/upstream exact; P gradients differ; bounded local default/math differences | Cache not sole explanation; no official-backend defect proof |
| NMR/FPC | Math attention, FP32 and objective arithmetic controls | Repeats exact; 8/12 direction criteria each | Reproducibility positive, derivative conjunction not admitted |
| DTC/SFC | Fixed-prefix double tail and signed functional steps | 12/12 derivative directions; bounded descent/ascent pass | Positive for changed shadow function only |
| ADR/SAR | Activated LoRA A/B derivatives and exact sampler extraction | Derivatives/lifecycle/independent Horn checks pass | Prerequisites positive; nominal capacity is not full active rank |
| HFIT | Forty retained shadow updates, then full prediction bank | Loss about 2% lower; artifact cap stops prediction; no full heldout metrics | Incomplete comparison, not generalization failure/success |
| FCE/FHR | Frozen context interface and metric-head derivatives | Context isolation, 6,150 locally active columns and numerical checks pass | No efficacy admission |
| CDG/GSG | Copied-descriptor support and coordinate-only geometry control | Descriptor uniqueness fails; ordinary geometry solves exact congruent copies | Retire copied-congruent fixture as efficacy evidence |
| BRF | Necessary bound for small native-base correction | Optimistic correction cannot meet all KISS safety conditions | Exact family excluded before head/fitting |

Sources: [RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md),
[DTC](../../2026-10-13/native-double-tail-control-01/REPORT.md),
[HFIT audit](../../2026-10-13/shadow-conditioned-fit-pilot-01/execution-stop-audit-01/REPORT.md),
[BRF](../../2026-10-14/bounded-native-residual-feasibility-01/REPORT.md),
[RBA](../../2026-10-15/release-backend-attribution-01/REPORT.md), and full AGENTS.

## Sources, reference roles, storage and execution controls

| Attempt/family | What was established | What was not established |
|---|---|---|
| LPC0 | Lossless reconstruction of all 100 available prefixes, smaller encoded representation | Self-contained full bank, missing predictions, whole-dossier bound or model gain |
| LCP0 | Available NPZ serialization checks and retained partial archive | Complete archive/reconstruction; time cap failed and original INCOMPLETE remains |
| APL/BEJ/BPC | Controlled reservation/journal/pipe cases and native exits | Universal arbitrary-writer, concurrency, process-tree or filesystem guarantees |
| WPC/NMQ | Byte/native-exit controls and three new retained-handle OS peak controls | Old WPC completeness or observer full-lifetime peaks; old gaps remain |
| PSR/PEL/POP | Available metadata/exposure roles; POSS-B outcomes were used in downstream analysis | Untouched POSS-B confirmation, exact complete execution lineage or independent truth |
| FTI | Exact sensor/world/clock/point-time ambiguity examples | Sensor axes, gravity, hardware clocks or per-return timing from monotone timestamps alone |
| PRI | Three hosted-matching weight identities | Training membership, full runtime equivalence or native backward validity |
| DSR | All 156 demo files/header inventory and exact loader reference role | External measured demo reference or source alignment truth |
| RBA | Exact tested local SDPA attribution and saved direction-count reconciliation | Immutable official FlashAttention runtime or unique historical cause |
| MDA | Full pinned 3,243-point-file catalog comparison, zero byte-identical local members | All-history/physical-scene distinctness or reference transplantation |
| ODA/DRD | Full original ZIP directory CRC/length consistency and source-link binding | Remote member cryptographic identity, registration reference construction |
| ADC | One complete finite public query and selected reference-related comments | Global absence; issue 3's sole comment was not inspected |
| JMD | Clear unposed joint task/control contract; shared-pose cycles are tautologies | New method, authenticated original-demo references or efficacy admission |
| RegX-B1 | Authorized exact eight files and source/schema identities | Numeric point/matrix validation, physical truth, training exclusion |
| RegX-B2 | Authorized pinned viewer and demonstrated README/code direction conflict | Executed canonical batch or corrected physical reference |
| RegX-C0 | Custom protocol/implementations/static review/source freezes | Any executed synthetic/actual numeric stage; guard stopped prestart, syntax/runtime untested |

Sources: October 14-16 sections of AGENTS and the linked dossiers. Latest C0
[report](../regx-interface-contract-01/REPORT.md) and
[runbook](../regx-interface-contract-01/RUNBOOK_CN.md) govern its first execution.
This map never authorizes replay, a cap reset, new acquisition or model use.
