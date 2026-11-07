# Next research decision after F2, R0, G0 and G1

2026-09-28. The owner requested brainstorming followed by a serious next
strategy decision. This record supersedes the immediate flow-guidance
engineering suggestion in `../NEXT_MECHANISM_MEMO.md`: **do not implement a
guided RAP sampler yet**. First test whether a distinct, physically grounded
visibility signal is informative and usable on the saved difficult pairs.
No positive algorithmic result or new method is claimed here.

## What the evidence permits

E0 arm A has a validated system engineering transfer on KITTI07/09/10.
F2 S has no development mechanism signal; its two fixed controls and the
older support/pooling routes do not justify more support or gate sweeps.
R0 local ICP and G0/G1 external global registration recover none of the
41 KITTI08 positives lacking a strictly correct native K4 candidate.
Correct-pose rejection (13/75 on08 under native N) and ten incorrect
accepts are separate unsolved problems.

The read-only `error_axes.json` rechecks selected N/R4 transforms against
the original GT error magnitudes for every saved pair. On 08, 26/41
K4-unavailable positives have selected-pose translation error <=2m and
37/41 rotation error <=5deg. The largest absolute translation component
is source-frame x/y/z on 23/8/10 pairs; median absolute components are
1.068/0.965/0.577m. This is not a single-axis calibration correction.
Eight of ten native incorrect accepts also lie within2m, so simply widening
the strict label or gate would mix desired and incorrect poses. These are
post-hoc observed-development diagnostics, not prospective efficacy.

## Brainstormed routes and disposition

| Route | Potential | Why it is or is not next |
|---|---|---|
| More generations, support pooling/projection, selector or gate tuning | Could change a few saved outcomes | F2/SC/PG failures and 41/75 absent candidates on08 make this an outcome-driven rescue; stop. |
| Another off-the-shelf local/global matcher | Independent candidates | R0/G0/G1 produced no missing-candidate recovery under their fixed tests; no blind parameter sweep. |
| Train a residual or adapt RAP | Could change the model prior | Upstream training/data curation are not released; cohort leakage, fresh-data and compute costs are substantial. Defer until a distinct training question is justified. |
| Direct geometric gradient in RAP's flow | Could alter candidate creation | Current gate rejects true poses and accepts wrong ones; a naive distance gradient may reinforce these errors. `sample_rectified_flow` uses inference mode. Visibility and flow guidance have prior art. Do not launch GPU work without an information test. |
| Sensor-ray visibility information test | Separates observed surface, occlusion, free space and unobserved directions; may expose a translation signal absent from point-to-point ICP | Best near-term *falsifiable* question, CPU-only and GT-free when scoring. It is a feasibility test of information, not a novelty or system claim. **Select V0.** |
| More backend/front-end tuning | Could improve aggregate metrics | E0 transfer is already frozen; E1 found no successor. It does not address F2's missing candidates. Defer. |

## Decision and execution boundary

**V0 is a prospective sensor-ray visibility/observability audit on the exact
F2 00/08 saved cohorts.** Its job is to decide whether there is a usable
geometric direction for pose creation before designing any flow guidance.
Implement a single range-ray model on the full corrected anchor scans, with
distinct *surface agreement*, *free-space contradiction*, *occlusion* and
*unobserved* counts and explicit comparable-ray coverage. Validate sensor
convention and identity/known-transform cases synthetically. Freeze the
exact angular/range tolerances, score, deterministic points, candidate
translation perturbations, common comparator, source/raw hashes, cost and
decision margins **before** evaluating real labels. Scoring and local search
must use no GT. Seal all candidate scores/poses before evaluator-only GT.

Evaluate per sequence and stratum, especially 08's 41 missing-candidate
positives, 13 correct rejections and ten wrong accepts. Require an
*executable* GT-blind local search to create strict candidates and avoid
new incorrect accepts; favorable scores at the GT pose alone are
insufficient. Keep the existing F2 gate unchanged and report correct
accepts, wrong accepts and confusers separately. Compare the same fixed
search using ordinary symmetric nearest-neighbor geometry so any value
from sensor visibility is distinguishable from generic local refinement.
This V0 test is post-hoc development, not a new method claim or independent
confirmation. If ray support is sparse, the energy is uninformative, or the
executable search cannot pass its predeclared gains/safety/cost margins,
**stop visibility-guided flow**. Do not tune bin widths or thresholds after
the result.

Only a V0 pass licenses an isolated RAP sampling engineering preflight:
reproduce native sampling exactly when guidance is disabled; preserve RNG,
precision, hook and gauge behavior; prove finite stable updates within a
fixed GPU cap. The later efficacy screen must beat native RAP **and** the
same visibility search applied after sampling, plus R0/F2 controls, at
reported point and time budgets. A credible development gain then needs a
fresh confirmation cohort and system-level graph impact before any thesis
method claim or production default change.

If V0 fails, return to a separately scoped model/data-convention question
before considering training. Do not rebrand the failed visibility score as
a different gate. Preserve E0 as the engineering reference meanwhile.

## Source and novelty limits

Visibility/free-space consistency was already studied by
[Huber and Hebert](https://www.cs.cmu.edu/~dhuber/papers/cvbvs2001.pdf).
[ODIN](https://openaccess.thecvf.com/content/CVPR2024/html/Jin_Multiway_Point_Cloud_Mosaicking_with_Diffusion_and_Global_Optimization_CVPR_2024_paper.html)
already couples overlap estimation with diffusion-aided registration;
[FUSER](https://github.com/Jiang-HB/FUSER) uses multiview registration and
diffusion refinement; [RAP](https://arxiv.org/abs/2512.01850) already
supports multiview flow and rigidity forcing. Gradient guidance in flow
models is also established in [flow-prior inverse-problem work](https://papers.nips.cc/paper_files/paper/2024/hash/698570ae5ec88e07e9f4547f831b4593-Abstract-Conference.html).
Thus neither visibility scoring nor flow guidance is novel by itself.
The closest-method and code audit must identify a RAP-specific mechanism
and measured benefit before any novelty wording. This source check is
focused, not exhaustive clearance.

This decision launches no V0 outcomes, GPU inference, training, production
change or Git sync. The next concrete action is to draft and freeze the
exact V0 protocol and synthetic ray-model checks, then execute its bounded
CPU information screen once. Completed prior experiment directories stay
immutable.
