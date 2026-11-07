# Boreas bounded access and metadata check

Declared before downloads. PG-V1 KITTI09 data gate failed; no PG-V1 inference
will run. This is a separate source-feasibility check, not a cohort amendment.

Use the first two sequences in the official localization training list:
boreas-2020-11-26-13-58 and boreas-2020-12-01-13-26. Inspect complete lidar pose
CSV and LiDAR/Applanix calibration for each, plus only the first timestamped
LiDAR scan from each CSV. Preserve official reference/splits/license/source text
for provenance, without installing or executing downloaded code.

Cap256MiB downloaded,64MiB per object,20 minutes and two raw scans. Use public
unsigned S3 requests to bucket boreas, us-west-2. No AWS account, credential,
registration, message or identity submission. Record hashes, sizes and URLs.
Read-only metadata checks: timestamp monotonicity, numeric finiteness, source
existence and cross-session position proximity. Proximity is not point-cloud
overlap, independent sample count or proof of PG-V1 stratum adequacy.

Do not choose pair outcomes, substitute GT for causal odometry, train, or run RAP.
Any later use needs a prospective cross-session/adapter annex: exact roles,
coordinate convention, causal support/deskew policy, non-GT retrieval, sampling,
resource cap and independent validation. Preserve NCLT as external and make no
claim that Boreas is excluded from RAP pretraining.

Sources: [AWS registry](https://registry.opendata.aws/boreas/),
[official guide](https://github.com/utiasASRL/pyboreas/blob/master/DATA_REFERENCE.md),
[official splits](https://github.com/utiasASRL/pyboreas/blob/master/pyboreas/data/splits.py).
