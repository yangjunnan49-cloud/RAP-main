# Experiment review and next decision

Date: 2026-10-10, Asia/Shanghai. Owner requested context recovery, a summary and audit of previous experiments, and a next-step judgment.

**Decision: PRIORITIZE_OBSERVATION_MEMBERSHIP_DIAGNOSIS_BEFORE_MORE_OPTIMIZATION.** The corrected frontend already has an engineering benefit. The recent measured-map experiments have not established a safe incremental method or a useful new RAP contribution. Their strongest unresolved result is a conflict between the geometric objective and the existing trajectory reference. One bounded audit of how shared surfaces are formed has higher expected information value than another change to optimizer variables or step count.

This request authorizes review of existing evidence and recording the judgment. It does not execute the previously proposed new membership experiment, train an adapter, or launch a full trajectory. All historical decisions and gates remain closed.

## Evidence recovered

AGENTS.md's latest CV2 boundary governs the current state; older pending plans are historical. In particular, RLP1 approval was received and its prerequisite stop is complete; RLP2 fitting and the owner-approved resource extension are complete; CV1's fixed-rotation proposal has already been tested as CV2. The ordinary-adaptation design's earlier originality rejection was a design decision under an older admission standard, not an unsuccessful training experiment. The owner subsequently permitted established methods and exploratory engineering. That relaxation does not alter old negative results or support an originality claim.

| Stage | Established result | Decision implication |
|---|---|---|
| E0 / E0-H1 | Frontend correction reduced development full mean ter from 0.761655% to 0.388718%. On the fixed exposed transfer set, O/A mean ter was 0.9595%/0.5056% and mean ATE 1.2177/0.7215m. | Preserve this engineering baseline. The KISS-SLAM comparison is mixed; improvement is not a new RAP mechanism or independent domain validation. |
| LC0 and metric accounting | Ideal distributed loops improved development ATE about 55–56% while increasing ter about 0.065–0.076 percentage points; the frozen conjunction failed. | Mapping and odometry utility differ. An evaluator oracle exposes opportunity but supplies no deployable method. Choose future primary metrics prospectively and show safety tradeoffs. |
| RLP1 | The weak-label coverage prerequisite stopped before training. | A prerequisite failure is not evidence that a trained readout fails or tokens are universally unlearnable. |
| RLP2 | J passed the full comparison against I but failed D and the useful G3/KISS comparisons. On 48 windows J median t/R was 0.888431m/0.552965deg versus G3 0.097115m/0.238968deg. On the matched 36 endpoints, J 0.888431m/0.593314deg versus KISS 0.022371m/0.049555deg. | Stop the exact frozen-token/soft-solve construction. Context/row binding affects the readout, but does not establish useful motion estimation. Nine fits and nine independent replays are not eighteen fitted candidates. |
| MMR0 | F/R each passed 0/4 declared translation-plus-rotation signals. R improved local aligned ATE in 3/4 windows, with rotation regressions in 3/4. Reference fixed-association cost exceeded initial cost in all four. | Preserve partial position-shape gains and failed primary criteria separately. Rematching is insufficient here; eight-node aligned ATE is not full-sequence utility. |
| SMP1 | Five of eight representations were unsupported; all three geometry-only outputs violated correction bounds. Three valid regularized outputs averaged about 1.94% ATE gain. Count-only audits raised 2m feature counts from 10/10/2/0 to 106/132/52/51 using all existing retained points. | The half split removed important support, with the cap adding loss. Correcting support is justified; feature counts alone do not prove accuracy. |
| SMP2 | Complete clusters made all four windows supported and valid, with safety passing, but mean fractional ATE gain was 1.137760%, below 5%. | The support defect was repaired without obtaining material local benefit. This does not reject all map optimization or bundle adjustment. |
| CV1 | On the fixed 00 revisit, F improved joint ATE 5.344% and endpoint t 7.955%, but R error increased 0.026466deg against a 0.01deg guard. J added only 0.316% ATE and 0.271% t improvement over F. | A real partial revisit signal exists. Neither full-pose improvement nor useful incremental internal-pose optimization was established. |
| CV2 | Translation-only T preserved every B rotation exactly. Mean fractional ATE/t gains were 4.107817%/13.189352%; 05 failed both 5% regression guards. | Rotation locking did not yield a safe cohort method. Stop this exact fixed-rotation construction. |

Primary sources: [E0](../../2026-09-26/e0-frontend-01/REPORT.md), [E0-H1](../../2026-09-27/e0-heldout-01/REPORT.md), [LC0](../../2026-10-07/retrieval-placement-audit-01/REPORT.md), [RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md), [MMR0](../../2026-10-09/measured-map-reoptimization-01/REPORT.md), [SMP1](../../2026-10-09/shared-plane-map-pilot-01/REPORT.md), [SMP2](../../2026-10-09/structural-holdout-map-pilot-01/REPORT.md), [CV1](../../2026-10-09/cross-visit-map-pilot-01/REPORT.md), [CV2](../../2026-10-09/rotation-protected-map-pilot-01/REPORT.md). Earlier matcher, intensity, ray, sampling, step-count, factor-shape, feedback and propagation screens remain stopped; they are not untried fixes.

## What this turn independently audited

[CHECKS.json](CHECKS.json) records the complete scope and input identities. A standalone auditor imported no scientific runner and wrote only this new review dossier.

- Rehashed all five measured-map delivery manifests: MMR0 35, SMP1 42, SMP2 37, CV1 42 and CV2 39 entries. Rechecked eight original/retry/diagnostic freezes with 54/61/28/34/51/67/104/16 entries. Together with model checks and RLP2 document checks, 338 unique files were hashed; every checked identity matched.
- Rehashed eight model/config files and the opaque checkpoint. No checkpoint was deserialized. Both repository HEADs, branches and existing tracked dirty sets matched CV2: main 4055d929 on codex/meeting-20260930 with two dirty paths; SLAM 6d3f2d22 on codex/e0-f1-20260926 with nine.
- Reconstructed CV2's existing camera-to-LiDAR reference conversion, proper rotation angles, SVD position alignment, endpoint and visit metrics for all three cases and O/B/F/T arms. Maximum metric discrepancy was 6.5781e-14. The seven non-anchor nodes define each visit RMSE/mean angle; the anchor remains in the position alignment and displayed per-node arrays.
- Recomputed existing train/holdout geometry from explicit retained points under the frozen labels, using centered covariance and equal mass per contributing scan. Maximum RMS/per-patch variance discrepancy was 5.6344e-13. Independently rebuilt the complete T-versus-B conjunction; it remains false. T rotation bytes, common visit translation and the eleven CV1/CV2 00 shared arrays matched.
- Recounted CV2's seven-stage ledger: 23.201184625s, peak RSS 100945920 bytes and current dossier size 10628103 bytes. The historical limits still pass. Imports/startup/design/docs are excluded from that historical clock; these are not production timings.
- Rechecked twelve RLP2 top-level sealed documents, including its closure and resource reports. Its full stage banks and fitting replay were not rehashed or rerun here. E0/LC0 and older branches were reviewed from their reports/handoff, not given new complete validators.

Historical numerical preflights, raw preprocessing, selected gradient checks and diagnostic validations are retained and hash-bound. This turn did not repeat raw preprocessing, optimizer updates, the rejected-feature census, or the diagnostic gradients. A matching hash confirms byte identity, not physical correctness or independence from shared scientific conventions.

The first new auditor failed because its visit averages incorrectly included the anchor and its angular calculation omitted the declared proper-rotation projection. [The original source](audit_attempt_01_source.py) and [failure record](FAILURE_attempt_01.json) are retained. Only the new auditor was repaired; no historical experiment or gate changed. The corrected audit passed in 7.086257s with observed peak RSS 40697856 bytes after imports. First-attempt complete wall/RSS were not captured, so this is not an all-attempt resource claim or an amendment to an old experiment budget.

Other accounting limits remain explicit: SMP2's failed metadata process has no measured peak RSS, so combined attempted-process RSS compliance is not fully verified. RLP2 used 6124.146614s against the owner-amended 6300s limit; its original 3600s limit failed and must not be reported as passed. Preserved MMR0/CV1/metadata INCOMPLETE markers describe their original failed attempts, not an unfinished validated retry.

## The CV2 result that changes the research priority

| Case | T versus B joint ATE gain | Endpoint t gain | Heldout RMS ratio |
|---|---:|---:|---:|
| 00 | +2.549% | +2.813% | 0.989300 |
| 05 | -6.334% | -18.559% | 0.984474 |
| 06 | +16.108% | +55.314% | 0.977039 |

All three heldout residuals improve while 05 pose errors worsen. Whole-patch holdout therefore does not supply a reliable refinement trigger in this construction. It shares the initial B-selected eligibility, observation model and correlated scans with the training objective. Numerical rank, support, proper rotations and low residual cannot certify correct physical correspondence.

05's absolute increases are 3.9602mm joint ATE and 11.6181mm endpoint error. Their small scale and unresolved reference quality limit a physical-harm interpretation; they do not change the frozen relative safety failure. A future application may use predeclared absolute and relative margins, but this review does not retroactively substitute them.

The separately sealed zero-optimizer diagnosis gives 05 a reference-directed cost slope of +0.042115 with original internal shapes and -0.068461 with reference internal shapes. Internal shape changes the objective's preference. Full reference poses nevertheless have higher train and holdout residuals in all three cases. This does not uniquely identify internal distortion, dynamics, aliasing, timing, calibration or reference error. A local derivative need not predict cost at a distant endpoint.

F on 06 improved ATE 17.409%, t 75.680% and R by 0.067445deg. Thus unconditional rotation locking loses useful correction in that case and still fails to protect 05. A retrospective 00=T/05=B/06=F selector would use outcome knowledge and has no deployable justification.

## My next-step judgment

I endorse the latest membership-audit direction, with a firm decision boundary. Keep the exact three cases, 48 scans, 288000 retained points, preprocessing and 2m criteria. Form memberships separately at B and the full reference G; fix each set, then cross-evaluate B/G and the already sealed F/T poses. G is an oracle diagnostic input only. Run zero optimizers and generate no new accuracy candidate.

The decisive deliverable must include retained scan/point row IDs, coverage intersection and exclusive coverage, split/merge relations, per-visit support, and a complete accepted/rejected census. Compare B and G within each fixed membership. Different mean costs across different memberships are not comparable evidence of a better physical model; equal voxel keys are not physical surface identity. Independent reconstruction of rejected as well as accepted groups matters because current audits do not cover the whole selection process.

Use the result as follows:

1. If preferences follow the membership-generating alignment, the objective is demonstrably sensitive to this construction. Develop an association/observation strategy that can operate without the reference, then test it against the same baseline. This result alone does not prove G membership correct or account for the entire 05 failure.
2. If changing formation location does not account for the conflict, pursue verified measurement timing/calibration/trajectory provenance or stable physical-surface evidence. If such evidence is unavailable, stop investment in this shared-plane objective rather than append another variable/scale/prior sweep. This rejects the tested explanation, not every form of selection bias or geometry optimization.
3. If only aggregate residuals change and coverage remains uninterpretable, mark the diagnostic inconclusive. Do not convert it into a residual-based acceptance policy or enlarge the cohort.

The proposed 1800s CPU / 2GiB RSS / 512MiB scope in [CV2's next design](../../2026-10-09/rotation-protected-map-pilot-01/NEXT_ROUND_PLAN.md) remains a draft for a distinct execution request. It includes failures and independent census validation. This turn has not formed those new memberships or frozen that protocol.

If the geometry branch reaches that stop, my preferred distinct alternative is tiny native-output capability diagnosis: one then eight development windows, a simple direct learner control, synthetic and real supervision reported separately, and actual pure-noise sampler inference. It would separate fitting from inference mismatch before expensive transfer evaluation. This is a new proposal, not a rescue of RLP2 or execution of the old twelve-fit adaptation design.

Any later deployable candidate needs a declared mapping or odometry objective, matched geometry controls, visible absolute/relative safety and ordinary cases, then full-sequence evaluation. These local banks do not demonstrate system gain, physically calibrated accuracy, independent generalization or an original breakthrough. The 09 discrepancy, checkpoint/site membership and scan-time/physical-identity unknowns remain.

## Preservation and handoff

Only new review artifacts and mutable AGENTS.md / the 2026-10-10 phase record were written. Scientific inputs, sources, banks, results, old seals, official GT and metric conventions are preserved. No model loading, fitting, new RAP inference, GPU, new membership, optimizer, trajectory, acquisition, installation, production/default/backbone/manuscript edit, commit or Git synchronization occurred. Existing CV2 metrics were re-evaluated using the existing reference files solely for this audit.
