# RPC0 prospective reference/physical consistency diagnosis

## Fixed cases and purpose

Prior temporal-identity-audit-01 already checked six sequences, complete filename/time bindings and190 local -10/+10-frame controls, without independent sensor trigger/OXTS evidence. Do not repeat that study as new evidence. This distinct census checks tightly adjacent physical returns, raw source-point identities/partitions, a representation control and coordinate-axis meaning around the first original admitted loop00(2429,3373) and09(0,1574), independently of new outcomes.

For each endpoint retain offsets[-1,0,+1] inside sequence bounds, with every boundary exclusion recorded. Total11 raw scans: six00, five09. All Cartesian revisit combinations:9 for00,6 for09. Adjacent same-visit controls use each existing +/-1 neighbour once (four00,three09). Future-neighbour controls are offline/noncausal diagnostics. No alternative offset is selected, fitted, used for scoring or promoted to a pose.

Freeze original raw/reference/odom/calibration/time/frame-manifest/summary/MGR prediction bindings, both new helpers, existing corrected supervisor, package versions, earlier validated audits/deliveries before numerical payload. Recheck all MGR0 frozen1567 and344 delivery identities (including Linux library sources without importing their models). Verify full available sequence counts, filenames, absolute paths, consecutive source IDs, timestamp equality/strict monotonicity and pose rows for00/09. These are internal consistency, not independent archive provenance.

Inventory only the exact00/09 dataset directories for per-scan and per-point timestamps, OXTS, trigger, calibration/rectification, semantic dynamic labels and archive receipts. Preserve path inventories/absence as scope-limited observations; do not claim the files do not exist elsewhere. Official KITTI/author SDK documentation establishes intended format/convention only, not authenticity or correct synchronization of these local files. No dataset download.

## Physical corpus and observations

Parse original little-endian float32 XYZI records; preserve raw source-point IDs. Complete reason labels: nonfinite, range<1.5m, range>80m, finite in-range cap-excluded, selected. Select4096 in-range returns without replacement by NumPy PCG64 seed derived from SHA256('RPC0|seq|frame'), then sort source IDs. Fewer4096 is a prerequisite stop. No voxel, normal, outlier or dynamic-surface filtering/registration. The fourth component is interpreted as intensity under the existing dataset schema, not per-point time.

Use identical selected IDs for two fixed representations: RAW coordinates and CORRECTED idealized float64 KITTI+.205deg radial correction. This is a diagnostic representation comparison, not a production parameter trial. Store pointwise displacement and analytical bound2*r*sin(theta/2). No scan-motion compensation or synthesized acquisition timestamps. Input corpus/census seal before new numerical reference calculation.

Predefine16 source-return strata: four sensor azimuth quadrants x range[1.5,20)/[20,80] x raw sensor z< -1 / >= -1. Labels use uncorrected source coordinates/IDs and do not change with pose. These are observed-coordinate partitions, not semantic ground/dynamic labels or verified shared surfaces. All16 counts, empty/low-support strata and NN within/outside1m/2.5m are retained. Eligibility for descriptive paired contrasts:>=64 source returns. Never choose subsets/poses based on residual or reference score.

## Coordinate checks and fixed geometry

Official intended calibration Tr maps LiDAR to rectified cam0; camera poses C map cam0 to camera0-world. V=Tr^-1 C Tr and G_ab=Tr^-1 C_a^-1 C_b Tr. Independently check absolute/relative conjugation, roundtrip and direction (<=1e-8), synthetic known rigid fixtures and common-gauge transfer. Preserve original rounded arrays and use general matrix solve/inverse; do not silently replace official poses by projected rotations.

Fixed anchor predictions N/RI/W/J come byte-identically from MGR0 index0, K from original odometry. For each neighbour pair(a,b), transfer them with local KISS only: O_a^-1 O_i T_ij O_j^-1 O_b. G uses directly calculated reference V_a^-1 V_b; G_transport applies the same KISS transfer to anchor G, a local-reference mismatch control. All seven arms are diagnostics, not performance candidates. No independent GICP or model is run. Shared W/J outputs and any exact equal transforms may reuse distance arrays with explicit aliases, without counting them as independent observations.

For both representations and all15 pairs/7 arms, retain every directed NN distance, deterministic target ID (nearest distance/index tie order), symmetric mean/median/q90 and overlap<1m/<=2.5m, censored2.5m MSE and all16 stratum census records. Query against full retained target support, not outcome-selected patches. Analytical NN change bound is source displacement plus maximum target displacement (including reference rotation operator norm). Check it, but do not infer a unique calibration cause from it.

For seven adjacent controls compare fixed original odom/reference motions on both representations. Report local t/R disagreement, elapsed time and pose-implied one-frame displacement envelope t+2*80*sin(R/2). This envelope describes observed inter-frame pose change, not actual within-scan motion, timing uncertainty or a proof of deskew correctness.

At each anchor express G-minus-N translation in endpoint-i LiDAR, LiDAR0-world and camera0-world axes with explicit rotation maps. Do not call any axis gravity/world vertical without independent attitude/physical evidence. Describe unchanged pose-reference errors only; no new KITTI/system score or reference correction.

## Prospective diagnostic classifications and stopping

Binding/calibration checks pass separately from physical truth. Local immediate agreement flag: each sequence's median local translation disagreement<=.20m and R<=1deg, following an explicitly new small-census description (not amendment of old gates). Revisit discrepancy flag:09 median G-minus-W symmetric mean distance>=.5m in both RAW/CORRECTED, at least5/6 neighbour pairs retain that gap, and a majority of eligible source-return strata retain>=.5m gap. Retain complete00 comparison and all adverse strata. Flags classify observed patterns, not correctness or calibration certificates.

If binding checks and local agreement hold while broad revisit discrepancy persists without independent provenance/sensor evidence, report `AVAILABLE_BINDINGS_VALID_BROAD_09_CONFLICT_PHYSICAL_CAUSE_UNRESOLVED`. Otherwise report `BOUNDED_REFERENCE_PHYSICAL_CENSUS_COMPLETE_WITH_UNRESOLVED_PATTERN`; never tune thresholds or expand offsets to force a diagnosis. Completion is this bounded audit, even when physical truth is unresolved. No further refinement or automatic repeated local audit follows without new evidence.

Independent validator implements raw labels/selection/correction, calibration/transfer equations, brute-force SciPy cdist nearest points/ties, every stored distance/stratum/aggregate/axis vector, aliases and classifications separately; no runner metric/construction imports. Recheck frozen identities and corpus/output ordering. Raw input metadata authenticating actual acquisition/deskew/reference accuracy may remain absent; do not certify it from numerical replay.

CPU only, combined900s child payload/2GiB full RSS/256MiB whole new dossier, attempted failures/validation included. Existing12GiB launch/4GiB observed host-commit guard, durable stdout/stderr/Windows launch/exit/host observations/full child ru_maxrss, remaining-budget alarm. Imports/WSL startup/design/final bookkeeping are separate; no old caps/gaps amendment or full production latency claim. Freeze before payload; preserve failures/sources/output routes.
