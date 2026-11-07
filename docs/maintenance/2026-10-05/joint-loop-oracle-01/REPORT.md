# Joint accepted-loop pose diagnostic — 2026-10-05

**VALIDATED: MATERIAL_CURRENT_EDGE_JOINT_HEADROOM (ATE branch only).**

This is an evaluator-only diagnostic, not a RAP improvement or global ceiling.
All current accepted poses were jointly replaced by their same-endpoint GT
poses. Endpoints, odometry, base noise, kernel settings and native propagation
were unchanged; robust effective influence could change with residuals.

| Sequence | Native P ter % | Joint J ter % | Native P ATE m | Joint J ATE m |
| --- | ---: | ---: | ---: | ---: |
| 00 | 0.518171 | 0.519232 | 2.754437 | 2.720629 |
| 05 | 0.320473 | 0.332222 | 1.294699 | 1.290508 |
| 06 | 0.327512 | 0.326037 | 0.332854 | 0.337063 |
| 07 | 0.394673 | 0.392977 | 0.326400 | 0.307764 |
| 09 | 0.593652 | 0.577698 | 1.074523 | 0.746446 |
| 10 | 0.528520 | 0.528520 | 0.763516 | 0.763516 |

## What changed in our understanding

- development: mean ter 0.388718418% -> 0.392496992% (P minus J -0.003778574 pp); mean ATE 1.460663506 -> 1.449400148 m (0.7711% improvement).
- transfer_exposed: mean ter 0.505615106% -> 0.499731628% (P minus J 0.005883478 pp); mean ATE 0.721479820 -> 0.605908422 m (16.0187% improvement).

The exposed-transfer cohort passes the prospectively frozen ATE opportunity
criterion (>=5% ATE gain, ter worsening <=0.01 pp). Neither cohort passes
the >=0.01 pp ter-gain branch. The development cohort passes neither branch.
09 drives most of the ATE opportunity: its ATE drops about 30.53% and ter
improves 0.015954 pp. 07 improves ATE too; 10 remains identical with no edges.
This demonstrates coupled current-edge opportunity missed by reading the
single-edge interventions as an all-edge ceiling. It does not establish
statistical independence, a GT-blind selector, or a practical pose generator.

Joint GT loops still leave mean ter above odometry in both cohorts, and
sequence09 J ter 0.577698% is above odometry 0.519444%. 05 ter worsens
under the joint replacement. Perfect current loop poses alone therefore
do not remove the regression in this specific frozen graph configuration.
No conclusion follows about all possible graph designs or added loops.
09 rotation drift worsens from 0.106938 to 0.129841 deg/100m; preserve this
secondary tradeoff rather than calling all metrics improved.

## Validation

63 identities froze; the complete 19-file GT-free native bank sealed before
the new evaluator loaded GT. A separate validator explicitly rebuilt every
native/oracle graph, checked all 58 replacement poses and unchanged metadata/
base sigmas, independently calibrated GT and recomputed Kabsch ATE and
22,194 segment records. It passed 8 check groups; maximum native/oracle graph difference is 0.
Bank/evaluation/validation wall 7.412s; max stage RSS 0.100 GiB; artifacts before report 8.535 MiB. Caps passed.

## Next step

Proceed to feasibility and prospective design for one strong official
outdoor registrar on actual online E0 inputs, initially GeoTransformer.
Use all 71 attempted pairs rather than selecting the ten exposed 09 errors
as the only efficacy sample. Separate its pure fixed-edge pose diagnostic
from common-gate acceptance and full executable system behavior. Freeze
training/checkpoint/source identities, actual input points, direction and
resource/decision rules before any new pair output. A direct matcher gain
would be a baseline, not a RAP innovation. Reserve independent trajectories
for later method confirmation. No training/default/production edit,
manuscript change, commit or Git synchronization. All old stops persist.
