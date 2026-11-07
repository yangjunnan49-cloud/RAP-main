"""NOC0 prospective freeze, bounded fitting and saved-trace evaluation."""
import sys
import time
import json
import resource
import signal
import subprocess
from pathlib import Path
import numpy as np
import local_motion_common as c

BASE=c.MAIN/'docs/maintenance/2026-10-10/native-output-capability-01'
OLD=c.MAIN/'docs/maintenance/2026-10-08/motion-supervised-readout-01'
HELPER=c.SLAM/'scripts/native_output_capability.py'
sys.path.insert(0,str(c.SLAM/'scripts'))
START=None
STAGE=None


def elapsed(): return time.monotonic()-START


def usage():
    import torch
    return dict(wall_seconds=elapsed(),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_initialized() else 0,
        artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()))


def ledger(): return c.read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []


def record(stage, success, **extra):
    rows=ledger(); rows.append(dict(stage=stage,success=success,utc=c.now(),**usage(),**extra))
    (BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')


def cap():
    u=usage()
    assert sum(x['wall_seconds'] for x in ledger())+u['wall_seconds'] <= 1800, 'combined wall cap'
    assert u['peak_RSS_bytes'] <= 4*2**30, 'RSS cap'
    assert max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes']) <= 3*2**30, 'GPU cap'
    assert u['artifact_bytes'] <= 512*2**20, 'artifact cap'


def finish(stage, **extra): cap(); record(stage,True,**extra)


def check():
    f=c.read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert c.sha(p)==h,p
    return f


def source_bindings():
    f=c.read(OLD/'full-bank/bank_seal.json'); g=c.read(OLD/'pose-targets/bank_seal.json')
    rel='bank/00_000002.npz'
    assert c.sha(OLD/'full-bank'/rel)==f['files'][rel]
    assert c.sha(OLD/'pose-targets'/rel)==g['files'][rel]
    return OLD/'full-bank'/rel, OLD/'pose-targets'/rel


def git_state():
    out=[]
    for root in (c.MAIN,c.SLAM):
        def git(*a): return subprocess.check_output(['git','-c','safe.directory='+str(root),'-C',str(root),*a],text=True).rstrip('\r\n')
        out.append(dict(root=str(root),HEAD=git('rev-parse','HEAD'),branch=git('branch','--show-current'),
            tracked_dirty=git('status','--short','--untracked-files=no').splitlines()))
    return out


def freeze():
    feature,target=source_bindings()
    previous=c.read(c.MAIN/'docs/maintenance/2026-10-10/membership-formation-diagnosis-01/REPOSITORY_STATE.json')
    current=git_state()
    for x,y in zip(current,previous['repositories']):
        assert all(x[k]==y[k] for k in ('HEAD','branch','tracked_dirty'))
    files=c.frozen_sources()+[HELPER,Path(__file__),Path(__file__).with_name('validate_native_output_capability.py'),
        BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',BASE/'algorithm_staging.py',feature,target,
        OLD/'full-bank/bank_seal.json',OLD/'pose-targets/bank_seal.json',OLD/'DELIVERY_SEAL.json',
        c.MAIN/'docs/maintenance/2026-10-10/membership-formation-diagnosis-01/DELIVERY_SEAL.json']
    files=list(sorted(set(files)))
    hashes={str(p):c.sha(p) for p in files}
    old=c.read(OLD/'full-bank/freeze.json')['files']
    for p,h in hashes.items():
        if p in old and p not in (str(HELPER),str(Path(__file__))): assert h==old[p],p
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in (HELPER,Path(__file__),Path(__file__).with_name('validate_native_output_capability.py')):
        (snap/(p.parent.name+'_'+p.name)).write_bytes(p.read_bytes())
    c.save(BASE/'freeze.json',dict(utc=c.now(),files=hashes,repositories=current,row=dict(seq='00',t=2,ids=[1,2,0],role='fit'),
        seed=20261010,heldout_noise_seed=20261011,limits=dict(wall_seconds=1800,GPU_bytes=3*2**30,RSS_bytes=4*2**30,artifact_bytes=512*2**20),
        full_optimizer_replay=False,execution_authorized=True))
    (BASE/'INCOMPLETE').write_text('Frozen NOC0; fitting and validation pending.\n')
    c.status(BASE,'frozen',status='AUTHORIZED_FROZEN',model_loaded=False)
    finish('freeze');print('NOC0 sources and inputs frozen',len(hashes),flush=True)


def load_model():
    import hydra
    import torch
    with hydra.initialize_config_dir(config_dir=str(c.MAIN/'config'),version_base='1.3'):
        cfg=hydra.compose(config_name='RAP_inference',overrides=['model=rap_12','model.inference_sampling_steps=5',
            'model.rigidity_forcing=true','model.n_generations=1','model.save_results=false'])
    assert cfg.model.flow_model_ckpt is None and cfg.model.encoder_ckpt is None
    model=hydra.utils.instantiate(cfg.model)
    w,allowed=c.safe_weights(c.MAIN/'weights/rap_model_12.ckpt')
    expected=model.state_dict(); assert set(w)==set(expected)
    assert all(w[k].shape==v.shape and w[k].dtype==v.dtype and torch.isfinite(w[k]).all() for k,v in expected.items())
    model.load_state_dict(w,strict=True); del w,expected
    model.cuda().eval().requires_grad_(False)
    return model,dict(strict=True,keys=len(model.state_dict()),weights_only=True,allowed=allowed,descriptor_loaded=False)


def fixture():
    from scipy.spatial.transform import Rotation
    from rap_slam.rap_backend import RAPBackend
    src,_=source_bindings()
    with np.load(src,allow_pickle=False) as f:
        p=f['points'][:1000].copy(); des=f['features'][:1000].copy(); noise=f['noise'].copy()
    truth=np.repeat(np.eye(4)[None],3,0)
    truth[1,:3,:3]=Rotation.from_rotvec([.02,-.03,.05]).as_matrix(); truth[1,:3,3]=[.5,-.2,.1]
    truth[2,:3,:3]=Rotation.from_rotvec([-.01,.04,-.02]).as_matrix(); truth[2,:3,3]=[-.3,.1,-.05]
    points=np.concatenate([p]+[(p-T[:3,3])@T[:3,:3] for T in truth[1:]])
    cond,scale,centers,counts,anchor=RAPBackend._normalize_parts(np.split(points,3));assert anchor==0
    y=np.concatenate([(q@T[:3,:3].T+T[:3,3]-centers[0])/scale for q,T in zip(np.split(points,3),truth)])
    return dict(points=points,features=np.tile(des,(3,1)),cond=cond,scale=np.array(scale),centers=np.array(centers),
        counts=counts,target=y.astype(np.float32),truth=truth,noise=noise)


def real_fixture():
    src,lab=source_bindings()
    with np.load(src,allow_pickle=False) as f:
        z={k:f[k].copy() for k in ('points','features','cond','scale','centers','counts','noise')}
    with np.load(lab,allow_pickle=False) as f: angular=f['angular_truth'].copy(); raw=f['raw_truth'].copy()
    truth=np.array([np.eye(4),angular[0],angular[1]])
    z['target']=np.concatenate([(p@T[:3,:3].T+T[:3,3]-z['centers'][0])/float(z['scale'])
        for p,T in zip(np.split(z['points'],3),truth)]).astype(np.float32)
    z['truth']=truth
    z['raw_truth']=raw; z['angular_truth']=angular
    z['cycle_delta']=np.array(abs(np.linalg.solve(truth[1],truth[2])-angular[2]).max())
    return z


def batch(z):
    import torch
    device='cuda';cond=torch.tensor(z['cond'],device=device)
    return dict(pointclouds=cond,pointclouds_gt=cond,features=torch.tensor(z['features'],device=device),
        scales=torch.tensor([float(z['scale'])],device=device,dtype=torch.float32),
        anchor_indices=torch.arange(3000,device=device)<1000,points_per_part=torch.tensor([[1000,1000,1000]],device=device),
        cu_seqlens=torch.tensor([0,3000],device=device))


def numpy_state(params): return {k:v.detach().cpu().numpy().copy() for k,v in params.items()}


def save_opt(folder,opt,params):
    arrays={}
    for n,p in params.items():
        for k,v in opt.state[p].items(): arrays[n+'|'+k]=v.detach().cpu().numpy() if hasattr(v,'detach') else np.array(v)
    np.savez(folder/'optimizer_final.npz',**arrays)


def inspect_grad(params):
    groups={}
    for n,p in params.items():
        assert p.grad is not None and torch_finite(p.grad),n
        group='A' if n.endswith('.A') else 'B' if n.endswith('.B') else 'MLP'
        groups[group]=groups.get(group,0.)+float(p.grad.double().square().sum())
    return {k:float(np.sqrt(v)) for k,v in groups.items()}


def torch_finite(p):
    import torch
    return bool(torch.isfinite(p).all())


def caches(model,b,y,noise):
    import torch
    from native_output_capability import args,prefix,TAUS
    out=[]
    with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
        for tau in TAUS:
            x=(1-tau)*y+tau*noise;kw=args(b,x,tau)
            out.append((prefix(model.flow_model,kw),kw))
            cap()
    return out


def sampler(model,b,noise):
    import torch
    captured=[]
    def hook(module,inputs,kwargs,output):
        captured.append(dict(x=kwargs['x'].detach().cpu().numpy().copy(),
            tau=kwargs['timesteps'].detach().cpu().numpy().copy(),v=output.detach().cpu().numpy().copy()))
    handle=model.flow_model.register_forward_hook(hook,with_kwargs=True)
    try:
        with c.rng(20261010),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
            result=model.sample_rectified_flow(b,None,x_1=noise,return_tarjectory=True)
    finally: handle.remove()
    assert len(captured)==5
    result={k:v.cpu().numpy() for k,v in result.items()}
    result.update(input_states=np.stack([x['x'] for x in captured]),velocities=np.stack([x['v'] for x in captured]),
        taus=np.concatenate([x['tau'] for x in captured]))
    cap();return result


def evaluate(model,z,b,cache,folder,checkpoint):
    import torch
    from native_output_capability import tail,poses,errors,gate,TAUS
    teacher=[]; cache_delta=0.;losses=[]
    y=torch.tensor(z['target'],device='cuda'); noise=torch.tensor(z['noise'],device='cuda')
    with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
        for tau,(e,kw) in zip(TAUS,cache):
            v=tail(model.flow_model,e,kw);q=kw['x']-tau*v
            teacher.append(q.cpu().numpy());losses.append(float((v-(noise-y)).square().mean()))
            cache_delta=max(cache_delta,float(abs(v-model.flow_model(**kw)).max()))
    assert cache_delta <= 1e-6,cache_delta
    arr=dict(teacher=np.array(teacher),teacher_losses=np.array(losses),cache_full_max_delta=np.array(cache_delta))
    records=[]
    for noise_name,seed in (('train',None),('unseen',20261011)):
        if seed is None: n=noise
        else:
            with c.rng(seed): n=torch.randn_like(noise)
        trace=sampler(model,b,n);arr[noise_name+'_noise']=n.cpu().numpy()
        arr.update({noise_name+'_'+k:v for k,v in trace.items()})
        for step in (0,4):
            part=poses(z['cond'],trace['end_point_trajectory'][step],z['centers'],float(z['scale']))
            rows=errors(part,z['truth']);arr[f'{noise_name}_parts_{step}']=part
            records.append(dict(noise=noise_name,step=step+1,errors=rows,synthetic_gate=gate(rows)))
    teacher_errors=[]
    for tau,q in zip(TAUS,teacher):
        part=poses(z['cond'],q,z['centers'],float(z['scale']))
        teacher_errors.append(dict(tau=tau,errors=errors(part,z['truth'])))
    np.savez(folder/f'evaluation_{checkpoint:04d}.npz',**arr)
    info=dict(checkpoint=checkpoint,teacher_loss_mean=float(np.mean(losses)),cache_full_max_delta=cache_delta,
        teacher_errors=teacher_errors,native=records)
    c.save(folder/f'evaluation_{checkpoint:04d}.json',info)
    return info


def native_fit(model,z,initial,name,lr,preflight=False):
    import torch
    from native_output_capability import trainables,tail,frozen_digest
    folder=BASE/'bank'/name;folder.mkdir()
    params=trainables(model.flow_model)
    with torch.no_grad():
        for n,p in params.items(): p.copy_(torch.tensor(initial[n],device='cuda'))
    frozen=frozen_digest(model.flow_model)
    b=batch(z); y=torch.tensor(z['target'],device='cuda'); noise=torch.tensor(z['noise'],device='cuda')
    cache=caches(model,b,y,noise);np.savez(folder/'initial.npz',**numpy_state(params))
    evals=[evaluate(model,z,b,cache,folder,0)]
    opt=torch.optim.AdamW(params.values(),lr=lr,weight_decay=1e-4)
    rows=[]
    for step in range(1,401):
        index=(step-1)%5;e,kw=cache[index];opt.zero_grad(set_to_none=True)
        with torch.autocast('cuda',dtype=torch.float16): v=tail(model.flow_model,e,kw)
        loss=(v-(noise-y)).square().mean();loss.backward();groups=inspect_grad(params)
        if step==1:
            assert groups['B']>0 and groups['MLP']>0
            if preflight:
                param=params['final_mlp.4.weight'];analytic=float(param.grad[0,0]);saved=float(param[0,0]);values=[]
                with torch.no_grad():
                    for sign in (-1,1):
                        param[0,0]=saved+sign*.001
                        with torch.autocast('cuda',dtype=torch.float16): vv=tail(model.flow_model,e,kw)
                        values.append(float((vv-(noise-y)).square().mean()))
                    param[0,0]=saved
                fd=(values[1]-values[0])/.002;assert abs(fd-analytic)<2e-4,(fd,analytic)
                c.save(folder/'preflight.json',dict(groups=groups,selected_output_weight_autograd=analytic,
                    selected_output_weight_FD=fd,FD_abs_delta=abs(fd-analytic),gradient_through_sampler=False,**usage()))
        if step==2: assert groups['A']>0
        norm=float(torch.nn.utils.clip_grad_norm_(params.values(),1.));assert np.isfinite(norm)
        opt.step();cap()
        rows.append(dict(step=step,tau=kw['timesteps'].item(),loss=float(loss.detach()),gradient_groups=groups,unclipped_norm=norm))
        if step in (100,400):
            np.savez(folder/f'parameters_{step:04d}.npz',**numpy_state(params))
            evals.append(evaluate(model,z,b,cache,folder,step))
        if step%100==0: print(name,'updates',step,'loss',rows[-1]['loss'],flush=True)
    assert frozen_digest(model.flow_model)==frozen
    save_opt(folder,opt,params)
    c.save(folder/'fit.json',dict(name=name,lr=lr,updates=400,trainable_parameters=443904,rows=rows,
        frozen_parameters_sha256=frozen,frozen_parameters_unchanged=True,evaluations=evals,**usage()))
    passed=next(x for x in evals[-1]['native'] if x['noise']=='train' and x['step']==5)['synthetic_gate']
    c.save(folder/'seal.json',dict(files={str(p.relative_to(folder)):c.sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    return passed


def direct_fit(z,name):
    import torch
    from native_output_capability import Direct,poses,errors,gate
    with c.rng(20261010): model=Direct().cuda()
    folder=BASE/'bank'/name;folder.mkdir();params=dict(model.named_parameters());count=sum(p.numel() for p in params.values())
    b=batch(z);y=torch.tensor(z['target'],device='cuda');np.savez(folder/'initial.npz',**numpy_state(params))
    opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4);rows=[];evals=[]
    def ev(step):
        with torch.no_grad(): q=model(b).cpu().numpy()
        part=poses(z['cond'],q,z['centers'],float(z['scale']));err=errors(part,z['truth'])
        info=dict(checkpoint=step,loss=float(np.mean((q-z['target'])**2)),errors=err,synthetic_gate=gate(err))
        np.savez(folder/f'evaluation_{step:04d}.npz',output=q,parts=part)
        c.save(folder/f'evaluation_{step:04d}.json',info);evals.append(info)
    ev(0)
    for step in range(1,401):
        opt.zero_grad(set_to_none=True);q=model(b);loss=(q-y).square().mean();loss.backward()
        assert all(p.grad is not None and torch_finite(p.grad) for p in params.values())
        norm=float(torch.nn.utils.clip_grad_norm_(model.parameters(),1.));assert np.isfinite(norm);opt.step();cap()
        rows.append(dict(step=step,loss=float(loss.detach()),unclipped_norm=norm))
        if step in (100,400):
            np.savez(folder/f'parameters_{step:04d}.npz',**numpy_state(params));ev(step)
    save_opt(folder,opt,params)
    c.save(folder/'fit.json',dict(name=name,lr=1e-3,updates=400,trainable_parameters=count,rows=rows,evaluations=evals,**usage()))
    c.save(folder/'seal.json',dict(files={str(p.relative_to(folder)):c.sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    print(name,'400 updates',evals[-1]['errors'],flush=True)


def run():
    import torch
    from native_output_capability import adapt,trainables,poses,errors
    from rap_slam.rap_precision import ieee_matmul
    check();(BASE/'bank').mkdir()
    z=fixture();np.savez(BASE/'bank/synthetic_fixture.npz',**z)
    math=errors(poses(z['cond'],z['target'],z['centers'],float(z['scale'])),z['truth'])
    assert all(x['t_m']<1e-5 and x['R_deg']<1e-5 for x in math),math
    c.save(BASE/'math_preflight.json',dict(errors=math,passed=True,model_loaded=False))
    model,audit=load_model();cap()
    # Baseline and initialized adapter must agree before any optimizer step.
    b=batch(z);noise=torch.tensor(z['noise'],device='cuda')
    with ieee_matmul():
        frozen=sampler(model,b,noise)
        with c.rng(20261010): adapt(model.flow_model)
        initialized=sampler(model,b,noise)
        delta=max(float(abs(frozen[k]-initialized[k]).max()) for k in frozen)
        assert delta==0,delta
        initial=numpy_state(trainables(model.flow_model))
        np.savez(BASE/'bank/frozen_synthetic.npz',**frozen)
        c.save(BASE/'model_preflight.json',dict(checkpoint=audit,initialized_native_delta=delta,trainable_parameters=443904,**usage()))
        pass1=native_fit(model,z,initial,'synthetic_native_lr1e-4',1e-4,preflight=True)
        direct_fit(z,'synthetic_direct')
        selected=1e-4 if pass1 else None
        if not pass1:
            if native_fit(model,z,initial,'synthetic_native_lr5e-4',5e-4): selected=5e-4
        real=False
        if selected is not None:
            rz=real_fixture();np.savez(BASE/'bank/real_fixture.npz',**rz)
            assert float(rz['cycle_delta'])<1e-6
            native_fit(model,rz,initial,'real_native',selected)
            direct_fit(rz,'real_direct');real=True
    summary=dict(synthetic_native_pass=selected is not None,selected_lr=selected,real_window_executed=real,
        real_windows=1 if real else 0,noise_seeds=[20261010,20261011],one_seed_development_only=True,
        decision='TINY_NATIVE_SAMPLER_CAPABILITY_PRESENT' if selected is not None else 'NO_FIXED_BUDGET_NATIVE_SAMPLER_FIT',
        no_transfer_or_system_claim=True,**usage())
    check();c.save(BASE/'bank.json',summary)
    c.save(BASE/'bank_seal.json',dict(freeze_sha256=c.sha(BASE/'freeze.json'),manifest_sha256=c.sha(BASE/'bank.json'),
        files={str(p.relative_to(BASE)):c.sha(p) for p in sorted((BASE/'bank').rglob('*')) if p.is_file()},
        preflight={p.name:c.sha(p) for p in (BASE/'math_preflight.json',BASE/'model_preflight.json')}))
    c.status(BASE,'bank_sealed',status='FITTING_COMPLETE_VALIDATION_PENDING',**summary)
    finish('fit_and_evaluate');print('NOC0 complete bank sealed',summary['decision'],flush=True)


if __name__=='__main__':
    import torch
    START=time.monotonic();STAGE=sys.argv[1]
    def alarm(signum,frame): raise TimeoutError('NOC0 remaining combined wall exhausted')
    signal.signal(signal.SIGALRM,alarm)
    signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in ledger()))))
    try: {'freeze':freeze,'run':run}[STAGE]()
    except Exception as ex:
        record(STAGE,False,error=repr(ex))
        c.save(BASE/('FAILURE_'+STAGE+'.json'),dict(error=repr(ex),utc=c.now(),**usage()))
        c.status(BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)
