# F2-V1: structured generation development screen — DRAFT

2026-09-27. Owner requested direction advice and a protocol, not execution.
NOT approved, implemented, execution-frozen or run. After approval, freeze
PROTOCOL.md, source, all inputs and comparator dependencies before outcomes.

## 1. Recommendation and question

Prioritize one question: does causal within-visit motion coupling at EVERY
RAP generation step improve executable cross-visit poses beyond native
multiview, final-only projection and matched-point pooling?

F1 establishes executability only. E1 found no eligible backend successor;
it did not establish why trajectory ATE trails the comparator. Keep E0
development_baseline_v2 fixed and defer further backend/frontend tuning.
This screen must demonstrate better selected poses AND more correct accepted
loops; oracle improvement alone cannot pass. It does not measure system ATE.
No training, new gate, soft-constraint search or automatic PG-route rescue.

## 2. Exact membership and exposure

Repository-relative parent paths:

- 00: docs/maintenance/2026-09-14/hl-v2/data-expansion-01/
  discovery_inputs.json and discovery_evaluator.json.
- 08: docs/maintenance/2026-09-14/support-control-01/data/
  confirmation_inputs.json and confirmation_evaluator.json.

Use all100 pairs from EACH parent in saved order, including the original
four support IDs per pair. cohort_proposal.json beside this draft records
every ID, source SHA256 and seed. It is an inherited membership inventory,
not raw-data verification or an execution freeze. Reverify parents against
the archived PG-DEV execution_freeze.json before execution.

Each sequence has25 pairs in each inherited stratum: confuser,
ambiguous_positive, low_overlap, ordinary. The latter75 are the positive
denominator. Keep membership/strata even if correction changes overlap;
report them as historical strata. No reclassification or replacement.
00 has HL/SC/PG/E0/F1 exposure;08 has SC/PG exposure. BOTH are development.
The four F1 pairs had engineering exposure without loop-accuracy evaluation.
Shared scans/sites invalidate independent-pair claims. No significance claim.

Freeze both memberships before output. Run/validate/freeze00 before08 without
changing methods. Complete both even after a valid scientific negative on00;
only correctness, missing data or resources cause early termination.

## 3. Corrected input and causal local motion

Apply KITTI0.205-degree correction exactly once. This is a point correction,
not a global pose rotation; leave GT/calibration coordinate conventions intact.
Filter original-scan range>=1.5m. Preserve F1 voxel0.4m, outlier20/2.5 and
cap seed42. No extra range/voxel tuning. Six parts ordered
[i,is1,is2,j,js1,js2], counts[2000,1000,1000,2000,1000,1000]. Shortage stops
preparation as INCONCLUSIVE_DATA; never duplicate or relax allocations.

Retain saved past support IDs/timestamps (<=5s), but recompute
L=inv(T_odom(anchor))*T_odom(support) from corrected causal LiDAR odometry.
00 inherits hash-verified E0 full-00-A/odom_poses.txt.08 gets ONE causal full
odometry pass: E0-A max80/min1.5/voxel0.8, no deskew or loop closure. Freeze
its artifact before RAP; no08 trajectory evaluation to select configuration.
Do not reselect supports by their new traveled distance. Record this distinction.
Runner receives local L only, never world poses, cross-visit odometry, GNSS,
GT or historical error fields. GT stays in a separate evaluator.

All hypotheses are new corrected-input generations. Uncorrected old banks
are historical, not arm controls. Freeze retained point identities/arrays,
features, normalization, raw scan hashes, local motion and dependencies.

## 4. Fixed methods and inference budget

Frozen RAP12/miniSpinNet, no fine tuning; neural FP16, protected IEEE rigid
fits, five Euler steps and K4 for A/N/S/P. F reuses N.

| Arm | Definition | Points per generation |
|---|---|---:|
| A | Anchor-only; identical retained anchor points/features |4000|
| N | Native six-part; decode RAW final per-part fits |8000|
| F | N with group projection of RAW final endpoint only |8000|
| S | Group projection of RAW clean endpoints at EVERY step |8000|
| P | Two pooled parts, same six retained scans transported by L, reused descriptors |8000|
| A-ICP | Fixed ICP refinement of selected A-R4 pose |same anchors|
| KM-A | KISS-Matcher on retained anchors |4000|
| KM-P | KISS-Matcher on identical transported P points |8000|

N/F/S share exact points/features/normalization/noise. S decodes final group
poses; also save raw final pose as diagnostic, not another candidate arm.
P uses its own normalization and two partitions; it is not a pure attention
ablation. A is not equal-data/equal-compute. F standalone cost includes N.

Seed=27000000+100000*s+10*p+g for integer sequence s, zero-based saved pair
index p, generation g=0..3. Enumerate before execution. N/S/P share ordered
8000x3 Gaussian noise; A takes matching anchor slices. Request-local RNG and
precision restoration required. No outcome-based arm order or seed changes.

A-ICP: Open3D point-to-point, no scale; source j, target i, initialized by
A-R4 mapping j into i. Same retained2000-point anchors; max correspondence
1.0m, max30 iterations, relative fitness/RMSE tolerance1e-6. One refinement
of the selected pose, no retry/fallback. Invalid input/output stays invalid.

KM-A/KM-P: official Python KISSMatcherConfig(0.4), source j, target i,
estimate without initializer, augmentation or ICP; one call per pair/arm.
All other defaults explicitly dumped and frozen before outcomes. Returned
valid pose gets the common gate; native inlier counts are diagnostics, not
an extra rejection threshold. Freeze release/commit, source/wheel hashes and
native dependencies in preparation. They are not installed in this turn.
Mandatory comparator: if setup fails, stop before RAP outcomes; no silent
omission. Isolated setup cap2 wall hours/2GiB public package-source downloads.

## 5. Selection and common gate

For every RAW clean endpoint, fit each INPUT PART independently using official
Procrustes, compute official point-weighted rigidity RMSE in meters
(average_per_part=False), then average the five steps. R4 selects the smallest
finite score among valid final transforms; lower generation breaks ties.
Same score function within each arm; absolute scores are not compared across
representations. F inherits N scores. S score is BEFORE group projection:
forced-zero projected residual is neither confidence nor a ranking feature.
No gate-based reranking, learned/support selector or GT selection.

Freeze score source and independently crosscheck with NumPy. Save all4 poses,
scores, raw/projected final endpoints and per-step raw data needed to
reconstruct scores, normalization, L and precision/RNG identities. Full noisy
state traces are only mandatory on the fixed engineering subset.

All methods use the SAME corrected, seed42, independently frozen anchor-only
evaluation clouds, each capped4000 with existing preprocessing. These differ
from generation2000-point anchors. Use existing symmetric NN overlap with
strict distance<1m, mean symmetric NN distance over ALL points; accept iff
overlap>=0.7 AND mean_dist<=2.5m. Invalid rejects. No pooled-cloud gate.

Report K1(g0), R4 and GT-only oracle4 for A/N/F/S/P; only R4 is executable
decision evidence. Oracle minimizes max(RTE/1m,RRE/5deg), ties lower g.
Do not impose PG's oracle-headroom gate or substitute oracle for failed R4.

## 6. Outcomes and prospective decision

Use existing transform_label inverse/error semantics, independently checked
with noncommuting synthetic transforms. Strict success: RTE<=1m AND RRE<=5deg.
Legacy5m/10deg labels are separate. Positive clipped error:
min(5,max(RTE/1m,RRE/5deg)); invalid/missing=5 and strict failure, retained in
denominators. Deterministic invalid predictions count as failures; corrupt
I/O, implementation failure or OOM are INCONCLUSIVE, not scientific negatives.
Report all strata, per-pair transitions, correct accepts, wrong accepts,
confuser accepts and positive selected success/error, including rejected poses.

DEVELOPMENT_SIGNAL requires ALL conditions on EACH sequence separately:

1. S-R4 strict positive successes exceed EACH of A-R4/N-R4/F-R4/P-R4 by
   >=3 of75 (4 percentage points). A practical margin, not a significance test.
2. S mean positive clipped error <=0.95 times EACH of those four controls.
3. S correct accepted positives exceed EACH control by >=2 of75.
4. Against EACH control, zero newly wrong accepted pairs over all100;
   ordinary strict-success and correct-accept counts are no lower.
5. Against EACH of A-ICP/KM-A/KM-P, S has no lower positive strict count or
   correct-accept count, no greater positive mean clipped error, total wrong
   accepts or confuser accepts. This is competitive screening, not SOTA proof.
6. Standalone full-cohort S-R4 wall <=1.25 times EACH of N-R4/F-R4/P-R4.
   A/ICP/KM costs reported without claiming matched computation.

Valid complete failure of any gate => NO_DEVELOPMENT_SIGNAL. Report separate
mechanism, acceptance, comparator and cost gates. Do not pool away one failed
sequence, select best post-hoc arm, retune seeds/strength or train a selector.
Data/correctness/resource failure => INCONCLUSIVE with reason. Better oracle
or selected poses without useful accepted loops cannot pass.

## 7. Cost and sensitivity

Whole-cohort standalone timing includes raw read/filter, feature extraction,
normalization, K4 sampling, decoding/selection and common gate; model load
reported separately. Compute shared preparation once if useful, but charge
it IN FULL to each arm requiring it. Save a timing ledger. P adds transport,
F includes N inference, A charges only anchors, A-ICP adds refinement and final
gate; KM charges actual preprocessing/matching without unused neural features.
Synchronize GPU boundaries. Rotate [A,N,S,P] order by pair index mod4; F
postprocesses N. Warm OS cache disclosed. Report total, median/p90 and memory.
No timing superiority from only a favorable small sample.

Engineering subset: first saved pair per stratum per sequence (8 total).
Main K4 outputs remain in the cohort. Compare N-g0 to official native sampler
and replay S-g0 after intervening arms; max endpoint/state delta<=1e-6.
Check RNG/precision restoration on success and injected exception; no hooks.

Sensitivity on those8 pairs: F1 support-only left-composed (+0.10m x,+1degree
yaw) and (-0.10m x,-1degree yaw), all4 seeds with unchanged points/noise.
Report pose shifts, errors, strict/gate transitions; no strength selection or
robustness claim. Descriptive sensitivity does not replace failed main gates.
Evaluator-only local-motion GT errors are computed after output freeze.

F1 tolerances: finite tensors, SO3 orthogonality/determinant<=1e-5,
normalization roundtrip<=1e-4m, group residual<=1e-4; independent float64
projected-point disagreement<=1e-4 normalized and decoded-pose delta<=1e-3.
Separate validator reconstructs every score/selection, label, gate and decision,
audits correction exactly-once, causality, frame direction and all identities.
Parent/raw/model/source hashes checked before and after. Zero enforced group
residual is not registration evidence.

## 8. Stages, caps and subsequent boundary

F2.0 AFTER APPROVAL: parent/raw verification, isolated comparator installation,
synthetic direction checks, corrected08 odometry, fixed points/motions/seeds,
CPU geometry tests, then source/input/protocol execution freeze. No GT labels
loaded by generation. Preserve all completed E0/E1/F1 and old bank directories.
F2.1: full00 generation, evaluation/validation, report and hash freeze.
F2.2: unchanged08 generation and final independent checks/decision.

Caps: one RTX5070,12GiB peak allocated,2 GPU-process wall hours including
model loading/preprocessing,20GiB artifacts,30 CPU wall minutes for08 odometry
and60 CPU wall minutes for matching/evaluation. Stage watchdogs; no concurrent
GPU task. Limits are ceilings, not predicted runtimes. No dataset download.
Maximum network sampling calls:3200 main (200x4 A/N/S/P xK4),64 sensitivity,
8 native checks,8 S replays =3280. F adds800 projections, not inference calls.
KM400 calls, ICP200 refinements. No unlisted warmups; first timed calls count.

Exclusive outputs, INCOMPLETE until validation passes, preserve failed attempts.
Post-freeze correctness fixes need named amendments; no silent overwrite or
threshold change. Deliver REPORT, per-pair records/transitions, timing ledger,
decision/validation JSON and artifact hashes. No production edit or Git sync.

If positive, propose a SEPARATE fixed-frontend/backend system-integration and
fresh-confirmation protocol: full retrieval, accepted-edge impact and ATE/ter.
No automatic execution. Pair results alone cannot demonstrate system gains.
Fresh membership requires exposure audit; previously screened KITTI data are
not unseen. Boreas is an option, not an automatic download/data-adequacy claim.
If negative, stop this exact mechanism and discuss a distinct hypothesis;
do not abandon the owner's broader breakthrough requirement. Manuscript and
HL/SC/PG stops persist.

## 9. Primary-source boundary, checked2026-09-27

- [RAP](https://arxiv.org/html/2512.01850v1): multiview generation/rigid recovery
  are established components; native multiview alone is not the contribution.
- [FUSER authors](https://github.com/Jiang-HB/FUSER): joint multiview prediction
  and SE(3)^N diffusion refinement are existing related approaches.
- [KISS-Matcher authors](https://github.com/MIT-SPARK/KISS-Matcher) and
  [API example](https://github.com/MIT-SPARK/KISS-Matcher/blob/main/python/examples/run_kiss_matcher.py)
  provide an external registration comparator with an explicit resolution.

This focused review is not exhaustive novelty clearance. Potential distinction:
causal within-visit coupling DURING generation while retaining scan partitions.
The group rigid fit itself is pooled least squares and not novel. A closer
paper/code audit is necessary before a larger campaign or novelty claim.

## 10. Decision requested

Recommend commissioning this ONE bounded F2 screen with mandatory comparators
and corrected-motion preparation. Drafting approval is not execution approval.
Release/commit/source hashes remain preparation deliverables, not unspecified
tuning freedoms. Any outcome-driven change of methods, cohort, score, gates,
resolution, margins or budget requires a different prospective protocol.
