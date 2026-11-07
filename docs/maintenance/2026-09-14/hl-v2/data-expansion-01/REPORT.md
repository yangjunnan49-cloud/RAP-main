# HL-V2 sufficient fixed development cohorts

The prospective [annex](PROTOCOL.md) explicitly amends the data/support protocol.
Original HL-V1 pilot-01 INCONCLUSIVE remains unchanged.

| Role/sequence | Raw scans | Keyframes | Candidates | Supported | Selected |
|---|---:|---:|---:|---:|---:|
| Discovery00 | 4541 | 670 | 15064 | 14989 | 100 |
| Confirmation02 | 4661 | 812 | 16660 | 16616 | 100 |

| Stratum | 00 population | 00 supported | 00 selected | 02 population | 02 supported | 02 selected |
|---|---:|---:|---:|---:|---:|---:|
| Confuser | 11800 | 11746 | 25 | 14734 | 14690 | 25 |
| Ambiguous positive | 150 | 143 | 25 | 61 | 61 | 25 |
| Low overlap | 923 | 922 | 25 | 485 | 485 | 25 |
| Ordinary | 759 | 754 | 25 | 102 | 102 | 25 |

Both roles meet the fixed data minima and target25 per stratum. No fallback
sequence needed. Oracle/B4 discrepancy adequacy still requires model results.
All9,202 scans were read/hashed and checked finite/nonempty/XYZI/source IDs;
timestamps, GT and calibration were bound. Corrected00 parent hashes verified;
02 uses fresh full raw KISS-ICP odometry with original6m/12deg keyframes.
Both are historically observed development data; no pretraining-exclusion claim.

Changed controls: ring shortlist50/top20 SC without cutoff; retain top5
proximity30m; add10 deterministic real offset bands30-80m; causal raw support
at2m/5m within5s. Unchanged GT strata, strict pose thresholds,K4 and H1/H2 gates.
This is not production retrieval or natural-stream prevalence estimation.

Independent checks reproduced proposal union, raw-support cumulative search,
strata, priority/hash/quota/query-cap selection and GT-free inputs. Sixteen
selected overlaps matched independent brute-force distances. Scalar SC spots
match within1e-6. Roles were hash-frozen before inference. Fixed visual examples
were inspected without changing membership; semantic repetition stays unverified
beyond the numeric proxy. See ACCESS_AND_VISUAL_RECORD.md.

Data-stage wall00/02:248.875s/306.904s, including source reads/frontend where
applicable, excluding independent validation/documentation. They ran concurrently;
do not add them as session wall time. No RAP model ran in this data stage.

MulRan official access requires identity information and no form was submitted.
Additional raw downloads were unnecessary for these adequate local cohorts.
Public-download authorization persists. NCLT remains future external data.
Separate preflight/pilot artifacts hold runtime and model-result decisions.
