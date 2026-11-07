"""LC0 prospective GT-separated exposure and placement diagnostic."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.metadata, json, resource, sys, time, traceback
import numpy as np

MAIN=Path(__file__).resolve().parents[2]; SLAM=MAIN.parent/'RAP-SLAM'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
BASE=MAIN/'docs/maintenance/2026-10-07/retrieval-placement-audit-01'
BANK=BASE/'bank'; EV=BASE/'evaluation'
SEQS={'00':4541,'05':2761,'06':1101,'07':1101,'09':1591,'10':1201}
GROUPS={'development':['00','05','06'],'transfer_exposed':['07','09','10']}
ARMS=['N','C','P','H']
sys.path[:0]=[str(SLAM),str(SLAM/'scripts')]
import retrieval_exposure as alg

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def utc(): return datetime.now(timezone.utc).isoformat()
def src(s): return MAIN/f"docs/maintenance/{'2026-09-26/e0-frontend-01' if s in GROUPS['development'] else '2026-09-27/e0-heldout-01'}/full-{s}-A"
def poses(p):
    x=np.loadtxt(p).reshape(-1,3,4); o=np.tile(np.eye(4),(len(x),1,1)); o[:,:3]=x; return o
def cap(start):
    assert time.perf_counter()-start<=3600
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=500*2**20
def attempts(s):
    out=[]
    with (src(s)/'verification_measurements.jsonl').open() as f:
        for line in f:
            if '"event": "candidate_started"' in line:
                d=json.loads(line); out.append({k:d[k] for k in ['i','j','attempt_id']})
    return out

def freeze():
    start=time.perf_counter()
    files=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_retrieval_placement_audit.py'),Path(__file__).with_name('validate_dense_propagation.py'),SLAM/'scripts/retrieval_exposure.py']
    files += [SLAM/p for p in ['rap_slam/scan_context.py','rap_slam/loop_closure.py','rap_slam/real_dataset.py','rap_slam/pose_graph.py','rap_slam/trajectory_protocol.py','rap_slam/evaluate.py','scripts/run_pipeline.py','scripts/eval_paper_metrics.py']]
    parents={}
    for folder in ['2026-09-26/e0-frontend-01','2026-09-27/e0-heldout-01']:
        p=MAIN/'docs/maintenance'/folder/'freeze.json'; files.append(p); parents.update(read(p)['inputs'])
    old=MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01'
    files += [old/n for n in ['freeze.json','bank_seal.json','validation.json','results.json']]
    oldfiles=read(old/'freeze.json')['files']; raw=[]
    for s,n in SEQS.items():
        files += [src(s)/p for p in ['odom_poses.txt','optimized_poses.txt','keyframes.json','source_frames.json','run_manifest.json','verification_measurements.jsonl','accepted_loops.json']]
        files += [DATA/'poses'/f'{s}.txt',DATA/'sequences'/s/'calib.txt']
        meta=read(src(s)/'source_frames.json'); assert meta['source_frame_ids']==list(range(n))
        c=read(src(s)/'run_manifest.json')['config']
        for k,v in dict(loop_dist=15.,loop_sep=200,max_candidates=12,loop_method='both',sc_dist_thresh=.25,sc_max_radius=80.,sc_rings=20,sc_sectors=60,sc_shortlist=10,apply_kitti_205=True).items(): assert c[k]==v,(s,k)
        for k in read(src(s)/'keyframes.json'): raw.append(Path(meta['scan_files'][k]))
    hashes={}
    for p in dict.fromkeys(files+raw):
        h=sha(p); hashes[str(p)]=h
        if p in raw: assert h==parents[str(p)],p
        if str(p) in oldfiles: assert h==oldfiles[str(p)],p
    assert len(raw)==1800
    save(BASE/'freeze.json',dict(utc=utc(),files=hashes,raw_files=[str(p) for p in raw],packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','gtsam','evo']},sequences=SEQS,wall_s=time.perf_counter()-start))
    (BASE/'INCOMPLETE').write_text('LC0 awaiting independent bank and metric validation\n')
    cap(start); print('LC0 frozen',len(hashes),'identities,1800 raw scans',flush=True)

def verify(include_raw=True):
    f=read(BASE/'freeze.json'); raw=set(f['raw_files'])
    for p,h in f['files'].items():
        if include_raw or p not in raw: assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in f['packages']}
def seal_verify():
    verify(); f=read(BASE/'bank_seal.json')
    assert set(f['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in f['files'].items(): assert sha(BANK/p)==h,p
def graph(odom,kf,edges):
    from rap_slam.pose_graph import optimize_pose_graph,propagate_to_full_trajectory
    opt=optimize_pose_graph(list(odom),list(kf),edges)
    return np.asarray(propagate_to_full_trajectory(list(odom),list(kf),opt)),np.array([opt[k] for k in kf])
def fixture():
    from rap_slam.scan_context import make_scan_context,make_ring_key,sc_distance
    p=np.array([[4.,0,-1.5],[4.,0,1.],[-4.,0,-1.],[-4.,-0.,2.],[80.,0,3.],[81.,0,10.],[0.,0,10.]])
    z=np.zeros((20,60),np.float32); z[0,29]=3.; z[0,59]=1.; z[0,0]=4.; z[19,29]=5.
    got=make_scan_context(p); assert np.array_equal(got,z)
    empty=make_scan_context(np.empty((0,3))); assert sc_distance(empty,empty)==(0.,0)
    np.savez(BANK/'fixture.npz',points=p,descriptor=got,ring_key=make_ring_key(got),empty=empty)

def bank():
    start=time.perf_counter(); started=utc(); verify(); BANK.mkdir(); fixture(); counts={}
    from rap_slam.scan_context import find_candidates_sc
    from rap_slam.loop_closure import find_candidates,merge_candidates
    for s,n in SEQS.items():
        root=BANK/s; root.mkdir(); kf=read(src(s)/'keyframes.json'); odom=poses(src(s)/'odom_poses.txt'); meta=read(src(s)/'source_frames.json')
        sc=[]; rk=[]; points=[]
        for a,k in enumerate(kf):
            d,r,c=alg.descriptor(meta['scan_files'][k]); sc.append(d); rk.append(r); points.append(c)
            if (a+1)%100==0: print('LC0 descriptors',s,a+1,'/',len(kf),flush=True)
            cap(start)
        sc=np.asarray(sc); rk=np.asarray(rk); np.savez(root/'descriptors.npz',sc=sc,ring_key=rk,point_counts=points,keyframes=kf)
        ex=alg.exposure(kf,odom,sc,rk); np.savez(root/'exposure.npz',**ex)
        d={k:{'sc':sc[a],'ring_key':rk[a]} for a,k in enumerate(kf)}
        pc=find_candidates(list(odom),kf,15.,200,12); cc=find_candidates_sc(d,kf,200,.25,10,12)
        final=merge_candidates(pc,cc,12)
        for key,pairs in [('proximity_cap',pc),('sc_cap',cc),('final',final)]:
            assert pairs==[(int(ex['i'][t]),int(ex['j'][t])) for t in ex[key]],(s,key)
        original=attempts(s); assert final==[(e['i'],e['j']) for e in original],(s,final,original)
        save(root/'attempts.json',original); np.save(root/'odom.npy',odom)
        edges=[{k:e[k] for k in ['i','j','T_rel','mean_dist','overlap','measurement_id']} for e in read(src(s)/'accepted_loops.json')]
        save(root/'native_edges.json',edges); full,keys=graph(odom,kf,edges)
        assert np.max(abs(full-poses(src(s)/'optimized_poses.txt')))<1e-5
        np.save(root/'N.npy',full); np.save(root/'N_keys.npy',keys)
        counts[s]={k:len(ex[k]) for k in ['i','proximity_precap','sc_precap','proximity_cap','sc_cap','union_precap','final']}
        counts[s].update(keyframes=len(kf),points=sum(points),accepted=len(edges))
        print('LC0 exposure complete',s,counts[s],flush=True); cap(start)
    assert sum(c['final'] for c in counts.values())==71 and sum(c['accepted'] for c in counts.values())==58
    verify(); save(BANK/'execution.json',dict(utc=utc(),started_utc=started,counts=counts,wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,gt_read=False))
    save(BASE/'bank_seal.json',dict(utc=utc(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(BANK)):sha(p) for p in BANK.rglob('*') if p.is_file()}))
    print('LC0 complete GT-free bank sealed',flush=True)

def coverage(ex,dist):
    stages={'eligible':np.arange(len(dist)),'sc_top10':np.flatnonzero(ex['ring_rank']<=10)}
    stages.update({k:ex[k] for k in ['sc_precap','sc_cap','proximity_precap','proximity_cap','union_precap','final']})
    out={}
    for k,ids in stages.items():
        near=ids[dist[ids]<15.]; far=ids[dist[ids]>=15.]
        nq=set(ex['j'][near].tolist()); fq=set(ex['j'][far].tolist())
        out[k]=dict(pairs=len(ids),near_pairs=len(near),far_pairs=len(far),queries=len(set(ex['j'][ids].tolist())),near_queries=len(nq),mixed_queries=len(nq&fq))
    return out
def gates(rows,means):
    tests={}; signal={}
    for a in ['P','H']:
        safety={s:dict(ter=rows[s][a]['ter']<=rows[s]['N']['ter']+.01,ate=rows[s][a]['ate']<=1.05*rows[s]['N']['ate']) for s in SEQS}
        cohorts={g:dict(ter=m['N']['ter']-m[a]['ter']>=.01,ate=1-m[a]['ate']/m['N']['ate']>=.05,placement_ter=m[a]['ter']<m['C']['ter'],placement_ate=m[a]['ate']<m['C']['ate']) for g,m in means.items()}
        signal[a]=any(all(c.values()) for c in cohorts.values()) and all(all(v.values()) for v in safety.values())
        tests[a]=dict(cohorts=cohorts,safety=safety,actionable=signal[a])
    decision='NATIVE_PRECAP_PLACEMENT_OPPORTUNITY' if signal['P'] else ('STRUCTURAL_ONLY_PLACEMENT_OPPORTUNITY' if signal['H'] else 'NO_FIXED_BUDGET_PLACEMENT_SIGNAL')
    return dict(tests=tests,decision=decision)

def evaluate():
    start=time.perf_counter(); seal_verify(); assert read(BASE/'bank_validation.json')['passed']
    assert sha(BASE/'bank_validation.json')==read(BASE/'bank_validation_seal.json')['validation_sha256']
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    gt_start=utc(); EV.mkdir(); rows={}; cov={}; selection={}; old=read(MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01/results.json')
    for s,n in SEQS.items():
        root=EV/s; root.mkdir(); ex=dict(np.load(BANK/s/'exposure.npz',allow_pickle=False)); kf=np.load(BANK/s/'descriptors.npz')['keyframes']; odom=np.load(BANK/s/'odom.npy')
        calib=DATA/'sequences'/s/'calib.txt'; gt=np.asarray(load_gt_poses(str(DATA/'poses'/f'{s}.txt'),str(calib),apply_calib=True)); tr=_read_calib_transform(str(calib)); ti=np.linalg.inv(tr)
        dist=np.linalg.norm(gt[ex['i'],:3,3]-gt[ex['j'],:3,3],axis=1); np.save(root/'gt_pair_distances.npy',dist)
        cov[s]=coverage(ex,dist); ids=np.arange(n).tolist(); rows[s]={}; selection[s]={}
        selected={'C':ex['final'][dist[ex['final']]<15.],'P':alg.distributed(ex['union_precap'],ex['i'],ex['j'],dist),'H':alg.distributed(np.arange(len(dist)),ex['i'],ex['j'],dist)}
        for a in ARMS:
            if a=='N': est=np.load(BANK/s/'N.npy')
            else:
                edges=[dict(i=int(ex['i'][t]),j=int(ex['j'][t]),T_rel=(np.linalg.inv(gt[ex['i'][t]])@gt[ex['j'][t]]).tolist(),mean_dist=1.,overlap=1.) for t in selected[a]]
                assert len(edges)<=12; save(root/f'{a}_edges.json',edges); est,keys=graph(odom,kf,edges); np.save(root/f'{a}.npy',est); np.save(root/f'{a}_keys.npy',keys)
                selection[s][a]=dict(pair_ids=selected[a].tolist(),pairs=[[e['i'],e['j']] for e in edges],count=len(edges))
            lidar=epm.evaluate_pair(list(gt),list(est),ids); camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@est@ti),ids)
            rows[s][a]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segment_count=camera['kitti_segments'])
            save(root/f'{a}_segments.json',camera['kitti_segment_records'])
            if a=='N': assert all(abs(rows[s][a][k]-old['rows'][s]['full'][k])<=1e-5 for k in rows[s][a])
        print('LC0 evaluated',s,rows[s],flush=True); cap(start)
    means={g:{a:{k:float(np.mean([rows[s][a][k] for s in ss])) for k in ['ate','ter','rer']} for a in ARMS} for g,ss in GROUPS.items()}
    save(EV/'coverage.json',cov); save(EV/'selection.json',selection)
    save(BASE/'results.json',dict(utc=utc(),gt_read_started_utc=gt_start,bank_seal_sha256=sha(BASE/'bank_seal.json'),bank_validation_seal_sha256=sha(BASE/'bank_validation_seal.json'),rows=rows,cohort_means=means,gate=gates(rows,means),wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    seal_verify(); save(BASE/'evaluation_seal.json',dict(utc=utc(),results_sha256=sha(BASE/'results.json'),files={str(p.relative_to(EV)):sha(p) for p in EV.rglob('*') if p.is_file()}))
    print('LC0 decision',read(BASE/'results.json')['gate']['decision'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('stage',choices=['freeze','bank','evaluate']); a=p.parse_args()
    try: globals()[a.stage]()
    except Exception as e:
        path=BASE/f'FAILURE_{a.stage}.json'
        if not path.exists(): save(path,dict(error=repr(e),traceback=traceback.format_exc(),utc=utc()))
        raise
