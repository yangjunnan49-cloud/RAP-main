# O3: fixed-budget source allocation

Declared 2026-09-13 before O3 inference. Compare the saved O2 budget-12 arm
against a new source-balanced arm on all four explicitly bound fresh frontends.
Recompute descriptors and both ranked proposer lists, capped at 12 each, using
unchanged O2 thresholds. Selection: take the first six unique proximity pairs;
then the first six SC pairs not already selected; if fewer than 12 are selected,
backfill from remaining proximity then remaining SC order. Normalize pair order,
deduplicate globally, preserve selection order and stop at 12. This quota grants
SC selection opportunity; membership may still overlap the proximity list.
No GT ranking, spatial suppression or per-sequence rule. No extra proposer budget.

Fresh RAP verification uses seed 42, shared RNG in the selected order; all O2
registration, gate and backend settings are unchanged. The O2 baseline is reused,
not timed again. This compares whole selection policies, including RNG ordering,
not isolated edge-set effects. Save both proposer lists and selection allocation.
Require regenerated proposer lists to equal the saved O2 budget-12 lists.

Use the O2 integrity checks: full source binding, source/input hashes, complete
attempts and generations, exact measurement-edge associations, gate and rotation
checks, saved finite trajectory evaluation. Hash baseline metrics/candidates/events.
Report first-pose and aligned LiDAR APE, separate camera KITTI drift (custom
LiDAR drift for POSS), attempted/accepted labels, pair overlap, SC allocation
versus SC-only membership, and separate monotonic stage costs. Baseline timings
come from O2; new timings are single warmed observations, not speedup estimates.

Predeclared screen: improve first-pose APE by more than 1e-6 m on at least three
of four sequences, no sequence regresses by more than 5%, and no dangerous edge
is accepted. Report saturation and secondary regressions. No production default
change based on this development screen alone. If it fails, consolidate O1-O3
and diagnose specific measurement/selection limitations before another experiment;
do not continue an unbounded quota or threshold sweep.
