"""Independent SGC0 adjoints, SciPy Lie derivatives, Horn/segment metrics and gates.

S optimizer replay shares the frozen experiment routine; no independent GTSAM solver claim.
"""
import hashlib
import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-10-12/scan-level-graph-feasibility-01'
BANK=BASE/'bank'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
SEQS=('00','05','06','07','09','10')
C=np.diag([.0025]*3+[.09]*3)

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def write(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def stamp(): return datetime.now(timezone.utc).isoformat()
def hat(w):
    x,y,z=w; return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
def transport(t):
    r=t[:3,:3]; return np.block([[r,np.zeros((3,3))],[hat(t[:3,3])@r,r]])
def left_jac(w):
    theta=np.linalg.norm(w); k=hat(w)
    if theta<1e-5: a=.5-theta**2/24+theta**4/720; b=1/6-theta**2/120+theta**4/5040
    else: a=(1-np.cos(theta))/theta**2; b=(theta-np.sin(theta))/theta**3
    return np.eye(3)+a*k+b*k@k
def exp(x):
    t=np.eye(4); t[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix(); t[:3,3]=left_jac(x[:3])@x[3:]; return t
def log(t):
    w=Rotation.from_matrix(t[:3,:3]).as_rotvec(); return np.r_[w,np.linalg.solve(left_jac(w),t[:3,3])]
def canonical(a):
    a=a.copy()
    for t in a:
        u,_,v=np.linalg.svd(t[:3,:3]); t[:3,:3]=u@np.diag([1.,1.,np.linalg.det(u@v)])@v
    return a
def close(a,b,tol=1e-8):
    a=np.asarray(a); b=np.asarray(b); assert np.isfinite(a).all() and np.isfinite(b).all()
    assert np.max(abs(a-b))<=tol,(np.max(abs(a-b)),tol)
def normerr(a,b): return float(np.linalg.norm(a-b)/np.linalg.norm(b))
def verify_freeze():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')}
    return f
def covariances(o,kf,stored):
    largest=0.; aggregate=0.
    for a,b in zip(kf[:-1],kf[1:]):
        total=np.zeros((6,6))
        for i in range(a,b):
            q=np.linalg.solve(o[i+1],o[b]); ad=transport(q); expected=ad@C@ad.T/(b-a)
            largest=max(largest,normerr(stored[i],expected)); ai=np.linalg.inv(ad); total+=ai@stored[i]@ai.T
            assert np.linalg.eigvalsh(stored[i]).min()>0
        aggregate=max(aggregate,normerr(total,C))
    assert max(largest,aggregate)<=5e-8
    return largest,aggregate
def preflight():
    freeze=verify_freeze(); record=read(BASE/'preflight.json'); assert freeze['utc']<record['utc']; assert len(record['cases'])==8
    largest_fd=largest_schur=largest_composition=largest_reverse=0.
    for case in record['cases']:
        o=np.asarray(case['poses']); m=len(o)-1; cv=np.asarray(case['covariances']); covariances(o,[0,m],cv)
        h=np.zeros((6*(m+1),6*(m+1))); analytic=h.copy()
        for i in range(m):
            z=np.linalg.solve(o[i],o[i+1]); jac=np.zeros((6,12)); eps=1e-6
            for j in range(12):
                d=np.eye(6)[j%6]*eps
                def residual(sign):
                    a=o[i]@(exp(sign*d) if j<6 else np.eye(4)); b=o[i+1]@(exp(sign*d) if j>=6 else np.eye(4))
                    return log(np.linalg.solve(z,np.linalg.solve(a,b)))
                jac[:,j]=(residual(1)-residual(-1))/(2*eps)
            exact=np.column_stack([-transport(np.linalg.inv(z)),np.eye(6)])
            largest_fd=max(largest_fd,float(np.max(abs(jac-exact)))); close(jac,exact,2e-6)
            indices=np.arange(6*i,6*(i+2)); h[np.ix_(indices,indices)]+=jac.T@np.linalg.solve(cv[i],jac)
            analytic[np.ix_(indices,indices)]+=exact.T@np.linalg.solve(cv[i],exact)
            # Reversing an edge transforms right covariance by Ad(Z).
            reverse=transport(z)@cv[i]@transport(z).T; back=transport(np.linalg.inv(z))@reverse@transport(np.linalg.inv(z)).T
            largest_reverse=max(largest_reverse,normerr(back,cv[i])); assert normerr(back,cv[i])<=5e-8
        ends=np.r_[np.arange(6),np.arange(6*m,6*(m+1))]; mid=np.arange(6,6*m)
        def marginal(mat):
            value=mat[np.ix_(ends,ends)].copy()
            if len(mid): value-=mat[np.ix_(ends,mid)]@np.linalg.solve(mat[np.ix_(mid,mid)],mat[np.ix_(mid,ends)])
            return value
        z=np.linalg.solve(o[0],o[-1]); j=np.column_stack([-transport(np.linalg.inv(z)),np.eye(6)]); expected=j.T@np.linalg.solve(C,j)
        err=normerr(marginal(h),expected); largest_schur=max(largest_schur,err); assert err<=5e-8
        close(marginal(analytic),case['schur'],2e-7); close(expected,case['direct'],2e-7)
        vectors=np.asarray(case['perturbations']); predicted=np.zeros(6); central=[]
        for sign in (1,-1):
            product=np.eye(4)
            for i in range(m): product=product@np.linalg.solve(o[i],o[i+1])@exp(sign*1e-6*vectors[i])
            central.append(log(np.linalg.solve(z,product)))
        for i in range(m): predicted+=transport(np.linalg.solve(o[-1],o[i+1]))@vectors[i]
        observed=(central[0]-central[1])/2e-6; e=float(np.max(abs(observed-predicted))); largest_composition=max(largest_composition,e)
        close(observed,predicted,2e-6); close(observed,case['observed_derivative'],2e-6); close(predicted,case['predicted_derivative'],2e-8)
        close(np.asarray(case['perfect_output']),o,1e-5)
        close(np.asarray(case['gauge_output']),np.asarray(case['gauge'])@np.asarray(case['perfect_output']),1e-5)
        assert case['no_loop_error']<=1e-5
    for row in record['correlation_counterexample']:
        m=row['span']; rho=row['rho']; corr=(1-rho)*np.eye(m)+rho*np.ones((m,m))
        assert np.linalg.eigvalsh(corr).min()>0
        close(np.sum(corr)/m,row['variance_multiplier'],1e-12); assert row['variance_multiplier']>1
    write(BASE/'preflight_validation.json',dict(utc=stamp(),passed=True,case_count=8,finite_difference_jacobian_max=largest_fd,
        finite_difference_schur_relative_max=largest_schur,composition_derivative_max=largest_composition,reverse_covariance_relative_max=largest_reverse,
        independent_method='SciPy SE3, central differences, explicit Schur elimination; stored optimized fixture endpoints, no independent LM solver'))
    print('independent synthetic numerical gates passed',flush=True)
def calibration(s):
    line=next(x for x in (DATA/'sequences'/s/'calib.txt').read_text().splitlines() if x.startswith('Tr:'))
    t=np.eye(4); t[:3]=np.asarray([float(x) for x in line.split(':',1)[1].split()]).reshape(3,4); return t
def load(p):
    a=np.loadtxt(p); t=np.tile(np.eye(4),(len(a),1,1)); t[:,:3]=a.reshape(-1,3,4); return t
def horn_rmse(gt,est):
    g=np.linalg.solve(gt[0],gt); e=np.linalg.solve(est[0],est); x=e[:,:3,3]; y=g[:,:3,3]; x=x-x.mean(0); y=y-y.mean(0)
    h=x.T@y; a=h+h.T-np.trace(h)*np.eye(3); v=np.array([h[1,2]-h[2,1],h[2,0]-h[0,2],h[0,1]-h[1,0]])
    k=np.block([[np.array([[np.trace(h)]]),v[None]],[v[:,None],a]])
    _,vectors=np.linalg.eigh(k); q=vectors[:,-1]; r=Rotation.from_quat(np.r_[q[1:],q[0]]).as_matrix()
    return float(np.sqrt(np.mean(np.sum((x@r.T-y)**2,axis=1))))
def segments(gt,est):
    g=np.linalg.solve(gt[0],gt); e=np.linalg.solve(est[0],est); distance=np.zeros(len(g))
    for i in range(1,len(g)): distance[i]=distance[i-1]+np.linalg.norm(g[i,:3,3]-g[i-1,:3,3])
    rows=[]
    for a in range(0,len(g),10):
        for length in range(100,801,100):
            b=a+1
            while b<len(g) and distance[b]<=distance[a]+length: b+=1
            if b==len(g): continue
            de=np.linalg.solve(e[a],e[b]); dg=np.linalg.solve(g[a],g[b]); error=np.linalg.solve(de,dg)
            rows.append(dict(first=a,last=b,source_first=a,source_last=b,length_m=length,
                translation_fraction=float(np.linalg.norm(error[:3,3])/length),
                rotation_rad_per_m=float(np.arccos(np.clip((np.trace(error[:3,:3])-1)/2,-1,1))/length),
                speed_mps=float(length/(.1*(b-a+1)))))
    return rows
def diagnostic(o,t,kf):
    corrections=np.asarray([x@np.linalg.inv(y) for x,y in zip(t,o)]); z=np.asarray([np.linalg.solve(a,b) for a,b in zip(corrections[:-1],corrections[1:])])
    local=np.asarray([np.linalg.solve(a,b) for a,b in zip(t[:-1],t[1:])]); original=np.asarray([np.linalg.solve(a,b) for a,b in zip(o[:-1],o[1:])])
    correction=np.asarray([log(v) for v in z]); motion=np.asarray([log(np.linalg.solve(a,b)) for a,b in zip(original,local)])
    return dict(correction_max_t=float(np.linalg.norm(correction[:,3:],axis=1).max()),correction_max_r_deg=float(np.degrees(np.linalg.norm(correction[:,:3],axis=1)).max()),
        adjacent_change_max_t=float(np.linalg.norm(motion[:,3:],axis=1).max()),adjacent_change_max_r_deg=float(np.degrees(np.linalg.norm(motion[:,:3],axis=1)).max()),
        boundary_max_t=float(np.linalg.norm(correction[np.asarray(kf[1:])-1,3:],axis=1).max()))
def validate():
    f=verify_freeze(); seal=read(BASE/'bank_seal.json'); result=read(BASE/'results.json'); started=stamp()
    assert seal['freeze_sha256']==sha(BASE/'freeze.json') and result['bank_seal_sha256']==sha(BASE/'bank_seal.json')
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items(): assert sha(BANK/p)==h,p
    assert f['utc']<read(BANK/'execution.json')['started_utc']<seal['utc']<result['gt_read_started_utc']<started
    import scan_level_graph_feasibility as r
    actual={}; maxmetric=0.; count=0; maxcov=0.; replay={}; diagmax=0.
    for s in SEQS:
        raw=load(r.src(s)/'odom_poses.txt'); o=canonical(raw); frames=read(BANK/s/'frames.json'); kf=frames['keyframes']
        assert frames['source_frame_ids']==list(range(len(raw))) and kf==read(r.src(s)/'keyframes.json')
        loops=read(BANK/s/'loops.json'); original=r.loop_records(s,True); assert loops==original
        cov=np.load(BANK/s/'covariances.npy'); errors=covariances(o,kf,cov); maxcov=max(maxcov,*errors)
        rr=r.native(raw,kf,r.loop_records(s)); bb=r.native(o,kf,loops); ss,sd=r.scan(o,cov,loops)
        deltas={a:float(np.max(abs(t-np.load(BANK/s/f'{a}.npy')))) for a,t in [('R',rr),('B',bb),('S',ss)]}
        assert max(deltas.values())<=1e-8; replay[s]=deltas
        execution=read(BANK/'execution.json')['rows'][s]; assert sd['nodes']==execution['S']['nodes'] and sd['factors']==execution['S']['factors'] and sd['iterations']==execution['S']['iterations']
        assert sd['factors']==len(raw)+len(loops) and execution['B_factors']==len(kf)+len(loops)
        dg=read(BANK/s/'diagnostics.json')
        for arm in ('B','S'):
            independent=diagnostic(o,np.load(BANK/s/f'{arm}.npy'),kf)
            for key,val in independent.items(): diagmax=max(diagmax,abs(val-dg[arm][key])); close(val,dg[arm][key],1e-7)
        delta=np.asarray([log(np.linalg.solve(a,b)) for a,b in zip(bb[kf],ss[kf])]); close(np.linalg.norm(delta[:,3:],axis=1).max(),dg['keyframe_B_S_max_t'],1e-7)
        close(np.degrees(np.linalg.norm(delta[:,:3],axis=1)).max(),dg['keyframe_B_S_max_r_deg'],1e-7)
        camera_gt=load(DATA/'poses'/f'{s}.txt'); tr=calibration(s); ti=np.linalg.inv(tr); lidar_gt=ti@camera_gt@tr; actual[s]={}
        for arm in ('O','P','R','B','S'):
            t=np.load(BANK/s/f'{arm}.npy'); seg=segments(camera_gt,tr@t@ti); recorded=read(BASE/'evaluation'/s/f'{arm}_segments.json')
            assert len(seg)==len(recorded); count+=len(seg)
            for left,right in zip(seg,recorded):
                for key in ('first','last','source_first','source_last','length_m'): assert left[key]==right[key]
                for key in ('translation_fraction','rotation_rad_per_m','speed_mps'): close(left[key],right[key],2e-10)
            values=dict(ate=horn_rmse(lidar_gt,t),ter=float(np.mean([v['translation_fraction'] for v in seg])*100),
                rer=float(np.mean([v['rotation_rad_per_m'] for v in seg])*180/np.pi*100),segments=len(seg))
            actual[s][arm]=values
            for key,val in values.items(): maxmetric=max(maxmetric,abs(val-result['rows'][s][arm][key])); close(val,result['rows'][s][arm][key],1e-8)
    groups=dict(development=SEQS[:3],transfer_exposed=SEQS[3:],all=SEQS)
    means={g:{a:{k:float(np.mean([actual[s][a][k] for s in seqs])) for k in ('ate','ter','rer')} for a in ('O','P','R','B','S')} for g,seqs in groups.items()}
    for g in means:
        for a in means[g]:
            for k in means[g][a]: close(means[g][a][k],result['means'][g][a][k],1e-8)
    tests={}
    for control in ('B','R'):
        tests[control+'_mean_ATE_gain5pct']=means['all']['S']['ate']<=.95*means['all'][control]['ate']
        for k in ('ter','rer'): tests[control+'_mean_'+k+'_nonworse']=means['all']['S'][k]-means['all'][control][k]<=1e-10
        for s in SEQS:
            tests[s+'_'+control+'_ATE_guard']=actual[s]['S']['ate']<=1.05*actual[s][control]['ate']
            for k in ('ter','rer'): tests[s+'_'+control+'_'+k+'_guard']=actual[s]['S'][k]-actual[s][control][k]<=.01
    for s in SEQS:
        for k in ('ate','ter','rer'): tests[s+'_normalization_'+k]=abs(actual[s]['B'][k]-actual[s]['R'][k])<=.001
    tests['10_no_op']=float(np.max(abs(np.load(BANK/'10/S.npy')-np.load(BANK/'10/B.npy'))))<=1e-5
    assert tests==result['gate']['tests'] and all(tests.values())==result['gate']['passed']
    verify_freeze()
    write(BASE/'validation.json',dict(utc=stamp(),passed=True,independent_segment_records=count,independent_metric_max_delta=maxmetric,
        independent_covariance_relative_max=maxcov,independent_diagnostics_max_delta=diagmax,graph_replay_max_deltas=replay,
        tests=tests,scientific_gate_passed=all(tests.values()),shared_S_optimizer_replay=True,independent_GTSAM_optimizer=False,
        raw_frontend_RAP_descriptor_replay=False))
    print('full bank, independent metrics/covariances/gates and shared graph replay validated',flush=True)
