# D1 four-pair shared-identity engineering: validated negative

Decision: **NO_FOUR_PAIR_FEEDBACK_RESPONSE**. All four fixed real-input cases
passed the frozen source, state, geometry and control identities. Only two of
four passed the prospective feedback response rule, which required all four.
Stop this exact dual-anchor per-step projection route before any evaluator GT,
candidate-selection screen or trajectory. There is no pose-accuracy result.

## Scope and source binding

The pre-output freeze bound121 source/input/checkpoint identities, including
the original SID0 projector, the isolated runner and independent validators.
The original four F2 rows were00_24_629,00_210_1656,08_569_1554 and
08_583_802. Their24 corrected raw scan instances generated32,000 canonical
processed points and1,024,000 feature values. The direct source validator
reconstructed every point/feature/noise element exactly from one parent RNG
stream per six-scan pair, separately from the D1 runner. Strict restricted
checkpoint loading matched344 RAP and58 descriptor state keys.

The original F2 N0 raw/state replay was byte-exact. Each new I/P/C/U arm's
repeat and dummy-label runs were byte-exact; I and U also matched their native
sampler raw/state outputs exactly. All five steps kept raw clean, projected
clean, velocity, state before/after and fixed original noise distinct.
Independent Horn reconstruction checked the dual-anchor solver traces and
relative poses without importing the runner or projector. Maximum combined
independent discrepancy was3.689e-6, within the frozen input/state tolerances;
solver-specific Horn discrepancies were at most1.470e-13 across the pairs.
Maximum native clean/pose comparison discrepancies were6.614e-7/3.798e-5.
All rotations and resource gates passed.

## Frozen response screen

Raw/velocity effects are maximum differences in model-normalized coordinates.
Relative effects and their floors are maximum matrix-entry differences in
mixed rotation/translation units; translation and angle details are retained
in `attempt-02/validation.json`. Each floor is10times the larger of the
fixed absolute guard and measured native numerical-policy discrepancy.
Passing requires raw, velocity, C-versus-F and C-versus-PF effects all exceed
their floors on **each** of the four fixed pairs. F projects I's final raw;
PF projects P's final raw, controlling CPU projection precision.

| Pair | Raw effect / floor | Velocity effect / floor | C−F / C−PF relative effect / floor | Pass |
| --- | ---: | ---: | ---: | --- |
|00_24_629|0.04442 / 0.02127|0.08044 / 0.04799|3.286 / 3.109 / 2.873|Yes|
|00_210_1656|0.00145 / 0.01390|0.00566 / 0.02920|0.00355 / 0.00112 / 0.05156|No|
|08_569_1554|0.03191 / 0.01204|0.08961 / 0.04656|1.991 / 2.015 / 0.7518|Yes|
|08_583_802|0.01915 / 0.01708|0.04550 / 0.03917|0.2196 / 0.2416 / 0.5708|No|

The last08 pair changes later raw predictions, but its relative effect is
below the declared numerical-policy floor. The second00 pair fails both raw
and relative checks. The two positive responses are engineering changes,
not evidence that either resulting pose is closer to truth. The native union
U differs as a complete-context reference; it cannot rescue the failed
predeclared feedback criterion.

## Validation history and resources

The complete four-pair GT-free bank contained96 NPZs and was SHA-sealed before
either validator. The direct source/noise validator passed. The original
numerical validator stopped on its first pair because it expected the repeat
NPZ to contain the root-only `wall_seconds` metadata field. It produced no
validation result. Preserve its frozen source, original freeze, bank, seal,
failure record and `AMENDMENT_01.md`. A separate12-identity attempt-02 froze
the sole scientific correction to the metadata key-set assertion; all array,
sample, solver, threshold and response gates stayed unchanged. The repaired
validator passed all four pairs against the original sealed bank without
rerunning the model. See `attempt-02/PROTOCOL.md`, freeze and validation.

Successful bank, source validator and numerical validator wall times were
61.368+5.002+10.519=76.890s. Peak allocated GPU2.413GiB, peakRSS2.675GiB;
artifacts before final documents208.229MB. All fixed30min/12GiB/8GiB/1GB
caps pass. The failed original validation attempt took approximately4s extra;
it is disclosed separately from the successful-stage resource sum.

This study read no evaluator GT and computed no pose error, registration
success, trajectory metric, graph effect, confidence calibration or training
result. The local12-layer checkpoint's exact training membership remains
unknown. SID0's consistent-wrong2m blind spot remains. Shared clean-endpoint
guidance has close prior art, so an original RAP breakthrough is unproven.
All earlier negative stops and official metrics remain unchanged; no training,
production/default/model/manuscript edit, download/install, commit or Git sync.

Next boundary: no D2 promotion, solver/weight/step/noise/density/cohort rescue
or favorable-pair selection. [NEXT_ROUND_PLAN.md](NEXT_ROUND_PLAN.md) defines
a separate read-only causal/novelty reassessment before any different arm.

Primary artifacts: [PROTOCOL.md](PROTOCOL.md), [manifest.json](manifest.json),
[freeze.json](freeze.json), [bank_seal.json](bank_seal.json),
[source_binding_validation.json](source_binding_validation.json),
[attempt-02/validation.json](attempt-02/validation.json), and [STATUS.json](STATUS.json).
