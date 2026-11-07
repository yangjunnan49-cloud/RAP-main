"""Independent all-distance brute-force checks; no diagnostic runner import."""
import time,resource
import numpy as np
from scipy.spatial.distance import cdist
import validate_dense_propagation as v
B=v.MAIN/'docs/maintenance/2026-10-05/online-geometry-consistency-01'; OLD=B.parent/'online-geotransformer-01'; E=B/'evaluation-01'
read,sha,save=v.read,v.digest,v.write
def nearest(x,y):
    return np.concatenate([cdist(x[k:k+128],y).min(axis=1) for k in range(0,len(x),128)])
def main():
    t=time.monotonic(); freeze=read(B/'freeze.json'); result=read(B/'results.json'); seal=read(B/'distance_seal.json')
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    assert freeze['utc']<result['started_utc']<result['completed_utc']<seal['utc']
    assert seal['files']=={str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()}
    n=totaldist=0; maxdelta=0.; summary={}; raw=read(OLD/'input-bank/attempts.json')
    for s in v.SEQS:
        tr=v.calibration(s); gt=np.linalg.inv(tr)@v.load(v.DATA/'poses'/f'{s}.txt')@tr; od=v.load(v.src(s)/'odom_poses.txt'); pred=read(OLD/'prediction-bank'/f'{s}.json'); rr=result['rows'][s]
        for k,(r,g,row) in enumerate(zip(raw[s],pred,rr)):
            assert row['attempt_id']==r['attempt_id']==g['attempt_id'] and row['native_accepted']==(r['status']=='accepted'); n+=1
            a=np.load(OLD/'input-bank'/s/f"{r['i']:06d}.npy").astype('float64'); b=np.load(OLD/'input-bank'/s/f"{r['j']:06d}.npy").astype('float64'); arrays=np.load(E/s/f'{k:02d}.npz')
            poses=dict(RAP=np.array(r['T_rel']),Geo=np.array(g['T_rel']),GT=np.linalg.solve(gt[r['i']],gt[r['j']]),odom=np.linalg.solve(od[r['i']],od[r['j']]))
            for arm,T in poses.items():
                q=(T[:3,:3]@b.T).T+T[:3,3]; ba=nearest(q,a); ab=nearest(a,q); d=np.r_[ba,ab]
                for name,values in [('ba',ba),('ab',ab)]:
                    delta=float(np.max(np.abs(values-arrays[arm+'_'+name]))); maxdelta=max(maxdelta,delta); assert delta<1e-8; totaldist+=len(values)
                metrics=dict(overlap=float((d<1).mean()),mean_m=float(d.mean()),median_m=float(np.quantile(d,.5)),p95_m=float(np.quantile(d,.95)))
                for key,x in metrics.items(): v.close(x,row[arm][key],1e-8)
            rap,geo=poses['RAP'],poses['Geo']; translation=float(np.sqrt(np.sum((rap[:3,3]-geo[:3,3])**2))); rotation=float(np.arccos(np.clip((np.sum(rap[:3,:3]*geo[:3,:3])-1)/2,-1,1))*180/np.pi)
            v.close(translation,row['agreement']['translation_m'],1e-8); v.close(rotation,row['agreement']['rotation_deg'],1e-8)
        summary[s]={}
        for subset,selection in [('all',rr),('native_accepted',[r for r in rr if r['native_accepted']])]:
            actual=dict(n=len(selection))
            if selection:
                actual.update(median_GT_minus_RAP_mean_m=float(np.median([r['GT']['mean_m']-r['RAP']['mean_m'] for r in selection])),median_RAP_minus_GT_overlap=float(np.median([r['RAP']['overlap']-r['GT']['overlap'] for r in selection])),median_RAP_Geo_translation_m=float(np.median([r['agreement']['translation_m'] for r in selection])),median_RAP_Geo_rotation_deg=float(np.median([r['agreement']['rotation_deg'] for r in selection])),pose_medians={arm:{key:float(np.median([r[arm][key] for r in selection])) for key in ['overlap','mean_m','median_m','p95_m']} for arm in poses})
            assert actual==result['summary'][s][subset]; summary[s][subset]=actual
        print('brute-force validated geometry',s,flush=True)
    assert n==71 and totaldist==2272000
    r=summary['09']['all']; decision='SHARED_09_GEOMETRY_LABEL_DISCREPANCY' if r['median_GT_minus_RAP_mean_m']>=.5 and r['median_RAP_minus_GT_overlap']>=.1 and r['median_RAP_Geo_translation_m']<=.5 and r['median_RAP_Geo_rotation_deg']<=2 else 'NO_SHARED_09_GEOMETRY_LABEL_SCREEN_SIGNAL'
    assert decision==result['decision']; size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file()); wall=result['wall_s']+time.monotonic()-t; peak=max(result['peak_rss_gib'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    assert wall<300 and peak<2 and size<100000000
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    save(B/'validation.json',dict(passed=True,decision=decision,pairs=n,directed_distances=totaldist,max_distance_delta=maxdelta,total_wall_s=wall,validator_wall_s=time.monotonic()-t,peak_rss_gib=peak,artifact_bytes_before_report=size,utc=v.now()))
    print('validated',decision,totaldist,'NN distances',flush=True)
if __name__=='__main__': main()
