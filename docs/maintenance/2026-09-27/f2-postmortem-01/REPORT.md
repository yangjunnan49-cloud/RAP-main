# F2 saved-result diagnosis — completed 2026-09-27

Post-hoc observed-development analysis under [PROTOCOL.md](PROTOCOL.md).
F2's frozen decision remains **NO_DEVELOPMENT_MECHANISM_SIGNAL**. This
diagnostic neither selects an arm nor changes a gate. `analysis.json` retains
all pair identities and per-stratum partitions; `freeze.json` records ten
input/protocol/script identities. Independent PowerShell recount passed 58
checks (`validation.json`). No raw scans, GT file, generation, GPU, graph
optimization or production code was used.

## Positive-pair partition (75 per sequence)

| Seq | Arm | Correct and accepted | Correct but rejected | Correct candidate missed by R4 | No correct candidate in K4 | Incorrect accepts /100 |
|---|---|---:|---:|---:|---:|---:|
| 00 | N | 23 | 26 | 3 | 23 | 1 |
| 00 | S | 22 | 27 | 4 | 22 | 2 |
| 00 | P | 23 | 31 | 2 | 19 | 1 |
| 08 | N | 17 | 13 | 4 | 41 | 10 |
| 08 | S | 17 | 13 | 5 | 40 | 10 |
| 08 | P | 17 | 13 | 3 | 42 | 9 |

“Correct candidate” is evaluator-only OR4, chosen using ground truth; it
is an upper bound on saved candidates, not an executable selector. The four
columns partition the 75 non-confuser positives exactly. All arms reject all
25 confusers on each sequence. For N's 08 wrong accepts, none of the four
generated candidates is strictly correct; selecting a different saved
candidate cannot repair them. The analogous count is 0/1 on 00. This is
specific to the frozen K4 bank.

## Paired effects

| Seq | Comparison | Strict gains / losses | Correct-accept gains / losses | New / resolved incorrect accepts |
|---|---|---:|---:|---:|
| 00 | N to S | 2 / 2 | 0 / 1 | 1 / 0 |
| 00 | N to P | 7 / 2 | 0 / 0 | 0 / 0 |
| 08 | N to S | 1 / 1 | 0 / 0 | 0 / 0 |
| 08 | N to P | 3 / 3 | 1 / 1 | 0 / 1 |

P's five net strict successes on 00 do not add a correct accepted loop under
the fixed gate. On 08 P gives no net strict or correct-accept gain. These
paired observations do not rescue the earlier pooled-context route or select
P for production.

## Gate restriction on correct selected N poses

On 00, 26 selected-correct N poses are rejected: 22 fail both overlap and
mean-distance conditions, 3 overlap only and 1 distance only. On 08, 13
are rejected: 11 fail both and 2 overlap only. The gate values are computed
on the estimated transform. Their failure does not establish that a true
pose would be geometrically unobservable or that relaxing the gate would
remain safe. The 08 incorrect accepts (10/100) make threshold relaxation
particularly unjustified.

## Research implication and limits

The dominant observed 08 category is missing a strictly correct candidate
(41/75 under N), not R4 missing an existing correct candidate (4/75). A
next mechanism should therefore test whether it can **create or refine**
correct poses on fixed hard cases, while retaining separate acceptance and
graph-impact evaluation. The saved rows cannot show whether a local
refinement basin exists or whether partial visibility causes the gate
rejections. Establish those before committing to a visibility-aware method.
No threshold, support, seed, motion, point-budget or backend sweep follows.
