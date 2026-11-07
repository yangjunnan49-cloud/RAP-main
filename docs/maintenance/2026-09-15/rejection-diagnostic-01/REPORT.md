# Rejection diagnosis: no justified new experiment from saved evidence

2026-09-15. Decision: **NO_JUSTIFIED_REJECTION_EXPERIMENT_FROM_SAVED_EVIDENCE**.

This owner-authorized, bounded post-hoc diagnosis is complete. It does not
establish a new rejector, independent generalization or end-to-end SLAM benefit.
The saved evidence does not justify training or launching a rejection experiment
based on candidate consistency or the already available scalar scores. Stop this
diagnostic route and move to thesis scope discussion. All previous stops remain.

## 1. What the current gate actually accepts

Each sequence contains the same 100 development pairs, including 75 positives
and 25 confusers. Strict correctness remains <=1m translation AND <=5deg rotation.

| Sequence / method | Correct accepted | Incorrect accepted | Correct rejected | Incorrect rejected |
|---|---:|---:|---:|---:|
| 00 / A-R4 | 22 | 2 | 31 | 45 |
| 08 / A-R4 | 16 | 9 | 16 | 59 |
| 00 / P-R4 | 22 | 2 | 33 | 43 |
| 08 / P-R4 | 17 | 9 | 18 | 56 |

All accepted transforms in these four rows satisfy the historical <=5m/10deg
criterion. All 25 confusers per sequence are rejected in both methods. For the
primary A-R4 baseline, the 11 strictly incorrect accepts have translation errors
1.016508–2.923210m and rotation errors0.296983–0.893105deg. They fail the strict
translation requirement; they are not observed gross false-place accepts in this
cohort. Historical "safe" is a metric label, not a guarantee of safe graph impact.
No full graph replay was run here, and these errors could still harm trajectories.

This corrects an overly broad motivation for a new dangerous-loop rejector:
the latest 2/9 counts alone cannot demonstrate that problem. Earlier HL-V2
diagnostics used different sampled gates and cannot be pooled into these counts.

## 2. Four consistent candidates can all be wrong

For every currently accepted A-R4 and P-R4 result, the selected transform has
all three other candidates within the descriptive 1m/5deg tolerance. This holds
for both correct and incorrect accepts. The neighbor count has zero observed
discrimination (accepted-correctness AUC0.5 in all four rows).

For all 11 primary A-R4 incorrect accepts, **none of the four candidates is
strictly correct**. Reordering those same candidates cannot correct these cases.
Do not extend that statement to P-R4: one00 P-R4 incorrect acceptance has two
strictly correct candidates, already included in the completed PG oracle analysis.

On08 A-R4, correct versus incorrect accepts have almost equal median maximum
pairwise translation dispersion:0.095818 versus0.094307m. Rotation dispersion
medians are0.183942 versus0.178774deg. These are repeated similar estimates with
residual pose error; the cause of the shared error is not established.

| A-R4 incorrect accepted pair | Stratum | Translation error (m) | Rotation error (deg) |
|---|---|---:|---:|
| 00_187_1621 | ordinary | 1.016508 | 0.854481 |
| 00_1381_3530 | low_overlap | 1.862716 | 0.308458 |
| 08_242_1650 | low_overlap | 2.378025 | 0.494407 |
| 08_207_1688 | low_overlap | 2.923210 | 0.557175 |
| 08_748_1454 | ordinary | 1.070635 | 0.296983 |
| 08_2483_3868 | ordinary | 1.754607 | 0.669784 |
| 08_2483_3874 | ordinary | 1.728592 | 0.688675 |
| 08_2532_3868 | ordinary | 1.490184 | 0.794357 |
| 08_2503_3868 | ordinary | 1.727324 | 0.873832 |
| 08_2518_3856 | ordinary | 1.437207 | 0.893105 |
| 08_2532_3862 | ordinary | 1.443154 | 0.792688 |

Six of nine08 errors are concentrated in source frames2483–2532 paired with
3856–3874, including reused scans. Nine pairs use only seven distinct source_i
and seven distinct source_j IDs. These are correlated development observations,
not nine independent failure mechanisms. No uncertainty interval or population
false-loop prevalence is inferred from the stratified counts.

## 3. Available scalar evidence does not support the proposed expansion

The following descriptive AUC is the fraction of correct/incorrect accepted
pair comparisons ordered correctly by the stated confidence direction, counting
ties as half. Higher overlap/neighbor count and lower distances/dispersion/rigidity
are the fixed directions. No fitted thresholds, sign reversal, feature combination,
cross-validation or significance claim is made.00 has only two incorrect accepts.

| Feature | 00 A-R4 | 08 A-R4 | 00 P-R4 | 08 P-R4 |
|---|---:|---:|---:|---:|
| Overlap | 0.614 | 0.604 | 0.636 | 0.565 |
| Mean distance | 0.773 | 0.417 | 0.773 | 0.392 |
| Rigidity | 0.682 | 0.167 | 0.795 | 0.111 |
| Translation dispersion | 0.568 | 0.528 | 0.636 | 0.686 |
| Rotation dispersion | 0.591 | 0.535 | 0.932 | 0.510 |
| Selected-candidate neighbors | 0.500 | 0.500 | 0.500 | 0.500 |

Dispersion provides no convincing repeated primary-baseline separation. Existing
distance/rigidity directions can reverse on08. The modest overlap ordering is
already part of the existing gate and is not a distinct mechanism. The favorable
P-R4 cells do not warrant a post-hoc method switch or rescue of PG. These
observations do not mathematically rule out nonlinear classifiers or other
unmeasured evidence; they do not justify investing in one here.

## 4. Lost correct accepts are the more visible acceptance limitation

All31/16 A-R4 correct rejected results fail the overlap>=0.7 clause. Of these,
28/13 also fail mean distance<=2.5m. The same pattern holds for P-R4: all33/18
fail overlap,30/16 also fail distance. Changing only one clause would leave most
of these correct results rejected.

A-R4 correct rejected strata are00 ambiguous18 / low-overlap8 / ordinary5,
and08 ambiguous12 / low-overlap3 / ordinary1. This is a measured gap between pose
correctness and the gate, not evidence that loosening the gate is safe. A rejector
appended to the existing gate cannot recover any of these rejected correct poses.
Even perfect evaluator-only rejection would retain at most the current22/16
correct accepts while removing2/9 strictly incorrect ones; reject-all retains0.

Source inspection confirms the gate uses symmetric nearest-neighbor distances
over all preprocessed points, including the mean over all distances. It does not
explicitly evaluate visible free space or identify a shared visible region.
Partial visibility is a possible explanation for some correct rejections, but
the saved scalars cannot establish that causal explanation. Raw geometry and
sensor visibility were not recomputed. This is not authorization to rename the
failed support-distance score, launch a threshold sweep, or implement a new gate.

## 5. Decision and next boundary

The initially proposed rejection direction has no sufficiently specific new
evidence from this diagnosis. Recommend **scope convergence now**, with the
corrected baseline, modest PG gains and negative controls retained accurately.
Discuss with the owner/advisor whether the existing system contribution meets
the master's thesis requirement before resuming manuscript work. No publication
readiness or thesis acceptance is guaranteed by this diagnostic.

If a further algorithmic contribution is required, that is a new direction
decision: state its mechanism and distinguish strict pose accuracy, gross false
loops and correct-accept coverage. It requires fresh evidence and a prospective
protocol, rather than automatic continuation from this report. Visibility or
graph consistency remains untested, not selected. NCLT remains external.

## 6. Verification and execution record

- Rehashed830 PG +835 SC +829 HL parent artifacts (2494 manifest entries).
  Verified both GT array hashes against their original data manifests.
- Reconstructed1400 saved selected pose labels/acceptance decisions and checked
  all1600 saved candidate gates. Recomputed400 R4 selections and400 diagnostic
  rows; all four aggregate tables match the completed PG metrics.
- Maximum pose-label differences: translation2.274e-13m, rotation2.843e-14deg.
  Label reconstruction uses linear solves with the original atan2 definition.
  Dispersion uses scipy's proper-rotation conversion for tiny floating errors;
  it is a descriptive transform spread, not calibrated geometric uncertainty.
- A first attempt stopped before diagnostic outputs because simple translation
  subtraction did not exactly preserve the inverse-GT error definition under
  finite GT precision. The first freeze is retained; v2 corrects the metric
  semantics. No cohort, threshold or source experiment changed.
- Separate PowerShell checks reconstruct row categories, gate clauses, legacy
  labels, published totals and critical consensus/candidate-count findings.
- No raw clouds rehashed, no new inference/training/download, no production
  change or graph evaluation. Original HEADs and pre-existing dirty changes
  remain. No Git synchronization. Completed files must not be overwritten.

See [scope](SCOPE.md), [per-pair results](pairs.json), [summary](summary.json),
[validation](validation.json), and [cross-check](crosscheck.json).
