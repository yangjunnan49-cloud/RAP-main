# HL-V2 confirmation results

Decision: **STOP_NEURAL_EXPANSION**; adequacy=True, discrepant positives=29.

| Method | Positive success/75 | Accepted | Incorrect accepted | Mean clipped positive error |
|---|---:|---:|---:|---:|
| B1 | 26/75 | 39 | 24 | 1.815487 |
| B4 | 26/75 | 40 | 26 | 1.933277 |
| S4 | 25/75 | 40 | 26 | 1.937351 |
| R4 | 27/75 | 40 | 25 | 1.807299 |
| OR4 | 29/75 | 39 | 24 | 1.550009 |
| REJ | 0/75 | 0 | 0 | 5.000000 |

H1 recall gain=0.040000; relative clipped-error reduction=0.19824792080510212; H2 metric=clipped_error, recovery=-0.010630506784991814; ordinary recall loss=0.0; newly incorrect pairs=0.

All methods share one immutable K4 bank. OR4 is an evaluator-only upper bound; R4 uses official average per-step rigidity RMSE. Ungated recall and gated acceptance remain separate. Full counts, failure denominators, continuous errors, all strata and harmful/helpful transitions are in metrics.json and evaluator-only decisions. No significance or independent-domain claim. No training was performed. Discovery must freeze before confirmation inference.
