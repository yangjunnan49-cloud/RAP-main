# NOC1: fixed-adapter native noise robustness census

Owner said "探索并且执行下一轮" after NOC0. This authorizes this next fixed diagnostic before checkpoint loading. NOC0 establishes fixed-noise fitting, not transfer; all prior experiments and seals remain unchanged. No optimizer, adaptation, new model architecture or full trajectory in NOC1.

## Fixed inputs and outputs

Reuse NOC0's exact synthetic same-scan fixture and real00/t2 [1,2,0] window, each three1000-point parts/native32 descriptors. B is the original frozen RAP represented with NOC0's exact initialized zero-B adapters; A is the corresponding fixture's final400-update native parameters at lr1e-4. All443904 adapter/output-MLP values are frozen, all other parameters unchanged. No descriptor inference, raw preprocessing, new reference pose, nearby window, GT replacement or physical calibration. The old406019 direct clean-point learner's final output is retained as a fixed contextual control, not a balanced efficacy comparator.

Primary census: exactly16 new noise draws, indexed0..15, seed SHA256("NOC1-noise-census|20261010|i").digest()[:4] interpreted unsigned BIG-ENDIAN. Each draw is torch.randn((3000,3), CUDA float32), with original RNG state restored. Verify seed uniqueness and exclusion of850873755/20261010/20261011. Use the same noise array for B/A and both fixtures; these are paired draws on two exposed tasks, not independent scene samples. Separate references: original byte-exact training noise850873755 and old unseen20261011. Those two previously exposed draws are excluded from primary aggregate/gates.

For each of18 noises x2 fixtures x2 arms, run the exact production five-step Euler/rigidity-feedback sampler, n_generations1, IEEE float32 geometry, original fp16 neural attention. Save all72 raw endpoint/state/input/velocity traces. The inference batch contains only conditions/features/scale/anchor/group boundaries and condition placeholders; no target coordinates/poses, training cache or teacher state enters inference. Capture the model state before/after each arm and ensure byte-identical values, no optimizer calls. Replay both reference noise outputs byte-exactly against NOC0 for each fixture/arm.

Seal the complete prediction bank before deriving new reference-error outcomes. Independent validation reconstructs every native recurrence and decodes every first/fifth-step output using Horn quaternion geometry versus SVD in the evaluator. Repeat full native inference for first/last primary draw on each fixture/arm only, plus exact noise replay; no full repeated census/model fitting. Retain invalid outputs/failures with INCOMPLETE and stop, no fallback or seed replacement.

## Prospectively fixed primary descriptive gate

For each fixture and moving part separately, compute16-draw B/A mean/median/q90/std t(m)/R(deg), paired B-minus-A means/medians and joint nonworse signs. Descriptive quantiles use numpy linear interpolation. All four fixture/part cells must jointly satisfy:

- A mean t <=.90 B mean t (at least10% fractional improvement).
- Median paired t gain >=.005m.
- A mean R <= B mean R +.01deg AND median paired R gain >=0.
- At least12/16 draws jointly have A t<=B t and A R<=B R.
- A q90 t <=1.05 B q90 t AND A q90 R <=B q90 R +.02deg.

This new engineering screening rule is frozen before NOC1 outcomes; it does not amend NOC0's .05m/.2deg capability gate or any older scientific conjunction. Also report every absolute capability pass count, min/max and the two original reference draws' percentile ranks among new draws. No p-value, population generalization or calibrated tail/safety claim:16 draws/two exposed tasks are a small conditional census. A full gate pass supports designing nearby-window no-update evaluation only, not automatic execution/training/system promotion.

If the gate fails, stop additional noise/seed/step/model/checkpoint/window sweeps on this exact census. Retain partial gains and adverse parts. Do not infer universal native unlearnability, unique memorization cause, GT error or physical truth. No noise/arm/point selector or pose ensemble is produced.

## Declared secondary diagnosis after prediction seal

With the same fixed weights/noises, evaluate target-derived teacher states at tau1/.8/.6/.4/.2, velocity/clean-output arrays, and independent per-part poses. This is a separate oracle diagnostic, zero optimizer; reference target states never enter production inference. Compute mean teacher velocity MSE and teacher-versus-native final error gaps, fresh/train noise contrasts, per-part pose dispersion across draws, and Spearman correlation of teacher loss/target-free raw rigidity residual with actual reference errors. Rigidity residual means each raw endpoint's distance from its per-part best rigid condition fit, aggregated across5 steps in metric units. It is not calibrated confidence, physical accuracy or a noise-selector objective. Correlations are descriptive and may be null for a constant vector; no best-draw selection, averaging, rescue, new candidate or causal claim.

The direct control's final output is copied byte-exactly and its existing errors are rechecked. Unequal architecture/init/capacity and copied synthetic descriptors remain explicit limitations. Synthetic transform truth is known; real reference remains weak and site/checkpoint/timing/calibration provenance unresolved. Teacher MSE and native pose improvements may disagree.

## Resources and closure

New combined execution/independent validation ceiling900 seconds, GPU allocated AND reserved high-water3GiB, process peak RSS4GiB, whole NOC1 dossier512MiB. Include checkpoint loading, noise generation, all forward/diagnostic/evaluation/validation attempts and failures. Check caps at each draw, use remaining-time alarm. Record all attempted RSS/GPU and failures. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. NOC0's budget is closed and unchanged.

Freeze source/input identities, all16 seeds, controls, gates and caps before CUDA noise/model payload. Snapshot new sources. Preserve NOC0 all103 delivery identities and its old failure/retry/validation/provenance notes; unchanged model/config/checkpoint identities and both HEADs/branches/two and nine tracked dirty sets. Only new isolated main maintenance scripts/docs and mutable handoffs. No sibling helper modification, install/acquisition, learning, new geometry optimization, production/default/backbone-source/manuscript edits, official metric replacement, full trajectory, commit or Git sync. Next plan is design only.
