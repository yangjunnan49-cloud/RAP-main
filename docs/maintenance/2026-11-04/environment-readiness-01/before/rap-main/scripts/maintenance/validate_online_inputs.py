"""Independent raw input/gate/calibration checks, before any neural output."""
import sys,json,time,resource,hashlib,importlib.metadata
from pathlib import Path
import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree
M=Path('/mnt/e/githouse/RAP-main'); B=M/'docs/maintenance/2026-10-05/online-geotransformer-01'; I=B/'input-bank'; F=M/'docs/maintenance/2026-10-05/geotransformer-feasibility-01'
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def score(a,b,T):
    transformed=b@T[:3,:3].T+T[:3,3]; x=cKDTree(a).query(transformed)[0]; y=cKDTree(transformed).query(a)[0]
    return .5*((x<1).mean()+(y<1).mean()),.5*(x.mean()+y.mean())
def main():
    t=time.monotonic(); freeze=read(B/'freeze.json'); seal=read(B/'input_seal.json'); rows=read(I/'attempts.json')
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    for p,h in read(F/'preflight_freeze.json')['files'].items(): assert sha(p)==h,p
    assert freeze['packages']=={n:importlib.metadata.version(n) for n in freeze['packages']}
    assert seal['freeze_sha256']==sha(B/'freeze.json')
    assert seal['files']=={str(p.relative_to(I)):sha(p) for p in I.rglob('*') if p.is_file()}
    assert freeze['utc']<read(I/'execution.json')['started_utc']<seal['utc']
    assert not (B/'prediction-bank').exists() and not (B/'evaluation-01').exists()
    census=read(I/'scan_census.json'); regenerated={}; points_checked=0
    for c in census:
        s,f=c['seq'],c['frame']; raw=M.parent/'Datasets/data_odometry_velodyne/dataset/sequences'/s/'velodyne'/f'{f:06d}.bin'
        p=np.fromfile(raw,dtype='float32').reshape(-1,4)[:,:3]; p=p[np.linalg.norm(p,axis=1)>=1.5]
        x,y,z=p.T; rho=np.hypot(x,y); safe=rho>1e-6; angle=np.deg2rad(.205)
        corrected=p.copy(); corrected[:,0]=np.where(safe,x*np.cos(angle)-x*z/np.maximum(rho,1e-6)*np.sin(angle),x)
        corrected[:,1]=np.where(safe,y*np.cos(angle)-y*z/np.maximum(rho,1e-6)*np.sin(angle),y)
        corrected[:,2]=np.where(safe,z*np.cos(angle)+rho*np.sin(angle),z)
        cloud=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(corrected.astype('float64'))).voxel_down_sample(.4)
        cloud,_=cloud.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.5); ds=np.asarray(cloud.points,dtype='float32')
        if len(ds)>4000: ds=ds[np.random.default_rng(42).choice(len(ds),4000,replace=False)]
        saved=np.load(I/s/f'{f:06d}.npy'); assert np.array_equal(ds,saved),(s,f)
        assert 200<=len(ds)<=4000 and c['points']==len(ds); points_checked+=len(ds); regenerated[s,f]=ds
    accepted=0; deltas=[]
    for s,rr in rows.items():
        old=read(M/'docs/maintenance/2026-09-29/system-opportunity-audit-01/attempt-01'/s/'candidates.json'); assert rr==old
        for r in rr:
            a,b=regenerated[s,r['i']],regenerated[s,r['j']]; ov,md=score(a,b,np.array(r['T_rel']))
            assert abs(ov-r['overlap'])<=1e-6 and abs(md-r['mean_dist'])<=1e-6
            admitted=ov>=.7 and md<=2.5; assert admitted==(r['status']=='accepted'); accepted+=admitted
            deltas.append(max(abs(ov-r['overlap']),abs(md-r['mean_dist'])))
    assert sum(map(len,rows.values()))==71 and accepted==58
    # Use separately validated CPU grid extension; independent SciPy radius census
    # and histogram/percentile logic, without the official calibration helper.
    import torch
    sys.path.insert(0,str(F/'extension-build-v2')); import rap_geotransformer_ext as ext
    hist_n=int(np.ceil(4/3*np.pi*(1.275/.3+1)**3)); hist=np.zeros((5,hist_n),dtype='int64'); calibrated_pairs=0
    for s,rr in rows.items():
        for r in rr:
            clouds=[regenerated[s,r['i']],regenerated[s,r['j']]]; radius=1.275; voxel=.3
            for stage in range(5):
                if stage:
                    merged=torch.from_numpy(np.concatenate(clouds)); lens=torch.tensor([len(x) for x in clouds],dtype=torch.int64)
                    pp,ll=ext.grid_subsampling(merged,lens,voxel); aa=pp.numpy(); split=int(ll[0]); clouds=[aa[:split],aa[split:]]
                counts=np.concatenate([cKDTree(cloud).query_ball_point(cloud,radius,return_length=True) for cloud in clouds]); counts=np.minimum(counts,hist_n)
                hist[stage]+=np.bincount(counts,minlength=hist_n)[:hist_n]
                voxel*=2; radius*=2
            calibrated_pairs+=1
            if np.min(hist.sum(1))>2000: break
        if np.min(hist.sum(1))>2000: break
    limits=(np.cumsum(hist.T,axis=0)<.8*hist.sum(1)).sum(0).tolist()
    assert limits==read(I/'neighbor_limits.json')['limits'],(limits,read(I/'neighbor_limits.json'))
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    record=dict(passed=True,utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),freeze_sha256=sha(B/'freeze.json'),input_seal_sha256=sha(B/'input_seal.json'),scans=len(census),exact_points=points_checked,pairs=71,native_accepted=accepted,native_score_max_delta=float(max(deltas)),independent_neighbor_limits=limits,calibration_pairs=calibrated_pairs,calibration_histogram=hist.tolist(),wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    assert record['wall_s']+read(I/'execution.json')['wall_s']<1800 and record['peak_rss_gib']<6
    with (B/'input_validation.json').open('x') as f: json.dump(record,f,indent=2)
    print('independently verified exact inputs',len(census),'all71 gate scores; neighbor limits',limits,flush=True)
if __name__=='__main__': main()
