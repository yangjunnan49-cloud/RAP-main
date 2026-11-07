"""RAD1 staged driver. The real bank never parses evaluator GT or strata."""
from __future__ import annotations
import argparse, hashlib, json, os, resource, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent/'RAP-SLAM'
BASE = MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01/attempt-02'
F2 = MAIN/'docs/maintenance/2026-09-27/f2-structured-dev-01'
C1 = MAIN/'docs/maintenance/2026-09-28/c1-descriptor-information-01'
GT = {'00': MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy',
      '08': MAIN/'docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy'}
ARMS = ['R','P','D','Z']
sys.path.insert(0, str(SLAM/'scripts'))
import measurement_association_v2 as alg


def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def state(stage,**kw):
    (BASE/'STATUS.json').write_text(json.dumps(dict(stage='RAD1',status=stage,utc=now(),**kw),indent=2)+'\n')
def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
def cohort(): return [(s,r) for s in ('00','08') for r in read(F2/f'inputs_{s}.json')]
def check_cap(start,seconds):
    assert time.perf_counter()-start<=seconds,'wall cap'
    assert rss()<=4*2**30,'RSS cap'
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=300*2**20,'artifact cap'
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    return f


def freeze():
    import scipy,open3d
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    assert not (BASE/'freeze.json').exists()
    assert read(F2/'validation.json')['passed'] and read(C1/'validation.json')['passed']
    old=read(F2/'artifact_hashes.json'); cb={(r['sequence'],r['pair']):r['sha256'] for r in read(C1/'bank.json')}
    rows=cohort(); assert len(rows)==200 and all(sum(s==v for s,_ in rows)==100 for v in ('00','08'))
    files=[BASE/'PROTOCOL.md',BASE/'measurement_association_source.py',Path(__file__),
        MAIN/'scripts/maintenance/validate_raw_association_decoder_v2.py',SLAM/'scripts/measurement_association_v2.py',SLAM/'scripts/structured_motion_dev.py',
        SLAM/'rap_slam/rap_backend.py',SLAM/'rap_slam/real_dataset.py',
        F2/'artifact_hashes.json',F2/'validation.json',C1/'bank.json',C1/'validation.json',Path(sys.executable)]
    manifest=[]
    for s in ('00','08'):
        files += [F2/f'inputs_{s}.json',F2/s/'records.json',F2/s/'gates.json',
                  F2/s/'evaluator_only_decisions.json',GT[s]]
    native_wall=0.
    for s,row in rows:
        key=row['key']; folder=F2/s/key
        for name in ['inputs.npz']+[f'N{k}.npz' for k in range(4)]:
            p=folder/name;assert sha(p)==old[f'{s}/{key}/{name}'];files.append(p)
        p=C1/s/f'{key}.npz'; assert sha(p)==cb[s,key];files.append(p)
        for k in (0,3):
            p=Path(row['scans'][k]['path']);assert sha(p)==row['scans'][k]['sha256'];files.append(p)
        manifest.append(dict(seq=s,pair=key,source_i=row['source_i'],source_j=row['source_j'],
                             anchor_paths=[row['scans'][k]['path'] for k in (0,3)]))
    # GT-free generation timing metadata only; no evaluation outcomes here.
    for s in ('00','08'):
        records=read(F2/s/'records.json');selected=[r for r in records if r['arm']=='N']
        assert len(selected)==400
        native_wall+=sum(r['wall_s'] for r in selected)
    save(BASE/'manifest.json',dict(rows=manifest,counts=[2000,1000,1000,2000,1000,1000],
         input_whitelist=['points','cond','centers','scale','counts'],native_whitelist=['end_point_trajectory','T','rigidity_steps'],
         features_whitelist=['features'],native_historical_generation_wall_s=native_wall))
    files += [BASE/'manifest.json',BASE.parent/'freeze.json',BASE.parent/'bank_seal.json',BASE.parent/'FAILURE_validation_bank.json',BASE.parent/'AMENDMENT_01.md']
    assert sha(BASE/'measurement_association_source.py')==sha(SLAM/'scripts/measurement_association_v2.py')
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in sorted(set(files))},
         runtime=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,open3d=open3d.__version__,
                      executable=str(Path(sys.executable))),gt_parsed=False,rows=manifest))
    (BASE/'INCOMPLETE').write_text('RAD1 validation pending\n')
    state('FROZEN',identities=len(set(files)),pairs=200,gt_read=False,new_inference=False)
    print('RAD1 freeze',len(set(files)),'identities; native cost',round(native_wall,3),flush=True)


def synthetic():
    verify();start=time.perf_counter();dest=BASE/'synthetic';dest.mkdir()
    rng=np.random.Generator(np.random.PCG64(2026100701));entries=[]
    for k in range(20):
        x=rng.normal(size=(96,3))*[13,9,4]
        T=np.eye(4);T[:3,:3]=Rotation.from_rotvec(rng.normal(size=3)*.3).as_matrix();T[:3,3]=rng.normal(size=3)*3
        y=alg.apply(np.linalg.inv(T),x)
        G=np.eye(4);G[:3,:3]=Rotation.from_rotvec(rng.normal(size=3)).as_matrix();G[:3,3]=rng.normal(size=3)*10
        qx,qy=alg.apply(G,x),alg.apply(G,alg.apply(T,y))
        variants=[('rigid',x,y,qx,qy,np.arange(96),np.arange(96))]
        H=np.eye(4);H[:3,:3]=Rotation.from_rotvec([.13,-.2,.07]).as_matrix();H[:3,3]=[7,-4,2]
        variants.append(('gauge',x,y,alg.apply(H,qx),alg.apply(H,qy),np.arange(96),np.arange(96)))
        px,py=rng.permutation(96),rng.permutation(96)
        variants.append(('rows',x[px],y[py],qx[px],qy[py],px,py))
        variants.append(('scale_roundtrip',x,y,(qx/37.7)*37.7,(qy/37.7)*37.7,np.arange(96),np.arange(96)))
        A,B=alg.fit(x,qx),alg.fit(y,qy)
        variants.append(('projected',x,y,alg.apply(A,x),alg.apply(B,y),np.arange(96),np.arange(96)))
        reference=None
        for tag,a,b,c,d,ix,iy in variants:
            pairs,dist=alg.associate(c,d,ix,iy);out,info=alg.solve(a,b,pairs,dist,np.eye(4),ix,iy)
            assert not info['fallback'] and np.max(np.abs(out-T))<1e-9
            canonical=sorted((int(ix[i]),int(iy[j])) for i,j in pairs)
            if reference is None:reference=canonical
            assert canonical==reference
            p=dest/f'{k:02d}-{tag}.npz'
            np.savez_compressed(p,x=a,y=b,qx=c,qy=d,ids_x=ix,ids_y=iy,pairs=pairs,distances=dist,T=out,expected=T)
            entries.append(dict(file=str(p),sha256=sha(p),case=tag))
    line=np.c_[np.arange(8),np.zeros((8,2))]
    assert alg.fit(line,line) is None and alg.fit(line[:2],line[:2]) is None
    triangle=np.array([[0.,0,0],[1,0,0],[0,1,0]])
    crossed_source=np.repeat(triangle,3,axis=0);crossed_target=np.tile(triangle,(3,1))
    assert alg.fit(crossed_source,crossed_target) is None
    duplicate=np.array([[0.,0,0],[0,0,0],[1,0,0],[0,1,0]])
    ids=np.array([3,1,2,0]);p,d=alg.associate(duplicate,duplicate,ids,ids)
    assert np.array_equal(p,alg.associate(duplicate,duplicate,ids,ids)[0])
    irregular=rng.normal(size=(160,3))*[7,9,4];wrong=np.eye(4);wrong[0,3]=2
    true_score=alg.geometry(irregular,irregular,np.eye(4));wrong_score=alg.geometry(irregular,irregular,wrong)
    assert true_score[1]==0 and wrong_score[1]>.1
    motif=np.array([[.1,.2,.3],[.3,.9,.1],[.7,.1,.8],[.9,.5,.6]])
    periodic=np.concatenate([motif+[2*i,0,0] for i in range(12)])
    a=periodic[4:];b=periodic[:-4];alternate=alg.fit(b,a)
    assert np.max(np.abs(alternate-wrong))<1e-10 and np.max(np.linalg.norm(alg.apply(wrong,b)-a,axis=1))<1e-12
    periodic_score=alg.geometry(periodic,periodic,wrong);assert periodic_score[0]>=.7 and periodic_score[1]<=2.5
    p=dest/'counterexamples.npz';np.savez_compressed(p,line=line,crossed_source=crossed_source,crossed_target=crossed_target,duplicate=duplicate,ids=ids,tie_pairs=alg.associate(duplicate,duplicate,ids,ids)[0],
        irregular=irregular,wrong=wrong,true_score=true_score,wrong_score=wrong_score,periodic=periodic,
        periodic_target=a,periodic_source=b,alternate=alternate,periodic_score=periodic_score)
    entries.append(dict(file=str(p),sha256=sha(p),case='degenerate_ties_wrong_periodic'))
    verify();check_cap(start,300)
    save(BASE/'synthetic_seal.json',dict(utc=now(),files=entries,wall_s=time.perf_counter()-start,peak_rss_bytes=rss()))
    state('SYNTHETIC_SEALED',gt_read=False,new_inference=False)
    print('RAD1 synthetic sealed',len(entries),'files',flush=True)


def load_pair(s,row):
    folder=F2/s/row['key']
    with np.load(folder/'inputs.npz',allow_pickle=False) as z:
        assert z['counts'].tolist()==[2000,1000,1000,2000,1000,1000]
        parts=np.split(z['points'].astype(float),np.cumsum(z['counts'])[:-1]);x,y=parts[0],parts[3];scale=float(z['scale'])
        assert np.max(np.abs(z['cond']*scale+np.repeat(z['centers'],z['counts'],axis=0)-z['points']))<2e-5
    with np.load(C1/s/f"{row['key']}.npz",allow_pickle=False) as z:
        features=np.split(z['features'].astype(float),[2000,3000,4000,6000,7000]);fx,fy=features[0],features[3]
    raw=[];native=[];rigidity=[]
    for k in range(4):
        with np.load(folder/f'N{k}.npz',allow_pickle=False) as z:
            q=np.split(z['end_point_trajectory'][-1].astype(float)*scale,[2000,3000,4000,6000,7000])
            raw.append([q[0],q[3]]);native.append(z['T'].copy());rigidity.append(float(np.mean(z['rigidity_steps'])))
    return x,y,fx,fy,np.asarray(raw),np.asarray(native),np.asarray(rigidity)


def gate_clouds(row):
    sys.path.insert(0,str(SLAM))
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.real_dataset import kitti_vertical_correction
    g=RAPBackend.__new__(RAPBackend);g.voxel_size=.4;g.remove_outliers=True;g.max_points_per_scan=4000;g.seed=42;g.feature_extractor=None
    full=[];fit_points=[]
    for k in (0,3):
        raw=np.fromfile(row['scans'][k]['path'],np.float32).reshape(-1,4)[:,:3]
        raw=raw[np.linalg.norm(raw,axis=1)>=1.5]
        corrected=np.ascontiguousarray(kitti_vertical_correction(raw),dtype=np.float32)
        full.append(g.preprocess(corrected)[0]);fit_points.append(g.preprocess(corrected,max_points=2000)[0])
    return full,fit_points


def bank():
    verify();assert read(BASE/'synthetic_validation.json')['passed']
    start=time.perf_counter();state('BANK_RUNNING',gt_read=False,new_inference=False)
    dest=BASE/'bank';dest.mkdir();rows=[];arm_wall=np.zeros(4);common_wall=io_wall=0.;bridge=0.
    original_gates={s:read(F2/s/'gates.json') for s in ('00','08')}
    for index,(s,row) in enumerate(cohort()):
        active=row['key'];io=time.perf_counter();x,y,fx,fy,q,native,rig=load_pair(s,row);io_wall+=time.perf_counter()-io
        tick=time.perf_counter();full,reconstructed=gate_clouds(row)
        assert np.array_equal(reconstructed[0],x) and np.array_equal(reconstructed[1],y)
        held=[v[cKDTree(p).query(v,workers=1)[0]>1e-5] for v,p in zip(full,(x,y))]
        assert min(map(len,held))>=200
        ngate=np.asarray([alg.geometry(*full,T) for T in native]);nscore=np.asarray([alg.geometry(*held,T) for T in native])
        for k in range(4):
            saved=original_gates[s][active]['N'][str(k)]
            assert abs(ngate[k,0]-saved['overlap_ratio'])<1e-10 and abs(ngate[k,1]-saved['mean_dist'])<1e-8
        common_wall+=time.perf_counter()-tick
        Ts=np.zeros((4,4,4,4));pairs=np.full((4,4,512,2),-1,np.int64);distances=np.zeros((4,4,512));counts=np.zeros((4,4),np.int64)
        fallback=np.zeros((4,4),bool);proposals=np.zeros((4,4),np.int64);seed_ranks=np.zeros((4,4),np.int64)
        clique_masks=np.zeros((4,4,512),bool);refit_masks=np.zeros((4,4,3,512),bool);final_masks=np.zeros((4,4,512),bool)
        scores=np.zeros((4,4,2));gates=np.zeros((4,4,2));projected=np.zeros_like(q);wall=np.zeros(4)
        for ai,arm in enumerate(ARMS):
            tick=time.perf_counter()
            for k in range(4):
                if arm=='R':a,b=q[k]
                elif arm=='P':
                    A,B=alg.fit(x,q[k,0]),alg.fit(y,q[k,1]);assert A is not None and B is not None
                    bridge=max(bridge,float(np.max(np.abs(np.linalg.inv(A)@B-native[k]))))
                    projected[k]=[alg.apply(A,x),alg.apply(B,y)];a,b=projected[k]
                elif arm=='D':a,b=fx,fy
                else:
                    seed=int(hashlib.sha256(f'RAD1|{active}|{k}'.encode()).hexdigest()[:16],16)
                    rng=np.random.Generator(np.random.PCG64(seed));a=q[k,0,rng.permutation(len(x))];b=q[k,1,rng.permutation(len(y))]
                m,d=alg.associate(a,b);T,info=alg.solve(x,y,m,d,native[k]);n=len(m)
                Ts[ai,k]=T;pairs[ai,k,:n]=m;distances[ai,k,:n]=d;counts[ai,k]=n
                fallback[ai,k]=info['fallback'];proposals[ai,k]=info['proposals'];seed_ranks[ai,k]=info['seed_rank']
                clique_masks[ai,k,info['clique']]=True;refit_masks[ai,k,:,:n]=info['refits'];final_masks[ai,k,:n]=info['final_inliers']
                scores[ai,k]=alg.geometry(*held,T);gates[ai,k]=alg.geometry(*full,T)
            wall[ai]=time.perf_counter()-tick;arm_wall[ai]+=wall[ai]
        assert bridge<5e-4
        selected=np.asarray([alg.select(sc) for sc in scores]);nsel=int(np.argmin(rig));ngsel=alg.select(nscore)
        p=dest/f'{active}.npz';np.savez_compressed(p,T=Ts,pairs=pairs,distances=distances,counts=counts,
            fallback=fallback,proposals=proposals,seed_ranks=seed_ranks,clique_masks=clique_masks,refit_masks=refit_masks,
            final_masks=final_masks,scores=scores,gates=gates,selected=selected,native=native,native_rigidity=rig,
            native_gates=ngate,native_scores=nscore,native_selected=np.array([nsel,ngsel]),
            gate_x=full[0],gate_y=full[1],held_x=held[0],held_y=held[1],projected=projected,arm_wall_s=wall)
        rows.append(dict(seq=s,pair=active,file=str(p),sha256=sha(p)))
        check_cap(start,1800)
        if (index+1)%10==0: print('RAD1 bank',index+1,'of200',round(time.perf_counter()-start,1),'s',flush=True)
    verify()
    save(BASE/'bank.json',dict(rows=rows,wall_s=time.perf_counter()-start,arm_wall_s=dict(zip(ARMS,arm_wall.tolist())),
         common_preprocessing_and_native_score_wall_s=common_wall,input_io_wall_s=io_wall,peak_rss_bytes=rss(),
         max_native_bridge_delta=bridge,gt_read=False,new_inference=False))
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),bank_sha256=sha(BASE/'bank.json'),
         npz_bytes=sum(Path(r['file']).stat().st_size for r in rows)))
    state('BANK_SEALED',pairs=200,gt_read=False,new_inference=False)
    print('RAD1 bank sealed',flush=True)


def metric(T,G):
    e=np.linalg.inv(G)@T;R=e[:3,:3]
    angle=np.degrees(np.arctan2(np.linalg.norm([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])/2,np.clip((np.trace(R)-1)/2,-1,1)))
    return np.array([np.linalg.norm(e[:3,3]),angle])


def summarize(outcomes,cost):
    groups={}
    for s in ('00','08'):
        rr=[r for r in outcomes if r['seq']==s]
        groups[s]={}
        for arm in ['N','NG']+ARMS:
            pos=[r['methods'][arm] for r in rr if r['stratum']!='confuser']
            ordinary=[r['methods'][arm] for r in rr if r['stratum']=='ordinary']
            groups[s][arm]=dict(strict=sum(v['strict'] for v in pos),clip_mean=float(np.mean([v['clip'] for v in pos])),
                ordinary_strict=sum(v['strict'] for v in ordinary),correct_accepts=sum(v['strict'] and v['accepted'] for v in pos),
                incorrect_accepts=sum(r['methods'][arm]['accepted'] and not r['methods'][arm]['strict'] for r in rr),
                confuser_accepts=sum(r['methods'][arm]['accepted'] for r in rr if r['stratum']=='confuser'),
                oracle_strict=sum(r['methods'][arm]['oracle_strict'] for r in rr if r['stratum']!='confuser'))
    hard=[r for r in outcomes if r['seq']=='08' and r['stratum']!='confuser' and not r['native_available']]
    assert len(hard)==41
    recovery={a:sum(r['methods'][a]['strict'] for r in hard) for a in ARMS}
    g=groups['08'];h=groups['00'];tests={
        '08_gain_native':g['R']['strict']>=g['N']['strict']+4,
        '08_gain_projected':g['R']['strict']>=g['P']['strict']+3,
        '08_gain_descriptor':g['R']['strict']>=g['D']['strict']+3,
        '08_gain_native_geometric_selector':g['R']['strict']>=g['NG']['strict']+3,
        '08_hard_selected_recovery':recovery['R']>=5,'08_clipped_error':g['R']['clip_mean']<=.95*g['N']['clip_mean'],
        '00_strict_safety':h['R']['strict']>=h['N']['strict'],'00_clipped_safety':h['R']['clip_mean']<=1.02*h['N']['clip_mean'],
        'historical_incremental_cost':cost<=.25}
    for s in ('00','08'):
        a,b=groups[s]['R'],groups[s]['N']
        for name,field,sign in [('ordinary','ordinary_strict',1),('correct_accepts','correct_accepts',1),
                                ('incorrect_accepts','incorrect_accepts',-1),('confuser','confuser_accepts',-1)]:
            tests[s+'_'+name]=sign*a[field]>=sign*b[field]
    return dict(decision='RAD1_DEVELOPMENT_SIGNAL' if all(tests.values()) else 'NO_RAW_ASSOCIATION_DECODER_SIGNAL',
        groups=groups,hard08_selected_recoveries=recovery,gates=tests,incremental_cost_ratio_historical=cost)


def evaluate():
    verify();start=time.perf_counter();v=read(BASE/'bank_validation.json');seal=read(BASE/'bank_seal.json')
    assert v['passed'] and sha(BASE/'bank_validation.json')==read(BASE/'bank_validation_seal.json')['sha256']
    assert sha(BASE/'bank.json')==seal['bank_sha256'];bankdata=read(BASE/'bank.json');outcomes=[]
    truths={s:np.load(GT[s],allow_pickle=False) for s in ('00','08')}
    labels={s:read(F2/s/'evaluator_only_decisions.json') for s in ('00','08')}
    for index,((s,row),entry) in enumerate(zip(cohort(),bankdata['rows'])):
        label=labels[s][index%100];assert label['source_i']==row['source_i'] and label['source_j']==row['source_j']
        assert sha(entry['file'])==entry['sha256'];z=np.load(entry['file'],allow_pickle=False)
        truth=np.linalg.inv(truths[s][row['source_i']])@truths[s][row['source_j']]
        native_errors=np.asarray([metric(T,truth) for T in z['native']]);native_strict=(native_errors[:,0]<=1)&(native_errors[:,1]<=5)
        methods={}
        for arm,Ts,select,gates in [('N',z['native'],int(z['native_selected'][0]),z['native_gates']),
                                 ('NG',z['native'],int(z['native_selected'][1]),z['native_gates'])]+[(a,z['T'][i],int(z['selected'][i]),z['gates'][i]) for i,a in enumerate(ARMS)]:
            errors=np.asarray([metric(T,truth) for T in Ts]);strict=(errors[:,0]<=1)&(errors[:,1]<=5)
            methods[arm]=dict(generation=select,errors=errors.tolist(),strict=bool(strict[select]),oracle_strict=bool(strict.any()),
                clip=float(min(5,max(errors[select,0],errors[select,1]/5))),
                accepted=bool(gates[select,0]>=.7 and gates[select,1]<=2.5))
        assert methods['N']['strict']==label['methods']['N']['strict']
        assert methods['N']['accepted']==label['methods']['N']['accepted']
        assert bool(native_strict.any())==label['methods']['N-OR4']['strict']
        outcomes.append(dict(seq=s,pair=row['key'],stratum=label['stratum'],native_available=bool(native_strict.any()),methods=methods))
        z.close()
    cost=bankdata['arm_wall_s']['R']/read(BASE/'manifest.json')['native_historical_generation_wall_s']
    summary=summarize(outcomes,cost);summary.update(evaluation_wall_s=time.perf_counter()-start,peak_rss_bytes=rss())
    save(BASE/'outcomes.json',outcomes);save(BASE/'summary.json',summary);check_cap(start,600)
    state('EVALUATED_PENDING_VALIDATION',decision=summary['decision'],gt_read=True,new_inference=False)
    print('RAD1 decision',summary['decision'],summary['hard08_selected_recoveries'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','synthetic','bank','evaluate']);args=parser.parse_args()
    try:globals()[args.stage]()
    except Exception as exc:
        p=BASE/f'FAILURE_{args.stage}.json'
        if not p.exists():save(p,dict(utc=now(),stage=args.stage,error=repr(exc),traceback=traceback.format_exc()))
        state('INCOMPLETE',failed_stage=args.stage,error=repr(exc));raise
