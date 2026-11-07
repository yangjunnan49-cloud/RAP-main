# Next development hypothesis: protect the RAP rotation, refine map translation

Status DESIGN_RECOMMENDATION_ONLY. CV1 is complete with a validated engineering
repair and no passing full-pose conjunction. No additional candidate/cohort has
been frozen or executed. Original tolerances/gates and the first-case exposure
remain; these suggestions do not convert CV1 into a passed method.

## Evidence that changes the investment decision

The actual revisit supplies216cross-visit patches,163train/53holdout, both visits
supported in all eight scans. F versus saved RAP Z lowers joint16node aligned ATE
5.344% and endpoint translation7.955%, while worsening endpoint rotation.026466deg
(fixed guard.01). J yields5.644%/8.205% but rotation+.030760deg. All holdout and
internal safety checks pass. J versus F adds only.316%ATE/.271%endpoint translation,
far below the5%conditions for an internal-pose claim. These are partial single-case
development effects, not a system improvement or physical calibration finding.

The strongest actionable candidate is conventional rigid map refinement.
Expanding internal BA, weakening its prior or adding more latent readout capacity
has no demonstrated benefit under this construction. Stop automatic extra CV1
iterations/regularizer/hash/scale/point/window tuning and do not run the formerly
conditional whole-system confirmation as if this conjunction had passed.

## A simple testable restriction, with its post-outcome motivation explicit

Test whether measured cross-visit surfaces can refine translation while exactly
preserving the saved RAP relative rotation and both internal O shapes. This is
a three-variable version of rigid refinement, not a new information source or
original mechanism. It is proposed after observing the exposed rotation tradeoff.
Its endpoint rotation safety is largely structural; useful translation/jointATE
and unused-patch consistency still have to improve in new outputs. Locking R
could remove the translation gain too. Do not assume the six-DOF result carries
over, or infer that native RAP rotation is generally physically reliable.

For a new bounded development phase, use first original accepted-loop array
records of00/05/06 with last8keyframes on each side. Freeze exact identities and
hashes prospectively; no GT/overlap/quality ranking or replacement on unsupported
cases.00is the already-exposed CV1case;05/06also have historical exposure. No
independent generalization claim. No new RAP call or retrieval changes.

Keep same retained preprocessing,2m eligible cross-visit planes, complete-patch
hash split and support checks. B=saved RAP Z; F=matched six-DOF rigid refinement;
T=new three-variable translation-only refinement, fixed Zrotation/internal O.
Do not include J automatically. Use24updates,same damping/backtracking/.2m steps;
endpoint correction<=5m. Translation update in the fixed Zbody frame; explicitly
assign fixed rotations rather than recompositing nominally identity rotations.
Source/numeric preflight must verify three-variable moment gradients, exact
rotation/shape invariance, rank-deficient translation blind directions and proper
source bindings. Same observations and analytical plane nuisance refitting.

Seal all B/F/Tpose records before new reference outcomes. Preserve every case,
including unsupported records. Require all3supported/valid,>=2/3jointATE AND
endpoint-t improvements,mean fractional gains>=5%for both, no case jointATE or
endpoint-t regression>5%, rotation change from B<=1e-8deg, each visit's existing
5%ATE/tRMSE/.02deg mean-R safety and each holdout RMSratio<=1.01. Compare T/F
tradeoffs separately; no best-angle/translation oracle or selecting F/T after
GT. A negative result stops this specific fixed-rotation hypothesis. A positive
three-case development result would justify a separate full-system test with
unchanged official ter/rer/ATE, runtime and false-loop effects.

Proposed new CPU ceiling1800s/RSS2GiB/dossier512MiB, every attempted stage counted,
not an amendment to closed CV1. No density/patch/prior/iteration/cohort sweep,
acquisition/install/training/backbone/default/manuscript/commit/Git sync. Any
eventual adoption can be conventional engineering under owner originality
relaxation; credit [BALM](https://arxiv.org/abs/2209.08854) and related geometry.

## Unknown details this would and would not resolve

It would test retention of the observed translation benefit under protected
rotation across a fixed three-case cohort. It would not explain why map objective
and rotation reference disagree, physical patch identity/dynamics, surface
selection bias at RAP Z, initialization basin, KISS/map observation correlation,
missing point times or covariance, calibration consistency, checkpoint training
membership/site exposure,09discrepancy or independent system generalization.
Do not use lower heldout residual to decide which rotation reference is wrong.
