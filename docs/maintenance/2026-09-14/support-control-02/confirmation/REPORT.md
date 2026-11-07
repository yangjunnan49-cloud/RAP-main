# SC-V1.1 confirmation

Decision: **NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE**. Neural expansion remains stopped.

| Method | Strict success | Correct accepts | Incorrect/accepted | Clipped positive error |
|---|---:|---:|---:|---:|
| B1 | 32/75 | 17 | 10/27 | 1.543525882 |
| B4 | 34/75 | 17 | 10/27 | 1.268507725 |
| R4 | 32/75 | 16 | 10/26 | 1.393695261 |
| A4 | 33/75 | 17 | 10/27 | 1.269984013 |
| S4 | 31/75 | 17 | 10/27 | 1.400363980 |
| P4 | 32/75 | 17 | 10/27 | 1.401031220 |
| P4x2 | 32/75 | 17 | 10/27 | 1.401031220 |
| G4 | 31/75 | 16 | 10/26 | 1.402462151 |
| OR4 | 37/75 | 16 | 10/26 | 1.226284942 |
| REJ | 0/75 | 0 | 0/0 | 5.000000000 |

A4/oracle gap=0.04369907089927971; discrepant positives=10; S4 recovery=-2.983586705141944; ordinary recall loss=0.0.

Conditions: {'recovery_25percent': False, 'no_worse_than_R4': False, 'ordinary_loss_at_most_2pp': True, 'no_new_incorrect_A4': True, 'no_new_incorrect_R4': True}.

G4 and OR4 are evaluator-only diagnostics. No GT enters executable selectors. All arms use the same immutable bank; full per-stratum and pair transitions are in metrics/evaluator files. No independent-domain or novelty claim.
