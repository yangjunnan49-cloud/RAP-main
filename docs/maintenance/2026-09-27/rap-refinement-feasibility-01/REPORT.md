# R0 fixed local-refinement feasibility — completed 2026-09-27

Under frozen [PROTOCOL.md](PROTOCOL.md), a standard 2000-point-anchor,
point-to-point ICP ran once from each F2 native R4 pose on all 100 pairs of
KITTI 00 and all 100 pairs of KITTI 08. The CPU runner read no GT or
evaluator rows for pose computation; it did byte-hash them for the frozen
input integrity guard, as recorded in [AMENDMENT_01.md](AMENDMENT_01.md).
Its 200-pose bank was SHA256-sealed before evaluator parsing.
Separate validation passed 214 checks (`validation.json`): frozen 213-file
identity set, exact N/R4 origin, SE(3), saved evaluator labels, aggregate
and decision arithmetic, bank seal and caps. No GPU inference, training,
production change, F2 overwrite or Git synchronization.

Decision: **NO_LOCAL_REFINEMENT_FEASIBILITY_SIGNAL**.

| Sequence | N strict /75 | ICP strict /75 | Paired gains / losses | N clipped error | ICP clipped error |
|---|---:|---:|---:|---:|---:|
| 00 | 49 | 51 | 4 / 2 | 1.472846 | 1.496762 |
| 08 | 30 | 30 | 0 / 0 | 1.579930 | 1.595318 |

On 00, low-overlap strict successes rise 3 to 6, but ordinary successes
fall 25 to 24; the other paired gain/loss is in the ambiguous stratum.
Three of the four00 gains had no correct native K4 candidate; one was a
native R4 selection miss. On 08, no positive pair changes strict
correctness, including all41 without a correct native K4 candidate.
All 50 confuser transforms are retained in the sealed bank; their gate
acceptance was not evaluated. All 200 fits returned
finite SE(3) poses (174 converged before 30 iterations, 26 reached 30),
and every pose moved; the result is not a no-correspondence execution
failure. CPU process wall 3.49 s, peak RSS 0.068 GiB, artifacts 0.339 MB.

The predeclared 08 gate requires >=3 net strict gains, >=5% clipped-error
improvement and <=1 strict loss; it fails the first two. 00 also exceeds
its <=1 loss guard. These are observed-development outcomes under one
fixed local ICP recipe, not a proof that every refinement method fails.
The F2 4000-point common acceptance gate was not recomputed, so R0 makes
no accepted-loop or graph-impact claim. ICP is established baseline
machinery and is not a proposed original contribution.

Consequence: stop this local ICP/refiner route. The specific F2 08 deficit
remains candidate creation (41/75 without a correct native K4 candidate),
with nontrivial correct-pose rejection and wrong accepts as separate issues.
Any next algorithmic hypothesis needs a different mechanism and a separate
novelty/source audit before an efficacy protocol; do not tune ICP distance,
iteration count, supports or F2 gates to rescue this screen.
