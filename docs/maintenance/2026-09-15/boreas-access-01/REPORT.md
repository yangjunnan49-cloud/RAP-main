# Boreas public access and source-format result

**Public access and bounded format check passed. No cohort or RAP outcomes.**

PG-V1 remains INCONCLUSIVE_DATA on KITTI09. This separate check obtained metadata and two raw examples for a prospective replacement data annex; it does not amend PG-V1 or prove sample adequacy.

| Sequence | Pose rows | Duration s | Median interval s | First scan points | Point-time offsets s |
|---|---:|---:|---:|---:|---|
| boreas-2020-11-26-13-58 | 9984 | 1035.382 | 0.103714 | 213346 | [-0.0517580509185791, 0.0517575740814209] |
| boreas-2020-12-01-13-26 | 9277 | 961.959 | 0.103699 | 207817 | [-0.0517575740814209, 0.0517580509185791] |

Downloaded 10 objects / 15,147,962 bytes (14.446 MiB) in 393.233s. This is one bounded transfer, not a stable throughput benchmark. All downloaded object hashes were rechecked. No AWS credentials or identity submission, SDK install or execution of downloaded source occurred.

CSV timestamps are strictly increasing; numeric fields and both six-field float32 scans are finite. First scan filenames match the first pose timestamp. Both calibration matrices pass finite/rigid checks. Full pose orientation, real aligned-cloud geometry and LiDAR-only support transport still need the separate adapter validation. The header says GPSTime; units were checked against the documented microsecond filename convention, not guessed.

9,277/9,277 second-session positions lie within10m of a first-session position; median nearest position distance is 0.427102m. This demonstrates positional overlap of the inspected metadata only. It does not count independent pairs, positive registration labels, support availability or four-stratum eligibility.

![Position metadata](route_metadata.png)

## Access sources and remaining boundary

The [AWS registry](https://registry.opendata.aws/boreas/) lists unsigned access without an AWS account and CC BY4.0. The [official guide](https://github.com/utiasASRL/pyboreas/blob/master/DATA_REFERENCE.md) describes repeated traversals, timestamps and sensor formats. The first two sessions were chosen from the [official localization training list](https://github.com/utiasASRL/pyboreas/blob/master/pyboreas/data/splits.py) before this download. Official dataset train membership is not this project's model training split or proof of RAP pretraining exclusion.

KITTI-360 was not acquired: its [official page](https://www.cvlibs.net/datasets/kitti-360/) requires registration and intended-use information. No alternate download link was used to bypass that process. MulRan identity requirements remain unanswered; Boreas permits this access check without them. NCLT stays external.

Next: write the bounded Boreas cross-session adapter/data annex against these exact source identities, then validate coordinate/point-time and causal LiDAR motion on a small fixed window before bulk acquisition. Estimate data volume and measured download cost before committing to full routes. Follow [adapter requirements](ADAPTER_REQUIREMENTS.md). No full dataset, confirmation membership, adapter or scored experiment is claimed complete. Keep the fixed support-selector route and neural expansion stopped.

Both original repository HEADs and production defaults remain unchanged. Only RAP-main maintenance helpers, documents and scoped data artifacts were added; no commit/push/pull/reset/cleanup. No download remains running.
