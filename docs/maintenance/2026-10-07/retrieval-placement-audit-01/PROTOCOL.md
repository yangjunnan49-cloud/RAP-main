# LC0: fixed-budget retrieval exposure and measurement-placement opportunity

Prospective protocol, 2026-10-07. Owner requested proceeding after PFG1.
This is a diagnostic on six previously exposed E0 A sequences, not a method,
independent confirmation, physically achievable result or global ceiling.

## Question and scope

Can useful measurement locations absent from the original shortlist offer both
KITTI ter and aligned LiDAR ATE opportunity at maximum12 loops per sequence?
Reconstruct all original71 attempts before GT. Preserve all prior negative
stops, banks, labels, source HEADs and dirty work. No inference, training,
production/default/model/manuscript changes, acquisition, installation or Git.
Only isolated algorithm/orchestration/validator additions and handoff records.

## GT-free bank

Sequences00/05/06 development and07/09/10 exposed-transfer; all original source
frames, odometry and keyframes. Hash the1800 keyframe raw scans and compare
them to the original E0 input freezes. Do not read the GT-containing generation
records: parse only candidate_started lines for i,j,attempt_id. GT/calibration
files are hashed without parsing poses until independent bank validation.

Raw float32 XYZ: native range>=1.5m before KITTI vertical correction0.205deg,
no maximum range. Full corrected scan feeds native float32 Scan Context:
20rings,60sectors,80m radius,z_offset2,maxheight, native ceil bin boundaries.
Native float32 ring-key distance and stable ordering are preserved, including
ties and float32 reductions. Temporal eligibility is source-frame j-i>=200.
Proximity: odometry distance<15m, stable i-outer/j-inner sort, first12.
SC: per query j, ring-distance order with i-ascending ties, first10; native
60-shift cosine distance<0.25; stable global distance sort preserving j then
ring rank; first12. Merge proximity first, SC second, canonical dedup, first12.

Persist all eligible pairs, distances, per-query ring ranks, SC scores/shifts
or -1 for unscored, pass masks, ordered pre-cap/capped/final lists. Replay the
native producers and all original attempt identity/order exactly. Independently
reconstruct all corrected raw inputs/descriptors and retrieval filters/ranks.
Native replayed full graph must agree with saved E0 within1e-5 per entry.
If faithful reproduction fails, stop before GT and disclose; no silent new
retriever or tolerance/rule change. Fixed descriptor boundary/empty/tie fixtures
also run after freeze. Seal the complete bank, then independent validation and
its seal before any GT pose parsing. Sources/bank hashes remain unchanged.

## Evaluator-only coverage and placement

Position-proxy GT-near means LiDAR GT translation distance<15m. GT-far is its
complement. This is a place-radius exposure proxy, not scan overlap, physical
correctness or strict registration success. Mixed queries have both near and
far pairs in a stage; this records ambiguity exposure without asserting alias
identity. Report every denominator: eligible, SC top10, SC pass/pre-cap/cap,
proximity pre-cap/cap, union pre-cap and final, near pairs/queries and mixed
queries. Missing coverage cannot be called executable retrieval recall.

N: original accepted58 measurements with original weights and poses.
C: original final shortlist, keep GT-near pairs in original order.
P: union of native proximity/SC pass sets before global caps, GT-near only.
H: all structurally eligible pairs, GT-near only.
P/H fixed selection: for each query j choose its nearest GT historical i,
ties smallest i; sort queries ascending; K=min(12,number of queries), take
mid-quantile positions floor((k+0.5)*number_queries/K), k=0..K-1.
C retains all eligible original pairs (<=12), no temporal redistribution.
C/P/H edge T=inv(GT_i)GT_j. All share fixed sigmas[.03rad]*3+[.20m]*3,
Huber1, native odometry[.05rad]*3+[.30m]*3, prior[.01]*6, LM100 and original
piecewise-constant dense propagation. Oracle mean_dist=1 is an explicit common
reference noise, not measured geometry/confidence. No tuning by GT results.
Counts may differ across arms; report them. P/H versus C diagnoses availability
and placement together, not a location-only causal effect at equal edge count.

Use unchanged official LiDAR GT/calibration: aligned LiDAR ATE, camera KITTI
ter/rer, first-pose anchoring, original segment convention. Independently
rebuild selections, graphs, all dense trajectories and every metric segment.
Tolerance graph/dense1e-5, metrics1e-8, exposure/ranks/attempt lists exact;
SC numerical reconstruction max1e-6 with exact lists/filters required.

## Frozen decisions and limits

For each P/H cohort, material requires mean ter gain>=.01 percentage points
AND aligned ATE gain>=5% versus N, and strict improvement versus C in BOTH
cohort means. An arm is actionable only if at least one cohort meets those
conditions AND all six sequences pass ter<=N+.01pp and ATE<=1.05*N.
Report all component gates and both cohorts. Prefer P if actionable; otherwise
H if actionable; otherwise NO_FIXED_BUDGET_PLACEMENT_SIGNAL. These are bounded
opportunity gates, not proof a GT-blind method can attain the oracle.

Each freeze/bank/validation/evaluation stage<=1h CPU, peak RSS4GiB; all new
artifacts<=500MiB. Single-thread scientific runtime already installed. No GPU.
Failing stages preserve original code/freeze/partial bank and INCOMPLETE.
Do not change density/radius/budget/selection/cohort/noise to rescue a result.

## Follow-on boundary

Actionable P motivates a separately designed cheap GT-blind new measurement
ranking/source at unchanged neural budget. Actionable H alone motivates an
accessible independent retrieval cue first. Neither motivates a bounded stop
and distinct local source or explicitly authorized new supervised scope.
No follow-on experiment or fitting is automatically authorized by LC0.
09 physical discrepancy, unknown checkpoint membership and RAP originality
remain unresolved; generic retrieval/distribution controls are prior art.
