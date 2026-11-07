# NOC0 native-output capability diagnostic

VALIDATED_CAPABILITY_DIAGNOSTIC_COMPLETE_WITH_NUMERICAL_REPAIR; decision **TINY_NATIVE_SAMPLER_CAPABILITY_PRESENT**. Owner said "执行下一轮" then "继续". This is the small diagnostic recommended after MF0, not the old twelve-fit draft or stopped RLP2. All retained outcomes are exposed development evidence.

## Result

Synthetic native five-step train-noise gate passed: True. Selected declared learning rate: 0.0001. Real windows executed: 1. Total optimizer updates: 1600; each retained fit400 updates. No extra steps, windows, seeds or undeclared learning-rate rescue. Moving part1/part2 errors below use independent proper rigid decode, t metres/R degrees.

| Arm | Initial five-step train noise | Final five-step train noise or direct output | Final five-step unseen noise |
| --- | --- | --- | --- |
| real_direct | direct initial loss 0.0188992 | 0.028712m, 0.176788deg / 0.023674m, 0.296687deg | noise-independent direct output |
| real_native | 0.163526m, 0.291382deg / 0.217319m, 0.256414deg | 0.073905m, 0.094643deg / 0.025654m, 0.112750deg | 0.075783m, 0.109760deg / 0.356156m, 0.275540deg |
| synthetic_direct | direct initial loss 0.0186898 | 0.211516m, 1.158409deg / 0.048265m, 0.295697deg | noise-independent direct output |
| synthetic_native_lr1e-4 | 0.030309m, 0.095174deg / 0.121640m, 0.162675deg | 0.035851m, 0.064734deg / 0.045693m, 0.105355deg | 0.108810m, 0.188068deg / 0.081261m, 0.177461deg |

The synthetic conditional gate is both moving parts <=.05m and <=.2deg on the fixed training noise. Unseen noise was withheld from fitting, but shares the exact same scan/task: it is not scene transfer. A single known-transform fit or weak-reference real-window fit is not calibrated accuracy, independent generalization, RAP superiority, useful system gain or original mechanism. The direct control differs in initialization, architecture and capacity ({'real_direct': 406019, 'real_native': 443904, 'synthetic_direct': 406019, 'synthetic_native_lr1e-4': 443904}); comparisons diagnose fitting only.

Noise provenance: training noise is the byte-exact original RLP2 00/t2 array (original seed850873755), adapter/direct initialization and sampler RNG guard use20261010, unseen noise uses20261011. The sealed bank summary's noise_seeds[0]=20261010 labels initialization rather than the original noise seed; NOISE_PROVENANCE_NOTE records this metadata correction without rewriting sealed arrays/manifest. Actual training noise identity is independently checked.

## Teacher forcing versus actual sampler

- real_native: mean teacher velocity MSE 0.000120238788 -> 2.05159093e-05; final tau1 teacher 0.162709m, 0.232428deg / 0.174903m, 0.244639deg; tau.2 0.075435m, 0.097705deg / 0.015374m, 0.116459deg.
- synthetic_native_lr1e-4: mean teacher velocity MSE 1.01567159e-05 -> 1.91901157e-05; final tau1 teacher 0.062005m, 0.091843deg / 0.096759m, 0.350057deg; tau.2 0.039696m, 0.063257deg / 0.040993m, 0.113161deg.

Teacher outputs use target-derived X_tau and remain separately labelled. Pure-noise inference uses original measured normalized inputs/descriptors and the unmodified production five-step Euler/rigidity-feedback sampler, with no target coordinates, target poses, teacher prefix cache or gradients through detached sampler outputs. All raw endpoints, states, velocities and one-step/five-step decoded poses are saved, including adverse and unseen-noise outcomes. Independent auditing checks every saved recurrence and gate. Low normalized MSE alone cannot establish a metric pose fit; common scale and sparse late-state errors can mask meaningful motion differences.

## Numerical failure and repair

Original92-entry freeze, partial bank/source snapshots, failure/two-row ledger/INCOMPLETE are intact. The initial backward had zero gradients for all four low-rank B matrices, and stopped before optimizer update1. Separate zero-update gradient diagnosis checks scales1 and1024 with identical parameters/states/loss. Scale1 B norm0, scale1024/unscale B norm3.1292e-5; output-MLP norm.00256185 identical. Every B branch is restored. This confirms this particular fp16 underflow, not universal unlearnability. AMENDMENT_01 discloses fixed backward scale1024 and gradient division before clipping/AdamW; no objective weight, learning-rate, count, seed, gate or cap changed. Zero A gradients at zero-B initialization are expected; A becomes active after updates. Retry source/input freeze has 102 entries and separate output routing; unchanged helper/production sources. Selected output-weight FD abs difference 5e-10.

## Validation and resources

Independent Horn quaternion decode, exact target/normalization and real-source bindings (when admitted), all saved teacher/native/direct metrics, conditional search admission, every five-step recurrence and selected final full model/direct checkpoint forwards pass. 12 checkpoint records audited; max pose delta 3.72e-14, metric 2.95e-13, native float32 recurrence versus independent float64 geometry 7.4e-07, selected forward 0. First-ten-block teacher caches equal full forwards and frozen parameters retain their digest. Before validator execution, static review caught float32 real-point mean computation in its independent centre reconstruction; AMENDMENT_02 separately binds the float64 cast matching native normalization. Original validator sources and all fitted arrays remain unchanged; validation-attempt-02 has an independent source/input freeze. This is a pre-execution validator correction, not another failed fit or outcome change. Validation is bounded: no full independent AdamW replay and no independent replay of the selected FD beyond its stored values. No new raw preprocessing, descriptor inference or physical-reference verification.

All 6 recorded stages, including original failure and zero-update diagnosis, total 405.596767s. Peak allocated/reserved GPU 614.96/654.00MiB, RSS 2.703754GiB. Original+diagnosis+retry whole-dossier artifact count is finalized in DELIVERY_SEAL.1800s/3GiB GPU/4GiB RSS/512MiB caps pass. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Full resource ledger retained; all attempted RSS captured.

## Repository and evidence limits

Both original HEADs/branches/two and nine tracked dirty sets retained; checkpoint hash and all frozen model/config sources match. Strict weights-only344-key RAP load, no miniSpin load. Prior map/MF0/review delivery counts {'measured-map-reoptimization-01': 35, 'shared-plane-map-pilot-01': 42, 'structural-holdout-map-pilot-01': 37, 'cross-visit-map-pilot-01': 42, 'rotation-protected-map-pilot-01': 39, 'membership-formation-diagnosis-01': 56, 'experiment-review-01': 6} match. RLP2 12 top-level delivery identities match; its full old bank/optimizer replay was not repeated. New isolated helper, main maintenance scripts/dossier and mutable handoffs only. No production/default/backbone-source/manuscript edit, acquisition/install, official-GT replacement, full trajectory/system metric, commit or Git sync. Prior stops/seals, physical time/calibration/reference/site/checkpoint-training-membership uncertainties and exploration relaxation remain.
