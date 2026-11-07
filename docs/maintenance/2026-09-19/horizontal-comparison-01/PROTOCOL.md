# HC-V1: Horizontal comparison protocol (system level, KITTI trajectory metrics)

2026-09-19. Owner authorized the A+B combination this session: (A) literature
transcription upgrade of the paper comparison table, (B) actual KISS-SLAM runs
on KITTI 00/05/06. This protocol follows the established maintenance discipline:
prospective declaration, hash freeze before outcomes, exclusive output
directory, independent validation, no production/default changes, no Git sync.

Exclusive directory: `docs/maintenance/2026-09-19/horizontal-comparison-01/`.
Do not rerun or overwrite once completed.

## 1. Positioning

Descriptive thesis comparison evidence, not a new method screen. No decision
gate about research directions follows from this table automatically. The
breakthrough-direction-01 F1 preparation remains the separate next research
task and is not advanced or blocked by this work.

## 2. Comparator set (frozen, five named + table family)

Named comparators selected 2026-09-19 with the owner:

1. PIN-SLAM (Pan et al., T-RO 2024) — first-tier neural-implicit LiDAR SLAM
   with loop closure. Source: archived T-RO preprint PDF `sources/
   2401.09101v2_pin_slam.pdf`, Table IV (KITTI ATE RMSE [m], Umeyama-aligned,
   decimeter precision, 10-run mean) and Table III (odometry ter).
2. KISS-SLAM (Guadagnino et al., IROS 2025) — modern LiDAR-only full SLAM,
   same KISS-ICP lineage as our front-end. No published KITTI numbers found;
   obtained by actual local execution (Section 5).
3. CT-ICP (Dellenbach et al., ICRA 2022) — first-tier odometry-only ceiling.
   Existing ter row in `RAP-SLAM/data/literature/kitti_baselines.json`
   (read-only reference; that file is NOT modified).
4. MULLS (Pan et al., ICRA 2021) — classic full SLAM; ter/rer rows already
   transcribed; ATE row from PIN-SLAM Table IV.
5. SuMa++ (Chen et al., IROS 2019) — classic surfel SLAM with loop closure;
   ter/rer rows already transcribed. The ATE table uses the SuMa row of
   PIN-SLAM Table IV (SuMa++ per-sequence ATE exists only in third-party
   papers; flagged, not mixed into the same-source block).

The ATE table additionally carries the full same-source Table IV family
(SC-KISS-ICP, SC-F-LOAM, SC-LeGO-LOAM, HLBA, Litamin2, PIN-LO) because they
share PIN-SLAM's exact evaluation convention. SC-KISS-ICP (Scan Context
retrieval + KISS-ICP odometry + ICP refine + offline PGO) is the closest
classical analogue of our architecture and is a headline row.

## 3. Our canonical numbers

"Ours" = corrected core baseline v1 (`docs/maintenance/2026-09-11/
core-baseline-v1/`, frozen full reruns `full-poss-01`, `full-kitti06-01`,
`full-kitti05-01`, `full-kitti00-01`; budget 12 defaults; no intrinsic angle
correction). Metrics are recomputed from those frozen trajectory outputs with
the existing metric code (`rap_slam.evaluate` APE conventions and
`rap_slam.trajectory_protocol.kitti_drift`, M2 v2 all-segment protocol), and
must match `core-baseline-v1/registry.json` within 1e-9.

The older P0 draft `RAP-SLAM/output_paper_metrics/comparison_table.md` is
superseded for citation purposes because (a) its 00 product is the legacy
budget-40 run and (b) its drift values predate the M2 v2 all-segment
aggregation fix. It is left untouched on disk.

Secondary context rows (clearly flagged, never mixed into headline claims):
KITTI 01/03/04 live products (no true revisits; equal to odometry by
construction) and KITTI 02 (live edges with current-backend PGO rerun).
POSS has no published baseline and stays an ours-only block.

## 4. Metric conventions (never mixed in one column)

- ter/rer: KITTI official protocol, all-segment mean (M2 v2), camera
  reference frame for KITTI, LiDAR frame for POSS. Literature rows annotated
  where a 0.2/0.205 deg intrinsic angle correction was applied by the authors
  (MULLS family, CT-ICP); ours applies none.
- ATE: unaligned first-pose-anchored APE RMSE (our running convention) and
  Umeyama SE(3)-aligned ATE RMSE (evo `--align` convention = PIN-SLAM Table IV
  convention) are separate columns/tables. Decimeter precision of the
  transcribed literature rows is stated once in the table header.

## 5. Part B: KISS-SLAM actual execution

- Environment: WSL Ubuntu-24.04 on the same machine. Fresh venv
  `~/venvs/kiss-slam-hc1`. Primary install path: `pip install kiss-slam`
  (PyPI release; exact version recorded via `pip freeze`). Fallback: clone
  `github.com/PRBonn/kiss-slam` at tag `IROS25` + editable install per README
  (apt deps libeigen3-dev/libsuitesparse-dev). If both fail after at most 2
  hours of environment work, B is declared INFEASIBLE_ENV with logs archived;
  no further escalation in this version.
- Data (read-only): `/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset/`
  with `sequences/{00,05,06}/velodyne` and `poses/{00,05,06}.txt`. GT file
  SHA256 recorded; must equal the hashes used by core-baseline-v1 (recorded in
  its `source_hashes`).
- Runs: sequences 00, 05, 06; all frames; one run per sequence; the
  unmodified default config from `kiss_slam_dump_config` archived per run.
  No parameter tuning, no restart-after-inspection with changed settings.
  A failed sequence stays failed with its log archived.
- Caps: CPU-only expectation, total wall <= 2 h for the three runs
  (00 approx 4541 frames), recorded per run.
- Outputs (all copied back into `b-kiss-slam/`): pose files (their native
  format + KITTI-format conversion if needed), stdout/stderr logs, config,
  `pip freeze`, run manifest with output SHA256s.
- Evaluation: new additive script `RAP-SLAM/scripts/eval_external_trajectory.py`
  (does not modify existing files) computing the same metrics as Section 3
  from the KISS-SLAM pose files against the same GT. Frame count must equal
  GT length exactly (4541/2761/1101); any mismatch stops evaluation and is
  reported, not patched.

## 6. Execution plan for A

- New maintenance helper `RAP-main/scripts/maintenance/
  build_horizontal_comparison.py` plus validator
  `validate_horizontal_comparison.py`. Existing comparison assets
  (`kitti_baselines.json`, `comparison_table.md`, `make_comparison_table.py`)
  are read-only inputs, never edited.
- New literature file `data-literature/kitti_ate_pin_slam_tab4.json` inside
  this exclusive directory, transcribed solely from the archived PDF page 11
  (Table IV); the earlier arXiv v1 numbers circulating in third-party surveys
  differ (e.g. PIN-SLAM row 02: 3.3 v1 vs 2.1 v2) and are superseded by the
  T-RO version; the discrepancy is recorded in the report.
- Output: `COMPARISON_TABLE_V1.md` + `comparison_v1.json`.

## 7. Independent validation (before REPORT.md is finalized)

1. Re-extract Table IV text from the archived PDF and diff against the
   transcribed JSON (exact match at the printed precision).
2. Recompute our four-sequence metrics from the frozen `full-*-01` outputs;
   require <=1e-9 vs `registry.json`.
3. Recompute all table means (00-06 mean, Avg.*, Avg.) from JSON and require
   exact consistency with the rendered Markdown.
4. B: recompute KISS-SLAM metrics from archived pose outputs; verify frame
   counts, finiteness, monotonic order, GT hash match, and that config is the
   unmodified default.
5. Verify no writes outside the declared allowlist (this directory; the two
   new RAP-SLAM/RAP-main helper scripts; WSL venv).

## 8. Boundaries

No production/default changes; no edits to completed maintenance directories;
no Git commit/push/reset; no outcome-based row selection — all declared rows
ship regardless of favorability; no claim that transcription equals same-data
comparison (only B rows are same-data); POSS rows carry no literature claims.
