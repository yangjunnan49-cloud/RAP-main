# RLP1 stopped before fitting: fixed weak-label coverage fails

**VALIDATED_PREREQUISITE_STOP**, decision
INSUFFICIENT_FIXED_WEAK_LABEL_COVERAGE. The owner approved the complete reviewed
pilot. Its mandatory all-pair/all-direction weak-label preflight failed, so
the authorized conditional fitting/evaluation stages did not start. This is
not a negative result about joint-token learnability or model accuracy.

## Completed engineering result

The separately frozen attempt-03 four-window GT-free engineering bank has16
complete NPZs and independent validation. On00/05/06/07,t200, native J exactly
reproduces TR0 points/descriptors/noise, normalization, raw/state/part/relative
poses and512-D tokens. I uses three one-part examples for all five flow calls
with unchanged rows/conditions/features/scale/anchor roles and original noise.
Its repeats are exact. Perturbing only the third scan's initial noise by+1
leaves the first two scans' raw/state/tokens exactly unchanged.

Independent reconstruction verifies12 scans,12000 processed points,384000
descriptor values and original noise; passive last-layer/export equality,
five nominal times and batch/part row bindings; native one-value J versus
three-value I CUDA vector draws and outer RNG restoration. Quaternion Horn
reconstructs poses with maximum delta5.46229728115577e-14<1e-8. Strict restricted
344/58-key loading and parameter/mode invariance pass. No native sampler/model/
default changes. This establishes an interface control, not physical motion
correctness, calibrated confidence or originality.

## The stopping evidence

The weak-label preflight froze before its synthetic and real outputs, after
engineering bank/source validation. It uses exactly the approved .30m set
positive/.60m unmatched/third-view support rules on the original1000 processed
points per scan. Input order is [199,200,198]. Every direction of all three
pairs must have at least20 supported positive rows in each fixed window.

| Query/target part, candidate/source part | 00 positives | 05 positives | 06 positives |
|---|---:|---:|---:|
| 0,1 (199,200) |92|86|23|
| 0,2 (199,198) |92|74|**15**|
| 1,0 (200,199) |92|90|20|
| 1,2 (200,198) |67|79|23|
| 2,0 (198,199) |99|72|**15**|
| 2,1 (198,200) |73|77|31|

06's199/198 adjacent pair fails in both directions. The primary199/200 pair
meets the floor, but the frozen requirement covers all three training pairs.
There are15 positive/170 unmatched/815 ignored rows for02, and15/163/822 for20.
The writer saved the failing06 file then stopped.07 real labels were not
generated. There is no complete weak-label bank seal or successful weak-stage
validation, and its original INCOMPLETE marker remains.

The separate prerequisite-stop-audit froze all14 existing partial NPZs (11
synthetic plus3 real) and relevant source/GT identities. It imports no readout
algorithm, independently reconstructs brute-force distances, raw camera/LiDAR
relative transforms, six directed masks, third support and counts. Every saved
label mask and class matches exactly; maximum distance/transform delta is
2.2737367544323206e-13<1e-10. Independent quaternion solves match rigid/planar
fixtures to4.163336342344337e-16, reject rank1, verify rounded/reflected proper
rotations and calibration. Three selected soft-solver gradient entries agree
with central finite differences to4.6027300026896256e-11<1e-6.

This audit validates the **stop evidence**, not completion of the failed weak
stage. Four synthetic head backward checks ran before real labels, without
optimizer updates, but their end-of-stage JSON was not written; no independent
head-gradient claim is made from an absent ledger. The saved soft-gradient
fixture is independently validated as above. Physical point identity and
short-segment GT accuracy remain unverified.

## Failure disclosure and prospective corrections

Two engineering writer failures precede attempt-03:

- Original engineering: exact pose replay failed because the writer serialized
  solve(parts0,parts1) while TR0 used inv(parts0)@parts1. Preserve the original
  freeze/runner/validator, empty bank, failure and INCOMPLETE. Amendment01 restores
  native serialization in a separate attempt-02; independent Horn uses unchanged
  tolerance and all scientific settings remain.
- Attempt-02: first00 I repeat snapshot called.copy() on float scale metadata.
  A reused failure filename also caused a secondary FileExistsError; the prior
  failure was not overwritten. Preserve its freeze/source, partial00 J NPZ,
  failure disclosure and INCOMPLETE. Amendment02 uses array/scalar-safe copies
  and distinct attempt failure names. Attempt-03 reruns all four windows.

Neither correction changed model/data/grouping/noise/windows/times/gates or
tolerances. The weak-label shortage is independently validated and receives
**no correction, replacement or threshold/density/seed rescue**.

## Scope, cost and conclusion

The first engineering freeze also fixes the same204 count-derived windows and
big-endian LMF1 input seeds before any labels. No full204 feature bank, full
labels, nine optimizer fits,432 evaluation predictions, GT errors or trajectory
exists. A small readout/solver helper was implemented and instantiated only for
synthetic gradient prerequisites. RAP/miniSpin remain frozen. No production/
default/manuscript edit, acquisition/install, commit or Git synchronization.

RESOURCE_LOG has11 recorded process stages, including failed attempts, freezes
and validators, totaling115.32903792662546s at sampling boundaries. Peak
allocated GPU1.386877GiB, RSS2.688793GiB; new study files about198.34MiB before
delivery documents. WSL startup and final ledger serialization lie outside
those process counters; no runtime-comparator or exact end-to-end benchmark is
claimed. The execution interval and these counters are comfortably within the
60-minute compute cap; other resource caps pass. See RESOURCE_AUDIT.json for
the final enclosing interval and artifact count.

DS0's16 source entries and TR0's20 bank files rehash unchanged at close. Both
original HEADs/branches and existing dirty work remain main4055d929 on
codex/meeting-20260930 and SLAM6d3f2d22 on codex/e0-f1-20260926. Old negative
stops/banks/official GT/metrics,09 discrepancy,unknown checkpoint/site membership
and the owner's original breakthrough requirement persist.

Decision: stop this fixed pilot at its mandatory prerequisite. The result says
the declared weak supervision fails its prospective coverage requirement; it
does not establish that tokens lack useful information, that fitting would
fail, or that labels/GT are physically wrong. No useful local/system/originality
claim is available. A distinct next design must be reviewed prospectively;
this fixed run cannot be resumed through an outcome-dependent rescue.
