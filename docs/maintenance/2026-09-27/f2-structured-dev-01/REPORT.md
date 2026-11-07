# F2-V1 structured-motion generation development screen — final report (2026-09-27)

Protocol: [PROTOCOL.md](PROTOCOL.md) (frozen before generation). Decision:
**NO_DEVELOPMENT_MECHANISM_SIGNAL**. Independent validation:
[validation.json](validation.json) (passed, 4000 valid generations, exact
evaluator-row reproduction). One named validator amendment:
[AMENDMENT_01.md](AMENDMENT_01.md) (validator-only center-convention fix; no
artifact, metric, or decision change).

This is an observed-development screen on two fixed, previously observed
cohorts (KITTI 00 discovery 100 pairs from HL-V2, KITTI 08 confirmation 100
pairs from SC-V1.1; 25 per stratum each). It is not independent confirmation,
not a first-tier claim, and not a general impossibility proof for structured
motion constraints. All HL/SC/PG stops and the manuscript pause persist. No
production code, default, or Git state was changed.

## Arms and gates (as frozen)

- **N**: native six-part generation (anchor + 2 supports per visit), no group
  projection.
- **F**: N's generations with group projection applied to the final endpoint
  only (decode-only arm; reuses N trajectories).
- **S**: per-step group projection of the raw clean endpoint onto the two
  rigid visit groups transported by saved causal local LiDAR motions.
- **P**: equal-point pooled control (two 4000-point visits, support points
  transported by the same motions; no structure).
- **A**: anchor-only reference (two 2000-point anchors).
- K=4 per pair, per-pair seeds `sha256('F2|structured-motion|kitti|{seq}|{i}|{j}|{k}')`.
- Selection: official step-mean rigidity RMSE on the raw trajectory
  (R4 = argmin over valid generations); enforced projection residuals never
  serve as the score.
- Common gate: seed-42 geometric backend (voxel 0.4, cap 4000) on the
  corrected anchors; accept iff overlap >= 0.7 and mean distance <= 2.5 m
  (thresh 1.0 m).
- Data convention: >=1.5 m filter, 0.205 deg vertical correction, voxel 0.4,
  statistical outliers 20/2.5, caps [2000,1000,1000,2000,1000,1000]. Saved
  historical local poses re-verified exactly equal to odometer recomputation
  (max delta 0.0 over all 400 support links).

## Results

All 200 pairs produced 4 valid generations in every generation arm (4000
valid generation records; zero failures). Confuser accepts: 0/25 for every
arm on both sequences.

### KITTI 00 (discovery role, observed development)

| Arm | Strict success /75 | Selection recall | Incorrect accepts | Accepted | Mean clipped positive error |
|---|---:|---:|---:|---:|---:|
| N | 49 | 0.653333 | 1 | 24 | 1.472846 |
| F | 47 | 0.626667 | 2 | 24 | 1.681532 |
| S | 49 | 0.653333 | 2 | 24 | 1.571764 |
| P | 54 | 0.720000 | 1 | 24 | 1.343208 |
| A | 50 | 0.666667 | 2 | 24 | 1.477135 |
| S-OR4 (oracle diagnostic) | 53 | 0.706667 | 1 | 24 | 1.334977 |

Ordinary-stratum recall: N 1.00, F 0.92, S 0.96, P 1.00, A 0.96.

### KITTI 08 (confirmation role, observed development)

| Arm | Strict success /75 | Selection recall | Incorrect accepts | Accepted | Mean clipped positive error |
|---|---:|---:|---:|---:|---:|
| N | 30 | 0.400000 | 10 | 27 | 1.579930 |
| F | 25 | 0.333333 | 8 | 25 | 2.071347 |
| S | 30 | 0.400000 | 10 | 27 | 1.691330 |
| P | 30 | 0.400000 | 9 | 26 | 1.713966 |
| A | 30 | 0.400000 | 10 | 27 | 1.647875 |
| S-OR4 (oracle diagnostic) | 35 | 0.466667 | 10 | 26 | 1.420955 |

Ordinary-stratum recall: N 0.60, F 0.60, S 0.60, P 0.64, A 0.60.

### Condition evaluation (per-sequence signal requires all eight)

| Condition | 00 | 08 |
|---|---|---|
| C1 S vs N: recall gain >= 3pp | FAIL (+0.00pp) | FAIL (+0.00pp) |
| C1 S vs N: clipped error <= 0.95x | FAIL (1.572 vs 1.399) | FAIL (1.691 vs 1.501) |
| C2 S vs F: recall gain >= 3pp | FAIL (+2.67pp) | PASS (+6.67pp) |
| C2 S vs F: clipped error <= 0.95x | PASS | PASS |
| C3 S vs P: recall gain >= 3pp | FAIL (-6.67pp) | FAIL (+0.00pp) |
| C3 S vs P: clipped error <= 0.95x | FAIL (1.572 vs 1.276) | FAIL (1.691 vs 1.628) |
| C4 incorrect accepts <= N's | FAIL (2 > 1) | PASS (10 = 10) |
| C4 ordinary recall loss <= 2pp | FAIL (4.00pp) | PASS (0.00pp) |
| C5 engineering caps | PASS | PASS |

Sequence signals: 00 False, 08 False. Final decision:
**NO_DEVELOPMENT_MECHANISM_SIGNAL** ([decision.json](decision.json)).

## Sensitivity arms (observations only, no accuracy claim)

Fixed support-motion perturbations (+/-0.10 m x, +/-1 deg z, left-multiplied
onto the four support links), first five ordinary pairs per sequence, S arm,
K4 (20 generations per sign per sequence). Deviation of the perturbed
selected transform from the unperturbed one:

- 00: translation median 0.0824/0.0847 m, max 0.1579/0.1601 m; rotation
  median 0.0229/0.0204 deg, max 0.0705/0.0679 deg (minus/plus).
- 08: translation median 0.0976/0.0999 m, max 0.1505/0.1495 m; rotation
  median 0.0308/0.0344 deg, max 0.0571/0.0556 deg (minus/plus).

The mechanism's output is stable at the scale of the injected perturbation.

## Engineering and cost

- Wall: 00 = 1091.2 s, 08 = 1081.1 s, cumulative 2172.4 s (cap 4 h).
- Peak GPU allocated 2.42 GiB both runs (cap 12 GiB); artifacts 5.39 GB
  (cap 20 GiB).
- Native sampler reproduction delta exactly 0.0; reordered S replay delta
  exactly 0.0 (pair 00_24_629). RNG/precision state restoration asserted per
  generation including on an injected exception; no hooks or monkeypatches;
  `sample_rectified_flow` identity asserted unchanged after every generation.
- GT accessed only inside evaluate(), after the per-sequence generation bank
  hash freeze; evaluator GT fields never entered the runner process space
  before that freeze.
- Preflight (first 10 pairs of 00) passed: 160 generations, native/replay
  deltas 0.0 ([00/preflight_validation.json](00/preflight_validation.json)).

## Independent validation

[validation.json](validation.json): passed. 200 pairs, 4000 valid
generations; max independent projected-point delta 1.16e-6; max pose decode
delta 1.60e-5; max constraint residual delta 8.88e-8; max rigidity delta
1.45e-5; gate recomputation delta exactly 0.0; local-motion recheck delta 0.0
(== freeze record); evaluator-only rows reproduced exactly; decision
arithmetic recomputed independently. Validator SHA256 recorded there
(amended copy, F2-AMENDMENT-01).

## Administrative history (execution facts, no outcome impact)

- The freeze was regenerated twice before any generation completed, because
  two runner defects were found only at run startup: (1) `check_freeze`
  treated freeze.json `inputs` keys (sequence names) as file paths;
  (2) a generation-time assertion wrongly expected 2-D point counts. Both
  fixes preceded any completed generation; every freeze recorded identical
  input identities (796 distinct raw scans, max local-motion recheck delta
  0.0). The frozen runner/validator hashes in freeze.json match the executed
  code.
- The first validation attempt stopped on the frozen validator's center
  convention defect; fixed per F2-AMENDMENT-01 (E0-AMENDMENT-01 pattern:
  original frozen file unchanged, amended copy recorded by SHA256).
- GPU runs and validation were launched through detached WSL helper scripts
  (`scripts/maintenance/f2_launch.ps1`, `f2_run.sh`, `f2_validate.sh`;
  execution conveniences with no analysis logic) because this environment's
  tool calls cannot host long-lived processes; run logs are kept alongside
  them (`f2_run00.log`, `f2_run08.log`, `f2_validate.log`). An earlier
  `/tmp`-based logging attempt lost logs to a WSL instance restart; no
  artifacts were affected.
- [PROTOCOL_DRAFT.md](PROTOCOL_DRAFT.md) is a preserved alternative draft
  found in this directory before freeze (stricter arm set and margins,
  mandatory external comparators). It was never frozen or executed; the
  executed PROTOCOL.md governs. The mechanism question (arm comparison under
  equal local motions) is unaffected by that draft's local-motion convention
  concern because all structured arms share the same motions; external
  comparators belong to a later confirmation stage per the research memo.

## Interpretation boundaries

- On these observed development cohorts, per-step group projection (S) shows
  no recall gain over native generation (N), loses to the equal-point pooled
  control (P) on 00, worsens mean clipped error versus N on both sequences,
  and adds one incorrect accept on 00. Final-only projection (F) is worse
  than N on both sequences. The pooled control P, not the structured
  mechanism, holds the best recall on 00 (54/75) — an observed-development
  fact only, not a new selected route.
- This screen does not prove structured-motion constraints fail in general:
  one sampler configuration (K4, five steps), one motion source (saved
  anisotropic-odometry local poses), one point budget, two development
  sequences.
- Per the frozen protocol, a negative decision ends this development route:
  no gate tuning, no arm rescue, no support/motion sweep from this screen.

## Next boundary

Owner decision. Options consistent with the standing discipline: (a) accept
the negative result and retire the structured-motion generation mechanism;
(b) commission a separately scoped question (e.g., why the pooled control
dominates on 00, or the E1/E0-pending first-tier confirmation story). No
automatic follow-on experiment is authorized by this report. The completed
f2-structured-dev-01 directory must not be rerun or overwritten.
