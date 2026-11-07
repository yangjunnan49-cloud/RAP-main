# Research repositioning: two-week decision plan

Status: discussion draft, 2026-09-14. No algorithm implementation, training,
dataset acquisition or experiment is authorized by this document alone. The
owner requests research and alignment first. Manuscript drafting is paused.
Target: Chinese Academy of Sciences journal Zone 2; field not fixed. Available
new-work horizon: 1-2 weeks. Small adaptation training is permitted. The owner
confirmed one RTX 5070, access to public datasets as needed, and a preference
for reliable loop closure under low overlap/repetitive structure. This confirms
scope and resources, not approval to start implementation during this turn.

This is a focused literature and feasibility review, not an exhaustive novelty
search or a prediction of journal acceptance. CAS category/year must be checked
for any eventual journal shortlist; JCR Q2 is not interchangeable with CAS Zone 2.
A short project can establish a stronger result or a credible direction, but
cannot guarantee a publication level by counting modules or experiments.

## 1. Diagnosis of the present work

The strongest existing asset is a corrected, traceable offline pipeline and a
frozen, reproducible baseline. The present scientific gap is more specific:

- The contribution is still primarily integration of pretrained registration
  into a conventional odometry/retrieval/PGO chain.
- Current natural RAP cohorts are small and all-safe after budget filtering.
  They do not expose low-overlap failures, perceptual aliasing or the situations
  in which a generative registrar should justify its cost.
- Identity and odometry ICP are useful controls, but omit a strong global
  registration baseline and a complete modern LiDAR-only SLAM baseline.
- More candidates, scalar weighting and ICP refinement have already produced
  mixed outcomes. These are evidence against an undirected parameter sweep,
  not proof that the framework has reached its potential.
- Four repeatedly inspected development sequences cannot become a fresh test set
  merely by renaming a split. Published precision gains alone are insufficient
  if aligned APE or camera drift deteriorates.

Measured foundation: [O1-O3](../2026-09-13/OPTIMIZATION_SYNTHESIS.md),
[matched comparison](../2026-09-13/o3-comparator-01/REPORT.md),
[full baseline](../2026-09-11/core-baseline-v1/REPORT.md).

## 2. Literature boundaries and nearest competitors

The entries below distinguish established ideas from a possible contribution.
Publication/acceptance status is not inferred from an arXiv identifier. RAP,
ROVER, sequential testing and the 2026 map-consistency work were inspected via
their available HTML pages; other entries use author repositories, project pages
or primary abstracts. A targeted full-text difference audit remains a day-1 task.

| Work / primary source | Relevant established idea | Implication for this project |
|---|---|---|
| [RAP](https://arxiv.org/html/2512.01850v1) | Native multiview registration, rigidity-based generation selection, and downstream mapping applications | Neither multiview inference nor best-of-K selection nor attaching RAP to SLAM is new by itself. |
| [KISS-SLAM](https://arxiv.org/abs/2503.12660), [code](https://github.com/PRBonn/kiss-slam) | A simple LiDAR-only system with local maps, closure and graph optimization | The system baseline must be stronger than odometry without loops. |
| [KISS-Matcher](https://arxiv.org/abs/2409.15615), [code](https://github.com/MIT-SPARK/KISS-Matcher) | Fast global registration combining feature extraction, correspondence pruning and pose solving | Mandatory global registration comparator before claiming an initialization advantage. |
| [GeoTransformer](https://arxiv.org/abs/2202.06688) | Geometric feature matching for robust low-overlap registration | Add a learned comparator if installation and weights fit the time budget. |
| [SGLC](https://arxiv.org/abs/2407.08106) | Semantic graph-guided full loop closing with pose estimation | A generic retrieval/verification/refinement pipeline is already crowded. |
| [ROVER](https://arxiv.org/html/2508.13488v1) | Verification using a trajectory prior after candidate-conditioned graph optimization | Trajectory-consistency gating alone is insufficient novelty; avoid rejecting valid loops just because odometry drifted. |
| [Sequential Testing](https://arxiv.org/html/2512.09447v1) | Accumulating temporal descriptor evidence for adaptive accept/reject decisions | Temporal support or deferred commitment alone is not new. Treat proposed SPRT error targets separately from empirical guarantees under correlated observations. |
| [Information-aware odometry and retroactive closure](https://arxiv.org/html/2607.13516v1) | Coupling information-aware estimation with recovery of missed loops | Re-search after PGO or uncertainty-based weighting alone is weak differentiation. Recent preprint: overlap risk, not a validated benchmark we reproduced. |
| [X-ICP](https://arxiv.org/abs/2211.16335) | Direction-dependent localizability and constrained updates | A Hessian-based degeneracy module is established prior work, not a new contribution by naming it uncertainty-aware. |
| [Budgeted loop closure](https://arxiv.org/abs/1806.00188), [MAC](https://arxiv.org/abs/2203.13897) | Budget-constrained selection and spectral graph sparsification | Generic information-gain selection is a comparator or engineering arm. |
| [Max-mixture](https://openslam-org.github.io/maxmixture.html) | Multimodal constraints and explicit outlier hypotheses in SLAM | Retaining multiple poses or adding a null hypothesis is established machinery. |
| [Learned hypothesis selection](https://doi.org/10.1016/j.neucom.2024.129277) | Learning to choose registration hypotheses using geometric evidence | A small MLP selecting a pose is not sufficient differentiation by itself. |
| [Multi-Mapcher](https://arxiv.org/abs/2511.00635) | Robust registration for heterogeneous multi-session map alignment | Multi-session extension has strong overlap and substantial evaluation cost. |

The initial search did not establish an identical method to the specific proposal
below. This is not a claim that no such method exists. Closest full texts and
their citations must be checked before naming a contribution.

## 3. Candidate directions and priority

| Direction | Potential benefit | Novelty risk | Two-week feasibility | Decision |
|---|---|---|---|---|
| Observation-supported selection of generative registration hypotheses | Recover correct alternatives and reject plausible but unsupported alignments | Medium-high: learned selection and temporal checks already exist | Best fit if the diagnostic shows a measurable selection gap | Preferred conditional route |
| Joint multiview loop factors with correlation-aware information | Avoid treating a single joint generation as many independent measurements | Medium; requires a defensible model, not just fewer edges | High mathematical/integration risk in two weeks | Longer-term alternative, not parallel work |
| Information-aware candidate scheduling | Improve information per inference second | High overlap with budgeted closure/MAC | Feasible but weak standalone contribution | Supporting baseline only |
| LoRA/full RAP adaptation or new flow architecture | Better proposal distribution | High data and training risk; local training code/gradients unverified | Uncertain even with a small adapter | Do not start as the main route |
| Cross-session/heterogeneous mapping | More application breadth | Existing RAP demos and Multi-Mapcher overlap | Data/extrinsics/GT work may consume the deadline | Use only if resources already exist |

The preferred contribution is not 'another confidence threshold'. The question is:
**Can raw observations excluded from hypothesis generation distinguish correct
and incorrect generative alignments when the generator's own geometric score
cannot, and can a small learned model exploit that evidence across sequences?**

This question has a measurable failure mode, a direct comparator and an early
falsification test. It addresses loop reliability and fine pose selection; it
does not assume that existing easy-sequence APE must improve substantially.

## 4. Preferred method hypothesis

Working description: observation-supported generative loop registration.
This is a proposal, not an established novel method or final paper title.

1. Keep RAP frozen and produce K candidate transforms, initially K=4. Preserve
   independent request seeds, raw hypothesis identities and all diagnostics.
   Cluster clearly distinct SE(3) modes for analysis; do not average rotations
   or translations from incompatible modes.
2. For each candidate pair, obtain a small temporal support set from each visit.
   Use only past frames for a causal version; if future frames are used, declare
   the fixed latency and evaluate the same latency for all methods. Select
   support with local travelled distance/rotation, not GT or a favourable score.
3. Generation and support observation IDs must be disjoint. Transport support
   scans into each candidate anchor using short local odometry only. Do not use
   the global odometry loop transform as a truth criterion. Separate local-motion
   error from registration error, and test degradation as that local error grows.
4. Test each generated transform on real support geometry: robust bidirectional
   residuals, spatially distributed support, normal agreement where reliable,
   and visibility/free-space contradictions only where the sensor model supports
   them. A missing observation is not automatically contradictory evidence.
   Mask regions outside the jointly observable field of view.
5. Train a small shared support-evidence encoder/ranker, initially with cached
   features and fewer than roughly one million parameters. It scores a set of
   hypotheses using support observations and the generator diagnostics, with a
   reject option when no hypothesis is supported. This is adapter-head training,
   not a claim that the RAP backbone has been fine-tuned.
   A concrete minimal representation is a spatial grid of robust residual
   quantiles, normal agreement, occupied/observed masks and support counts per
   hypothesis, aggregated across short temporal supports. Use identical inputs
   for a simple pooled MLP control. Start with up to two past support scans per
   anchor and K=4; profile before increasing either. Grid scale and local-motion
   uncertainty treatment must be fixed on development data, not on held-out runs.
6. Use pairwise/listwise ranking targets derived from continuous RTE/RRE on the
   training partition, and an explicit all-bad target. Avoid reducing all safe
   poses to the same class: a 5 m/10-degree label is too coarse for fine selection.
   Thresholds are fixed on validation data, never on the final sequences.
7. Initially emit one selected measurement to the unchanged graph backend.
   Add neither a new covariance model nor all pairwise edges from one generation
   to the core experiment. A conservative abstention path is preferable to an
   unsupported calibrated-probability claim.

Why this might differ: the scoring evidence comes from actual observations not
used to generate that hypothesis, and assesses cross-visit metric support rather
than only descriptor persistence, same-pair overlap or global-trajectory agreement.
The hypothesis-specific spatial evidence representation and training objective
must demonstrate value beyond a hand-crafted temporal residual score. If they
do not, the result is an engineering verifier rather than the desired method.

Disjoint observation IDs do not make the measurements statistically independent:
adjacent scans share scene structure and local odometry. No independence or
conformal-coverage theorem will be asserted. Symmetric repeated geometry may
fool both generator and support, dynamic objects may create contradictions, and
low overlap may leave too little evidence; each is an explicit failure case.

## 5. Two-day falsification before implementation investment

After plan agreement, use 100-200 development pairs spanning ordinary revisits,
low overlap, repetitive structures and non-overlapping retrieval confusers.
Start with K=4 and a modest number of support scans. No test data is used here.

- Measure single-sample, current best-of-K and GT-oracle best-of-K pose quality.
  The oracle is an explicitly labelled diagnostic upper bound, never a method.
- If good alternatives are rarely generated, ranking cannot solve the problem.
  Stop this route if the oracle improves strict registration recall by less than
  about five percentage points and offers no meaningful continuous-error gain.
- If support residuals cannot separate better/worse alternatives even on held-out
  development sequences, do not train a complex head in the hope it will create
  evidence absent from the input.
- Compare against pooled-submap registration and equal-cost multi-start ICP/global
  registration. If the benefit is explained entirely by extra scans or inference,
  the proposed novelty has not been demonstrated.
- Record the first measured runtime/memory profile before fixing the full data
  generation budget. Do not extrapolate two-way timing to multiview attention.

The numerical stop values above are proposed engineering gates for discussion,
not universal publication standards. They should be agreed before execution.

If hypotheses lack a useful oracle gap, the alternate decision is a bounded
proposal-quality study using short submaps or a small residual adapter; this
requires a new hypothesis and plan, not an automatic silent scope change.

## 6. Data and evaluation design

The four existing sequences stay development/regression evidence. A practical
two-week target is roughly 800-1500 training/validation pairs plus 300-500 fixed
test pairs, with full-sequence tests on about 4-6 previously untuned sequences
if access and runtime permit. These are resource targets, not sample-sufficiency
claims or guaranteed dataset availability. Prefer several distinct sequences/sites
over many overlapping windows from one route.

Use whole-sequence/site partitions. All repeated generations, perturbations and
support windows belonging to a physical pair/site remain in one partition. Fix
the split before looking at test outcomes. If there are too few independent
sites, state that the result is preliminary rather than manufacture confidence
intervals from thousands of correlated frames.

Retrieve a substantially broader candidate pool than the old top-12 cohort, log
all failures/rejections, and retain the natural stream separately from deliberately
stratified hard examples. Evaluation strata include low overlap, repeated structure,
viewpoint reversal, sparse scans and local odometry error. Synthetic corruptions
are a controlled supplementary test, not a replacement for real hard cases.
Synthetic negatives cannot establish a natural false-acceptance rate.

Data choices: KITTI 08-10 are candidates for new task-level holdout, subject to
our own usage audit and checkpoint binding. MulRan/HeLiPR can add repeat visits
or heterogeneous sensors; they are not automatically unseen to RAP. The RAP
paper lists KITTI, KITTI360, MulRan, Boreas, Spires and HeLiPR in training data
and describes exclusions for KITTI 08-10. Paper-level exclusions are not proof
about our local checkpoint. [RAP data protocol](https://arxiv.org/html/2512.01850v1).
[HeLiPR](https://sites.google.com/view/heliprdataset) requires a download request;
access/setup time must be budgeted. Shared routes across HeLiPR and MulRan are
not independent sites. No large download is started during this planning turn.

With public-data access confirmed, the preferred scope is one main repeat-visit
dataset plus one independent external environment, not downloading every listed
dataset. MulRan can provide the main multi-route pool; selected sessions from
[NCLT](https://robots.engin.umich.edu/nclt/) are a candidate external stress test
for repeated traversals and environmental change. Verify timestamp, motion
compensation, frame conventions and GT adequacy before choosing thresholds.
Different NCLT sessions remain the same physical campus and are not independent
sites. HeLiPR is an alternative if heterogeneous FOV is chosen as the central
challenge; avoid adding both HeLiPR and NCLT adapters in the first week. Exact
sequences and geographic separation require a data manifest before any fitting.

Primary pair metrics: registration recall at an agreed strict pose threshold
(candidate proposal: 1 m/5 degrees), RTE/RRE distributions, and false acceptance
versus accepted-correct recall, including a reject-all reference. Keep the legacy
5 m/10-degree label for continuity, not as the only success criterion. Report
the population and uncertainty of low false-acceptance estimates; zero observed
failures is not zero risk. Ground-truth uncertainty must be small enough for the
chosen strict threshold.

System metrics: rigidly aligned ATE as a literature-facing primary trajectory
metric, first-pose APE for continuity, camera KITTI drift, catastrophic failures,
accepted-loop coverage and runtime/memory. The emphasis change is prospective
and all historical metrics remain visible. Report per-sequence paired differences,
not a single pooled frame average. Fix this metric policy before new runs.

## 7. Required comparisons and ablations

Core pair comparators: frozen single RAP; RAP current best-of-K; RAP's documented
rigidity-based selector if accessible; hand-crafted support scoring; a same-input
small MLP without temporal support; proposed evidence encoder. Add identity and
odometry GICP/ICP and KISS-Matcher. GeoTransformer is desirable if its environment
and weights are available within one day; otherwise mark it missing, not silently
replace it with a weaker method.

Core system comparator: KISS-SLAM, plus the current RAP-SLAM default and the new
module in the identical frontend/backend. Distinguish native-system comparisons
from controlled registrar swaps. Keep LiDAR-only input budgets comparable; a
LiDAR-inertial method may be contextual but not an identical-input comparator.

Minimum causal ablations: no temporal support; hand-crafted versus learned support;
pooled submap versus disjoint support; K=1 versus K=4 at fixed and matched-cost
budgets; no abstention; local support-motion perturbation. Do not add all optional
modules or a full Cartesian product. Require about five well-motivated tables or
plots answering distinct questions, not a nominal number of experiments.

Runtime accounting must include feature/support construction, extra scans, RAP
samples and decision time. Compare equal input count and equal compute envelopes
where possible. A multi-sample method beating single-shot ICP is not enough.

## 8. Schedule and decision gates

| Days | Work after agreement | Deliverable / stop condition |
|---|---|---|
| 1-2 | Closest-paper audit, source/data split checks, 100-200-pair headroom pilot, baseline install | Stop if no oracle headroom, no discriminative support or infeasible data access. |
| 3-4 | Cache hypotheses/support evidence; implement only the small ranking/abstention head | Exact identities and independent request seeds; no test tuning. |
| 5-6 | Train on fixed split, compare to hand-crafted score and equal-data submap baseline | Retain only if improvement transfers to validation sequences and is not merely extra compute. |
| 7 | Freeze method and validation choices | One-week outcome: a tested method direction and pilot, not a promised journal-ready paper. |
| 8-10 | Locked held-out pair evaluation and controlled full-sequence tests | Log every failure; no changing thresholds after results. |
| 11-12 | Mechanism ablations, strong baselines, repeated stochastic seeds where relevant | Separate selection, input-context and compute effects. |
| 13-14 | Inspect failure cases, reproducibility package, decide readiness or further work | Assess novelty and meaningful metric gains before writing resumes. |

Suggested development targets for discussion: at least 5-10 percentage points
strict registration-recall gain on the declared hard slice at comparable false
acceptance; a positive aligned-ATE trend on most held-out sequences without new
catastrophic failures; a bounded, reported compute cost. These are ambitions and
decision criteria, not forecasts. A 0.01 m change on an easy sequence is unlikely
to carry the paper; a reproducible hard-case improvement may, if supported by a
clear method and strong comparisons.

## 9. Readiness standard and open decisions

A stronger submission needs one distinct technical problem, a method whose
essential mechanism survives ablation, strong contemporary comparisons, a
credible held-out evaluation and a clear benefit-cost boundary. It does not need
every ROS feature, a new sensor or a larger stack of named modules. If the two-week
study fails these tests, honestly narrow or extend the project rather than label
it CAS Zone 2-ready.

Confirmed: single RTX 5070, public data can be acquired, difficult-loop reliability
is the preferred target. The owner subsequently clarified that 1-2 weeks is the
direction-validation window, not a hard end to experiments. The operational
[HL-V1 protocol](HARD_LOOP_EXPERIMENT_PROTOCOL_V1.md) now fixes the initial pilot,
data roles and decision gates and supersedes prospective details in this draft.
Its conditional training annex will be frozen only after a recorded pilot GO.
Field/journal selection should follow the demonstrated contribution. Do not
assign a current CAS zone to a journal without checking its edition and category.

No new algorithm, training, downloads, submissions or messages to paper authors
were performed in this research turn. Existing manuscript drafts are preserved
as evidence summaries but are not the active task.
