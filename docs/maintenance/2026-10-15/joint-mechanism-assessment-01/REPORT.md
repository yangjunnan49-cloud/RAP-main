# JMD0 one mechanism decision: unposed joint map merging

Decision: CONDITIONAL_TASK_DEFINED_NO_EFFICACY_PROTOCOL_ADMITTED.
Scope: design and static source/evidence assessment only, no new numerical
fixture, point decoding, inference, learning, solver, pose metric or trajectory.

## Candidate and falsifiable effect

Task candidate: register three or more genuinely distinct, initially unposed
views/maps with metric references, using frozen RAP joint generation as a
proposal and the same measured-geometry verification as the strongest ordinary
control. Keep KISS/E0 local odometry intact. The proposed useful effect would
be recovery of correct multi-view alignments missed by equal-input geometry
and independent-pair RAP, without extra false acceptance or adverse tails.

The additional physical information would be the distinct measured views.
RAP's proposed increment would be its pretrained joint conditional prior, not
the mere existence of those views. Every relevant geometry/direct and independent
model control must receive the same measured support. Context dependence alone
is already known from FCE0 and is not this effect. Generic multiview generation
and map merging are already in the author's method and public description;
running the original model on those tasks is not a new algorithmic contribution.

## Source and comparison contract

Local point_cloud_dit.py routes pointwise encoding/anchor flags through every
transformer layer. Local layer.py sends within-part attention through
cu_seqlens_part and global attention through cu_seqlens_batch. This supports a
joint/independent information intervention in principle; FCE0 validated one
specific FP32 fixed-prefix intervention only. It does not validate any new full
sampler, precision condition or multiview efficacy bank. The local SDPA port's
max_seqlen parameter is unused; its name is not an enforced memory bound.

Required controls in a later, separately justified design:

| Arm | Observations and role | What it would separate |
|---|---|---|
| G | All common raw views, strong model-free pairwise/global geometry and fixed solver | Ordinary multiview information benefit |
| P | Independent-pair RAP over a predeclared connected observation graph, same geometric verifier | Pretrained pair proposal benefit |
| J | One joint RAP proposal over the same complete view population, same verifier | Incremental joint prior over G/P |
| W | Explicit alternative use of the same total work budget | Whether extra compute explains J's benefit |

Hold raw point IDs, preprocessing, feature exposure, metric scale, initialization
uncertainty, verifier/solver, acceptance rule, failures and evaluation population
fixed. A pairwise star and a fully connected pair graph have different work and
information paths; declare the graph before outcomes. Count preprocessing,
descriptors, all sampler calls, graph construction, optimization, failures and
fallbacks. No measured capacity equality is claimed merely by reusing weights.
No new trainable head is needed to test this task role.

## A gate that must be rejected before implementation

Cycle closure derived from one shared set of predicted poses is not independent
evidence of accuracy. If P_i maps part i to the generated common frame and
T_ij=P_i^-1 P_j, then T_ij T_jk T_ki=I for any P_i, including wrong poses.
Likewise, every jointly reconstructed rigid view can look internally consistent
without matching the observed physical scene. Do not use these algebraic
identities as an accuracy or confidence gate. Genuine measured cross-view
constraints and a stated external/supplied reference role remain necessary.
This is a group identity used for design review, not a newly executed experiment.

## Distinction from stopped constructions

| Earlier construction | Required actual difference | Present status |
|---|---|---|
| G0/G1 pairwise global matchers | New unposed multiview task and complete population, not resolution/point-budget rescue | Conditional; no new task admitted |
| CCR0 fixed causal three-scan geometry | Distinct unposed views, no relabeled nearby support-count sweep | Source/view relationship not authenticated |
| GSG0 copied-congruent fixture | Actual distinct observations, independently stated reference role | Headers/counts alone do not establish this |
| BRF0 bounded native-base head | No small bounded residual head or radius/base change | Structurally different, without demonstrated gain |
| RLP2 frozen matching head | No new token readout fit; direct joint versus independent generation | No original-RAP novelty follows |
| MGR0 RAP-initialized geometry | Useful joint increment over the strongest common-input geometry/initializer | Remains unproved; ordinary refinement alone is insufficient |

## Evidence decision

ODA0 now supports complete current author-bundle CRC/length consistency for all
156 files. DRD0 confirms the exact original ZIP URL in the current author blob;
ADC0's finite public discussion query supplies no reference construction.
The archive has no reference sidecar and the default demo constructs supplied-
coordinate references. Whether these clouds are already registered and how that
alignment was obtained is still UNKNOWN. Filename/header diversity does not
authenticate overlap, independent sessions, physical reference or pretraining
exclusion. The 27 scene names do not become 27 new confirmation scenes.

There are therefore two unmet conditions: a usable exact input/reference role
for this candidate and an incremental mechanism beyond the author's existing
generic joint method. A proposal could still become an honestly labeled
engineering study if its role is documented and the comparison answers a useful
question. It is not presently a justified new efficacy protocol or contribution.

Existing exposed KITTI engineering remains possible under its supplied-reference
role. This decision is not a universal requirement to authenticate all history
before any engineering work. It does prohibit converting the failed local-motion,
context, bounded-residual or oracle-placement constructions into this candidate
by changing names, favorable subsets or thresholds.

Next required evidence: an author statement or original record identifying the
original demo archive version and whether its members are registered, the exact
input-to-world reference convention/construction/quality, and any preprocessing
mapping. The local request is ready; sending it requires explicit authorization.
No further local numerical/storage/supervisor control can supply that statement.
No protocol, runner, cohort, threshold or fit is frozen by this document. The
next action after receiving a source record is a role/novelty decision, not
automatic inference. All prior scientific stops/references/09 unknown remain.
