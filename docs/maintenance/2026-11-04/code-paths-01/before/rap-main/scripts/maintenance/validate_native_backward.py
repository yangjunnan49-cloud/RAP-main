"""NBR0 CPU-only equation/census audit, no torch/model/backward import."""
import math
import numpy as np
from scipy.spatial.transform import Rotation
import native_backward_reproducibility as r

def load(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k].copy() for k in z.files}
def horn(x,y):
    a,b=x.mean(0),y.mean(0); s=(x-a).T@(y-b); v=np.array([s[1,2]-s[2,1],s[2,0]-s[0,2],s[0,1]-s[1,0]])
    h=np.empty((4,4)); h[0,0]=np.trace(s); h[0,1:]=v; h[1:,0]=v; h[1:,1:]=s+s.T-np.trace(s)*np.eye(3)
    values,vec=np.linalg.eigh(h); quat=vec[:,-1]; rot=Rotation.from_quat(np.r_[quat[1:],quat[0]]).as_matrix(); return rot,b-rot@a
def objective(z,q):
    cond=z['cond'].astype(float); centers=z['centers'].astype(float); scale=float(z['scale']); poses=[]; shapes=[]
    for k in range(3):
        x,y=cond[k*1000:(k+1)*1000],q[k*1000:(k+1)*1000]; rot,bias=horn(x,y); pose=np.eye(4); pose[:3,:3]=rot; pose[:3,3]=scale*bias-rot@centers[k]; poses.append(pose)
        shapes.append(np.mean((scale*(y-x@rot.T-bias))**2))
    translation=[]; rotation=[]
    for k in (1,2):
        rel=np.linalg.solve(poses[0],poses[k]); translation.append(np.sum(((rel[:3,3]-z['truth'][k,:3,3])/.05)**2))
        rotation.append(np.sum((z['truth'][k,:3,:3].T@rel[:3,:3]-np.eye(3))**2)/(2*math.radians(.2)**2))
    return float(np.mean(translation)+np.mean(rotation)+.001*np.mean(shapes)/.05**2)
def stats(a,b):
    assert a.shape==b.shape and a.dtype==b.dtype; d=np.asarray(a,dtype=float)-np.asarray(b,dtype=float)
    return dict(byte_equal=bool(np.array_equal(a,b)),different=int(np.sum(a!=b)),size=int(a.size),max_abs=float(np.max(np.abs(d))),relative_L2=float(np.sqrt(np.sum(d*d))/max(float(np.sqrt(np.sum(np.asarray(b,dtype=float)**2))),1e-30)))
def validate():
    r.verify(); r.check_seal(r.BASE/'traces','trace_seal.json'); result=r.read(r.BASE/'results.json'); execution=r.read(r.BASE/'traces/execution.json')
    assert execution['native_forwards']==execution['backwards']==8 and execution['prefix_forwards']==2 and execution['optimizer_calls']==execution['retained_updates']==0
    assert execution['initialized_trainables']==443904 and execution['strict_checkpoint']['strict'] and execution['strict_checkpoint']['weights_only']
    z=load(r.OLD/'bank/synthetic_fixture.npz'); noise=load(r.OLD/'bank/noise/fit_00.npz')['noise']; initial=load(r.OLD/'preflight/P/initial.npz'); costmax=0.; vgradientmax=0.; fdchecks=[]; linear=[]
    sequence=r.read(r.BASE/'freeze.json')['sequence']; assert [x['name'] for x in execution['traces']]==sequence
    rng=np.random.default_rng(417); directions=[]
    for sl,column in ((slice(1000,2000),0),(slice(2000,3000),1),(slice(0,1000),2)):
        d=np.zeros((3000,3)); d[sl,column]=1.; directions.append(d)
    for _ in range(9):
        d=rng.normal(size=(3000,3)); d/=np.linalg.norm(d); directions.append(d)
    for meta in execution['traces']:
        folder=r.BASE/'traces'/meta['name']; out=load(folder/'output.npz'); grads=load(folder/'gradients.npz'); hooks=load(folder/'hooks.npz'); after=load(folder/'parameters_after.npz')
        assert set(initial)==set(grads)==set(after) and all(np.array_equal(after[k],initial[k]) for k in initial)
        assert all(np.isfinite(a).all() for a in list(out.values())+list(grads.values())+list(hooks.values()))
        assert np.array_equal((noise-out['velocity']).astype(np.float32),out['output'])
        if meta['arm']=='V':
            residual=out['velocity']-(noise-z['target']); cost=float(np.mean(residual**2)); expected=(-2.*residual/9000).astype(np.float32)
            delta=float(np.max(abs(expected-out['upstream']))); assert delta<=1e-10; vgradientmax=max(vgradientmax,delta)
        else:
            q=out['output'].astype(float); cost=objective(z,q)
            for j,d in enumerate(directions):
                fd=(objective(z,q+1e-6*d)-objective(z,q-1e-6*d))/2e-6; analytic=float(np.sum(out['upstream'].astype(float)*d)); error=abs(fd-analytic); bound=max(1e-4,1e-5*abs(fd)); assert error<=bound,(meta['name'],j,error,bound)
                fdchecks.append(dict(trace=meta['name'],direction=j,finite_difference=fd,saved_upstream=analytic,delta=error,bound=bound))
        delta=abs(cost-meta['loss']); assert delta<=1e-7; costmax=max(costmax,delta)
        for module in meta['hook_modules']:
            go=hooks[module+'|scaled_gradient'].astype(float); rank=hooks[module+'|rank'].astype(float); product=go.T@rank
            rounded=product.astype(np.float16).astype(np.float32)/meta['factor']; actual=grads[module+'.B']; difference=rounded.astype(float)-actual.astype(float)
            ulp=np.abs(np.spacing(product.astype(np.float16)).astype(float))/meta['factor']; eligible=np.abs(difference)<=ulp
            linear.append(dict(trace=meta['name'],module=module,max_abs=float(np.max(abs(difference))),within_one_fp16_ULP=bool(eligible.all()),outside_ULP_values=int(np.sum(~eligible)),
                byte_equal=bool(np.array_equal(rounded,actual)),scope='float64 local linear product/fp16 rounding; native GEMM/reduction not independently reimplemented'))
        r.cap()
    for pair in result['pairs']:
        reconstructed={}
        for filename in ('output.npz','gradients.npz','hooks.npz'):
            left=load(r.BASE/'traces'/pair['left']/filename); right=load(r.BASE/'traces'/pair['right']/filename); reconstructed[filename]={key:stats(left[key],right[key]) for key in left}
        for filename,values in reconstructed.items():
            for key,v in values.items():
                ref=pair['details'][filename][key]
                for field,val in v.items():
                    if field=='relative_L2': assert abs(val-ref[field])<=1e-12*max(1.,abs(val))
                    else: assert val==ref[field]
        assert pair['all_byte_equal']==all(v['byte_equal'] for values in reconstructed.values() for v in values.values())
    for row in result['old_comparisons']:
        previous=r.OLD/('preflight' if row['path']=='cache' else 'preflight_replay')/row['arm']; left=load(r.BASE/f"traces/{row['arm']}_{row['path']}1/gradients.npz"); right=load(previous/'gradients.npz')
        for key in left:
            rebuilt=stats(left[key],right[key]); stored=row['gradients'][key]
            for field,val in rebuilt.items(): assert abs(val-stored[field])<=1e-12*max(1.,abs(val)) if field=='relative_L2' else val==stored[field]
    assert result['all_instrumented_pairs_byte_equal']==all(z['all_byte_equal'] for z in result['pairs'])
    assert result['decision']==('INSTRUMENTED_BACKWARD_REPRODUCIBLE' if result['all_instrumented_pairs_byte_equal'] else 'INSTRUMENTED_BACKWARD_MISMATCH_LOCALIZED')
    r.verify(); r.save(r.BASE/'validation.json',dict(utc=r.now(),passed=True,traces=8,optimizer_calls=0,parameters_unchanged_byteexact=True,independent_loss_max_delta=costmax,
        V_upstream_max_delta=vgradientmax,P_output_directional_FD=fdchecks,local_B_linear_checks=linear,all_local_B_within_one_ULP=all(z['within_one_fp16_ULP'] for z in linear),
        independent_difference_census=True,decision=result['decision'],native_fit_admitted=False,independent_full_transformer_backward=False))
    print('NBR0 independent artifact audit',result['decision'],flush=True)
