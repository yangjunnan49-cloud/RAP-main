"""Bounded public-data downloads and metadata inspection; no downloaded code execution."""
import csv
import hashlib
import io
import json
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy.spatial import cKDTree

OUT=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-15/boreas-access-01')
DEST=OUT/'downloads'
DEST.mkdir(exist_ok=False)
(OUT/'INCOMPLETE').write_text('Public access and metadata check pending\n')
start=time.monotonic();items=[];downloaded=0

def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(url,name):
    global downloaded
    if time.monotonic()-start>1200:raise RuntimeError('20-minute cap')
    dest=DEST/name;dest.parent.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(url,headers={'User-Agent':'RAP-research-data-audit/1.0'})
    size=0
    with urllib.request.urlopen(req,timeout=60) as response, dest.open('xb') as f:
        while True:
            chunk=response.read(1024*1024)
            if not chunk:break
            size+=len(chunk);downloaded+=len(chunk)
            if size>64*2**20 or downloaded>256*2**20:raise RuntimeError('Byte cap')
            f.write(chunk)
        status=response.status
    items.append(dict(url=url,path=str(dest.relative_to(OUT)),bytes=size,sha256=sha(dest),http_status=status))
    print('Downloaded',name,size,flush=True)
    return dest

save(OUT/'declaration.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),
     plan_sha256=sha(OUT/'ACCESS_PLAN.md'),runner_sha256=sha(Path(__file__)),max_bytes=256*2**20))
base='https://raw.githubusercontent.com/utiasASRL/pyboreas/master/'
for name,path in [('DATA_REFERENCE.md','DATA_REFERENCE.md'),('DATA_LICENSE.md','DATA_LICENSE.md'),
                  ('splits.source.txt','pyboreas/data/splits.py'),('utils.source.txt','pyboreas/utils/utils.py')]:
    fetch(base+path,'reference/'+name)
summaries=[];positions=[]
for seq in ['boreas-2020-11-26-13-58','boreas-2020-12-01-13-26']:
    prefix='https://boreas.s3.us-west-2.amazonaws.com/'+seq+'/'
    path=fetch(prefix+'applanix/lidar_poses.csv',seq+'/lidar_poses.csv')
    rows=list(csv.reader(path.read_text().splitlines()));header=rows.pop(0)
    ts=np.array([int(r[0]) for r in rows],dtype=np.int64)
    values=np.array([[float(x) for x in r[1:]] for r in rows])
    assert len(rows)>100 and (np.diff(ts)>0).all() and np.isfinite(values).all()
    positions.append(values[:,:3])
    cp=fetch(prefix+'calib/T_applanix_lidar.txt',seq+'/T_applanix_lidar.txt')
    calib=np.loadtxt(cp);assert calib.shape==(4,4) and np.isfinite(calib).all()
    orth=float(np.linalg.norm(calib[:3,:3].T@calib[:3,:3]-np.eye(3)))
    assert orth<1e-4 and abs(np.linalg.det(calib[:3,:3])-1)<1e-4
    scan=fetch(prefix+'lidar/'+str(ts[0])+'.bin',seq+'/'+str(ts[0])+'.bin')
    raw=np.fromfile(scan,dtype=np.float32)
    assert raw.size>0 and raw.size%6==0 and np.isfinite(raw).all()
    cloud=raw.reshape(-1,6)
    summaries.append(dict(sequence=seq,pose_rows=len(rows),header=header,
       first_timestamp_us=int(ts[0]),last_timestamp_us=int(ts[-1]),
       duration_s=float((ts[-1]-ts[0])/1e6),median_interval_s=float(np.median(np.diff(ts))/1e6),
       xyz_min=values[:,:3].min(0).tolist(),xyz_max=values[:,:3].max(0).tolist(),
       calibration_orthogonality=orth,first_scan_points=len(cloud),
       point_time_offset_minmax=[float(cloud[:,-1].min()),float(cloud[:,-1].max())]))
distance,index=cKDTree(positions[0]).query(positions[1],workers=1)
result=dict(access_verified=True,summary=summaries,
     second_session_pose_count=len(distance),second_poses_within_10m_of_first=int((distance<=10).sum()),
     cross_session_position_distance_median=float(np.median(distance)),
     scope='Position-only metadata overlap; not point overlap, cohort adequacy or independent samples',
     bytes_downloaded=downloaded,raw_scans_downloaded=2,wall_s=time.monotonic()-start,
     RAP_generations=0,cohort_frozen=False)
save(OUT/'download_manifest.json',items)
save(OUT/'validation.json',result)
(OUT/'INCOMPLETE').unlink()
save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()})
print(json.dumps(result),flush=True)
