# CCR0 prospective causal observation feasibility

Question: do two preceding physical scans add safe registration information around the original frozen RAP loop pose, beyond a single scan at matched retained-return count and matched maximum solver work? This is ordinary submap geometry and development evidence, not a novel RAP mechanism or certified physical truth.

## Fixed population and observations

Retain all 58 original E0 A admitted loops in stored order: sequences 00/05/06/07/09 have 12/12/12/12/10 loops. Retain every endpoint, including frame 0 and any failed/unsupported output. Sequence 10 has no admitted loops. Pilot is index 0 in 00/05/06, chosen before new labels. Do not retrieve new edges, select favorable windows, delete 09, replace the reference or import historic error fields into deployable records.

One fixed causal history is frames max(0,a-2)..a, oldest to newest, aligned into endpoint a by inv(O_a) O_h using the original frontend trajectory. No future scans, cross-visit alignment or reference enters construction. Original frontend rounded rotations receive the same determinant-corrected SVD projection as SGC0, defect and change <=1e-5; translations unchanged. History is uneven at boundaries and explicitly counted. No deskew, synchronization or physical-provenance correction is inferred.

Five observation arms per endpoint:

|Arm|Returns|Purpose|
|---|---|---|
|A|Exact original MGR0 4000-point physical cache|Historical preprocessing control|
|S|4000 actual returns from current scan|Single-scan source-ID baseline|
|C|4000 actual returns balanced across available causal history|Matched-count context|
|F|4000 actual returns per available scan, up to 12000|Full causal context, extra work|
|D|len(F) actual returns from current scan|Density control matched to F|

For S/C/F/D, reject nonfinite XYZI or range <1.5m; do not impose a new upper range, voxel centroids or outlier pruning. Use exact raw row IDs with a seed derived from SHA256('CCR0|sequence|frame'), PCG64 permutation of eligible IDs, nested prefixes, and sorted retained IDs. Apply the existing +0.205-degree intrinsic correction in float64. C quotas divide 4000 evenly across available frames, with remainder assigned to newer frames. F uses the 4000 prefix per frame. S is a subset of D; every C selection is a subset of F. No duplicate (frame,row) IDs. Raw-return policy differs from A; C-vs-S and F-vs-D isolate context within the common new policy, while A discloses that policy difference. Do not attribute S-vs-A changes to context. All used raw files, original bindings, frontend, reference and installed numerical dependencies are hashed before payload.

## Fixed solver and controls

Use installed Open3D 0.19 CPU only, process-local CUDA_VISIBLE_DEVICES empty before import. Reuse immutable MGR0 numerical functions: 20-neighbor PCA with deterministic distance/index ties; invalid normals become isotropic and are flagged; C=I-.999 nn^T is a shape, not calibrated covariance. GICP correspondence 2.5m, epsilon .001, L2, max80, relative fitness/RMSE 1e-6. FPFH radius2m/max100, FGR seed20261012/64 iterations and all MGR0 settings unchanged. No radius, history, point count, normal, initializer, selector, gate or iteration sweeps.

Each arm computes RI (original RAP initializer), GI (identity), GK (original frontend relative), GF (FPFH-FGR). Geometry W selects GI/GK/GF; RAP J selects RI/GK/GF. Both allocate three refinements; shared candidates are charged to both bundles. This matches maximum refinement count within an arm, not total pipeline time. F/D have three times the point capacity away from boundaries; actual reads, preprocessing, PCA, FPFH, refinement and selection times are recorded. Historical RAP generation is inherited, not free new generation or measured current production latency.

Candidate support and selection retain MGR0 rules: finite/proper SE3, >=100 valid mutual associations, both directional overlap >=.7 within2.5m, symmetric unregularized point-plane rank6 at relative1e-6. Minimum symmetric censored all-point squared NN distance, fixed tie order. Unsupported/failed J/W falls back to unchanged N and remains in denominators. Record every FGR/candidate failure, support/rank/cost, selected and rejected candidates. No heldout/reference selector. This stage has no new future-scan holdout: S/C/F/D endpoints reuse correlated data; no independent physical accuracy is inferred.

## Order and gates

Freeze before numerical execution. Synthetic transport/direction/gauge/no-op/boundary/source-ID/nesting/correction fixtures and derivative/support/rank/ambiguity fixtures must pass an independent validator. The GICP recovery replay uses the installed shared solver and is labelled accordingly. Build and seal every input. Independently reconstruct raw selections, correction and transports for all inputs; recompute PCA/covariances for all points from stored neighbors, and independently verify neighbor membership by brute distances at 32 evenly spaced rows per new cloud. This bounded membership check is not a full brute-force replay of every neighborhood.

Run fixed three-edge pilot for all five arms. Every RI and W/J must have declared support and finite outputs in the pilot; an observed unsupported pilot is a prerequisite stop, not evidence that all possible contexts fail. Independently rebuild support/selection before expansion. On a pilot stop, seal, score and report only that pilot; no alternate settings or favorable pilot replacement.

If pilot passes, compute complete 58-loop/five-arm bank (1160 maximum GICP candidates), retaining three pilot outputs byte-for-byte. Seal all predictions before new numerical reference access. Independently validate all support, objectives and selectors. Replay the three pilot S/C outputs with the same installed solver; this is shared-solver reproducibility, not independent GICP. Then evaluate original calibrated official-reference relative translation norm and rotation geodesic, without treating that reference as independently authenticated physical truth. Historical RPC0 09 conflict remains reported separately.

Engineering headroom requires BOTH C-J vs S-J and F-J vs D-J to pass: mean translation >=5% lower, mean rotation nonworse (+1e-10 degrees), >=44/58 joint nonworse (t/R tolerances .01m/.01deg), q90 t/R <=1.05 baseline +.01, each sequence mean t/R <=1.05 baseline +.01, no individual t/R harm >.2m/.2deg; >=52/58 supported J and >=90% per sequence. Also C-J/F-J each require >=5% mean translation gain vs original N, mean R nonworse, and the same N-relative tail/sequence/individual/joint guards. F-vs-C reports extra-work response, without being a substitute for either primary control. A/S and all W outputs are reported regardless. J-vs-W >=5% mean t gain plus nonworse mean R and the same sequence/tail safety is separately reported as initializer increment; it is not novelty or a learned context mechanism. Gates are fixed before new results, not amendments of MGR0/PG-DEV.

Only a passing engineering conjunction permits separately scoped unchanged-graph full trajectories or a frozen-feature residual feasibility study. Failure retires this exact three-frame/raw-ID observation construction; no rescue sweep. NOC4 reproducibility remains a prerequisite for native adapter updates. A distinct frozen-feature route would need its own target-free exact extraction, independent derivatives, functional-step, equal-active-capacity and strong/equal-work geometry controls.

## Resources and preservation

New combined scientific-child budget 5400s including imports, freeze, failures, preparation, solver replays and validators; full process RSS <=4GiB, new dossier incl supervision <=1GiB, GPU calls0. Final documentation/seal bookkeeping is recorded separately. Existing12GiB launch/4GiB observed host-headroom guards and durable Windows/child exits/peaks apply; no process restart. Include every attempted child, not only successes. No historical budget/gap backfill. Exclusive output directories and immutable failed sources/receipts. Independent equation errors: transport/correction <=1e-8m, PCA covariance <=1e-8, support matrices relative <=1e-9, selector score/objective <=1e-8, pose metrics <=1e-8, shared solver pose <=1e-5. Retain all earlier seals, negative stops, physical/site/checkpoint unknowns and original HEADs/branches/two-nine tracked dirty sets.
