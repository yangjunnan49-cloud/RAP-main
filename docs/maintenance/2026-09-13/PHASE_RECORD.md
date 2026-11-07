# Core baseline closure and first optimization outcome

Executed 2026-09-13. This supersedes pending-run and next-step statements in the
2026-09-11 record. Existing full POSS/05/00 artifacts already had reports,
validation and no INCOMPLETE markers; no full frontend was rerun this session.

Ran recompute_m2_metrics.py into legacy-metric-recheck-01, then
consolidate_core_baseline.py into core-baseline-v1 (both under 2026-09-11, as
fixed by the existing helpers). All 18 historical metric rows reproduce earlier
M2 values within absolute tolerance 1e-9. Four fresh runs have exact persisted
source identities and the same candidate ordering as the frozen replay.
Scoped offline baseline closure does not close optional statistical validation.
KITTI 06 and 00 camera translation drift worsen after PGO; preserve both.

Executed the previously declared O1 protocol with run_rap_icp_refinement.py.
The practical screen failed: only KITTI 05 first-pose APE improved. POSS, 06,
and 00 regressed. All 40 refined attempts were accepted and labeled safe.
No production default or algorithm source changed. Saved-log verification
independently rechecked all 40 gate decisions and exact measurement-to-edge
transforms; final_validation.json records this. The runner also checked valid
rotations, finite trajectories and source/input hash stability.

Results: ../2026-09-11/core-baseline-v1/REPORT.md and
../2026-09-11/optimization-o1-01/REPORT.md. Their INCOMPLETE markers are absent.
Timing remains a single warmed run; coarse stage clocks have known accounting
uncertainty. No cold-cache, real-time or generalization claim is made.

Snapshot directory is available, INCOMPLETE absent, central preservation
manifest SHA256 is d9f23fdde6871e4b765d0f76c765035091afdc48e6655d11bf6001fffa41d497.
The entire snapshot was not rehashed. Independent backup, training membership,
unused ROS/Spires and statistical guarantees remain outstanding/deferred.
HEADs remain RAP-main 4055d92 and RAP-SLAM 6d3f2d2; maintenance changes remain
uncommitted and unpushed. Legacy outputs were not modified.

Next: predeclare one budget-12 versus budget-40 comparison across all four fresh
frozen frontends, fixed seed/settings/gate/backend, no sequence-specific tuning.
Regenerate retrieval and RAP measurements in exclusive new directories. Report
candidate coverage, labels, APE, camera drift and additional runtime, retaining
negative results. Do not resume general auditing or S2-S5 without new evidence.

Both worktree whitespace checks passed after removing a trailing blank line.

## O2 completed: budget 12 versus 40

The owner requested continuing. O2_BUDGET_PROTOCOL.md was saved before execution.
New run_budget_comparison.py reused production components without source changes,
with persisted fresh frontend IDs and newly generated budget-12/40 measurements.
Outputs: [O2 report](optimization-o2-01/REPORT.md), summary.json, per-arm events,
metrics and validation; outer INCOMPLETE is absent. Model startup and descriptors
are shared, with separate monotonic timing. Both arms reset seed 42.

| Sequence | Budget 12 APE m | Budget 40 APE m | Effect |
|---|---:|---:|---|
| POSS | 1.822264 | 1.822264 | Only four candidates; unchanged |
| KITTI 06 | 2.446184 | 2.558393 | Worse |
| KITTI 05 | 3.417117 | 3.487993 | Worse |
| KITTI 00 | 11.432936 | 10.931019 | Better |

The predeclared development screen failed. Production remains budget 12.
KITTI camera translation drift: 06 0.667058 -> 0.672608%, 05 0.703737 ->
0.729551%, 00 0.914171 -> 0.913275%. KITTI verification costs rose from
16.9-18.0 s to 56.3-57.4 s; this excludes shared loading/descriptors and PGO.
All 164 attempts were accepted and GT-labeled safe. No dangerous/rejected
examples were created; risk calibration remains unsupported.

Validation checked every attempt/generation, gate, rotation and exact edge
association, finite saved trajectories, and evaluation from saved trajectory
files. All 1428 tracked source/input hashes were rechecked after execution;
used scans and shared algorithm/checkpoint sources also match the full-run
manifests. No production or legacy files changed.

Saved-output analysis via analyze_budget_comparison.py records
coverage_validation.json. Budget-12 candidate orders match all original full
runs; first-pose APE differs by at most 6.65e-7 m. All 40 shared-pair transforms
are exactly equal between budgets. No SC-only candidate enters either arm:
all selected pairs belong to the priority proximity list. This is a measured
selection limitation, not proof that an alternative will improve trajectories.

Next: predeclare a source-balanced fixed-budget-12 comparison on the same four
frontends, with deterministic proximity/SC quota, deduplication and backfill.
Fix the policy before inference; no GT selection or sequence-specific tuning.
Compare against O2 budget 12 and report candidate source coverage, APE, drift,
acceptance and cost. Do not adopt budget 40 or resume broad audits/statistical
arms based on this result.

Git HEADs remain 4055d92 / 6d3f2d2. Changes are uncommitted and unpushed.
Preservation directory/marker and central manifest were rechecked as above;
independent backup is still outstanding. M0-M5 is not universally complete.

## O3 completed: source allocation and bounded diagnostic

O3_SOURCE_PROTOCOL.md was fixed before inference. The runner passed six selector
checks, regenerated proposer lists exactly matching O2, and performed 40 fresh
RAP attempts. All were accepted/safe. Gates, rigid transforms, exact measurement
associations, finite saved trajectories and 1441 source/input hashes passed.
optimization-o3-01 has no INCOMPLETE marker. source_allocation.py,
run_source_comparison.py and diagnose_source_comparison.py are maintenance helpers;
production source/defaults and legacy artifacts remain unchanged.

Balanced 6+6 versus O2 first-pose APE: POSS unchanged at 1.822264 m; KITTI 06
2.446184 -> 2.533434; KITTI 05 3.417117 -> 3.214084; KITTI 00 11.432936 ->
10.336943. The screen failed (two improvements, not three). Six SC slots per
KITTI sequence introduce 4/4/6 pairs outside top-12 proximity. POSS has no added
pairs. Retain secondary metric tradeoffs, especially KITTI 05 aligned APE and
camera drift regressions. Full results are in optimization-o3-01/REPORT.md.

Saved-output analysis independently reproduces selection and allocation. Common
measurements change slightly in 06/05 when ordering changes. A separately declared
post-hoc diagnostic (O3_DIAGNOSTIC_PROTOCOL.md, diagnose_common_edges.py) reuses
exact O2 common edges and O3 new edges. APE 1.822264 / 2.535805 / 3.213732 /
10.336943 preserves the observed direction; see o3-common-fixed-01/REPORT.md.
This diagnostic is not the predeclared O3 arm or a new deployment policy.
Original O3 protocol bytes match its run hash; diagnostic protocol is separate.

OPTIMIZATION_SYNTHESIS.md consolidates O1-O3 without per-sequence winner picking.
Next: predeclare and run the matched identity/odometry ICP comparator on the exact
O3 selected pairs with fixed preprocessing/gate/backend. This closes the registrar
comparison for newly admitted candidates rather than launching a quota sweep.
No generalization or statistical coverage claims; M0-M5 remains partly open.

Git HEADs remain 4055d92 / 6d3f2d2. All maintenance work is uncommitted/unpushed.
Preservation marker/manifest were checked; independent backup remains outstanding.

## O3 matched comparator and thesis evidence tables completed

O3_COMPARATOR_PROTOCOL.md was declared before execution. run_o3_comparator.py
ran identity and odometry-initialized ICP on all 40 exact O3 candidate pairs,
using unchanged preprocessing, ICP parameters, geometric gates and backend.
Outputs: o3-comparator-01; INCOMPLETE absent. Production source/defaults and
legacy products were not changed. This run imports the existing SLAM modules.

| Sequence | RAP first APE m | Identity ICP | Odometry ICP |
|---|---:|---:|---:|
| POSS | 1.822264 | 1.857711 | 1.912702 |
| KITTI 06 | 2.533434 | 2.576697 | 2.581416 |
| KITTI 05 | 3.214084 | 3.179688 | 3.137198 |
| KITTI 00 | 10.336943 | 10.512414 | 10.567533 |

Identity accepts 36/40, with three dangerous KITTI 05 results and one dangerous
KITTI 00 result rejected. Odometry ICP accepts 40/40 safe. All 80 attempts
completed. All 76 accepted edges are safe. Lower first-pose APE does not imply
lower aligned APE or camera drift: full tables retain those counterexamples.
No general superiority claim or automatic default change follows.

Validation: known-transform direction check; 134 input/source hashes rechecked;
used scans and shared sources verified against O3; separate persisted-output
validator checks exact candidate order, initial transforms, source IDs, labels,
gates and all 76 measurement-edge associations, then recomputes saved trajectory
metrics. See validation.json and association_validation.json. No GPU RAP or
frontend rerun was necessary for this comparator.

consolidate_paper_evidence.py creates paper-evidence-v2/RESULTS.md and registry.json,
with default full-run tables, all O3 registrar secondary metrics, admissible thesis
claims and evidence links. This is a retrospective reporting consolidation, not
a new preregistration. O1-O3 remain mixed-result ablations; default budget 12,
heuristic RAP and relfloor+Huber remain unchanged.

Next: draft the thesis results section from paper-evidence-v2, separating main
full-system evidence, ablations and the O3 matched comparator. Preserve sequence
and metric tradeoffs; do not start more quota/threshold sweeps without a concrete
unresolved question. Optional statistics and ROS/Spires remain deferred.

Git HEADs remain RAP-main 4055d92 / RAP-SLAM 6d3f2d2. No commits or pushes.
Preservation directory exists, INCOMPLETE absent, central manifest hash remains
d9f23fdde6871e4b765d0f76c765035091afdc48e6655d11bf6001fffa41d497. The whole
snapshot was not rehashed and independent backup is still outstanding.

## Experimental-results chapter drafted

The owner requested continuing. Created paper-evidence-v2/EXPERIMENTAL_RESULTS_DRAFT.md
in English: evaluation scope/settings, explicit source ranges, default results,
O1-O3 ablations, post-hoc diagnostic, matched O3 ICP, costs and limitations.
The prose distinguishes evidence from interpretation and preserves secondary
metric regressions. Tables remain per-sequence; no selected per-sequence winners,
statistical guarantees or unverified domain-generalization claims were added.

Inspected E:/githouse/RAP-SLAM-report/paper/main.tex (an older Chinese outline).
No external report file was edited. MANUSCRIPT_INTEGRATION.md identifies sections
that need revision, including broad online/zero-error/generalization statements,
legacy metrics and expected targets. The chapter is a Markdown draft, not a
compiled manuscript. Formal method/dataset citation review remains pending.

Validation: 12 complete numeric rows in Tables 2-4 were generated independently
from saved baseline/O1/O2/O3/comparator JSON and matched the draft at six-decimal
precision. Nine local evidence links resolve; draft_validation.json stores the
chapter hash and check scope. Source ranges/keyframes were checked against the
full-run records. Both worktree whitespace checks passed. No experiments rerun,
production changes, commits or pushes; HEADs remain 4055d92 / 6d3f2d2.

Next: draft a source-verified methods section for the actual offline default,
covering transform direction, preprocessing/retrieval, measurement gates, graph
factors and metric frames. Then integrate methods/results and verify bibliography.
No parameter sweep is scheduled. Independent backup, training membership and
optional statistical/ROS/Spires work remain outstanding as previously recorded.
