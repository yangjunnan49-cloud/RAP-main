# Online registration comparator — next-stage design, not frozen or run

Historical design now executed as `online-geotransformer-01/`: read its
REPORT/PROTOCOL/freezes/amendments/seals/validation for the exact implemented
one-arm scope and validated negative result. Isolated feasibility passed.
The next current task is `online-geometry-consistency-01/NEXT_ROUND_PLAN.md`;
do not resume this comparator or choose a full-density rescue after outcomes.

The validated [joint-loop diagnostic](joint-loop-oracle-01/REPORT.md) establishes
an ATE opportunity on current exposed-transfer edges, driven mainly by 09.
It does not solve ter regression or establish a new RAP method. The failed
[fixed interpolation screen](dense-propagation-screen-01/REPORT.md) stays stopped.

## Concrete next task

Audit one official GeoTransformer KITTI release in an isolated dependency
location, then preflight transform direction and safe strict checkpoint loading.
Pin source commit and downloaded checkpoint SHA before executing any real pair.
Do not alter the working RAP environment or accept silent missing-weight loads.
An old-version requirement is a compatibility question, not permission to
replace the RAP runtime. Acquisition and isolated compatibility work now live
in `geotransformer-feasibility-01/`; consult its receipts for current status.

Primary sources checked on 2026-10-05:

- [Official repository](https://github.com/qinzheng93/GeoTransformer) lists a
  KITTI checkpoint and testing path. Its documented tested stack is Python3.8,
  PyTorch1.7.1 and CUDA11.1; local RAP is Python3.10/PyTorch2.7/CUDA12.8.
- [Release page](https://github.com/qinzheng93/GeoTransformer/releases) lists
  pretrained odometryKITTI weights. Exact downloadable asset identity and
  contents are not yet verified; API opens failed and the asset list did not
  render in the source fetch. Do not infer a verified checkpoint SHA from this.
- [Setup](https://github.com/qinzheng93/GeoTransformer/blob/main/setup.py) builds
  a compiled extension (listed subsampling/neighborhood sources are CPU C++).
  Compatibility with the existing compiler/Torch remains untested.
- [Requirements](https://github.com/qinzheng93/GeoTransformer/blob/main/requirements.txt)
  pins Open3D0.11.2; installation instructions are not a validated local setup.
- [KITTI config](https://github.com/qinzheng93/GeoTransformer/blob/main/experiments/geotransformer.kitti.stage5.gse.k3.max.oacl.stage2.sinkhorn/config.py)
  specifies initial voxel0.3m, no test point limit, and paper evaluation2m/5deg.
- [Dataset source](https://github.com/qinzheng93/GeoTransformer/blob/main/geotransformer/datasets/registration/kitti/dataset.py)
  declares train00–05, val06–07, test08–10. This declaration does not by itself
  authenticate every downloaded weight's actual training membership. 07 is
  a declared validation sequence, so it is not an unseen model-domain claim.

No GeoTransformer source/checkpoint match was found in the two working
repositories using name-based file search excluding archives. Other system
locations were not inventoried; this is not a universal absence claim.

## Proposed comparison scope

Use all 71 saved online E0 A attempts and all six sequences; do not select
only the ten known-wrong 09 accepted pairs. Reuse allowlisted endpoint/attempt
IDs from the sealed prior audit. Preserve selected RAP outputs as the reference.
GT/evaluator labels must not enter construction or selection.

First seal exact input clouds. RAP preprocess uses voxel/outlier operations and
a fresh fixed-seed cap per scan; its input points can be reconstructed without
RAP inference from corrected raw scans and frozen configuration, but must be
independently verified rather than assumed identical. The original per-
generation flow RNG was shared in recorded order; do not pretend an arbitrary
new seed is exact generation replay. No new RAP generation is needed for a
saved-output comparator.

Predeclare input roles before results: an equal-anchor-point arm tests the
same capped **4000 points per scan** (up to8000 per pair); an official-recipe arm tests the same corrected
raw observations using GeoTransformer's prescribed preprocessing. If both
are used, report their different point/compute budgets explicitly, and treat
the latter as an engineering comparator, not a same-compute causal control.
Do not choose whichever arm looks better after observing pair outputs.

Separate three claims in the eventual frozen protocol:

1. Candidate poses on all 71 attempts: strict1m/5deg, continuous errors,
   confidence and runtime, sealed before GT; paper2m/5deg can be supplementary.
2. Fixed-current-edge diagnostic: replace the existing 58 accepted RAP edge
   poses with comparator predictions while keeping graph endpoints/base noise
   fixed. This isolates graph response and is not a gated deployable system.
3. Executable common-gate system: evaluate every comparator pose under one
   predeclared common geometry gate, use its admitted edges and explicitly
   defined noise metadata. Report rejection/missing predictions and false
   acceptance; a new common gate must not be tuned on exposed GT labels.

Require a separately frozen exact implementation, independent validator,
synthetic transform-direction test, deterministic input/feature preflight,
checkpoint identities and prospective trajectory/safety/resource criteria
before full outputs. Use the existing six sequences as observed development;
reserve a distinct eligible trajectory cohort for later method confirmation.
No real-pair comparator protocol or inference bank is frozen yet. The earlier
2000-per-scan wording was a planning error, corrected from E0 configuration and
the backend's per-scan cap before any GeoTransformer pair output. This does not
revise any frozen experiment or measured outcome.

A strong matcher benefit would locate a recoverable information path and set
a baseline. It would not constitute a RAP contribution. Only then design one
RAP mechanism with direct-matcher and equal-budget controls; explain why it
differs from the stopped structured projection/support-transport routes.
No fine-tuning, retraining, production/default edit, manuscript or Git sync.
