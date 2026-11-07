# TR0: frozen joint-token extraction and native-invariance preflight

Prospective protocol, owner authorized by "continue next" on2026-10-07.
This is GT-free engineering only. It does not revive stopped native R3, RAD1,
support poses, directional information or shared-identity feedback. No head
fitting, GT errors, trajectory, production/default/model/manuscript edit,
download/install, commit or Git sync. Algorithm extraction resides in isolated
RAP-SLAM/scripts/joint_token_extraction.py; orchestration and independent
validation reside in RAP-main/scripts/maintenance. Native sources remain read-only.

## Fixed inputs and interface

Select the first structurally eligible row in the sealed LMF1 census from00,
05,06,07, in that order. Each t=200; native part order [199,200,198]. Selection
does not inspect per-window GT errors. Exact seeds, timestamps and raw paths
are written into freeze.json before inference. The original GT-free native NPZ
for each window is an exact replay reference. Verify native source/config/
checkpoint/raw identities against the original LMF1 freeze without reading
its evaluator GT files. Preserve the original58-window screen and negative.

Three scans,1000 native processed measured points/scan,32-D miniSpin descriptors,
original noise and normalization, frozen344-key RAP/58-key descriptor checkpoints,
strict restricted weights_only loading. Five-step Euler, rigidity forcing,
FP16 neural autocast and scoped IEEE float32 geometry. Runtime is frozen before
outputs: existing WSL Python3.10.20,torch2.7.0+cu128,numpy1.26.4,scipy1.15.2,
Open3D0.19.0,Hydra1.3.2,CUDA12.8,cuDNN90701,RTX5070; three CPU thread limits1.
Exact full runtime fields and checkpoint hashes are in freeze/bank records.

Use the existing return_transformer_features interface, never edit sampler or
model. Export float32 [3,1000,512] post-attention tokens from the last flow call,
whose input has nominal t=.2, before the last integration. This is neither the
final generated3-D endpoint nor an additional t=0 model evaluation. The passive
hook is on the last of12 transformer layers; a separate flow pre-hook binds all
five integration inputs/times and last-call condition/descriptor/scale/anchor/
part/batch row bindings. Neither hook returns replacements or changes tensors.

## Five controls per window, prospective accounting

- N: existing native trajectory interface, no token export or hooks.
- E: existing token export, no hooks.
- H: same export plus passive layer/flow hooks.
- R: exact E repeat from the same seeded runtime state.
- D: E with only pointclouds_gt replaced by deterministic finite arange*.01+10.

pointclouds_gt is a native placeholder containing the condition, not an official
GT label. The sampler discards that value. D tests that the existing placeholder
is not a hidden dependence of token/pose extraction. All other inputs identical.
Each control has five flow calls:100 expected calls over4windows; H independently
counts20 calls. No extra flow t=0 call, extra generation, density or seed variation.
Save20 compressed NPZs, including N measured inputs/noise/IDs, every control's
raw endpoints/post-step states/part and relative poses/RNG arrays, E/H/R/D tokens,
H hook tokens/row/time trace and D placeholder. No label bank or selection score.

The native _prepare_data draws one unused CUDA uniform value even with explicit
noise. Thus preserve the native RNG transition, not before==after CUDA state.
Every control starts from the same seeded Python/NumPy/CPU/CUDA state. Require
all after states equal N; Python/NumPy/CPU unchanged, CUDA exactly the state after
one torch.rand(1) draw. The enclosing seeded context restores the outer states.
Record tensor-state arrays and Python/NumPy digests, unchanged parameter versions
and module train/eval flags. Passive hooks may allocate/copy; timing is not exact.

## Gates, validation and stopping

Before any inference freeze this protocol, extraction/runner/validator, original
source/config/checkpoints, selected12 raw scans, source time/frame metadata,
four saved native NPZs and their original seals. Complete20-file GT-free bank
seals before independent validation. No GT evaluation is part of this stage.

Exact (zero tolerance): points/descriptors/noise, native saved replay, N/E/H/R/D
raw/state/part/relative-pose outputs, E/H/R/D tokens, H layer/export equality,
RNG transition, tensor row/part ordering and nominal float32 times. Tokens finite
float32 [3,1000,512]. Independent raw/KITTI205/Open3D preprocessing and direct
miniSpin reconstruction; direct normalization centers/scale <=1e-12, condition
exact; quaternion Horn part/relative fit delta<1e-8, proper rotation<1e-8.
Validator imports no new extraction algorithm and runs no RAP inference. It
checks the source-defined unused RNG draw independently from archived states.

Caps: <=600s each bank/validator stage, allocated GPU<3GiB, process RSS<4GiB,
all new study artifacts<200MiB. Include checkpoint/source identity rechecks in
stage timing. Freeze/hash time is recorded separately from neural bank cost.
No outcome-dependent tolerance/cap/window/noise/step/density rescue. Any source,
interface, replay or validation failure stops, preserves partial/full bank,
frozen code and INCOMPLETE, and requires a disclosed separate amendment before
repair. A pass means only extraction is usable without altering native behavior.
No accuracy, calibrated confidence, correspondence learnability or originality
claim; no automatic permission to train.

## Handoff

Report protocol/freeze/bank/seal/independent validation and cost; update AGENTS,
dated phase record, STATUS,HANDOFF,NEXT_ROUND_PLAN. Keep all old immutable studies,
negative stops, official GT/metrics, unknown checkpoint membership and09 physical
discrepancy. Original HEADs/branches/dirty work preserved. The conditional later
readout requires explicit fitting scope and honest site/data roles, matched
trained direct-descriptor/independent-token controls, measured-point correspondence
and coupled motion losses, and local rotation/translation plus native system
ter/ATE confirmation. Finite tokens alone are insufficient to select a head.
