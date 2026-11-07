# RAP / RAP-SLAM broad retrospective and next decision

Date: 2026-10-16, Asia/Shanghai. Scope: the owner's request to read AGENTS,
investigate the present state, review the attempts broadly, distinguish useful
and unsuccessful results, identify missed information, and make the next decision.

The project has a functioning, reproducible SLAM system and a substantial
frontend engineering gain. It has not yet demonstrated an additional useful
RAP-specific improvement over its strongest relevant controls. Several model
interfaces and numerical controls work; that is different evidence. Several
comparisons are incomplete; their missing outcomes cannot be counted as negative
accuracy results. The immediate C0 task remains preparation only.

This review makes a strategic decision, not a new scientific execution scope.
No model, point/transform decoding, fit, registration solver, trajectory metric,
network acquisition or external message was run. Historical protocols, stops,
seals, partial artifacts and reference files remain unchanged. The original
research objective is unresolved. No goal status or account-boundary claim is made.

## 1. Coverage and how to read the evidence

All 4,546 lines of the entry version of AGENTS were traversed, including its historical
sections and repository/evaluation boundaries. The review also inspected the
September 9 takeover/audit, earlier optimization synthesis, representative
primary reports, the October 11 saved benchmark scalars, October 15 strategy,
October 16 source/contract documents, and existing public-discussion responses.
The full mechanism-family map is in [ATTEMPT_MAP.md](ATTEMPT_MAP.md).

The map separates five kinds of result:

| Kind | Meaning |
|---|---|
| Engineering benefit | An actual measured improvement within the stated task and comparator |
| Prerequisite or diagnostic positive | A source, numerical, information-use or implementation property was established |
| Complete negative | The defined comparison completed and failed its prospective conjunction |
| Incomplete or inadequate | A resource, implementation, coverage or data prerequisite prevented that comparison |
| Unknown | The available records do not establish the claim |

A valid validator, many checks, a complete delivery seal and a successful process
exit do not all mean an effective algorithm. Conversely, a failed fixed method
does not establish universal impossibility. Counts from HL, PG, F2, RVC and
online E0 belong to different candidate policies and cannot be merged.

This is a broad documentary and saved-scalar review, not an all-history replay.
Thirty-three documentary sources are indexed. Twenty selected report identities,
all 19 C0 source bindings and the eight handoff10 seal entries match their
existing records. The 36 saved benchmark scalar rows form the complete grid;
recomputed per-sequence means match the saved means exactly, and all 24 printed
per-sequence ter/ATE cells match at six decimals.
Historical independent numerical checks remain historical; they were not rerun.
No global count of "experiments" is invented from incomparable stage, attempt,
fixture and validation counts. See SOURCE_INDEX.json and CHECKS.json.

## 2. What is actually running as the system

The main pipeline is KISS-ICP local odometry, keyframes, proximity/Scan Context
candidate retrieval, RAP loop-pose proposals and geometric acceptance, GTSAM
pose-graph optimization, then dense trajectory and map output. The established
offline baseline uses candidate budget 12, K1, five flow steps and NMS off.
Live retrieval/NMS/source-ID handling is a distinct protocol. RAP currently
supplies loop constraints; it does not replace the local odometry backbone.

The September maintenance established material foundations: protected rigid
fitting against TF32 effects, corrected segment aggregation and source/frame
correspondence, regenerated representative measurements, separated measurement
identity from pair identity, and corrected leakage/calibration interpretations.
These repairs make later evidence more defensible; they do not retroactively
repair every legacy edge or validate the old conformal and uncertainty claims.
See the [takeover audit](../../audit-2026-09-09/AUDIT_REPORT.md).

The September 9 snapshot preserves 1,568 files on the same E: volume. This is
historical preservation, not an independently located backup. New experimental
code and results remain largely outside Git history. Current read-only status
still shows the original HEADs and branches: RAP-main 4055d929 on
codex/meeting-20260930, with .gitignore and AGENTS tracked-dirty; RAP-SLAM
6d3f2d22 on codex/e0-f1-20260926, with the same nine tracked-dirty paths listed
in CHECKS.json. Branch names therefore do not describe the complete scientific
state. No commit, push, reset, clean or synchronization was performed.

## 3. The effective results we should keep

### 3.1 E0 is the strongest demonstrated improvement

The explicit 0.205-degree KITTI intrinsic correction, E0 arm A, reduced
development full-system mean ter from 0.761655% to 0.388718%, and aligned ATE
from 1.629942 m to 1.460663 m. On the later fixed 07/09/10 system set, mean ter
fell from 0.959528% to 0.505615%, and ATE from 1.217655 m to 0.721480 m.
This is frontend engineering transfer, not a newly learned RAP mechanism.
The range/voxel-only arm did not deliver the same improvement.
Sources: [E0](../../2026-09-26/e0-frontend-01/REPORT.md),
[E0-H1](../../2026-09-27/e0-heldout-01/REPORT.md).

The correction was already visible in older S0b and comparison records. E0
made it coherent and prospectively evaluated; it should not be described as
a newly discovered physical mechanism or counted repeatedly as new progress.

### 3.2 RAP loops have bounded value, with a metric tradeoff

On the fixed corrected E0 frontend, adding the saved RAP loop graph changes
development mean ATE from 1.943835 m to 1.460664 m, while ter rises from
0.374547% to 0.388718%. On 07/09/10, ATE changes from 0.778065 m to
0.721480 m, while ter rises from 0.477262% to 0.505615%. Thus it would be
wrong to say RAP loops do nothing, or to say they improve all system metrics.
These are supplied-reference outcomes, not proof of physical truth or that RAP
is the best available loop registrar. Source:
[system opportunity audit](../../2026-09-29/system-opportunity-audit-01/REPORT.md).

### 3.3 The latest complete system result is still October 11

Six sequences, two complete systems, three process repetitions: 36 admitted
runs. The table below was recomputed from saved scalar rows in this review;
no trajectories or segments were reevaluated. Lower is better.

| Sequence | RAP ter % | KISS ter % | RAP aligned ATE m | KISS aligned ATE m |
|---|---:|---:|---:|---:|
| 00 | 0.518171 | 0.575272 | 2.754437 | 0.916513 |
| 05 | 0.320473 | 0.517250 | 1.294699 | 0.661035 |
| 06 | 0.327512 | 0.325492 | 0.332854 | 0.328341 |
| 07 | 0.394673 | 0.386563 | 0.326400 | 0.315371 |
| 09 | 0.593652 | 0.542063 | 1.074523 | 1.259111 |
| 10 | 0.528520 | 0.525043 | 0.763516 | 0.717761 |
| All six arithmetic mean | 0.447167 | 0.478614 | 1.091072 | 0.699689 |

RAP has better ter on 00/05, and better ATE only on 09. Its largest ATE
deficits are 00/05. The three repetitions primarily show repeatability under
the fixed conditions, not three independent scenes or fresh-noise robustness.
The published best actual repetitions remain RAP1/KISS3; this review table is
the three-run mean, not a best-per-sequence assembly.

Recorded execution cost also matters: each of the six RAP rows has greater
mean enclosing runtime and maximum Linux RSS than its KISS counterpart.
For 00, the observed means are 249.70 s versus 167.42 s, and observed maximum
RSS 15,297,425,408 versus 1,109,680,128 bytes. These are the archived benchmark
conditions, including their scope and overhead; they are not a new production
latency or algorithmic complexity benchmark. A component sampler timing cannot
be substituted for this complete work. Sources:
[benchmark report](../../../meeting_20261011/benchmark/REPORT.md),
[saved results](../../../meeting_20261011/benchmark/attempt03/results.json).

### 3.4 Numerical and source positives are real but narrower

Useful assets include exact source/input reproduction, safe strict checkpoint
loading, TR0 joint-token extraction, feature-to-point reliance in C2, DTC0
double-tail derivative checks, SFC0 descent witnesses, ADR0 activated-adapter
derivatives, SAR0 sampler bindings, FCE0 context isolation, and FHR0 locally
active head derivatives. PRI0 authenticates three local weights against hosted
identities; B1/B2 authenticate a fixed package and expose a direction conflict.
These facts make future implementation choices better informed. None by itself
demonstrates pose accuracy, generalization, native training repair or system gain.

## 4. What did not work, and what was never completed

The family map retains the detailed distinctions. The main pattern is:

* More hypotheses, support scoring, pooled/support context, per-step rigidity,
  earlier flow checkpoints, ten steps, fixed visibility, intensity and the
  particular feature/sampling interventions did not pass their stated useful
  improvement conditions. Missing good candidates, consistent wrong poses and
  incorrect acceptance remain distinct bottlenecks.
* Local ICP, GICP/FGR selection, fixed causal context, graph redistribution,
  measured information shape, interpolation, shared-plane and cross-visit map
  optimization produced partial improvements or small changes, but no safe
  material conjunction for their exact constructions.
* The complete RLP2 matching-head experiment is genuinely negative. J improves
  over separated I, but translation medians are J 0.888431 m versus same-point
  G3 0.097115 m; on the 36 common KISS endpoints, J 0.888431 m versus KISS
  0.022371 m. A weaker learned control cannot establish practical value.
* The complete NJE0 nonlocal comparison is also negative: J RTE 1.482851 m
  versus P 1.472642 m and practical synchronized geometry 1.471863 m. More
  joint views did not supply the required increment on these four groups.
* BRF0 is a necessary-condition exclusion before fitting. Its exact bounded
  correction family cannot satisfy all strong-control safety requirements even
  under optimistic corrections. A new head inside those bounds would not
  answer the problem.
* NOC0 proves tiny fixed-noise native fitting capability. NOC1 then fails the
  fresh-noise conjunction despite improved means. NOC4's native fit comparison
  never reaches retained training; restored optimizer probes increase loss and
  P gradients fail the required repeat check. NMR/FPC repeatability improves,
  but their direction conjunction still fails. DTC's changed double-tail
  positive is not a repair of the original native function.
* HFIT0 has 40 retained shadow updates and about 2% training-loss reduction,
  but prediction exceeds the 2 GiB artifact cap. No complete heldout result
  exists. LCP0's archive times out and remains unsealed. Neither is an accuracy
  negative, a generalization positive, or a restartable partial experiment.

Representative primary sources:
[RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md),
[NJE0](../../2026-10-15/nonlocal-joint-comparison-01/REPORT.md),
[BRF0](../../2026-10-14/bounded-native-residual-feasibility-01/REPORT.md),
[native/shadow attribution](../../2026-10-15/release-backend-attribution-01/REPORT.md),
[HFIT stop audit](../../2026-10-13/shadow-conditioned-fit-pilot-01/execution-stop-audit-01/REPORT.md).

## 5. Information and lessons that deserve more weight

### 5.1 A specific public-model compatibility lead was not followed

The already acquired ADC0 response contains official repository issue 3,
"Performance difference between online and offline model", created January 22
and updated January 23, 2026. A user reports a difference between the online
Gradio demonstration and downloadable model/configuration. The saved response
shows one comment. ADC0's prospectively fixed reference-documentation rule did
not select that comment, so its content and the resolution remain unknown.
The issue is marked closed in that historical saved response.

This was appropriate compliance with ADC0's narrow rule, not an ADC0 failure.
It is nevertheless a distinct unresolved source lead when reviewing capability
and compatibility. A user's report is not evidence that the weights are bad,
that the difference still exists, or that it explains our results. The single
reply could resolve the lead either way. No reply was fetched in this review;
no claim about today's issue state is made. Source:
[saved complete search response](../../2026-10-15/author-demo-clarification-01/response-00.json).

Before another broad model-fitting proposal, a future separately scoped source
check should resolve this exact existing reply and bind any stated distinction
to a concrete local setting/source identity. Do not start a new query campaign,
download another checkpoint, send an inquiry, or assume a backend fix from it.
The owner's declined author outreach remains declined.

### 5.2 Checkpoint identity is only one part of fidelity

PRI0 closes hosted weight byte identity. It does not close input construction,
point/feature preparation, normalization, anchor convention, sampling, solver
semantics or runtime identity. The local attention source explicitly uses a
PyTorch SDPA replacement; the observed author source uses external FlashAttention.
No equivalence or unique failure cause has been established. Known differences
such as five versus ten steps have already been tested; they are not fresh fixes.

| Fidelity item | Evidence now | Remaining decision |
|---|---|---|
| Three weight files | Hosted metadata/local bytes match, PRI0 | Training membership is still unknown |
| Local attention | Exact local SDPA source is identified, RBA0 | Official runtime equivalence is unproved |
| Model inputs and references | Default loader's internally constructed references identified, DSR0 | Cannot call default demo output an external-reference benchmark |
| RegX matrix direction | Pinned README/viewer conflict established, B2 | Use explicitly custom convention; do not claim canonical batch reproduction |
| Point/feature recipe | Differences recorded; P0 information screen completed | No causal explanation or new performance admission follows |
| Online/downloadable behavior | Historical user report, one uninspected reply | Exact resolution unknown; inspect only under a later source scope |

### 5.3 Surrogates are not the outcome

The records repeatedly break convenient substitutions: lower teacher velocity
MSE can accompany worse pose, lower heldout geometry residual can accompany
worse reference pose, exact joint cycles can accompany wrong registration, and
strict pair error can disagree with graph utility. Raw context dependence or a
locally active Jacobian is not material registration information. C1/P0 top-1
descriptor screens do not prove all generative use impossible; C4's failed
ordinary material-response gate does not prove support features are irrelevant.
These caveats limit explanations, without reopening any stopped construction.

### 5.4 The source/reference problem has separate parts

The old demo archive's CRC/length linkage is useful, but its physical alignment
and reference construction remain unauthenticated. RegX-B1 is a different fixed
source, not a truth transplant to those files. B2 shows that stored world clouds
are transformed into views by T, with inverse(T) as reference, contrary to the
README direction. C0 specifies X_i=T_i W_i and Q_i=inverse(T_i).

The default folder loader derives internal references from supplied coordinates.
Putting augmented X into that path and reporting its internal reference errors
would not implement the intended RegX task. This is the most actionable input
boundary to resolve; it is already recognized in C0's adoption decision.

Paris_02 supplies only two sample records, one pair and one triple, sharing three
clouds. Five view occurrences are not five independent scenes or five independent
trials. A synthetic augmentation inverse verifies construction relative to the
supplied world geometry; it does not authenticate physical registration accuracy
or pretraining exclusion. Do not expand it into a new efficacy benchmark.

### 5.5 09 is a warning, not a convenient exclusion

RAP and Geo share a large cross-visit reference/geometry discrepancy. Local
source/calibration checks and raw geometry diagnostics narrow some explanations,
but physical cause remains unknown. This does not establish wrong GT or correct
models. Retain 09 and its official reference. Since 09 is the only sequence with
better RAP ATE than KISS in the latest benchmark, stronger claims based on the
transfer mean are particularly fragile. The 00/05 ATE deficits remain a clearer
practical target than chasing another favorable mean.

### 5.6 Process overhead should no longer select the research agenda

The control, ledger and supervision work has supplied useful reusable assets.
It has not produced a new complete-system result since October 11. Another
codec, census, derivative fixture or source inventory is justified only when a
named next decision actually depends on it. Do not consume an allowance by
inventing prerequisites or relabeling a stopped family. The RVC selection error
demonstrates the cost: a September 15 "untested" note was used after September
28 V0 had closed that direction. Search the complete family history before
calling a proposal new. Preserve the numerical RVC negative and the mistake.

Independent physical truth and training-membership authentication limit claims;
they are not universal prerequisites for an honestly labeled supplied-reference
engineering study. Likewise, the owner's October 9 relaxation permits useful
ordinary engineering proposals; lack of algorithmic novelty alone is not a
reason to manufacture another novelty audit. Old frozen failures still stand.

## 6. Next decision

### Decision now

Preserve E0/KISS as the working backbone and the October 11 benchmark as the
latest system result. Do not launch another efficacy, fit, head, context, score,
solver or full-system experiment from this review. No concrete new mechanism
has yet earned that investment against the available strong controls.

The next executable scientific prerequisite remains the already frozen C0,
once its original resource guard truly passes and exact source bindings match.
Close it once in the prescribed synthetic/build/consume/independent-validation
order, within its original cumulative 900 s, 512 MiB child, 16 MiB dossier and
zero-GPU boundaries. Existing 2.1993678 s remains charged. Do not lower the
12 GiB Windows guard, stop other work, switch runtimes or restart old stages.
The review itself does not execute C0 or add permission for model evaluation.

The current read-only Windows observation at 08:18:24.0398817 UTC
(16:18:24 Beijing time) reports 10,630,574,080 bytes of commit headroom, still
below 12,884,901,888 required. Thus C0 remains preparation only. This is Windows
commit headroom, not physical free RAM or CUDA free memory. It is one observation,
not a lifetime guarantee. The first sandbox CIM read failed; its subsequent
zero casts are invalid and explicitly rejected, not a zero-headroom measurement.

### Decision after C0, without an automatic efficacy stage

1. If C0 fails, retain the failure and decide its exact implementation/evidence
   consequence. Do not change tolerances or select another scene to obtain PASS.
2. If C0 passes, mark the custom interface prerequisite complete and stop at
   that boundary. It does not create enough independent samples, an authenticated
   canonical benchmark, physical truth, a new mechanism or useful pose gain.
3. Give priority to resolving the one specific existing online/downloadable
   source lead, with a separately defined bounded source-read scope. Record an
   actionable local difference or an explicit non-explanation. Do not reopen
   the declined author outreach or require original-demo authentication to
   hold every other engineering task indefinitely.
4. Admit at most one later pilot only if a short decision states the available
   observation/task, the changed mathematical function, its actual difference
   from retired families, and why the strongest common-input ordinary geometry,
   direct and independent-model controls leave useful headroom. Historical
   gate failures remain failures. No such pilot is frozen by this review.

For a future mapping-system proposal, my preferred prospective target is ATE
with explicit ter/rer and per-sequence safety, because the visible 00/05 ATE
gap is material. This is a future design preference, not a revised score for
LC0/SGC0/F2/NJE0 or permission to tune their gates. Measure full work and failures.
Keep a separate account of engineering value and algorithmic novelty. A modest
engineering success can be useful without a new-method claim; a new-method
claim still needs its own measured increment.

The decisive missing deliverable is a falsifiable, useful comparison contract,
not another general inventory. If the source lead supplies no substantive
difference and no candidate meets that contract, record that no next model
payload is justified. Do not manufacture one. The research objective remains
unresolved; that assessment is neither completion, owner pause, account
exhaustion nor a new blocked goal status.

## 7. What changed in this review

Added this report, the family-level attempt map, a bounded source/check record,
and concise mutable handoff entries. Recounted saved benchmark scalars and
checked current repository metadata, selected sealed identities, C0 bindings
and absence of C0 stage outputs. No historical numerical result was repaired,
rescored or relabeled. No current process-tree absence, complete lifetime
resource certification or current account observation is claimed.
