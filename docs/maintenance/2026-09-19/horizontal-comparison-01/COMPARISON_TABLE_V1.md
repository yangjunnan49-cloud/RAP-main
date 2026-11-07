# RAP-SLAM horizontal comparison v1 (HC-V1)

Ours: corrected core baseline v1 (2026-09-11 frozen full reruns, budget-12 defaults, no intrinsic angle correction). Front-end: KISS-ICP with a single POSS-tuned config (max_range 80 m, min_range 1.5 m, voxel 0.8 m) — weaker than published KISS-ICP. Full system adds Scan Context + proximity retrieval, RAP K=4 generative verification (overlap >= 0.7 & mean_dist <= 2.5 m), loop-edge NMS (w=10), relfloor+Huber GTSAM PGO.

Coverage: our core-baseline sequences are KITTI 00/05/06 (+POSS-A). Literature 00–10 averages are verbatim quotes, not same-coverage comparisons; the `mean 00/05/06` column is recomputed over exactly those three sequences for every row.

## Table 1 — KITTI relative translational drift ter [%] (camera frame; per sequence)

| method | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | mean 00/05/06 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOAM | 0.78 | 1.43 | 0.92 | 0.86 | 0.71 | 0.57 | 0.65 | 0.63 | 1.12 | 0.77 | 0.79 | 0.67 |
| IMLS-SLAM | 0.50 | 0.82 | 0.53 | 0.68 | 0.33 | 0.32 | 0.33 | 0.33 | 0.80 | 0.55 | 0.53 | 0.38 |
| MC2SLAM | 0.51 | 0.79 | 0.54 | 0.65 | 0.44 | 0.27 | 0.31 | 0.34 | 0.84 | 0.46 | 0.52 | 0.36 |
| S4-SLAM | 0.62 | 1.11 | 1.63 | 0.82 | 0.95 | 0.50 | 0.65 | 0.60 | 1.33 | 1.05 | 0.96 | 0.59 |
| PSF-LO | 0.64 | 1.32 | 0.87 | 0.75 | 0.66 | 0.45 | 0.47 | 0.46 | 0.94 | 0.56 | 0.54 | 0.52 |
| SuMa | 0.68 | 1.70 | 1.20 | 0.74 | 0.44 | 0.43 | 0.54 | 0.74 | 1.20 | 0.62 | 0.72 | 0.55 |
| SuMa++ | 0.64 | 1.60 | 1.00 | 0.67 | 0.37 | 0.40 | 0.46 | 0.34 | 1.10 | 0.47 | 0.66 | 0.50 |
| LiTAMIN2 | 0.70 | 2.10 | 0.98 | 0.96 | 1.05 | 0.45 | 0.59 | 0.44 | 0.95 | 0.69 | 0.80 | 0.58 |
| LO-Net | 0.78 | 1.42 | 1.01 | 0.73 | 0.56 | 0.62 | 0.55 | 0.56 | 1.08 | 0.77 | 0.92 | 0.65 |
| MULLS-LO | 0.51 | 0.62 | 0.55 | 0.61 | 0.35 | 0.28 | 0.24 | 0.29 | 0.80 | 0.49 | 0.61 | 0.34 |
| MULLS-SLAM | 0.54 | 0.62 | 0.69 | 0.61 | 0.35 | 0.29 | 0.29 | 0.27 | 0.83 | 0.51 | 0.61 | 0.37 |
| CT-ICP | 0.49 | 0.76 | 0.52 | 0.72 | 0.39 | 0.25 | 0.27 | 0.31 | 0.81 | 0.49 | 0.48 | 0.34 |
| pyLiDAR-F2M | 0.51 | 0.79 | 0.51 | 0.64 | 0.36 | 0.29 | 0.29 | 0.32 | 0.78 | 0.46 | 0.57 | 0.36 |
| KISS-ICP (no per-seq ter) | – | – | – | – | – | – | – | – | – | – | – | – |
| F-LOAM (no per-seq ter) | – | – | – | – | – | – | – | – | – | – | – | – |
| **ours odometry (core-baseline-v1)** | 0.90 | – | – | – | – | 0.77 | 0.64 | – | – | – | – | **0.77** |
| **ours full (core-baseline-v1)** | 0.91 | – | – | – | – | 0.70 | 0.67 | – | – | – | – | **0.76** |
| **KISS-SLAM (same-data run, default cfg)** | 0.58 | – | – | – | – | 0.52 | 0.33 | – | – | – | – | **0.47** |

Literature sources and correction conventions: see `RAP-SLAM/data/literature/kitti_baselines.json` (accessed 2026-08-22). ter is a local (<=800 m) drift metric; loop closure mainly improves global consistency (Table 3).

## Table 2 — KITTI relative rotational drift rer [deg/100 m]

| method | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | mean 00/05/06 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SuMa++ | 0.22 | 0.46 | 0.37 | 0.46 | 0.26 | 0.20 | 0.21 | 0.19 | 0.35 | 0.23 | 0.28 | 0.21 |
| LiTAMIN2 | 0.28 | 0.46 | 0.32 | 0.48 | 0.52 | 0.25 | 0.34 | 0.32 | 0.29 | 0.40 | 0.47 | 0.29 |
| LO-Net | 0.42 | 0.40 | 0.45 | 0.59 | 0.54 | 0.35 | 0.35 | 0.45 | 0.43 | 0.38 | 0.41 | 0.37 |
| MULLS-LO | 0.18 | 0.09 | 0.17 | 0.22 | 0.08 | 0.17 | 0.11 | 0.18 | 0.25 | 0.15 | 0.19 | 0.15 |
| MULLS-SLAM | 0.13 | 0.09 | 0.13 | 0.22 | 0.08 | 0.07 | 0.08 | 0.11 | 0.17 | 0.12 | 0.19 | 0.09 |
| **ours odometry (core-baseline-v1)** | 0.39 | – | – | – | – | 0.36 | 0.32 | – | – | – | – | 0.35 |
| **ours full (core-baseline-v1)** | 0.39 | – | – | – | – | 0.34 | 0.32 | – | – | – | – | 0.35 |
| **KISS-SLAM (same-data run, default cfg)** | 0.16 | – | – | – | – | 0.21 | 0.07 | – | – | – | – | 0.15 |

## Table 3 — Global consistency: aligned ATE RMSE [m] (SE(3) Umeyama, evo `--align`)

Literature rows are the verbatim PIN-SLAM T-RO 2024 Table IV family (decimeter precision, motion-compensated clouds; ‡ = offline PGO; PIN-LO/PIN-SLAM are 10-run means). Their printed `Avg.*` (loop sequences) and `Avg.` columns are quoted verbatim after the per-sequence cells.

| method | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | mean 00/05/06 | Avg.* (printed) | Avg. (printed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SuMa | 1.10 | 14.60 | 8.00 | 1.00 | 0.30 | 0.70 | 0.60 | 1.10 | 3.70 | 1.20 | 1.40 | 0.80 | 2.30 | 3.10 |
| MULLS | 1.10 | 1.90 | 5.40 | 0.70 | 0.90 | 1.00 | 0.30 | 0.40 | 2.90 | 2.10 | 1.10 | 0.80 | 1.90 | 1.60 |
| Litamin2 | 1.30 | 15.90 | 3.20 | 0.80 | 0.70 | 0.60 | 0.80 | 0.50 | 2.10 | 2.10 | 1.00 | 0.90 | 1.50 | 2.40 |
| SC-LeGO-LOAM | 2.30 | 19.70 | 5.30 | 1.60 | 0.40 | 1.20 | 1.00 | 1.50 | 5.90 | 2.00 | 1.70 | 1.50 | 2.70 | 5.30 |
| HLBA ‡ | 0.80 | 1.90 | 5.10 | 0.60 | 0.80 | 0.40 | 0.20 | 0.30 | 2.70 | 1.30 | 1.10 | 0.47 | 1.50 | 1.40 |
| SC-F-LOAM ‡ | 1.30 | 4.70 | 3.30 | 0.70 | 0.30 | 1.20 | 0.40 | 0.50 | 3.00 | 1.30 | 1.60 | 0.97 | 1.60 | 1.70 |
| SC-KISS-ICP ‡ | 1.00 | 3.70 | 1.90 | 0.40 | 0.30 | 0.30 | 0.30 | 0.30 | 2.20 | 1.00 | 0.80 | 0.53 | 1.00 | 1.10 |
| PIN-LO | 5.60 | 4.30 | 9.30 | 0.70 | 0.10 | 1.70 | 0.50 | 0.50 | 3.00 | 1.80 | 0.80 | 2.60 | 3.20 | 2.60 |
| PIN-SLAM | 0.80 | 4.30 | 2.10 | 0.70 | 0.10 | 0.30 | 0.40 | 0.30 | 2.10 | 1.20 | 0.80 | 0.50 | 1.00 | 1.20 |
| **ours full (core-baseline-v1)** | 2.89 | – | – | – | – | 1.13 | 0.87 | – | – | – | – | 1.63 | – | – |
| **ours odometry (core-baseline-v1)** | 3.94 | – | – | – | – | 1.87 | 0.89 | – | – | – | – | 2.23 | – | – |
| **KISS-SLAM (same-data run, default cfg)** | 0.92 | – | – | – | – | 0.66 | 0.33 | – | – | – | – | 0.64 | – | – |

Known transcription notes (kept verbatim, not corrected): Naive 11-sequence mean of the printed Litamin2 row is 2.64, but the printed Avg. is 2.4; the naive mean of SC-LeGO-LOAM is 3.87, but the printed Avg. is 5.3. All other rows match naive means at decimeter rounding. The caption does not define the plain Avg. column beyond Avg.*; printed values are kept verbatim and the inconsistency is reported, not corrected.; Third-party surveys transcribe the arXiv v1 of this table (e.g. PIN-SLAM seq 02 = 3.3); the archived T-RO v2 PDF prints 2.1. This file follows the archived T-RO version only.

### Flagged context rows (legacy live products, same metric code; NOT core-baseline)

| seq | product | aligned ATE [m] | note |
|---|---|---|---|
| 01 | step3_kitti01 | 19.87 | legacy live product, no true revisits |
| 02 | step3_kitti02_current | 4.03 | legacy live product, current-backend PGO rerun |
| 03 | step3_kitti03 | 0.88 | legacy live product, no true revisits |
| 04 | step3_kitti04 | 0.40 | legacy live product, no true revisits |

### POSS-A (ours only; no published baseline)

frames 1419, loops accepted 4; aligned ATE odometry 2.564951 -> full 0.666054 m; unaligned APE 8.257400 -> 1.822264 m. POSS (PKU campus, Velodyne-32e): no published baseline; cross-sensor generalization set, LiDAR-frame drift in registry.
