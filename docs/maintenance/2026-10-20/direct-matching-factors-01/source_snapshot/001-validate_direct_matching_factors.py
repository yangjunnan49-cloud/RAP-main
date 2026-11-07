"""Independent brute-force matching algebra and Horn/KITTI metrics for DMF0."""
import numpy as np
from scipy.spatial.transform import Rotation
import direct_matching_factors as r
import validate_scan_level_graph as metric

r.imports()
BASE=r.BASE

def near(a,b,tol=1e-8):
    a,b=np.asarray(a),np.asarray(b); e=float(np.max(abs(a-b))); assert e<=tol,(e,tol); return e
def relative(a,b): return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1.))
def brute(q,p):
    ds=[]; ix=[]
    for k in range(0,len(q),64):
        d=np.sum((q[k:k+64,None,:]-p[None,:,:])**2,axis=2); ids=np.argmin(d,axis=1)
        ix.extend(ids); ds.extend(np.sqrt(d[np.arange(len(ids)),ids])); r.cap()
    return np.asarray(ds),np.asarray(ix)
def independent(a,b,z,scale=1.,jac=True):
    rot=z[:3,:3]; trans=z[:3,3]; forward=b@rot.T+trans; backward=(a-trans)@rot
    df,fi=brute(forward,a); db,bi=brute(backward,b); e=np.vstack([forward-a[fi],backward-b[bi]])
    d=np.r_[df,db]; good=d<=2.5; h=np.where(d<=.5,d*d,d-.25)
    f=np.ones_like(d); nonzero=d>1e-12; f[nonzero]=np.sqrt(h[nonzero])/d[nonzero]
    value=e*f[:,None]; value[~good]=[1.5,0,0]; normalizer=scale/np.sqrt(len(e)); value*=normalizer
    if not jac: return value.reshape(-1),None,float(good.mean())
    j=np.empty((len(e),3,6)); basis=np.eye(3)
    for k in range(3):
        j[:len(b),:,k]=np.cross(basis[k],b)@rot.T
        j[len(b):,:,k]=np.cross(backward,basis[k])
        j[:len(b),:,k+3]=rot[:,k]; j[len(b):,:,k+3]=-basis[k]
    coeff=np.zeros(len(d)); tail=(d>.5)&good
    coeff[tail]=1/(2*np.sqrt(h[tail])*d[tail]**2)-np.sqrt(h[tail])/d[tail]**3
    derivative=f[:,None,None]*j+coeff[:,None,None]*e[:,:,None]*np.einsum('na,nak->nk',e,j)[:,None,:]
    derivative[~good]=0; derivative*=normalizer
    return value.reshape(-1),derivative.reshape(-1,6),float(good.mean())

def synthetic():
    r.verify(); f=np.load(BASE/'synthetic.npz'); a,b,z=f['a'],f['b'],f['test']
    rr,jj,_=independent(a,b,z,float(f['scale'])); e1=near(rr,f['initial_r'],1e-8); e2=near(jj,f['initial_j'],1e-8)
    A,bq=f['A'],f['bq']; q=np.r_[bq,float(f['const'])]; jq=np.vstack([A,np.zeros((1,6))])
    errs=[relative(jq.T@q,jj.T@rr),relative(jq.T@jq,jj.T@jj),abs(float(q@q-rr@rr))/max(float(rr@rr),1.)]; assert max(errs)<=1e-8
    eps=1e-6; fd=[]
    for k in range(6):
        d=np.eye(6)[k]*eps
        fd.append((independent(a,b,z@metric.exp(d),float(f['scale']),False)[0]-independent(a,b,z@metric.exp(-d),float(f['scale']),False)[0])/(2*eps))
    ed=near(jj,np.column_stack(fd),2e-5)
    # Common-world gauge and node right perturbations use independent exponentials.
    ti=metric.exp(np.array([.1,.2,-.1,2.,1.,3.])); tj=ti@z; chain=np.column_stack([-metric.transport(np.linalg.inv(z)),np.eye(6)])
    global_j=jj@chain; observed=[]
    for k in range(12):
        step=np.eye(6)[k%6]*eps; values=[]
        for sign in (1,-1):
            x=ti@(metric.exp(sign*step) if k<6 else np.eye(4)); y=tj@(metric.exp(sign*step) if k>=6 else np.eye(4))
            values.append(independent(a,b,np.linalg.solve(x,y),float(f['scale']),False)[0])
        observed.append((values[0]-values[1])/(2*eps))
    eg=near(global_j,np.column_stack(observed),2e-5)
    world=metric.exp(np.array([-.2,.1,.1,4.,-3.,2.])); gauge=near(np.linalg.solve(world@ti,world@tj),z,1e-12)
    # Q is differentiated at a nonzero relative local coordinate.
    m=r.Matching(a,b,z); m.prepare(.5); test=z@metric.exp(np.array([.01,.02,-.01,.03,-.02,.01])); qr,qj=m.quadratic(test); qfd=[]
    for k in range(6):
        d=np.eye(6)[k]*eps
        def qvalue(t): return np.r_[m.A@metric.log(np.linalg.solve(z,t))+m.bq,m.const]
        qfd.append((qvalue(test@metric.exp(d))-qvalue(test@metric.exp(-d)))/(2*eps))
    eq=near(qj,np.column_stack(qfd),2e-5)
    # A fully censored observation contributes a constant and zero derivative.
    far=z.copy(); far[:3,3]+=100.; cr,cj,support=independent(a,b,far,1.)
    assert support==0 and np.max(abs(cj))==0 and abs(float(cr@cr)-2.25)<1e-12
    r.save(BASE/'synthetic_validation.json',dict(utc=r.now(),passed=True,brute_residual_max=e1,brute_jacobian_max=e2,
        independent_relative_FD_max=ed,independent_global_FD_max=eg,Q_nonzero_FD_max=eq,common_world_max=gauge,quadratic_equivalence=errs,
        censored_constant_verified=True,independent_nonlinear_optimizer=False))
    print('Independent synthetic/brute/gauge/global/Q derivatives pass',flush=True)

def bank():
    r.verify_bank(); maximum=0.; count=0; support=[]; objective={}
    from rap_slam.pose_graph import propagate_to_full_trajectory
    for s in r.SEQS:
        records=r.read(BASE/f'bank/{s}/loops.json'); init=r.read(BASE/f'bank/{s}/initial_factors.json')
        b=np.load(BASE/f'bank/{s}/B.npy'); o=r.proper(r.load(r.src(s)/'odom_poses.txt')); kf=r.read(r.src(s)/'keyframes.json')
        frames=r.read(BASE/f'bank/{s}/frames.json'); assert frames['source_frame_ids']==list(range(len(o))) and frames['keyframes']==kf
        assert records==[{**v,'T_rel':r.proper(np.asarray(v['T_rel'])).tolist()} for v in r.loops(s)]
        for arm in ('B','Q','D'):
            t=np.load(BASE/f'bank/{s}/{arm}.npy'); r.proper(t)
            reconstructed=np.asarray(propagate_to_full_trajectory(list(o),kf,{i:t[i] for i in kf})); near(t,reconstructed,1e-8)
        errors=[]; costs={'Q':0.,'D':0.}
        for row,info in zip(records,init):
            a=np.load(r.pointpath(s,row['i']))['points'].astype(float); bb=np.load(r.pointpath(s,row['j']))['points'].astype(float)
            z0=np.linalg.solve(b[row['i']],b[row['j']]); unscaled,uj,ss=independent(a,bb,z0)
            lam=(3/(.20*np.clip(row['mean_dist'],1,3))**2)/float(np.sum(uj[:,3:]**2))
            near(lam,info['lambda_strength'],1e-7); near(ss,info['support'],1e-12); assert ss>=.5; support.append(ss)
            scale=np.sqrt(lam); rr,jj=unscaled*scale,uj*scale; obj=r.Matching(a,bb,z0); obj.prepare(row['mean_dist'])
            nr,nj,_=obj.residual(z0); errors += [relative(rr,nr),relative(jj,nj)]
            qr,qj=obj.quadratic(z0); errors += [relative(qj.T@qr,jj.T@rr),relative(qj.T@qj,jj.T@jj),abs(float(qr@qr-rr@rr))/max(float(rr@rr),1.)]
            for arm in ('Q','D'):
                t=np.load(BASE/f'bank/{s}/{arm}.npy'); z=np.linalg.solve(t[row['i']],t[row['j']])
                if arm=='D': values,_,_=independent(a,bb,z,scale,False)
                else:
                    x=metric.log(np.linalg.solve(z0,z)); values=rr+jj@x
                costs[arm]+=float(values@values/2)
            count+=len(a)+len(bb); r.cap()
        assert max(errors)<=1e-8,max(errors); maximum=max(maximum,*errors)
        # Add original prior/motion objective using separate relative-pose equations.
        run=r.read(BASE/'bank/execution.json')['rows'][s]
        for arm in ('Q','D'):
            t=np.load(BASE/f'bank/{s}/{arm}.npy'); x=metric.log(np.linalg.solve(o[0],t[0])); costs[arm]+=float(x@x/(2*.01**2))
            sig=np.array([.05]*3+[.30]*3)
            for i,j in zip(kf[:-1],kf[1:]):
                z=np.linalg.solve(o[i],o[j]); current=np.linalg.solve(t[i],t[j]); x=metric.log(np.linalg.solve(z,current))/sig; costs[arm]+=float(x@x/2)
            # GTSAM Pose3 localCoordinates uses its Logmap; SciPy implementation is independent.
            err=abs(costs[arm]-run[arm]['final_error'])/max(abs(run[arm]['final_error']),1.)
            assert err<=1e-7,(s,arm,err,costs[arm],run[arm]['final_error'])
            objective[f'{s}_{arm}']=dict(independent=costs[arm],recorded=run[arm]['final_error'],relative_error=err)
    r.save(BASE/'bank_validation.json',dict(utc=r.now(),passed=True,independent_initial_directed_queries=count,
        maximum_relative_algebra_error=maximum,minimum_support=min(support),final_objectives=objective,shared_propagation=True,
        independent_nonlinear_optimizer=False,new_GT_read=False))
    print('Full brute-force initial/final observation validation passed',count,maximum,flush=True)

def metrics():
    r.verify_bank(); result=r.read(BASE/'results.json'); assert r.read(BASE/'bank_seal.json')['utc']<result['gt_read_started_utc']
    maximum=0.; count=0; rows={}
    for s in r.SEQS:
        camera=metric.load(r.DATA/f'poses/{s}.txt'); tr=metric.calibration(s); ti=np.linalg.inv(tr); lidar=ti@camera@tr; rows[s]={}
        for arm in ('B','Q','D'):
            t=np.load(BASE/f'bank/{s}/{arm}.npy'); seg=metric.segments(camera,tr@t@ti); saved=r.read(BASE/f'evaluation/{s}/{arm}_segments.json')
            assert len(seg)==len(saved); count+=len(seg)
            for a,b in zip(seg,saved):
                for key in ('first','last','source_first','source_last','length_m'): assert a[key]==b[key]
                for key in ('translation_fraction','rotation_rad_per_m','speed_mps'): maximum=max(maximum,near(a[key],b[key],2e-10))
            values=dict(ate=metric.horn_rmse(lidar,t),ter=float(np.mean([v['translation_fraction'] for v in seg])*100),
                rer=float(np.mean([v['rotation_rad_per_m'] for v in seg])*180/np.pi*100),segments=len(seg))
            rows[s][arm]=values
            for k in values: maximum=max(maximum,near(values[k],result['rows'][s][arm][k],1e-8))
    # Independent gate expression, rather than merely calling the experiment gate.
    means={a:{k:float(np.mean([rows[s][a][k] for s in r.SEQS])) for k in ('ate','ter','rer')} for a in ('B','Q','D')}; tests={}
    for c in ('B','Q'):
        tests[f'{c}_ATE_gain_5pct']=means['D']['ate']<=.95*means[c]['ate']+1e-10
        for s in r.SEQS:
            tests[f'{s}_{c}_ATE_improves']=rows[s]['D']['ate']<rows[s][c]['ate']
            tests[f'{s}_{c}_ATE_harm5pct']=rows[s]['D']['ate']<=1.05*rows[s][c]['ate']+1e-10
            for k in ('ter','rer'): tests[f'{s}_{c}_{k}_harm']=rows[s]['D'][k]-rows[s][c][k]<=.01+1e-10
    for k in ('ter','rer'): tests[f'B_mean_{k}_nonworse']=means['D'][k]-means['B'][k]<=1e-10
    assert tests==result['gate']['tests'] and all(tests.values())==result['gate']['passed']
    r.save(BASE/'metric_validation.json',dict(utc=r.now(),passed=True,independent_segments=count,maximum_metric_delta=maximum,
        tests=tests,scientific_gate_passed=all(tests.values()),rows=rows))
    print('Independent Horn/segments/gates validated',count,maximum,'scientific pass',all(tests.values()),flush=True)
