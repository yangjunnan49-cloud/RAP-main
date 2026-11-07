# SID0: prospective CPU shared-identity equation preflight

Date: 2026-10-06. Owner authorized the researched next direction. Isolated
engineering preflight of `../shared-identity-design-01/PLAN.md`; no dataset/GT,
model/descriptor inference, GPU, trajectory, training, production or Git change.

## Objective and coordinates

Canonical rows p_ij, metric raw clean Y_wij=s_w*y_wij:

    minimize sum_wi 1/(d_i*n_i) sum_j ||G_w Y_wij - Z_i p_ij||^2

All transforms proper SE(3), fix only G_0=I. Identity means the identical
original processed-input point row. Condition q=(p-c)/s; generated endpoints
decode s*y WITHOUT adding c. Return clean inv(G_w)*Z_i*p/s. A native fit q->y
has physical translation s*t_normalized-R*c. No estimated scale.

## Frozen solver

Independent proper Kabsch per factor first. Require covariance singular
sigma_2>1e-12*max(1,sigma_1). If reflected proper correction is needed also
require sigma_2-sigma_3 above that tolerance. This checks target-dependent
uniqueness, not merely input rank. Noncollinear planar points remain valid.
Target collapse/ambiguous isotropic reflection fail explicitly.

Connected trees use exact incidence propagation: G_0=I, Z_i=G_w*T_wi,
G_v=Z_i*inv(T_vi). All native local fits return unchanged. Only two windows
with exactly two shared scans enter the iterative solver. Initialize G_1 by
weighted proper Kabsch from right raw endpoints to corresponding left raw
endpoints in canonical row order; row weights1/(2*n_i). At fixed gauges fit
shared Z_i to repeated original rows. Unique Z_i=G_w*T_wi. Update G_1 using
shared scans only, then refit shared and unique Z at the updated gauge.

Maximum64 sweeps; stop absolute shared-objective change<=
1e-12*max(1,previous shared objective). Nonconvergence fails. Store initial and
every G/Z/shared/full objective. Full profiled cost adds gauge-invariant
unique native minima; global optimality is not claimed. Validator reports
final next-gauge-block residual.

Disclosed pre-freeze design clarification: the design plan stated relative
total-profiled-objective stopping. Constant unique residuals could indirectly
change termination despite supplying no gauge vote. This protocol uses the
shared variable objective and adds unique-residual invariance. No prior
output or accuracy informed this clarification.

## Fixed330 synthetic cases

Manifest freezes32 geometries times10 cases plus10 specials before output.
Seeds20261006+trial, no result filtering/rejection sampling. Counts17,19,13,11;
normal coordinates scaled[1.4,.9,.5] plus[.2*scan,0,0]. Trials0..15 fullrank;
16..31 original z=0, valid planar. Frozen runner specifies all pose/center/
scale/perturbation/row draws. Save analytic_T and explicit perturbation so
the independent validator reconstructs every raw endpoint.

Ten cases per geometry: single,one_shared,consistent,conflict,gauge,common_gauge,scale,
permutation,idempotent,unique_residual. Single/one_shared/consistent are native
reductions. Dual layout L=[0,2,1],R=[0,1,3]. Right B conflict applies fixed
.025rad z rotation and [.12,-.05,.02]m translation; nonrigid perturbation
sigma.003m, scales1.7/3.2. These are engineering fixtures, not operating
parameters selected by accuracy. Separate independent and common gauge changes;
scale case .7/6.3 with different centers; permutation shuffles factors and
local row IDs. Unique case adds50m seeded nonrigid perturbations only to
unique scans; shared solution and termination must not change.

Ten specials: chain/star trees with nonrigid raw endpoints; consistent wrong
2m relative pose; coincident/collinear input, collapsed target, isotropic
reflected covariance and disconnected incidence expected failures; constant
velocity and state-dependent feedback toys. Wrong2m MUST keep zero agreement
residual and unchanged known synthetic error: it demonstrates a limitation.

## Analytic feedback fixtures

Six centered +/-axis points per anchor, two windows, bias b_L=1,b_R=3, fixed
zero noise. Times1,.5,dt=.5 are analytic fixtures, not a RAP schedule change.
C projects every raw endpoint; I uses native independent projection; F uses
the IDENTICAL joint solver on I's final raw endpoints. Retain noise and update
x_next=(1-t+dt)*clean+(t-dt)*noise. Save all raw/state/clean/velocity arrays.

State-dependent Y_A=p, Y_B=p+(b_w+r_w(x)^2)*e_x, r_w=current B-minus-A
x-centroid; v=(x-Y)/t. First consensus relative2, final C3, terminal F3.25;
both subsequent raw predictions change. No correct target or gain is defined.
Constant prescribed velocity v=-Y_base, anchor offsets0 and b_w; projection
is linear/idempotent in this translation subspace and both C/F end at2.

## Gates, identity and limits

All330 cases required. Float64 point/maximum-pose-entry tolerance1e-9;
rotation determinant/orthogonality1e-10. Native reduction, gauge/scale/row,
idempotence and unique-factor invariance must pass. Conflict must change
relative pose >1e-5 maxentry versus left native, beyond common gauge.
Shared/full objective increases<=1e-10. Expected degeneracies must reject.
Toy values and next raw effect required; enforced residual alone insufficient.

Independent NumPy Horn/quaternion validator imports neither runner nor
projector. Require largest-eigenvalue gap>1e-12*max(1,max|eigenvalues|).
Rebuild analytic raw/cond, native normalized/metric fits, tree closed form,
every cycle block/trace, profiled constants, variants and analytic toy state
updates. Verify frozen sources and sealed files before and after checks.

Successful bank+validator wall<=120s; each peakRSS<=1GiB; sealed bank plus
validation artifacts<=20MB. Freeze runtime/executable,protocol,manifest,
three scripts and design dependencies before output. Seal bank.json and all
330NPZ before independent validation. INCOMPLETE persists until all checks
and caps pass. Preserve failed code/freeze/partial banks; correctness repairs
need disclosed new attempt/freeze with unchanged samples/gates. No rescue
by solver/fixture/threshold changes in response to accuracy.

Pass establishes equation engineering and analytic feedback existence only.
Originality, neural equivariance, physical correctness, checkpoint membership,
candidate creation and system gain remain unresolved. D1 four-pair GT-free
engineering needs a separate prospective freeze; this stage never launches it.
