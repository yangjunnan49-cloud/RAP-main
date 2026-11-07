# M3 fresh measurement pilot

Status: dataset-chain validation passed; statistical validation is pending.

- 24 preselected physical pairs across KITTI-02, KITTI-06 and POSS-00.
- 48 new GPU registrations; every transform, diagnostic and GT label belongs to the same generation.
- 24 selected-generation rows: 13 safe, 11 dangerous under the declared 5 m / 10 degree pose-error rule.
- All 24 historical SC margins are available, with query/self/future/nearby-site exclusion.
- Fit / calibration / test: 9 / 10 / 5 physical pairs, with no identical or reversed-pair overlap.
- 1 physical pair changes pose-correctness label between its two new generations.
- Heuristic gate on selected pilot rows: 13 safe accepted, 11 dangerous rejected.

These are deliberately chosen historical cases, not a random retrieval population. Nearby places and shared scans can remain correlated across pair groups. Only five dangerous calibration pairs are present. No conformal model was trained or guarantee claimed.

## Selected measurements

| Dataset | Source frames | Generation | Overlap | Mean distance m | TE m | RE deg | Label | SC margin |
|---|---|---:|---:|---:|---:|---:|---|---:|
| kitti/02 | 1609, 2215 | 1 | 0.3349 | 2.9228 | 95.502 | 12.645 | dangerous | -0.1414 |
| kitti/02 | 748, 1932 | 1 | 0.0793 | 21.3023 | 477.937 | 93.729 | dangerous | -0.1844 |
| kitti/02 | 1477, 2225 | 0 | 0.1091 | 12.1700 | 260.490 | 144.924 | dangerous | -0.1382 |
| kitti/02 | 813, 1597 | 1 | 0.1056 | 8.7817 | 301.420 | 7.979 | dangerous | 0.0191 |
| kitti/02 | 753, 1912 | 0 | 0.0966 | 11.9878 | 456.708 | 103.166 | dangerous | -0.2060 |
| kitti/02 | 1527, 2210 | 0 | 0.0436 | 19.1672 | 239.639 | 8.330 | dangerous | -0.0161 |
| kitti/02 | 1507, 2215 | 1 | 0.0730 | 10.8103 | 241.532 | 11.362 | dangerous | -0.0439 |
| kitti/02 | 753, 1944 | 1 | 0.0922 | 14.2810 | 491.695 | 91.175 | dangerous | -0.2259 |
| kitti/02 | 1502, 2270 | 0 | 0.1588 | 4.5014 | 161.253 | 4.836 | dangerous | -0.0323 |
| kitti/02 | 1532, 2215 | 0 | 0.1092 | 11.3176 | 211.330 | 178.850 | dangerous | -0.0277 |
| kitti/02 | 813, 1603 | 1 | 0.0685 | 12.2280 | 270.192 | 16.948 | dangerous | -0.0445 |
| kitti/02 | 1918, 4500 | 1 | 0.9677 | 0.3376 | 2.155 | 0.375 | safe | 0.1672 |
| kitti/02 | 1039, 4275 | 1 | 0.8179 | 0.9727 | 3.210 | 0.214 | safe | -0.2314 |
| kitti/02 | 966, 4230 | 0 | 0.9639 | 0.3854 | 3.448 | 0.096 | safe | 0.1681 |
| kitti/02 | 1878, 4465 | 1 | 0.9677 | 0.3523 | 2.098 | 0.265 | safe | 0.1621 |
| kitti/02 | 2004, 3402 | 0 | 0.7731 | 1.4754 | 2.206 | 0.433 | safe | -0.1677 |
| kitti/02 | 937, 4213 | 0 | 0.8813 | 0.7267 | 3.783 | 0.213 | safe | -0.0037 |
| kitti/02 | 3366, 4605 | 0 | 0.8624 | 0.6516 | 0.558 | 0.103 | safe | -0.0382 |
| kitti/02 | 1928, 4520 | 1 | 0.9261 | 0.4806 | 2.859 | 0.317 | safe | 0.1446 |
| kitti/02 | 1893, 4470 | 1 | 0.9229 | 0.5228 | 2.203 | 0.429 | safe | 0.1841 |
| poss/00 | 3850, 5244 | 1 | 0.7603 | 1.0095 | 0.482 | 0.216 | safe | 0.0173 |
| poss/00 | 3850, 5265 | 0 | 0.8670 | 0.6107 | 0.324 | 0.205 | safe | 0.3260 |
| kitti/06 | 133, 963 | 1 | 0.9155 | 0.5163 | 0.092 | 0.116 | safe | 0.3972 |
| kitti/06 | 128, 958 | 0 | 0.8770 | 0.5927 | 0.069 | 0.122 | safe | 0.3624 |

## Next decision

Expand independent physical sites/sequences and predeclare sampling before training any optional statistical gate. Keep the fixed heuristic as the core baseline. The sequence-holdout diagnostic exposes class/support gaps; it is not a replacement for a sufficiently populated split.
