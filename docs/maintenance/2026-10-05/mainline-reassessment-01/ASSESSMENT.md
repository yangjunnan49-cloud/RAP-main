# Return to the RAP-SLAM mainline — 2026-10-05

Status: evidence review and proposed solutions only. The owner closed weekly-
meeting preparation and requested renewed mainline diagnosis. No experiment,
synthetic preflight, inference, training, new metric computation, protocol
freeze or bank was produced. The latest experimental boundary remains the
[validated system audit](../../2026-09-29/system-opportunity-audit-01/REPORT.md).

## Diagnosis

The objective remains an original RAP-centred trajectory improvement for the
master's thesis. E0 A is a positive engineering reference, not a new RAP method.

| Saved E0 A group | Odometry ter | Full ter | Odometry aligned ATE | Full aligned ATE |
| --- | ---: | ---: | ---: | ---: |
| 00/05/06 | 0.374547% | 0.388718% | 1.943835 m | 1.460664 m |
| 07/09/10 | 0.477262% | 0.505615% | 0.778065 m | 0.721480 m |

These are previously validated arithmetic means, not new results. Three
problems must be distinguished:

1. **System regression:** loops lower global aligned ATE but raise relative
   segment ter. On 06 all twelve accepted poses meet the strict pair label,
   yet ter rises about 0.047577 percentage points. On 09 ten accepted poses
   have 3.64–4.13 m translation errors, yet ATE improves while ter rises
   0.074208 points. Pair correctness alone predicts neither outcome.
2. **Hard candidate absence:** F2 has 41/75 KITTI08 positives without a
   strict K4 candidate; 37 of these miss translation while meeting the
   rotation threshold. F2 uses balanced six-part/8000-point/K4 inputs;
   E0 uses online K1/4000-point inputs. This is a candidate-bank diagnosis,
   not a cause of E0's system regression.
3. **Contribution gap:** no tested RAP-specific mechanism establishes the
   required original trajectory gain. Mechanism-use observations and
   engineering corrections cannot substitute for it.

Best one-at-a-time same-endpoint GT replacements improve sequence ter by at
most 0.007351 percentage points. This reduces the immediate priority of
isolated accepted-pose refinement, but does not bound joint replacement,
additional edges or different candidate exposure. E0 A odometry ter is
already slightly below KISS-SLAM full-system ter on 07/09 and close on 10;
a controlled local-odometry deficit has not been demonstrated. Sequence10
has no accepted edge; its eleven attempted pairs are GT-far under the saved
15 m criterion. Missing useful loops remain unknown because the complete
retrieval shortlist is absent.

C2 shows feature-channel reliance. C1/P0/C3/I1 fail their fixed material
information gates; they do not prove a descriptor cause or that retraining
would solve translation ambiguity. Exact local 12-layer RAP checkpoint
training membership remains unknown. Preserve all stopped step-count,
ICP, support-mask, donor, structured-generation and support-pose routes.

## First solution: fixed dense correction interpolation

The native source applies T_s = C_a O_s, with C_a = K_a inv(O_a) held
constant until the next keyframe. Its SHA-256 matches the audit freeze:
`b6583705a13e57caba724cdfeb0d7eba4b289ec75e39cf239e0546ab9e4d297e`.
For two scans in one interval, inv(T_u) T_v = inv(O_u) O_v; at a boundary
the relative motion additionally contains inv(C_a) C_b. Correction changes
are concentrated at boundaries. This is an implementation fact and an
untested causal hypothesis. Smoothness does not guarantee accuracy.

Use exactly the [existing planned comparator](../../2026-09-29/system-opportunity-audit-01/NEXT_ROUND_PLAN.md):

`C_s = C_a Exp(alpha Log(inv(C_a) C_b))`,
`alpha = (s-a)/(b-a)`, `T_s = C_s O_s`.

Hold odometry, accepted loops, graph solution and optimized keyframe poses
fixed. This is retrospective offline reconstruction. Compare native P,
interpolated S and odometry. Freeze a separate protocol, runner, validator,
source/input identities and costs after synthetic SE(3) preflight; seal all
six GT-free trajectories before evaluator GT. Do not edit production or old banks.

Keep the planned gates: each group's mean ter improves by at least 0.01
percentage points versus P; each group's mean ATE worsens at most 2%;
each sequence's ter worsens at most 0.01 points and ATE at most 5%; sequence10
remains equal within 1e-5 pose-entry error. CPU-only caps: 20 minutes,
2 GiB RSS, 500 MB artifacts. Report all six sequences.

A pass establishes an engineering benefit of this reconstruction, not
exclusive causation or RAP originality. A failure stops this exact route
without an interpolation-space/weight sweep. Non-keyframe correction and
interpolation have [prior art](https://arxiv.org/abs/2009.08724).

## Subsequent solutions are conditional

After that screen, select one question about remaining trajectory headroom.
Do not launch several speculative modules together.

- If substantial ter regression remains, optionally freeze a new evaluator-
  only diagnostic jointly replacing all existing accepted poses by same-
  endpoint GT poses while fixing graph settings and reconstruction. This
  would test correlated current-edge pose headroom left unresolved by
  one-edge interventions. It is neither a deployable method nor an upper
  bound on all SLAM improvements. It is proposed, not selected or run.
- If accepted-pose headroom is material, use one official outdoor matcher
  comparator, initially GeoTransformer subject to compatibility, checkpoint
  and training-split checks. Compare exact system inputs and trajectory
  effects as well as pair accuracy. A direct matcher gain is a baseline,
  not a RAP contribution. Only a measurable cross-visit information path
  justifies a distinct RAP-side candidate mechanism with equal-data/compute
  direct-matcher controls. Do not revive the stopped fixed refinement arms.
- If current accepted poses have little relevant headroom, investigate
  missing graph-useful exposure before replacing retrieval. Complete future
  candidate logging would be necessary; saved sequence10 attempts cannot
  answer retrieval recall. Further online runs require a separate protocol.

RAP joint generated geometry versus the single pair-pose system interface
remains a potential research question, not a selected solution. The
[RAP paper](https://arxiv.org/html/2512.01850v2) already describes multi-view
registration and downstream PGO use. F2 per-step motion coupling and M1
support-pose reuse already failed. A richer factor must identify additional
measurable information beyond those tests and avoid treating correlated
outputs as independent evidence. More edges, a multi-view call or calling
dispersion uncertainty does not establish originality.

No fine-tuning/retraining remains the standing position. Reconsider only
after a specific recoverable mechanism, provenance and strong fixed controls
demonstrate a need. All six audit sequences are exposed for new research
choices; later method confirmation needs a separately reserved eligible cohort.

## Review record and next step

Read AGENTS.md, latest audit protocol/report/plan/handoff/status/freeze/seal/
validation, literature review, breakthrough reassessment, meeting handoff
and historical stops. Inspected both worktrees: RAP-main remains
`codex/meeting-20260930` at `4055d92`; RAP-SLAM remains
`codex/e0-f1-20260926` at `6d3f2d2`. Existing dirty work is preserved.
Snapshot directory and preservation manifest are present; archived payload
and the full audit bank were not rehashed. Checked primary
[KITTI](https://www.cvlibs.net/datasets/kitti/eval_odometry.php), RAP and
non-keyframe-correction sources; no exhaustive novelty clearance is claimed.

Exact next implementation task: prepare the separate fixed propagation
protocol, runner, independent validator and synthetic preflight, then freeze
before real trajectory generation. None of these new artifacts exists yet.
Manuscript pause, immutable banks, no production/default edit, no commit
and no Git sync persist. Continuity documents are the only changes this turn.
