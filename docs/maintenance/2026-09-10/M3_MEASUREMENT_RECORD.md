# M3 first batch: measurement identity and a fresh pilot

Date: 2026-09-10. Status: the bounded data-chain rebuild passed. M3 is still in
progress; this batch does not complete calibration, independent-site generalization,
production candidate logging, or the paper's full repaired-inference experiment.

## Implemented

- RAP-SLAM `rap_slam/measurement.py` defines physical-pair identity (canonical
  dataset/sequence, unordered source IDs), directed measurement identity with run
  and generation, same-generation metric selection, valid-transform GT labels,
  causal SC margin and deterministic label-independent grouped partitions.
- Pose correctness (5 m / 10 degree thresholds) and place proximity are separate.
  Missing GT or a nonrigid estimate gives an unlabeled result. No pair-only error
  joins or rotation projection are used. Angle uses atan2 after validity checks.
- `scripts/build_s1_dataset_v2.py` is a new exclusive-output pilot builder. It
  persists source selection before inference, scan/GT/calibration hashes, explicit
  request seeds, weight/source hashes, all generations, selected rows and splits.
  Each request's seed is derived from the root seed, physical sequence, ordered
  frame pair and generation. This is a seed contract, not a CUDA bit-exact guarantee.
- SC descriptors were regenerated from raw scans into the new run. The competing
  pool is the saved keyframe list restricted to f < query, query-f >= 200 and
  |f-candidate| >= 100. Self/future candidates are excluded; missing required
  descriptors fail rather than silently reducing the pool. This is a reconstructed
  full historical pool, not a claim to reproduce an old online shortlist/budget.
- The invalid legacy build_s1_features.py main is disabled and directs new work to
  v2. Its pure geometry helpers remain importable. Historical source and outputs
  remain in M0. Its old labeling/feature helpers are not the new data path.

## Evidence actually produced

- [Final focused tests](m3/check-02/validation.json): 18 checks covering generation
  identity, same-generation metrics/labels, reversed physical pairs, invalid input,
  causal feature pools, missing competitors and disjoint/order-independent splits.
- [Legacy audit](m3/check-02/legacy_audit.json): all 828 old candidate rows lack
  T_rel; 114/195 multigen entries mixed mean distance from a different selected
  generation; all 195 selected old rotations fail the declared 1e-5 numerical
  validity bound; 695/828 margins have the -d1 self-match signature. The original
  observations are preserved rather than relabeled by another inference run.
- [Fresh pilot report](m3/pilot-01/REPORT.md): 24 preselected physical pairs,
  48 actual GPU registrations. Selection: all 11 old KITTI-02 false-bucket pairs,
  nine deterministic hash-selected KITTI-02 true-bucket pairs, two old POSS pairs,
  and the first two KITTI-06 offline accepted pairs. Historical bucket names are
  sampling strata, never new labels. 1,079 source scans supplied regenerated SC
  descriptors and endpoint geometry features; no old feature cache was reused.
- All 48 new transforms passed validity and received same-measurement GT labels:
  25 safe / 23 dangerous. The overlap-selected rows are 13 safe / 11 dangerous.
  Four of the 24 pairs would still have mixed diagnostics under the old max/min
  rule. One pair, KITTI-02 1928/4520, changes correctness label between generations.
- [Export verification](m3/pilot-01/export_validation.json): 48 unique measurement
  IDs, 24 exact selected-generation records, complete causal competitor pools,
  and no identical/reversed physical-pair overlap between partitions. All 24 SC
  margins are available; none shows the old -d1 signature. Old selection files
  were hash-checked after inference and are unchanged.

## Interpretation and limits

The fixed heuristic accepts all 13 safe selected pilot rows and rejects all 11
dangerous selected rows. This is descriptive behavior on deliberately selected
cases, not a population recall/false-accept estimate or proof of zero dangerous
acceptance. The earlier negative results and unsafe labels are not erased.

Pair-group FIT/CALIBRATION/TEST contains 9/10/5 selected rows. Dangerous counts
are 3/5/3. Nearby sites and shared scans can still be correlated across pair groups;
this split only establishes the minimum no-identical-pair boundary. The diagnostic
sequence-level hash partition places all three sequences in calibration for this
fixed seed, leaving fit/test empty. We preserved that result rather than trying
seeds until a favorable split appeared. It is not a usable sequence-holdout study.

No conformal model or per-edge sigma model was fitted, exported or deployed.
F07-F09 remain open for their optional research arms. Five dangerous calibration
pairs cannot substantiate the intended small-error-rate narrative. More appropriate
independent sites and naturally generated candidates are needed before training.

## Executed version versus final source

The pilot used run_id `pilot-01`, registered once in this maintenance record.
Its executed builder and measurement module are copied beside the evidence as
builder_executed.py and measurement_executed.py; provenance.json hashes identify
them. After the pilot, the production builder was hardened to append a UUID to
future run IDs, reject an incomplete/duplicate 24-pair selection, and include more
feature/loader dependencies in source provenance. Generation-ID validation was
tightened and the old main was disabled. These final changes were tested; the GPU
pilot was not misleadingly claimed to have run under the later source hashes.

Both source snapshots are evidence copies, not supported entry points for reruns.
The executable new builder is in RAP-SLAM/scripts; always choose a new output path.

## Handoff and exact next task

Next: add per-measurement logging to the actual offline candidate verifier and
pipeline, preserving every accepted/rejected verification and explicit failures,
all generations, selected IDs, and source_frames.json bindings. Then construct a
predeclared natural candidate cohort across existing core sequences/sites before
fitting any optional statistical gate. Keep the fixed heuristic as the baseline.
This avoids treating a curated 24-pair pilot as the final thesis experiment.

No original experiment output or deployed model was overwritten. M0 snapshot
manifest identity and absence of INCOMPLETE were checked on entry. RAP-main HEAD
4055d92 and RAP-SLAM HEAD 6d3f2d2 remain unchanged; maintenance is uncommitted.
No pull, push, reset, clean or commit was performed. RAP model source is unchanged.
M0 independent-backup limitations remain. Temporary staging copies were removed
after application; final source identities are recorded in m3/final_source_manifest.json.
