"""NOC0 independent Horn geometry/trace audit and bounded checkpoint forwards."""
import importlib.util
import sys
import time
import signal
from pathlib import Path
import numpy as np
import local_motion_common as c

spec=importlib.util.spec_from_file_location('noc_runner',Path(__file__).with_name('native_output_capability.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def load(path):
    with np.load(path,allow_pickle=False) as z: return {k:z[k].copy() for k in z.files}


def horn(x,y):
    x=np.asarray(x,np.float64);y=np.asarray(y,np.float64)
    a=x.mean(0);b=y.mean(0)
    xx,xy,xz,yx,yy,yz,zx,zy,zz=((x-a).T@(y-b)).ravel()
    K=np.array([[xx+yy+zz,yz-zy,zx-xz,xy-yx],[yz-zy,xx-yy-zz,xy+yx,zx+xz],
        [zx-xz,xy+yx,-xx+yy-zz,yz+zy],[xy-yx,zx+xz,yz+zy,-xx-yy+zz]])
    ev,Q=np.linalg.eigh(K);w,i,j,k=Q[:,-1]
    R=np.array([[1-2*(j*j+k*k),2*(i*j-k*w),2*(i*k+j*w)],
        [2*(i*j+k*w),1-2*(i*i+k*k),2*(j*k-i*w)],
        [2*(i*k-j*w),2*(j*k+i*w),1-2*(i*i+j*j)]])
    assert np.max(abs(R.T@R-np.eye(3)))<1e-10 and abs(np.linalg.det(R)-1)<1e-10
    return R,b-R@a,float((ev[-1]-ev[-2])/max(abs(ev).max(),1e-12))


def parts(z,y):
    out=[]
    for k in range(3):
        sl=slice(k*1000,(k+1)*1000);R,t,gap=horn(z['cond'][sl],y[sl]);assert gap>1e-6
        T=np.eye(4);T[:3,:3]=R;T[:3,3]=float(z['scale'])*t-R@z['centers'][k];out.append(T)
    return np.array(out)


def metric(P,truth):
    from scipy.spatial.transform import Rotation
    out=[]
    for k in (1,2):
        p=np.linalg.solve(P[0],P[k]);delta=np.linalg.solve(truth[k],p)
        out.append(dict(part=k,t_m=float(np.linalg.norm(p[:3,3]-truth[k,:3,3])),
            R_deg=float(np.degrees(np.linalg.norm(Rotation.from_matrix(delta[:3,:3]).as_rotvec())))))
    return out


def gate(m): return all(x['t_m']<=.05 and x['R_deg']<=.2 for x in m)


def compare_m(a,b):
    assert [x['part'] for x in a]==[x['part'] for x in b]
    d=max(abs(x[k]-y[k]) for x,y in zip(a,b) for k in ('t_m','R_deg'));assert d<1e-8
    return d


def sealed(folder):
    s=c.read(folder/'seal.json')['files']
    assert s=={str(p.relative_to(folder)):c.sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='seal.json'}


def fixture_check(z,synthetic):
    from scipy.spatial.transform import Rotation
    centers=np.array([p.mean(0) for p in np.split(z['points'],3)])
    scale=1.5*abs(z['points'][:1000]-centers[0]).max()
    cond=np.concatenate([(p-center)/scale for p,center in zip(np.split(z['points'],3),centers)]).astype(np.float32)
    assert np.max(abs(cond-z['cond']))<1e-7 and abs(scale-float(z['scale']))<1e-10
    assert np.max(abs(centers-z['centers']))<1e-10
    target=np.concatenate([(p@T[:3,:3].T+T[:3,3]-centers[0])/scale for p,T in zip(np.split(z['points'],3),z['truth'])]).astype(np.float32)
    assert np.array_equal(target,z['target'])
    if synthetic:
        src=load(r.OLD/'full-bank/bank/00_000002.npz')
        base=src['points'][:1000];feature=src['features'][:1000]
        assert np.array_equal(z['points'][:1000],base) and np.array_equal(z['features'],np.tile(feature,(3,1)))
        for k,rv,t in ((1,[.02,-.03,.05],[.5,-.2,.1]),(2,[-.01,.04,-.02],[-.3,.1,-.05])):
            T=np.eye(4);T[:3,:3]=Rotation.from_rotvec(rv).as_matrix();T[:3,3]=t
            assert np.max(abs(T-z['truth'][k]))<1e-14
            assert np.array_equal(z['points'][k*1000:(k+1)*1000],(base-T[:3,3])@T[:3,:3])
        assert np.array_equal(src['noise'],z['noise'])
    else:
        src=load(r.OLD/'full-bank/bank/00_000002.npz');lab=load(r.OLD/'pose-targets/bank/00_000002.npz')
        assert all(np.array_equal(z[k],src[k]) for k in ('points','features','noise','cond','scale','centers','counts'))
        assert np.array_equal(z['truth'][1:],lab['angular_truth'][:2])
        cycle=abs(np.linalg.solve(z['truth'][1],z['truth'][2])-lab['angular_truth'][2]).max()
        assert abs(cycle-float(z['cycle_delta']))<1e-14
    target_error=metric(parts(z,z['target']),z['truth'])
    assert all(x['t_m']<1e-5 and x['R_deg']<1e-5 for x in target_error)
    return target_error


def trace_check(z,a,noise_name):
    x=a[noise_name+'_input_states'];v=a[noise_name+'_velocities'];taus=a[noise_name+'_taus']
    raw=a[noise_name+'_end_point_trajectory'];states=a[noise_name+'_trajectory'];noise=a[noise_name+'_noise']
    assert abs(taus-np.array([1,.8,.6,.4,.2])).max()<3e-8
    assert np.array_equal(x[0],noise)
    maximum=0.
    for step in range(5):
        t=1-step*.2
        assert np.max(abs(raw[step]-(x[step]-v[step]*t)))<1e-6
        projected=[]
        for part in range(3):
            sl=slice(part*1000,(part+1)*1000)
            R,b,gap=horn(z['cond'][sl],raw[step,sl]);assert gap>1e-6
            projected.append(z['cond'][sl]@R.T+b)
        expected=np.concatenate(projected)*(1-t+.2)+noise*(t-.2)
        d=float(abs(expected-states[step]).max());maximum=max(maximum,d);assert d<3e-5,d
        if step<4: assert np.array_equal(x[step+1],states[step])
    return maximum


def run():
    import torch
    from native_output_capability import adapt,trainables,args,Direct
    from rap_slam.rap_precision import ieee_matmul
    freeze=r.check();s=c.read(r.BASE/'bank_seal.json');summary=c.read(r.BASE/'bank.json')
    assert c.sha(r.BASE/'freeze.json')==s['freeze_sha256'] and c.sha(r.BASE/'bank.json')==s['manifest_sha256']
    for p,h in s['files'].items(): assert c.sha(r.BASE/p)==h,p
    for p,h in s['preflight'].items(): assert c.sha(r.BASE/p)==h,p
    syn=load(r.BASE/'bank/synthetic_fixture.npz');fixtures={'synthetic':syn}
    synthetic_math=fixture_check(syn,True)
    if summary['real_window_executed']:
        fixtures['real']=load(r.BASE/'bank/real_fixture.npz');fixture_check(fixtures['real'],False)
    model,audit=r.load_model()
    with c.rng(20261010): adapt(model.flow_model)
    maximum_metric=0.;maximum_pose=0.;maximum_trace=0.;maximum_forward=0.;evaluations=0;decision={};counts={}
    with ieee_matmul():
        for folder in sorted((r.BASE/'bank').iterdir()):
            if not folder.is_dir(): continue
            sealed(folder);fit=c.read(folder/'fit.json');assert fit['updates']==400
            z=fixtures['synthetic' if folder.name.startswith('synthetic') else 'real'];b=r.batch(z)
            rows=fit['rows'];assert [x['step'] for x in rows]==list(range(1,401))
            assert all(np.isfinite(x['loss']) and np.isfinite(x['unclipped_norm']) for x in rows)
            counts[folder.name]=fit['trainable_parameters']
            native='native' in folder.name
            if native:
                params=trainables(model.flow_model);saved=load(folder/'parameters_0400.npz')
                with torch.no_grad():
                    for n,p in params.items(): p.copy_(torch.tensor(saved[n],device='cuda'))
                assert all(x['gradient_groups']['B']>0 and x['gradient_groups']['MLP']>0 for x in rows)
                assert all(x['gradient_groups']['A']>0 for x in rows[1:])
                from native_output_capability import frozen_digest
                assert frozen_digest(model.flow_model)==fit['frozen_parameters_sha256']
            else:
                with c.rng(20261010): direct=Direct().cuda()
                assert sum(p.numel() for p in direct.parameters())==fit['trainable_parameters']
            for checkpoint in (0,100,400):
                a=load(folder/f'evaluation_{checkpoint:04d}.npz');info=c.read(folder/f'evaluation_{checkpoint:04d}.json')
                if native:
                    assert float(a['cache_full_max_delta'])<=1e-6
                    mse=[]
                    for k,tau in enumerate((1,.8,.6,.4,.2)):
                        moved=parts(z,a['teacher'][k]);m=metric(moved,z['truth'])
                        maximum_metric=max(maximum_metric,compare_m(m,info['teacher_errors'][k]['errors']))
                        mse.append(float(np.mean(((a['teacher'][k]-z['target'])/tau)**2)))
                        # The stored teacher output algebra is equivalent to velocity MSE.
                        assert abs(mse[-1]-float(a['teacher_losses'][k]))<2e-6
                        if checkpoint==400:
                            x=torch.tensor((1-tau)*z['target']+tau*z['noise'],device='cuda')
                            with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                                v=model.flow_model(**args(b,x,tau));q=(x-tau*v).cpu().numpy()
                            d=float(abs(q-a['teacher'][k]).max());maximum_forward=max(maximum_forward,d);assert d<2e-6,d
                    assert abs(np.mean(mse)-info['teacher_loss_mean'])<2e-6
                    for name in ('train','unseen'):
                        maximum_trace=max(maximum_trace,trace_check(z,a,name))
                        for step in (0,4):
                            P=parts(z,a[name+'_end_point_trajectory'][step]);m=metric(P,z['truth'])
                            d=float(abs(P-a[f'{name}_parts_{step}']).max());maximum_pose=max(maximum_pose,d);assert d<1e-8
                            rr=next(x for x in info['native'] if x['noise']==name and x['step']==step+1)
                            maximum_metric=max(maximum_metric,compare_m(m,rr['errors']));assert gate(m)==rr['synthetic_gate']
                            if checkpoint==400:
                                with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                                    v=model.flow_model(**args(b,torch.tensor(a[name+'_input_states'][step],device='cuda'),1-step*.2))
                                d=float(abs(v.cpu().numpy()-a[name+'_velocities'][step]).max());maximum_forward=max(maximum_forward,d);assert d<2e-6,d
                    if checkpoint==400:
                        decision[folder.name]=next(x for x in info['native'] if x['noise']=='train' and x['step']==5)['synthetic_gate']
                else:
                    P=parts(z,a['output']);m=metric(P,z['truth'])
                    maximum_metric=max(maximum_metric,compare_m(m,info['errors']))
                    assert gate(m)==info['synthetic_gate']
                    d=float(abs(P-a['parts']).max());maximum_pose=max(maximum_pose,d);assert d<1e-8
                    weights=load(folder/('initial.npz' if checkpoint==0 else f'parameters_{checkpoint:04d}.npz'))
                    direct.load_state_dict({n:torch.tensor(v,device='cuda') for n,v in weights.items()},strict=True)
                    with torch.no_grad(): q=direct(b).cpu().numpy()
                    d=float(abs(q-a['output']).max());maximum_forward=max(maximum_forward,d);assert d<2e-6
                evaluations+=1;r.cap()
            if (folder/'preflight.json').exists():
                pre=c.read(folder/'preflight.json');assert pre['FD_abs_delta']<2e-4
        first=decision['synthetic_native_lr1e-4']
        assert ('synthetic_native_lr5e-4' in decision)==(not first)
        selected=1e-4 if first else 5e-4 if decision.get('synthetic_native_lr5e-4',False) else None
        assert summary['selected_lr']==selected and summary['synthetic_native_pass']==(selected is not None)
        assert summary['real_window_executed']==(selected is not None)
    r.check();results=dict(passed=True,independent_Horn_decode=True,all_saved_metrics_and_gates_checked=True,
        all_sampler_recurrences_checked=True,selected_final_checkpoint_full_forwards=True,
        full_optimizer_replay=False,preflight_FD_independently_replayed=False,
        synthetic_exact_target_errors=synthetic_math,evaluation_records=evaluations,fit_parameter_counts=counts,
        maximum_metric_delta=maximum_metric,maximum_pose_delta=maximum_pose,
        maximum_sampler_recurrence_delta=maximum_trace,maximum_selected_forward_delta=maximum_forward,
        decision=summary['decision'],**r.usage())
    c.save(r.BASE/'validation.json',results)
    c.save(r.BASE/'validation_seal.json',dict(validation_sha256=c.sha(r.BASE/'validation.json'),
        bank_seal_sha256=c.sha(r.BASE/'bank_seal.json'),freeze_sha256=c.sha(r.BASE/'freeze.json')))
    r.finish('independent_validation')
    c.status(r.BASE,'validated',status='VALIDATED_CAPABILITY_DIAGNOSTIC_COMPLETE',**summary)
    (r.BASE/'INCOMPLETE').unlink();print('NOC0 independent validation PASS',results,flush=True)


if __name__=='__main__':
    r.START=time.monotonic()
    def alarm(signum,frame): raise TimeoutError('NOC0 validation remaining wall exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in r.ledger()))))
    try: run()
    except Exception as ex:
        r.record('independent_validation',False,error=repr(ex))
        c.save(r.BASE/'FAILURE_validation.json',dict(error=repr(ex),utc=c.now(),**r.usage()))
        c.status(r.BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)
