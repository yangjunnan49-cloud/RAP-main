# M2 evaluation and core correctness batch

Date: 2026-09-10. The owner requested sustained progress and clarified master's
thesis scope: prioritize a convincing core system and defensible evidence, with
proportionate attention to details. The active AGENTS.md now records this policy.

## Acceptance and scope

Core M2 acceptance is reached for the offline KITTI/POSS path with bounded tests.
This is not a claim that every optional dataset, live failure case, historical edge,
or paper table is repaired. Next is M3 measurement identity and label consistency.
Spires extrinsics and production live source-stamp logging remain explicitly
deferred until those paths are selected for new thesis evidence. Existing live
products are retained as legacy evidence with stated correspondence assumptions.

| Finding | Change and validation | Remaining boundary |
|---|---|---|
| F02 | Added three fresh KITTI-06 pair comparisons to earlier four POSS pairs and three-part test. Maximum repaired KITTI rotation orthogonality error 2.094e-6 versus 1.103e-3 in fresh TF32 arm. | Legacy RAP edges/labels are not repaired by this patch. |
| F03 | All-segment weighting, strict distance endpoint, actual segment counts, per-segment frame IDs/errors/length/speed; distinct camera-reference KITTI output. | Sampled C++ agreement, not byte-exact parity for every trajectory. |
| F16 | Select scans by numeric source IDs anchored at requested start and stride; reject missing requested scans; select GT by those exact IDs; persist source frame manifest and timestamps where available. | Old manifests cannot be invented; live producer logging remains deferred. |
| F11 | Preserve separate scan observations through voxel selection; adaptive exact capped foreign-label nearest neighbor queries. | Map is still sampled, and GT-composed map is not an independent survey reference. Full old map tables remain legacy. |
| F18 | Empty clique statistics handle zero edges; KISS failure raises by default; fallback requires explicit opt-in; fallback range is applied. | Full ROS fault injection is outside this batch. |
| F10 | Deferred: Spires is outside the current core dataset scope. | Its extrinsic repair is required before using new Spires results. |

## Actual checks and evidence

- [Final regression report](m2-evaluation/check-03/validation.json): 28 checks.
  Cases include missing selected frames, a missing unselected frame with stride,
  duplicate/out-of-order IDs and stamps, persisted-ID GT lookup, live manifest and
  timestamp mismatches, exact-length segment endpoints, original crispness failure,
  coincident foreign observations, empty clique PGO and explicit fallback behavior.
- [Official KITTI page](https://www.cvlibs.net/datasets/kitti/eval_odometry.php) and
  [downloaded official devkit](https://s3.eu-central-1.amazonaws.com/avg-kitti/devkit_odometry.zip)
  were checked. The regression compiled the unchanged metric-function prefix
  from evaluate_odometry.cpp against its matrix.cpp. All first/last/length fields
  matched on 76 exact-distance synthetic segments and 570 KITTI-06 segments.
  Maximum translation-fraction discrepancy was 1.924e-9 on KITTI-06; maximum
  rotation discrepancy 3.130e-7 rad/m. Python uses float64 distances, whereas the
  reference accumulates float distances; tiny boundary/angle effects are possible.
  Speed uses the devkit's nominal 10 Hz inclusive endpoint convention. Strided
  metrics are labeled custom_sparse; they are not dense KITTI benchmark scores.
- The first full devkit harness compilation failed because its bundled main calls
  Mail.finalize, which its mail.h does not define. No metric code was changed to
  overcome this. check-01 is the failed attempt; check-02 passed; check-03 verifies
  final code plus the final live/fallback checks. No mail or benchmark submission
  entry point was run. Compiler warning about the old Matrix::det method is retained.
- [Saved trajectory comparison](m2-evaluation/recompute-01/COMPARISON.md): 18
  trajectories over nine products, including the seven golden product identities.
  Both APE definitions match the legacy evaluator within 1e-9. New LiDAR drift and
  camera drift are separate; every segment is saved in results.json. Original
  trajectory hashes were checked after evaluation. No PGO or RAP edge was replaced.
- [KITTI precision evidence](m2-evaluation/kitti-precision-01/results.json): source
  scans, checkpoint SHA256, explicit seed per pair, transforms and same-run metrics.
  This uses saved accepted pair identities, not a newly measured candidate recall.
- [Pipeline smoke](m2-evaluation/pipeline_smoke.json): actual ten-frame KITTI-06
  run, IDs 128,130,...,146; KISS-ICP, PGO without loop edges, evaluation and map
  output completed. Products are in `.maintenance-archive/2026-09-10-m2-smoke-01`.
  This tests integration and persistence, not thesis performance.

## What the new comparison says

KITTI-03 odometry LiDAR drift changes from 1.1190% to 0.9402%; KITTI-04 from
1.0639% to 0.9273%; KITTI-06 from 0.5829% to 0.6422%. These are aggregation/protocol
changes, not algorithm improvements. Camera reference adds a separate, smaller
change (KITTI-06 odometry 0.6430%).

The old products support improvements in global trajectory consistency on several
sequences, not uniform improvement in local drift. For example, KITTI-05 aligned
APE decreases 1.8686 -> 1.1285 m and camera drift 0.7722 -> 0.7039%, while KITTI-06
offline aligned APE decreases slightly (0.8934 -> 0.8689 m) and camera drift worsens
(0.6430 -> 0.6671%). Keep this mixed outcome in the thesis. Do not selectively
replace datasets or metrics to imply universal superiority.

## Protocol contracts and rerun scope

- Offline new runs save source_frames.json alongside poses. The manifest contains
  ordered source IDs, scan paths, and source timestamps when times.txt is available.
  Existing offline outputs without it are labeled legacy_config_assumed_complete.
- The paper evaluator supports `--offline-only` and refuses an existing output
  directory. The repaired map evaluator requires `--out` naming a new directory.
  Both final command-line help entry points were checked after these options were added.
- New live evaluation requires `<odom_tum>.frames.json` containing actual source IDs
  and the matching TUM timestamps, and requires odometry/map timestamp equality.
  `--allow-legacy-live-index` is an explicit diagnostic escape hatch for old logs;
  it produces an unverified legacy binding label. No timestamps were reverse-guessed.
- APE remains at the LiDAR reference point. KITTI camera drift conjugates both GT
  and estimate with the supplied Tr. Each sequence remains separately reported;
  pooled drift must pool segment records, not silently average sequence means.
- The old odometry and saved-PGO trajectories remain useful diagnostic baselines.
  Any thesis table claimed to use the precision-repaired RAP must regenerate its
  RAP measurements and derived labels, then PGO. Projecting old rotations is not
  such a regeneration. Build measurement identities first in M3 to avoid rerunning
  expensive inference twice. Optional N-way/conformal/sigma arms are outside the
  primary thesis protocol until their separate data and split issues are repaired.

## Git and handoff

RAP-main remains at 4055d92 and RAP-SLAM at 6d3f2d2, with uncommitted maintenance
changes. No pull, push, reset, clean or commit was performed. RAP inference source
is unchanged. Old outputs and the M0 snapshot remain intact; snapshot manifest
identity and absence of INCOMPLETE were rechecked. Same-volume backup limitations
and unknown historical acquisition/checkpoint bindings remain unchanged.

The M2 test runners are in RAP-main/scripts/maintenance. Production changes are
in RAP-SLAM (trajectory_protocol, real_dataset, odometry, pose_graph,
eval_paper_metrics, eval_map_consistency and run_pipeline), in addition to F02.

Exact next action: inspect S1 gens/T_rel feature joins and GT label generation,
introduce measurement_id tied to the selected generation and source frame pair,
then correct historical-candidate SC margin and physical-pair grouping. Produce
a bounded clean dataset and explicit exclusions before any calibration training.
Do not resume the superseded S2 research checklist.
