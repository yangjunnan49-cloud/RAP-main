# C6 causal loop-pose transport screen — complete

Decision: **NO_CAUSAL_TRANSPORT_SCREEN_SIGNAL**. The exact policy in
[PROTOCOL.md](PROTOCOL.md) was frozen with 16 file identities before the
GT-free bank. The 200-row bank was SHA-sealed before either F2 evaluator
labels or KITTI GT were read for this run. Separate validator passed 991
identity, donor-policy, matrix, label and decision checks. Bank generation
took 0.078s; all seven artifacts total 89,543 bytes. No GPU inference,
training, gate evaluation, production edit or Git synchronization occurred.

| Sequence | Covered pairs | Covered native-K4-unavailable positives | Strict transport / odometry on those | Other covered strict transport / odometry |
| --- | ---: | ---: | ---: | ---: |
| 00 | 22/100 | 1 | 0 / 0 | 20 / 0 of 21 |
| 08 | 15/100 | 8 | 0 / 0 | 7 / 7 of 7 |

The hard08 decision target was at least two transported strict recoveries
and at least two more than the odometry-only control; actual counts were
zero and zero. Among the eight exposed hard08 pairs, all eight chosen
donors were accepted by F2's GT-blind gate but later labeled strict-wrong.
Among the seven covered08 native-K4-available positives, all donors were
strict-correct; both transported and odometry-only poses were strict.
This explains why the gate alone cannot make causal reuse safe here.
The 00 transport positives are already in the native-K4-available group;
they are no new candidate-availability gain.

This is an observed-development screen. The existing hard08 labels were
inspected for exposed-cohort size after choosing the 50-frame window but
before the C6 freeze; they were not used to generate or choose candidates.
The F2 sample contains isolated pairs, not the full online retrieval
stream. Thus sparse donor coverage does not rule out transport in other
systems. C6 also did not recompute the common geometry gate for its poses,
so its strict pose results imply no accepted-loop or graph benefit.

Stop this exact accepted-donor/50-frame policy. Do not enlarge the window,
choose GT-correct donors, or tune a new gate using these outcomes. A further
research arm requires a distinct independently justified candidate signal
and a prospective safety comparator. E0 arm A remains the positive
held-out-system engineering result; no new RAP algorithmic gain is established.
