"""Exclusive HL0 provenance audit; does not generate or evaluate hypotheses."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path('/mnt/e/githouse/RAP-main')
OUT = ROOT/'docs/maintenance/2026-09-14/hl-v1/preflight-01'
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()
def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2)+'\n')

OUT.mkdir(parents=True,exist_ok=False)
(OUT/'INCOMPLETE').write_text('HL0 checks in progress; no pilot gate claimed.\n')
protocol = ROOT/'docs/maintenance/2026-09-14/HARD_LOOP_EXPERIMENT_PROTOCOL_V1.md'
(OUT/'PROTOCOL.md').write_bytes(protocol.read_bytes())
save('execution_plan.json',dict(scope='HL0 only; KITTI05 resource pairs; no KITTI06 hypothesis outcomes',
    protocol_sha256=sha(protocol),rng_tolerance=1e-6,se3_tolerance=1e-5,gt_tolerance=1e-4,
    profile_selection='First ten support-eligible KITTI05 proximity pairs sorted by HL-V1 pair hash, separation>=200 and distance<=30m; feasibility sample only, not HL1 stratified cohort',
    support='Nearest past keyframe crossing each of 2m/5m cumulative full-frame odometry distance; distinct IDs; age<=5s; exclude both anchors'))
snap=ROOT/'.maintenance-archive/2026-09-09-m0'
summary=json.loads((ROOT/'docs/maintenance/2026-09-09/preservation_summary.json').read_text())
assert not (snap/'INCOMPLETE').exists()
assert sha(snap/'manifest.json')==summary['manifest_sha256']
save('preservation_check.json',dict(manifest_sha256=sha(snap/'manifest.json'),entries=len(json.loads((snap/'manifest.json').read_text())),scope='Manifest integrity and availability; archived payload not fully rehashed in HL0'))
results=[]
for seq,n in [('05',2761),('06',1101)]:
    parent=ROOT/f'docs/maintenance/2026-09-11/full-kitti{seq}-01'
    assert not (parent/'INCOMPLETE').exists()
    assert (parent/'validation.json').exists() and (parent/'REPORT.md').exists()
    manifest=json.loads((parent/'input_manifest.json').read_text())
    mismatches=[]
    for p,h in manifest.items():
        if not Path(p).exists() or sha(p)!=h: mismatches.append(p)
    pipeline=parent/'pipeline'
    frames=json.loads((pipeline/'source_frames.json').read_text())
    ids=frames['source_frame_ids']; times=np.array(frames['timestamps'])
    assert ids==list(range(n)) and len(times)==n and np.isfinite(times).all() and (np.diff(times)>0).all()
    paths=frames['scan_files']
    assert len(paths)==n
    scans=[]
    for i,p in enumerate(paths):
        p=Path(p); assert int(p.stem)==i
        raw=np.fromfile(p,dtype=np.float32)
        assert raw.size>0 and raw.size%4==0 and np.isfinite(raw).all()
        scans.append(dict(source_id=i,path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    base=Path(paths[0]).parents[1]
    assert np.array_equal(times,np.loadtxt(base/'times.txt'))
    odom=np.loadtxt(pipeline/'odom_poses.txt').reshape(-1,3,4)
    assert len(odom)==n and np.isfinite(odom).all()
    kfs=json.loads((pipeline/'keyframes.json').read_text())
    assert kfs==sorted(set(kfs)) and kfs[0]==0 and kfs[-1]==n-1
    save(f'data_{seq}.json',dict(parent=str(parent),source_ids=ids,timestamps=times.tolist(),scans=scans,
        timestamps_sha256=sha(base/'times.txt'),parent_files={str(p):sha(p) for p in pipeline.glob('*.json')},
        odometry_sha256=sha(pipeline/'odom_poses.txt'),keyframes=kfs,input_manifest_mismatches=mismatches))
    results.append(dict(sequence=seq,frames=n,keyframes=len(kfs),rechecked_parent_hashes=len(manifest),mismatches=mismatches))
    print(results[-1],flush=True)
save('provenance_validation.json',results)
