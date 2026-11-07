# NOC1: native noise robustness census

VALIDATED_ZERO_UPDATE_NOISE_CENSUS_COMPLETE_WITH_EXECUTION_RETRY; decision **NO_STABLE_FRESH_NOISE_ADAPTER_CONJUNCTION**. Owner said "探索并且执行下一轮" after NOC0. New fixed16-draw census and separate oracle teacher diagnosis completed, zero optimizer calls. Primary conjunction: **False**. This is conditional evidence on the same two exposed tasks, not new-scene transfer or system performance.

## Fresh-noise result

B is frozen native RAP with initialized zero-B adapters; A is the unchanged NOC0 final400-update native adapter for each fixture. All16 fresh CUDA noises are predeclared BIG-ENDIAN SHA256-derived seeds and paired identically across B/A and fixtures. Original training noise850873755 and old unseen20261011 are separately repeated and excluded from aggregates. No best-noise/arm selector or pose ensemble. Quantiles use linear interpolation; t metres, R degrees; joint signs require both t and R nonworse within a draw.

| Fixture/part | Mean t B/A | Mean R B/A | q90 t B/A | q90 R B/A | Joint nonworse A | A absolute .05m/.2deg pass | Full cell gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic part1 | 0.157385 / 0.142062 | 0.163699 / 0.141256 | 0.276437 / 0.231988 | 0.241181 / 0.204461 | 9/16 | 1/16 | False |
| synthetic part2 | 0.151187 / 0.124324 | 0.146506 / 0.122776 | 0.237691 / 0.195658 | 0.210627 / 0.194313 | 11/16 | 1/16 | False |
| real part1 | 0.081116 / 0.075886 | 0.137916 / 0.096847 | 0.127245 / 0.114603 | 0.218538 / 0.153493 | 5/16 | 4/16 | False |
| real part2 | 0.282999 / 0.249439 | 0.257483 / 0.235528 | 0.361652 / 0.354870 | 0.318207 / 0.311593 | 12/16 | 0/16 | True |

The prospective cell gate requires mean t gain>=10%, paired median t gain>=5mm, mean R harm<=.01deg with nonnegative paired median R gain, joint nonworse>=12/16, q90 t harm<=5% and q90 R harm<=.02deg. All four cells must pass. This is an engineering screening criterion, not a retroactive NOC0 or historical gate amendment, calibrated safety bound or population test.

- synthetic part1: failed mean_t/joint_signs; median paired t/R gain 0.021897m/0.026589deg.
- synthetic part2: failed joint_signs; median paired t/R gain 0.025456m/0.025718deg.
- real part1: failed mean_t/median_t/joint_signs; median paired t/R gain 0.004142m/0.059120deg.

All four mean t and R errors improve and all q90 guards pass. Only real part2 passes its complete cell gate. The joint t/R nonworse counts9/11/5/12 show why these partial average gains do not establish consistent per-draw improvement. Synthetic part1 mean t gain9.736% narrowly misses10%; real part1 mean t gain6.447% and paired median4.142mm miss their thresholds. Do not describe this as universal adaptation failure or a tail regression.

## Was the original training noise representative?

Empirical percentile is the fraction of16 fresh errors <=the old reference error, lower is better. These ranks do not treat the old draw as a fresh independent test or quantify a physical confidence interval.

| Fitted A reference | t(m) | R(deg) | t fresh percentile | R fresh percentile |
| --- | --- | --- | --- | --- |
| synthetic part1 training_reference | 0.035851 | 0.064734 | 6.25% | 6.25% |
| synthetic part1 old_unseen_reference | 0.108810 | 0.188068 | 31.25% | 81.25% |
| synthetic part2 training_reference | 0.045693 | 0.105355 | 0.00% | 37.50% |
| synthetic part2 old_unseen_reference | 0.081261 | 0.177461 | 37.50% | 87.50% |
| real part1 training_reference | 0.073905 | 0.094643 | 43.75% | 43.75% |
| real part1 old_unseen_reference | 0.075783 | 0.109760 | 43.75% | 75.00% |
| real part2 training_reference | 0.025654 | 0.112750 | 0.00% | 6.25% |
| real part2 old_unseen_reference | 0.356156 | 0.275540 | 87.50% | 68.75% |

Both old reference noises reproduce NOC0 native raw states/endpoints/velocities byte-exactly for all B/A/fixture combinations (eight reference inferences). Their unusual or typical ranks are diagnostics; no unique memorization/noise cause, reference correctness, checkpoint exposure or physical truth is inferred.

## Training state versus actual inference

Teacher-state diagnosis follows the complete prediction seal, uses old target-derived coordinates only in this labelled oracle scope, and is not a new performance candidate. It runs five tau values at each fixed weight/noise without gradients. Loss is normalized pointwise velocity MSE over all three parts, therefore shared by the two part rows within each fixture. The t gap is actual native fifth-step error minus teacher tau.2 error; the correlation columns describe fitted A on16 fresh draws, not independent efficacy or a selector.

| Fixture/part | Teacher mean MSE B/A | Native-minus-teacher final t gap B/A(m) | A teacher loss/native t Spearman | A rigidity/native t Spearman |
| --- | --- | --- | --- | --- |
| synthetic part1 | 1.16111639e-05 / 2.59427733e-05 | 0.005496 / 0.004942 | 0.3852941176470588 | 0.06176470588235294 |
| synthetic part2 | 1.16111639e-05 / 2.59427733e-05 | 0.004949 / 0.001703 | 0.5411764705882353 | 0.17941176470588235 |
| real part1 | 0.00012350442 / 2.88227654e-05 | -0.002548 / -0.004554 | 0.4294117647058823 | 0.24705882352941175 |
| real part2 | 0.00012350442 / 2.88227654e-05 | 0.008625 / 0.016710 | 0.7264705882352941 | 0.08823529411764705 |

Synthetic A teacher MSE rises from1.16112e-5 to2.59428e-5 while both native mean pose errors improve; real A MSE falls from1.23504e-4 to2.88228e-5 without a full motion conjunction. Teacher velocity MSE is therefore not a sufficient proxy for this motion screen. A mean final native-minus-teacher t gaps are+4.942/+1.703/-4.554/+16.710mm; these small and mixed-sign gaps do not establish actual-state distribution shift as the dominant explanation. Teacher-state errors themselves remain substantial. A distinct pose-aligned, noise-varying fitting design is a hypothesis motivated by these mismatches, not a diagnosed causal cure.

All full per-draw errors, one/five-step outputs, teacher tau metrics, per-arm losses, min/max/std/median/q90, paired changes, joint signs, reference ranks and120-dependent-pair pose-dispersion summaries are retained in results.json. Rigidity is target-free raw endpoint distance to its own per-part best rigid condition fit, averaged over five steps in metric units; it does not calibrate pose errors. Correlation is descriptive; no causal, residual-to-accuracy or confidence claim. No pose mean/ensemble candidate was produced. The old simple direct controls are byte-bound contextual outputs: unequal architecture/init/capacity and synthetic copied descriptors prevent RAP-superiority conclusions.

## Validation and resources

All72 native traces independently reconstruct using Horn geometry versus evaluator SVD, first/fifth-step poses, every raw clean equation and rigid feedback recurrence, teacher clean algebra, all pose/MSE/rigidity metrics and aggregate fields. The statistics aggregation code is shared but run on independently reconstructed Horn records; the full gate is independently duplicated.18 noise draws independently regenerate exactly, eight first/last fresh full native inferences and40 teacher forward calls reproduce byte-exactly. Max pose delta 4.92e-14, metric 4.15e-13, recurrence 7.4e-07, rigidity 1.53e-15, teacher algebra 0, aggregate 4.92e-12. No full repeated72-inference census, optimizer replay, raw preprocessing or descriptor inference.

One validation attempt was started before the still-running evaluation completed its results seal. It stopped with FileNotFoundError before numerical checks. FAILURE_validation.json, its resource entry and EXECUTION_RETRY_NOTE.md are preserved. The same frozen validator passed after evaluation completed; no implementation, weights, noise, scientific outputs, gate or cap changed. This is an execution-order retry, not an implementation repair or a failed scientific candidate.

7 recorded stages total 219.739328s, peak allocated/reserved GPU 409.29/444.00MiB, peak RSS 2.367081GiB.900s/3GiB GPU/4GiB RSS/512MiB whole-dossier caps pass, all attempted RSS recorded. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Artifact bytes are finalized in DELIVERY_SEAL.

## Decision boundary and preservation

NO_STABLE_FRESH_NOISE_ADAPTER_CONJUNCTION. Do not turn partial average improvements, teacher losses or lower noise dispersion into a system/physical/independent-generalization claim. Frozen checkpoint training/site membership, real reference/physical time/calibration and all previous uncertainties remain. NOC0 all103 delivery identities, its original failure/retry/validator/provenance notes and source/parameter arrays match.138 source/input freeze entries; all original model/config/checkpoint identities retained. Both HEADs/branches/two and nine tracked dirty sets preserved, sibling helper unchanged. No new training, window, acquisition/install, production/default/backbone-source/manuscript edit, official metric replacement, full trajectory, commit or Git sync. Prior map/RLP2 stops and originality exploration relaxation persist; no original mechanism.
