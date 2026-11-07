# HL-V2 frozen-bank failure diagnosis

Post-hoc descriptive analysis only. Both roles are now development data. The original STOP_NEURAL_EXPANSION decision is unchanged; no new selector, threshold, generation or training.

| Role | Stratum | Changed selection | Strict gained/lost | Sum S4-B4 clipped error | S4 incorrect accepts | Of these legacy unsafe | Oracle correct but S4 rejected |
|---|---|---:|---:|---:|---:|---:|---:|
| discovery | ambiguous_positive | 18/25 | 3/1 | -0.555388 | 0 | 0 | 20 |
| discovery | confuser | 4/25 | 0/0 | 0.000000 | 0 | 0 | 0 |
| discovery | low_overlap | 14/25 | 0/0 | -1.281266 | 1 | 0 | 10 |
| discovery | ordinary | 19/25 | 0/0 | 0.087210 | 1 | 0 | 5 |
| confirmation | ambiguous_positive | 14/25 | 0/1 | -0.583751 | 6 | 0 | 7 |
| confirmation | confuser | 3/25 | 0/0 | 0.000000 | 0 | 0 | 0 |
| confirmation | low_overlap | 8/25 | 0/0 | 1.262892 | 8 | 2 | 3 |
| confirmation | ordinary | 16/25 | 0/0 | -0.373566 | 12 | 2 | 4 |

Confusers are excluded from positive error and recall metrics. Legacy unsafe means failing the historical 5m/10deg check; strict incorrect uses the unchanged 1m/5deg definition. Rejection here describes S4, not whether an oracle transform would pass the gate.

## Short-motion check

Compared each saved odometry support-to-anchor transform to the corresponding GT relative pose. Statistics count all 400 support usages per role, including repeated links; unique link counts are in JSON. No GT motion is substituted into scoring.

- discovery: translation median/p90/max 0.0538/0.1195/0.6471 m; rotation 0.1019/0.2883/1.3792 deg.
- confirmation: translation median/p90/max 0.0529/0.1450/0.4058 m; rotation 0.0925/0.2012/2.7831 deg.

These measurements can bound local-motion discrepancies but do not establish the cause of ranking failures. Four nearby support scans may retain similar geometry and ambiguity; proving that mechanism requires a separately declared control. Do not infer spatial independence from exclusion of anchor source IDs.

## Next research boundary

Neural training remains stopped. Use these failures to formulate a bounded, prospective support-evidence question, with official R4 and equal-data/compute controls. Freeze its protocol and fresh confirmation membership before generating new outcomes. KITTI00/02 cannot be reused as unseen confirmation after this diagnosis. Preserve NCLT for external evaluation. No automatic score sweep or threshold search.
