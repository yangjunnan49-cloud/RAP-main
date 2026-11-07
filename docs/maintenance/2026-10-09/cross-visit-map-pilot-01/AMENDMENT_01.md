# Implementation-only rigid endpoint retraction repair

Original51entryfreeze and all sources/snapshots remain immutable. Original
preflight failed perfect-input no-op<1e-8 before real coordinates or evaluator
poses. Separate same-fixture diagnosis records Fdelta3.200699603e-7 versus
J8.881784197e-16; initial Fgradient<9e-15/full-rank H, no physical step warranted.

The F move recomposed its endpoint as E' rigid_inverse(E) E along with other
scans. In finite precision this repeatedly multiplies E^T E into the endpoint,
amplifying small SO3 orthogonality error (roughly cubing matrix error). Repair
only assigns the endpoint directly to its computed E' product retraction;
nonendpoint poses retain the same mathematical E' L_i map. No additional solve,
projection, stopping rule, threshold, membership, budget, gate or dataset change.
The exact same full synthetic preflight must pass under all original tolerances.

Preserve original helper/staging/runner/validator/freeze, failure/diagnosis,
RESOURCE_LOG and INCOMPLETE. Deploy a distinct cross_visit_map_attempt02.py,
separate orchestration/validator wrappers and attempt-02freeze/output directory.
Include all original failed/successful measured stages in the new combined ledger;
their original ledger stays unchanged. No real point/GT outcome exists before
this amendment. All scientific settings are the unchanged prospective protocol.
