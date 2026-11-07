# SC-V1.1 discovery

Decision: **NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE**. Neural expansion remains stopped.

| Method | Strict success | Correct accepts | Incorrect/accepted | Clipped positive error |
|---|---:|---:|---:|---:|
| B1 | 50/75 | 22 | 1/23 | 1.263181736 |
| B4 | 52/75 | 22 | 2/24 | 1.103923261 |
| R4 | 53/75 | 22 | 1/23 | 1.091010852 |
| A4 | 54/75 | 22 | 2/24 | 1.133144631 |
| S4 | 54/75 | 22 | 2/24 | 1.080597330 |
| P4 | 53/75 | 22 | 2/24 | 1.087966771 |
| P4x2 | 53/75 | 22 | 2/24 | 1.087966771 |
| G4 | 54/75 | 22 | 2/24 | 1.083239886 |
| OR4 | 57/75 | 22 | 2/24 | 0.937255448 |
| REJ | 0/75 | 0 | 0/0 | 5.000000000 |

A4/oracle gap=0.19588918306725345; discrepant positives=14; S4 recovery=0.2682501421731215; ordinary recall loss=0.0.

Conditions: {'recovery_25percent': True, 'no_worse_than_R4': True, 'ordinary_loss_at_most_2pp': True, 'no_new_incorrect_A4': True, 'no_new_incorrect_R4': False}.

G4 and OR4 are evaluator-only diagnostics. No GT enters executable selectors. All arms use the same immutable bank; full per-stratum and pair transitions are in metrics/evaluator files. No independent-domain or novelty claim.
