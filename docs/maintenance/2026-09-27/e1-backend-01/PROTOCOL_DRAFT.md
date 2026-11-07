# E1-V1 PROTOCOL DRAFT: bounded backend (PGO) review

Status: **DRAFT, 2026-09-27. Not approved, not frozen, not executed.**
Created at the owner's request after the validated E0 result. Execution
requires explicit owner approval, then a hash freeze of this protocol (renamed
PROTOCOL.md), the replay script and all inputs before any run. Nothing in this
document is a measured result.

## 1. Purpose and scope

Engineering-only review of the pose-graph backend on observed development
sequences, targeting the measured ATE gap left by E0. No novelty claim, no
research-contribution claim, no efficacy statement about the RAP generative
verifier. The RAP pipeline, gate thresholds, candidate generation, front-end
configuration and production defaults are all out of scope and unchanged.

Measured basis (validated E0 full-system arm A vs HC-V1 measured KISS-SLAM
0.0.2 defaults, identical sequences):

| Seq | Full ter % ours / KISS | Full aligned ATE m ours / KISS |
|---|---|---|
| 00 | 0.518 / 0.575 | 2.754 / 0.917 |
| 05 | 0.320 / 0.517 | 1.295 / 0.661 |
| 06 | 0.328 / 0.325 | 0.333 / 0.328 |

ter is at or past the comparator on all three sequences; ATE lags on 00/05.
E1 reviews only the backend as the remaining measured difference.

## 2. Verified structural differences (arm justification)

Verified from the installed kiss_slam 0.0.2 package source used by HC-V1 and
from our frozen run artifacts:

1. **Edge trust**: KISS-SLAM adds every factor (odometry and accepted loops)
   with an identity 6x6 information matrix and no robust kernel — accepted
   loops are fully trusted after their strict acceptance. Ours downweights
   loop edges (relfloor: sigma scale clip(mean_dist/1, 1, 3)) and wraps them
   in Huber(k=1).
2. **Edge clustering**: KISS-SLAM measured 7/5/4 closures on 00/05/06, one
   per local map pair (100 m splitting). We accepted 12/12 candidates per
   sequence with dense near-duplicate clusters (00 example: i = 2429, 2433,
   2437 within eight frames, same target region). Our own module history
   documents that NMS width 10 fixes dense-cluster over-weighting on prior
   data; production runs NMS=0.
3. **Strictly incorrect accepts**: 34/2 strict correct/incorrect among the 36
   accepted E0 loops (evaluator-only diagnostic). An outlier-rejecting kernel
   (existing gnc_tls path, default off, previously smoke-tested 2026-09-05)
   is the existing mechanism intended for this.
4. Out of scope here: KISS-SLAM's point-to-plane ICP loop refinement on dense
   local maps and its local-map graph granularity. Changing measurement
   generation or graph granularity requires new mapping passes and is a
   separate proposal (not E1).

## 3. Fixed inputs (no new inference)

Replay PGO on the frozen E0 full-system artifacts only:
full-{00,05,06}-A/{odom_poses.txt, keyframes.json, accepted_loops.json,
verification_measurements.jsonl, summary.json}, hash-verified against the E0
artifact_hashes.json before any optimization. Saved loop measurements (T_rel,
overlap, mean_dist) are reused unchanged. CPU-only; no scans, no GPU, no model
inference, no GT input to any optimization. GT remains evaluator-only.

## 4. Fixed arms (complete set; no sweep, no additions)

- **O**: production backend reproduction (relfloor ref=1 cap=3 + Huber k=1,
  NMS=0). Must reproduce the saved optimized poses within max abs matrix
  delta 1e-5; stop on failure.
- **W1**: loop edges with identity-equivalent diagonal sigmas, robust kernel
  off; odometry edges unchanged. Mirrors the comparator's trust-all-accepted
  weighting.
- **W2**: production relfloor sigmas with the existing gnc_tls kernel path at
  its previously recorded defaults; GNC diagnostics saved per edge.
- **E1**: production weighting/kernel plus existing nms_loop_edges width=10
  edge thinning (value fixed here a priori from documented module history,
  not selected from E1 outcomes).

Odometry edges, node sets, keyframes and measurements are identical across
arms; only loop-edge weighting/kernel/edge-set treatment varies.

## 5. Metrics, gates and decision

Same frozen metric code (eval_paper_metrics) and GT convention as E0;
evaluate replayed optimized trajectories per sequence: unaligned/aligned
LiDAR APE and camera ter/rer.

- Eligibility (all required): mean aligned ATE over 00/05/06 <= 0.95x O;
  mean camera ter <= O + 0.02 percentage points; no sequence ter regression
  >0.05 points; no sequence ATE regression >10%.
- Selection: minimum mean ATE, then minimum mean ter, then alphabetical.
- Decision: FREEZE_DEVELOPMENT_SUCCESSOR_V3 only if all correctness checks
  pass and the selected arm beats development_baseline_v2's recorded full
  means on ATE. Otherwise NO_SUCCESSOR; record and stop.
- One run per arm, no retries to improve results. No threshold, width or
  kernel-parameter search. No eligible arm is not a failure of the process.

## 6. Validation, budget and preservation

- Independent validator script (frozen beside the replay script): input hash
  verification, O double-run determinism check (identical output), geometry
  checks, metric recomputation from saved replay trajectories with an
  independent NumPy crosscheck anchored before alignment (E0-AMENDMENT-01
  lesson), and gate arithmetic recomputation.
- Caps: 30 minutes total CPU wall, 1 GiB artifacts, no network, no GPU.
  Stop on failed correctness, nondeterminism or cap breach; preserve failed
  attempts and freeze; correctness fixes need a named amendment.
- Exclusive directory docs/maintenance/2026-09-27/e1-backend-01; INCOMPLETE
  marker discipline as in E0; artifact hash freeze at completion.
- No production edits, no Git commit or synchronization; branches and dirty
  work preserved.

## 7. Explicit boundaries

00/05/06 are observed development data with prior exposure; E1 outcomes are
development evidence only. No first-tier or SOTA claim from E1 regardless of
outcome; any external claim requires a separately frozen confirmation cohort
with exposure accounting. E1 does not authorize F2 and F2 does not authorize
E1; the research track (structured generation) and this engineering track are
independent decisions. Re-examining front-end arm C (better odometry ATE than
A) is not part of E1 and would need its own protocol. Manuscript remains
paused; all HL/SC/PG stops persist.

## 8. Open decision points for the owner

1. Approve the four-arm set (O / W1 / W2 / E1) as the complete design.
2. Confirm NMS width 10 fixed a priori for arm E1.
3. Confirm the eligibility margins (5% ATE improvement; ter guards).
