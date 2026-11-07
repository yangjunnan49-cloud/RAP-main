# LC0 complete retrieval and measurement-placement opportunity audit

Status: **VALIDATED_NEGATIVE**; decision **NO_FIXED_BUDGET_PLACEMENT_SIGNAL**.

Owner requested proceeding on2026-10-07. This is a fixed-budget, evaluator-only diagnostic on historically exposed E0 A data. No executable accuracy or originality gain follows.

## Source and validation

Frozen1873 identities before outputs, including1800 raw keyframe scans matched to original E0 hashes. Native two-producer/merger replay and independent extraction reproduce all71 original attempts, including endpoint order and attempt IDs. All58 accepted edges/native weights remain; native graphs reproduce saved E0. All319728 eligible pair rows, ring ranks, filters, pre-cap/capped/final lists are complete.

Independent raw processing reconstructs1800 descriptors from 221611925 retained points: all2160000 float32 descriptor pixels and36000 ring-key values exact. Independent SC scores maxdelta0.000e+00, native graph maxdelta2.665e-10. The validator shares numeric bin/rounding conventions but uses sorted-bin maxima and simultaneous shift scoring; it imports no new algorithm/runner/native retrieval or graph.

Complete GT-free bank seal and independent validation seal precede GT pose parsing. GT position-proxy coverage, selections, oracle transforms, explicit graphs and metrics reconstruct independently.
Independent oracle graph maxdelta5.963e-10; 29592 segment records; aggregate metric maxdelta5.896e-13. No failure/amendment/repair. All previous failures and stops remain untouched.

## Exposure

GT-near below15m is a position proxy; it is not overlap or physical registration truth. Mixed-query counts are ambiguous exposure, not identified aliases. Complete denominators are in evaluation/coverage.json.

| Seq | Eligible near/all | Native union pre-cap near/all | Final near/all | Near queries eligible/union/final | Oracle C/P/H counts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00 | 1036/204970 | 906/1064 | 12/12 | 150/146/9 | 12/12/12 |
| 05 | 448/60275 | 436/453 | 12/12 | 77/77/11 | 12/12/12 |
| 06 | 237/13595 | 235/235 | 12/12 | 49/49/12 | 12/12/12 |
| 07 | 38/5921 | 38/53 | 12/12 | 5/5/3 | 12/5/5 |
| 09 | 11/26919 | 11/16 | 10/12 | 4/4/4 | 10/4/4 |
| 10 | 0/8048 | 0/11 | 0/11 | 0/0/0 | 0/0/0 |

Counts are maximum12 per sequence, not increased neural work. Oracle counts may differ; P/H versus C includes measurement availability and placement, not a location-only equal-count causal effect. N uses original poses/weights; C/P/H use the same declared reference noise and GT-near filter. All oracle edges are evaluator-only.

## Trajectory opportunity

N=native, C=original shortlist with ideal GT-near measurements, P=distributed native pre-cap measurements, H=distributed structurally eligible measurements.

| Cohort | Arm | Mean ter % | Aligned ATE m | ter gain vs N pp | ATE gain vs N % |
| --- | --- | ---: | ---: | ---: | ---: |
| development | N | 0.388718 | 1.460664 | +0.000000 | +0.000 |
| development | C | 0.392497 | 1.449400 | -0.003779 | +0.771 |
| development | P | 0.453886 | 0.653784 | -0.065168 | +55.241 |
| development | H | 0.464529 | 0.642622 | -0.075811 | +56.005 |
| transfer_exposed | N | 0.505615 | 0.721480 | +0.000000 | +0.000 |
| transfer_exposed | C | 0.499451 | 0.603277 | +0.006164 | +16.383 |
| transfer_exposed | P | 0.498479 | 0.598877 | +0.007136 | +16.993 |
| transfer_exposed | H | 0.498479 | 0.598877 | +0.007136 | +16.993 |

| Seq | N ter/ATE | C ter/ATE | P ter/ATE | H ter/ATE |
| --- | ---: | ---: | ---: | ---: |
| 00 | 0.518171/2.754437 | 0.519232/2.720629 | 0.624604/1.013102 | 0.656533/0.979617 |
| 05 | 0.320473/1.294699 | 0.332222/1.290508 | 0.418662/0.590198 | 0.418662/0.590198 |
| 06 | 0.327512/0.332854 | 0.326037/0.337063 | 0.318393/0.358051 | 0.318393/0.358051 |
| 07 | 0.394673/0.326400 | 0.392977/0.307764 | 0.387783/0.298551 | 0.387783/0.298551 |
| 09 | 0.593652/1.074523 | 0.576856/0.738551 | 0.579133/0.734565 | 0.579133/0.734565 |
| 10 | 0.528520/0.763516 | 0.528520/0.763516 | 0.528520/0.763516 | 0.528520/0.763516 |

The frozen gate requires >=.01pp mean ter and>=5% aligned ATE gain together, improvement over C in both means, plus all-six safety (<=.01pp ter regression and<=5% ATE regression). Full component booleans are in results.json; no post-result selection/radius/noise/budget/cohort rescue.

- P actionable=False; cohorts={"development": {"ate": true, "placement_ate": true, "placement_ter": false, "ter": false}, "transfer_exposed": {"ate": true, "placement_ate": true, "placement_ter": true, "ter": false}}; failed safety=[('00', 'ter'), ('05', 'ter'), ('06', 'ate')]
- H actionable=False; cohorts={"development": {"ate": true, "placement_ate": true, "placement_ter": false, "ter": false}, "transfer_exposed": {"ate": true, "placement_ate": true, "placement_ter": true, "ter": false}}; failed safety=[('00', 'ter'), ('05', 'ter'), ('06', 'ate')]

## Meaning and limits

This completes the formerly missing native candidate exposure record. A near-query omission is conditional on the15m GT-position proxy, not a calibrated recall estimate for physical revisits. A selected oracle is neither a global bound nor guaranteed recoverable by any matcher;09 physical label/geometry discrepancy remains unresolved. Six sequences and their graph outcomes are previously exposed, not independent confirmation. Unknown RAP checkpoint training membership persists. Generic temporal distribution/retrieval controls are prior art; no RAP novelty is established.

Successful freeze/bank/independent-bank/evaluation/independent-evaluation stages total594.513s, peak RSS0.116GiB. Per-stage1h/4GiB and500MiB artifact caps pass; no GPU/model inference. See EXECUTION_SUMMARY.json for stage costs and payload size.

## Continuation

Read NEXT_ROUND_PLAN.md and HANDOFF.md. All earlier stopped arms, sealed banks, official GT/metrics, manuscript pause and original breakthrough requirement persist. No training, production/default/model/manuscript edit, acquisition/install, commit or Git sync. Original HEADs/branches and dirty work preserved.
