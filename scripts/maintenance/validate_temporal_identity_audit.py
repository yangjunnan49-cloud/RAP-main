"""Independent raw reconstruction, indexing, calibration and brute-force distances."""
import time,resource
import numpy as np
import open3d as o3d
from scipy.spatial.distance import cdist
import validate_dense_propagation as v
B=v.MAIN/'docs/maintenance/2026-10-05/temporal-identity-audit-01'; OLD=B.parent/'online-geotransformer-01'; I=B/'input-bank'; E=B/'evaluation-01'
read,sha,save=v.read,v.digest,v.write
def raw(s,i): return v.DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def reconstruct(s,i):
    p=np.fromfile(raw(s,i),dtype='float32').reshape(-1,4)[:,:3]; p=p[np.linalg.norm(p,axis=1)>=1.5]; x,y,z=p.T; rho=np.hypot(x,y); safe=rho>1e-6; angle=np.deg2rad(.205); corrected=p.copy()
    corrected[:,0]=np.where(safe,x*np.cos(angle)-x*z/np.maximum(rho,1e-6)*np.sin(angle),x); corrected[:,1]=np.where(safe,y*np.cos(angle)-y*z/np.maximum(rho,1e-6)*np.sin(angle),y); corrected[:,2]=np.where(safe,z*np.cos(angle)+rho*np.sin(angle),z)
    cloud=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(corrected.astype('float64'))).voxel_down_sample(.4); cloud,_=cloud.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.5); ds=np.asarray(cloud.points,dtype='float32')
    if len(ds)>4000: ds=ds[np.random.default_rng(42).choice(len(ds),4000,replace=False)]
    return ds
def nearest(x,y): return np.concatenate([cdist(x[k:k+128],y).min(1) for k in range(0,len(x),128)])
def main():
    t=time.monotonic(); freeze=read(B/'freeze.json'); seal=read(B/'bank_seal.json'); result=read(B/'results.json'); identity=read(I/'identity.json'); rows=read(I/'controls.json'); scans=endpoints=distancecount=0; maxdelta=0.; totalrows=0
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    assert seal['freeze_sha256']==sha(B/'freeze.json') and result['bank_seal_sha256']==sha(B/'bank_seal.json')
    assert seal['files']=={str(p.relative_to(I)):sha(p) for p in I.rglob('*') if p.is_file()}
    assert freeze['utc']<read(I/'execution.json')['started_utc']<seal['utc']<result['gt_read_started_utc']
    expected=[]
    for c in read(OLD/'input-bank/scan_census.json'):
        for offset in [-10,10]:
            j=c['frame']+offset
            if 0<=j<__import__('system_opportunity').SEQS[c['seq']]: expected.append(dict(seq=c['seq'],i=c['frame'],j=j,offset=offset,causal=offset<0))
    assert rows==freeze['controls']==expected
    for s in v.SEQS:
        manifest=read(v.src(s)/'source_frames.json'); cam=v.load(v.DATA/'poses'/f'{s}.txt'); n=len(cam); stamps=np.loadtxt(v.DATA/'sequences'/s/'times.txt'); ids=[int(__import__('pathlib').Path(p).stem) for p in manifest['scan_files']]
        assert sorted(int(p.stem) for p in raw(s,0).parent.glob('*.bin'))==list(range(n))==ids==manifest['source_frame_ids']; assert len(stamps)==n and np.array_equal(stamps,manifest['timestamps']) and np.all(np.diff(stamps)>0)
        assert manifest['scan_files']==[str(raw(s,i)) for i in range(n)] and identity[s]['full_absolute_frame_path_and_timestamp_match']
        tr=v.calibration(s); gt=np.linalg.solve(tr,cam@tr); od=v.load(v.src(s)/'odom_poses.txt'); local=[r for r in rows if r['seq']==s]; needed=sorted({r[k] for r in local for k in ['i','j']}); assert len(needed)==identity[s]['scans']
        for i in needed:
            saved=np.load(I/s/f'{i:06d}.npy'); assert np.array_equal(saved,reconstruct(s,i)); scans+=1
            old=OLD/'input-bank'/s/f'{i:06d}.npy'
            if old.exists(): assert np.array_equal(saved,np.load(old)); endpoints+=1
        for k,(r,row) in enumerate(zip(local,result['rows'][s])):
            for key in r: assert r[key]==row[key]
            a=np.load(I/s/f"{r['i']:06d}.npy").astype('float64'); b=np.load(I/s/f"{r['j']:06d}.npy").astype('float64'); poses=dict(GT=np.linalg.solve(gt[r['i']],gt[r['j']]),odom=np.linalg.solve(od[r['i']],od[r['j']])); arrays=np.load(E/s/f'{k:03d}.npz')
            for arm,T in poses.items():
                assert np.max(np.abs(T-np.array(row[arm]['T_rel'])))<1e-8; q=(T[:3,:3]@b.T).T+T[:3,3]; x=nearest(q,a); y=nearest(a,q); d=np.r_[x,y]
                for direction,values in [('ba',x),('ab',y)]:
                    delta=float(np.max(np.abs(values-arrays[arm+'_'+direction]))); maxdelta=max(maxdelta,delta); assert delta<1e-8; distancecount+=len(values)
                v.close(float((d<1).mean()),row[arm]['overlap'],1e-9); v.close(float(d.mean()),row[arm]['mean_m'],1e-8)
            g,o=poses['GT'],poses['odom']; v.close(float(np.linalg.norm(g[:3,3]-o[:3,3])),row['agreement']['translation_m'],1e-8); v.close(float(np.degrees(np.arccos(np.clip((np.sum(g[:3,:3]*o[:3,:3])-1)/2,-1,1)))),row['agreement']['rotation_deg'],1e-7); totalrows+=1
        rr=result['rows'][s]; actual=dict(n=len(rr),median_abs_mean_difference_m=float(np.median([abs(r['GT']['mean_m']-r['odom']['mean_m']) for r in rr])),median_abs_overlap_difference=float(np.median([abs(r['GT']['overlap']-r['odom']['overlap']) for r in rr])),median_translation_m=float(np.median([r['agreement']['translation_m'] for r in rr])),median_rotation_deg=float(np.median([r['agreement']['rotation_deg'] for r in rr])),GT_median_mean_m=float(np.median([r['GT']['mean_m'] for r in rr])),odom_median_mean_m=float(np.median([r['odom']['mean_m'] for r in rr])))
        assert actual==result['summary'][s]
        for r,row in zip(read(OLD/'input-bank/attempts.json')[s],result['cross_visit'][s]):
            truth=np.linalg.solve(gt[r['i']],gt[r['j']]); error=truth[:3,3]-np.array(r['T_rel'])[:3,3]; norm=float(np.linalg.norm(error))
            assert row['attempt_id']==r['attempt_id']; assert np.max(np.abs(error-row['error_xyz_in_i_lidar_m']))<1e-8; v.close(norm,row['translation_norm_m'],1e-8); v.close(abs(float(error[2]))/max(norm,1e-12),row['z_fraction'],1e-8)
        print('independent temporal controls validated',s,len(rr),flush=True)
    assert endpoints==98 and totalrows==len(rows) and distancecount==totalrows*16000
    r=result['summary']['09']; gate=dict(mean=r['median_abs_mean_difference_m']<=.1,overlap=r['median_abs_overlap_difference']<=.05,translation=r['median_translation_m']<=.2,rotation=r['median_rotation_deg']<=1)
    decision='LOCAL_09_CONSISTENT_CROSS_VISIT_DISCREPANCY' if all(gate.values()) else 'LOCAL_09_DISCREPANCY_REQUIRES_FOLLOWUP'; assert gate==result['local_09_gate'] and decision==result['decision']; fraction=float(np.median([r['z_fraction'] for r in result['cross_visit']['09']])); assert fraction==result['cross_09_median_z_fraction'] and (fraction>=.8)==result['cross_09_z_dominant']
    wall=read(I/'execution.json')['wall_s']+result['wall_s']+time.monotonic()-t; peak=max(read(I/'execution.json')['peak_rss_gib'],result['peak_rss_gib'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20); size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file()); assert wall<900 and peak<2 and size<100000000
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    save(B/'validation.json',dict(passed=True,decision=decision,utc=v.now(),scans=scans,matched_prior_endpoints=endpoints,local_controls=totalrows,directed_distances=distancecount,max_distance_delta=maxdelta,independent_checks=['freeze/stage/seal','all clouds and 98 prior endpoints','full absolute file/index/time chain','independent calibration/relative poses','every brute-force NN distance','all metrics/component errors/aggregates/gates','resources and final integrity'],total_wall_s=wall,validator_wall_s=time.monotonic()-t,peak_rss_gib=peak,artifact_bytes_before_report=size))
    (B/'STATUS.json').write_text(__import__('json').dumps(dict(stage='VALIDATED',utc=v.now(),decision=decision,report='pending'),indent=2)+'\n'); print('validated',decision,flush=True)
if __name__=='__main__': main()
