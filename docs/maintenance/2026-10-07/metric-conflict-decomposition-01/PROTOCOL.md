# MDC0: evaluator-only decomposition of the sealed LC0 metric conflict

Prospective computation protocol2026-10-07; the LC0 pattern was already
observed: lower aligned ATE with higher development ter. Owner said continue.
This is post-hoc explanatory accounting, not a prospective method screen,
physical causal attribution or permission to rescue any stopped arm.

## Fixed inputs and computation

Freeze this protocol, isolated algorithm, runner, independent validator,
LC0 source/results/validation seals and exact N/C/P/H trajectories/segment
records on00/05/06/07/09/10, plus their unchanged official GT/calibration.
No new graph, inference, feature extraction, training or changed trajectory.
Every original LC0 KITTI segment participates; no favorable subset/threshold.
The entire analysis uses evaluator GT; do not call it a GT-free bank.

Let g=pG_last-pG_first and e=pE_last-pE_first in the declared camera world.
Matrices R retain serialized numerical values; use general3x3 solves, not
transpose inverses. For each segment, length L, define

    u = solve(RE_last, RE_first solve(RG_first,g) - g) / L
    v = solve(RE_last, g - e) / L
    z = u + v

z is exactly the translation component of inv(deltaE) deltaG divided by L.
u is the start-orientation-associated term, v the endpoint-chord term. Their
squared norms add only with the cross term2 dot(u,v); do not assign them
nonnegative causal shares or equate them to calibrated uncertainty.

Two compulsory gauges:
F: independently first-pose-anchor GT and estimated camera trajectories,
the original KITTI convention.
A: from F fit one proper rigid/no-scale Kabsch alignment of estimated camera
positions to GT, then apply it to the whole estimated pose trajectory. Do NOT
re-anchor it afterwards. Translation offsets cancel in chords. Total z/ter is
invariant under that constant estimated-world gauge; u/v/cross may redistribute.
A resembles position alignment for interpretation, but is not the LiDAR ATE
alignment and never replaces any official metric.

Persist all u,v,z and first/last/length per segment, both gauges, plus the rigid
alignment matrix. Summaries for every sequence/arm/gauge: mean||z||*100 (ter),
mean u^2, v^2, cross and total^2 times10000, and cohort arithmetic means.
Report P/H minus N changes, signed accounting terms and gauge sensitivity.
No material improvement gate or executable-method decision is created here.

## Validation and limits

Fixed analytic cases: perfect poses, chord-only displacement, orientation-only
change and constant-global-rotation cancellation; they demonstrate why an
orientation/chord split is gauge-dependent. Independent validator imports no
new algorithm/runner, derives z via full4x4 relative-pose solves and v in the
estimated endpoint frame; u=z-v. Independently fit A with Horn quaternion
eigenanalysis rather than Kabsch SVD. Validate every serialized vector/summary,
LC0 segment identity/ter and both-gauge invariance.

Vector/summary tolerance1e-8, alignment1e-8, exact segment IDs; accounting
closure1e-10. Freeze before all decomposition outputs, seal complete outputs
before independent validation. Preserve failures and INCOMPLETE, no silent
repair. Each stage<=1h CPU,RSS4GiB,artifacts100MiB,no GPU. All original LC0
and older banks/stops remain immutable; both original HEADs/dirty work persist.

Conclusions are algebraic/descriptive. Dominant signed terms are not unique
physical causal shares; gauge sensitivity prevents blaming a single source.
This can narrow the next measurement-objective design, but does not validate
odometry covariance, sqrt(span) weights, new retrieval or a learned readout.
No production/default/model/manuscript edit, acquisition/install, commit/Git.
