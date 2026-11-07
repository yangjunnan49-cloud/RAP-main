# C3: one fixed local-geometry descriptor information comparator

Freeze this protocol, both programs and every input identity before computing
descriptors. C3 asks whether fixed FPFH on the *same saved F2 anchor points*
contains materially more cross-visit top-1 correspondence information than
the C1 miniSpinNet descriptors on difficult KITTI08 pairs. It is an
observed-development diagnostic, not a RAP registration run or encoder choice.

## Input and descriptor

Use the 100 saved-order F2 pairs each on KITTI00 and08, without replacement.
Only the target part0 and source part3 2000-point arrays from each frozen F2
`inputs.npz` are inputs. Do not reload raw scans, resample, downsample, add
points or access GT/labels before sealing the descriptor bank. Open3D 0.19.0
legacy CPU `PointCloud.estimate_normals` uses hybrid radius **2.0m**, maximum
30 neighbors. Orient normals toward the LiDAR origin `(0,0,0)` independently
in each scan. `compute_fpfh_feature` uses hybrid radius **5.0m**, maximum100
neighbors; output is 33-D per point. This one scale uses the same 5m local
radius as miniSpinNet and allows the sparse 2000-point anchors larger
neighborhoods than the Open3D example for fully voxelized clouds. These
parameters are fixed, not fitted. Save descriptors in point order as float64
and count zero-norm rows. Set `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`.

Before real computation, synthetic translation/rotation and descriptor-shape
checks must pass. Freeze protocol, runner, separate validator, F2 source and
200 saved `inputs.npz`, C1 bank/pair/summary identities, F2 evaluator labels
and GT identities. Bank code may hash GT/labels to bind inputs but must never
parse them. It must create `INCOMPLETE` before work and SHA-seal all200
descriptor artifacts and bank manifest before evaluator access. No C1/C2
files may be modified.

## Fixed evaluator and decision

Reuse exactly C1's source-to-target GT transform, 1m nearest geometric
eligibility, pair as unit, L2 descriptor normalization and nearest target
feature by Euclidean distance. For zero-norm source descriptors, count top-1
as incorrect; exclude zero-norm targets from the feature tree. Use the same
16 C1 SHA256/PCG64 target-coordinate permutations per pair; source zero
descriptors remain incorrect in controls. Never substitute a second-best
match, ratio test or mutual matching. Report each pair's coverage, true
conditional recall, shuffled mean, paired true-minus-control and paired
FPFH-minus-C1 differences. Report group summaries by sequence, stratum and
native K4 candidate availability, without cross-sequence pooling.

Primary group: KITTI08 positive pairs with no strict native N K4 candidate
and >=10% geometric eligibility, as already defined by C1 (33 of41).
`MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE` requires at least20 adequately
covered pairs with >=95% nonzero source and target FPFH descriptors, median
FPFH true-minus-control conditional recall >=0.10, **and** median paired
(FPFH true-minus-control minus C1 true-minus-control) >=0.05 on those
supported pairs. If the nonzero/support count is below20, decide
`INCONCLUSIVE_DESCRIPTOR_SUPPORT`; otherwise failure of either effect
margin is `NO_MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE`. These are
prospective exploratory effect margins, not a statistical test. Secondary
descriptive groups cannot override the decision.

A positive result only motivates a separately frozen RAP interface/model
adaptation study, not immediate training, default replacement, novelty or
performance claims. A negative result stops this fixed FPFH setting; no
radius, orientation or threshold sweep. This comparison is intentionally
unequal in context: C1 miniSpinNet used full corrected scans to compute
features at the saved anchors, while FPFH sees only saved anchors. Interpret
it as an anchor-local information test, not a general ranking of encoders.

## Cost and validation

Caps: <=30min descriptor-bank wall time, <=2GiB new descriptor artifacts,
<=2GiB peak process RSS. Evaluator follows bank sealing. Separate validator
rehashes frozen inputs and all200 artifacts, checks shapes/finiteness/zero
counts, recomputes all200 pair metrics and16 controls independently, checks
C1 pairing/group/decision arithmetic, and independently regenerates FPFH
for eight fixed pairs (saved indices0,25,50,75 for each sequence). It records
Open3D/NumPy/SciPy versions and checks no `INCOMPLETE` remains. A failure
leaves an explicit incomplete state; do not overwrite completed work.

Method reference: Rusu, Blodow and Beetz, ICRA 2009, “Fast Point Feature
Histograms (FPFH) for 3D Registration”; Open3D 0.19.0 `compute_fpfh_feature`
and global-registration documentation. C1's fixed evaluator is the metric
reference.
