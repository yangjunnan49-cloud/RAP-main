# P0-02: deterministic descriptor preflight amendment

This is an engineering correction to the frozen
[`P0-01` protocol](../p0-point-selection-preflight-01/PROTOCOL.md).
P0-01's sealed four-pair bank failed independent descriptor reproducibility
because `MiniSpinNet.select_patches` shuffles its full support cloud with
NumPy global RNG and the original runner left that RNG unseeded. Preserve
P0-01 intact and do not interpret its descriptors as an efficacy result.

Keep the same first two F2 pairs in each sequence, all six scan identities,
0.25 m voxelization, outlier/FPS rules, fixed 8,000-point budget, complete
pre-outlier voxel support, 5 m descriptor radius, checkpoint, resources and
GT-free boundary. Immediately before extracting the six descriptors of a
pair, save NumPy RNG state, seed it with that pair's saved F2 generation-0
seed (`inputs_{seq}.json` field `seeds[0]`), extract parts in saved order,
then restore NumPy RNG state. This matches the C1/F2 scoped per-pair seed
convention; the new input support still differs from F2. FPS still uses
global Torch seed 42 in an isolated RNG scope. Stop if any exact budget or
resource condition fails; no outcome-driven seed adjustment.

Freeze this amendment, new runner/validator, source/weight identities and
all four pair input identities before running. Seal a new bank in this
directory; do not overwrite P0-01. Independent validation must regenerate
all 24 descriptors exactly under the declared NumPy seed, as well as the
original source/point/shape/resource checks. Retain `INCOMPLETE` on failure.
No GT, labels, RAP generation, training, default change or Git sync.
