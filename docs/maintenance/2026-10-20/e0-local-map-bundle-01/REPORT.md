# LMB0 — large ATE benefit, failed drift-preserving conjunction

Status: **VALIDATED_COMPLETE_WITH_PARTIAL_ATE_BENEFIT_AND_FAILED_ORIGINAL_CONJUNCTION**. Preserve the original construction and negative gate. The conditional ALL_SIX_EXTENSION_PLAN is not admitted by these results. No production/default or library source is changed.

## Actual comparison

All7302 raw files match the original E0 input freeze. Every00/05 frame is processed using the fixed E0 poses, the same1.5--80m range and0.205degree correction. The existing installed KISS-SLAM map/detector/geometry/backend bundle supplies a different observation unit. No RAP or odometry alignment call occurs in M; the E0 frontend is cached, so this is not a complete raw-frontend pipeline timing or new RAP gain.

00 produces32 local maps,7 accepted loops in32 map queries;05 produces19 maps,6 accepted loops in19 queries. Every query and raw hash is retained. Directly consumed frame membership and reset anchors are explicit. Inherited native voxel support has only conservative source-prefix lineage, not per-return attribution. Selected installed Python/pybind files and package versions are frozen; this is not complete authentication of all transitive native libraries or their build chain.

| Sequence | Arm | Aligned LiDAR ATE m | KITTI camera ter % | rer deg/100m |
| --- | --- | ---: | ---: | ---: |
| 00 | Current E0/RAP B | 2.754436970 | 0.518170683 | 0.178312486 |
| 00 | Local-map M | 0.887838583 | 0.571053798 | 0.152868730 |
| 05 | Current E0/RAP B | 1.294699362 | 0.320473024 | 0.120950742 |
| 05 | Local-map M | 0.359070270 | 0.322511469 | 0.106117236 |

The mean ATE reduction is large, while00 ter regresses by0.052883115 percentage point and mean ter increases. Original mean-ter nonworse and00 per-sequence ter-harm tests fail; the frozen conjunction is false. The new result is a measured engineering tradeoff, not a retroactive PASS. Both targets retain lower ATE; rotation drift also decreases. The small05 ter increase stays within the declared individual harm allowance.

For context, the October11 complete KISS-SLAM means are00 ATE0.916513m/ter0.575272% and05 ATE0.661035m/ter0.517250%. M is better at both displayed metrics on these two exposed development sequences, but this cached-E0 prototype and the archived complete KISS pipeline differ in work and implementation. No six-sequence or independent generalization claim follows.

## Validation

The synthetic fixed-E0/no-loop interface returns zero pose discrepancy. All real adapter relatives independently match within4.122e-13. Complete predictions seal before numeric GT. Independent Horn alignment and explicit KITTI segment equations reproduce10178 records and all primary metrics, maximum difference7.585e-14. No independent nonlinear optimizer or full raw preprocessing reimplementation is claimed.

The freeze stage costs115.9032046 enclosing seconds, the synthetic stage5.5737563s, complete bank501.7887143s, evaluator3.1522148s and independent validator4.7245667s. Later diagnostic/control stages count under the same original1800s scope; no reset occurs. Exact resource totals and measured peaks are consolidated in the weekly handoff. Nested native/parent clocks are not added. Host/setup/full process-tree peak limits remain explicit.

## Finite post-hoc diagnosis

Before-fine arrays were already sealed. Their00/05 ATE is0.886032436/0.356200730m and ter0.572512777/0.319297689%. These are explanatory outcomes, not newly selected deployable arms. In particular,00 drift regression exists before fine optimization. Removing fine optimization after seeing05 cannot rescue the frozen test.

Source inspection identifies a separate contract mismatch: native fine optimization fixes id_-1 near map ends, while the documented interface calls for preserving coarse keyposes. A known three-map fixture with anchors0/3/6 at x0/3.3/6.0 yields native anchor outputs0/3.1/6.2. Real coarse poses can be recovered from every map body without GT or rounded graph-node matching; reconstruction errors are<=2.416e-13. Native fine output moves those coarse anchors by up to8.172mm/0.334degree on00 and2.817mm/0.272degree on05.

An isolated source-frame-aware dense graph control fixes actual coarse-anchor vertices to their prescribed poses. Its synthetic analytic translation solution, no-op and common-world checks pass. This establishes implementation correctness for that control, not an accuracy result. No corrected real trajectory has yet been evaluated. It does not establish an author-confirmed defect or the cause of00 metric loss.

## Decision boundary

Keep low-drift B and the large-ATE-benefit M evidence available, with the full tradeoff shown. The owner was asked asynchronously whether future objectives prioritize ATE with competitive KISS drift, preserve current RAP drift, or compare two fixed operating modes. That choice affects a new prospective task only. The original LMB0 negative, DMF0 negative, old family stops and all source/reference unknowns remain.

The current explicit owner continuation is in reset1792497266, first observed0%/ordinarytrue at06:54:26UTC. The preceding window's last95% observation did not establish exhaustion. No automatic reset continuation, scheduler, outreach, Git mutation or goal-status action. The broader research objective remains unresolved.
