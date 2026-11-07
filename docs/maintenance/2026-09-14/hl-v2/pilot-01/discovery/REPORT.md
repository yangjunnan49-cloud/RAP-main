# HL-V2 discovery results

Decision: **GO**; adequacy=True, discrepant positives=18.

| Method | Positive success/75 | Accepted | Incorrect accepted | Mean clipped positive error |
|---|---:|---:|---:|---:|
| B1 | 50/75 | 23 | 1 | 1.263182 |
| B4 | 52/75 | 24 | 2 | 1.103923 |
| S4 | 54/75 | 24 | 2 | 1.080597 |
| R4 | 53/75 | 23 | 1 | 1.091011 |
| OR4 | 57/75 | 24 | 2 | 0.937255 |
| REJ | 0/75 | 0 | 0 | 5.000000 |

H1 recall gain=0.066667; relative clipped-error reduction=0.15097771628463702; H2 metric=recall, recovery=0.39999999999999936; ordinary recall loss=0.0; newly incorrect pairs=0.

All methods share one immutable K4 bank. OR4 is an evaluator-only upper bound; R4 uses official average per-step rigidity RMSE. Ungated recall and gated acceptance remain separate. Full counts, failure denominators, continuous errors, all strata and harmful/helpful transitions are in metrics.json and evaluator-only decisions. No significance or independent-domain claim. No training was performed. Discovery must freeze before confirmation inference.

Discovery-only GO is diagnostic and does not authorize training. The frozen confirmation result governs the final decision. Independent recomputation passed all500 selected method results, bank hashes, numerical labels and gate accounting.
