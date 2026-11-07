# 2026-09-19 phase record

## HC-V1 horizontal comparison complete (A+B, owner-approved)

The owner took the project back from codex (temporarily unavailable) and
approved a horizontal comparison task: A) literature transcription + formal
comparison table, B) a same-data KISS-SLAM run, under the codex-era protocol
discipline. Exclusive directory:
[horizontal-comparison-01](horizontal-comparison-01/REPORT.md).

Five comparators were selected: PIN-SLAM (T-RO 2024, first tier), KISS-SLAM
(IROS 2025, executed locally), CT-ICP, MULLS, SuMa++. Component-level matcher
comparison (KISS-Matcher/GeoTransformer) is deferred to the F1/F2 track.

Part A: PIN-SLAM T-RO v2 PDF archived (sha256 recorded); Table IV transcribed
verbatim (9 rows × 13 values), including two printed-vs-naive-mean
inconsistencies (Litamin2, SC-LeGO-LOAM) kept verbatim. Formal
`COMPARISON_TABLE_V1.md` + `comparison_v1.json` generated from the frozen
core-baseline-v1 registry (budget-12 defaults; 00 values 11.432935/2.891543,
not legacy budget-40). Legacy P0 table superseded, not modified.

Part B: kiss-slam 0.0.2 (kiss-icp 1.3.0, map_closures 2.1.0) installed in a
fresh WSL Python 3.12.3 venv; two undeclared upstream dependencies (pillow,
matplotlib) added; unmodified default config (sha256 recorded). KITTI
00/05/06 each run once on identical data: frames exactly 4541/2761/1101,
closures 7/5/4, wall 173.14/109.39/49.64 s, peak RSS ~1.0 GiB, CPU-only.
Evaluation used the same metric code as the frozen baseline (new additive
`RAP-SLAM/scripts/eval_external_trajectory.py`).

Measured (same data, default cfg): KISS-SLAM ter 0.575/0.517/0.325 %,
rer 0.156/0.213/0.072 deg/100m, aligned ATE 0.9168/0.6614/0.3281 m for
00/05/06 (means 0.472 %, 0.147, 0.636 m). Ours full: ter 0.914/0.704/0.667,
rer 0.389/0.342/0.317, ATE 2.8915/1.1293/0.8690 m (means 0.762 %, 0.349,
1.630 m). On these sequences KISS-SLAM defaults outperform our current system
on both metric families. Contributing factors are listed in the report; no
causal attribution is claimed.

Independent validation: 5/5 checks pass (`validation.json`) across two
environments — PDF re-extraction (9 rows), frozen-baseline recompute
(58 values ≤1e-9), table arithmetic (36 cells), external-run recomputation
(18 values + GT sha256 vs frozen input manifests), write scope (RAP-SLAM
comparison assets unmodified).

New maintenance scripts: `scripts/maintenance/build_horizontal_comparison.py`,
`scripts/maintenance/validate_horizontal_comparison.py` (RAP-main);
`scripts/eval_external_trajectory.py` (RAP-SLAM, additive). No production
defaults changed; no tuning on either side; no completed directory touched;
no Git commit/sync. Both HEADs and prior dirty work remain.

## Post-comparison discussion (2026-09-19)

Owner asked how to improve toward first-tier ("SOTA") level. Fact-checked
before recommending: KISS-SLAM's run had deskew=True in config but its kitti
dataloader passes empty per-point timestamps, so deskew was a no-op — the
2026-08-16 KITTI deskew falsification stands and deskew is off the table for
KITTI. The active front-end differences are the intrinsic 0.205°
vertical-angle correction (theirs on / ours off), max_range 100 vs 80,
min_range 0.0 vs 1.5, mapping voxel 1.0 vs 0.8. The ter gap is front-end
dominated (ours odometry 0.77 vs full 0.76).

Recorded proposal (not approved, not started, no protocol frozen): E0
front-end alignment arms (205 on) / (KISS defaults) / (combined),
odometry-only on 00/05/06 with identical metric code; then best arm
full-system; new frozen baseline branch required; 00/05/06 become development
data after selection; first-tier claim needs frozen confirmation (02/07-10 or
Boreas). E1 backend review only if a post-E0 gap remains; E2 LIO stays
deferred. Proposed first-tier target: ter ≤0.5 % and aligned ATE ≤0.7 m mean
over 00/05/06. F1 research track unchanged.

## Standing research state (unchanged)

The 2026-09-15 breakthrough instruction remains active: F1 engineering
preflight (structured short-motion constraints inside multiview generation)
is the declared next research task and was not started. HC-V1 is a benchmark
task, not a research arm; it does not supersede F1, does not rescue stopped
routes (HL/SC/PG), and makes no publication claim. Manuscript drafting remains
paused. NCLT external role and public-download authorization persist.
