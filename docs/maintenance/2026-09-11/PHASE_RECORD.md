# M3 offline logging and fresh core replay

## Core closure batch (in progress)

The owner explicitly requested finishing essential reruns/old metric checks in
this turn and entering optimization promptly. FULL_CORE_COMPLETION_PROTOCOL.md
fixes remaining full POSS/05/00 runs; existing full KITTI 06 is retained.
`run_remaining_core.py` runs sequentially with separate exclusive directories.
POSS completed: 1419 frames, 82 keyframes, 4 safe accepted loops, first-pose APE
8.257400 -> 1.822264 m; 1486 source/input identities rechecked. KITTI 05 and 00
are pending. No source algorithm changes. Planned closure: reproduce the existing
18 corrected historical metric rows, consolidate core-baseline-v1, then execute
the predeclared O1 RAP-initialized ICP refinement experiment. Markers determine
completion; this paragraph does not claim the pending steps passed.

## Latest continuation: full KITTI 06 frontend completed

`FULL_FRONTEND_PROTOCOL.md` predeclares KITTI 06 frames 0-1100, fixed core
settings, coarse stage timing boundaries and validation. The maintenance helper
`run_full_kitti06.py` launches the existing production pipeline without modifying
algorithm source. Outputs: [full-kitti06-01](full-kitti06-01/REPORT.md). Both
INCOMPLETE markers are absent; `validation.json` confirms 1101 exact source IDs
and scan paths, available timestamps, 12 complete measurements and exact accepted
edge associations, valid rotations, recomputed metrics and 1168 rechecked input/
source hashes. Initial hashes include every scan, calibration, GT, model weights,
RAP Python/config files and SLAM modules. All 12 candidates were accepted and
GT-labeled safe; 202 keyframes were selected, including source frame 1100.

First-pose LiDAR APE: 2.777067 -> 2.446184 m. Rigid-aligned APE:
0.893350 -> 0.868971 m. Camera-frame all-segment drift (570 segments) translation:
0.643021% -> 0.667058%; rotation: 0.319708 -> 0.316593 deg/100 m. The translation
drift worsens despite global APE improvement; retain this negative result.
This is local evaluation on a KITTI training sequence, not a benchmark submission.

Production wall times: loading 14.82 s, odometry 48.47 s, loop closure 24.35 s,
PGO 0.07 s, evaluation/map export 11.88 s; total 99.61 s. Subprocess including
startup: 100.40 s. Preflight hashes warm input reads. These coarse one-run timings
do not establish cold-cache or real-time performance. Fresh odometry SHA256
04cd88e1...b22da matches the legacy KITTI 06 odometry byte-for-byte. Optimized
trajectory bytes differ from core-replay-01, though reported APE agrees to six
decimals; numerical equivalence beyond this was not tested or claimed.

No production source or legacy outputs changed. Both whitespace checks passed.
HEADs remain 4055d92 / 6d3f2d2, all maintenance edits uncommitted and unpushed.
Snapshot marker and central manifest hash were checked as before; independent
backup remains outstanding. M3/M4/M5 are not complete. Next: extend the frozen
full frontend protocol to POSS, KITTI 05 and 00 with the already defined ranges,
then consolidate per-sequence APE, camera drift where applicable and timing.
Optional statistical claims remain deferred pending suitable independent cohorts.

## Latest continuation: matched conventional registration comparator

This entry supersedes earlier next-step paragraphs below. The protocol in
[REGISTRATION_COMPARATOR_PROTOCOL.md](REGISTRATION_COMPARATOR_PROTOCOL.md) was
written before execution. `run_registration_comparator.py` ran Open3D 0.19
point-to-point ICP on all 40 frozen candidates with identity and odometry initial
transforms, fixed settings, production geometric preprocessing and the same
heuristic gate / relfloor + Huber backend. No GT enters initialization or gating.
The maintenance helper imports RAP-SLAM; neither repository's production source
was changed in this continuation. See [results](comparator-01/REPORT.md).

Identity ICP accepted 35/40: all 35 accepted results are safe and five rejected
results are dangerous under the declared pose-error labels. Odometry ICP accepted
40/40, all safe. All 80 attempts completed without exception. RAP's first-pose APE
is lower than identity ICP on all four sequences, but odometry ICP is better on
KITTI 05 (2.911334 vs RAP 3.417117 m). Preserve that counterexample. All ICP arms
improve over odometry. Different accepted sets are part of the fixed-gate system
comparison, not a registration-only isolation. ICP is local; no superiority over
global registration or unseen population is established. Its five dangerous
results do not create an independent RAP calibration cohort.

Validation: synthetic known-rigid-transform direction check passed; 125 source
and input hashes were rechecked after execution, including scans against the
previous replay hashes. Independent saved-log validation confirms exact candidate
order for both arms, recomputed gate decisions and all 75 measurement-to-edge
transform associations. Both Git whitespace checks passed (line-ending warnings
only). New outputs have no INCOMPLETE marker. The preservation directory exists,
has no INCOMPLETE marker, and the central manifest SHA256 matches the recorded
d9f23fdd...d497 value; the entire 4.6 GB snapshot was not rehashed this session.

HEADs remain RAP-main 4055d92 / RAP-SLAM 6d3f2d2. Maintenance work remains
uncommitted/unpushed. No legacy outputs were overwritten; independent-device
backup remains outstanding. M3/M4/M5 are not declared complete.

Exact next step: predeclare and run an explicit-source-frame full frontend core
rerun, starting KITTI 06, using the fixed paper protocol. Record stage runtimes
and evaluate with the corrected frame/metric chain. This replaces historical
frontend binding assumptions; do not expect the refreshed frontend to reproduce
historical trajectories exactly. Statistical arms remain deferred pending
independent cohorts with suitable class support.

## Later continuation: paper protocol and controlled backend comparison

The next-step paragraph at the end of the original entry below is now superseded.
`CORE_PAPER_PROTOCOL.md` fixes scope, metrics and comparisons, explicitly after
observing core-replay-01 and before this new ablation. The four existing sequences
remain development evidence rather than an unseen holdout.

`scripts/maintenance/run_core_backend_ablation.py` executed 16 optimizations:
fixed/relfloor noise crossed with no kernel/Huber, reusing the same fresh edges
and frozen frontend in every arm. All trajectories are finite; all four default
arms reproduce saved fresh trajectories within absolute tolerance 1e-8. Outputs,
metrics and source/input hashes are in [backend-ablation-01](backend-ablation-01/REPORT.md).
No legacy outputs or production source were changed in this continuation.

The largest first-pose APE spread between backend arms is approximately 0.00055 m
on POSS; other sequences differ by less than 0.00001 m. The clean 40-edge cohort
does not demonstrate superiority of robust weighting. Preserve this negative
ablation rather than turning backend complexity into an unsupported contribution.
All arms improve over frozen odometry, supporting the loop-correction system on
these sequences. This does not establish superiority of RAP over another registrar.

Next: fix a conventional registration comparator and evaluate identical candidate
pairs, preprocessing and explicit initial conditions, recording its own acceptance
policy before execution. Keep optional statistical gating deferred pending suitable
independent cohorts. M5 protocol work has started, not completed. Git HEADs and
uncommitted/unpushed state remain unchanged; no full frontend or GPU rerun in this
continuation. The prior same-volume preservation and independent-backup limitation
remain unchanged.

Executed 2026-09-11. This record supersedes the previous next step to integrate
offline measurement logging. M3 statistical validation remains incomplete.

## Delivered changes

Production changes are in RAP-SLAM: new `rap_slam/verification_log.py`, optional
invocation identity in `measurement.py`, immediate generation callbacks in
`rap_backend.py`, recording in `loop_closure.py`, and fresh-output handling in
`scripts/run_pipeline.py`. Each attempted candidate records source frames,
completed generations, selected measurement, gate decision or inference failure.
Accepted edges reference the exact selected measurement ID. Partial generations
survive later inference failure; evidence-write errors abort execution. Writes
are incremental, not a power-loss durability guarantee. Other pipeline exceptions
can leave started events; INCOMPLETE prevents interpreting those runs as finished.
Existing output directories are refused. Historical runners that precreate their
output directory must be adjusted before reuse; do not target legacy outputs.

New `scripts/replay_core_candidates.py` regenerates retrieval and RAP measurements
on saved offline odometry/keyframes, then performs PGO and evaluation. It records
parent hashes, scan hashes, source IDs, candidates, causal descriptor features,
checkpoint/source identities and all verification events. This is loop-stage
revalidation; historical frontend frame-range correspondence remains an assumption.

## Executed checks

- [Recorder validation](m3-logging/check-01/validation.json): eight checks passed,
  covering accepted/rejected/failed attempts, multigeneration identity, partial
  failure, invalid rotations, fatal recording failure, mismatched selection,
  existing-log refusal and compatibility without a recorder.
- [Pipeline validation](m3-logging/pipeline-check-01/validation.json): three checks
  passed for failure preservation/no final output, overwrite refusal, and real GPU
  measurement-to-edge/source-frame correspondence.
- Real KITTI 06 frames 128-137: ten frames, two automatically proposed candidates,
  two generations each, both accepted, complete PGO/evaluation/output. Output is
  `.maintenance-archive/2026-09-11-m3-pipeline-01` under RAP-main. First-pose APE
  worsened from 0.0565667393 m to 0.0875247569 m. This deliberately short-separation
  integration check is not a paper benchmark; retain the negative result.
- Both worktree diff whitespace checks passed. No upstream RAP model changes.

## Fresh core evidence

See [report](m3-logging/core-replay-01/REPORT.md), preregistered run protocol and
per-sequence products in the same directory. Candidate budget 12, one generation,
seed 42 reset per sequence, heuristic overlap >= 0.7 and mean distance <= 2.5 m,
NMS 0, relfloor + Huber. Shared backend RNG follows recorded candidate order;
this does not promise isolated per-request randomness.

| Sequence | Candidates / accepted | Odom first APE m | Fresh first APE m |
|---|---:|---:|---:|
| POSS | 4 / 4 | 8.2574 | 1.8223 |
| KITTI 06 | 12 / 12 | 2.7771 | 2.4462 |
| KITTI 05 | 12 / 12 | 5.1935 | 3.4171 |
| KITTI 00 | 12 / 12 | 12.2667 | 11.4329 |

[Final association check](m3-logging/core-replay-01/final_validation.json) verified
every accepted edge against its logged transform. All 40 measurements are labeled
safe under the declared 5 m / 10 degree pose-error rule; maximum rotation
orthogonality residual is 2.526e-6. These are correlated, budget-filtered candidates,
not an independent test population. No dangerous examples means this run cannot
estimate dangerous-edge acceptance or fit/validate conformal coverage. KITTI 00's
historical big-budget result used a different budget, so comparing it with this
run does not isolate the precision fix. Replay drift metrics use the LiDAR frame;
do not present them as the official camera-frame KITTI score.

## Preservation, status and exact next step

Legacy outputs remain untouched; successful new runs have no INCOMPLETE marker.
The earlier M3 first-batch source manifest was finalized and its staging directory
removed. This turn's source identities are preserved in `m3-logging/final_source_manifest.json`.
RAP-main HEAD 4055d92 and RAP-SLAM HEAD 6d3f2d2 remain unchanged; maintenance edits
are uncommitted and unpushed. Independent-device backup remains outstanding.

Next, write the core paper comparison protocol before running more experiments:
freeze frontend, retrieval budget, gate and metric frame; distinguish baseline
comparisons from component ablations. Predeclare any additional cohort by whole
sites/sequences, including natural rejected candidates, before calibration. Keep
the fixed heuristic as the master's-thesis core and defer optional statistical
claims if class support or independent partitions remain inadequate. Do not
resume the superseded S2-S5 checklist or declare M3/M4/M5 wholly complete.
