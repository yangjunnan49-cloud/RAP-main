# Before execution: bounded construction plan

Status: DRAFT_DESIGN_READY_FOR_EQUATION_PREFLIGHT_ONLY.
No stage below was implemented, run or experimentally frozen in this phase.
Owner authorization covers the next direction; do not re-ask the same permission
for reversible preparation. The requested current deliverable is research and
planning before execution. Every future stage separately freezes its protocol,
code, inputs, independent validator and stop rules before output.

## Hypothesis and layout

Different contexts around the same revisit anchors can propose conflicting
relative poses. Per-step rigid-input consensus feedback may create a correct
candidate absent from uncoupled generation and identical terminal consensus.
This is not an extra sensor measurement or an established original method.

Use six previously defined physical scans A,A1,A2,B,B1,B2:

- W_L=[A,A1,A2,B], caps[2000,1000,1000,2000], total6000.
- W_R=[A,B,B1,B2], caps[2000,2000,1000,1000], total6000.
- Native union U=[A,A1,A2,B,B1,B2], original caps, total8000 unique points.

Both windows share two distinct anchors. Cache points/features once per unique
scan within each pair, preserve rows, and reuse them across all arms. Ignore
stored motion matrices. Rebuild standard window centers/scales and verify
them; do not assume equal scales. This cross-visit construction does not reopen
LMF1 local three-frame odometry or F2 odometry-transported group projection.

## StageD0: next action, CPU equation/solver preflight

Implement an isolated CPU projector and independent validator only. Synthetic
points/analytic velocities, no RAP/descriptor inference, dataset GT, local
error screen or trajectory. Preserve all existing source and banks.

Prospective two-window solver for the report's objective:

1. Independently proper-Kabsch fit raw metric endpoints; fix G_L=I only.
2. Initialize G_R by weighted proper Kabsch from the two shared metric raw
   endpoint arrays in W_R to the corresponding arrays in W_L, with weights
   1/(d_i n_i). This includes translation from the weighted centroids and is
   equivariant to independent window coordinate changes. Reject an undefined
   fit; no alternate initialization chosen by outcome.
3. At fixed gauges, fit shared Z_i to repeated original rows and metric targets
   with the stated weights. Unique factors attain their independent fit.
4. Update G_R using both shared anchors only. Unique factors have
   gauge-invariant minimized cost and must not become spurious gauge votes.
5. At most64 sweeps; objective-change tolerance1e-12 relative to
   max(1,previous objective). Evaluate the profiled objective: shared residuals
   plus each unique factor's independent Kabsch minimum, a gauge-invariant
   constant. Do not score stale unique poses after a gauge update. Record the
   full trace/counts and recompute unique poses at final gauges. Nonconvergence
   is engineering failure, not an output silently admitted. Global optimum
   is not claimed.

Freeze these choices before synthetic output. Check uniqueness of every
Kabsch fit as well as input noncollinearity: arbitrary raw targets can collapse
and produce a degenerate cross-covariance even for valid input geometry.
Such undefined fits fail explicitly. A correctness repair can precede a new
freeze with disclosure, but real accuracy must not choose the solver.
Single-window and one-shared-scan cases use their exact native/analytic
reductions. Larger-tree cases are independently checked by the proof's
closed-form incidence propagation, not by implicitly extending this two-window
iterative solver into another generative algorithm.

| Required synthetic case | Expected interpretation |
| --- | --- |
| Single window with nonrigid raw endpoints | Native independent rigid-fit reduction |
| One shared scan, and larger tree incidences | No relative-pose effect after return to local frames |
| Dual shared anchors already consistent | Rigid-manifold no-op/idempotence |
| Different context predictions conflict | Relative effect beyond common gauge |
| Different known scales/centers | Correct metric decode/return; no estimated scale |
| Common/independent window gauges | Projector-relative identities with one gauge fixed |
| Point/incidence permutations | Correct row mapping and stable output |
| Noncollinear planar points | Valid proper SE(3) |
| Coincident/collinear shared points | Explicit degeneracy failure |
| Consistent relative pose wrong by2m | Zero agreement residual, unchanged error; mechanism limitation |
| Prescribed constant velocity sequence | Agreement when projection/flow commute analytically |
| Analytic state-dependent toy velocity | Demonstrate actual feedback/noncommutation; no real accuracy claim |

Proposed tolerances:1e-9m points,1e-9 maximum matrix entry for coordinate/no-op
identities,1e-10 determinant/orthogonality. Use32 deterministic nondegenerate
geometries plus adversarial cases; <=120s CPU,<=1GiB RSS,<=20MB artifacts.
Independent Horn/quaternion/explicit translation cases and objective checks
must replace merely replaying the same projector. These are proposed bounds.

All identities and expected failures must pass. Reduced shared residual alone
is not admission. Gauge-only effects or terminal-equivalent feedback stop
before GPU. Engineering success does not clear originality.

## StageD1: conditional GT-free four-pair engineering

Only afterD0 passes and a separate D1 protocol/code/source freeze. Select
the first two original F2 input rows for00 and08 without parsing strata/errors:

| Sequence | Anchors | A supports | B supports |
| --- | --- | --- | --- |
|00|24,629|21,18|627,624|
|00|210,1656|205,199|1653,1650|
|08|569,1554|566,563|1551,1548|
|08|583,802|580,577|798,792|

These structural IDs were read in this design audit; their estimated motions
and GT are not operator inputs. Use sanitized whitelisted identity manifests.
Proposed caches are F2 processed points and matching C1 features, with
allow_pickle=false and exact source/row binding. Independently reconstruct
under recorded parent seeds, then reuse the canonical cache; do not separately
extract per window. Cache mismatch stops engineering instead of substituting
a feature recipe. Different legacy pair/cap/seed means a different cache.

Reuse strict safe344/58-key loading; checkpoint split stays unknown. Prove
old native N0 using its original F2 saved noise[0], separately from the new
trial noise. Prove disabled-coupling replay on the trial's matching native
window input/noise. Unchanged five Euler steps;
no point/feature/window/seed/step/weight/noise/solver sweep.

Noise choice: independently drawn once per window instance from fixed
pair/window seeds, identical across C/I/F and retained unchanged. For U take
one predetermined instance row per unique scan with standard Gaussian
marginal. Freeze that mapping; do not transform noise or equate noisy states.

| Arm | Operation | Comparison role |
| --- | --- | --- |
| I | Two uncoupled native windows, retain both anchor poses | Same inputs/noise/neural work |
| F | I with the identical joint projector only at final raw clean endpoints | Direct feedback-versus-terminal comparison |
| C | Joint projection every step, new model calls, projected final pose decode | Candidate operation |
| U | Native all-six-unique-scan generation | Complete-context reference |

C/I/F use10 neural calls and60000 point-steps. C projects five times, F once,
I never: exact matched neural work, not total computation. Report extra solver
and total time; no artificial dummy cost. U uses five calls/40000 point-steps;
global-attention proxy64000000 versus72000000 per step, and part/linear work
also differs. U is same-unique-input, not exact-compute.

Save input/features/IDs, conditions/scales/centers, fixed noise, all raw and
projected clean endpoints, noisy states, gauges/scan poses, solver traces,
velocity responses and timing. Never replace raw endpoints with projected
ones. Check repeat/dummy-GT invariance, RNG/precision restoration, mapping,
valid rotations and next-step model effect; seal all GT-free output before
independent validation. Relative/raw-prediction effect must exceed its measured
numerical floor; enforced agreement is insufficient.

Proposed caps:30min cumulative GPU,12GiB GPU allocated,8GiB RSS,1GB artifacts.
No label/efficacy calculation. This stage proves engineering only.

## StageD2: conditional candidate screen

A separate protocol is required before any full generation/label read.
Write the domain-specific construction versus nearest prior art, cost
frontier, generation count, output choice and material gates first.
A standard-method migration cannot replace the original-breakthrough objective.

Proposed population: all200 original F2 exposed-development pairs, including
ordinary/low-overlap/ambiguous/confuser cases. Hard08's41 native-K4-unavailable
positives remain an evaluator-only subgroup. No method-specific dropping or
GT-error ranking; include failures in denominators.

Candidate creation precedes selection. Compare C with F, both I outputs and
native U at prospectively declared lower/higher budget endpoints. Fixed U K4
andK8 for C K4 is a possible frontier, with differing costs reported honestly.
Use D1 engineering costs, never accuracy, to finalize budgets before output.

M1's five-strict/three-interior floors are proposed minimum material standards,
not passed gates or relaxed old stops. "Recovered" must mean a correct C
candidate unavailable from fresh direct controls at declared budgets, not
only absent from the old native K4 bank. Add paired net availability and00
ordinary/confuser safety gates. Exact new efficacy/safety rules remain to be
fixed in the separate D2 protocol before generation.

Seal complete GT-free banks and independent source/geometry checks before
official evaluator labels. Oracle availability supplies no executable selector.
Selection/acceptance needs a separately defined GT-blind rule and unchanged
common geometry gate. Enforced agreement is never a confidence certificate.

## StageD3 and stopping

Only material candidate creation plus GT-blind selection/safety can license
a separate all-online-attempt system protocol. Keep KISS/retrieval/evaluation
fixed for attribution; assess ter and aligned LiDAR ATE plus sequence safety.
Pair accuracy does not imply a trajectory gain. Resolve or disclose training
membership/exposure before a confirmation claim.

Stop on algebra/identity/source/engineering failure, missing benefit over
terminal/native context controls, or safety failure. No alternate shared
scans/noise/weights/density/schedule/cohort/graph rescue. Preserve failed code,
freeze and partial banks; disclose correctness-only repairs with new freezes.

No training, production/default/model/manuscript or Git change is planned.
Future isolated implementation follows repository boundaries and actual
write permissions; no production sampler or frozen helper is edited.
