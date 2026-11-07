# Next distinct stage: preserve clusters and hold out structures

Status: DESIGN_RECOMMENDATION_ONLY. No new point-dense optimization, actual
revisit candidate or whole trajectory is frozen/implemented by this document.
SMP1 remains closed with no eligible representation; its post-hoc counts do not
change that result or establish accuracy. The owner selected the mainline, not
a retroactive rescue of its two frozen representation trials.

## The concrete change

Use every already-retained MMR0 point to construct2m shared planes. Avoid splitting
the interior of every local surface into alternate rows before estimating its
cross-scan support. The census shows106/132/52/51features and adequate scan support
in all four windows with these existing points. Full uncapped.5m voxel data would
provide119/209/155/392features, but is unnecessary merely to clear the observed
support issue. It remains a separately justified representation alternative later.

The essential resource separation is between retaining measured geometry in
compact moments and passing points through a neural model. A point-cluster map
can consume more surface observations without a correspondingly large token
bank. This engineering concept has established prior art,not originality claimed.
[BALM](https://arxiv.org/abs/2209.08854).

## A reviewable small development protocol

1. Form eligible planes from all retained points at unchanged O and frozen2m
   membership criteria. Split **complete patches**,not point rows,using a fixed
   hash of sequence/window/voxel key. A proposed75%training/25%geometry-check split
   should be fixed before any new optimizer output,with SHA256 first4bytes interpreted
   big-endian. Show actual training/test counts and scan/normal coverage; do not
   select a favorable split or substitute unsupported windows after outcomes.

2. Optimize only training-patch geometry plus the same fixed.10m/.15deg adjacent
   motion regularizer. O versus one P candidate is sufficient for this narrow
   representation test; do not repeat uncontrolled G already observed to drift.
   Keep the24-update/damping/step/backtracking settings initially. Reusing this
   prior does not make it a calibrated covariance or independent measurement.

3. Evaluate the predeclared unused patch geometry without letting it alter
   candidate poses. Plane nuisance geometry may be fitted for reporting its
   consistency,clearly distinguishing this from a separate pose-reference test.
   Repeated spatial observations remain correlated; this is structural geometric
   validation,not statistical independence or generalization. Use unchanged
   local reference translation/rotation/aligned-ATE conventions and display all
   window outcomes. An alternative whole-scan holdout would require separately
   defining which poses remain supported,not silently dropping an observation.

4. Declare an accuracy/safety criterion before new outcomes. The prior SMP1
   local draft remains a reasonable starting point:>=3/4aligned-ATE improvements,
   mean fractional gain>=5%,no ATE/tRMSE regression>5%,no mean rotation
   regression>.02deg and bounded geometric-check degradation. These are proposals
   for a distinct future stage,not already frozen conditions or old gate amendments.

5. If promising,design one **actual revisiting pair of submaps** selected from
   the original GT-blind development accepted-loop bank. Retain both submaps'
   internal scan poses and shared structure,fixing initial alignment/measurement
   identity. Compare direct measured-map refinement with the existing fixed-pose
   factor graph. No retrieval tuning,oracle loop or RAP initialization yet.
   If local gains remain small,that does not test cross-visit information; a
   different explicit revisit hypothesis can be reviewed without calling the
   local experiment a success. No complete sequence follows automatically.

## Limits and stop rules

At most one initial support-preserving representation/holdout construction;
retain every output. No threshold/patch-hash/point-budget/regularizer sweep to
find a favorable result. A limited later development search must be declared
as a new phase and retain its exposure history. Synthetic/source/selected
numeric checks are enough until a promising full-system candidate warrants
expensive replay. A proposed new CPU ceiling is1800s/RSS2GiB/artifacts512MiB;
it is not an amendment to closed SMP1/MMR0 resource accounts.

Source frame/time/preprocessing provenance,feature identity/dynamics,plane
membership selection bias and geometry-reference consistency remain unresolved.
More supported surfaces can also encode biased geometry. Do not infer physical
correctness from full rank,normal diversity,plane residual or model agreement.
No invented point times,new deskew or officialGT/metric replacement.

Whole-sequence sparse mapping and incremental RAP initialization should remain
separate later tests. Report full ATE plus unchanged official ter/rer,runtime,
false-loop effects and exposure; independent system utility is still unestablished.
