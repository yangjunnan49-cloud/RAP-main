# Concrete Evidence Dependencies

Late design-only supplement. This is an evidence request specification, not a
sent message, a download request or authorization to acquire data. No placeholder
below is an authenticated fact; unknown fields must remain UNKNOWN until bound
to a specific source. Existing weak-reference engineering roles remain usable
within their limits, not promoted to independent physical confirmation.

## Exact Acquisition And Frame Association

Required evidence: release/archive identifier, provider or original acquisition
record, extraction/member manifest, local content identities and the exact
mapping from recording/sequence/frame ID to scan member, pose row and time row.
Record whether indices are original capture IDs or a renumbered extraction.
Missing indices, duplicate frames, dropped sensor packets and unavailable
intervals must stay explicit. Counts/min-max/file sizes are not content identity.

For current POSS00,4170 scans exist in3850-5268 and6750-9500;5269-6749 is missing.
Two36924-row pose/time tables do not fill that hole. The saved HTTP ZIP URL and
uncompressed-size resume condition are downloader behavior, not an authenticated
manifest of current bytes. No persistent per-member receipt was written by that
script. A ZIP library's possible transient CRC check is a different claim.

For KITTI00/09 physical questions, obtain the authoritative odometry-to-raw-drive
and raw-frame association for the exact release/extraction. An intended public
format mapping does not by itself authenticate our extraction. Do not guess a
drive name from temporal or geometric similarity. No extra local radius/offset
sweep can supply an external acquisition record.

## Reference Pose And Coordinate Definitions

Required evidence: the method/instruments used to construct each reference;
whether a row maps sensor-to-world or world-to-sensor; which physical sensor/body
is represented; calibration direction and rectification; axis units, handedness,
world-origin/gravity definition and any interpolation/fusion. Bind the actual
pose/calibration release, not just a format-compatible loader.

The POSS camera projection readme describes point projection using its transform.
It does not identify which sensor frame the pose table represents. Horizontal
position traces cannot uniquely choose a sensor/world convention(FTI0). Neither
this uncertainty nor the09 source-observation conflict proves the reference
wrong. Keep official GT and benchmark scoring unchanged; any separately supplied
reference would require its own declared role and must not replace old outcomes.

## Time And Motion Compensation

Required evidence: timestamp clock/units/epoch, clock synchronization/calibration,
which scan event each timestamp denotes, scan start/end timing, point acquisition
order/time and any upstream motion compensation. State what is measured versus
inferred from angle/order. For cross-sensor comparison, bind each clock and its
association rather than relying on increasing rows alone.

Current POSS timestamps are strictly increasing but not an arithmetic grid.
That numerical fact authenticates neither physical rate nor epoch. Current
XYZI schema has no measured per-return time field; a synthetic azimuth-time
helper is not an acquisition record. No real point times are synthesized or
deskew configuration changed by this request.

## Exposure And Checkpoint Membership

Required evidence: original task/session role, history of fitting/calibration/
evaluation/model selection, site/recording relationship and exact checkpoint
training/capture membership when a pretraining-exclusion claim is intended.
Unknown access history is not untouched data; missing manifests are not an
independence certificate. Retain outcome exposure even if one fitting predicate
excluded the row. POSS-B has12 saved error outcomes in downstream analysis,
while the old finite-mean_dist calibration filter includes0 B rows.

The exact local RAP12-layer checkpoint is identified by SHA256
0c5b9f20ee4dfe2345c3cd47dd0632a3d807a3da69c7653900a755cd06564200.
The earlier name-presence audit/public paper recipe does not authenticate this
file's tensor loading history, curation revision or membership. Do not infer
that a paper's reported08-10 exclusion applies to this local artifact. No new
checkpoint acquisition or unrestricted pickle fallback is authorized here.

## Evidence Acceptance And Owner Decision

For each supplied record, retain who/what published it, exact source/location,
capture/release/retrieval date, identity hash, scope and unresolved alternatives.
An archive hash binds bytes; a trustworthy provider/acquisition link supplies
provenance. A self-written receipt produced now cannot retroactively certify
an old missing acquisition record. Prefer original records over a new local
description that repeats the same assumptions.

Before external retrieval, the owner must separately authorize the source,
objects, storage/network/compute envelope and permitted read/verification task.
No automatic acquisition, install, dataset relabeling or reserved-cohort claim.
Authenticated data alone would still not establish a new useful RAP mechanism:
the distinct observable, common-input strong controls, complete populations and
system/effect gates in NEXT_SCIENCE_DESIGN remain necessary.
