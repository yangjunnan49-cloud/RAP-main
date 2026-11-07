# D1: prospective four-pair, GT-free engineering protocol

Date: 2026-10-06. The owner authorized continuation after SID0. This stage
checks whether the frozen shared-identity projector can be bound to the
unchanged RAP flow and produce a feedback response on four real inputs. It
does not evaluate pose accuracy, choose candidates or run trajectories.

## Frozen population and inputs

Take the first two original F2 input rows for sequence00 and08, in parent
order: 00_24_629,00_210_1656,08_569_1554,08_583_802. The six physical
scan IDs per pair are in manifest.json. This fixed structural selection was
recorded before D1 output; no label, error, motion or stratum fields enter.

Reconstruct F2 points and C1 descriptors in canonical order
[A,A1,A2,B,B1,B2],caps[2000,1000,1000,2000,1000,1000]. Use the single
original parent seed scope across all six preprocess calls: miniSpinNet's
patch shuffle consumes that sequential RNG stream. Compare all8000 point
rows and256000 feature values exactly with separately sealed F2/C1 caches.
Bind original corrected raw scan hashes, input/feature/native NPZ hashes and
restricted source/weight identities before output. Shared A/B use identical
cached original rows/features in both windows. Recompute window normalization
independently; do not require different-context normalized rows to be
byte-identical. The original six-scan U normalization must reproduce F2.

L=[A,A1,A2,B] and R=[A,B,B1,B2], each6000points. U has8000 unique rows.
The two dual-shared scans are A and B. Source identity is exact row binding,
not inferred cross-scan correspondence. Original saved F2 noise[0] is used
only for the old native replay. New fixed SHA-derived L/R Gaussian noises are
drawn independently once, reused unchanged across I,P,C,F,PF. U maps A/A1/
A2/B from L, B1/B2 from R. Noise is not rotated or replaced after projection.

## Frozen operations and direct controls

Five unchanged Euler steps and unchanged strict safe344/58-key checkpoints.
Raw clean is x_t-t*v; next state is clean*(1-t+dt)+original_noise*(t-dt).
Save raw, clean, velocity, state before/after and noise separately at every
step. Same reference model calls and precision scope as original native RAP.

- I: independent native GPU float32 per-part projection in L/R;10 calls.
- P: independent CPU float64 original-point per-part projection in L/R;
 10 calls. This measures effects of numerical projection policy.
- C: frozen SID0 dual-anchor CPU float64 projection after every raw endpoint,
  returned as float32 before each next model call;10 calls/five joint solves.
- U: native GPU projection on the six-scan union;5 calls.
- F: exact same joint projector on I's final raw endpoint; incremental0 calls.
- PF: exact same joint projector on P's final raw endpoint; incremental0 calls.

Standalone F/PF each include their parent10 model calls. I/P/C match neural
work, not total work; solver times and total times are reported separately.
U has different point/attention cost. The P/PF controls were specified
prospectively because GPU float32 versus CPU float64 projection can itself
change later model inputs. The design's I/F/U controls remain intact.

Prove the old saved F2 N0 raw/state replay exactly with original noise;
prove current I and U custom loops exactly equal native sampler raw/state on
their matching inputs/noise. Repeat I/P/C/U and dummy pointclouds_gt runs
must be byte-equal in saved raw/clean/state/velocity/poses. Verify Python,
NumPy, CPU/CUDA torch RNG and global precision state restoration. Never alter
production sampler, model, checkpoint or earlier banks.

## Independent engineering validation and gates

Freeze protocol, sanitized manifest, isolated runner, independent Horn
validator and direct source/noise replay validator, original SID0 math,
runtime, all fixed raw/cache/weight/source hashes and resource limits before
generation. Bank all four complete pairs, including every control and every
step solver trace, then SHA-seal all bank NPZs and bank.json before independent
validation. The direct source/noise validator rebuilds raw point selection,
all descriptors under one original seed stream and trial noise without
importing the D1 runner or doing flow inference. The Horn validator imports
neither D1 runner nor projector; it reconstructs C/F/PF poses, trace and
returned clean/state equations, cache identities, native outputs and controls.

Identity tolerances froze before output: normalized native clean2e-5,
native metric pose5e-4, double precision pose1e-7, float32 returned clean
cast5e-7, float32 state recurrence2e-5, proper double rotation1e-10. GPU native observed rotations use
their native metric pose tolerance. Source point/descriptor/noise and native
replay/repeat/dummy checks require exact equality. All4 pairs must pass
identities. Undefined or nonconvergent SID0 fits fail; preserve partial bank.

Response is separate from identity. For each pair, require a next-step
(steps1..4) raw and velocity C-minus-P effect and a final C-minus-F AND
C-minus-PF A/B relative-pose max-entry effect. Each must exceed10times
the larger of its fixed absolute guard and independently measured numeric
reconstruction/repeat/native-policy discrepancy. Guards:2e-5 normalized
for raw/velocity and5e-4 for a physical relative-pose matrix. The
prespecified response admission requires4/4 pairs; fewer means stop this
exact arm. Enforced clean agreement does not count. Matrix max-entry mixes
translation and rotation units; report physical translation and angle
differences separately, but make no accuracy inference. U differences are
reported as direct context comparisons, not an after-the-fact rescue gate.

Successful bank plus two validators wall<=1800s, GPU allocated<=12GiB,
peakRSS<=8GiB, all artifacts<=1GB. An engineering mismatch creates
INCOMPLETE and a preserved failure/partial bank. A correctness repair must
use a new attempt/freeze, unchanged cases/thresholds and full disclosure.
If source reconstruction, old replay, state identity or response admission
fails, do not move to evaluator labels or a larger cohort. No density/noise/
step/solver/weight/cohort sweep is authorized by this protocol.

Even a D1 pass establishes only the real-input feedback mechanism. It does
not establish a correct candidate, physical measurement, calibrated
confidence, registration/graph gain or RAP originality. A separate
prospectively frozen full candidate screen with fresh direct controls and
00 safety would be needed. Unknown local checkpoint training membership
and all earlier negative stops remain.
