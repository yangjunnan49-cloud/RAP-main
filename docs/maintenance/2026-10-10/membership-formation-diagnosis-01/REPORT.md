# MF0: reference-formed membership does not remove the objective conflict

Date: 2026-10-10, Asia/Shanghai. Owner instruction: "启动新实验".
Status: **VALIDATED_DIAGNOSTIC_COMPLETE_WITH_VALIDATOR_REPAIR**.
Decision: **FORMATION_LOCATION_DOES_NOT_RESOLVE_REFERENCE_CONFLICT**.

The authorized fixed diagnostic is executed and independently validated. All six membership sets satisfy the prospective support rules. In every case, the training objective prefers the original alignment B even when the shared patches are formed at the full reference G. Both sources' separately declared point-intersection diagnostics also prefer B. Changing the formation location therefore does not remove the observed objective/reference conflict. This is not proof that B is physically correct, G is wrong, or every membership bias has been excluded.

My decision is to stop further pose refinement and parameter sweeps on this shared-plane objective until independent physical observation evidence is available. The next distinct development alternative is tiny native-output adaptation capability diagnosis, described as design only in NEXT_ROUND_PLAN.md. No adapter or new accuracy method was executed here.

## Fixed execution and complete census

Reuse exact CV2 first-accepted 00/05/06 revisits 2429->3373,538->1302,150->978; two eight-scan visits per case, 48 scan bindings and 288000 retained points. B/F/T are copied from sealed CV2 banks; G uses the same full-reference camera-to-LiDAR/proper-rotation convention as the earlier oracle diagnosis. G is a diagnostic input only. No preprocessing, point set, scan time, calibration, threshold, scale, hash, case, prior or pose was changed.

Complete 2m voxels use >=6 points per contributing scan, >=3 scans, >=40 points, the existing plane/offset rules and both-visit support. All eligible B keys, moments, labels and whole-patch hash splits reproduce CV2 exactly. Every candidate and rejected point is accounted for, including sub-six-point scan contributions inside accepted voxels.

| Case | Formation | Candidate voxels | Support rejected | Plane rejected | Single-visit rejected | Cross accepted | Train / holdout |
|---|---|---:|---:|---:|---:|---:|---:|
| 00 | B | 2957 | 2405 | 336 | 0 | 216 | 163 / 53 |
| 00 | G | 3131 | 2596 | 374 | 7 | 154 | 115 / 39 |
| 05 | B | 3367 | 2868 | 332 | 35 | 132 | 102 / 30 |
| 05 | G | 3383 | 2872 | 344 | 38 | 129 | 95 / 34 |
| 06 | B | 4613 | 4201 | 208 | 0 | 204 | 163 / 41 |
| 06 | G | 4604 | 4192 | 212 | 0 | 200 | 162 / 38 |

All **22055 candidate records** were independently reconstructed from explicit retained points. Candidate IDs, accepted labels, rejection reasons, raw/effective per-scan counts, all support-passing eigenvalues and offsets, scan-balanced local moments and hashes agree. This is a complete census of these retained banks, not a census of all uncapped raw returns or independently verified physical surfaces.

The bank stores each scan's source frame, node and every retained row ordinal; freeze.json binds the original raw hashes. These are stable data-row identities, not physical landmarks or invented raw-return indices. The already validated CV2 raw preprocessing is reused and hash-bound, not rerun here.

## Crossed costs: compare within each row

Both memberships were sealed and independently validated before costs were evaluated. Fixed B/G/F/T train, holdout and full-set plane costs were computed with equal patch/contributing-scan mass and analytical plane nuisance refits. Optimizer calls are **zero**; no new pose errors or performance candidate were generated.

| Case | Fixed membership | Train RMS at B (m) | Train RMS at G (m) | Holdout RMS at B (m) | Holdout RMS at G (m) | Train preference |
|---|---|---:|---:|---:|---:|---|
| 00 | B-formed | 0.052995 | 0.128768 | 0.051398 | 0.141372 | B |
| 00 | G-formed | 0.038391 | 0.061328 | 0.038985 | 0.064968 | B |
| 05 | B-formed | 0.050042 | 0.060513 | 0.041500 | 0.049677 | B |
| 05 | G-formed | 0.047274 | 0.056433 | 0.045629 | 0.052969 | B |
| 06 | B-formed | 0.053253 | 0.055432 | 0.051935 | 0.053157 | B |
| 06 | G-formed | 0.052449 | 0.053941 | 0.053609 | 0.053388 | B |

The comparison within each fixed membership is meaningful for that engineered objective. Different rows have different surfaces, points and weights; lower G-formed mean RMS than B-formed mean RMS does not establish a better physical observation model. Reference formation changes selection substantially in 00 and modestly in the other cases, yet does not reverse any training preference.

There is a visible holdout exception: on 06 G-formed holdout, G RMS is about **0.221mm lower** than B. Preserve it; not every partition prefers B. It does not resolve the all-three training conflict or establish a deployable precision method. The frozen preference classification uses training cost and a numerical 1e-10 tie tolerance; no accuracy PASS is defined.

All four existing-pose cost columns, per-patch variances, local gradients and intersection diagnostics are retained in [attempt-02/results.json](attempt-02/results.json), not only the B/G summary shown here. F/T cost improvement is not a new accuracy result or a selector.

## Coverage, regrouping and the common-row diagnostic

| Case | Accepted point intersection | Accepted point union | Point Jaccard | B patches split across G groups | G groups merging B patches |
|---|---:|---:|---:|---:|---:|
| 00 | 10424 | 20337 | 0.512563 | 138 | 139 |
| 05 | 10698 | 13008 | 0.822417 | 80 | 82 |
| 06 | 9993 | 13857 | 0.721152 | 132 | 133 |

Split/merge counts refer to the bipartite graph of shared retained row IDs, not a physical surface-identity graph. All 16 per-scan coverages, exclusive sets, candidate/rejection arrays and complete patch-overlap matrices are saved and independently checked. Same voxel keys alone do not establish the same observed surface.

The declared intersection diagnostic keeps each source's original labels only on rows accepted by both sources. It retains nonempty original patches, reports weak/single-scan support, and renormalizes the remaining scan mass without new eligibility filtering. It does not replace training membership.

| Case | B grouping on shared rows: B / G RMS (m) | G grouping on shared rows: B / G RMS (m) |
|---|---:|---:|
| 00 | 0.030895 / 0.052518 | 0.033324 / 0.058775 |
| 05 | 0.042564 / 0.052193 | 0.043372 / 0.052820 |
| 06 | 0.049076 / 0.050506 | 0.049520 / 0.051019 |

Both groupings still prefer B in each case. Intersection removes exclusive rows but leaves different partitions and weights; it cannot assign unique physical causal shares or rule out all association errors.

## Directional check and interpretation

| Case | B-formed training slope towards G endpoint translation | G-formed training slope |
|---|---:|---:|
| 00 | -0.126450 | -0.066224 |
| 05 | +0.042115 | +0.036333 |
| 06 | -0.338246 | -0.352512 |

Units are engineering cost/m. At B, all second-visit scans translate together towards G's endpoint translation, with the B internal shapes and rotations fixed. 05's slope remains positive with G-formed membership: the local objective still opposes that reference translation direction. This does not contradict CV2's earlier sign reversal after replacing internal shapes; that diagnostic changed internal poses, while this derivative evaluates B shapes under different labels.

00/06 have negative local slopes while the distant full-reference pose costs more. Local directional derivatives and full-reference costs test different changes and distances; no contradiction or global optimum claim follows.

The tested explanation, "formation at B alone accounts for the conflict," is insufficient under these fixed criteria. Internal shape, dynamic or aliased surfaces, scanning/provenance/timing, preprocessing/calibration and reference limitations remain unresolved. The full accepted/rejected census and precise numerical checks narrow implementation uncertainty; they do not identify any of these physical explanations. Official GT and metric conventions remain unchanged.

## Validator-only repair, verification and resources

Original 144-entry freeze, complete bank and synthetic preflight remain intact. The original validator failed while comparing a per-scan list of dictionaries as numeric arrays, after rebuilding and matching the first case's candidate arrays. [AMENDMENT_01.md](AMENDMENT_01.md) describes the separate 178-entry attempt-02 freeze: only recursive list comparison and output routing change. The entire bank/preflight was reused byte-for-byte; all three full census reconstructions were rerun, then the unchanged evaluator and complete cost validator ran. No membership algorithm, scientific threshold, grouping or pose was repaired. The original failure, four-row ledger and INCOMPLETE marker are retained; the validated retry has no INCOMPLETE marker.

Synthetic zero-optimizer census/hash/rejection/gradient/gauge checks pass; gradient FD difference 4.6334e-12. Independent real census/moment/eigenvalue/offset maximum difference **1.1704e-12**, reference-pose reconstruction **1.0125e-13**. Every **84** explicit cost record passes, maximum point-cost/RMS/variance discrepancy **9.9176e-13**; independent translation gradient **2.5396e-14** and directional FD **3.5510e-11**. Prior CV2 B-membership diagnostic costs reproduce. This completes the retained-bank rejected census missing from earlier audits, without optimizer or raw-preprocessing replay.

Eight measured stages including the failed original validation total **24.855108s**, peak observed RSS **69152768 bytes**. Every attempted stage's RSS is captured. The entire dossier including original/retry banks was 61657084 bytes before delivery bookkeeping. Combined 1800s / 2GiB / 512MiB limits pass; no GPU. Imports, WSL startup, design/docs and final identity/delivery bookkeeping are excluded; this is not production latency. There is no old-budget amendment.

Closure verifies both freezes, byte-identical banks/preflight, all five old map delivery seals, the review seal, eight model/config identities and the opaque checkpoint digest. Both original HEADs/branches and two/nine tracked dirty sets remain. No checkpoint deserialization, training, RAP inference, new pose optimizer, full trajectory, official metric replacement, acquisition/install, production/default/backbone/manuscript edit, commit or Git synchronization occurred. Only isolated new helper/maintenance scripts/new docs/mutable handoffs changed. Independent generalization, calibrated confidence and an original breakthrough remain unestablished.
