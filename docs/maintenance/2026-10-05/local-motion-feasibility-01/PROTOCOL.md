# LMF0 causal local-motion engineering preflight

Authorized continuation of FDI1's distinct next direction. Engineering only,
no new GT computation. Freeze protocol, runner, independent validator, all RAP,
descriptor and config dependencies, existing weights, E0 manifests/timestamps
and complete raw identities for the fixed-index census before output.

Rule: t in range(0,N,200), exposed00/05/06/07/09/10; exclude t<2 for all arms.
Inputs [t-1,t,t-2] in individual original LiDAR frames; all timestamps <=t.
Engineering generation: first eligible t=200 each sequence, no GT-error ranking.
All data are observed development and checkpoint training split is unknown.

RAP loading: reuse C2 explicit OmegaConf/NumPy safe_globals allowlist under
weights_only=True; inspect serialized globals, never unrestricted fallback.
Only state_dict applied; strict=True, exact keys/shapes/dtypes/finiteness for
RAP344 and miniSpinNet58 keys. Require original F2 checkpoint SHA. No metadata
config/RNG/optimizer applied, downloads or training. Production loaders unused.

Fixed preprocessing: range>=1.5m, +.205deg correction, .4m voxel, outlier20/2.5,
seed42 cap1000/scan; 5m descriptor radius with the same1000 points as patch
support. Feature/noise RNG SHA256('LMF1|sequence|t') first4 bytes big-endian.
R3: native3000-point three-part K1/five-step Euler, per-part rigidity only,
no KISS-derived motion constraint. R2: same first two scans/features and first
2000 noise rows, declares lower compute; not equal-total-budget attribution.
Decode double rigid fits, inv(A_previous) A_current maps current to previous.

G2: identity-initialized point-to-point ICP current->previous; nearest distance
<=3m, >=20 matches, max30 steps, stop max entry |increment-I|<1e-7.
G3: identical geometric oldest->previous fit; pool previous1000 and transformed
oldest1000, register current1000 initialized by G2. Same three physical scans/
3000 unique points as R3; no KISS/GT/native RAP pose provided. Saved KISS will
be a later practical dense-map reference, not an equal-input causal ablation.

Synthetic tests precede generation: nontrivial known three-frame transforms,
all six input permutations, centers/scales, common registered-frame gauge,
roundtrip and inverse direction; future/duplicate/out-of-order causal rejection;
known ICP and support transport. These verify algebra, not learned order or
rotation invariance. Axis max scale/global-z descriptors are not assumed
rotation equivariant. Two exact saved native N0 replays: first F2 entry00/08,
saved C1 features/noise, raw/noisy maxdelta<=1e-5.

Six local R3/R2 pipelines finite with proper decoded rotations. Full seeded
point/feature/inference repetition maxdelta<=1e-5; arbitrary dummy pointclouds_gt
under same noise must leave generation byte-exact. Save and seal inputs,
features/noise/raw endpoints/poses before independent Horn fits, direct
normalization and brute-force ICP for every local control. No GT pose reads.
Caps combined bank/validation1200s, GPU allocated<12GiB, RSS<4GiB,
artifacts<100MB. Failed engineering stops; no accuracy conclusion.

Pass licenses separately frozen complete fixed-census local error screen;
its margins/evaluator must precede GT. Isolated maintenance orchestration only,
no production/model/default edits, trajectory rerun, manuscript, commit or
Git sync. All stopped routes persist; native multi-frame RAP is prior art,
not an original mechanism. Owner breakthrough requirement remains unresolved.
