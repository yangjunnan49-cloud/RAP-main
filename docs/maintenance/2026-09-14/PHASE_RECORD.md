# Research repositioning record

## Closure pointer: SC-V1.1 complete on 2026-09-15

The subsequent fixed-control experiment is complete with confirmation
NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE; neural expansion remains stopped.
See the [latest phase record](../2026-09-15/PHASE_RECORD.md),
[final report](support-control-02/REPORT.md) and
[completed direction decision](../2026-09-15/RESEARCH_DIRECTION_DECISION.md).
The earlier SC-V1.1-not-started next step below is historical and superseded.

## Current checkpoint: SC-V1 control declaration and SC0 complete

The owner requested reading AGENTS.md and advancing the project. Inspected both
dirty main worktrees and original HEADs4055d92/6d3f2d2; read workspace/root
instructions, HL-V1/V2, final pilot/diagnosis, baseline and literature matrix.
Reverified829 frozen pilot artifacts and3 diagnosis artifacts before reuse.
M0 snapshot exists without INCOMPLETE; manifest hash matches the saved summary.
This does not revalidate archived payload or provide an independent backup.

Declared [SC-V1](support-control-01/PROTOCOL.md) before new labels: isolate the
observation-versus-score confound in B4/S4 with a same-score anchor control A4,
unchanged S4, identical-support pooled P4/P4x2 query-budget controls, official R4,
and GT-motion sensitivity G4 restricted to evaluation. No learned head, score
sweep or new novelty claim. No scorer implementation or outcomes yet.

Executed the fixed data-only order: discovery07 then10; confirmation08 reached
headroom so09 was not audited. Read/hash/finite-checked6,373 raw scans and built
fresh KISS-ICP frontends. Candidate totals4,399 discovery /11,545 confirmation.
Independent union/support/stratum/per-sequence selection and bounded brute-force
overlap checks passed; pooled role selection was independently reconstructed.

| Role | Sequences | Confuser | Ambiguous | Low overlap | Ordinary | Total | Adequate |
|---|---|---:|---:|---:|---:|---:|---|
| Discovery | 07+10 | 25 | 3 | 17 | 0 | 45 | No |
| Confirmation | 08 | 25 | 25 | 25 | 25 | 100 | Yes |

Decision: **SC0 INCONCLUSIVE_DATA; SC1 not started**. Discovery has only3/9
supported ambiguous/ordinary pairs even before query-cap exclusions. Preserve
the shortage as a cohort failure, not a scientific failure of support evidence.
Both exact memberships are [hash-frozen](support-control-01/data/cohort_freeze.json)
before any new scores;08's adequate membership is available for a future annex.
Data wall365.566s; no RAP inference/training, downloads, new external data or
identity submissions. Public-download authorization, NCLT external and writing
pause remain. Data artifact51 hashes, original829+3 hashes, source/protocol and
metadata stability checks passed at closure. Raw data were not rehashed at closure.
See [report](support-control-01/REPORT.md) and [validation](support-control-01/validation.json).

Only maintenance orchestration helpers, protocol, artifacts and handoff documents
were added in RAP-main; existing SLAM data helpers were reused read-only. Original
dirty work, algorithms, model and production defaults are unchanged. No commit,
push, pull, reset or cleanup. Sandbox WSL denial was resolved by scoped approved
execution; no unresolved execution failure or running job remains.

Exact next task: prospective SC-V1.1 data-role annex, using already observed
HL-V2 KITTI00 as development discovery and preserving exactly frozen KITTI08
confirmation. Explicitly bind inherited00 bank/seeds and fresh08 seeds, retain
the fixed controls/scores/gates, freeze before new scores, then implement and
validate in RAP-SLAM. Discovery report must precede confirmation outcomes.
No resampling08 or pretending00/02 are unseen. Additional raw data are unnecessary
for this proposed amendment. SC-V1.1 is not yet declared/executed; SC-V1's data
stop remains a separate result. Neural expansion remains stopped, including
after any future mechanism-only signal. Do not rerun completed SC0 directories.

## Documentation-only fresh-conversation handoff

The owner requested that new work begin in the next conversation to prevent
context degradation. Updated AGENTS.md with an ordered reading list, the exact
confirmation stop decision, completed output locations, helper entry points,
and the next-task boundary. Removed obsolete active instructions to start the
already completed data expansion; original HL-V1 evidence remains historical.
No new research protocol, cohort, experiment, download or training was started
in this handoff turn. No background experiment remains from the completed pilot.
Next conversation should begin with the bounded support-evidence question and
prospective controls described in AGENTS.md, keeping neural expansion stopped.
Only continuity documentation changed; no Git synchronization was performed.

## Current checkpoint: HL-V2 complete, STOP_NEURAL_EXPANSION

The owner authorized autonomous public downloads and avoiding preventable sample
shortages. Froze HL_V2_DATA_EXPANSION_ANNEX.md before new labels/inference:
broader real proposals and causal raw supports, unchanged strict labels/gates.
Original HL-V1 INCONCLUSIVE preserved. Verified9,202 scans;15,064/16,660 candidates;
selected100/100 with25 per stratum. Independent checks and fixed visual review
passed; no membership filtering. Both role manifests frozen before outcomes.
MulRan form requires identity, requested asynchronously; no submission. Local
data suffice, so no extra raw download was necessary. NCLT remains external.

New10-pair preflight:40 valid hypotheses/support scores,40.891s synchronized
pair wall, peak allocated4.457GiB/reserved8.998GiB. Reordered and observed-versus-
original sampler deltas exactly0. Instance observer uses unchanged RAP functions
for official mean per-step rigidity RMSE. No upstream source/default edits.
Both 100-pair K4 banks completed with 400 valid hypotheses and support scores
each. Discovery results were independently checked and hash-frozen before
confirmation inference. Independent checks passed 500 selections per role;
all 800 seeds, transforms, support combinations and hashes passed final audit.
Completed markers cleared. No active experiment or training remains.

| Role | B4/S4/R4/OR4 strict success out of 75 | Oracle recall gain | Oracle error reduction | S4 gap recovery | H1 | H2 |
|---|---|---:|---:|---:|---|---|
| Discovery 00 | 52 / 54 / 53 / 57 | 6.67 pp | 15.0978% | 40.00% recall | PASS | PASS |
| Confirmation 02 | 26 / 25 / 27 / 29 | 4.00 pp | 19.8248% | -1.0631% clipped error | PASS | FAIL |

Both adequacy checks passed, with 18/29 discrepant positive pairs. Confirmation
governs: **STOP_NEURAL_EXPANSION**. Ordinary recall loss is zero and S4 introduces
no newly incorrect accepted pair, but it fails the required 25% gap recovery.
Full bank wall times were 390.496/527.545 s; both peak allocated/reserved
4.457/8.998 GiB. These include preprocessing, inference, scoring and writes,
not just active GPU compute. See [complete report](hl-v2/pilot-01/REPORT.md).

Continued with a separate [post-hoc diagnosis](hl-v2/diagnostic-01/REPORT.md),
without changing any hypothesis, score, gate or decision. Confirmation low-
overlap contributes +1.262892 summed clipped error (S4 minus B4), offsetting
ambiguous/ordinary improvements; ambiguous positives lose one strict success.
S4's 26 incorrect accepts are 6 ambiguous, 8 low-overlap and 12 ordinary; four
also fail legacy 5m/10deg correctness. No confuser is accepted. These are
case-control counts, not a deployment prevalence estimate. Local support-motion
translation median/p90/max is 0.0529/0.1450/0.4058 m; rotation
0.0925/0.2012/2.7831 deg. This bounds errors but does not prove their causal role.
Both roles are now development data; their frozen pilot artifacts remain intact.

Added scoped RAP-SLAM bank/evaluator/independent-validation helpers and RAP-main
maintenance finalization, plotting and post-hoc analysis helpers. Original
HEADs 4055d92 / 6d3f2d2 and existing dirty work remain; no commit, push, pull,
reset, cleanup or production/upstream change. Scoped execution approvals
succeeded; there is no unresolved execution failure in this checkpoint.

Exact next step: neural expansion remains stopped. Formulate a bounded new
support-evidence question, including official R4 and equal-data/compute controls,
and freeze its protocol and fresh confirmation cohort before generating new
outcomes. Do not silently tune the scoring rule or reuse 00/02 as unseen evidence.
Public-download authorization persists; no new raw download was needed to obtain
this adequate pilot. MulRan identity request remains unanswered, not a blocker
to the completed result. NCLT external role and manuscript pause remain.

## Historical checkpoint: HL1 data adequacy INCONCLUSIVE

The owner requested continuation after HL0. Executed the fixed HL1 candidate and
stratum audit in [pilot-01](hl-v1/pilot-01/REPORT.md), with exclusive creation.
The sample-size gate fails on both sequences; H1/H2 are NOT EVALUATED. No RAP
hypotheses, selector comparisons or training ran in this turn. HL0 PASS stands.

| Sequence | Candidate union | Supported | Selected confuser/ambiguous/low/ordinary | Decision |
|---|---:|---:|---|---|
| 05 discovery | 457 | 25 | 1 / 0 / 0 / 15 | INCONCLUSIVE |
| 06 data confirmation | 445 | 0 | 0 / 0 / 0 / 0 | INCONCLUSIVE |

05 pre-support strata: 8 confusers, 0 ambiguous positives, 1 low overlap and
422 ordinary, plus 26 overlap-gap pairs. 06 has 445 ordinary only. Thus changing
support alone cannot supply the required >=10 pairs per hard stratum; total
selected minima >=60 also fail. No synthetic fill, threshold relaxation or
outcome-dependent replacement. The hypothesis is not scientifically falsified.

Built the complete per-query expanded ring shortlist20 and SC<=.25/top20 plus
proximity<=30m/top5 union with separation200. Stored all temporal-eligible
ring/proximity distances, shortlisted SC distances/ranks, source membership,
GT-only labels, support metadata and exact priority/hash/quota/query-cap reasons.
Generation inputs exclude GT/strata. Every used scan hash was verified against
HL0 before construction and rechecked after labelling; parent metadata is stable.

Independent checks reconstruct candidate unions, causal support and sampling;
scalar-versus-batched SC max differences 2.30e-8/2.35e-8. Four visual examples
across both sequences have exact overlap agreement with independent chunked
brute-force distances. Inspected figures; no membership changed. The 05 report,
visual record and artifacts were hash-frozen before the 06 data audit. No
confirmation model outcomes exist. CPU construction/label wall times 17.847s
and 10.580s; RAP GPU time0. Independent validation/documentation are outside
those timings; human labour was not independently instrumented.

Added only `RAP-SLAM/scripts/hl1_cohort_audit.py` and `validate_hl1_cohort.py`,
plus maintenance artifacts/documents. Existing dirty changes preserved; model
and production defaults unchanged. HEADs remain 4055d92 / 6d3f2d2 on main.
No commit/push/pull/reset/cleanup/download/training. Scoped WSL/sibling-write
escalations succeeded; no unresolved execution failure.

Closure note: a redundant final WSL AST-only check was later rejected by
automatic approval review because the account usage limit was reached. Both
scripts had already executed successfully on both sequences, including all
independent checks. No workaround or retry of that rejected action was used.
After the owner requested continuation, the unaffected in-workspace artifact
hash verification and completion records were finalized with ordinary access.

Exact next step is the [data-expansion decision](hl-v1/pilot-01/DATA_EXPANSION_DECISION.md):
bounded metadata/access inventory of proposed MulRan real repeated routes,
then a prospective annex with verified sessions/roles before new registration
outcomes. A raw-scan-support amendment is only proposed, not adopted. Preserve
the original INCONCLUSIVE outcome; never silently rename a changed run HL-V1.
No new learned-head work or manuscript restart follows from this result.

## Prior execution checkpoint: HL0 complete

2026-09-14 execution supersedes the not-started statements in the historical
planning entries below. The owner requested HL0 only; HL1 remains NOT STARTED.

Created [preflight-01](hl-v1/preflight-01/REPORT.md) exclusively under HL-V1.
Decision: **HL0 PASS, bounded engineering prerequisites only.** H1/H2 are not
evaluated; no training GO or scientific success is claimed. INCOMPLETE was removed
only after independent bank validation and final source checks; all artifacts
are hash-bound. No KITTI06 hypotheses/outcome labels were generated or inspected.

- Verified complete raw IDs, all 3,862 finite scans, timestamps, calibration, GT,
  frozen odometry/keyframes and all 3,996 input-manifest hashes with zero mismatch.
  M0 manifest integrity verified; same-volume/independent-backup limitation remains.
- Synthetic transform direction, strict error boundaries, SO(3), empty support,
  duplicate/causal/age checks passed. GT text rigidity residual <1.80e-7; this is
  numeric precision evidence, not a physical GT accuracy certificate.
- Two-support anchors: KITTI05 51/374; KITTI06 22/202. Only 35 eligible KITTI05
  proximity pairs within 30m/separation200 exist in the resource registry. Ten
  were selected by the predeclared pair hash before outcomes. This registry is
  not the full HL1 SC population and does not establish four-stratum adequacy.
- Forty K=4 hypotheses and all 160 support combinations valid; no CUDA OOM or
  inference failure. Synchronized pair wall total 39.794s, peak allocated/reserved
  4.457/8.998GiB. Warmed inputs and correlated proximity pairs limit extrapolation.
  Four additional requests were RNG checks only, never oracle retries or bank
  replacements. Reordered, cache and fresh-process repeats are exact (delta0);
  caller RNG/backend state restoration passed. CPU/GPU kernel-active time and
  human labour were not separately instrumented; timings are scoped wall times.
- Bounded literature audit records RAP/ROVER/sequential testing/learned Hough
  selection and newly identified RegScorer overlap. Publisher full text was
  access-limited for learned scorers. No novelty certificate; official RAP
  rigidity selector requires an adapter before any claimed baseline comparison.

Added two standalone algorithm/validation scripts in RAP-SLAM/scripts and two
maintenance-only provenance/finalization scripts in RAP-main/scripts/maintenance.
No model or production-default changes. Existing dirty changes preserved;
HEADs stay 4055d92 / 6d3f2d2 on main; no commit/push/pull/reset/cleanup.
Initial sandbox WSL access failed; approved scoped escalation succeeded. No
unresolved runtime error remains. Both repository diff whitespace checks passed
(Git emitted pre-existing line-ending conversion warnings); four helpers parse.

Exact next step: fresh pilot-01, broader candidate registry, evaluator-only
four-stratum sampling and adequacy audit, then KITTI05 discovery inference and
frozen report before KITTI06 confirmation. Preserve shortages and INCONCLUSIVE
when thresholds cannot be met. Do not rerun HL0, use the profile bank as hard-loop
validation, relax support rules, train or resume drafting automatically.

## Historical planning and handoff entries

2026-09-14. The owner explicitly paused manuscript work and requested research
and planning before implementation, targeting CAS Zone 2. Clarifications:
1-2 weeks, one RTX 5070, small adaptation training allowed, public datasets
accessible, and difficult-scene reliable loop closure preferred. No target field
or journal has been fixed. No journal quartile or publication outcome is promised.

Reviewed current evidence and backend APIs (pairwise/multigeneration/multiview
registration, learned features and geometric scoring). Conducted focused web
literature searches and primary-source checks: RAP, KISS-SLAM, KISS-Matcher,
GeoTransformer, ROVER, sequential loop testing, information-aware/retroactive
closure, X-ICP, budgeted selection/MAC, max-mixture, learned hypothesis selection,
Multi-Mapcher and public dataset protocols. Sources and reading depth are recorded
in RESEARCH_REPOSITIONING_PLAN.md; this is not an exhaustive novelty certification.

Preferred conditional route: use actual short temporal support observations
excluded from RAP generation to select/reject frozen generated hypotheses with
one small trained head. The plan distinguishes this from existing generic
confidence learning/temporal filtering and requires a hand-crafted-support and
equal-data/compute comparison. A two-day headroom pilot is proposed before larger
training. Multiview covariance/hyperfactor and full RAP fine-tuning are higher-risk
alternatives, not simultaneous tasks in this two-week window.

Proposed data/evaluation adds natural hard negatives, continuous RTE/RRE, strict
registration recall, acceptance tradeoffs, task-level sequence/site holdout,
strong global registration and full LiDAR-only SLAM baselines. Existing four
sequences remain development evidence. RAP training data includes many plausible
new datasets; new-to-project is not new-to-pretraining. No data was downloaded.

No production/model changes, training, experiments or manuscript extension.
Only planning/handoff documents changed. Prior drafts and measured outcomes are
preserved. Git worktrees remain dirty with earlier maintenance work; no commit,
push, pull, reset or cleanup. M0-M5 is not declared universally complete.

Historical next step (superseded by the protocol entry below): discuss the plan and agree on the novelty target, pilot decision gates and
whether the two-week horizon is exploratory or a final experimental deadline.
Implementation requires the owner's next direction; do not auto-start it.

## HL-V1 protocol declaration and continuity update

The owner clarified that 1-2 weeks is a direction-validation window, not the
final experimental deadline, and requested a concrete protocol plus AGENTS.md
update. Created [HARD_LOOP_EXPERIMENT_PROTOCOL_V1.md](HARD_LOOP_EXPERIMENT_PROTOCOL_V1.md).
This declaration is prospective; numerical gates are project screening choices,
not measured results or journal acceptance standards.

Fixed HL0/HL1: KITTI 05 discovery and KITTI 06 confirmation, four deterministic
sampling strata, target 100 pairs per sequence, K=4 frozen RAP requests, two
causal support keyframes per anchor, a fixed geometric support score, immutable
shared hypotheses and B1/B4/S4/oracle/reject-all comparisons. Defined transform
direction, strict pose criteria, failure denominators, shortages, decision-metric
precedence and GO/STOP/INCONCLUSIVE gates. Confirmation remains historically
observed development evidence. No independent-generalization claim is attached.

HL2/HL3 remain conditional: exact MulRan sessions/site partitions and training
configuration require a frozen annex after pilot GO; NCLT is the proposed
external dataset. Same-data/compute controls, strong registration/system
references and prospective trajectory metrics are required for later claims.
No claim is made that all final training details are already fixed.

Updated the authoritative AGENTS.md override, research-plan open decisions and
maintenance reading order. Earlier evidence and negative findings are preserved.
Reviewed protocol consistency, including shortlist capacity, sampling cap order,
invalid-support handling and the distinction between oracle diagnostics and
inference inputs. Documentation validation checks local Markdown link targets
and whitespace; no experiment or runtime test is implied by these checks.

Both repositories remain at 4055d92 / 6d3f2d2 with earlier uncommitted maintenance
changes; no commit, push, pull, reset or cleanup. This update changes planning
documents only. No download, inference, training or manuscript drafting started.
Independent backup and checkpoint training-membership gaps remain unresolved.

Exact next step on an instruction to continue/execute research: begin HL0
source/data/geometry/RNG/resource preflight, then run the declared untrained HL1
and persist its decision. Do not re-ask settled resource/window/direction choices,
resume writing, or enter training before its gates. Current HL0 and HL1 status:
NOT STARTED.

## Fresh-conversation handoff confirmed

The owner accepted HL0 followed by the untrained HL1 pilot and will open a new
conversation for execution. Added an explicit entry point near the top of
AGENTS.md: ordered reading, frozen-parent discovery, actual data completeness
checks, exclusive preflight output creation, repository write boundaries and
the exact not-started checkpoint. A continuation request should begin execution,
without repeating the already settled direction/resource questions.

Rechecked both dirty worktrees; existing maintenance changes remain intact.
This handoff adds documentation only, starts no jobs and makes no commit/push.
HL0, HL1, pilot runner, hypothesis bank and trained head remain unclaimed/not
started. Next agent must follow the complete HL-V1 protocol, not infer results
or implementation from the existence of this plan.
