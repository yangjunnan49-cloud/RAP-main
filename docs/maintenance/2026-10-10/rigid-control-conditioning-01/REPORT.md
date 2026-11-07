# NOC3: fixed-anchor rigid-control feasibility

VALIDATED_CONTROL_DIAGNOSTIC_COMPLETE; decision **FIXED_ANCHOR_METRIC_CONTROL_FEASIBLE**. Owner said "请继续推进下一步". Four predeclared CPU float64 controls completed and independently checked. Primary scaled DIRECT/DECODE conjunction: **True**. This is supervised known-transform control feasibility, not RAP fitting or a pose-estimation/system performance candidate.

## Executed controls

Same NOC2 three1000-point synthetic fixture. Descriptors/noises are unused. Anchor pose identity, twelve physical translation(m)/rotation-vector(rad) parameters, all initialized zero. Proper rotation is matrix_exp(skew). DIRECT applies NOC2's same metric/chordal loss to the parameters; DECODE constructs measured-coordinate rigid outputs and runs the unchanged NOC2 SVD loss. SCALED uses fixed .05m/.2deg unit preconditioning; RAW uses physical solver coordinates. Each condition gets one fixed L-BFGS invocation, max20 iterations/max40 closure calls/strong-Wolfe, no clipping or weight decay. Trials are retained; final accepted state defines the gate, no best-step/arm fallback.

| Condition | Iterations / closures | Final t part1/2(m) | Final R part1/2(deg) | Scaled gradient max | Full condition |
| --- | --- | --- | --- | --- | --- |
| RAW_DIRECT | 12 / 14 | 3.28339087e-10 / 1.91926894e-10 | 2.39129169e-09 / 8.05792093e-10 | 9.69799039e-09 | True |
| RAW_DECODE | 12 / 14 | 3.28341479e-10 / 1.91929478e-10 | 2.39129709e-09 / 8.05797696e-10 | 9.69803421e-09 | True |
| SCALED_DIRECT | 4 / 6 | 5.39431918e-12 / 3.14974184e-12 | 4.04422982e-12 / 9.91292582e-12 | 9.84612392e-11 | True |
| SCALED_DECODE | 4 / 6 | 5.3952299e-12 / 3.15310575e-12 | 4.04872917e-12 / 9.89221039e-12 | 9.84834436e-11 | True |

Both SCALED conditions must pass t<=.005m/R<=.05deg on both moving parts, properness, finite loss and scaled-variable gradient<=1e-5. RAW cases are fixed descriptive comparators. Hessian condition numbers at identity: RAW_DIRECT 205.067699; RAW_DECODE 205.067699; SCALED_DIRECT 1.001903; SCALED_DECODE 1.001903. Unit preconditioning changes solver coordinates; identity/reference/observations and objective are fixed. Relative cost routes' value/gradient/Hessian agreement is numerical evidence for this exact smooth rigid family, not every neural output or fp16 gradient.

## Audit and limits

Zero/probe/reference representability, anchor/properness, all12 physical gradients at each of three probes and12x12 Hessians are retained in preflight. Independent scipy rotation and Horn quaternion decode reconstruct every trial/final pose/output/cost; all12 gradients at every trial are compared with independent central differences. Full optimization replay reproduces all four traces, accepted outputs and optimizer states exactly using the same frozen source/torch optimizer. This is deterministic full replay, not an independently implemented L-BFGS algorithm. Max independent cost 7.28e-12, gradient 1.02e-06, Horn pose 1.15e-14; optimizer trace replay 0. No model, GPU or native fitting/inference, descriptor extraction, real/nearby windows or new prediction census. Optimization uses reference supervision; this is a numerical control and cannot establish physical accuracy or generalization.

NOC2 affine final20.442/19.929mm remains a fixed-budget prerequisite stop. This round changes control family, gauge, precision, optimizer and solver-unit preconditioning; it cannot assign NOC2's failure uniquely to one of those changes. Comparisons within these four conditions address scaling and decoding only under this new fixed family/solver. Passing cannot retroactively amend NOC2 or prove an adapted RAP sampler converges. No rates/steps/init/gate/window rescue.

## Resources and preservation

5 recorded successful stages total29.159543s, peak RSS0.618805GiB;600s/2GiB/64MiB CPU-only caps pass, all attempted RSS captured. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Artifact bytes finalized in DELIVERY_SEAL. No failed execution stage or implementation repair.

160 source/input freeze entries. NOC0/NOC1/NOC2 original/corrected delivery counts[103, 188, 53, 5] unchanged. Original model/config/checkpoint and sibling helpers retained; both HEADs/branches/two and nine tracked dirty sets preserved. Only isolated maintenance/docs and mutable handoffs. No model/checkpoint load, acquisition/install, production/default/backbone-source/manuscript edit, official metric/reference replacement, trajectory, commit or Git sync. Old stops/seals/physical/reference/time/site/checkpoint unknowns persist. Conventional proper geometry/L-BFGS credited, no original mechanism or system gain.
