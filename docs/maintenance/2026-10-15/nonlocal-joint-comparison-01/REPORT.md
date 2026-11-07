# NJE0 complete exposed nonlocal joint comparison: negative

COMPLETE_EXPOSED_COMMON_INPUT_JOINT_ENGINEERING_SCREEN_FAILED.

Four fixed loop-connected groups,29views and32original measurements were fully
evaluated. Joint RAP fails all three prospective engineering gates. Retire this
exact single-noise/common-normalization/1000-keypoint/native-five-step joint
construction. Do not tune seeds, groups, point counts, anchors, radii or steps
to rescue it, or promote it to a full-system experiment. This is a complete
negative comparison, not universal evidence against multiview learning.

All predictions for all groups/methods were sealed before reference evaluation.
The independent validator checks the seal-stage exit precedes metrics launch.
There were no backward calls, gradient changes, fitted heads or weight updates.
Original RAP already supports multiview generation; no algorithmic novelty is
claimed. All examples were exposed KITTI engineering data; training exclusion
and physical truth remain unauthenticated. Sequence09 remains included with
unresolved reference/physical interpretation. No official reference was changed.

## Results on all32 fixed measurements

|Method|Mean RTE m|Mean RRE deg|
|---|---:|---:|
|J native joint RAP|1.482851|0.240790|
|P independent pair RAP|1.472642|0.206005|
|Ps synchronized pair RAP|1.471701|0.218757|
|Gd unposed1000-point geometry|1.821697|1.584572|
|Gs all-view synchronized G|1.548748|1.283774|
|Wd practical4000-point geometry plus odometry start|1.474044|0.174041|
|Ws all-view synchronized W|1.471863|0.175487|
|O original frontend odometry|2.273346|0.794291|

J's RTE is0.6933% worse than P and0.7576% worse than Ps. The required aggregate
RTE against the strongest control was<=1.398116m; J achieved1.482851m. Its RRE
also exceeds Wd's0.174041+.05deg allowance. Improvement over a weaker Gd control
does not satisfy the conjunction of strong controls.

|Group (views/edges)|J RTE|P RTE|Ps RTE|Gs RTE|Wd RTE|Ws RTE|
|---|---:|---:|---:|---:|---:|---:|
|05 (3/2)|.076709|.083672|.083672|.060333|.033086|.029842|
|00 (9/8)|.783035|.798717|.798717|.792304|.820370|.817210|
|07 (10/12)|.155169|.122062|.119861|.298622|.127973|.124498|
|09 (7/10)|3.917151|3.910271|3.909904|3.951736|3.900458|3.900829|

Only00 satisfies the group RTE safety rule against its best control. The05
joint improvement over P remains inferior to practical ordinary geometry;07
worsens against both P and W. These are descriptive fixed-group results, not
independent significance estimates or identification of a physical cause.
09's large common error is not evidence of a particular reference defect.
All256 method/edge RTE/RRE rows and gates are retained in metrics.json.

## Input and validation evidence

The239-identity NJC0 topology prerequisite was followed by326frozen identities
for this comparison, including exact parent caches, weight/source/config and
reference byte identities. Every view contributes the same frozen4000-point
support and deterministic1000keypoints. P/J share descriptors, normalized rows,
component scale and per-view noise exactly; anchor flags differ as declared.
W receives additional frontend trajectory initialization, explicitly making it
a stronger practical control rather than an equal-information unposed method.

Preflight quaternion Horn/SVD errors are1.5543122344752192e-15, exact synthetic
graph recovery and backend normalization error0. All36native generations retain
their final normalized clouds, native/Horn/physical-unit fits. Independent SciPy
rotation alignment matches saved Horn fits within9.97466e-15. A separate decoder
using general matrix solves differs at most1.1367011e-5 in physical transforms,
consistent with float32 rotation/transpose inversion tolerances.

An independent blocked brute-force distance calculation, with no primary
driver/KDTree helper, checks all525candidate scores/supports over5,250,000,000
point-pair distances. Maximum score difference8.881784197001252e-16. Independent
calibration/reference composition and rotation-angle API check all256metric rows:
RTE discrepancy8.08242361927114e-14m, RRE5.67905175330452e-7deg. No model rerun.
Graph costs decrease as required; direct and synchronized controls both remain
in the comparison. Correlated all-pair factors are not calibrated independent
evidence. Cycle closure from shared poses is not an accuracy result.

## Complete work and resource interpretation

Encoder29calls; P32pair/J4joint generations, source-configured180flow evaluations;
G/W each105complete pairs, combined210FGR/525GICP starts and8geometry graph solves,
plus4P synchronization solves. Inputs and descriptors are computed once and
shared. P presents64000native point rows versus J29000, while their single global
attention token-pair proxies are128million versus239million. Neither quantity
is total FLOPs; shared raw inputs do not imply equal work.

Recorded P generation calls total8.157027217268478s, J2.3864083040389233s.
They are interleaved in one warm process with P first in each group, not repeated
standalone latency measurements. Shared loading/encoding/validation and geometry
work remain separately included. No production latency or system speedup follows.

Nine enclosing attempts: eight successes and one retained Open3D prestart
device-selection assertion failure, before real geometry. The exact independent
CPU-selection insertion/driver routing is bound in CPU_VARIANT_BINDING and
PRESTART_CPU_VARIANT; original source/freeze/failure/initial INCOMPLETE survive.
No scientific predicate, input, output or budget changed and no partial real
numerical computation was replayed. Original combined2400s cap includes all.
Actual cumulative child115.80492744292133s; Windows137.6652337s including startup/
imports; max Linux processRSS2,789,040,128bytes. Full child/Windows exits survive.
Actual dossier size and every receipt are enumerated in COSTS/CHECKS.

Before loading, CUDA reported11,553,210,368free bytes against9,663,676,416required;
the preparatory Windows NVML1775MiB reading differed. No reason for the different
API readings is inferred and no other process was stopped. Native forward peak
PyTorch allocation1,488,649,728bytes/reservation2,715,811,840bytes satisfies8GiB.
These allocator peaks exclude other libraries/context/other tasks. In particular,
the failed Open3D CUDA-selection import has UNKNOWN non-PyTorch GPU peak; its
raw receipt's zero denotes no PyTorch allocator, not measured all-device zero.
Do not claim complete all-native GPU/process-tree caps. Linux RSS/time/dossier
and scoped PyTorch caps pass; this resource uncertainty remains explicit.
All prelaunch Windows headroom guards passed12GiB; the neural attempt's later
minimum9,622,667,264bytes is observed, not a claim of persistent12GiB headroom.
Ordinary setup/closing RSS and observer lifetime stay UNKNOWN.

The initial pending INCOMPLETE marker is retained with the original failure;
current STATUS/CHECKS distinguish complete negative science from historical
pending/failed stages. No acquisition, outreach, installation, production/default/
backbone/reference/manuscript edit, process restart, commit or Git sync. Original
ten inherited markers, prior seals/stops and both repository states persist.
Latest complete system benchmark stays2026-10-11attempt03. This loop-component
result is not a new trajectory/ATE/ter/rer or full58-loop efficacy benchmark.
