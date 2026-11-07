# RAP / RAP-SLAM stage summary and next strategy

Date: 2026-10-15, Asia/Shanghai. Scope: owner-requested review and strategy.
Focus: 2026-10-10 through 2026-10-15, with earlier controls used as context.

The project has a reproducible complete SLAM baseline and a substantial recorded
frontend engineering improvement. An additional useful RAP-specific system
contribution remains unproved. Recent work established numerical prerequisites,
excluded several exact constructions, and corrected source/reference assumptions.
It did not produce a newer complete-system improvement after the October 11
benchmark. The next investment should answer a concrete evidence dependency and
then one mechanism decision, with practical controls considered before fitting.

This document reports historical experiments and a new strategic judgment.
It is not a scientific execution protocol, a new benchmark, an amendment of old
gates, or a reason to resume partial runs. No scientific payload or network
acquisition was performed for this review.

## 1. System and established result

The operating path is KISS-ICP local motion, keyframes, proximity/Scan Context
retrieval, RAP loop-pose verification, GTSAM pose-graph optimization, and dense
trajectory evaluation. RAP supplies loop constraints; it does not replace the
local odometry backbone. The local registration model uses a 12-layer DiT and
five flow calls in the complete-system configuration. Its attention layer is a
local PyTorch SDPA port. These source/runtime facts matter when attributing
results to the public release.

The earlier E0 correction is a real engineering asset: development mean segment
translation drift fell from 0.761655% to 0.388718%, and exposed-transfer drift
from 0.959528% to 0.505615%. That gain belongs to the frontend correction and
must not be credited to a newly learned RAP component. See the
[October 12 review](../../2026-10-12/stage-review-01/REPORT.md).

The [October 11 benchmark](../../../meeting_20261011/benchmark/REPORT.md) remains
the latest complete-system comparison: six sequences, two systems, three process
repetitions, 36 admitted runs. The following arithmetic means were recounted
from the saved 36 scalar rows in this review; trajectories were not reevaluated.
Lower is better for both metrics.

| Cohort | RAP ter (%) | KISS ter (%) | RAP aligned ATE (m) | KISS aligned ATE (m) |
|---|---:|---:|---:|---:|
| 00/05/06 | 0.388718 | 0.472672 | 1.460663 | 0.635296 |
| 07/09/10 | 0.505615 | 0.484556 | 0.721480 | 0.764081 |
| All six | 0.447167 | 0.478614 | 1.091072 | 0.699689 |

RAP has lower mean ter on 00/05 and lower mean ATE only on 09. KISS has lower
mean ter on 06/07/09/10 and lower ATE on the other five sequences. The principal
RAP ATE deficits are 00/05. The transfer-cohort ATE advantage depends on 09,
whose physical observation/reference conflict remains unresolved. Keep 09 and
the official reference in every applicable official comparison.

Segment drift and aligned ATE measure different error behavior. Neither lower
pair error nor lower geometric residual guarantees improvement in both. Three
fixed-seed process repetitions establish process reproducibility, not independent
scene or fresh-noise robustness. The recorded global best repetitions remain
RAP1/KISS3; do not assemble a best-per-sequence table. Original resource failures,
two Windows observation gaps, and the null attached-launcher exit remain.

## 2. What the recent experiments changed

| Work | Established result | Consequence |
|---|---|---|
| Native backward diagnosis, NBR02 | Identical forward and endpoint upstream values coexist with repeat differences in P parameter gradients | Cache alone does not explain the measured mismatch; original native comparison stays incomplete |
| Math and FP32 controls, NMR0/FPC0 | Math repeats become exact; NMR and both FPC variants each pass only 8/12 fixed direction checks | Reproducibility and directional corroboration are separate gates; no native training admission |
| Double-tail controls, DTC0/SFC0/ADR0/SAR0 | Changed fixed-prefix double function passes 12/12 directions; bounded descent, activated-adapter derivatives, and source-sampler bindings pass | A useful numerical feasibility result for that exact shadow function, without native-function equivalence |
| Shadow fit, HFIT0 | 40 retained manual updates reduce V and P fit losses by about 2% | Prediction exceeded the original 2 GiB artifact cap; complete heldout comparison is absent |
| Frozen feature/head interface, FCE0/FHR0 | Context isolation and source extraction pass; all 6,150 head columns are locally active; derivative controls pass | Functional context dependence and numerical validity do not establish pose accuracy or contribution |
| Descriptor and geometry controls, CDG0/GSG0 | Descriptor all-point uniqueness fails; ordinary full-shape geometry recovers the exact congruent copies | Retire the copied-congruent fixture as RAP efficacy/innovation evidence |
| Bounded residual feasibility, BRF0 | Even optimistic allowed corrections violate the required KISS sequence safety conditions | Stop the exact native-base/component-bound family before head implementation or fitting |
| Source/exposure/time audits, PSR0/PEL0/POP0/FTI0 | Existing engineering sources are available; POSS-B has reported outcome exposure; trajectory/time structure cannot authenticate physical conventions | No relabeling old data as untouched confirmation or inferring sensor truth from local geometry |
| Release/demo audits, PRI0/DSR0/RBA0/MDA0 | Hosted weight byte identities, local runtime attribution, default demo reference roles, and pinned catalog comparison are now explicit | Original demo member/reference authentication is the next exact evidence dependency |
| Storage/supervision controls | Prefix reconstruction and several controlled budget/pipe/final-memory-query cases pass | Whole-dossier guarantees, old resource gaps, and failed archive/fit comparisons remain unresolved |

The rows have different scientific meanings. A validated negative experiment,
an incomplete resource-stopped comparison, a positive derivative control, and
an unknown physical provenance question must retain those distinct statuses.

### Native adaptation

[NBR02](../../2026-10-13/native-backward-reproducibility-02/REPORT.md) observes
6,219 differing P gradient values between full repeats and 6,143 between cached
repeats, despite exact forward/upstream arrays. [NMR0](../../2026-10-13/native-math-reproducibility-01/REPORT.md)
removes those instrumented repeat differences under math attention, but four P
direction checks remain outside their predeclared bounds. FP32 controls retain
direction gaps. These finite-precision observations do not uniquely identify
an autograd defect, a kernel cause, or an official upstream failure.

[DTC0](../../2026-10-13/native-double-tail-control-01/REPORT.md) passes all 12
checks after freezing the first ten-layer prefix and using a double trainable
tail. Later numerical controls establish descent and sampler/lifecycle behavior
for that changed function. Nominal 443,904 trainables do not prove full active
rank; B=0 initially makes the corresponding LoRA A gradients inactive.

[HFIT0](../../2026-10-13/shadow-conditioned-fit-pilot-01/execution-stop-audit-01/REPORT.md)
retains 20 V and 20 P updates, but prediction stopped at 2,156,270,857 bytes
against 2,147,483,648 allowed. Its 37 partial directories have no complete
51-case prediction seal or heldout results. The outcome is incomplete, not a
failed generalization result and not demonstrated noise robustness. Preserve
the partial evidence and original cap; do not score a favorable subset.

### Practical controls and exact stops

Earlier [RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md) is the
central warning about comparison choice: joint J beats separated I, yet its
all-48 translation median is 0.888431 m versus same-point geometry 0.097115 m.
On the 36 matched KISS endpoints, J is 0.888431 m versus KISS 0.022371 m.
J-versus-I alone is insufficient evidence of useful RAP value.

[FCE0](../../2026-10-13/frozen-context-extraction-01/REPORT.md) and
[FHR0](../../2026-10-13/frozen-metric-head-derivatives-01/REPORT.md) establish
working feature and derivative interfaces. Their pointwise D already contains
learned RAP encoding, so it is not a raw geometry control. [GSG0](../../2026-10-13/geometry-signature-control-01/REPORT.md)
then solves both exactly copied transforms with translation errors around
1e-14 m using ordinary geometry. This is a strong reason to end efficacy work
on that fixture, while retaining it for source/numerical checks.

[BRF0](../../2026-10-14/bounded-native-residual-feasibility-01/REPORT.md) is stronger
than another failed fit: the new component bounds imply norm limits of
0.086603 m and 0.346410 degrees. Even optimistic sequence translation harm
against KISS is at least 0.026818 m on 07 and 0.014341 m on 09, exceeding the
0.005 m safety allowance. A new head within that exact family cannot fix the
necessary-condition failure. This says nothing universal about all residual
functions or all RAP representations; it does not authorize a radius/base swap.

### Physical source, release and evaluation roles

[PRI0](../public-release-identity-01/identity-attempt-02/REPORT.md) establishes that
three local weight files, totaling 686,394,961 bytes, match author-linked hosted
SHA256 metadata. Training membership, site exclusion, historical acquisition,
and numerical runtime equivalence remain separate.

[RBA0](../release-backend-attribution-01/REPORT.md) binds historical failures to
the local SDPA source and the hosted-matching checkpoint. Observed author source
uses external FlashAttention; its mutable/cached observation is not an immutable
runtime identity. Therefore the local failures cannot be reported as a demonstrated
official FlashAttention defect. The maintenance brief is local and unsent.

[DSR0](../demo-source-role-01/source-attempt-02/REPORT.md) inventories 156 files,
478,400,579 bytes, 27 directories. The default PLY path sees 26 directories;
Oxford's five PCD files are not enumerated. The loader supplies sampled input
coordinates as pointclouds_gt and transforms those into evaluation references.
Already-aligned supplied clouds could support that alignment convention; the
audit establishes neither their physical state nor independently measured truth.
The demo path is not automatically an external-truth registration benchmark.

[MDA0](../official-demo-metadata-01/REPORT.md) acquires 1,273,695 metadata bytes
within the approved 4 MiB cap and compares the complete pinned RegX catalog.
Of 3,243 point files, 3,215 LFS identities have zero local SHA256 matches and
28 non-LFS files have zero local length matches. No current demo member is byte
identical in that revision. Reencoding, resampling, common physical scenes and
other historical versions remain unknown. No linked scene-reference metadata
was admitted; same-name RegX poses cannot be transplanted onto local demo files.

[POP0](../../2026-10-14/poss-outcome-provenance-01/layout-attempt-02/REPORT.md)
also supersedes the interpretation that POSS-B was merely configured: its 12
stored loop outcomes appear in downstream analysis. It is outcome-exposed,
although per-frame execution/source lineage remains unauthenticated. Its NaN
mean_dist values exclude all B rows from the old fit; that fit has 188 eligible
rows, not evidence of B fitting. [FTI0](../../2026-10-14/frame-time-identifiability-01/REPORT.md)
shows why horizontal tracks and increasing timestamps cannot identify gravity,
sensor axes, hardware clocks, or per-return timing. The
[09 physical conflict](../../2026-10-12/reference-physical-consistency-01/REPORT.md)
stays unresolved; no corrected reference or loader fault follows.

## 3. Strategic assessment

My assessment is that the binding problem has moved beyond implementation
readiness. Three conditions must now meet: a defensible observation/reference
role, information that distinguishes a useful new mechanism from retired ones,
and an advantage over strong practical controls that reaches the full system.
More derivative passes, file identities, or prototype budget cases alone meet
none of the latter two conditions.

This does not mean all research must wait for perfect provenance. Existing
KITTI data can support explicitly exposed, supplied-reference engineering
development, as [PSR0](../../2026-10-14/physical-source-role-feasibility-01/REPORT.md)
already states. Independent physical confirmation and authenticated exclusion
from pretraining require additional evidence. Those claim boundaries should be
kept explicit rather than made universal blockers.

The highest-value immediate dependency is the original demo archive and
reference construction, because it determines which measured registration task
the already-local data can legitimately support. Limit this to a finite evidence
decision. Another broad metadata census or geometry correlation would add little.
Storage and supervisor work should resume only for a separately justified task
whose decision actually depends on it.

## 4. Recommended next sequence and decision conditions

These are strategic recommendations, not a frozen protocol or new execution
authorization. Relative priorities express judgment, not success probabilities.

| Priority | Concrete deliverable | Proceed condition | Stop/hold condition |
|---|---|---|---|
| 1. Exact demo/reference evidence | Resolve the existing 156-member request against the original archive version and reference construction | Exact member linkage and documented units/frame/alignment/reference role | No exact mapping: keep demo diagnostic-only; report unknowns without another broad acquisition |
| 2. One mechanism decision | One page naming the extra observation, mathematical output, old-family differences, strongest ordinary explanation, and failure criterion | Available inputs and a falsifiable incremental RAP effect remain after strong-control/necessary-condition review | No extra information, ordinary geometry already sufficient, or exact retired family: end the proposal before extraction/fitting |
| 3. One bounded development test | A complete common-input comparison with declared roles, metrics, safety, cost and resource scope | A new prospective scope; useful pose gain over strongest geometry/direct controls and the relevant separated/joint comparison | Only surrogate loss/J-versus-I improves, safety fails, support fails, or budget is exhausted |
| 4. System and confirmation | Full prescribed sequences, followed by reserved-source confirmation where authenticated | Local benefit survives complete ATE/ter/rer and failure/runtime accounting | Pair-level gain fails to reach the system, or independent-source role remains unknown |

For priority 1, reuse the existing
[unsent request](../continuation-handoff-06/AUTHOR_DATA_REQUEST_DRAFT.md) and
[156-member identity list](../continuation-handoff-06/DEMO_MEMBER_REQUEST.json).
The decisive questions are archive version/member SHA256, whether inputs were
already registered or synthetically transformed, input-to-world transform
conventions and reference construction/quality, exact RegX preprocessing mapping
if any, and training/session role or an explicit unknown. Do not redraft another
inventory. No outreach or new acquisition occurs under this summary request.

If references are documented, that enables supplied-reference engineering; it
does not itself certify physical truth or unseen pretraining membership. If
they remain unavailable, leave that task unsupported and assess any different
existing-data engineering proposal on its own stated reference role.

For priority 2, retain KISS/E0 as the strong backbone. A possible task to assess
is unposed multi-view registration or map merging with substantial initial-pose
uncertainty, where RAP's generated joint constraints might serve a clearer role
than replacing centimeter-scale adjacent odometry. This is a conditional task
candidate, not an admitted mechanism or a novelty claim. It must distinguish
itself explicitly from stopped G0/G1 proposals, CCR0 context, copied-congruent
fixtures and the bounded native-base residual. Generic multiview/submap methods
already have prior art. If exact source/reference records or that distinction
are missing, do not create a new cohort or run a renamed old construction.

For a future system-improvement proposal, I recommend ATE-primary development
with explicit ter/rer and per-sequence safety, since 00/05 ATE is the largest
current gap. This is a proposed future metric choice; existing simultaneous
gates and stopped experiments remain unchanged. Set actual margins before any
new outcomes rather than copying a favorable observed number.

Any later test must hold measured point IDs, preprocessing, information access,
initialization/base pose, solver, exposure and complete population fixed across
the relevant controls. Include strong raw geometry, direct statistics/model-free
inference, and separated/joint controls. Measure active capacity if learning is
involved. Count descriptor extraction, cache creation, neural sampling, solver,
failed attempts, fallbacks and full evaluation. Apply numerical checks only to
the changed function needed for that test. Seal complete predictions before
new evaluator errors; use fixed-checkpoint fitting and evaluation separately.

The immediate next deliverable is priority 1's evidence decision plus priority
2's one-page mechanism assessment. It is not another fit, archive retry, context
sweep, full RegX download, or production integration.

## 5. Review checks and preserved boundaries

Fourteen key report byte identities were compared against their existing
delivery-seal entries and all matched. The saved benchmark scalar rows were
recounted for cohort/sequence means and the 36-run grid. These checks are
document identity and scalar arithmetic only; historical validators are cited
as historical validation, not rerun here. SOURCE_INDEX.json and CHECKS.json
record the exact review sources and checks.

Both current repository HEADs, branches and tracked dirty sets were read:
RAP-main 4055d929c594b0033aafc6eed339c910369eef55 on codex/meeting-20260930
(two tracked dirty paths); RAP-SLAM 6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6
on codex/e0-f1-20260926 (nine). Initial sandbox Windows/WSL status reads could
not access RAP-SLAM; the authorized read-only WSL Git retry succeeded. An inline
PowerShell scalar-summary command had a pipeline parse error before evaluation;
the corrected read-only arithmetic command succeeded. No scientific code or
historical experiment changed as a result of either preparation issue.

All ten retained markers and the original scientific decisions remain governed
by their existing dossiers; this review does not newly rehash all 552 handoff
identities or recertify resources/process absence. WPC0 remains resource
INCOMPLETE; NMQ0/MDA0 observer full-lifetime peaks and ordinary setup RSS remain
unknown. HFIT0 artifact failure and LCP0 time failure remain distinct stops.

The existing account-stop record describes the prior exhausted window and is
separate from the later closing-window reading. Its exact original observation
time is unknown. The account seal and owner-close checks already record the
retrospective close. This review does not infer current account usage, restart
after reset, or treat budget exhaustion as scientific completion.

Only this review's new documents and mutable AGENTS/phase handoffs are updated.
Original delivery/account seals, snapshots, partial products, official references,
production/default/backbone/manuscript and Git history stay intact. No model,
point/pose evaluation, fit, installation, external message, acquisition, process
restart, commit or Git synchronization is performed. The research goal remains
unresolved.
