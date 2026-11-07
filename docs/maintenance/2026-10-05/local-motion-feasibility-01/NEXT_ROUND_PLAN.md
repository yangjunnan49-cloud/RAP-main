# Next bounded stage: complete fixed-census causal local accuracy screen

Planning/design only. LMF0 engineering is validated in attempt-02; no local
accuracy protocol, evaluator, bank, freeze or GT result is created by this plan.
Do not infer accuracy or a trajectory gain from LMF0. FDI1 confidence arm and
all other stopped mechanisms remain stopped.

Use the identical58-window fixed-index census, six shared t=0 exclusions and
input order[t-1,t,t-2]; no GT-error ranking or selected favorable segments.
All windows are development exposure, including six engineering windows; unknown
weight training membership prevents held-out claims. No new seed/step/count/
voxel/patch radius/control search. Freeze exact protocol, runner, independent
validator, evaluator, all raw inputs, saved unoptimized KISS trajectories and
GT/calibration identities before complete-window output. Hashing GT files is
allowed at freeze; no GT numeric processing until all predictions are sealed.

Arms R3/R2/G3/G2 retain LMF0 definitions. Save exact points, features, noise,
raw/noisy endpoints, decoded poses, support transport and geometric iteration
records for every window. Saved KISS relative T=inv(O[t-1]) O[t] is the practical
reference; its dense running map gives more physical context than these local
arms, so that comparison cannot causally isolate learned registration.
R3 vs G3 has matched3000-point/three-scan support; R3 vs R2 tests added support
with explicitly different compute, not equal-total-budget novelty.

Proposed gates to finalize prospectively, before GT: paired median translation
error improvement of R3 versus each KISS/G2/G3 >=0.01m, paired median relative
improvement >=10% (denominator max(control_error,1e-6m)), and >=60% strictly
positive paired gains against each. Added-context attribution versus R2 requires
paired median translation improvement>=0.005m and >=60% positive signs. All
windows must yield finite valid outputs; no method-specific dropping/fallback.
For every sequence and KISS/G2/G3 control, mean translation error regression
<=0.01m and median paired rotation error regression<=0.05deg. Report sequence
and pooled values, pair-level rows, signs and failures; no significance or
independence claim from nearby deterministic sampled frames.

Use calibrated LiDAR GT with unchanged official conventions. Evaluate
E=inv(T_GT) T_pred, translation norm and proper-rotation angle, with a frozen
explicit treatment of serialized GT nonorthogonality. Independent reconstruction
must verify raw/point/feature/seed/census binding, all Horn pose fits, all
brute-force ICP controls, KISS and GT relative direction, every error/aggregate/
gate, complete bank identities and seal-before-GT stage ordering. Synthetic
direction/rotation serialization tests precede real evaluation. Provisional
caps1800s bank/eval/validation, GPU<12GiB, RSS<4GiB, artifacts<250MB, finalized
with the protocol. Preserve/disclose any engineering amendment, never tune gates
using GT or bank outcomes.

Failure stops this exact local layout before a trajectory trial, without
window/seed/step/budget/point-selection/initialization rescue. Pass only licenses
a separately frozen full causal trajectory comparison with unchanged retrieval,
graph and evaluator, direct material ter/ATE and sequence safety gates. Local
prediction accuracy and accumulated trajectory gain are separate claims.
Native three-scan RAP is not an original algorithm. Further RAP-specific
construction is conditional on evidence and still must beat matched controls.
No training or manuscript/default/production/Git changes scheduled.
