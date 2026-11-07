# HC-V1 — Horizontal comparison of RAP-SLAM against published LiDAR SLAM systems

Date: 2026-09-19. Owner-approved task: horizontal comparison experiment, parts A+B,
following the codex-era protocol discipline (prospective protocol, hash freeze,
exclusive directory, independent validation).

- Protocol: `PROTOCOL.md` (sha256 a0d8dfca6338e462d2dfcecfbcf8958cccf258ac41b81a6df1a8e4221293b9cc, frozen in `FREEZE.json`)
- Exclusive directory: `docs/maintenance/2026-09-19/horizontal-comparison-01/`
- Decision: **COMPLETE — comparison table published with 5/5 independent checks passing.**

This is a measurement report. It makes no efficacy claim beyond the recorded
numbers and establishes no new research direction.

## Scope

- **A (literature transcription + formal table).** Verbatim transcription of
  published per-sequence numbers for the five selected comparators (PIN-SLAM
  T-RO 2024 first-tier, KISS-SLAM IROS 2025, CT-ICP, MULLS, SuMa++) plus the
  pre-existing literature baseline file, and construction of the formal
  comparison table with our frozen core-baseline-v1 numbers.
- **B (same-data external run).** KISS-SLAM executed locally on the identical
  KITTI 00/05/06 data with unmodified default configuration, evaluated with the
  identical metric code as our frozen baseline.
- Component-level matcher comparison (KISS-Matcher / GeoTransformer) is
  explicitly out of scope; it belongs to the F1/F2 research track.

## Our reference numbers (canonical)

Source: frozen core-baseline-v1 (2026-09-11 full-*-01 reruns, budget-12
defaults, no intrinsic angle correction). Camera-frame KITTI drift; SE(3)
Umeyama-aligned ATE. Never mixed.

| sequence | ter full [%] | rer full [deg/100m] | ATE aligned full [m] | ATE aligned odometry [m] |
|---|---|---|---|---|
| 00 | 0.914171 | 0.389455 | 2.891543 | 3.94 |
| 05 | 0.703737 | 0.342123 | 1.129313 | 1.87 |
| 06 | 0.667058 | 0.316593 | 0.868971 | 0.89 |
| mean | 0.761655 | 0.349390 | 1.63 | 2.23 |

(00 uses the budget-12 default values 11.432935/2.891543, not legacy budget-40.)

## Part A — literature transcription

- Archived source: `sources/2401.09101v2_pin_slam.pdf` (arXiv v2 = T-RO 2024
  version, 14,023,329 bytes, sha256
  adbb1b9eab69aa4ba338b2ba52214532675d037cf9808deb6068470d9c92950c).
- Transcription: `data-literature/kitti_ate_pin_slam_tab4.json`, 9 method rows ×
  13 values (11 sequences + printed Avg.* + printed Avg.), verbatim at printed
  decimeter precision.
- Known verbatim notes (reported, not corrected): printed Avg. for Litamin2 is
  2.4 vs naive mean 2.64; SC-LeGO-LOAM 5.3 vs 3.87. v1/v2 version difference
  (PIN-SLAM seq 02: 3.3 → 2.1) recorded; this file follows the archived T-RO v2.
- The legacy `comparison_table.md` (P0) is superseded by
  `COMPARISON_TABLE_V1.md` and was not modified.

## Part B — KISS-SLAM same-data runs

- Environment: fresh WSL venv `/root/venvs/kiss-slam-hc1`, Python 3.12.3,
  kiss-slam 0.0.2 (PyPI wheel), kiss-icp 1.3.0, map_closures 2.1.0, open3d
  0.20.0; `env/pip_freeze.txt` (85 lines). Two undeclared upstream dependencies
  (pillow, matplotlib) were installed; no parameter was changed.
- Config: unmodified defaults; `config/default_config.yaml` sha256
  a17813d28ee273739e0e685913025b3b1091f09229736a2c2cdaf1c566d19718. The kitti
  dataloader applies the intrinsic vertical-angle correction by default
  (upstream default, kept).
- Runs (CPU-only, WSL Ubuntu-24.04):

| sequence | frames | closures | wall [s] | peak RSS [GiB] |
|---|---|---|---|---|
| 00 | 4541 | 7 | 173.14 | 1.04 |
| 05 | 2761 | 5 | 109.39 | 1.02 |
| 06 | 1101 | 4 | 49.64 | 1.02 |

- Pose files are camera-frame (`apply_calibration`: cam = Tr·velo·Tr⁻¹);
  archived under `poses/`, per-run configs under `config/`, logs under `logs/`,
  full manifest with sha256 in `b-kiss-slam/manifest.json` (135 files).
- Evaluation: `RAP-SLAM/scripts/eval_external_trajectory.py` (additive), same
  `eval_paper_metrics.evaluate_pair` code path as the frozen baseline; frame
  counts enforced exactly (4541/2761/1101), no patching.

### Measured KISS-SLAM results (same data, default cfg)

| sequence | ter [%] (camera) | rer [deg/100m] | ATE aligned [m] |
|---|---|---|---|
| 00 | 0.575 | 0.156 | 0.9168 |
| 05 | 0.517 | 0.213 | 0.6614 |
| 06 | 0.325 | 0.072 | 0.3281 |
| mean 00/05/06 | 0.472 | 0.147 | 0.636 |

Measured facts only: on these three sequences KISS-SLAM's default pipeline
outperforms our current system on both local drift and global consistency (ours
mean ter 0.76 vs 0.47; mean aligned ATE 1.63 m vs 0.64 m). Contributing factors
include, non-exclusively: intrinsic angle correction (theirs, not ours),
per-sequence-independent tuned KISS-ICP defaults vs our single POSS-tuned
front-end config, and different loop-closure machinery. No causal attribution
is claimed; our KITTI front-end config is known-weaker (PROTOCOL section on
canonical numbers).

## Deliverables

- `COMPARISON_TABLE_V1.md` — formal tables: T1 ter (18 rows), T2 rer, T3
  aligned ATE (12 rows: PIN-SLAM Tab. IV family + ours + KISS-SLAM same-data),
  legacy context rows flagged, POSS-A (no published baseline).
- `comparison_v1.json` — machine-readable table content.
- `data-literature/kitti_ate_pin_slam_tab4.json`, `sources/` PDF.
- `b-kiss-slam/` — env freeze, default+run configs, poses, logs, g2o graphs,
  eval_results.json, manifest.json (135 sha256 entries).
- `validation.json` — 5/5 checks, two environments.

## Independent validation (all pass)

| check | values | environment |
|---|---|---|
| pdf_transcription | 9 rows re-extracted from archived PDF, exact match | Windows py3.12.14 |
| baseline_recompute | 58 values recomputed from frozen pose files vs registry ≤1e-9 | WSL rap-inference py3.10.20 |
| table_arithmetic | 36 derived cells, md consistency | Windows py3.12.14 |
| external_runs | 18 metric values recomputed from archived poses; GT sha256 matches frozen baseline input manifests | WSL rap-inference py3.10.20 |
| write_scope | RAP-SLAM data/literature + output_paper_metrics unmodified (git) | Windows py3.12.14 |

## Boundaries preserved

No production defaults changed; no tuning of KISS-SLAM or RAP-SLAM for this
comparison; no completed maintenance directory touched; no Git commit/sync;
literature numbers verbatim (not corrected); POSS has no published baseline;
the new scripts (`scripts/maintenance/build_horizontal_comparison.py`,
`scripts/maintenance/validate_horizontal_comparison.py`,
`RAP-SLAM/scripts/eval_external_trajectory.py`) are additive. The F1
engineering-preflight research task declared on 2026-09-15 remains the pending
research next step and is not superseded by this comparison.

## Remaining limitations

- Literature 00–10 coverage vs our 00/05/06 coverage: averages are quoted
  verbatim and the recomputed `mean 00/05/06` column is the only same-coverage
  comparison for literature rows.
- ter/rer literature values are as-printed by their sources (varying correction
  conventions, noted in the table conventions block).
- KISS-SLAM result is a single default-config run per sequence; no variance
  estimate (KISS-SLAM is near-deterministic; PIN-SLAM's own table reports
  10-run means ± std).
