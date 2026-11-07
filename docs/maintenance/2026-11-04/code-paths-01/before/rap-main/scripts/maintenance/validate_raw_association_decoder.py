"""Independent RAD1 verification. No decoder/runner imports. Horn geometry."""
from __future__ import annotations
import argparse,hashlib,json,os,resource,time,traceback
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01'
F2=MAIN/'docs/maintenance/2026-09-27/f2-structured-dev-01'
C1=MAIN/'docs/maintenance/2026-09-28/c1-descriptor-information-01'
GT={'00':MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy',
    '08':MAIN/'docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy'}
ARMS=['R','P','D','Z']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    return f
def rss():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
def transform(T,x):return (T[:3,:3]@np.asarray(x).T).T+T[:3,3]


def horn(source,target):
    p,q=np.asarray(source,float),np.asarray(target,float)
    if len(p)<3 or p.shape!=q.shape:return None
    a,b=p-p.mean(0),q-q.mean(0)
    for v in (a,b):
        sv=np.linalg.svd(v,compute_uv=False)
        if sv[0]<=1e-12 or sv[1]<=sv[0]*1e-6:return None
    S=a.T@b;xx,xy,xz=S[0];yx,yy,yz=S[1];zx,zy,zz=S[2]
    N=np.array([[xx+yy+zz,yz-zy,zx-xz,xy-yx],
        [yz-zy,xx-yy-zz,xy+yx,zx+xz],[zx-xz,xy+yx,-xx+yy-zz,yz+zy],
        [xy-yx,zx+xz,yz+zy,-xx-yy+zz]])
    _,vectors=np.linalg.eigh(N);w,x,y,z=vectors[:,-1]
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=q.mean(0)-R@p.mean(0);return T


def neighbors(points,reference,ids):
    tree=cKDTree(reference);count=min(4,len(reference));dist,index=tree.query(points,k=count,workers=1)
    if count==1:dist=dist[:,None];index=index[:,None]
    result=[]
    for i,(d,ind) in enumerate(zip(dist,index)):
        k=min(3,len(reference))
        if count>k and d[k]==d[k-1]:
            ind=np.array(tree.query_ball_point(points[i],d[k-1]+1e-12),int)
        values=np.sqrt(np.sum((reference[ind]-points[i])**2,axis=1))
        result.append(ind[np.lexsort((ids[ind],values))][:k])
    return np.asarray(result)


def association(a,b,ids_a=None,ids_b=None):
    a,b=np.asarray(a,float),np.asarray(b,float)
    ia=np.arange(len(a)) if ids_a is None else ids_a;ib=np.arange(len(b)) if ids_b is None else ids_b
    f=neighbors(a,b,ib);r=neighbors(b,a,ia);pairs=[];dist=[]
    for i in range(len(a)):
        for j in f[i]:
            if i in r[j]:pairs.append((i,int(j)));dist.append(float(np.sqrt(np.sum((a[i]-b[j])**2))))
    m=np.asarray(pairs,dtype=np.int64).reshape(-1,2);d=np.asarray(dist)
    order=np.lexsort((ib[m[:,1]],ia[m[:,0]],d))[:512]
    return m[order],d[order]


def replay_solver(x,y,m,d,fallback,ids_x=None,ids_y=None):
    n=len(m);empty=dict(fallback=True,proposals=0,seed_rank=-1,clique=[],refits=np.zeros((3,n),bool),final=np.zeros(n,bool))
    if n<3:return fallback.copy(),empty
    a,b=x[m[:,0]],y[m[:,1]]
    da=np.sqrt(np.sum((a[:,None]-a[None])**2,axis=2));db=np.sqrt(np.sum((b[:,None]-b[None])**2,axis=2))
    compat=(np.abs(da-db)<=1)&(m[:,0,None]!=m[None,:,0])&(m[:,1,None]!=m[None,:,1])
    ix=np.arange(len(x)) if ids_x is None else ids_x;iy=np.arange(len(y)) if ids_y is None else ids_y
    order=sorted(range(n),key=lambda v:(-int(compat[v].sum()),float(d[v]),int(ix[m[v,0]]),int(iy[m[v,1]])))
    best=None;valid_count=0
    for rank,root in enumerate(order[:32]):
        clique=[root];remaining=set(np.flatnonzero(compat[root]))
        while remaining and len(clique)<64:
            point=next(v for v in order if v in remaining);clique.append(point)
            remaining.intersection_update(np.flatnonzero(compat[point]))
        T=horn(b[clique],a[clique]);refits=[]
        if T is None:continue
        for _ in range(3):
            mask=np.sqrt(np.sum((transform(T,b)-a)**2,axis=1))<=1
            T=horn(b[mask],a[mask])
            if T is None:break
            refits.append(mask)
        if T is None:continue
        res=np.sqrt(np.sum((transform(T,b)-a)**2,axis=1));inliers=res<=1
        key=(-int(inliers.sum()),round(float(np.minimum(res,1).dot(np.minimum(res,1))/n),12),rank)
        valid_count+=1
        if best is None or key<best[0]:best=(key,T,rank,clique,np.asarray(refits),inliers)
    if best is None:return fallback.copy(),empty
    _,T,rank,clique,refits,final=best
    return T,dict(fallback=False,proposals=valid_count,seed_rank=rank,clique=clique,refits=refits,final=final)


def stats(x,y,T,brute=False):
    b=transform(T,y);a=np.asarray(x,float)
    if brute:
        mins_a=np.full(len(a),np.inf);mins_b=np.full(len(b),np.inf)
        for start in range(0,len(a),64):
            d=np.sqrt(np.sum((a[start:start+64,None]-b[None])**2,axis=2))
            mins_a[start:start+len(d)]=d.min(1);mins_b=np.minimum(mins_b,d.min(0))
    else:
        mins_a=cKDTree(b).query(a,workers=1)[0];mins_b=cKDTree(a).query(b,workers=1)[0]
    return np.array([(sum(mins_a<1)/len(a)+sum(mins_b<1)/len(b))/2,(sum(mins_a)/len(a)+sum(mins_b)/len(b))/2])
def selection(scores):return sorted(range(len(scores)),key=lambda k:(-scores[k,0],scores[k,1],k))[0]
def proper(T,tol=1e-9):
    assert np.isfinite(T).all() and np.max(np.abs(T[3]-[0,0,0,1]))<=1e-10
    assert np.max(np.abs(T[:3,:3].T@T[:3,:3]-np.eye(3)))<=tol and abs(np.linalg.det(T[:3,:3])-1)<=tol


def synthetic():
    verify();start=time.perf_counter();seal=read(BASE/'synthetic_seal.json');delta=0.;count=0
    for entry in seal['files']:
        assert sha(entry['file'])==entry['sha256'];z=np.load(entry['file'],allow_pickle=False)
        if entry['case']!='degenerate_ties_wrong_periodic':
            m,d=association(z['qx'],z['qy'],z['ids_x'],z['ids_y'])
            assert set(map(tuple,m))==set(map(tuple,z['pairs']))
            # Stored source association order is checked by independent distances;
            # Horn then reproduces the fixed solver in that numerical row order.
            sv=np.sqrt(np.sum((z['qx'][z['pairs'][:,0]]-z['qy'][z['pairs'][:,1]])**2,axis=1))
            assert np.max(np.abs(sv-z['distances']))<1e-10
            T,info=replay_solver(z['x'],z['y'],z['pairs'],z['distances'],np.eye(4),z['ids_x'],z['ids_y'])
            assert not info['fallback'];proper(T)
            error=float(np.max(np.abs(T-z['expected'])));delta=max(delta,error);assert error<1e-8
            assert np.max(np.abs(T-z['T']))<1e-8
        else:
            assert horn(z['line'],z['line']) is None and horn(z['line'][:2],z['line'][:2]) is None
            m,d=association(z['duplicate'],z['duplicate'],z['ids'],z['ids'])
            assert np.array_equal(m,z['tie_pairs'])
            T=horn(z['periodic_source'],z['periodic_target']);assert np.max(np.abs(T-z['wrong']))<1e-10
            for name,T in [('true_score',np.eye(4)),('wrong_score',z['wrong'])]:
                assert np.max(np.abs(stats(z['irregular'],z['irregular'],T,True)-z[name]))<1e-10
            assert np.max(np.abs(stats(z['periodic'],z['periodic'],T,True)-z['periodic_score']))<1e-10
        z.close();count+=1
    assert time.perf_counter()-start<=300
    save(BASE/'synthetic_validation.json',dict(passed=True,files=count,max_Horn_delta=delta,wall_s=time.perf_counter()-start,peak_rss_bytes=rss(),gt_read=False))
    print('RAD1 independent synthetic passed',count,'files',delta,flush=True)


def reconstruct_gate(paths):
    # Reproduce source recipe directly, without importing the preprocessing class.
    import open3d as o3d
    full=[];fit=[]
    for path in paths:
        raw=np.fromfile(path,np.float32).reshape(-1,4)[:,:3];raw=raw[np.linalg.norm(raw,axis=1)>=1.5]
        # Exact float32 correction requires the audited production convention.
        import sys
        sys.path.insert(0,str(MAIN.parent/'RAP-SLAM'))
        from rap_slam.real_dataset import kitti_vertical_correction
        p=np.ascontiguousarray(kitti_vertical_correction(raw),dtype=np.float32)
        cloud=o3d.geometry.PointCloud();cloud.points=o3d.utility.Vector3dVector(p.astype(float))
        cloud=cloud.voxel_down_sample(.4);cloud,_=cloud.remove_statistical_outlier(20,2.5)
        arr=np.asarray(cloud.points,dtype=np.float32)
        values=[]
        for cap in (4000,2000):
            ids=np.random.default_rng(42).choice(len(arr),cap,replace=False) if len(arr)>cap else np.arange(len(arr))
            values.append(arr[ids])
        full.append(values[0]);fit.append(values[1])
    return full,fit


def bank():
    frozen=verify();start=time.perf_counter();seal=read(BASE/'bank_seal.json');assert sha(BASE/'bank.json')==seal['bank_sha256']
    data=read(BASE/'bank.json');manifest=read(BASE/'manifest.json');assert len(data['rows'])==200
    for e in data['rows']:assert sha(e['file'])==e['sha256']
    max_pose=max_score=max_dist=max_projected=0.;associations=solves=brute_distances=0
    for index,(entry,row) in enumerate(zip(data['rows'],manifest['rows'])):
        assert entry['pair']==row['pair'] and entry['seq']==row['seq'];s,key=entry['seq'],entry['pair'];z=np.load(entry['file'],allow_pickle=False)
        with np.load(F2/s/key/'inputs.npz',allow_pickle=False) as p:
            counts=p['counts'];assert counts.tolist()==[2000,1000,1000,2000,1000,1000]
            x,y=p['points'][:2000].astype(float),p['points'][4000:6000].astype(float);scale=float(p['scale'])
        with np.load(C1/s/f'{key}.npz',allow_pickle=False) as p:fx,fy=p['features'][:2000].astype(float),p['features'][4000:6000].astype(float)
        full,original=reconstruct_gate(row['anchor_paths']);assert np.array_equal(original[0],x) and np.array_equal(original[1],y)
        held=[a[cKDTree(b).query(a,workers=1)[0]>1e-5] for a,b in zip(full,(x,y))]
        for name,value in [('gate_x',full[0]),('gate_y',full[1]),('held_x',held[0]),('held_y',held[1])]:assert np.array_equal(z[name],value)
        assert min(map(len,held))>=200
        dcache=None
        for k in range(4):
            with np.load(F2/s/key/f'N{k}.npz',allow_pickle=False) as p:
                native=p['T'];proper(native,1e-5);assert np.array_equal(native,z['native'][k])
                assert float(p['rigidity_steps'].mean())==z['native_rigidity'][k]
                raw=np.asarray([p['end_point_trajectory'][-1,:2000].astype(float)*scale,p['end_point_trajectory'][-1,4000:6000].astype(float)*scale])
            projected=np.array([transform(horn(x,raw[0]),x),transform(horn(y,raw[1]),y)])
            err=float(np.max(np.abs(projected-z['projected'][k])));max_projected=max(max_projected,err);assert err<1e-7
            seed=int(hashlib.sha256(f'RAD1|{key}|{k}'.encode()).hexdigest()[:16],16);rng=np.random.Generator(np.random.PCG64(seed))
            representations=[raw,projected,[fx,fy],[raw[0,rng.permutation(2000)],raw[1,rng.permutation(2000)]]]
            for ai,(a,b) in enumerate(representations):
                if ai==2 and dcache is not None:m,d=dcache
                else:m,d=association(a,b)
                if ai==2:dcache=(m,d)
                n=int(z['counts'][ai,k]);assert n<=512 and len(m)==n
                saved=z['pairs'][ai,k,:n];assert set(map(tuple,m))==set(map(tuple,saved)),(key,k,ARMS[ai],'matches')
                assert np.all(z['pairs'][ai,k,n:]==-1)
                distances=np.sqrt(np.sum((a[saved[:,0]]-b[saved[:,1]])**2,axis=1))
                err=float(np.max(np.abs(distances-z['distances'][ai,k,:n])));max_dist=max(max_dist,err);assert err<1e-7
                # Verify exact canonical order independently, allowing 1e-10 arithmetic ties.
                sd=z['distances'][ai,k,:n];assert np.all(np.diff(sd)>=-1e-10)
                T,info=replay_solver(x,y,saved,sd,native);proper(T,1e-5 if info['fallback'] else 1e-9)
                error=float(np.max(np.abs(T-z['T'][ai,k])));max_pose=max(max_pose,error);assert error<1e-7,(key,k,ARMS[ai],error)
                assert info['fallback']==z['fallback'][ai,k] and info['proposals']==z['proposals'][ai,k] and info['seed_rank']==z['seed_ranks'][ai,k]
                cm=np.zeros(n,bool);cm[info['clique']]=True
                assert np.array_equal(cm,z['clique_masks'][ai,k,:n]) and np.array_equal(info['refits'],z['refit_masks'][ai,k,:,:n])
                assert np.array_equal(info['final'],z['final_masks'][ai,k,:n])
                for name,points in [('scores',held),('gates',full)]:
                    actual=stats(*points,z['T'][ai,k]);error=float(np.max(np.abs(actual-z[name][ai,k])));max_score=max(max_score,error);assert error<1e-10
                    if index in (0,100):
                        brute=stats(*points,z['T'][ai,k],True);assert np.max(np.abs(brute-actual))<1e-10
                        brute_distances+=len(points[0])*len(points[1])
                associations+=n;solves+=1
            assert np.max(np.abs(stats(*full,native)-z['native_gates'][k]))<1e-10
            assert np.max(np.abs(stats(*held,native)-z['native_scores'][k]))<1e-10
        assert z['native_selected'][0]==int(np.argmin(z['native_rigidity'])) and z['native_selected'][1]==selection(z['native_scores'])
        assert z['selected'].tolist()==[selection(a) for a in z['scores']]
        z.close();assert time.perf_counter()-start<=1800 and rss()<=4*2**30
        if (index+1)%10==0:print('RAD1 independent bank',index+1,'of200',round(time.perf_counter()-start,1),'s',flush=True)
    assert seal['npz_bytes']==sum(Path(r['file']).stat().st_size for r in data['rows'])
    assert data['wall_s']<=1800 and data['peak_rss_bytes']<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=300*2**20
    save(BASE/'bank_validation.json',dict(passed=True,pairs=200,solves=solves,associations=associations,
        max_Horn_pose_delta=max_pose,max_distance_delta=max_dist,max_projected_delta=max_projected,max_geometry_score_delta=max_score,
        brute_force_distances=brute_distances,wall_s=time.perf_counter()-start,peak_rss_bytes=rss(),gt_read=False))
    save(BASE/'bank_validation_seal.json',dict(utc=now(),sha256=sha(BASE/'bank_validation.json'),bank_sha256=seal['bank_sha256']))
    print('RAD1 independent bank passed',solves,'solves',max_pose,flush=True)


def metric(T,G):
    e=np.linalg.solve(G,T);R=e[:3,:3];v=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])
    return np.array([np.sqrt(e[:3,3].dot(e[:3,3])),np.rad2deg(np.arctan2(np.sqrt(v.dot(v))/2,max(-1,min(1,(np.trace(R)-1)/2))))])


def evaluation():
    verify();start=time.perf_counter();assert read(BASE/'bank_validation.json')['passed']
    assert sha(BASE/'bank_validation.json')==read(BASE/'bank_validation_seal.json')['sha256']
    bankdata=read(BASE/'bank.json');outcomes=read(BASE/'outcomes.json');summary=read(BASE/'summary.json')
    assert len(outcomes)==200;truths={s:np.load(GT[s],allow_pickle=False) for s in ('00','08')}
    labels={s:read(F2/s/'evaluator_only_decisions.json') for s in ('00','08')};groups={};delta=0.
    for index,(row,entry) in enumerate(zip(outcomes,bankdata['rows'])):
        s=row['seq'];label=labels[s][index%100];assert row['pair']==entry['pair']==f"{s}_{label['source_i']}_{label['source_j']}"
        assert row['stratum']==label['stratum'];assert sha(entry['file'])==entry['sha256'];z=np.load(entry['file'],allow_pickle=False)
        truth=np.linalg.solve(truths[s][label['source_i']],truths[s][label['source_j']])
        for ai,arm in enumerate(['N','NG']+ARMS):
            Ts=z['native'] if ai<2 else z['T'][ai-2];sel=int(z['native_selected'][ai]) if ai<2 else int(z['selected'][ai-2])
            gates=z['native_gates'] if ai<2 else z['gates'][ai-2];errors=np.array([metric(T,truth) for T in Ts])
            md=row['methods'][arm];error=float(np.max(np.abs(errors-np.asarray(md['errors']))));delta=max(delta,error);assert error<1e-8
            strict=(errors[:,0]<=1)&(errors[:,1]<=5);clip=float(min(5,max(errors[sel,0],errors[sel,1]/5)))
            accepted=bool(gates[sel,0]>=.7 and gates[sel,1]<=2.5)
            assert md['generation']==sel and md['strict']==bool(strict[sel]) and md['oracle_strict']==bool(strict.any())
            assert abs(md['clip']-clip)<1e-8 and md['accepted']==accepted
            if arm=='N':
                assert row['native_available']==bool(strict.any())==label['methods']['N-OR4']['strict']
                assert md['strict']==label['methods']['N']['strict'] and accepted==label['methods']['N']['accepted']
        z.close()
    for s in ('00','08'):
        rr=[r for r in outcomes if r['seq']==s];assert len(rr)==100
        assert all(sum(r['stratum']==tag for r in rr)==25 for tag in ('ordinary','confuser','low_overlap','ambiguous_positive'))
        groups[s]={}
        for arm in ['N','NG']+ARMS:
            pos=[r for r in rr if r['stratum']!='confuser'];md=lambda r:r['methods'][arm]
            groups[s][arm]=dict(strict=sum(md(r)['strict'] for r in pos),clip_mean=sum(md(r)['clip'] for r in pos)/75,
                ordinary_strict=sum(md(r)['strict'] for r in rr if r['stratum']=='ordinary'),
                correct_accepts=sum(md(r)['strict'] and md(r)['accepted'] for r in pos),
                incorrect_accepts=sum(md(r)['accepted'] and not md(r)['strict'] for r in rr),
                confuser_accepts=sum(md(r)['accepted'] for r in rr if r['stratum']=='confuser'),oracle_strict=sum(md(r)['oracle_strict'] for r in pos))
            for field,value in groups[s][arm].items():assert abs(summary['groups'][s][arm][field]-value)<1e-10
    hard=[r for r in outcomes if r['seq']=='08' and r['stratum']!='confuser' and not r['native_available']];assert len(hard)==41
    rec={arm:sum(r['methods'][arm]['strict'] for r in hard) for arm in ARMS};assert rec==summary['hard08_selected_recoveries']
    historical=read(BASE/'manifest.json')['native_historical_generation_wall_s'];cost=bankdata['arm_wall_s']['R']/historical
    assert abs(cost-summary['incremental_cost_ratio_historical'])<1e-12
    g,h=groups['08'],groups['00'];gates={}
    gates['08_gain_native']=g['R']['strict']-g['N']['strict']>=4
    for control,tag in [('P','projected'),('D','descriptor'),('NG','native_geometric_selector')]:gates['08_gain_'+tag]=g['R']['strict']-g[control]['strict']>=3
    gates.update({'08_hard_selected_recovery':rec['R']>=5,'08_clipped_error':g['R']['clip_mean']<=.95*g['N']['clip_mean'],
        '00_strict_safety':h['R']['strict']>=h['N']['strict'],'00_clipped_safety':h['R']['clip_mean']<=1.02*h['N']['clip_mean'],
        'historical_incremental_cost':cost<=.25})
    for s in ('00','08'):
        r,n=groups[s]['R'],groups[s]['N'];gates[s+'_ordinary']=r['ordinary_strict']>=n['ordinary_strict']
        gates[s+'_correct_accepts']=r['correct_accepts']>=n['correct_accepts'];gates[s+'_incorrect_accepts']=r['incorrect_accepts']<=n['incorrect_accepts']
        gates[s+'_confuser']=r['confuser_accepts']<=n['confuser_accepts']
    assert gates==summary['gates'];decision='RAD1_DEVELOPMENT_SIGNAL' if all(gates.values()) else 'NO_RAW_ASSOCIATION_DECODER_SIGNAL'
    assert decision==summary['decision'];assert time.perf_counter()-start<=600
    save(BASE/'validation.json',dict(passed=True,decision=decision,pairs=200,max_error_delta=delta,wall_s=time.perf_counter()-start,
        peak_rss_bytes=rss(),summary_sha256=sha(BASE/'summary.json'),outcomes_sha256=sha(BASE/'outcomes.json'),
        native_reproduction=True,gt_free_validation_precedes_gt=True))
    save(BASE/'validation_seal.json',dict(utc=now(),sha256=sha(BASE/'validation.json')))
    (BASE/'INCOMPLETE').unlink()
    print('RAD1 final independent validation passed',decision,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['synthetic','bank','evaluation']);args=parser.parse_args()
    try:globals()[args.stage]()
    except Exception as exc:
        p=BASE/f'FAILURE_validation_{args.stage}.json'
        if not p.exists():save(p,dict(utc=now(),error=repr(exc),traceback=traceback.format_exc()))
        raise
