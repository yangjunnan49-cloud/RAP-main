# Next hypothesis: actual cross-visit structure with retained internal poses

Status: CONCRETE_DESIGN_ONLY, no two-visit plane bank, numerical preflight,
optimization, endpoint accuracy or whole trajectory executed. SMP2 did not pass
its material-gain conjunction. This is a different information-source test,
not extra SMP2 steps, a favorable split or a declaration that SMP2 succeeded.

## What the completed round changes

Full point clusters resolve the measured support prerequisite. Four supported
windows and four valid poses yield3/4positive local aligned-ATE gains but only
1.138%mean, below5%. Mean structural-holdout RMS falls0.701%. Thus lack of
cross-scan support is a real representation issue but fixing it is insufficient
for this local objective/regularizer. It does not isolate whether the remaining
limit is prior stiffness, geometry bias, association, or little new information
in one already-tracked visit. No prior-strength search is selected.

The next specific question is whether observations from an actual second visit
can correct the relative submap placement and whether freeing internal scan
poses adds anything beyond a conventional rigid submap alignment.

## Concrete source binding

Use sequence00, original E0 A accepted-loop array index0:2429->3373,
measurement_id ef08402bdc746147a081b1137926970c29f435d724db04ef096c8f11d475977e.
No quality/GT sorting or alternate loop. Visits use the last8keyframes ending
at each endpoint:

- A:2378,2384,2391,2398,2405,2413,2423,2429.
- B:3318,3324,3331,3338,3345,3352,3361,3373.

Sixteen raw-frame/file-size/SHA256 bindings have been checked in
revisit-design-audit-01/attempt-02/results.json; coordinate payload has not been
parsed. Existing E0 source-frame mapping, odometry and original accepted RAP Z
are bound. The original JSON includes historical GT errors and was displayed
in this turn; selection uses only its prescribed array index and whitelisted
i/j/Z/measurement identity. This is exposed development, not GT-unseen evidence.
The metadata audit needed a disclosed frame-schema repair; original source,
freeze/failure/INCOMPLETE preserved. It changed no scientific SMP2 output.

## Proposed first engineering pilot

1. Preprocess these16original measured scans with the same range1.5..80m,
   +.205deg correction,.5m voxel and6000cap rule. Freeze before reading coordinates.
   Preserve variable point counts; no invented times or new deskew. Project saved
   rotations to proper SO3 with disclosed original/projection deltas, rather than
   interchanging general and rigid inverses on rounded serialized matrices.

2. Express each visit's internal O poses relative to its own endpoint. Anchor A's
   endpoint to identity. Initialize B with the fixed saved RAP Z, preserving B's
   internal O poses. Also retain the original odometry relative placement as a
   separate O reference. Z is initialization for geometry arms, not an extra
   factor counted alongside the same measured surfaces. No retrieval, acceptance,
   new RAP call or descriptor/readout fitting.

3. Construct unchanged2m eligible shared-plane patches at this common initialization
   using complete per-scan moments. Keep only patches observed in both visits,
   with unchanged>=3contributing scans/total>=40/per-scan>=6support and plane
   criteria. Membership remains fixed for this first diagnostic. Hash complete
   cross-visit patches with UTF-8 `CV1|00|2429|3373|2|{kx},{ky},{kz}`, SHA256
   first4big-endian bytes modulo4=0holdout. No scale/hash/flatness/point sweep.
   Prospective support:>=10training cross-visit patches,>=3contributing scans and
   >=100training points per visit;>=5holdout cross-visit patches. Show coverage of
   all16scans. Motion chains regularize unobserved interiors; that is not measured
   physical observability. On failure, keep this one source and stop; no next edge.

4. Compare **O / B / F / J** on identical inputs. B is saved RAP Z alignment with
   fixed internal O shapes:the one-loop relative-pose baseline. F refines only B's
   six rigid submap-placement variables against training cross-visit planes,
   keeping both visits internally fixed. J adjusts15scan poses with A endpoint
   fixed, against the same cross-visit patches, plus only the14within-visit motion
   edges at the existing.10m/.15deg scale. Do not connect the chronological gap
   between A and B with a fabricated adjacent edge. Normalize the regularizer by
   these14edges. Both geometry arms refit plane nuisance parameters;24updates and
   the same damping/backtracking. F and J share the same initial alignment. Report
   objective scaling and initialization basins; neither is calibrated covariance.

5. Internal corrections from each visit's fitted endpoint-relative initial shape
   remain bounded1m/5deg; endpoint placement correction from Z bounded5m/25deg.
   The F/J solver needs a new explicit variable/chain implementation in RAP-SLAM,
   because the existing helper assumes one chronological chain and pose0anchor.
   Synthetic checks must cover fixed internal shape, both independent visit gauges,
   absent gap edge, compact-vs-explicit Schur system, selected FD gradients, proper
   poses, and a planar unobservable displacement. Seal every pose before numeric
   reference outcomes; selected numeric/explicit-point checks suffice initially.

6. Evaluate held-out whole-patch RMS plus relative endpoint translation/rotation
   error, joint16node rigid-aligned ATE, and each visit's internal local errors.
   Geometry is consistency, not physical truth; official short-segment references
   retain their caveat. An engineering refinement signal for F or J versus B needs
   >=5%jointATE AND>=5%endpoint translation gain, endpoint rotation regression
   <=.01deg, no per-visit ATE/tRMSE regression>5% or mean rotation>.02deg, and
   holdout RMS ratio<=1.01. A distinct internal-pose claim additionally needs J
   versus F to pass the same conjunction. Preserve O/B/F/J regardless of outcome.
   If only F helps, the actionable direction is conventional rigid submap
   refinement; do not attribute it to internal BA or originality. A single case
   cannot establish system utility or statistical generalization.

7. New proposed CPU budget1800s/RSS2GiB/artifacts512MiB; no old budget amendment.
   If there is a usable signal, next confirmation uses first original accepted
   records of00/05/06 under a newly fixed cohort, then full unchanged ter/rer/ATE
   and timing. No automatic complete-sequence replay or production promotion.

## Details still not mastered

Cross-visit patch support and physical feature identity/dynamic contamination;
internal submap distortion versus simple rigid placement error; retention of
biased geometry selected for flatness at an already aligned initial pose; prior
stiffness/objective normalization and information already reused by KISS; local
minimum dependence on RAP Z; range-dependent preprocessing/calibration effects;
point-time and per-scan covariance/correlation unavailable; official reference
versus map-consistency conflict (especially09); checkpoint training/site exposure.
None is resolved by full rank, normal diversity, lower residual or this support
repair. No invented sensor-time model or metric/GT replacement is selected.

Established map bundle-adjustment work is eligible under the owner's originality
relaxation, including [BALM](https://arxiv.org/abs/2209.08854). The new information
source and controls make the hypothesis testable; they do not make it original.
