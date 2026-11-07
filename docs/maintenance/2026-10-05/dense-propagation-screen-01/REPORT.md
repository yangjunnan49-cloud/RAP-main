# Fixed dense-pose correction screen — 2026-10-05

**VALIDATED: NO_FIXED_INTERPOLATION_SIGNAL.** Stop this exact interpolation route.

The fixed SE(3) interpolation was constructed without GT on unchanged saved E0 A
odometry and optimized keyframes. No graph reoptimization or RAP inference.

| Sequence | Odom ter % | Native P ter % | Interpolated S ter % | P minus S, pp | P ATE m | S ATE m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 00 | 0.513202 | 0.518171 | 0.518056 | 0.000114 | 2.754437 | 2.754446 |
| 05 | 0.330504 | 0.320473 | 0.320027 | 0.000446 | 1.294699 | 1.294696 |
| 06 | 0.279935 | 0.327512 | 0.326715 | 0.000796 | 0.332854 | 0.332845 |
| 07 | 0.383823 | 0.394673 | 0.394442 | 0.000232 | 0.326400 | 0.325948 |
| 09 | 0.519444 | 0.593652 | 0.591901 | 0.001751 | 1.074523 | 1.074651 |
| 10 | 0.528520 | 0.528520 | 0.528520 | -0.000000 | 0.763516 | 0.763516 |

## Frozen decision

- development: mean ter 0.388718415% -> 0.388266097%; gain 0.000452319 pp versus required >=0.01. Mean ATE 1.460663494 -> 1.460662429 m.
- transfer_exposed: mean ter 0.505615106% -> 0.504954083%; gain 0.000661023 pp versus required >=0.01. Mean ATE 0.721479820 -> 0.721371552 m.

Both material ter gates fail; all fifteen other safety/identity gates pass.
The actual small improvements are retained; failure is not zero numerical effect.
06 and 09 still have clear ter regression versus their odometry. This fixed
interpolation does not remove it. No general impossibility or exclusive causal
attribution follows, and no interpolation-space/weight rescue is licensed.

## Validation and provenance

49 protocol/source/input/preflight identities froze before the full output.
The complete 25-file GT-free bank sealed before evaluator GT. The independent
validator reconstructed all S poses with SciPy/analytic SE(3), independently
computed rigid-alignment ATE and all strict-endpoint KITTI segment records,
verified baseline reproduction, correction diagnostics and all seventeen gates.
It passed 8 groups and 22,194 segment records. Maximum analytic trajectory difference is 1.77e-11; native saved-path difference <=6.39e-10.
Sequence10 P/S difference 2.27e-13. Bank/evaluation/validation wall 8.300s, max stage RSS 0.099 GiB; artifacts before report 9.248 MiB. All resource caps pass. Setup/preflight time is recorded separately.

## Next question

A separately frozen joint same-endpoint GT replacement diagnostic can ask
whether current accepted poses have coupled trajectory headroom. It must
keep native propagation, endpoints, odometry, graph settings and base noise
fixed. This is evaluator-only, not a deployable method or global ceiling.
Generic interpolation is prior art; no original RAP gain or new independent
confirmation is established. No default/production edit, training, manuscript
change, commit or Git sync. Earlier negative stops and old banks persist.
