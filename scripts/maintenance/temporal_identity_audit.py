"""Prospective exact endpoint temporal audit, GT-free bank then evaluator."""
import sys,time,resource
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import system_opportunity as h
B=h.MAIN/'docs/maintenance/2026-10-05/temporal-identity-audit-01'; OLD=B.parent/'online-geotransformer-01'; GEO=B.parent/'online-geometry-consistency-01'; BANK=B/'input-bank'; EVAL=B/'evaluation-01'
read,sha,save=h.read,h.sha,h.save
def now(): return __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
def state(stage,**kw): (B/'STATUS.json').write_text(__import__('json').dumps(dict(stage=stage,utc=now(),**kw),indent=2)+'\n')
def census():
    endpoints=read(OLD/'input-bank/scan_census.json'); rows=[]
    for c in endpoints:
        for offset in [-10,10]:
            j=c['frame']+offset
            if 0<=j<h.SEQS[c['seq']]: rows.append(dict(seq=c['seq'],i=c['frame'],j=j,offset=offset,causal=offset<0))
    return endpoints,rows
def raw(s,i): return h.DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def files():
    endpoints,rows=census(); p=[B/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_temporal_identity_audit.py'),Path(h.__file__),OLD/'input_seal.json',OLD/'input_validation.json',OLD/'bank_seal.json',OLD/'validation.json',GEO/'freeze.json',GEO/'distance_seal.json',GEO/'results.json',GEO/'validation.json',h.ROOT/'rap_slam/real_dataset.py',h.ROOT/'rap_slam/trajectory_protocol.py',h.ROOT/'rap_slam/rap_backend.py',h.ROOT/'rap_slam/rap_precision.py',h.ROOT/'scripts/run_pipeline.py']
    p += [x for x in (OLD/'input-bank').rglob('*') if x.is_file()]
    for s,n in h.SEQS.items():
        p += [h.DATA/'poses'/f'{s}.txt',h.DATA/'sequences'/s/'calib.txt',h.DATA/'sequences'/s/'times.txt',h.source(s)/'source_frames.json',h.source(s)/'odom_poses.txt']
        ids={r[k] for r in rows if r['seq']==s for k in ['i','j']}; p += [raw(s,i) for i in sorted(ids)]
    return sorted(set(p))
def verify(): assert read(B/'freeze.json')['files']=={str(p):sha(p) for p in files()}
def cap(t):
    assert time.monotonic()-t<900 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20<2
    assert sum(p.stat().st_size for p in B.rglob('*') if p.is_file())<100000000
def freeze():
    assert read(GEO/'validation.json')['passed'] and read(OLD/'validation.json')['passed'] and not BANK.exists()
    save(B/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in files()},endpoints=census()[0],controls=census()[1])); state('FROZEN'); print('frozen identity/temporal audit',len(files()),'files',len(census()[1]),'controls',flush=True)
def build():
    verify(); BANK.mkdir(); (B/'INCOMPLETE').write_text('Identity/temporal audit pending complete independent validation\n'); state('INPUT_RUNNING'); t=time.monotonic(); start=now(); identity={}
    from rap_slam.real_dataset import load_scans
    from rap_slam.rap_backend import RAPBackend
    backend=RAPBackend.__new__(RAPBackend); backend.feature_extractor=None; backend.voxel_size=.4; backend.max_points_per_scan=4000; backend.remove_outliers=True; backend.seed=42
    endpoints,rows=census()
    for s,n in h.SEQS.items():
        manifest=read(h.source(s)/'source_frames.json'); stamps=np.loadtxt(h.DATA/'sequences'/s/'times.txt'); actualids=sorted(int(p.stem) for p in raw(s,0).parent.glob('*.bin'))
        assert actualids==list(range(n))==manifest['source_frame_ids']
        assert manifest['scan_files']==[str(raw(s,i)) for i in range(n)] and manifest['pose_reference']=='lidar' and manifest['sequence']==s
        assert len(stamps)==n and np.all(np.diff(stamps)>0) and np.array_equal(stamps,np.array(manifest['timestamps']))
        dest=BANK/s; dest.mkdir(); needed=sorted({r[k] for r in rows if r['seq']==s for k in ['i','j']})
        for i in needed:
            points,_=load_scans(str(raw(s,i).parent),start=i,end=i,min_range=1.5,kitti205=True); points,_=backend.preprocess(points[0]); np.save(dest/f'{i:06d}.npy',points)
            old=OLD/'input-bank'/s/f'{i:06d}.npy'
            if old.exists(): assert np.array_equal(points,np.load(old)),(s,i)
        identity[s]=dict(n=n,scans=len(needed),min_dt_s=float(np.diff(stamps).min()),max_dt_s=float(np.diff(stamps).max()),median_dt_s=float(np.median(np.diff(stamps))),full_absolute_frame_path_and_timestamp_match=True)
        cap(t); print('identity/cloud bank',s,len(needed),flush=True)
    save(BANK/'controls.json',rows); save(BANK/'identity.json',identity); save(BANK/'provenance_limits.json',dict(raw_ox_ts_verified=False,sensor_trigger_archive_verified=False,scope='available local sequence manifests/times/calibration; no independent raw sensor trigger archive supplied'))
    save(BANK/'execution.json',dict(started_utc=start,wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)); verify(); cap(t)
    save(B/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(B/'freeze.json'),files={str(p.relative_to(BANK)):sha(p) for p in BANK.rglob('*') if p.is_file()})); state('BANK_SEALED')
def evaluate():
    verify(); seal=read(B/'bank_seal.json'); assert seal['files']=={str(p.relative_to(BANK)):sha(p) for p in BANK.rglob('*') if p.is_file()}
    EVAL.mkdir(); state('EVALUATING'); t=time.monotonic(); start=now(); results={}; cross={}; summary={}
    from rap_slam.real_dataset import load_gt_poses
    for s,n in h.SEQS.items():
        gt=np.asarray(load_gt_poses(str(h.DATA/'poses'/f'{s}.txt'),str(h.DATA/'sequences'/s/'calib.txt'),apply_calib=True)); od=h.poses(h.source(s)/'odom_poses.txt',n); results[s]=[]; dest=EVAL/s; dest.mkdir()
        local=[r for r in read(BANK/'controls.json') if r['seq']==s]
        for k,r in enumerate(local):
            a=np.load(BANK/s/f"{r['i']:06d}.npy"); b=np.load(BANK/s/f"{r['j']:06d}.npy"); poses=dict(GT=np.linalg.inv(gt[r['i']])@gt[r['j']],odom=np.linalg.inv(od[r['i']])@od[r['j']] ); row=dict(r); arrays={}
            for arm,T in poses.items():
                q=b@T[:3,:3].T+T[:3,3]; x=cKDTree(a).query(q)[0]; y=cKDTree(q).query(a)[0]; arrays[arm+'_ba']=x; arrays[arm+'_ab']=y
                row[arm]=dict(overlap=float(.5*((x<1).mean()+(y<1).mean())),mean_m=float(.5*(x.mean()+y.mean())),T_rel=T.tolist())
            g,o=poses['GT'],poses['odom']; row['agreement']=dict(translation_m=float(np.linalg.norm(g[:3,3]-o[:3,3])),rotation_deg=float(np.degrees(np.arccos(np.clip((np.trace(g[:3,:3].T@o[:3,:3])-1)/2,-1,1)))))
            np.savez(dest/f'{k:03d}.npz',**arrays); results[s].append(row)
        rr=results[s]; summary[s]=dict(n=len(rr),median_abs_mean_difference_m=float(np.median([abs(r['GT']['mean_m']-r['odom']['mean_m']) for r in rr])),median_abs_overlap_difference=float(np.median([abs(r['GT']['overlap']-r['odom']['overlap']) for r in rr])),median_translation_m=float(np.median([r['agreement']['translation_m'] for r in rr])),median_rotation_deg=float(np.median([r['agreement']['rotation_deg'] for r in rr])),GT_median_mean_m=float(np.median([r['GT']['mean_m'] for r in rr])),odom_median_mean_m=float(np.median([r['odom']['mean_m'] for r in rr])))
        cross[s]=[]
        for r in read(OLD/'input-bank/attempts.json')[s]:
            truth=np.linalg.inv(gt[r['i']])@gt[r['j']]; error=truth[:3,3]-np.array(r['T_rel'])[:3,3]; norm=float(np.linalg.norm(error)); cross[s].append(dict(attempt_id=r['attempt_id'],error_xyz_in_i_lidar_m=error.tolist(),translation_norm_m=norm,z_fraction=abs(float(error[2]))/max(norm,1e-12)))
        cap(t); print('local temporal geometry',s,len(rr),flush=True)
    r=summary['09']; gate=dict(mean=r['median_abs_mean_difference_m']<=.10,overlap=r['median_abs_overlap_difference']<=.05,translation=r['median_translation_m']<=.20,rotation=r['median_rotation_deg']<=1)
    decision='LOCAL_09_CONSISTENT_CROSS_VISIT_DISCREPANCY' if all(gate.values()) else 'LOCAL_09_DISCREPANCY_REQUIRES_FOLLOWUP'
    save(B/'results.json',dict(gt_read_started_utc=start,completed_utc=now(),bank_seal_sha256=sha(B/'bank_seal.json'),rows=results,cross_visit=cross,summary=summary,local_09_gate=gate,cross_09_median_z_fraction=float(np.median([r['z_fraction'] for r in cross['09']])),cross_09_z_dominant=bool(np.median([r['z_fraction'] for r in cross['09']])>=.8),decision=decision,wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)); verify(); state('EVALUATED',decision=decision); print(decision,flush=True)
if __name__=='__main__':
    try: {'freeze':freeze,'bank':build,'evaluate':evaluate}[sys.argv[1]]()
    except Exception as e: state('STOPPED',error=repr(e)); raise
