# DS0: a bounded readout pilot has an actionable data/supervision design

**READ_ONLY_DESIGN_COMPLETE**, not an experiment or training result. The owner
requested starting the next stage after validated TR0. DS0 inspects existing
metadata/schema/source and primary documentation; no raw point-cloud payload,
relative GT, correspondence label, model inference, optimization or GT error
was generated. Numeric pose files were read for row/column/finiteness checks,
not hidden under a claim of no GT access. No numeric poses are retained here.

## Actual local data and roles

KITTI00-10 has23201 contiguous named raw scan files. All positive sizes are
divisible by16 bytes; scan/pose/timestamp counts agree, pose columns12 finite,
times strictly increasing, and finite12-valueTr calibration keys present.
Counts00..10:4541,1101,4661,801,271,2761,1101,1101,4071,1591,1201.
This establishes schema/metadata readiness, not raw numeric integrity or
physical local GT accuracy. DATA_AUDIT and raw_metadata_manifest store evidence.

Oxford contains five finite eight-column TUM files, with no expected point-cloud
sequence/calibration directories observed. It cannot currently supply a
confirmed evaluation set. part2 contains only unrelated immediate items;
no relevant archive observed, no deeper/content inspection. This does not
assert that no other copy exists outside the authorized inventory.

The role draft is immediately implementable:144 fit windows00-05,12 diagnostic
development06,48 historically exposed readout evaluation07-10. All204 are
uniform count-derived indices with three consecutive scans and no shared raw
frame path between windows. Physical site separation is not established.
Historical M3 also used02 calibration;01-04 are not claimed unseen. Existing
E0 six sequences and08 pair exposure and unknown checkpoint membership remain.
See DATA_ROLES and WINDOW_MANIFEST_DRAFT; this is not a training experiment freeze.

## Two overlooked supervision/provenance issues change the plan

The KITTI official documentation warns about GT error on very short segments.
Consequently this proposal uses set-valued weak matches/unmatched/ignored
regions with third-view support, rather than exact nearest-point identity.
Paired exploratory GT comparisons do not establish physical millimetre accuracy;
full100-800m system ter/rotation and aligned ATE remain the relevant later test.
[KITTI official specification](https://www.cvlibs.net/datasets/kitti/eval_odometry.php).

The RAP paper includes Oxford5/6 scenes in training and states KITTI08-10 were
excluded. Published training roles cannot establish our local checkpoint's
membership. Oxford is not a zero-shot set merely because it is a different
dataset. [RAP training data](https://arxiv.org/html/2512.01850v1).
Also Oxford official GT is base-frame motion; first-pose anchoring generally
does not remove the sensor extrinsic's rotational lever arm. The current loader
does not apply it. This is a source/convention limitation, not a new accuracy
diagnosis or loader fix. [Oxford GT convention](https://dynamic.robots.ox.ac.uk/datasets/oxford-spires/).

## A concrete experiment, rather than another feature-dimension claim

TRAINING_ANNEX_DRAFT specifies one frozen-backbone small-head pilot. A shared
75202-parameter nominal head uses direct descriptors D, cross-view-separated
frozen tokens I, or joint tokens J. D's zero padding leaves61440 inactive
weights, disclosed; I/J active capacity matches. Same labels, original-point
solver, three fixed seeds and1000 updates; no epoch/best-seed/hyperparameter
selection. I/J differ in global context grouping throughout all five flow steps.
Source supports that grouping; runtime independence is not yet validated, and
I can be outside pretrained one-part distribution. It is an ablation, not
an optimized external odometry baseline. All costs must be reported.

The readout produces new measured-point correspondences and a coupled proper
SE3 fit. Labels preserve multiple positive candidates<=.30m, unmatched>=.60m,
third-view observable support<=.60m and ignored uncertain rows. No verified
physical point identity or real dynamic/static annotation is asserted. A
separately sealed engineering/weak-label preflight must pass before fitting.
The planned weak motion loss and angular scoring convention are explicit;
official GT/old metrics are not edited. Generic matching has close prior art,
so a small MLP or advantage over an untrained matcher is insufficient.
[SuperGlue](https://arxiv.org/abs/1911.11763),
[GeoTransformer](https://arxiv.org/abs/2202.06688).

Admission requires joint-over-I/D improvement in both translation and rotation,
per-sequence safety and complete output coverage. Useful local motion additionally
must beat the same-point G3 and saved KISS07/09/10 at identical endpoints.
Without that, no trajectory stage. A pass still needs a separate full-system
protocol for ter AND aligned ATE; no production/default promotion is authorized.
This is an exploratory master's-thesis development route; independent physical/
checkpoint/site confirmation remains unavailable, not silently assumed.

## Completed work, costs and boundary

The standard-library audit took34.800947s including source/TR0 bank rechecks.
It inventories23201 raw metadata entries,16 pose-file schemas (11 KITTI+5
Oxford),11 timestamp/calibration sets and204 draft windows. CPU only, no GPU
initialization/model loading. TR0's109-identity freeze,20-file bank and validated
result reproduce unchanged before/after; audited source hashes unchanged.
No experimental failure/repair or new INCOMPLETE. Earlier paper-page fetch
failures were resolved via primary arXiv pages and are not experiment failures.

No head implementation, label bank, independent-context runtime bank, experiment
freeze or fit exists. Current no-fitting boundary persists until explicit owner
scope. The draft requests only small-head training after prerequisites, leaving
RAP and descriptor weights frozen. Acquisition/install, production/default/
model/manuscript edit, commit/Git sync remain out of scope. All old negative
stops/banks/official labels/metrics,09 discrepancy and original-breakthrough
requirement persist. Both original HEADs/branches/dirty work are preserved.
