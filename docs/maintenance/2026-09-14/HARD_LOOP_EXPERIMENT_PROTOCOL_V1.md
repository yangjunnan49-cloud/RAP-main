# Hard-loop research protocol v1

Declared 2026-09-14, before any experiment under this protocol.
Identifier: HL-V1. Status: protocol fixed for the first feasibility stage;
no new runs, downloads, trained heads or measured outcomes under HL-V1 exist yet.

## 1. Authority, objective and scope

The owner has accepted the research direction: reliable loop registration in
low-overlap/repetitive scenes, with frozen RAP proposals and additional real
observations for hypothesis selection or rejection. One RTX 5070 is available;
public data acquisition and small adaptation training are feasible. CAS Zone 2
is an aspiration, not a promised outcome. The 1-2 weeks are a direction-validation
window, not a final experimental or submission deadline; promising work can continue.

The current request authorizes protocol and handoff updates only. Do not start
downloads, implementation, inference or training in this turn. A later instruction
to continue/execute this research authorizes starting HL0 below without asking
again about already agreed resources or direction. Training is conditional on
the recorded gates, not an automatic first step. A material change of research
question requires discussion; routine implementation choices do not.

This protocol supersedes prospective next steps in RESEARCH_REPOSITIONING_PLAN.md
and all manuscript-writing/old S2-S5 instructions. Preserve all earlier baselines,
negative results and drafts. Production defaults remain unchanged. Algorithm
implementation belongs in RAP-SLAM; RAP-main model source stays read-only unless
a later explicit upstream exception is needed. The initial learned component is
an external head, not RAP backbone fine-tuning.

## 2. Questions and stage boundaries

- H1: Does K=4 contain useful correct alternatives missed by current selection?
- H2: Do disjoint support scans select those alternatives better than same-pair
  diagnostics, without GT at inference and without merely using more data?
- H3: Does a lightweight learned evidence representation transfer beyond its
  training sequences and improve the accuracy/acceptance tradeoff?

HL0 is provenance/data/runtime preflight. HL1 is the two-working-day H1/H2 pilot
without learned training. HL2 is small-head training on a frozen expanded split,
only if HL1 passes. HL3 is locked external testing, strong baselines and system
evaluation. Failure or insufficient evidence in HL1 is a useful outcome, not a
reason to hide results or start a larger model. Two days exclude tool/network
outages; record actual labour, elapsed time and GPU time separately.

## 3. Fixed data roles

| Role | Assignment | Interpretation |
|---|---|---|
| HL1 discovery | KITTI 05, complete source IDs 0-2760 | Already observed development sequence; exploratory diagnostics |
| HL1 confirmation | KITTI 06, complete source IDs 0-1100 | No fit using its HL1 measurements before the discovery report is frozen; still historically observed, not independent generalization |
| Regression only | Existing POSS 3850-5268 and KITTI 00 0-4540 | Keep original baseline results; no new hard-loop test claim |
| HL2 train/validation | MulRan, site-disjoint geographic route groups to be frozen in split manifest before fitting | Exact sessions depend on metadata/access; no split may be selected by model outcome |
| HL3 external | NCLT selected sessions, held out as a whole dataset from head fitting | Same campus sessions are correlated; do not describe them as independent sites |
| Optional additional regression | KITTI 08-10 after prior-use audit | Task-level holdout only if prior usage permits; not proof of RAP pretraining exclusion |

The first two pilot sequences are immediately specified; their existing full-run
frontends and explicit source IDs are frozen parents. Building descriptors on
these parents is permitted during execution. New-data sessions are deliberately
not invented here. Before HL2, a data-only manifest must list exact downloaded
sessions, hashes, GT/extrinsics, route overlap, scan ranges, support availability
and split roles. It must be frozen before generating outcome-dependent selection
or training. All overlapping sites, anchor/support windows, hypotheses and
augmentations stay in one partition. If route separation is not defensible,
do not label the partition geographically independent.

NCLT is preferred over adding several adapters in parallel. If it is unsuitable,
record the metadata/GT reason and revise the external-data annex before examining
method results. Dataset-level newness to this project is not pretraining novelty:
the local RAP checkpoint's membership remains unresolved.

## 4. HL0 preflight: bounded prerequisites

Before pilot inference:

1. Verify both worktrees/HEADs, parent completion markers, source/calibration/GT
   identities and current RAP/checkpoint hashes against the preserved parents.
   Refuse overwrite; retain failure products with INCOMPLETE.
2. Check the nearest-paper difference matrix against RAP generation selection,
   ROVER, sequential temporal verification and learned hypothesis selection.
   Record what is reused versus proposed. No novelty certificate is implied.
3. Verify strict pose-error labels against GT precision; source-frame and
   timestamp completeness; causal support construction and transform direction
   with a synthetic rigid-transform check.
4. Profile 10 development pairs, including K=4 and all support operations. Record
   synchronized wall times, peak allocated/reserved GPU memory and environment.
   CUDA OOM is an engineering failure, not registration failure. If infeasible,
   reduce batch/concurrency first; changes to K/input caps require a recorded
   protocol amendment before the scored pilot.
5. Smoke-test request-local RNG: executing the same request alone, reordered,
   and from cache must recover identical saved hypotheses within declared
   numerical tolerance. Prefer exact equality when deterministic; otherwise
   record max SE(3) differences and use one immutable hypothesis bank per comparison.

Bound this to the prerequisites needed for HL1; do not restart general maintenance.

## 5. Candidate population and difficulty labels

Use the frozen keyframes, minimum frame separation 200, existing SC descriptor
geometry (20 rings, 60 sectors, 80 m), with ring-key shortlist expanded to 20
for this pilot. For each query keyframe,
retain up to 20 SC candidates with distance <=0.25 and up to five proximity
candidates within 30 m, then deduplicate physical pairs. Do not apply the legacy
global top-12 budget or RAP acceptance before sampling. Persist ranks, distances,
source membership and the complete unfiltered candidate list. This broader pool
is an experimental sampling protocol, not a production-default change.

GT is allowed only in an offline labelling/sampling tool. Let O_GT be the mean
of the two nearest-neighbour coverage fractions at 1 m after alignment by GT,
on the same fixed 0.4 m geometric preprocessing. It is not reciprocal-match
coverage. Define disjoint strata in this priority order:

1. Confusers: SC-proposed pairs with anchor GT distance >20 m and O_GT <0.05.
2. Repetitive/ambiguous-positive proxy: O_GT >=0.30 and the same query has at
   least two different historical SC candidates within 0.02 descriptor distance
   of its best candidate, separated from each other by at least 200 source frames.
3. Low overlap: 0.10 <= O_GT <0.30, excluding earlier strata.
4. Ordinary revisit: O_GT >=0.50, excluding earlier strata.

The ambiguous-positive definition is a reproducible proxy, not proof that a
scene is repetitive. Audit visual examples after sampling and retain disagreement
labels; do not remove failures based on visual preference. O_GT gaps are excluded
from the stratified pilot only and stay in the natural candidate registry.

Target 25 pairs per stratum per sequence: 100 discovery + 100 confirmation.
Sort candidates in each stratum by SHA256 of UTF-8
`HL-V1|dataset|sequence|source_i|source_j` and take the first eligible pairs, with
at most three selected pairs per query. No replacement or outcome-dependent
resampling. Missing support is recorded before inference. If a stratum is short,
use all available eligible pairs and retain the shortage; do not relax thresholds
or fill it with synthetic negatives. A valid quantitative HL1 gate needs >=60
pairs and >=10 per stratum on each sequence. Otherwise outcome is INCONCLUSIVE
and only a documented data-expansion decision is allowed.

Process strata in the priority order above; the three-pair cap applies across
all strata. Eligibility uses source/support metadata and predeclared GT strata,
never generated pose outcomes. Persist capped and unsupported exclusions.

The balanced pilot is case-control evidence; its accepted-set contamination
does not estimate the natural stream's prevalence or false-loop rate. Retain
natural-stream evaluation for HL3. Ground-truth place labels and measurement
pose correctness remain separate concepts.

## 6. Frozen generation and support construction

RAP settings: existing frozen weights and learned features, five steps, one
generation per call, K=4 calls per pair, voxel 0.4 m, max 4000 points, existing
outlier removal and minimum range 1.5 m. IEEE rigid-fit protection stays enabled.
Seeds are independent per request: first eight hex digits of SHA256 of
`HL-V1|hypothesis|dataset|sequence|source_i|source_j|generation`, reduced modulo
2^31. Store the resulting integer and RNG versions. Same hypotheses serve all
selectors. No oracle retries, no resampling failed generations, no choosing the
best sequence seed. Failed/nonrigid outputs are ineligible but remain logged.

For each anchor, select up to two past keyframes: the nearest earlier keyframe
whose cumulative local-odometry travelled distance from the anchor reaches 2 m,
and similarly 5 m. Require distinct IDs, age <=5 seconds from persisted
timestamps, and exclusion of both generating anchors. If both targets return
the same frame, retain only one. Do not use future frames, GT motion, or the
global candidate relative odometry transform to judge correctness. HL1 scoring
requires two distinct support frames on each side; otherwise record unsupported
and exclude before inference. Later production fallback must be evaluated explicitly.

Let A_s=inv(O_i) O_s and B_t=inv(O_j) O_t be short-motion transforms from support
scans into their respective anchors. Hypothesis T_ij maps anchor j into i.
Compare A_s P_s with T_ij B_t P_t, for each of the four support-scan combinations.
Equivalently the s<-t transform is inv(A_s) T_ij B_t. Test this convention before
using real labels. Preprocess support scans with the same geometric rules.

Fixed HL1 support score: for each of four combinations, compute bidirectional
nearest-neighbour distances in anchor i, clamp each distance to 3 m, average
each direction, then average directions and support combinations. Lower is better.
Also log residual median/90th percentile and 1 m coverage; do not fit score
weights in HL1. Missing points make a combination invalid, not zero residual.
Any invalid combination makes that hypothesis's support score invalid. S4 uses
only hypotheses with all four valid combinations; if none exist, it fails/rejects
and stays in the original eligible-pair denominator. Never drop a pair afterward.
No visibility/free-space ray test or normals enter this first pilot. Such additions
need their own later ablation. The score can penalize legitimate non-overlap;
this limitation is part of H2, not something hidden by GT overlap masks.

## 7. HL1 methods, metrics and exact gates

Mandatory selectors on the SAME immutable bank:

| ID | Definition |
|---|---|
| B1 | First generation; failed generation counts as failure |
| B4 | Highest same-pair overlap, tie by lowest mean distance, then generation ID |
| S4 | Lowest fixed support score, tie by generation ID |
| OR4 | GT oracle: minimize max(RTE/1 m, RRE/5 degrees), tie by ID; diagnostic only |
| REJ | Reject all; exposes the trivial low-false-acceptance solution |

All selectors, including the oracle, require valid SE(3). An empty valid bank
counts as failure/rejection for every selector. B4/S4 ranking does not use GT.
For gate comparisons apply the existing overlap >=0.7 AND mean distance <=2.5 m
to the selected candidate, with no fallback to another generation. Do not add
an S4 rejection threshold in HL1. Report ungated pose selection separately from
gated system decisions. An official RAP rigidity-based selector, when accessible,
is an additional named baseline; do not substitute our B4 for it without saying so.

Strict pose success: RTE <=1 m AND RRE <=5 degrees. Keep continuous RTE/RRE,
90th percentile, legacy 5 m/10-degree label and failure counts. For real revisits,
selection recall = strict successes / all eligible positive pairs, including
inference failures. A gate's correct-accept recall uses accepted strict successes
with the same denominator. Report (a) incorrect accepted transforms / accepted
transforms, (b) incorrect accepted transforms / all attempts, and (c) accepted
confusers / all confusers, with raw numerators/denominators. Do not conflate them.

Freeze the discovery report before inspecting confirmation outcomes. Evaluate
these rules on the confirmation sequence, and show both sequences and every
stratum without significance claims from correlated frames:

- Adequacy: cohort minima above, plus >=10 positive pairs where OR4 and B4
  differ in strict success OR normalized continuous error by at least 0.10.
- H1 passes if OR4 improves ungated positive recall over B4 by >=5 percentage
  points; alternatively, its mean clipped error decreases by >=15%, where
  e=min(5,max(RTE/1 m,RRE/5 degrees)) and failures have e=5. The alternate
  continuous-error path must be reported as such, not called recall improvement.
  If both paths pass, recall is the predeclared H2 decision metric. Mean clipped
  error is evaluated over the same eligible positive pairs, including failures.
- H2 passes if S4 recovers >=25% of the OR4-versus-B4 improvement on the same
  metric that passed H1, loses <=2 percentage points recall on ordinary revisits,
  and introduces no additional incorrectly accepted transforms versus B4 in
  this fixed pilot. This last condition is an engineering screen, not a zero-risk
  guarantee. Report harmful and helpful pair transitions separately.
  Specifically, no pair may become an incorrectly accepted transform under S4
  if it was not incorrectly accepted under B4; helpful transitions do not offset it.
- Both H1 and H2 plus adequacy: GO for HL2. Adequate cohort but H1 failure:
  STOP ranking route and investigate proposal quality in a separately agreed plan.
  H1 passes but H2 fails: STOP neural-head expansion; examine unsupported geometry,
  short-motion error and support-score failure before proposing a revised protocol.
  Inadequate samples or unresolved correctness/resource problems: INCONCLUSIVE,
  not PASS and not evidence that the scientific idea is false.

No gate may be revised after outcomes and still called HL-V1. An amendment must
retain the original decision, rationale and affected data; used data become
development material. These criteria are project decisions, not CAS acceptance rules.

## 8. Required controls before claiming a method advantage

During HL1 collect feasibility/cost; before HL2 conclusions compare S4/learned
selection with pooled short-submap RAP using identical anchor+support scans,
and with a hand-crafted support selector. Pooling uses the same local odometry,
not GT, and its changed point coverage/cap is reported. Compare both equal-input
and equal-wall-time envelopes rather than pretending the two are identical.

Global baseline: KISS-Matcher; local baselines: identity/odometry ICP or GICP.
Record settings, initialization, preprocessing and method-specific failures.
GeoTransformer and the official RAP selector are desirable nearest baselines,
with explicit installation/availability outcomes. KISS-SLAM is the required
complete LiDAR-only reference for final system claims, not a prerequisite for
the two-day headroom decision. Do not change the frontend just to favour RAP.

If extra data or compute fully explains the result, H1/H2 may still establish a
feasible tool, but the learned-method novelty gate remains unmet.

## 9. Conditional HL2/HL3 annex and window success

After HL1 GO, freeze exact new-data site splits and a head-training annex before
training. Cache roughly 800-1500 development pairs as a resource target, not an
independent sample count. Reserve 300-500 external pairs plus a continuous natural
candidate stream; do not require exact quotas when the population lacks a stratum.
The annex must fix architecture, inputs, losses, normalization using train only,
optimizer, training budget, seeds, model selection and abstention threshold rules.
No backbone training, covariance learning, new PGO or semantic model in this first
window. A compact evidence head below roughly 1M parameters is the starting scope.

Mandatory ablations: same-pair-only features; hand-crafted support; pooled/simple
MLP versus spatial evidence encoder; K=1 versus K=4; no rejection; local support
motion sensitivity. Do not claim independent support noise from disjoint frame IDs.
The frozen hypothesis bank must permit exact paired comparison and repeated
head-training seeds, without rerunning RAP unnecessarily.

External protocol must be signed into the manifest before model evaluation.
Primary pair results are strict correct-accept recall versus incorrect acceptance;
report all thresholds/denominators. Primary trajectory result is SE(3)-aligned ATE,
with first-pose APE and camera KITTI drift retained prospectively. No post-result
metric switching. Report all sequences, natural failures, pose-error distributions,
runtime/peak memory, and input/compute differences. No pooling across incompatible
coordinate-frame metrics or frame-level bootstrap as independent runs.

Window success means H1/H2 evidence plus at least preliminary transfer beyond
head-training sequences, with a benefit not explained only by extra data/compute.
It does NOT mean a publishable paper is guaranteed at day 14. If promising, allocate
more time for strong baselines, held-out testing and a defensible method. If not,
retain the negative diagnostic and choose the next question with the owner.

## 10. Artifacts, status and resumption contract

Each fresh run directory must retain: protocol copy/hash; source/checkpoint hashes;
environment; data/split manifest; full candidate list; sampling strata/reasons;
support IDs/timestamps/local poses; immutable hypotheses/seeds; input hashes;
selector scores/decisions; GT labels in evaluator-only files; metrics with counts;
timing/memory; validation; REPORT.md; and INCOMPLETE until validation finishes.
Selectors receive an input structure without GT-derived fields or stratum labels.
An oracle output is stored separately and cannot enter production edge selection.

Recommended first IDs: `hl-v1/preflight-01`, `hl-v1/pilot-01` under a new dated
maintenance output root. Exclusive creation, no cleanup of legacy products.
After each session, update AGENTS.md and the phase record with actual status,
counts, protocol deviations, gate decision and exact next step. Do not mark GO
without the corresponding persisted confirmation result.

Current completion checklist:

- [x] Owner intent/resources and validation-window meaning recorded.
- [x] HL0/HL1 protocol, comparisons and decisions specified before execution.
- [ ] HL0 source/data/RNG/geometry/runtime checks.
- [ ] HL1 discovery report frozen.
- [ ] HL1 confirmation and GO/STOP/INCONCLUSIVE decision.
- [ ] Conditional new-data split/head-training annex.
- [ ] HL2 training and HL3 external evidence.

On the next instruction to execute/continue research, begin HL0 and then the
specified HL1, not manuscript drafting, a generic quota sweep or full RAP training.
