# RLP2 complete motion-supervised readout pilot

Status: VALIDATED_NEGATIVE. Decision: NO_COUPLED_JOINT_READOUT_SIGNAL.
Owner authorized the complete immediate pilot with "执行你的建议" and then "请继续".
All204 feature/pose-target windows, nine fixed1000-update fits,432 primary and144
permutation predictions,708 error records and15 scientific stage validations are complete.
Primary coverage 432/432; permutation coverage 144/144.
No RLP2 numerical implementation failure/repair or scientific setting change occurred.
Owner separately approved at most45 additional process minutes before any GT model-error outcome was inspected. Combined ceiling is now6300s (105min); all scientific settings and other caps remain unchanged. Original budget stops retained: 1. The isolated hash-bound resource-amendment-01 launcher changes only combined cap enforcement; original scientific sources and all partial compute/failure snapshots remain. Original60min is not claimed as passed.

J fails the required conjunction of coupled comparisons against I and D. Stop investment in this exact frozen-token, fixed-budget motion-supervised readout construction. This does not prove universal token unlearnability. No trajectory or automatic rescue follows.

## Actual experimental scope

Original count-selected windows:144 fit00-05,12 development06,48 historically exposed
evaluation07-10;612 unique raw frame paths.06 was retained in the source/target banks
but used for no optimizer step, tuning or selection. Three fixed seeds20261007/08/09
and the same initial state across D/I/J per seed. Exactly9000 promoted optimizer
updates plus9000 separate independent replay updates, not18 fitted candidates.
Each per-window error is the median of all three seed errors before cohort comparison.
No favorable window/seed/epoch selection.

D uses32 descriptors+480 zero padding; I uses full-flow separated-context512-D tokens;
J uses joint-context512-D tokens. Identical9 common channels and521->128SiLU->64
unit embeddings.75072 nominal parameters; D13632effective, I/J identical active capacity.
Frozen RAP/miniSpin extraction uses original1000 points/scan, scanorder[t-1,t,t-2],
big-endian original LMF1 noise seed, last nominalt=.2, five native flow calls.
Both I and J were extracted for every window (2040 flow calls total).

Pose-only R/t weak supervision from update1 for all three pairs; no point-positive
count floor, overlap/dustbin branch or hard-match inference decoder. Float32 IEEE
dual-softmax-product weights normalize in float64 and solve proper SE3 on original
measured points. Same continuous solve at train and inference; Horn relative gap>1e-6,
no nonunique solve skip/fallback. AdamW lr1e-3,wd1e-4,batch1,clip1,1000updates;
fixed cyclic hash order and loss scales. Exact encoding saves float32 embeddings,
FULL raw-W SHA256, marginals/mass/spectrum/gap and pose. Validators regenerate all
weights byte-exactly on pinned operators, then use independent double Horn.

## Local results

All48 exposed-window cohort medians, t(m) / R(deg): D: 0.951464 / 0.606511; I: 1.392460 / 0.698359; J: 0.888431 / 0.552965

| Control | Windows | J median t(m) / R(deg) | Control median | Paired control-minus-J gain | Positive fractions t / R | Full gate |
|---|---:|---:|---:|---:|---:|---|
| I | 48 | 0.888431 / 0.552965 | 1.392460 / 0.698359 | 0.549531 / 0.050644 | 0.833333 / 0.625000 | True |
| D | 48 | 0.888431 / 0.552965 | 0.951464 / 0.606511 | 0.250173 / 0.007573 | 0.687500 / 0.541667 | False |
| G3 | 48 | 0.888431 / 0.552965 | 0.097115 / 0.238968 | -0.758844 / -0.357058 | 0.000000 / 0.041667 | False |
| KISS | 36 | 0.888431 / 0.593314 | 0.022371 / 0.049555 | -0.878705 / -0.495560 | 0.000000 / 0.000000 | False |

Gains are paired medians, not differences of cohort medians. J vs each I/D requires
both paired gains>=.005m/.01deg, both J medians<=90%control, positive fractions>=.60
for each, and every sequence mean regression<=.005m/.02deg. G3 requires paired
gains.005m/.01deg+sequence safety. KISS uses36 identical07/09/10 endpoints, paired
gains.002m/.005deg, both J medians<=90%control+sequence safety. Dense-map KISS has
different input/context/cost; same-point G3 is separately included.

| Comparison | Sequence | J-minus-control mean t(m) / R(deg) | Safety pass |
|---|---|---:|---|
| J vs I | 07 | -0.700672 / -0.150454 | True |
| J vs I | 08 | -0.901896 / -0.154279 | True |
| J vs I | 09 | -0.274850 / 0.017939 | True |
| J vs I | 10 | -0.702775 / -0.239431 | True |
| J vs D | 07 | -0.465484 / 0.023975 | False |
| J vs D | 08 | -0.330333 / -0.096240 | True |
| J vs D | 09 | -0.001475 / 0.072658 | False |
| J vs D | 10 | -0.325222 / -0.113905 | True |
| J vs G3 | 07 | 0.627576 / 0.267531 | False |
| J vs G3 | 08 | 0.751801 / 0.428747 | False |
| J vs G3 | 09 | 1.128418 / 0.557067 | False |
| J vs G3 | 10 | 0.796792 / 0.344418 | False |
| J vs KISS | 07 | 0.703636 / 0.502629 | False |
| J vs KISS | 09 | 1.246334 / 0.735734 | False |
| J vs KISS | 10 | 0.858603 / 0.494613 | False |

Full per-seed/per-window errors and sequence mean/median arrays are in
evaluation/bank/results.json. Official GT files and historical system metrics stay
unchanged; new angular targets use the declared proper-rotation projection only.

## Fixed diagnostics

Within each scan, J token rows roll137 while coordinates/common rows remain fixed.
All144 diagnostic outputs were generated after primary validation and before GT
error evaluation. This changes the input distribution and alone proves no causal
mechanism or physical point identity. Identity is evaluator-only, not a fallback.

```text
{
  "total": 144,
  "valid": 144,
  "complete_window_medians": 48,
  "median_error": [
    1.709437308446691,
    11.652314104807001
  ],
  "median_permuted_minus_J": [
    0.8886542706152053,
    10.59458165580885
  ]
}
Identity median t(m) / R(deg): 0.854124 / 0.250591
```

## Independent evidence

Numerical:6 solver/rejection fixtures,18 initialized00/05 head checks,selected
finite-difference gradient delta3.823e-10, Horn
delta1.510e-14; no optimizer in this prerequisite.
Full bank:612 scans/612000 points/19584000 descriptor values and original noise exact;
native group/time/RNG bindings,48 same-point G3 and36 KISS endpoints independently
checked. Max pose/control delta1.099e-13; no native flow rerun
in that validator.204 weak pose targets maxdelta6.288e-13.

| Seed | Arm | Updates | Initial/final/optimizer exact | Max loss delta | Max gradient norm delta |
|---|---|---:|---|---:|---:|
| 20261007 | D | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261007 | I | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261007 | J | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261008 | D | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261008 | I | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261008 | J | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261009 | D | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261009 | I | 1000 | True | 0.000e+00 | 0.000e+00 |
| 20261009 | J | 1000 | True | 0.000e+00 | 0.000e+00 |

Prediction weight hashes all exact. Independent primary/diagnostic Horn pose maxima
5.329e-14/1.590e-13; final708 GT/error/
aggregate/gate records maxerror delta2.195e-13.
Independent fitting implements its own head/loss/solve and replays every step,
not just checkpoint arithmetic. CLOSURE_CHECKS.json rechecks every stage freeze,
complete bank/seal/validation, old RLP1/DS0/design delivery files, original TR0 and
isolated helper/staging binding. Historical AGENTS/PHASE snapshots are mutable
handoffs and excluded from old delivery comparisons. REPOSITORY_STATE.json checks
original HEADs/branches and tracked dirty counts. No prior failure/bank was removed.

## Resources

Recorded process sum 6124.147s /6300s; full extraction 304.527s /1200s; max fit 76.383s /300s.
Peak GPU 1.387GiB /3GiB; RSS 2.678GiB /4GiB; artifacts at final timed checkpoint 3.112GiB /4GiB. Amended caps pass; original budget stops 1.

Counters are sums of recorded monotonic process stages, including freezes, validation,
all9000 independent replay updates and closure/delivery hashing. They are not the
enclosing session wall time. Routine implementation/documentation, idle intervals
and WSL launching are separate; UTC stamps include a long gap and are not the cap
clock. Owner separately approved at most45 additional process minutes before any GT model-error outcome was inspected. Combined ceiling is now6300s (105min); all scientific settings and other caps remain unchanged. Original budget stops retained: 1. The isolated hash-bound resource-amendment-01 launcher changes only combined cap enforcement; original scientific sources and all partial compute/failure snapshots remain. Original60min is not claimed as passed. No precision/density reduction or scientific rescue.

## Limits and next boundary

Exposed engineering pilot, not an independent generalization result. Published RAP
training includes Oxford and excludes KITTI08-10, but local checkpoint binding/site
membership remains unknown; historical02/M3/E0/08 exposure persists. Short-segment
weak GT/09 discrepancy is not resolved or physically verified. I is a possible
one-part OOD ablation with unequal attention work; D effective capacity is smaller.
No calibrated confidence, exact physical correspondence, system metric gain or
originality established by this soft matching/SVD/pose-supervised construction.
All old scientific stops/banks and owner's original breakthrough requirement remain.

Stop this exact head/soft-solve/loss/frozen-token construction under the present project budget. No epoch, seed, temperature, loss, density, correspondence threshold, window or cohort rescue follows. Any future experiment needs a distinct measurable mechanism and a new reviewable scope. No new experimental arm is selected or frozen by this delivery.
No production/default/backbone/manuscript edits, acquisition/install, commit or Git
synchronization. Training authorization was used only for these isolated small heads.
