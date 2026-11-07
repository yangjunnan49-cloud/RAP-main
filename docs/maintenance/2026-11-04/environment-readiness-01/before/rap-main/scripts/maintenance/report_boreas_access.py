"""Report completed source-access evidence; no model/data selection outcomes."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-15/boreas-access-01')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
assert not (OUT/'INCOMPLETE').exists()
manifest=read(OUT/'artifact_hashes.json')
assert all(sha(OUT/p)==h for p,h in manifest.items())
v=read(OUT/'validation.json');assert v['access_verified']
items=read(OUT/'download_manifest.json')
assert all(sha(OUT/r['path'])==r['sha256'] for r in items)
lines=['# Boreas public access and source-format result','',
       '**Public access and bounded format check passed. No cohort or RAP outcomes.**','',
       'PG-V1 remains INCONCLUSIVE_DATA on KITTI09. This separate check obtained '
       'metadata and two raw examples for a prospective replacement data annex; '
       'it does not amend PG-V1 or prove sample adequacy.','',
       '| Sequence | Pose rows | Duration s | Median interval s | First scan points | Point-time offsets s |',
       '|---|---:|---:|---:|---:|---|']
fig,ax=plt.subplots(figsize=(7,6))
for r in v['summary']:
    lines.append(f"| {r['sequence']} | {r['pose_rows']} | {r['duration_s']:.3f} | "
                 f"{r['median_interval_s']:.6f} | {r['first_scan_points']} | {r['point_time_offset_minmax']} |")
    a=np.loadtxt(OUT/'downloads'/r['sequence']/'lidar_poses.csv',delimiter=',',skiprows=1)
    ax.plot(a[:,1],a[:,2],linewidth=.7,label=r['sequence'].replace('boreas-',''))
ax.set_aspect('equal');ax.set_xlabel('Supplied ENU x (m)');ax.set_ylabel('Supplied ENU y (m)')
ax.legend(fontsize=8);ax.set_title('Position metadata only; no point-cloud overlap claim')
fig.tight_layout();fig.savefig(OUT/'route_metadata.png',dpi=150);plt.close(fig)
lines+=['',f"Downloaded {len(items)} objects / {v['bytes_downloaded']:,} bytes "
        f"({v['bytes_downloaded']/2**20:.3f} MiB) in {v['wall_s']:.3f}s. "
        'This is one bounded transfer, not a stable throughput benchmark. All '
        'downloaded object hashes were rechecked. No AWS credentials or identity '
        'submission, SDK install or execution of downloaded source occurred.','',
        'CSV timestamps are strictly increasing; numeric fields and both six-field '
        'float32 scans are finite. First scan filenames match the first pose timestamp. '
        'Both calibration matrices pass finite/rigid checks. Full pose orientation, '
        'real aligned-cloud geometry and LiDAR-only support transport still need the '
        'separate adapter validation. The header says GPSTime; units were checked '
        'against the documented microsecond filename convention, not guessed.','',
        f"{v['second_poses_within_10m_of_first']:,}/{v['second_session_pose_count']:,} "
        'second-session positions lie within10m of a first-session position; median '
        f"nearest position distance is {v['cross_session_position_distance_median']:.6f}m. "
        'This demonstrates positional overlap of the inspected metadata only. It '
        'does not count independent pairs, positive registration labels, support '
        'availability or four-stratum eligibility.','',
        '![Position metadata](route_metadata.png)','',
        '## Access sources and remaining boundary','',
        'The [AWS registry](https://registry.opendata.aws/boreas/) lists unsigned '
        'access without an AWS account and CC BY4.0. The '
        '[official guide](https://github.com/utiasASRL/pyboreas/blob/master/DATA_REFERENCE.md) '
        'describes repeated traversals, timestamps and sensor formats. The first '
        'two sessions were chosen from the '
        '[official localization training list](https://github.com/utiasASRL/pyboreas/blob/master/pyboreas/data/splits.py) '
        'before this download. Official dataset train membership is not this '
        'project\'s model training split or proof of RAP pretraining exclusion.','',
        'KITTI-360 was not acquired: its '
        '[official page](https://www.cvlibs.net/datasets/kitti-360/) requires '
        'registration and intended-use information. No alternate download link '
        'was used to bypass that process. MulRan identity requirements remain '
        'unanswered; Boreas permits this access check without them. NCLT stays external.','',
        'Next: write the bounded Boreas cross-session adapter/data annex against '
        'these exact source identities, then validate coordinate/point-time and '
        'causal LiDAR motion on a small fixed window before bulk acquisition. '
        'Estimate data volume and measured download cost before committing to full '
        'routes. Follow [adapter requirements](ADAPTER_REQUIREMENTS.md). No full '
        'dataset, confirmation membership, adapter or scored experiment is claimed '
        'complete. Keep the fixed support-selector route and neural expansion stopped.','',
        'Both original repository HEADs and production defaults remain unchanged. '
        'Only RAP-main maintenance helpers, documents and scoped data artifacts '
        'were added; no commit/push/pull/reset/cleanup. No download remains running.','']
with (OUT/'REPORT.md').open('x') as f:f.write('\n'.join(lines))
save(OUT/'closure_validation.json',dict(passed=True,original_manifest_files=len(manifest),
     downloaded_objects=len(items),download_bytes=v['bytes_downloaded'],
     generator_sha256=sha(Path(__file__))))
save(OUT/'closure_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()})
print('Boreas access report complete',flush=True)
