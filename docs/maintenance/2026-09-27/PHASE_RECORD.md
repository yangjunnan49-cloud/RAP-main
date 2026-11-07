# 2026-09-27 phase record

Owner requested continuation of approved E0 then F1. Read current handoff and
actual files. Original exec session90056 no longer exists; a WSL process check
shows no remaining experiment. KITTI00 O/A/B/C have complete saved outputs;
KITTI05-O is an empty interrupted directory. Termination cause/time unknown.

E0 administrative [resume annex](../2026-09-26/e0-frontend-01/RESUME_ANNEX_01.md)
preserves original protocol/runner/freeze and completed outputs. Reverify all
inputs, re-evaluate inherited00 cells, freeze continuation/validator identities,
then run only remaining05/06 cells in resume-01 and the selected full-system
arm. No arm/selection rule change or claim of new independent evidence.
New maintenance helper: scripts/maintenance/resume_e0_frontend.py.

F1 source/input freeze and successful synthetic geometry checks already exist.
No F1 model output yet. Wait for E0 generation to complete before its bounded
GPU preflight. No F2 execution or manuscript restart. Branches and dirty work
preserved, no Git sync.

## E0 finalization and F1 execution (owner: "立即启动")

E0 finalization: the frozen validator stopped on its unanchored NumPy ATE
crosscheck (float64 gauge conditioning, delta 5.83e-7 vs tolerance 1e-8;
frozen-code recomputation matched saved metrics exactly, anchored crosscheck
agrees to 4.4e-12). Recorded as named E0-AMENDMENT_01 in the E0 directory;
amended copy validate_e0_frontend_v2.py anchors both trajectories before the
crosscheck, tolerance unchanged, original frozen validator untouched. The
amended validator passed all 15 checks: 64 frozen sources rehashed, 12 cells
(exact IDs, finite SE(3), metric recomputation <1e-9, independent ATE
crosscheck), O baseline reproduction <=1e-5, selection arithmetic matched
selection.json exactly, full-run frame/source binding, measurement/edge
identity and GT-label diagnostics, 20GiB output cap. Decision
FREEZE_DEVELOPMENT_SUCCESSOR arm A; development_baseline_v2.json frozen;
REPORT.md/results.png/artifact_hashes.json written; INCOMPLETE removed. The
resumed process had already re-verified all 8421 raw inputs post-execution.
Runtime accounting: inherited 00 cells 550.267s plus resumed process 827.091s
within the 5400s resumed allowance (1800s reserved for the interrupted
process); full-system phase 461.2s within its 1800s cap.

F1 execution: the first detached launch was killed by WSL session teardown
before any file was created (no attempt directory, nothing to preserve);
relaunched under setsid, the standard detach. attempt-01 completed in 24.943s
process wall, peak allocated 2.418GiB (cap 12GiB), four pairs x five arms plus
replay and two sensitivity perturbations. Native reproduction delta exactly 0
on all four pairs; reordered S replay delta <=1e-6; RNG/precision state
restored including the injected-exception path; GT never loaded by the runner.
Independent float64 NumPy audit passed (PASS_ENGINEERING): projected-point
delta 4.79e-7, decoded-pose delta 4.37e-6, constraint residual 4.37e-10.
finalize_f1_structured.py wrote REPORT.md, sensitivity.json and
final_artifact_hashes.json; attempt-01/INCOMPLETE removed. Evaluator-only
local-motion diagnostic over 16 supports: max translation 0.098383m, max
rotation 0.339194deg. No efficacy claim; no F2 protocol or execution.

Next: owner decision on commissioning a separately frozen F2 development
protocol. No Git sync; branches and dirty work unchanged.

## E1 backend review protocol drafted (owner: "直接开始" on the drafting offer)

Owner asked whether current work is on the metric-improvement path; answer
given: E0 already improved measured system metrics (engineering, not the
novel architecture part), ter now at/past the measured KISS-SLAM comparator
on 00/05/06 while ATE still lags (2.754/1.295 vs 0.917/0.661 on 00/05).
Owner then approved drafting only. Arm basis verified against the installed
kiss_slam 0.0.2 source (identity 6x6 information for all factors, no robust
kernel, MapClosures+ICP+overlap acceptance, 100m local-map nodes, 7/5/4
closures) and our frozen E0 artifacts (relfloor+Huber, NMS=0, 12/12 accepted
with dense clusters, 34/2 strict). Draft at
e1-backend-01/PROTOCOL_DRAFT.md: replay-only PGO on frozen full-*-A artifacts
(no new inference/GPU), fixed arms O/W1(identity)/W2(gnc_tls)/E1(nms w=10),
ATE-primary gates, 30min/1GiB caps, no sweeps, development-only scope.
NOT approved, NOT frozen, NOT executed. Awaiting owner decision on the three
listed decision points. No code written for E1; no experiment state exists.

## E1 authorized, frozen, executed and validated

Owner asked to read AGENTS.md, continue E1 execution and explicitly allowed
draft revisions. This supersedes the preceding pending-approval status.
Preserved draft; PROTOCOL.md retains four arms, NMS10, 5% mean ATE eligibility
and all original regression guards. Clarifications before outcomes: W1 unit
loop sigmas with unchanged odometry is not all-factor equal weighting nor
KISS-SLAM reproduction; ter06 slightly trails KISS; backend causality unknown.
Specified exact GNC/default parameters, GT field stripping, serialized O
reference tolerance and exact repeat, validation details and CPU budget.

New additive maintenance scripts e1_backend.py and validate_e1_backend.py
call existing RAP-SLAM algorithms without production changes. Frozen52 files
include original E0 input hash checks, GT/calibration inherited hash checks,
metric/backend sources, protocol/scripts and package identities. Source ZIP
saved. WSL required a sandbox escalation; approved execution used the existing
environment, CPU only, with external timeouts. No network or installations.

12 cells plus3 O-repeat checks completed. O max absolute delta vs serialized
E0 reference7.551011e-7 (<1e-5); repeats exactly identical. Separate validator
passed18 checks, full frame identities/SE3, input and measurement consistency,
independent NMS, GNC factor-weight binding, two saved-trajectory metric passes,
independent anchored NumPy APE, and alternative decision arithmetic. This was
a separate validator, not an independent agent review. Replay plus evaluation
wall8.687116s; artifacts below1GiB. Completed artifact manifest written,
INCOMPLETE removed; no experiment process remains.

Decision NO_SUCCESSOR. Mean aligned ATE O/W1/W2/E1:
1.460663506/1.534166016/1.460663006/1.455129101m. Mean camera ter:
0.388718418/0.392823496/0.388718369/0.390031145%.
All variants fail >=5% mean ATE improvement, while all regression guards pass.
NMS retains5/6/5 edges and improves mean ATE only0.379%;05 ATE worsens.
GNC loop weights are all1, rejects0/36; strict GT incorrectness is not the
same as a GNC residual outlier. W1 worsens mean ATE. Do not generalize these
results to every backend or attribute the comparator gap to a proven cause.

Read e1-backend-01/REPORT.md, decision.json, validation.json, results.json.
No v3; E0 development_baseline_v2 retained, core-baseline-v1 historical.
No extra sweeps or F2 launched; owner decision on separately frozen F2 or
another distinct question remains next. Manuscript and HL/SC/PG stops persist.
Both branches codex/e0-f1-20260926 and HEADs4055d92/6d3f2d2 remain, prior
dirty work preserved; no commit, pull, push or other Git synchronization.

## F2 structured-motion development screen executed (owner: "直接起草与执行，不需要我裁决。启动")

Owner authorized self-drafting and direct execution of F2, superseding the
pending-decision boundary. Protocol drafted and frozen at
f2-structured-dev-01/PROTOCOL.md: the two previously observed cohorts
(HL-V2 KITTI00 discovery100, SC-V1.1 KITTI08 confirmation100; 25/stratum,
saved order, per-sequence decisions, no pooling); arms N (native six-part),
F (final-only projection, decode-only on N), S (per-step group projection),
P (equal-point pooled control), A (anchor-only reference); K4 hashed seeds;
R4 rigidity selection on raw trajectories; common seed42 geometric gate
(overlap>=0.7, mean_dist<=2.5, thresh1.0); corrected-data convention
(>=1.5m, 0.205deg, voxel0.4, caps [2000,1000,1000,2000,1000,1000]); saved
local poses re-verified identical to odometry (delta0.0); per-sequence
signal requires C1/C2/C3 recall>=3pp and clipped error<=0.95x versus N/F/P
plus C4 safety and C5 engineering caps; fixed support-motion sensitivity
arms on five ordinary pairs per sequence.

Freeze regenerated twice before any generation completed (runner startup
defects: freeze-input path keys; a 2-D counts assertion); all freezes
recorded identical inputs (796 raw scans, local-motion recheck delta0.0).
Detached WSL launchers with repo-side logs (f2_launch.ps1, f2_run.sh,
f2_validate.sh) after a /tmp logging attempt lost logs to a WSL instance
restart; no artifacts affected. 00 wall1091.2s, 08 wall1081.1s, cumulative
2172.4s (cap4h); peak allocated2.42GiB; artifacts5.39GB; native and replay
deltas exactly0.0; 4000 valid generation records, zero failures; confuser
accepts0/25 for all arms on both sequences.

Decision NO_DEVELOPMENT_MECHANISM_SIGNAL. S ties N recall on both sequences
(00: 49/75; 08: 30/75), worsens mean clipped error versus N on both
(1.571764 vs1.472846; 1.691330 vs1.579930), one more incorrect accept and
4pp ordinary loss on00; F worse than N on both; pooled P best00 recall
(54/75) — observed fact, not a selected route. Sensitivity: selected-T
deviation median<=0.10m/<=0.034deg, max<=0.16m/<=0.07deg at the injected
scale. First validation stopped on the frozen validator's group-center
convention defect in its independent decode crosscheck (measured:
3.9543162905113007 group vs6.55e-6 per-part on the failing record);
F2-AMENDMENT_01 recorded, amended copy validate_f2_structured_v2.py passed
all checks (projected1.16e-6, pose1.60e-5, constraint8.88e-8, rigidity
1.45e-5, gates0.0, evaluator rows exact, decision arithmetic independent),
validation.json written, INCOMPLETE markers removed.

Read f2-structured-dev-01/REPORT.md, decision.json, metrics.json,
sensitivity.json, AMENDMENT_01.md, validation.json. Negative decision ends
this route: no gate tuning, arm rescue or support/motion sweep. Not a
general impossibility proof (one sampler configuration, one motion source,
one point budget, two development sequences). Next boundary: owner decision
on retiring the mechanism or a separately scoped question. HL/SC/PG stops
and manuscript pause persist; no production/default change; both HEADs and
dirty work preserved; no Git sync. Completed f2-structured-dev-01 must not
be rerun or overwritten.

## Post-F2 action plan executed (owner: "合理的决策，请做好行动规划后执行")

The owner authorized planning and execution after F2. No F2 completed file
was rerun or overwritten. Wrote `f2-postmortem-01/PLAN.md` and froze its
`PROTOCOL.md`, diagnostic script and F2 saved-result identities before
computing new aggregates. Read-only diagnostic over the exact 00/08 F2
evaluator rows passed a separate 58-check PowerShell recount. Native N's
positive-pair partition (correct accepted / correct rejected / R4 selection
miss / no correct K4 candidate) is 00=23/26/3/23 and 08=17/13/4/41.
08's ten native incorrect accepts have no correct saved candidate; 00's one
does not either. N->P gains/losses are00=7/2 strict but0/0 correct accepts;
08=3/3 strict and1/1 correct accepts. See `f2-postmortem-01/REPORT.md`,
`analysis.json`, `freeze.json`, `validation.json`. These are post-hoc observed
development facts, not a selected route or new gate.

Executed separately frozen `e0-heldout-01/PROTOCOL.md` on complete KITTI
07/09/10, each O/A full system and same-data default KISS-SLAM. These
sequences did not select E0 arm A or have earlier recorded RAP-SLAM full
outcomes, but 07/10 had prior SC data/old-odometry screening and 09 had
PG data screening; not fully unseen or cross-domain. 71 source and3902
input identities froze before trajectories; E0 algorithmic source hashes
matched the original E0 freeze and inputs rehashed after runs. Independent
validator passed9 run groups (exact frames/config, geometry, metrics,
measurement/edge binding, labels), plus28 independent PowerShell arithmetic
and identity checks. Wall548.6s, artifacts408.8MB; no incomplete marker.
Decision HELDOUT_TRANSFER under the declared A-vs-O rule. O/A/KISS mean
camera ter=0.959528/0.505615/0.484556%, mean aligned LiDAR ATE=
1.217655/0.721480/0.764081m. KISS ter is lower on each sequence; A's
mean ATE advantage is driven by09, while KISS ATE is lower on07/10.
For A, accepted strict correct/incorrect loops07=12/0,09=0/10,10=0/0;
09 full ATE improves over A odometry despite strict-inaccurate loop labels,
so strict label is not graph-effect attribution. See `e0-heldout-01/REPORT.md`,
`results.json`, `validation.json`, `decision_crosscheck.json`. No config
selection/default change or broad first-tier claim.

The conditional next mechanism premise was tested under a third frozen,
CPU-only `rap-refinement-feasibility-01/PROTOCOL.md`: fixed point-to-point
ICP from N/R4 on the saved F2 2000-point anchor sets, all100 pairs on each
sequence. Runner byte-hashed frozen GT/evaluator files for integrity but did
not parse/use their contents for pose computation; bank sealed before
evaluator parsing. R0-AMENDMENT_01 records the literal protocol wording
clarification without changing source, bank or outcomes.
Independent validator passed214 checks, wall3.49s, peak RSS0.068GiB.
Decision NO_LOCAL_REFINEMENT_FEASIBILITY_SIGNAL:00 strict49->51/75
(4 gains,2 losses), clipped error1.472846->1.496762;08 strict30->30/75
(no transitions), clipped error1.579930->1.595318. The fixed local ICP
route ends; no accepted-loop/trajectory efficacy was claimed. See
`rap-refinement-feasibility-01/REPORT.md`, `summary.json`, `validation.json`.

Next boundary: a genuinely different candidate-creation question, preceded
by focused primary-source and RAP source audit and separately scoped/frozen
protocol. No S/P/ICP parameter rescue, automatic backend/frontend sweep,
production edit, training, manuscript claim, or Git sync. Both original
HEADs and dirty work were preserved; this phase only added maintenance
scripts/documents/artifacts and updated the handoff.
