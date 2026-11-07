"""SGC0 isolated CPU graph experiment; production sources and historical files read-only."""
import hashlib
import importlib.metadata
import json
import resource
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import gtsam
import numpy as np

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / 'RAP-SLAM'
BASE = MAIN / 'docs/maintenance/2026-10-12/scan-level-graph-feasibility-01'
DATA = MAIN.parent / 'Datasets/data_odometry_velodyne/dataset'
BANK = BASE / 'bank'
SUP = BASE / 'supervision'
SEQS = dict(zip(('00','05','06','07','09','10'), (4541,2761,1101,1101,1591,1201)))
C = np.diag([.05**2]*3 + [.30**2]*3)
sys.path[:0] = [str(SLAM), str(SLAM/'scripts')]
from rap_slam.pose_graph import optimize_pose_graph, propagate_to_full_trajectory


def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for part in iter(lambda:f.read(1048576), b''): h.update(part)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def src(s):
    folder='2026-09-26/e0-frontend-01' if s in tuple(SEQS)[:3] else '2026-09-27/e0-heldout-01'
    return MAIN/'docs/maintenance'/folder/f'full-{s}-A'
def load(p):
    a=np.loadtxt(p); out=np.repeat(np.eye(4)[None],len(a),axis=0); out[:,:3]=a.reshape(-1,3,4); return out
def skew(x):
    a,b,c=x; return np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])
def adj(t):
    out=np.zeros((6,6)); out[:3,:3]=out[3:,3:]=t[:3,:3]; out[3:,:3]=skew(t[:3,3])@t[:3,:3]; return out
def inv(t):
    out=np.eye(4); out[:3,:3]=t[:3,:3].T; out[:3,3]=-t[:3,:3].T@t[:3,3]; return out
def proper(a):
    a=np.asarray(a); r=a[...,:3,:3]
    assert np.isfinite(a).all() and np.max(abs(r.swapaxes(-1,-2)@r-np.eye(3)))<=1e-5
    assert np.max(abs(np.linalg.det(r)-1))<=1e-5 and np.max(abs(a[...,3,:]-[0,0,0,1]))<=1e-12
    u,_,vt=np.linalg.svd(r); d=np.repeat(np.eye(3)[None],len(a),axis=0); d[:,-1,-1]=np.linalg.det(u@vt)
    out=a.copy(); out[:,:3,:3]=u@d@vt
    assert np.max(abs(out-a))<=1e-5
    return out
def normalized(a,b): return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
def rels(o): return np.asarray([inv(a)@b for a,b in zip(o[:-1],o[1:])])
def allocate(o,kf):
    cov=np.empty((len(o)-1,6,6)); largest=0.
    for a,b in zip(kf[:-1],kf[1:]):
        total=np.zeros((6,6))
        for i in range(a,b):
            q=inv(o[i+1])@o[b]; ad=adj(q); ci=ad@C@ad.T/(b-a); cov[i]=(ci+ci.T)/2
            ai=adj(inv(q)); total+=ai@ci@ai.T
        largest=max(largest,normalized(total,C))
    assert largest<=5e-8
    return cov,largest
def loop_records(s,normalize=False):
    rows=[{k:r[k] for k in ('i','j','T_rel','overlap','mean_dist','measurement_id') if k in r} for r in read(src(s)/'accepted_loops.json')]
    if normalize and rows:
        matrices=proper(np.asarray([r['T_rel'] for r in rows]))
        for r,t in zip(rows,matrices): r['T_rel']=t.tolist()
    return rows
def native(o,kf,loops):
    opt=optimize_pose_graph(list(o),kf,loops)
    return np.asarray(propagate_to_full_trajectory(list(o),kf,opt))
def scan(o,cov,loops,initial=None):
    graph=gtsam.NonlinearFactorGraph(); values=gtsam.Values()
    for i,t in enumerate(o if initial is None else initial): values.insert(i,gtsam.Pose3(t))
    graph.add(gtsam.PriorFactorPose3(0,gtsam.Pose3(o[0]),gtsam.noiseModel.Diagonal.Sigmas(np.full(6,.01))))
    for i,(z,ci) in enumerate(zip(rels(o),cov)):
        graph.add(gtsam.BetweenFactorPose3(i,i+1,gtsam.Pose3(z),gtsam.noiseModel.Gaussian.Covariance(ci)))
    for r in loops:
        scale=float(np.clip(r.get('mean_dist',.5),1,3))
        noise=gtsam.noiseModel.Diagonal.Sigmas(np.array([.03]*3+[.20]*3)*scale)
        noise=gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber(1.),noise)
        graph.add(gtsam.BetweenFactorPose3(r['i'],r['j'],gtsam.Pose3(r['T_rel']),noise))
    params=gtsam.LevenbergMarquardtParams(); params.setMaxIterations(100)
    optimizer=gtsam.LevenbergMarquardtOptimizer(graph,values,params); result=optimizer.optimize()
    out=np.asarray([result.atPose3(i).matrix() for i in range(len(o))])
    diagnostic=dict(nodes=len(o),factors=graph.size(),iterations=optimizer.iterations(),initial_error=graph.error(values),final_error=graph.error(result))
    assert diagnostic['final_error']<=diagnostic['initial_error']+1e-9
    return out,diagnostic
def old_identities():
    rows=read(MAIN/'docs/maintenance/2026-10-12/stage-review-01/IDENTITY_CHECKS.json')
    unique={}
    for row in rows:
        p=row['path'].replace('E:\\','/mnt/e/').replace('\\','/')
        unique[p]=row['sha256']
    for p,h in unique.items(): assert sha(p)==h,p
    return unique
def repositories():
    out={}
    for name,p in [('main',MAIN),('slam',SLAM)]:
        def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*args],text=True).strip()
        out[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
    return out
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')}
    assert f['repositories']==repositories()
    return f
def freeze():
    old=old_identities()
    paths=[BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',Path(__file__),Path(__file__).with_name('validate_scan_level_graph.py'),
           Path(__file__).with_name('invoke_supervised_wsl_current.ps1'),SLAM/'rap_slam/pose_graph.py',SLAM/'rap_slam/real_dataset.py',
           SLAM/'rap_slam/trajectory_protocol.py',SLAM/'rap_slam/evaluate.py',SLAM/'scripts/eval_paper_metrics.py',
           MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01/results.json',
           MAIN/'docs/maintenance/2026-10-12/stage-review-01/IDENTITY_CHECKS.json']
    for s in SEQS:
        paths += [src(s)/x for x in ('odom_poses.txt','optimized_poses.txt','keyframes.json','accepted_loops.json','source_frames.json','summary.json')]
        paths += [DATA/'poses'/f'{s}.txt',DATA/'sequences'/s/'calib.txt',DATA/'sequences'/s/'times.txt']
    for p in paths: old[str(p)]=sha(p)
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'): (snapshot/p.name).write_bytes(p.read_bytes())
    f=dict(utc=now(),files=old,packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')},
           python=sys.version,repositories=repositories(),cohort=SEQS,cap_seconds=900,cap_rss_bytes=4*2**30,cap_artifact_bytes=512*2**20)
    save(BASE/'freeze.json',f); (BASE/'INCOMPLETE').write_text('SGC0 prospective experiment pending numerical gates and validation.\n')
    print('SGC0 frozen',len(old),'identities',flush=True)
def schur(o,cov):
    m=len(o)-1; h=np.zeros((6*(m+1),6*(m+1)))
    for i,(z,ci) in enumerate(zip(rels(o),cov)):
        j=np.column_stack([-adj(inv(z)),np.eye(6)]); part=j.T@np.linalg.solve(ci,j); ids=np.arange(6*i,6*(i+2)); h[np.ix_(ids,ids)]+=part
    ends=np.r_[np.arange(6),np.arange(6*m,6*(m+1))]; internal=np.arange(6,6*m)
    s=h[np.ix_(ends,ends)]
    if len(internal): s-=h[np.ix_(ends,internal)]@np.linalg.solve(h[np.ix_(internal,internal)],h[np.ix_(internal,ends)])
    z=inv(o[0])@o[-1]; j=np.column_stack([-adj(inv(z)),np.eye(6)])
    return s,j.T@np.linalg.solve(C,j)
def preflight():
    verify(); rng=np.random.default_rng(20261012); cases=[]
    for m in (1,2,5,9,1,2,5,9):
        o=[gtsam.Pose3.Expmap(rng.normal(size=6)*.2).matrix()]
        for i in range(m):
            w=rng.normal(size=6)*np.array([.08]*3+[.5]*3); o.append(o[-1]@gtsam.Pose3.Expmap(w).matrix())
        o=np.asarray(o); cov,ce=allocate(o,[0,m]); hs,hk=schur(o,cov); se=normalized(hs,hk); assert se<=5e-8
        no,nd=scan(o,cov,[]); noerr=float(np.max(abs(no-o))); assert noerr<=1e-5
        loops=[dict(i=0,j=m,T_rel=(inv(o[0])@o[-1]).tolist(),mean_dist=.5)]
        initial=np.asarray([t@gtsam.Pose3.Expmap(rng.normal(size=6)*.01).matrix() for t in o])
        fit,fd=scan(o,cov,loops,initial); perfect=float(np.max(abs(fit-o))); assert perfect<=1e-5
        g=gtsam.Pose3.Expmap(rng.normal(size=6)*.3).matrix(); go=g@o
        gc,_=allocate(go,[0,m]); gout,_=scan(go,gc,loops,g@initial); gauge=float(np.max(abs(gout-g@fit))); assert gauge<=1e-5
        perturb=rng.normal(size=(m,6)); h=1e-6; changed=np.eye(4); minus=np.eye(4); predicted=np.zeros(6)
        for i,z in enumerate(rels(o)):
            changed=changed@z@gtsam.Pose3.Expmap(h*perturb[i]).matrix(); minus=minus@z@gtsam.Pose3.Expmap(-h*perturb[i]).matrix()
            q=inv(o[i+1])@o[-1]; predicted+=adj(inv(q))@perturb[i]
        endpoint=inv(o[0])@o[-1]
        observed=(gtsam.Pose3.Logmap(gtsam.Pose3(inv(endpoint)@changed))-gtsam.Pose3.Logmap(gtsam.Pose3(inv(endpoint)@minus)))/(2*h)
        derivative=float(np.max(abs(observed-predicted))); assert derivative<=2e-6
        cases.append(dict(poses=o.tolist(),covariances=cov.tolist(),schur=hs.tolist(),direct=hk.tolist(),covariance_relative_error=ce,
              schur_relative_error=se,no_loop_error=noerr,perfect_error=perfect,gauge_error=gauge,derivative_error=derivative,
              perturbations=perturb.tolist(),predicted_derivative=predicted.tolist(),observed_derivative=observed.tolist(),
              perfect_initial=initial.tolist(),perfect_output=fit.tolist(),gauge=g.tolist(),gauge_output=gout.tolist()))
    source=[]
    for s,n in SEQS.items():
        frames=read(src(s)/'source_frames.json'); kf=read(src(s)/'keyframes.json'); o=load(src(s)/'odom_poses.txt')
        assert frames['source_frame_ids']==list(range(n)) and o.shape==(n,4,4) and kf==sorted(set(kf)) and kf[0]==0 and kf[-1]==n-1
        times=np.loadtxt(DATA/'sequences'/s/'times.txt'); assert np.array_equal(times,np.asarray(frames['timestamps'])) and np.all(np.diff(times)>0)
        loops=loop_records(s); assert all(r['i'] in kf and r['j'] in kf and r['i']<r['j'] for r in loops)
        po=proper(o); cv,ce=allocate(po,kf)
        source.append(dict(seq=s,scans=n,keyframes=len(kf),loops=len(loops),max_projection=float(np.max(abs(po-o))),covariance_error=ce,
                           covariance_min_eigenvalue=float(np.linalg.eigvalsh(cv).min())))
    # Transported endpoint-frame increments with equicorrelation rho=.25:
    # endpoint variance is [1+(m-1)rho] C rather than C.
    correlation=[dict(span=m,rho=.25,variance_multiplier=1+(m-1)*.25) for m in (2,5,9)]
    save(BASE/'preflight.json',dict(utc=now(),cases=cases,source_census=source,correlation_counterexample=correlation))
    print('synthetic preflight and fixed input census complete',flush=True)
def diagnostics(o,b,s,kf):
    out={}
    for arm,t in [('B',b),('S',s)]:
        corr=np.asarray([x@inv(y) for x,y in zip(t,o)]); z=rels(corr); local=rels(t); original=rels(o)
        correction=np.asarray([gtsam.Pose3.Logmap(gtsam.Pose3(v)) for v in z])
        motion=np.asarray([gtsam.Pose3.Logmap(gtsam.Pose3(inv(a)@v)) for a,v in zip(original,local)])
        out[arm]=dict(correction_max_t=float(np.linalg.norm(correction[:,3:],axis=1).max()),correction_max_r_deg=float(np.degrees(np.linalg.norm(correction[:,:3],axis=1)).max()),
            adjacent_change_max_t=float(np.linalg.norm(motion[:,3:],axis=1).max()),adjacent_change_max_r_deg=float(np.degrees(np.linalg.norm(motion[:,:3],axis=1)).max()),
            boundary_max_t=float(np.linalg.norm(correction[np.asarray(kf[1:])-1,3:],axis=1).max()))
    delta=np.asarray([gtsam.Pose3.Logmap(gtsam.Pose3(inv(a)@v)) for a,v in zip(b[kf],s[kf])])
    out['keyframe_B_S_max_t']=float(np.linalg.norm(delta[:,3:],axis=1).max()); out['keyframe_B_S_max_r_deg']=float(np.degrees(np.linalg.norm(delta[:,:3],axis=1)).max())
    return out
def bank():
    verify(); assert read(BASE/'preflight_validation.json')['passed']; BANK.mkdir(); rows={}; started=now()
    for s,n in SEQS.items():
        d=BANK/s; d.mkdir(); raw=load(src(s)/'odom_poses.txt'); p=load(src(s)/'optimized_poses.txt'); kf=read(src(s)/'keyframes.json')
        o=proper(raw); loops=loop_records(s,True); cov,ce=allocate(o,kf)
        r=native(raw,kf,loop_records(s)); rawdelta=float(np.max(abs(r-p))); assert rawdelta<=1e-3,(s,rawdelta)
        b=native(o,kf,loops)
        rb_t=float(np.max(np.linalg.norm(b[:,:3,3]-r[:,:3,3],axis=1)))
        rb_r=float(np.degrees(np.linalg.norm(np.asarray([gtsam.Rot3.Logmap(gtsam.Rot3(proper(np.asarray([a]))[0,:3,:3].T@v[:3,:3])) for a,v in zip(r,b)]),axis=1)).max())
        assert rb_t<=.01 and rb_r<=.001,(s,rb_t,rb_r)
        ss,sd=scan(o,cov,loops); proper(ss)
        if s=='10': assert not loops and np.max(abs(ss-o))<=1e-5 and np.max(abs(b-ss))<=1e-5
        for arm,t in [('O',raw),('P',p),('R',r),('B',b),('S',ss)]: np.save(d/f'{arm}.npy',t)
        np.save(d/'covariances.npy',cov); save(d/'frames.json',dict(source_frame_ids=list(range(n)),keyframes=kf))
        save(d/'loops.json',loops); save(d/'diagnostics.json',diagnostics(o,b,ss,kf))
        rows[s]=dict(raw_replay_max_delta=rawdelta,B_R_max_translation=rb_t,B_R_max_rotation_deg=rb_r,nominal_covariance_error=ce,
                     B_nodes=len(kf),B_factors=len(kf)+len(loops),S=sd)
        cap(); print('bank',s,rows[s],flush=True)
    save(BANK/'execution.json',dict(started_utc=started,utc=now(),rows=rows)); verify()
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(BANK)):sha(p) for p in sorted(BANK.rglob('*')) if p.is_file()}))
    print('all-six GT-free trajectory bank sealed',flush=True)
def verify_bank():
    verify(); f=read(BASE/'bank_seal.json'); assert f['freeze_sha256']==sha(BASE/'freeze.json')
    assert set(f['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in f['files'].items(): assert sha(BANK/p)==h,p
def gate(rows,means):
    checks={}
    for control in ('B','R'):
        checks[control+'_mean_ATE_gain5pct']=means['all'][control]['ate']*.95>=means['all']['S']['ate']
        for metric in ('ter','rer'): checks[control+'_mean_'+metric+'_nonworse']=means['all']['S'][metric]<=means['all'][control][metric]+1e-10
        for s in SEQS:
            checks[s+'_'+control+'_ATE_guard']=rows[s]['S']['ate']<=1.05*rows[s][control]['ate']
            for metric in ('ter','rer'): checks[s+'_'+control+'_'+metric+'_guard']=rows[s]['S'][metric]-rows[s][control][metric]<=.01
    for s in SEQS:
        for metric in ('ate','ter','rer'): checks[s+'_normalization_'+metric]=abs(rows[s]['B'][metric]-rows[s]['R'][metric])<=.001
    checks['10_no_op']=float(np.max(abs(np.load(BANK/'10/S.npy')-np.load(BANK/'10/B.npy'))))<=1e-5
    return dict(tests=checks,passed=all(checks.values()),decision='SCAN_GRAPH_ENGINEERING_SIGNAL' if all(checks.values()) else 'NO_SAFE_MATERIAL_SCAN_GRAPH_SIGNAL')
def evaluate():
    verify_bank(); ev=BASE/'evaluation'; ev.mkdir(); started=now()
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    rows={}; old=read(MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01/results.json')
    for s,n in SEQS.items():
        (ev/s).mkdir(); calib=DATA/'sequences'/s/'calib.txt'; gt=np.asarray(load_gt_poses(str(DATA/'poses'/f'{s}.txt'),str(calib),apply_calib=True))
        tr=_read_calib_transform(str(calib)); ti=np.linalg.inv(tr); ids=read(BANK/s/'frames.json')['source_frame_ids']; assert gt.shape==(n,4,4)
        rows[s]={}
        for arm in ('O','P','R','B','S'):
            t=np.load(BANK/s/f'{arm}.npy'); lidar=epm.evaluate_pair(list(gt),list(t),ids); camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),ids)
            rows[s][arm]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segments=camera['kitti_segments'])
            save(ev/s/f'{arm}_segments.json',camera['kitti_segment_records'])
            if arm=='P':
                for key in ('ate','ter','rer'): assert abs(rows[s][arm][key]-old['rows'][s]['full'][key])<=1e-5
        cap(); print('evaluated',s,rows[s]['S'],flush=True)
    groups=dict(development=tuple(SEQS)[:3],transfer_exposed=tuple(SEQS)[3:],all=tuple(SEQS))
    means={g:{a:{k:float(np.mean([rows[s][a][k] for s in seqs])) for k in ('ate','ter','rer')} for a in ('O','P','R','B','S')} for g,seqs in groups.items()}
    result=dict(utc=now(),gt_read_started_utc=started,bank_seal_sha256=sha(BASE/'bank_seal.json'),rows=rows,means=means,gate=gate(rows,means))
    save(BASE/'results.json',result); print(result['gate'],flush=True)
def usage(start):
    return dict(wall_seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),GPU_calls=0)
def cap():
    assert usage(START)['peak_RSS_bytes']<=4*2**30
    assert usage(START)['artifact_bytes']<=512*2**20
    host=SUP/'host_latest.json'
    if host.exists(): assert read(host)['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic(); log=SUP/stage; prior=list(SUP.glob('*/child_exit.json'))
    used=sum(read(p)['wall_seconds'] for p in prior); assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('SGC0 combined payload cap'))); signal.alarm(max(1,int(900-used)))
    ok=False; error=None
    try:
        cap()
        if stage in ('validate_preflight','validate'):
            import validate_scan_level_graph as v
            {'validate_preflight':v.preflight,'validate':v.validate}[stage]()
        else: {'freeze':freeze,'preflight':preflight,'bank':bank,'evaluate':evaluate}[stage]()
        cap(); ok=True
    except BaseException as e:
        error=repr(e); traceback.print_exc()
        save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error,**usage(START)))
    finally:
        signal.alarm(0); save(log/'child_exit.json',dict(utc=now(),success=ok,error=error,full_resource_capture=True,**usage(START)))
    if not ok: sys.exit(1)

if __name__=='__main__': run(sys.argv[1])
