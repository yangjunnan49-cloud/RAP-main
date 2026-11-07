# C0 conditioning source and checkpoint audit

2026-09-28. This is a read-only source/weight check after S1's negative
five-versus-ten-step development screen. It is not a new registration result.

## Observations

- RAP-SLAM supplies per-point 32-D miniSpinNet features for all six F2/S1
  parts (`rap_backend.py:preprocess`; `structured_motion_dev.py:build_batch`).
  RAP's `PointCloudDiT` config enables `local_feat_concat_on`, and
  `embedding.py` concatenates those features with coordinate, noise and
  scale embeddings. Thus the local feature channel is connected in source.
- `FeatureExtractor._load_checkpoint` catches exceptions and uses
  `strict=False`; `extract_features` catches extraction errors and returns
  zero vectors. A silent load/extraction failure was therefore a concrete
  issue to rule out before proposing model or data changes.
- The safe, read-only [checkpoint audit](checkpoint_audit.json) loaded
  `mini_spinnet_t.pth` with `weights_only=True`. All 58 `Desc.` keys exactly
  match the instantiated miniSpinNet's 58 state keys, all shapes match, all
  tensors are finite, and `strict=True` load succeeds. The checkpoint SHA256
  is `daf910b6e2a79c4346a6ef8eeb18b56ffc15b552cc82af091b8b6c0a18116eef`.
  S1's runner also asserted every regenerated scan's features were finite
  and contained a nonzero entry. This rules out a wholly unloaded
  checkpoint or all-zero feature fallback in the audited S1 run. It does
  not prove every descriptor is informative, or every feature extraction
  call avoided a partial failure.
- The released training and data-curation code remain listed as unreleased
  in the local README. A KITTI feature-domain mismatch is a hypothesis,
  not an established cause. The exact model training membership cannot
  be inferred from this source audit.

## Decision and next bounded question

Stop configuration-level rescue of F2 (structured projection), V0 (ray
score), D0 (early checkpoint) and S1 (ten steps). The next useful question
is **whether the actual six-part KITTI input contains discriminative
cross-visit local feature information, especially on 08 positives where
native K4 lacks any correct candidate**. Do not start training or change
the model/default from C0.

Run one separately frozen C1 descriptor-information audit on the exact F2
00/08 observed-development pairs. Regenerate miniSpinNet descriptors for
the saved F2 points and assert exact point/count/condition identity; keep
all descriptors, scan identities and preprocessing diagnostics in a bank
sealed before evaluator GT. For the two anchor scans of each pair, use GT
only after the seal to establish which sampled points have a geometric
counterpart within a predeclared physical radius. Measure top-1 descriptor
match correctness on those eligible points, and report eligible coverage
separately. Break out 00/08, stratum and native-K4 candidate availability;
include a within-pair shuffled-descriptor control. Preserve pair-level
results and report uncertainty by pair, not by treating thousands of points
as independent samples. This is an information diagnostic, not an
executable registration method or a causal test of model use. Freeze exact
radius, normalization, control permutation, cost and validator before
computing descriptors. Use its result to decide whether a small paired
model-use intervention is justified. No automatic training campaign.

The current positive evidence remains E0's engineering transfer on held-out
system sequences. There is no validated RAP algorithmic improvement from
F2/V0/D0/S1. Preserve the manuscript pause, prior stops and no-Git-sync
boundary.
