# DMF0 prospective protocol

This is one new global measurement-coupling screen. Freeze code and actual inputs before synthetic/real numerical stages. E1/SGC0/PFG/MGR/MMR/SMP/CV/MF stops remain. No per-pair optimizer, shared plane, altered retrieval, new loop or parameter sweep is included.

## Ordered stages and decision

component: inspect archived KISS 00/05 graph counts and existing installed source semantics without loading point coordinates or GT. It is a component inventory, not a causal attribution. The source resets KISS odometry at local-map boundaries, uses unit information for map-motion and loop factors, exports transformed world PLYs, and keeps source membership internally in local trajectories. If no explicit raw-frame membership accompanies the exported maps, do not transplant their graph to E0. Existing complete-system results are context only. Proceed instead with the bounded same-input backend comparison below, conditional on availability of every prescribed input. Missing inputs stop rather than select favourable replacements.

freeze -> synthetic -> validate_synthetic -> bank -> validate_bank -> evaluate -> validate_metrics. No numerical GT is read before the full 00/05 bank seal. Conditional extensions require a new prospective supplement; a failed primary conjunction stops this candidate.

## Inputs and arms

All 00/05 E0 A keyframes and all 12+12 admitted loops. Consume only i,j,T_rel,mean_dist,overlap,measurement_id from existing loop records; discard saved error/GT fields. Use every relevant existing MGR endpoint points array, 4000 points per endpoint, no resampling or normal recomputation. Bind cached bytes to the existing input seal. Bind original raw files via the established cache lineage without calling it a fresh independent raw reconstruction.

Project original nearly proper rotations by SVD with maximum allowed matrix change 1e-5, translations unchanged. Replay B with original pose graph, and verify against saved trajectories (maximum matrix entry delta 1e-3). Q and D start at that same B keyframe state and retain original E0 motion factors/prior and unchanged propagation. No original loop pose factor is added beside a geometric factor representing its observation.

B: current complete Pose3 loop graph. Q: frozen local quadratic of a declared censored symmetric point-to-point cost at B. D: identical cost with nearest-neighbour rematching and exact residual relinearization inside the global optimizer. This practical comparison combines rematching and relinearization; it does not separate their effects.

For each loop Z=Ti^-1 Tj, transform j points into i, and i points into j. Match all points in each direction to the closest target using cKDTree workers=1. Maximum Euclidean distance c=2.5m. For distance d<=c use radial Huber cost h(d)=d^2 for d<=0.5m, else 2*0.5*d-0.5^2. Encode a 3-vector residual sqrt(h(d))/d times the displacement. At zero use identity derivative. For d>c use constant [sqrt(h(c)),0,0] and zero derivative. Every point contributes; no support-dependent denominator or favourable point removal. Divide residuals by sqrt(total directed point count). Cost is continuous at censoring but its residual representation/derivative need not be smooth at association or cap boundaries. Numerical derivative checks avoid those boundaries and do not prove global smoothness.

The forward right-pose point Jacobian is R[-[p]x,I]; inverse is [[Z^-1 q]x,-I]. Include the derivative of radial Huber residual scaling. For global right perturbations, compose with [-Ad(Z^-1), I]. Relative Logmap derivatives use GTSAM, checked independently with SciPy exponentials and central differences.

Nominal strength: once at B, set lambda=(3/(0.20*clip(mean_dist,1,3))^2)/trace(J_translation^T J_translation). Require finite positive denominator and >=50% directed pairs within c. Lambda is fixed for Q and D; no tuning. This matches only initial nominal translation-curvature trace, not rotational shape, actual robust pose-factor information, independent evidence or calibrated covariance.

Q uses SVD J=U S Vt at Z0; residual is [S Vt Log(Z0^-1 Z)+U^T r0, sqrt(max(||r0||^2-||U^T r0||^2,0))]. Keep all six singular directions; do not truncate or pad to create capacity. Q and D must match initial objective, gradient and GN curvature within 1e-8 relative. Q is a frozen quadratic in the relative local coordinate, not merely a covariance.

GTSAM LM max iterations 50 for Q/D, fixed default remaining parameters, B uses the established native solver. Both candidates share solver limits and observations; actual work is reported. Stop invalid/nonfinite/support/numerical/resource cases. No seed, point, radius, kernel, iteration, lambda or favourable-edge rescue.

## Validation and success

Before real points: known-transform recovery of the matching cost, forward/inverse direction, common world gauge, relative/global analytic derivatives, Q/D initial equivalence, small no-loop graph no-op. Independent validator uses explicit brute-force neighbours, independent radial derivative formulas and SciPy SE3 exponential. This is not an independent nonlinear optimizer.

After bank seal, independently reconstruct all candidate initial quadratic cost/gradient/curvature with brute-force matches in fixed chunks, validate support/strength and final objective. No repeated optimizer required absent a discrepancy. Independently evaluate rigid-aligned LiDAR ATE and every camera KITTI segment using the established separate Horn/segment implementation; compare to existing evaluator values. Predictions, input hashes and source IDs checked in both validators.

Primary engineering gate: D's 00/05 arithmetic mean ATE <=0.95 times B's and <=0.95 times Q's; D ATE improves on both sequences against B and Q. Mean ter and mean rer nonworse against B. Per-sequence harm limits against B and Q: ATE <=5%, ter <=0.01 percentage point, rer <=0.01 degree/100m. All comparisons include 1e-10 numerical slack except the strict improvement signs. Report absolute gap to complete KISS-SLAM, without calling that a controlled component result. No gate is changed after outcomes.

00/05 are exposed development targets; passing permits considering a separately frozen all-six extension, not an independent generalization claim. If D does not beat Q, no direct-update advantage is established. If Q improves B but D fails, retain the observation but do not promote Q by rewriting this gate; a distinct later decision is necessary. Report complete negatives and incomplete executions separately. Latest full-system benchmark remains October 11 until a genuinely new complete pipeline is run.
