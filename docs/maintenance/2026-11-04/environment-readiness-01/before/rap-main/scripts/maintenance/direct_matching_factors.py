"""DMF0 isolated direct/frozen matching factors; no production modifications."""
import time
START = time.monotonic()
import json
import hashlib
import sys
import resource
import signal
import traceback
from pathlib import Path
from datetime import datetime, timezone

MAIN = Path(__file__).resolve().parents[2]
BASE = MAIN/'docs/maintenance/2026-10-20/direct-matching-factors-01'
SUP = BASE/'supervision'
SLAM = MAIN.parent/'RAP-SLAM'
DATA = MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
MGR = MAIN/'docs/maintenance/2026-10-12/measured-gicp-registration-01'
SEQS = ('00', '05')

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone.utc).isoformat()
def save(p, x):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(x, f, indent=2, allow_nan=False); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def used():
    total=0.
    for d in SUP.glob('*'):
        if not d.is_dir(): continue
        n=read(d/'child_exit.json')['wall_seconds'] if (d/'child_exit.json').exists() else 0.
        w=read(d/'exit.json')['wall_seconds'] if (d/'exit.json').exists() else 0.
        total+=max(n,w)
    return total
def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=256*2**20
    if (SUP/'host_latest.json').exists(): assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def src(s): return MAIN/f'docs/maintenance/2026-09-26/e0-frontend-01/full-{s}-A'
def loops(s):
    return [{k:r[k] for k in ('i','j','T_rel','mean_dist','overlap','measurement_id')} for r in read(src(s)/'accepted_loops.json')]
def pointpath(s,i): return MGR/f'input/{s}/{i:06d}.npz'
def rawpath(s,i): return DATA/f'sequences/{s}/velodyne/{i:06d}.bin'
def kisspath(s):
    root=MAIN/f'docs/meeting_20261011/benchmark/attempt03/r01-{s}-KISS-SLAM/slam_output'
    return sorted(p for p in root.iterdir() if p.name!='latest' and p.is_dir())[0]
def kisssources():
    root=Path('/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages/kiss_slam')
    return [root/n for n in ('slam.py','local_map_graph.py','pose_graph_optimizer.py')]

def component():
    source={str(p):sha(p) for p in kisssources()}; rows={}
    for s in SEQS:
        d=kisspath(s); row={}
        for name in ('trajectory.g2o','local_maps/local_map_graph.g2o'):
            p=d/name; vs=[]; edges=[]
            for line in p.read_text().splitlines():
                t=line.split()
                if t and t[0]=='VERTEX_SE3:QUAT': vs.append(int(t[1]))
                elif t and t[0]=='EDGE_SE3:QUAT': edges.append((int(t[1]),int(t[2])))
            row[name]=dict(sha256=sha(p),vertices=len(vs),edges=len(edges),nonadjacent_index_edges=[e for e in edges if abs(e[0]-e[1])!=1])
        row.update(E0_keyframes=len(read(src(s)/'keyframes.json')),E0_loops=len(loops(s)),
                   exported_map_files=len(list((d/'local_maps/plys').glob('*.ply'))),config_sha256=sha(d/'config.yml'),
                   member_sidecars=[str(p.relative_to(d)) for p in d.rglob('*') if p.is_file() and any(k in p.name.lower() for k in ('source','member','frame','timestamp'))])
        rows[s]=row
    save(BASE/'COMPONENT_RESULT.json',dict(utc=now(),source_identities=source,rows=rows,
        decision='NO_IDENTIFIABLE_E0_COMPONENT_TRANSPLANT; ADMIT_FIXED_INPUT_DMF_SCREEN',
        causal_attribution=False,point_decode=False,GT_numeric_read=False,
        reasons=['local map IDs differ from raw scan IDs','map PLY exports apply optimized keypose',
                 'KISS local odometry resets and unit information differ from E0','no explicit source membership sidecar found in these two archive folders']))
    print(json.dumps(rows),flush=True)

def imports():
    global np, gtsam, KDTree
    import numpy as np
    import gtsam
    from scipy.spatial import cKDTree as KDTree
    sys.path[:0]=[str(SLAM),str(SLAM/'scripts')]

def freeze():
    import importlib.metadata as md
    paths=[Path(__file__),Path(__file__).with_name('validate_direct_matching_factors.py'),
           Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'COMPONENT_RESULT.json',
           SLAM/'rap_slam/pose_graph.py',SLAM/'rap_slam/real_dataset.py',SLAM/'scripts/eval_paper_metrics.py',
           Path(__file__).with_name('validate_scan_level_graph.py'),MGR/'input_seal.json',MGR/'freeze.json',*kisssources()]
    prior=read(MGR/'freeze.json')['files']; seal=read(MGR/'input_seal.json')['files']
    for s in SEQS:
        paths += [src(s)/n for n in ('odom_poses.txt','optimized_poses.txt','keyframes.json','accepted_loops.json','source_frames.json')]
        paths += [DATA/f'poses/{s}.txt',DATA/f'sequences/{s}/calib.txt']
        paths += [kisspath(s)/n for n in ('trajectory.g2o','local_maps/local_map_graph.g2o','config.yml')]
        for i in sorted({r[k] for r in loops(s) for k in ('i','j')}):
            p=pointpath(s,i); raw=rawpath(s,i)
            assert sha(p)==seal[f'{s}/{i:06d}.npz']
            assert sha(raw)==prior[str(raw)]
            paths += [p,raw]
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    identities={str(p):sha(p) for p in paths}
    for i,p in enumerate(paths):
        if p.suffix in ('.py','.ps1','.md'): (snapshot/f'{i:03d}-{p.name}').write_bytes(p.read_bytes())
    save(BASE/'freeze.json',dict(utc=now(),files=identities,packages={p:md.version(p) for p in ('numpy','scipy','gtsam','evo')},
         python=sys.version,cohort=list(SEQS),caps=dict(seconds=1800,rss=4*2**30,dossier=256*2**20,gpu=0)))
    (BASE/'INCOMPLETE').write_text('Pending frozen synthetic, complete bank, and independent evaluation.\n')
    print('Frozen',len(identities),'inputs/sources',flush=True)
def verify():
    for p,h in read(BASE/'freeze.json')['files'].items(): assert sha(p)==h,p
def load(p):
    a=np.loadtxt(p); out=np.tile(np.eye(4),(len(a),1,1)); out[:,:3]=a.reshape(-1,3,4); return out
def inv(t):
    out=np.eye(4); out[:3,:3]=t[:3,:3].T; out[:3,3]=-out[:3,:3]@t[:3,3]; return out
def skew(p):
    p=np.asarray(p); x,y,z=np.moveaxis(p,-1,0); o=np.zeros_like(x)
    return np.stack([o,-z,y,z,o,-x,-y,x,o],axis=-1).reshape(p.shape[:-1]+(3,3))
def proper(t):
    a=np.asarray(t).copy(); u,_,v=np.linalg.svd(a[...,:3,:3]); d=np.broadcast_to(np.eye(3),a[...,:3,:3].shape).copy(); d[...,-1,-1]=np.linalg.det(u@v)
    a[...,:3,:3]=u@d@v; assert np.max(abs(a-t))<=1e-5
    return a
def adj(t):
    a=np.zeros((6,6)); a[:3,:3]=a[3:,3:]=t[:3,:3]; a[3:,:3]=skew(t[:3,3])@t[:3,:3]; return a
def exp(x): return gtsam.Pose3.Expmap(np.asarray(x)).matrix()

class Matching:
    def __init__(self,a,b,z,scale=1.):
        self.a,self.b,self.z0=np.asarray(a),np.asarray(b),z.copy()
        self.ta,self.tb=KDTree(a),KDTree(b); self.scale=scale; self.calls=0
    def residual(self,z,jac=True):
        self.calls+=1; r=z[:3,:3]; t=z[:3,3]
        y=self.b@r.T+t; v=(self.a-t)@r
        df,ix=self.ta.query(y,workers=1); dr,jx=self.tb.query(v,workers=1)
        e=np.concatenate([y-self.a[ix],v-self.b[jx]])
        d=np.concatenate([df,dr]); active=d<=2.5; safe=np.maximum(d,1e-30)
        robust=np.where(d<=.5,d*d,d-.25); h=np.where(active,robust,2.25)
        f=np.sqrt(np.maximum(robust,0))/safe; f=np.where(d<1e-12,1.,f)
        out=e*f[:,None]; out[~active]=[1.5,0.,0.]
        norm=self.scale/np.sqrt(len(e)); out*=norm
        if not jac: return out.reshape(-1),None,dict(support=float(active.mean()),directed_points=len(e))
        jf=np.concatenate([-np.einsum('ab,nbc->nac',r,skew(self.b)),np.broadcast_to(r,(len(self.b),3,3))],axis=2)
        jr=np.concatenate([skew(v),np.broadcast_to(-np.eye(3),(len(v),3,3))],axis=2)
        j=np.concatenate([jf,jr]); derivative=np.zeros_like(d)
        tail=(d>.5)&active
        derivative[tail]=f[tail]*(.5/robust[tail]-1/safe[tail])/safe[tail]
        radial=f[:,None,None]*np.eye(3)+derivative[:,None,None]*e[:,:,None]*e[:,None,:]
        j=np.einsum('nab,nbc->nac',radial,j); j[~active]=0.; j*=norm
        return out.reshape(-1),j.reshape(-1,6),dict(support=float(active.mean()),directed_points=len(e))
    def prepare(self,mean_dist):
        r,j,info=self.residual(self.z0); trace=float(np.sum(j[:,3:]**2)); assert trace>1e-12 and info['support']>=.5
        lam=(3/(.20*np.clip(mean_dist,1,3))**2)/trace; self.scale=float(np.sqrt(lam))
        r,j,info=self.residual(self.z0); u,s,v=np.linalg.svd(j,full_matrices=False)
        self.A=s[:,None]*v; self.bq=u.T@r; orth=float(r@r-self.bq@self.bq); assert orth>=-1e-8*max(float(r@r),1.)
        self.const=np.sqrt(max(orth,0.)); self.initial=dict(cost=float(r@r/2),lambda_strength=float(lam),translation_trace=float(np.sum(j[:,3:]**2)),
            singular_values=s.tolist(),support=info['support'],directed_points=info['directed_points'])
        rq,jq=self.quadratic(self.z0); errs=[abs(float(rq@rq-r@r))/max(float(r@r),1.),
             float(np.linalg.norm(jq.T@rq-j.T@r)/max(np.linalg.norm(j.T@r),1.)),
             float(np.linalg.norm(jq.T@jq-j.T@j)/max(np.linalg.norm(j.T@j),1.))]
        assert max(errs)<=1e-8,errs
        self.initial['quadratic_equivalence']=errs
    def quadratic(self,z):
        h=np.zeros((6,6),order='F'); x=gtsam.Pose3.Logmap(gtsam.Pose3(inv(self.z0)@z),h)
        return np.r_[self.A@x+self.bq,self.const],np.vstack([self.A@h,np.zeros((1,6))])
    def callback(self,arm,i,j):
        def call(f,values,H):
            z=inv(values.atPose3(i).matrix())@values.atPose3(j).matrix()
            if arm=='D': rr,jj,_=self.residual(z,H is not None)
            else: rr,jj=self.quadratic(z)
            if H is not None:
                H[0]=np.asfortranarray(jj@(-adj(inv(z)))); H[1]=np.asfortranarray(jj)
            return rr
        return call

def synthetic():
    verify(); rng=np.random.default_rng(20261020); a=rng.normal(size=(96,3))*2
    z=exp([.03,-.02,.01,.1,-.2,.05]); b=(a-z[:3,3])@z[:3,:3]
    test=z@exp([.002,-.001,.001,.006,-.005,.004]); m=Matching(a,b,test); m.prepare(.5)
    r,j,_=m.residual(test); zero=m.residual(z,False)[0]; assert np.linalg.norm(zero)<=1e-10
    fd=[]; eps=1e-6
    for k in range(6):
        d=np.eye(6)[k]*eps; fd.append((m.residual(test@exp(d),False)[0]-m.residual(test@exp(-d),False)[0])/(2*eps))
    delta=float(np.max(abs(j-np.column_stack(fd)))); assert delta<=2e-5,delta
    # Explicit outlier and Huber-tail derivative coverage.
    tail=Matching(a,b,test@exp([0,0,0,.7,0,0])); tail.prepare(.5)
    ti=tail.residual(tail.z0); tfd=[]
    for k in range(6):
        d=np.eye(6)[k]*eps; tfd.append((tail.residual(tail.z0@exp(d),False)[0]-tail.residual(tail.z0@exp(-d),False)[0])/(2*eps))
    terr=float(np.max(abs(ti[1]-np.column_stack(tfd)))); assert terr<=2e-5,terr
    fixture=dict(a=a,b=b,truth=z,test=test,tail=tail.z0,initial_r=r,initial_j=j,A=m.A,bq=m.bq,const=m.const,scale=m.scale)
    np.savez(BASE/'synthetic.npz',**fixture)
    from rap_slam.pose_graph import optimize_pose_graph
    o=[np.eye(4),exp([.01,.02,0,.4,.1,0]),exp([.02,.03,0,.8,.2,0])]
    no=optimize_pose_graph(o,[0,1,2],[]); noerr=max(float(np.max(abs(no[k]-o[k]))) for k in no); assert noerr<=1e-8
    # Known-transform recovery, one pose anchored, same factor callback as real D.
    graph=gtsam.NonlinearFactorGraph(); vals=gtsam.Values(); vals.insert(0,gtsam.Pose3()); vals.insert(1,gtsam.Pose3(test))
    graph.add(gtsam.PriorFactorPose3(0,gtsam.Pose3(),gtsam.noiseModel.Isotropic.Sigma(6,1e-6)))
    graph.add(gtsam.CustomFactor(gtsam.noiseModel.Isotropic.Sigma(len(r),1.),[0,1],m.callback('D',0,1)))
    params=gtsam.LevenbergMarquardtParams(); params.setMaxIterations(50)
    fit=gtsam.LevenbergMarquardtOptimizer(graph,vals,params).optimize(); recovery=float(np.max(abs(fit.atPose3(1).matrix()-z))); assert recovery<=1e-5
    save(BASE/'synthetic.json',dict(utc=now(),passed=True,derivative_max=delta,tail_derivative_max=terr,no_loop_noop=noerr,recovery_max=recovery,initial=m.initial))
    print('synthetic passed',delta,terr,recovery,flush=True)

def make_graph(o,kf,records,initial,objects,arm):
    graph=gtsam.NonlinearFactorGraph(); vals=gtsam.Values()
    for i in kf: vals.insert(i,gtsam.Pose3(initial[i]))
    graph.add(gtsam.PriorFactorPose3(0,gtsam.Pose3(o[0]),gtsam.noiseModel.Isotropic.Sigma(6,.01)))
    noise=gtsam.noiseModel.Diagonal.Sigmas(np.array([.05]*3+[.30]*3))
    for a,b in zip(kf[:-1],kf[1:]): graph.add(gtsam.BetweenFactorPose3(a,b,gtsam.Pose3(inv(o[a])@o[b]),noise))
    for row,m in zip(records,objects):
        n=len(m.residual(m.z0,False)[0]) if arm=='D' else 7
        graph.add(gtsam.CustomFactor(gtsam.noiseModel.Isotropic.Sigma(n,1.),[row['i'],row['j']],m.callback(arm,row['i'],row['j'])))
    initial_error=graph.error(vals); params=gtsam.LevenbergMarquardtParams(); params.setMaxIterations(50)
    opt=gtsam.LevenbergMarquardtOptimizer(graph,vals,params); result=opt.optimize(); final_error=graph.error(result)
    assert final_error<=initial_error+1e-7,(arm,initial_error,final_error)
    out={k:result.atPose3(k).matrix() for k in kf}
    return out,dict(iterations=opt.iterations(),initial_error=initial_error,final_error=final_error,nodes=len(kf),factors=graph.size(),matching_callback_calls=sum(m.calls for m in objects))

def bank():
    verify(); assert read(BASE/'synthetic_validation.json')['passed']; dest=BASE/'bank'; dest.mkdir(); started=now(); execution={}
    from rap_slam.pose_graph import optimize_pose_graph,propagate_to_full_trajectory
    for s in SEQS:
        d=dest/s; d.mkdir(); raw=load(src(s)/'odom_poses.txt'); o=proper(raw); kf=read(src(s)/'keyframes.json'); rec=loops(s)
        assert len(rec)==12 and kf[0]==0 and kf[-1]==len(o)-1
        rz=proper(np.array([r['T_rel'] for r in rec]))
        for r,z in zip(rec,rz): r['T_rel']=z.tolist()
        b=np.asarray(propagate_to_full_trajectory(list(o),kf,optimize_pose_graph(list(o),kf,rec)))
        delta=float(np.max(abs(b-load(src(s)/'optimized_poses.txt')))); assert delta<=1e-3,delta
        np.save(d/'B.npy',b); objects=[]
        for row in rec:
            a=np.load(pointpath(s,row['i']),allow_pickle=False)['points'].astype(float)
            bb=np.load(pointpath(s,row['j']),allow_pickle=False)['points'].astype(float)
            assert a.shape==bb.shape==(4000,3)
            m=Matching(a,bb,inv(b[row['i']])@b[row['j']]); m.prepare(row['mean_dist']); objects.append(m)
        save(d/'initial_factors.json',[m.initial for m in objects]); save(d/'loops.json',rec)
        save(d/'frames.json',dict(source_frame_ids=read(src(s)/'source_frames.json')['source_frame_ids'],keyframes=kf))
        execution[s]={'baseline_replay_max_delta':delta}
        for arm in ('Q','D'):
            for m in objects: m.calls=0
            begin=time.monotonic(); opt,info=make_graph(o,kf,rec,b,objects,arm)
            out=np.asarray(propagate_to_full_trajectory(list(o),kf,opt)); proper(out); np.save(d/f'{arm}.npy',out)
            info['wall_seconds']=time.monotonic()-begin; execution[s][arm]=info
            cap(); print('bank',s,arm,info,flush=True)
        cap()
    save(dest/'execution.json',dict(started_utc=started,utc=now(),rows=execution))
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}))
    verify(); print('Complete 00/05 prediction bank sealed before GT',flush=True)
def verify_bank():
    verify(); seal=read(BASE/'bank_seal.json'); assert seal['freeze_sha256']==sha(BASE/'freeze.json')
    for p,h in seal['files'].items(): assert sha(BASE/'bank'/p)==h

def gates(rows):
    means={a:{k:float(np.mean([rows[s][a][k] for s in SEQS])) for k in ('ate','ter','rer')} for a in ('B','Q','D')}; tests={}
    for c in ('B','Q'):
        tests[f'{c}_ATE_gain_5pct']=means['D']['ate']<=.95*means[c]['ate']+1e-10
        for s in SEQS:
            tests[f'{s}_{c}_ATE_improves']=rows[s]['D']['ate']<rows[s][c]['ate']
            tests[f'{s}_{c}_ATE_harm5pct']=rows[s]['D']['ate']<=1.05*rows[s][c]['ate']+1e-10
            for k in ('ter','rer'): tests[f'{s}_{c}_{k}_harm']=rows[s]['D'][k]<=rows[s][c][k]+.01+1e-10
    for k in ('ter','rer'): tests[f'B_mean_{k}_nonworse']=means['D'][k]<=means['B'][k]+1e-10
    return dict(means=means,tests=tests,passed=all(tests.values()))
def evaluate():
    verify_bank(); assert read(BASE/'bank_validation.json')['passed']; started=now(); out=BASE/'evaluation'; out.mkdir()
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    rows={}
    for s in SEQS:
        gt=np.asarray(load_gt_poses(str(DATA/f'poses/{s}.txt'),str(DATA/f'sequences/{s}/calib.txt'),apply_calib=True))
        tr=_read_calib_transform(str(DATA/f'sequences/{s}/calib.txt')); ti=np.linalg.inv(tr); rows[s]={}; (out/s).mkdir()
        ids=read(BASE/f'bank/{s}/frames.json')['source_frame_ids']; assert ids==list(range(len(gt)))
        for a in ('B','Q','D'):
            est=np.load(BASE/f'bank/{s}/{a}.npy'); lidar=epm.evaluate_pair(list(gt),list(est),ids); camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@est@ti),ids)
            rows[s][a]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segments=camera['kitti_segments'])
            save(out/s/f'{a}_segments.json',camera['kitti_segment_records'])
    save(BASE/'results.json',dict(utc=now(),gt_read_started_utc=started,bank_seal_sha256=sha(BASE/'bank_seal.json'),rows=rows,gate=gates(rows)))
    print(json.dumps(rows),flush=True)

def run(stage):
    remaining=1800-used(); assert remaining>0
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('DMF cumulative enclosing cap')))
    signal.alarm(max(1,int(remaining))); ok=False; error=None
    try:
        cap()
        if stage=='component': component()
        else:
            imports()
            if stage.startswith('validate_'):
                import validate_direct_matching_factors as v
                {'validate_synthetic':v.synthetic,'validate_bank':v.bank,'validate_metrics':v.metrics}[stage]()
            else: {'freeze':freeze,'synthetic':synthetic,'bank':bank,'evaluate':evaluate}[stage]()
        cap(); ok=True
    except BaseException as e:
        error=repr(e); traceback.print_exc(); save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error))
    finally:
        signal.alarm(0); save(SUP/stage/'child_exit.json',dict(utc=now(),success=ok,error=error,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok: sys.exit(1)
if __name__=='__main__': run(sys.argv[1])
