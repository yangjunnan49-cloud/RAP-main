"""Separately frozen evaluator-only all-online scan/pose geometry diagnostic."""
import sys,time,resource
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import system_opportunity as h
BASE=h.MAIN/'docs/maintenance/2026-10-05/online-geometry-consistency-01'; OLD=BASE.parent/'online-geotransformer-01'; OUT=BASE/'evaluation-01'
read,sha,save=h.read,h.sha,h.save
def now(): return __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
def paths():
    p=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_online_geometry_consistency.py'),Path(h.__file__),OLD/'input_seal.json',OLD/'bank_seal.json',OLD/'validation.json',OLD/'pair_outcomes.json',OLD/'results.json']
    for folder in ['input-bank','prediction-bank']: p += [x for x in (OLD/folder).rglob('*') if x.is_file()]
    for s in h.SEQS: p += [h.DATA/'poses'/f'{s}.txt',h.DATA/'sequences'/s/'calib.txt',h.source(s)/'odom_poses.txt']
    return sorted(set(p))
def verify(): assert read(BASE/'freeze.json')['files']=={str(p):sha(p) for p in paths()}
def freeze():
    assert read(OLD/'validation.json')['passed'] and not OUT.exists()
    for folder,name in [('input-bank','input_seal.json'),('prediction-bank','bank_seal.json')]:
        seal=read(OLD/name); assert seal['files']=={str(p.relative_to(OLD/folder)):sha(p) for p in (OLD/folder).rglob('*') if p.is_file()}
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in paths()})); print('geometry diagnostic frozen',len(paths()),flush=True)
def aggregate(rows):
    result={}
    for s,rr in rows.items():
        result[s]={}
        for subset,selected in [('all',rr),('native_accepted',[r for r in rr if r['native_accepted']])]:
            if not selected: result[s][subset]=dict(n=0); continue
            result[s][subset]=dict(n=len(selected),median_GT_minus_RAP_mean_m=float(np.median([r['GT']['mean_m']-r['RAP']['mean_m'] for r in selected])),median_RAP_minus_GT_overlap=float(np.median([r['RAP']['overlap']-r['GT']['overlap'] for r in selected])),median_RAP_Geo_translation_m=float(np.median([r['agreement']['translation_m'] for r in selected])),median_RAP_Geo_rotation_deg=float(np.median([r['agreement']['rotation_deg'] for r in selected])),pose_medians={a:{k:float(np.median([r[a][k] for r in selected])) for k in ['overlap','mean_m','median_m','p95_m']} for a in ['RAP','Geo','GT','odom']})
    return result
def evaluate():
    verify(); OUT.mkdir(); (BASE/'INCOMPLETE').write_text('Geometry diagnostic pending independent validation\n'); t=time.monotonic(); start=now(); rows={}
    native=read(OLD/'input-bank/attempts.json')
    for s,n in h.SEQS.items():
        cal=(h.DATA/'sequences'/s/'calib.txt').read_text(); line=next(x for x in cal.splitlines() if x.startswith('Tr:')); tr=np.eye(4); tr[:3]=np.array(line.split(':')[1].split(),dtype='float64').reshape(3,4)
        gt=np.linalg.inv(tr)@h.poses(h.DATA/'poses'/f'{s}.txt',n)@tr; o=h.poses(h.source(s)/'odom_poses.txt',n); preds=read(OLD/'prediction-bank'/f'{s}.json'); rows[s]=[]; dest=OUT/s; dest.mkdir()
        for k,(r,g) in enumerate(zip(native[s],preds)):
            assert r['attempt_id']==g['attempt_id']; a=np.load(OLD/'input-bank'/s/f"{r['i']:06d}.npy"); b=np.load(OLD/'input-bank'/s/f"{r['j']:06d}.npy")
            rap,geo=np.array(r['T_rel']),np.array(g['T_rel']); poses=dict(RAP=rap,Geo=geo,GT=np.linalg.inv(gt[r['i']])@gt[r['j']],odom=np.linalg.inv(o[r['i']])@o[r['j']]); vectors={}; row=dict(attempt_id=r['attempt_id'],i=r['i'],j=r['j'],native_accepted=r['status']=='accepted')
            for name,T in poses.items():
                q=b@T[:3,:3].T+T[:3,3]; x=cKDTree(a).query(q)[0]; y=cKDTree(q).query(a)[0]; d=np.concatenate([x,y]); vectors[name+'_ba']=x; vectors[name+'_ab']=y
                row[name]=dict(overlap=float(.5*((x<1).mean()+(y<1).mean())),mean_m=float(.5*(x.mean()+y.mean())),median_m=float(np.median(d)),p95_m=float(np.percentile(d,95)))
            row['agreement']=dict(translation_m=float(np.linalg.norm(rap[:3,3]-geo[:3,3])),rotation_deg=float(np.degrees(np.arccos(np.clip((np.trace(rap[:3,:3].T@geo[:3,:3])-1)/2,-1,1)))))
            np.savez(dest/f'{k:02d}.npz',**vectors); rows[s].append(row)
        print('geometry checked',s,len(rows[s]),flush=True)
    summary=aggregate(rows); r=summary['09']['all']; signal=r['median_GT_minus_RAP_mean_m']>=.5 and r['median_RAP_minus_GT_overlap']>=.1 and r['median_RAP_Geo_translation_m']<=.5 and r['median_RAP_Geo_rotation_deg']<=2
    decision='SHARED_09_GEOMETRY_LABEL_DISCREPANCY' if signal else 'NO_SHARED_09_GEOMETRY_LABEL_SCREEN_SIGNAL'
    save(BASE/'results.json',dict(started_utc=start,completed_utc=now(),rows=rows,summary=summary,decision=decision,wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    assert time.monotonic()-t<300 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20<2
    verify(); save(BASE/'distance_seal.json',dict(utc=now(),files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()})); print(decision,flush=True)
if __name__=='__main__': {'freeze':freeze,'evaluate':evaluate}[sys.argv[1]]()
