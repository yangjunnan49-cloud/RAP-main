# S0: matched-noise RAP 5→10 step engineering preflight

The local released RAP inference config (`config/RAP_inference.yaml`) and
demo (`demo.py`) default to 10 Euler sampling steps; RAP-SLAM's backend
and F2 use 5. D0 observed that F2's per-step K4 oracle availability
generally rose by the final fifth step, without establishing that extra
steps help. This is a **new, separate source-convention question**, not
a V0/D0 rescue or a claim that the official default is optimal.

Use the exact F2 KITTI00/08 saved-order pair indices [0,25,50,75] in
each sequence, one per fixed stratum; one native generation k=0 per pair.
No outcome-based replacement. Reuse F2's six ordered raw scan inputs,
corrected-data convention, preprocessing caps [2000,1000,1000,2000,1000,1000],
miniSpinNet weights, normalized conditions, saved k=0 noise and model
checkpoint. No GT, strata files or evaluator labels may be parsed by
the runner. Freeze this protocol, runner, independent validator, exact
input/source/checkpoint hashes and eight pair identities before inference.

For each pair, regenerate the six scan points/features under the F2
request-local RNG and IEEE matmul scope; assert points, counts, normalized
conditions, centers and scale reproduce `inputs.npz`. Run the unmodified
RAP native sampler with **5** Euler steps and the saved explicit noise.
Require the saved F2 N0 raw clean-endpoint and noisy-state trajectories
to match within1e-5 maximum, for all eight pairs; otherwise stop
`INCONCLUSIVE_REPRODUCTION`, with no 10-step efficacy conclusion.

Only after a pair's 5-step reproduction passes, set the model's step
count to 10 in this isolated process, run the same native sampler with
the same condition/features/noise, then restore 5 in `finally`.
Assert both trajectories have10 finite (8000,3) states, resulting final
relative SE(3) is valid, and scoped RNG/precision state is restored.
Save full 10-step raw endpoint/clean-state arrays and pose; no GT labels
or success counts. The validator independently hashes all sources and
outputs, redecodes all eight final poses from saved normalized points,
checks the original 5-step reproduction records and resources.

Engineering pass `PASS_STEPCOUNT_PREFLIGHT` requires all eight 5-step
reproductions <=1e-5, all eight finite/valid 10-step trajectories,
wall<=10min, peak allocated VRAM<=12GiB and new artifacts<=1GiB. A
failure is `INCONCLUSIVE_ENGINEERING`; do not use eight pairs to select a
step count. A pass only licenses a separately frozen *full* observed-
development 5-vs-10 comparison with K4, original R4 selection and gate,
fixed cost/eligibility margins and later independent confirmation.

No production/default edit, training, network, data acquisition, GT
motion or Git sync. Preserve F2 and D0 completed artifacts.
