# RAP generated-structure directional response: a distinct hypothesis

## Mainline interpretation

The temporal audit closes the available frame/time/calibration checks. It leaves a cross-visit geometry/label discrepancy, not permission to revise GT. The stopped interpolation, scalar rigidity selection, support transport, masks, intensity, point selection and direct GeoTransformer arms do not create a defensible RAP gain. A candidate mechanism should add information that the system currently discards and test that information separately from generation, acceptance and graph utility.

The concrete proposal is to measure how **joint generated spatial regions and late flow endpoints affect the decoded relative pose**, retaining a full six-dimensional directional response. Two anchor views were generated together with four supports; their responses can be correlated. Jointly deleting one spatial region from both anchor fits preserves that coupling. Summing two independent per-view response matrices discards it. Their difference is the specific mechanism to test.

## Source evidence and prior art

[RAP's primary paper, sections 3.2–3.3](https://arxiv.org/html/2512.01850v2), describes joint point generation, rigid pose recovery and scalar rigidity-guided inference. Local `sampler.py` saves the predicted clean point endpoint before its rigidification, while `rap_backend.py` decodes the final relative pose and a scalar geometric admission score. The saved F2 bank retains these endpoints. This makes a CPU-only extraction possible without changing weights or sampling.

Registration covariance and direction-dependent graph weighting are established topics. [Bonnabel et al.](https://arxiv.org/abs/1410.7632) explain why correspondence/rematching assumptions matter for ICP covariance; [Brossard et al.](https://arxiv.org/abs/1909.05722) include initialization, correlation and sensor-bias effects. A jackknife matrix is not automatically a calibrated covariance. Generic anisotropic weighting, spatial deletion, late-step dispersion, and gauge cancellation are not novelty claims. A possible contribution would require showing that RAP's **joint generated response** contains useful information beyond scalar rigidity, independent-view deletion and equal-point geometric conditioning, followed by a fair system benefit. This has not been established.

## Fixed extraction

Use only one saved native N0 generation for each of the first four frozen-input-order pairs in 00 and 08 (eight exposed-development pairs). Use anchor parts 0 and 3; support parts have already conditioned the native generation. Decode per-view poses A and B from centered condition points and raw endpoints, respecting saved centers/scale. Relative pose is A^-1 B. The final relative pose is preserved.

Partition the final rigidly placed anchor points into eight shared regions using deterministic farthest-point landmarks. First landmark is farthest from the joint centroid; subsequent landmarks maximize nearest-landmark distance. Assign points to their nearest landmark. This partition uses common geometry and is invariant to a common left rigid change of generated coordinates. It need not contain balanced regions; require at least 200 remaining points in each anchor for every deletion.

For each of the last three raw endpoints, decode the full relative pose T_s. Jointly delete each region, refit A and B, and compute the right tangent xi_b = Log(T_s^-1 T_s,b), ordered rotation radians then translation metres. Let C_joint,s = 7/8 sum_b (xi_b - mean xi)(xi_b - mean xi)^T. Average the three matrices. Add C_time = 1/3 sum_s Log(T_final^-1 T_s) Log(T_final^-1 T_s)^T. These dependent deterministic samples measure sensitivity, not posterior uncertainty.

The independent-view control deletes each region from only A and then only B, forms separate centered matrices and sums them; it uses the same points, landmarks and full poses. The isotropic control is trace(C_normalized)/6 times identity, where normalization uses existing graph units D = diag(0.03 rad x3, 0.20 m x3). Raw mixed-unit eigenvalues cannot be compared meaningfully. No graph information matrix is deployed in this preflight.

## Necessary limitation

An exactly rigid but wrong generated relative pose can have zero spatial and temporal response. A mandatory synthetic counterexample must demonstrate this blind spot. Stable generation is not proof of accuracy; this mechanism cannot by itself resolve the 09 discrepancy or reject all sequence-10 aliases. Also, simply summing rigid-fit residual gradients is uninformative at a stationary least-squares solution. Do not label the proxy an error estimate without a separate calibration study.

## Progression

Engineering preflight tests decode identity, independent recomputation, finite PSD matrices, common-gauge invariance, deformation sensitivity and the rigid-wrong counterexample. It reads no evaluator GT and can establish only executability. A separately frozen all-200 F2 information screen would test directional alignment of pose errors against trace-matched isotropic, scalar-rigidity and independent-view controls, with geometric-conditioning control added before any labels. The eight exposed preflight pairs must be identified, not called independent confirmation.

Only a material information signal would justify a separately frozen all71 online paired system screen. E0 did not save native raw flows/RNG state; a newly instrumented replay cannot claim exact reproduction of its original poses. New native, joint-response, independent-response, trace-isotropic and geometric controls must share the same new generation, pose, gate, compute budget and accepted edge set. Source capture and safe weight-loading preflight would precede inference. Use unchanged material ATE/ter and sequence safety criteria; no GT-specific axis suppression, confidence scale sweep, GT replacement or gate rescue. Reserve later eligible trajectories after an exposure census. No online screen is frozen or running yet.
