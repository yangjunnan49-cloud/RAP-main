# RAD1: validated negative raw endpoint association screen

Decision: **NO_RAW_ASSOCIATION_DECODER_SIGNAL**. The valid result is the
separately frozen **attempt-02**, independently validated through final GT
evaluation. The original attempt remains INCOMPLETE after its disclosed
rotation-degeneracy failure. Its complete bank and all frozen sources survive.
Read AMENDMENT_01.md, attempt-02/PROTOCOL.md, summary.json, validation.json
and seals under attempt-02. Owner authorized planning/handoff/execution on
2026-10-07 following the measurement-interface reassessment.

## What was actually tested

All200 original F2 development pairs,100 each on00/08, retained original
order, inputs, strata and four native generations. No neural inference or
training ran. R used final raw generated anchor coordinates to propose
cross-view original row associations, then fitted original measured points.
P applied the identical association/solver to proper rigid images of those
raw outputs. D used saved miniSpinNet descriptors with the same budget and
solver. Z destroyed the generated-coordinate/original-row binding by fixed
independent permutations. N retained original minimum-rigidity selection;
NG reselected those same native poses using the new geometric rule.

Mutual-top3 associations capped512;32 deterministic greedy compatible seeds,
64-point support cap,1m compatibility/inlier thresholds, three proper rigid
refits. Selection used original common-cloud points excluded from fitting
rows; these are unused fitting points, not independent observations or unseen
model context. All arms used the same selection and full F2 geometry gate.
Failure/fallback remained in denominators. No GT oracle selected output.
Each arm ultimately produced800 valid fitted poses and zero fallback poses;
all200 selected outputs per arm also have zero fallback. These counts are
reported descriptively from the independently sealed banks.

The essential control is P: if generated coordinates are exactly rigid images
A*x and B*y, their cross-view Euclidean distances are equivalent to matching
x with inv(A)*B*y. A benefit shared with P/NG does not establish useful raw
nonrigid structure, even though it may change pose decoding.

## Correctness failure and separate repair

Original1497 identities froze before101 synthetic files and200 real NPZs.
Synthetic Horn checks passed, but independent real-bank validation failed
at08_384_634/D0 after120 complete pairs. Both implementations selected the
same support and consensus masks. Nine final correspondences reused point
rows: the two point sets were noncollinear, yet cross-covariance was rank1.
Different proper rotations had identical minimum SSE; pose delta24.7894.
This was a missing rotation-identifiability check, not an accuracy result.

AMENDMENT_01 defines a shared objective eigengap rejection before every fit,
independently implemented through Kabsch spectra and Horn eigenvalues. The
repair is disclosed as a changed correctness condition; its relative cutoff
is1e-6, the value already used for the original point-set rank check. This
does not claim the two different rank quantities have identical sensitivity.
All data, associations, budgets, consensus thresholds, selectors, admission
and scientific outcome gates stay unchanged. GT had not been parsed.

Attempt-02 froze1501 identities including original freeze/seal/failure and
amendment. It independently passes the additional crossed-correspondence
degeneracy case and reruns the complete200-pair bank. Original programs,
bank and failure are not overwritten, silently relabeled or used as repaired
predictions. Root INCOMPLETE describes that preserved original attempt;
the repaired attempt's INCOMPLETE was removed only after final validation.

## Measured outcome

Strict success means RTE<=1m and RRE<=5deg on75 positives per sequence.
Numbers are automatically selected poses, not best-of-four oracle outputs.

| Method | 00 selected strict /75 | 08 selected strict /75 | 00 incorrect accepts /100 | 08 incorrect accepts /100 |
| --- | ---: | ---: | ---: | ---: |
| N original RAP selection |49|30|1|10|
| NG native geometric selection |50|31|2|10|
| R raw association decoder |50|30|3|10|
| P rigid-output control |50|31|2|10|
| D descriptor control |25|19|3|8|
| Z row-identity destruction |0|0|0|0|

R selected **0/41** strict recoveries on the fixed hard08 set versus required
>=5. A separately labeled post-hoc descriptive audit of the sealed outcomes
also finds **zero oracle-available hard08 poses** in every R/P/D/Z arm. This
does not modify gates or license another selector: this decoder's difficult
cases lacked a correct candidate. It is not a global ceiling for RAP outputs
or all possible correspondence constructions.

08 R strict gain is0 versus required>=4 over N; it trails P and NG by1 and
only beats the weak D control. Clipped error falls1.579930->1.520489, about
3.76%, below required5%.00 clipped error worsens1.472846->1.566873, about
6.38%, exceeding the2% safety allowance.00 ordinary strict falls25->23;
correct accepts23->21 and incorrect accepts1->3. Confuser admissions remain
zero for every arm on both sequences. Cost and08 admission/ordinary safety
pass, but the conjunction of material and safety gates fails.

Descriptive paired counts: R gains3/losses2 strict cases versus N on00, and
gains1/losses1 on08. Neither the00 net+1 nor its equality with P is evidence
of a distinct raw contribution. Oracle-positive counts are N/R/P=52/52/53
on00 and34/32/33 on08. No new online admission, graph or trajectory result
exists. Official E0 ter/rer/ATE and strict labels are unchanged.

## Independent evidence and resources

Attempt-02 contains101 sealed synthetic files and200 complete real NPZs.
GT-free independent validation reconstructs3,200 solves and1,627,908
associations. Source-binding checks reproduce both original2000-point
anchors and full geometry clouds exactly. Native matrices/rigidity and old
admissions reproduce. Horn/Kabsch max pose delta4.563e-11; association-distance
delta4.721e-13; projected-coordinate delta7.414e-13; geometry-score delta
6.040e-14. Bounded brute force checks677,600,000 point-pair distances.
Native rigid bridge delta6.070e-5 is below frozen5e-4 tolerance.

GT-free validation sealed at2026-10-07T01:13:57Z before evaluator access.
Final independent evaluation reproduces all200 errors, strata, original N
labels, aggregates and gates; max error delta2.274e-13. No repaired-attempt
failure, further gate/parameter change or bank edit followed validation.

| Successful attempt-02 stage | Wall seconds |
| --- | ---: |
| Synthetic bank |11.355|
| Independent synthetic verification |3.692|
| Complete real bank, all arms |565.908|
| Independent GT-free verification |330.985|
| Evaluation |2.118|
| Independent evaluation |2.041|

Stage total916.099s, excluding source hashing before stages, diagnosis and
documentation. Peak stage RSS422,408,192 bytes(~0.393GiB); no GPU/model work.
New attempt NPZ bytes119,180,518(~113.66MiB). R incremental association/
fitting/selection/admission work100.671s versus historical800 native-generation
wall460.573s, ratio21.858%. This passes the25% historical reference gate;
it is not a live online overhead benchmark. Shared preprocessing/native
scores27.460s, input IO8.456s; serialization, repeated hash checks and other
bank overhead remain in total565.908s. Individual arms R/P/D/Z cost
100.671/100.526/110.052/91.921s. All repaired stage/resource caps pass.

Failed original work is additional: bank544.416s, synthetic11.873s and
independent synthetic3.460s; its failed bank-validator log records199.1s
through120 complete pairs, but full failed-validator wall/RSS was not saved.
Do not omit that failed work when discussing research effort. Total retained
original+repair artifacts are recorded in RESOURCE_AUDIT.json after delivery
records are finalized, below300MiB. Both original banks are retained.

## Interpretation and next boundary

This frozen decoder fails to turn raw nonrigid endpoint structure into useful
new hard-pair poses. P and NG account for the small selected-pose changes;
00 safety regresses. There is no raw-specific pose gain, uncertainty
calibration, physically correct alias resolution, system gain or originality
result. D's weakness is confined to this exact sparse correspondence/solver
construction, not a conclusion about every descriptor matcher. The periodic
synthetic alias still passes physical geometry and remains disclosed.

Stop this exact final-raw mutual-top3/clique/refit route. Do not rescue it by
step/top-k/seed/density/noise/solver/selector/gate/cohort changes or promote
P/NG as a substitute continuation. See NEXT_ROUND_PLAN.md for a distinct
read-only measurement-source/statistical-model audit, planned only. A new
information-bearing construction needs evidence before another pose screen.
Paper wording alone cannot satisfy the owner's original breakthrough goal.

All earlier negative stops and immutable banks remain. Both repositories'
original HEADs4055d929c594b0033aafc6eed339c910369eef55 and
6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6, branches and existing dirty work
are preserved. New algorithm sources are isolated in RAP-SLAM/scripts;
drivers/validators and records are in RAP-main maintenance. No training,
production/default/model/manuscript edit, acquisition/install, commit or Git
sync. Unknown local checkpoint training membership and09 physical discrepancy
remain unresolved. These are exposed development findings, not held-out
accuracy confirmation or a general impossibility result.
