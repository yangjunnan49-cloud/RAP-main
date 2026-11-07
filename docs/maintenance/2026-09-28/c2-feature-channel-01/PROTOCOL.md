# C2 fixed feature-channel intervention

Freeze before any new RAP generation. C1 found weak top-1 miniSpinNet
cross-visit information on native-K4-unavailable positives but measurable
information on ordinary pairs. C2 asks whether the frozen RAP flow model
responds materially to point-feature assignment. It is a small mechanism
diagnostic, not a new candidate route or efficacy screen.

## Fixed inputs and arms

Exact F2 observed-development KITTI00 and08 pairs at saved-order indices
[0,1,25,26,27,28,50,51,52,53,75,76,77,78] in each sequence (28 pairs;
two confusers and four per positive stratum per sequence). Generation0
only; fixed original F2 six corrected scans, caps
[2000,1000,1000,2000,1000,1000], same points/miniSpinNet features,
normalization, explicit saved noise, seed, RAP12 model, native five Euler
steps and rigidity forcing. No support-motion input, GT or evaluator
labels in bank generation. Same precision and request-local RNG scope.

Arm T uses true per-point features. It **must** reproduce saved F2 N0
raw clean-endpoint and noisy-state trajectories exactly (maximum absolute
delta <=1e-5) for all28 pairs. If any pair fails, stop
`INCONCLUSIVE_REPRODUCTION` before analyzing arm Q. Arm Q independently
permutes each of the six part's descriptor rows using NumPy PCG64 seed
from first8 bytes of SHA256(`C2|pair|part-index`), preserving each part's
feature multiset, point order, noise and model. Do not alter the anchor
geometry or acceptance gate. Save full Q raw/state trajectories, exact
feature permutation indices, decoded source-to-target pose, and paired
raw-final RMS/pose deltas. Decode poses with F2's unchanged per-part fit.

The RAP checkpoint must be loaded using `torch.load(weights_only=True)`
with only explicitly enumerated standard NumPy/OmegaConf classes as
restricted safe globals, and its state dict loaded into the same model.
miniSpinNet is loaded with `weights_only=True` and `strict=True` as C1.
Never use unguarded pickle loading. Exact T reproduction is the required
check that this safe loading path is equivalent to F2 inference. Freeze
protocol, runner, independent validator, all sources/weights and selected
inputs/GT identities before generation. Seal the whole Q bank before
evaluator-only GT/stratum analysis.

## Prospective reading and limits

Per pair, raw-final delta is RMS Euclidean displacement in normalized
model coordinates. Pose delta is norm of inv(T_true)@T_shuffle
translation in meters and SO(3) angle in degrees. A pair has material
pose response if raw-final RMS>=0.005 **and** pose delta is >=0.25m or
>=0.25deg. Declare `POSE_LEVEL_FEATURE_RELIANCE` if >=6 of the eight
fixed ordinary pairs respond. Otherwise declare
`FLOW_ONLY_FEATURE_RELIANCE` if >=6/8 ordinary pairs have raw-final
RMS>=0.005; else `NO_MATERIAL_FEATURE_RELIANCE`.

After the bank seal, report responses by sequence and stratum and
describe paired strict/accepted changes under the original F2 GT and
anchor-only gate. These are diagnostic on a small observed subset; no
claim of improvement, novelty, independent confirmation or model
adaptation follows. Do not select a favorable permutation or tune effect
margins. A flow response without a pose response suggests model channel
use that cancels in rigid decoding; a pose response says the channel
influences registration, not that its information is good.

Caps: <=10min bank wall, <=12GiB peak allocated VRAM, <=0.5GiB new
artifacts. Independent validator rehashes all frozen sources and bank,
checks28 exact T reproductions, permutation validity/content, Q raw
shape/finite state, independent pose decode and delta/evaluator/decision
arithmetic. Preserve old results/HEADs and do not sync Git.
