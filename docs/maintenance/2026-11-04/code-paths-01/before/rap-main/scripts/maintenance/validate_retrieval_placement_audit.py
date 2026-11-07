"""Independent LC0 raw descriptors, retrieval, graphs and metric validation.

Imports neither the new runner/algorithm nor native retrieval/graph/metrics.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,resource,sys,time,traceback
import numpy as np
import gtsam
MAIN=Path(__file__).resolve().parents[2]; DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
BASE=MAIN/'docs/maintenance/2026-10-07/retrieval-placement-audit-01'; BANK=BASE/'bank'; EV=BASE/'evaluation'
SEQS=['00','05','06','07','09','10']; ARMS=['N','C','P','H']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()
def load(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def src(s):return MAIN/f"docs/maintenance/{'2026-09-26/e0-frontend-01' if s in SEQS[:3] else '2026-09-27/e0-heldout-01'}/full-{s}-A"
def pose(p):
    x=np.loadtxt(p).reshape(-1,3,4);o=np.repeat(np.eye(4)[None],len(x),0);o[:,:3]=x;return o
def verify():
    f=read(BASE/'freeze.json');seal=read(BASE/'bank_seal.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert seal['freeze_sha256']==sha(BASE/'freeze.json')
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items():assert sha(BANK/p)==h,p
def cap(start):
    assert time.perf_counter()-start<=3600 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=500*2**20

def raw_descriptor(path):
    raw=np.fromfile(path,np.float32).reshape(-1,4)[:,:3]
    xyz=raw[np.sqrt(np.sum(raw*raw,axis=1))>=1.5].copy()
    x,y,z=xyz.T;rho=np.hypot(x,y);active=rho>1e-6;den=np.maximum(rho,1e-6)
    angle=np.deg2rad(.205);c=np.cos(angle);s=np.sin(angle)
    corrected=xyz.copy()
    corrected[:,0]=np.where(active,x*c-np.where(active,x*z/den,0.)*s,x)
    corrected[:,1]=np.where(active,y*c-np.where(active,y*z/den,0.)*s,y)
    corrected[:,2]=np.where(active,z*c+np.where(active,rho,0.)*s,z)
    return grid(corrected),len(xyz)
def grid(xyz):
    p=np.asarray(xyz,dtype=np.float64);r=np.sqrt(np.sum(p[:,:2]*p[:,:2],axis=1))
    keep=(r>1e-6)&(r<=80);p=p[keep];r=r[keep]
    rings=np.minimum(19,np.maximum(0,np.ceil((r/80)*20).astype(np.int64)-1))
    sector=np.minimum(59,np.maximum(0,np.ceil(((np.degrees(np.arctan2(p[:,1],p[:,0]))+180)/360)*60).astype(np.int64)-1))
    bins=rings*60+sector;heights=np.maximum(p[:,2]+2,0).astype(np.float32)
    order=np.lexsort((heights,bins));bins=bins[order];heights=heights[order]
    ends=np.r_[bins[:-1]!=bins[1:],True] if len(bins) else np.array([],bool)
    output=np.zeros(1200,np.float32);output[bins[ends]]=heights[ends]
    return output.reshape(20,60)
def score(a,b):
    # Simultaneous shifts, retaining native float32 row reductions and ratios.
    cols=(np.arange(60)[None,:]-np.arange(60)[:,None])%60
    shifts=b[:,cols].transpose(1,0,2)
    na=np.sqrt(np.sum(a*a,axis=0));nb=np.sqrt(np.sum(b*b,axis=0))[cols]
    denom=na[None,:]*nb;dot=np.sum(a[None,:,:]*shifts,axis=1)
    sim=np.zeros((60,60),np.float64);valid=denom>1e-8;sim[valid]=dot[valid]/denom[valid]
    sim[(na[None,:]<1e-8)&(nb<1e-8)]=1.
    scores=1-np.mean(sim,axis=1);shift=int(np.argmin(scores));return float(scores[shift]),shift
def graph(odom,kf,edges):
    f=gtsam.NonlinearFactorGraph();v=gtsam.Values()
    for k in kf:v.insert(int(k),gtsam.Pose3(odom[k]))
    f.add(gtsam.PriorFactorPose3(int(kf[0]),gtsam.Pose3(odom[kf[0]]),gtsam.noiseModel.Diagonal.Sigmas(np.repeat(.01,6))))
    odnoise=gtsam.noiseModel.Diagonal.Sigmas(np.array([.05,.05,.05,.30,.30,.30]))
    for a,b in zip(kf[:-1],kf[1:]):f.add(gtsam.BetweenFactorPose3(int(a),int(b),gtsam.Pose3(np.linalg.solve(odom[a],odom[b])),odnoise))
    for e in edges:
        scale=min(3.,max(1.,float(e['mean_dist'])))
        noise=gtsam.noiseModel.Diagonal.Sigmas(np.array([.03,.03,.03,.20,.20,.20])*scale)
        robust=gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber(1.),noise)
        f.add(gtsam.BetweenFactorPose3(e['i'],e['j'],gtsam.Pose3(np.array(e['T_rel'])),robust))
    p=gtsam.LevenbergMarquardtParams();p.setMaxIterations(100);r=gtsam.LevenbergMarquardtOptimizer(f,v,p).optimize()
    keys=np.array([r.atPose3(int(k)).matrix() for k in kf]);full=np.empty_like(odom)
    for a,k in enumerate(kf):
        end=int(kf[a+1]) if a+1<len(kf) else len(odom);full[k:end]=(keys[a]@np.linalg.inv(odom[k]))@odom[k:end]
    return full,keys

def bank():
    start=time.perf_counter();verify();fx=load(BANK/'fixture.npz')
    assert np.array_equal(grid(fx['points']),fx['descriptor']) and score(fx['empty'],fx['empty'])==(0.,0)
    max_score_delta=0.;max_graph_delta=0.;totals=dict(scans=0,points=0,eligible_pairs=0,sc_scores=0,attempts=0);rows={}
    for s in SEQS:
        root=BANK/s;d=load(root/'descriptors.npz');ex=load(root/'exposure.npz');kf=read(src(s)/'keyframes.json');meta=read(src(s)/'source_frames.json');odom=pose(src(s)/'odom_poses.txt')
        assert np.array_equal(kf,d['keyframes']) and np.array_equal(odom,np.load(root/'odom.npy'))
        for a,k in enumerate(kf):
            sc,count=raw_descriptor(meta['scan_files'][k]);assert np.array_equal(sc,d['sc'][a]),(s,k,'descriptor')
            rk=np.sum(sc,axis=1,dtype=np.float32)/np.float32(60);assert np.array_equal(rk,d['ring_key'][a]) and count==d['point_counts'][a]
            totals['scans']+=1;totals['points']+=count
            if (a+1)%100==0:print('LC0 independent raw',s,a+1,'/',len(kf),flush=True)
            cap(start)
        pairs=[(a,b) for a in range(len(kf)) for b in range(a+1,len(kf)) if kf[b]-kf[a]>=200]
        ai=np.array([p[0] for p in pairs]);bj=np.array([p[1] for p in pairs]);ii=np.array(kf)[ai];jj=np.array(kf)[bj]
        for k,z in [('ai',ai),('bj',bj),('i',ii),('j',jj)]:assert np.array_equal(z,ex[k]),(s,k)
        od=np.array([float(np.sqrt(np.dot(odom[i,:3,3]-odom[j,:3,3],odom[i,:3,3]-odom[j,:3,3]))) for i,j in zip(ii,jj)])
        rd=np.array([float(np.sqrt(np.dot(d['ring_key'][b]-d['ring_key'][a],d['ring_key'][b]-d['ring_key'][a]))) for a,b in pairs])
        assert np.max(abs(od-ex['odom_distance']))<=1e-12 and np.array_equal(rd,ex['ring_distance'])
        ranks=np.zeros(len(pairs),np.int32);scores=np.full(len(pairs),-1.);shifts=np.full(len(pairs),-1,np.int16)
        for b in range(1,len(kf)):
            ids=sorted(np.flatnonzero(bj==b).tolist(),key=lambda t:(rd[t],ii[t]))
            for rank,t in enumerate(ids,1):ranks[t]=rank
            for t in ids[:10]:scores[t],shifts[t]=score(d['sc'][ai[t]],d['sc'][bj[t]])
        error=float(np.max(abs(scores-ex['sc_distance'])));max_score_delta=max(max_score_delta,error);assert error<=1e-6
        assert np.array_equal(ranks,ex['ring_rank']) and np.array_equal(shifts,ex['sc_shift'])
        prox=sorted(np.flatnonzero(od<15).tolist(),key=lambda t:(od[t],t))
        scpass=sorted(np.flatnonzero((scores>=0)&(scores<.25)).tolist(),key=lambda t:(scores[t],bj[t],ranks[t]))
        final=list(dict.fromkeys(prox[:12]+scpass[:12]))[:12]
        for key,value in [('proximity_precap',prox),('proximity_cap',prox[:12]),('sc_precap',scpass),('sc_cap',scpass[:12]),('union_precap',sorted(set(prox+scpass))),('final',final)]:assert np.array_equal(value,ex[key]),(s,key)
        original=[]
        with (src(s)/'verification_measurements.jsonl').open() as f:
            for line in f:
                if '"event": "candidate_started"' in line:
                    x=json.loads(line);original.append({k:x[k] for k in ['i','j','attempt_id']})
        assert original==read(root/'attempts.json') and [(int(ii[t]),int(jj[t])) for t in final]==[(e['i'],e['j']) for e in original]
        native=read(root/'native_edges.json');expected=[{k:e[k] for k in ['i','j','T_rel','mean_dist','overlap','measurement_id']} for e in read(src(s)/'accepted_loops.json')];assert native==expected
        full,keys=graph(odom,kf,native);delta=max(float(np.max(abs(full-np.load(root/'N.npy')))),float(np.max(abs(keys-np.load(root/'N_keys.npy')))))
        assert delta<=1e-5 and np.max(abs(full-pose(src(s)/'optimized_poses.txt')))<=1e-5;max_graph_delta=max(delta,max_graph_delta)
        totals['eligible_pairs']+=len(pairs);totals['sc_scores']+=int(sum(ranks<=10));totals['attempts']+=len(final)
        rows[s]=dict(eligible_pairs=len(pairs),attempts=len(final),max_score_delta=error,graph_delta=delta)
        print('LC0 independent exposure',s,rows[s],flush=True);cap(start)
    assert totals['scans']==1800 and totals['attempts']==71
    verify();assert read(BASE/'freeze.json')['utc']<read(BANK/'execution.json')['started_utc']<read(BASE/'bank_seal.json')['utc']
    save(BASE/'bank_validation.json',dict(passed=True,utc=utc(),totals=totals,rows=rows,max_score_delta=max_score_delta,max_graph_delta=max_graph_delta,wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,gt_read=False))
    save(BASE/'bank_validation_seal.json',dict(utc=utc(),bank_seal_sha256=sha(BASE/'bank_seal.json'),validation_sha256=sha(BASE/'bank_validation.json')))
    print('LC0 GT-free independent validation sealed',totals,flush=True)

def independent_selection(ids,ex,dist):
    choices={}
    for t in ids:
        if dist[t]>=15:continue
        j=int(ex['j'][t]);value=(float(dist[t]),int(ex['i'][t]),int(t))
        if j not in choices or value<choices[j]:choices[j]=value
    ordered=[choices[q][2] for q in sorted(choices)];k=min(12,len(ordered))
    return [ordered[((2*a+1)*len(ordered))//(2*k)] for a in range(k)]
def coverage(ex,dist):
    sets={'eligible':list(range(len(dist))),'sc_top10':np.flatnonzero(ex['ring_rank']<=10).tolist()}
    for k in ['sc_precap','sc_cap','proximity_precap','proximity_cap','union_precap','final']:sets[k]=ex[k].tolist()
    output={}
    for k,ids in sets.items():
        n=[t for t in ids if dist[t]<15];f=[t for t in ids if dist[t]>=15];nq={int(ex['j'][t]) for t in n};fq={int(ex['j'][t]) for t in f}
        output[k]=dict(pairs=len(ids),near_pairs=len(n),far_pairs=len(f),queries=len({int(ex['j'][t]) for t in ids}),near_queries=len(nq),mixed_queries=len(nq.intersection(fq)))
    return output
def evaluate():
    start=time.perf_counter();verify();r=read(BASE/'results.json');assert read(BASE/'bank_validation.json')['passed']
    assert read(BASE/'freeze.json')['utc']<read(BANK/'execution.json')['started_utc']<read(BASE/'bank_seal.json')['utc']<read(BASE/'bank_validation_seal.json')['utc']<r['gt_read_started_utc']
    assert r['bank_validation_seal_sha256']==sha(BASE/'bank_validation_seal.json') and r['bank_seal_sha256']==sha(BASE/'bank_seal.json')
    seal=read(BASE/'evaluation_seal.json');assert seal['results_sha256']==sha(BASE/'results.json')
    assert set(seal['files'])=={str(p.relative_to(EV)) for p in EV.rglob('*') if p.is_file()}
    for p,h in seal['files'].items():assert sha(EV/p)==h,p
    sys.path.insert(0,str(Path(__file__).parent))
    from validate_dense_propagation import segments,aligned_rmse,calibration
    selections=read(EV/'selection.json');cov=read(EV/'coverage.json');actual={};max_graph=0.;max_metric=0.;records=0;oracle_edges=0
    for s in SEQS:
        cam=pose(DATA/'poses'/f'{s}.txt');tr=calibration(s);ti=np.linalg.inv(tr);gt=ti@cam@tr
        ex=load(BANK/s/'exposure.npz');kf=load(BANK/s/'descriptors.npz')['keyframes'].tolist();odom=np.load(BANK/s/'odom.npy')
        dist=np.array([np.sqrt(np.dot(gt[i,:3,3]-gt[j,:3,3],gt[i,:3,3]-gt[j,:3,3])) for i,j in zip(ex['i'],ex['j'])]);assert np.max(abs(dist-np.load(EV/s/'gt_pair_distances.npy')))<=1e-10
        assert coverage(ex,dist)==cov[s];actual[s]={}
        selected={'C':[int(t) for t in ex['final'] if dist[t]<15.],'P':independent_selection(ex['union_precap'],ex,dist),'H':independent_selection(range(len(dist)),ex,dist)}
        for a in ARMS:
            if a=='N':est=np.load(BANK/s/'N.npy')
            else:
                pairids=selected[a];assert selections[s][a]['pair_ids']==pairids and selections[s][a]['count']==len(pairids)<=12
                edges=read(EV/s/f'{a}_edges.json');assert len(edges)==len(pairids)
                for e,t in zip(edges,pairids):
                    i,j=int(ex['i'][t]),int(ex['j'][t]);assert (e['i'],e['j'])==(i,j) and e['mean_dist']==1. and e['overlap']==1.
                    assert np.max(abs(np.array(e['T_rel'])-np.linalg.solve(gt[i],gt[j])))<=1e-10
                assert selections[s][a]['pairs']==[[e['i'],e['j']] for e in edges]
                est=np.load(EV/s/f'{a}.npy');full,keys=graph(odom,kf,edges);error=max(float(np.max(abs(full-est))),float(np.max(abs(keys-np.load(EV/s/f'{a}_keys.npy')))))
                max_graph=max(max_graph,error);assert error<=1e-5,(s,a,error);oracle_edges+=len(edges)
            assert np.isfinite(est).all();rot=est[:,:3,:3];assert np.max(abs(rot.transpose(0,2,1)@rot-np.eye(3)))<=1e-5 and np.max(abs(np.linalg.det(rot)-1))<=1e-5
            rec=segments(cam,tr@est@ti,list(range(len(gt))));saved=read(EV/s/f'{a}_segments.json');assert len(rec)==len(saved)
            for x,y in zip(rec,saved):
                for k in ['first','last','source_first','source_last','length_m']:assert x[k]==y[k]
                for k in ['translation_fraction','rotation_rad_per_m','speed_mps']:assert abs(x[k]-y[k])<=1e-8
            m=dict(ate=aligned_rmse(gt,est),ter=float(np.mean([x['translation_fraction'] for x in rec])*100),rer=float(np.mean([x['rotation_rad_per_m'] for x in rec])*180/np.pi*100),segment_count=len(rec))
            actual[s][a]=m;records+=len(rec)
            for k,v in m.items():error=abs(v-r['rows'][s][a][k]);max_metric=max(max_metric,error);assert error<=1e-8,(s,a,k,error)
        print('LC0 independent oracle and metrics',s,flush=True);cap(start)
    means={g:{a:{k:float(np.mean([actual[s][a][k] for s in seqs])) for k in ['ate','ter','rer']} for a in ARMS} for g,seqs in [('development',SEQS[:3]),('transfer_exposed',SEQS[3:])]}
    for g,m in means.items():
        for a in ARMS:
            for k,v in m[a].items():assert abs(v-r['cohort_means'][g][a][k])<=1e-8
    tests={};signals={}
    for a in ['P','H']:
        safety={s:dict(ter=actual[s][a]['ter']<=actual[s]['N']['ter']+.01,ate=actual[s][a]['ate']<=1.05*actual[s]['N']['ate']) for s in SEQS}
        cohorts={g:dict(ter=m['N']['ter']-m[a]['ter']>=.01,ate=1-m[a]['ate']/m['N']['ate']>=.05,placement_ter=m[a]['ter']<m['C']['ter'],placement_ate=m[a]['ate']<m['C']['ate']) for g,m in means.items()}
        signals[a]=any(all(c.values()) for c in cohorts.values()) and all(all(v.values()) for v in safety.values())
        tests[a]=dict(cohorts=cohorts,safety=safety,actionable=signals[a])
    decision='NATIVE_PRECAP_PLACEMENT_OPPORTUNITY' if signals['P'] else ('STRUCTURAL_ONLY_PLACEMENT_OPPORTUNITY' if signals['H'] else 'NO_FIXED_BUDGET_PLACEMENT_SIGNAL')
    assert dict(tests=tests,decision=decision)==r['gate'];verify()
    save(BASE/'validation.json',dict(passed=True,utc=utc(),decision=decision,independent_segment_records=records,oracle_edges=oracle_edges,max_graph_delta=max_graph,max_metric_delta=max_metric,wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    save(BASE/'validation_seal.json',dict(utc=utc(),validation_sha256=sha(BASE/'validation.json'),results_sha256=sha(BASE/'results.json'),evaluation_seal_sha256=sha(BASE/'evaluation_seal.json')))
    (BASE/'INCOMPLETE').unlink();print('LC0 fully validated',decision,records,'segments',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['bank','evaluate']);a=p.parse_args()
    try:globals()[a.stage]()
    except Exception as e:
        path=BASE/f'FAILURE_validation_{a.stage}.json'
        if not path.exists():save(path,dict(error=repr(e),traceback=traceback.format_exc(),utc=utc()))
        raise
