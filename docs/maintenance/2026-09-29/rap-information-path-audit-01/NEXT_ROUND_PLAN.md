# Next-round plan: P0 point-selection information preflight

Written 2026-09-29 for the next conversation. **Planning record only:** P0
has no frozen protocol, runner, output bank or result. No P0 experiment was
started in this conversation. Begin with `AGENTS.md`, this plan, the adjacent
`REPORT.md`, C1's protocol/report and F2's protocol/report. Treat completed
C1/F2/C2 and later banks as immutable.

## Why this question

The source audit found an actionable input-path difference without proving
its effect. F2 uses 0.4 m voxels, fixed random keypoint caps, and miniSpinNet
patches supported by those already capped points. Local upstream `demo.py`
defaults to 0.25 m voxels and FPS; `SampleProcessor` describes FPS keypoints
against the **pre-FPS voxel cloud**. The paper reports 0.25 m for KITTI and
a 5 m descriptor radius. C1 found poor miniSpinNet top-1 information on
hard08 native-K4-unavailable positives, while C2 confirmed the model uses
the feature channel. A paired input-information test is therefore the next
bounded question. It is not a claim that preprocessing caused the failures.

## Planned sequence

1. **Resolve and freeze the comparator.** Inspect the local upstream
   `SampleProcessor` and FPS functions, including outlier removal,
   pre-FPS safety cap, deterministic seed, point ordering, voxelization
   and feature patch support. Define exactly one upstream-inspired arm:
   0.25 m voxelization, FPS keypoints, full pre-FPS voxel support for
   miniSpinNet, radius 5 m. Keep the six per-part keypoint counts equal to
   F2's `[2000,1000,1000,2000,1000,1000]` so both arms have 8000 model
   input points. This fixed-count arm is **not** the paper's adaptive
   allocation; state that limitation. If exact counts are impossible on a
   scan or FPS resources are unsuitable, stop and report before efficacy
   scoring. Do not silently change budgets, support density or seeds.
2. **Engineering preflight without labels.** Use an identity-fixed small
   sample selected from the saved F2 order before reading outcomes (for
   example the first four pairs per sequence). Verify coordinate frame,
   corrected raw scan identity, counts, finite/nonzero descriptors, fixed
   radius, repeatability, and time/memory. Confirm the F2 control reads
   its saved points/features exactly. The preflight can reveal defects
   but must not select a favorable comparator. Save its own source and
   input hashes and independent checks.
3. **Prospectively freeze the information protocol before full generation.**
   Use all 200 exact F2 observed-development pairs (100 each on 00/08),
   with the unchanged two 2000-point anchors for F2 and the matched new
   anchors for P0. Freeze the exact comparator implementation, allocation,
   796 referenced corrected raw scan identities, saved F2 points/features,
   checkpoint hashes, C1 evaluator/GT identities, controls, decision
   margins, wall/GPU/artifact caps, and a separate validator. The runner
   may hash GT files for identity but cannot parse GT or labels before
   the complete point/feature bank is sealed. Leave `INCOMPLETE` on any
   partial run.
4. **Information evaluation after the seal.** Reuse C1's source-to-target
   transform, exact 1 m geometric eligibility, normalized-descriptor
   top-1 recall and 16 coordinate-permutation controls. The pair is the
   unit. Primary fixed group: the 41 hard08 positive pairs with no strict
   native F2 N/K4 candidate; report eligible counts and the subset with
   >=10% eligible source points for both arms. Compare paired
   true-minus-shuffled conditional recall on a predeclared common set,
   and separately report coverage changes. Include 00 and native-K4-
   available strata as controls. Freeze a material paired margin before
   seeing P0 features (recommended: >=10 percentage-point median gain on
   hard08 common-eligible pairs, >=2/3 positive signs, adequate group
   size; guard ordinary-pair information against material regression).
   Do not fit the margin to output.
5. **Independent validation and stop.** Independently check frozen hashes,
   every point/feature bank identity, all pair-level correspondence/control
   metrics, cohort arithmetic and decision. If the predeclared material
   information signal fails, retire this **exact** input-convention arm;
   do not sweep voxel size, FPS seed, count, radius or gate. If it passes,
   design a separate frozen RAP-generation test with identical K4 noise,
   weights, steps, selector and gate before claiming any registration gain.

## Separation and interpretation

- Preserve F2's six scans, frames, labels, 5-step native settings, model
  checkpoint and common gate. P0 measures input information; do not run
  RAP generation, acceptance, graph optimization, training or a default
  change as part of P0.
- The comparator jointly changes voxel scale, keypoint placement and
  descriptor patch support. A positive P0 cannot identify which component
  caused the gain. Do not describe it as paper reproduction or a novel RAP
  mechanism. It only licenses the separately frozen generation test.
- The paper's KITTI 08–10 exclusion is about the reported v2 recipe; exact
  membership of the local 12-layer checkpoint remains unknown. F2 uses a
  stricter correctness threshold and a different pair cohort than the
  paper. S1 has already rejected the fixed five-to-ten-step route.
- Prior negative decisions C3–C6 and I1, E0's engineering transfer,
  manuscript pause, no production/default edit and no Git sync persist.

## Next-conversation first action

Read `AGENTS.md` and these two audit files, then inspect the exact upstream
FPS and feature-support implementation. Write and freeze P0's engineering
preflight/protocol, runner and independent validator before producing new
real-pair outputs. The owner has asked to continue the research search; no
new permission request is required for this bounded, reversible work.
