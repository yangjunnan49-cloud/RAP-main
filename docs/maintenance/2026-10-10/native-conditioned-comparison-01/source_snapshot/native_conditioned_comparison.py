"""NOC4 isolated synthetic native comparison; original banks/sources are read-only."""
import inspect
import json
import signal
import sys
import time
from pathlib import Path
import numpy as np
import torch
import local_motion_common as c
import native_pose_fit as old
from native_output_capability import args, prefix, tail, frozen_digest
from rap_slam.rap_precision import ieee_matmul

PREVIOUS=old.BASE
CONTROL=c.MAIN/'docs/maintenance/2026-10-10/rigid-control-conditioning-01'
BASE=c.MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-01'
SETTINGS=dict(updates=400,parameters=443904,lr=1e-4,betas=[.9,.999],eps=1e-8,
              weight_decay=0,clip_norm=None,backward_multipliers=dict(V=1024.,P=1/1024))
n=old.n
o=old.o
load=n.load
assign=old.assign
model=old.model
seal=old.seal
check_seal=old.check_seal


def noise_rows():
    import hashlib
    rows=[dict(name=f'{role}_{i:02d}',role=role,index=i,seed=int.from_bytes(
        hashlib.sha256(f'NOC4|20261010|{role}|{i}'.encode()).digest()[:4],'big'))
        for role,count in (('fit',8),('eval',16)) for i in range(count)]
    excluded={850873755,20261010,20261011}|{x['seed'] for x in n.noise_rows()}
    import hashlib as h
    excluded|={int.from_bytes(h.sha256(f'NOC2|20261010|{role}|{i}'.encode()).digest()[:4],'big')
        for role,count in (('fit',8),('eval',16)) for i in range(count)}
    assert len({x['seed'] for x in rows})==24 and not {x['seed'] for x in rows}&excluded
    return rows


def old_deliveries():
    counts=[]
    for folder,count in ((n.OLD,103),(n.BASE,188),(PREVIOUS,53),(PREVIOUS/'delivery-correction-01',5),(CONTROL,37)):
        rows=c.read(folder/'DELIVERY_SEAL.json')['files'];assert len(rows)==count
        for row in rows: assert c.sha(folder/row['path'])==row['sha256'],row['path']
        counts.append(count)
    return counts


def check():
    f=c.read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert c.sha(p)==h,p
    assert f['settings']==SETTINGS and f['noise_rows']==noise_rows()
    assert f['runtime']['torch']==torch.__version__ and f['runtime']['numpy']==np.__version__
    assert torch.get_num_threads()==1
    return f


def admit(fixture):
    assert fixture=='synthetic'
    check_seal(BASE/'preflight')
    assert c.read(BASE/'preflight/probes.json')['passed'],'native numerical prerequisite failed'
    assert c.read(BASE/'validation_preflight.json')['passed']
    vs=c.read(BASE/'validation_preflight_seal.json')
    assert c.sha(BASE/'validation_preflight.json')==vs['validation_sha256']
    assert c.sha(BASE/'preflight/seal.json')==vs['preflight_seal_sha256']


# Reuse the unchanged prediction, objective, sampler and gate implementations.
# Their mutable run paths/settings are confined to this new process and dossier.
old.BASE=BASE
old.check=check
old.noise_rows=noise_rows
old.old_deliveries=old_deliveries
old.admit=admit
usage=old.usage
ledger=old.ledger
cap=old.cap
finish=old.finish
generate=old.generate
summarize=old.summarize
noise_check=old.noise_check


def optimizer(params):
    return torch.optim.AdamW(params.values(),lr=SETTINGS['lr'],betas=tuple(SETTINGS['betas']),
        eps=SETTINGS['eps'],weight_decay=0)


def freeze():
    old_deliveries();f=c.read(CONTROL/'freeze.json')
    files=dict(f['files'])
    for p,h in files.items(): assert c.sha(p)==h,p
    assert c.read(CONTROL/'validation.json')['passed'] and c.read(CONTROL/'results.json')['primary_conjunction']
    repos=n.noc.git_state();assert repos==f['repositories']
    sources=[Path(__file__).with_name(name) for name in ('native_conditioned_comparison.py',
        'validate_native_conditioned_comparison.py','close_native_conditioned_comparison.py')]
    extra=sources+[BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',CONTROL/'freeze.json',CONTROL/'DELIVERY_SEAL.json',
        CONTROL/'results.json',CONTROL/'validation.json',Path(inspect.getfile(torch.optim.AdamW))]
    for p in extra: files[str(p)]=c.sha(p)
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in sources: (snap/p.name).write_bytes(p.read_bytes())
    c.save(BASE/'freeze.json',dict(utc=c.now(),files=files,repositories=repos,settings=SETTINGS,noise_rows=noise_rows(),
        fixtures=['synthetic'],arms=['B','V','P'],fit_updates=800,probe_optimizer_calls=2,
        validation_probe_optimizer_calls=2,retained_probe_updates=0,
        limits=dict(wall_seconds=1800,GPU_bytes=3*2**30,RSS_bytes=4*2**30,artifact_bytes=512*2**20),
        runtime=dict(torch=torch.__version__,numpy=np.__version__,python=sys.version,threads=1,gpu=torch.cuda.get_device_name(0))))
    (BASE/'INCOMPLETE').write_text('NOC4 frozen; numerical prerequisite and synthetic fits/evaluation pending.\n')
    c.status(BASE,'frozen',status='AUTHORIZED_FROZEN');finish('freeze');print('NOC4 frozen',len(files),flush=True)


def prepare():
    check();(BASE/'bank/noise').mkdir(parents=True)
    source=n.RETRY/'bank/synthetic_fixture.npz'
    (BASE/'bank/synthetic_fixture.npz').write_bytes(source.read_bytes())
    c.save(BASE/'mathematical_preflight.json',old.mathematical(load(source)))
    for row in noise_rows():
        with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda',dtype=torch.float32).cpu().numpy()
        np.savez(BASE/'bank/noise'/f"{row['name']}.npz",noise=noise);cap()
    c.save(BASE/'noise_seal.json',dict(rows=noise_rows(),files={str(p.relative_to(BASE)):c.sha(p)
        for p in sorted((BASE/'bank/noise').glob('*.npz'))}))
    finish('math_and_noise');print('NOC4 math and24 fresh noises sealed',flush=True)


def loss_value(z,noise,velocity,arm):
    if arm=='V':
        value=(velocity-(noise-torch.tensor(z['target'],device='cuda'))).square().mean()
        return value,dict(velocity=value)
    return old.obj(z,noise-velocity)


def backward(params,loss,arm):
    factor=SETTINGS['backward_multipliers'][arm]
    (loss*factor).backward()
    for p in params.values(): p.grad.div_(factor)


def group(name): return 'A' if name.endswith('.A') else 'B' if name.endswith('.B') else 'MLP'


def parameter_changes(before,after):
    norms={};per={}
    for k in before:
        delta=after[k].astype(np.float64)-before[k].astype(np.float64)
        norms[group(k)]=norms.get(group(k),0)+float(np.sum(delta**2))
        per[k]=dict(nonzero=int(np.count_nonzero(delta)),max_abs=float(np.max(np.abs(delta))))
    return dict(norms={k:float(np.sqrt(v)) for k,v in norms.items()},parameters=per,
        max_abs=max(x['max_abs'] for x in per.values()))


def probe(m,params,initial,z,b,arm,folder,full=False):
    folder.mkdir(parents=True);assign(params,initial)
    noise=torch.tensor(load(BASE/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=args(b,noise,1.)
    with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16): e=prefix(m.flow_model,kw)
    def forward():
        with torch.autocast('cuda',dtype=torch.float16):
            return m.flow_model(**kw) if full else tail(m.flow_model,e,kw)
    opt=optimizer(params);opt.zero_grad(set_to_none=True);velocity=forward();loss,_=loss_value(z,noise,velocity,arm)
    backward(params,loss,arm);grads={k:p.grad.detach().cpu().numpy().copy() for k,p in params.items()}
    np.savez(folder/'initial.npz',**initial);np.savez(folder/'gradients.npz',**grads)
    np.savez(folder/'output_before.npz',output=(noise-velocity).detach().cpu().numpy())
    norms={};detail={}
    for k,g in grads.items():
        norms[group(k)]=norms.get(group(k),0)+float(np.sum(g.astype(np.float64)**2))
        detail[k]=dict(finite=bool(np.isfinite(g).all()),nonzero=int(np.count_nonzero(g)),size=g.size)
    norms={k:float(np.sqrt(v)) for k,v in norms.items()}
    finite=all(x['finite'] for x in detail.values());assert finite,'nonfinite native gradient'
    norm=float(np.sqrt(sum(x*x for x in norms.values())))
    param=params['final_mlp.4.weight'];analytic=float(param.grad[0,0]);saved=float(param[0,0]);vals=[]
    with torch.no_grad():
        for sign in (-1,1):
            param[0,0]=saved+sign*.001;vals.append(float(loss_value(z,noise,forward(),arm)[0]))
        param[0,0]=saved
    fd=(vals[1]-vals[0])/.002;fd_delta=abs(fd-analytic)
    # Exactly one actual probe update, never reused by fitting.
    opt.step();after=n.noc.numpy_state(params)
    with torch.no_grad(): post_velocity=forward();post_loss=float(loss_value(z,noise,post_velocity,arm)[0])
    np.savez(folder/'parameters_after.npz',**after)
    np.savez(folder/'output_after.npz',output=(noise-post_velocity).cpu().numpy())
    n.noc.save_opt(folder,opt,params);changes=parameter_changes(initial,after)
    tests=dict(finite_gradient=finite,A_zero_at_B0=norms['A']==0,
        each_B_active=all(x['nonzero']>0 for k,x in detail.items() if group(k)=='B'),MLP_active=norms['MLP']>0,
        output_weight_FD=fd_delta<=max(2e-4,.02*abs(analytic)),
        each_B_changes=all(x['nonzero']>0 for k,x in changes['parameters'].items() if group(k)=='B'),
        MLP_changes=changes['norms']['MLP']>0,A_unchanged=changes['norms']['A']==0,
        finite_step=all(np.isfinite(a).all() for a in after.values()),
        bounded_step=changes['max_abs']<=1.01e-4,loss_decreases=post_loss<float(loss.detach()))
    assign(params,initial);assert all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items())
    info=dict(arm=arm,loss_before=float(loss.detach()),loss_after=post_loss,gradient_norm=norm,
        gradient_groups=norms,gradient_parameters=detail,clip1_counterfactual=min(1.,1./norm),clipping_applied=False,
        backward_multiplier=SETTINGS['backward_multipliers'][arm],analytic=analytic,finite_difference=fd,
        FD_delta=fd_delta,parameter_changes=changes,tests=tests,passed=all(tests.values()),
        optimizer_probe_calls=1,retained_updates=0,parameters_restored_byteexact=True,forward='full' if full else 'cache')
    c.save(folder/'probe.json',info);seal(folder);cap();return info


def preflight():
    check();noise_check();m,params,initial,audit=model();z=load(BASE/'bank/synthetic_fixture.npz')
    b=n.noc.batch({k:z[k] for k in n.OBS});frozen=frozen_digest(m.flow_model)
    folder=BASE/'preflight';folder.mkdir();rows=[]
    with ieee_matmul():
        noise=torch.tensor(load(BASE/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=args(b,noise,1.)
        with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
            e=prefix(m.flow_model,kw);delta=float(abs(tail(m.flow_model,e,kw)-m.flow_model(**kw)).max())
        assert delta==0
        for arm in ('V','P'):
            row=probe(m,params,initial,z,b,arm,folder/arm);rows.append(row)
            print('NOC4 probe',arm,row['passed'],'loss',row['loss_before'],row['loss_after'],
                'groups',row['gradient_groups'],'failed',[k for k,x in row['tests'].items() if not x],flush=True)
    assert frozen_digest(m.flow_model)==frozen
    c.save(folder/'probes.json',dict(passed=all(x['passed'] for x in rows),records=rows,
        optimizer_probe_calls=2,retained_updates=0,initial_cache_full_delta=delta,checkpoint=audit,frozen_sha256=frozen))
    seal(folder);finish('native_numerical_preflight')
    c.status(BASE,'preflight',status='PREFLIGHT_PENDING_INDEPENDENT_AUDIT',preflight_passed=all(x['passed'] for x in rows))


def fit(fixture):
    check();noise_check();admit(fixture);z=load(BASE/'bank/synthetic_fixture.npz');m,params,initial,audit=model()
    b=n.noc.batch({k:z[k] for k in n.OBS});frozen=frozen_digest(m.flow_model)
    cache=[];folder=BASE/'bank/synthetic_cache';folder.mkdir();prefix_deltas=[]
    with ieee_matmul():
        with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
            for row in noise_rows()[:8]:
                noise=torch.tensor(load(BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda')
                kw=args(b,noise,1.);e=prefix(m.flow_model,kw)
                delta=float(abs(tail(m.flow_model,e,kw)-m.flow_model(**kw)).max());assert delta==0
                prefix_deltas.append(delta);cache.append((e,kw,noise));np.savez(folder/f"{row['name']}.npz",embedding=e.cpu().numpy())
        seal(folder)
        for arm in ('V','P'):
            assign(params,initial);folder=BASE/'bank'/f'synthetic_{arm}';folder.mkdir()
            np.savez(folder/'initial.npz',**initial);opt=optimizer(params);rows=[]
            for step in range(1,401):
                e,kw,noise=cache[(step-1)%8];opt.zero_grad(set_to_none=True)
                with torch.autocast('cuda',dtype=torch.float16): velocity=tail(m.flow_model,e,kw)
                loss,terms=loss_value(z,noise,velocity,arm);backward(params,loss,arm)
                groups=n.noc.inspect_grad(params);assert groups['B']>0 and groups['MLP']>0
                assert all(torch.count_nonzero(p.grad)>0 for k,p in params.items() if group(k)=='B')
                if step>1: assert groups['A']>0
                norm=float(np.sqrt(sum(v*v for v in groups.values())))
                before=n.noc.numpy_state(params);opt.step();after=n.noc.numpy_state(params)
                assert all(np.isfinite(a).all() for a in after.values());changes=parameter_changes(before,after)
                assert changes['norms']['B']>0 and changes['norms']['MLP']>0
                rows.append(dict(step=step,noise_index=(step-1)%8,loss=float(loss.detach()),
                    terms={k:float(v.detach()) for k,v in terms.items()},norm=norm,groups=groups,
                    clip1_counterfactual=min(1.,1./norm),parameter_change_norms=changes['norms'],
                    max_parameter_change=changes['max_abs']))
                if step in (100,400): np.savez(folder/f'parameters_{step:04d}.npz',**after)
                cap()
                if step%100==0: print('NOC4 fit',arm,step,rows[-1]['loss'],'gradient',norm,flush=True)
            n.noc.save_opt(folder,opt,params);deltas=[]
            with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                for e,kw,noise in cache:
                    delta=float(abs(tail(m.flow_model,e,kw)-m.flow_model(**kw)).max());assert delta==0;deltas.append(delta)
            assert frozen_digest(m.flow_model)==frozen
            c.save(folder/'fit.json',dict(arm=arm,fixture='synthetic',updates=400,parameters=443904,lr=1e-4,
                settings=SETTINGS,rows=rows,initial_cache_full_deltas=prefix_deltas,final_cache_full_deltas=deltas,
                frozen_parameters_sha256=frozen,checkpoint=audit,clipping_applied=False));seal(folder)
    finish('fit_synthetic');c.status(BASE,'fit',status='FITS_COMPLETE_PREDICTIONS_PENDING')


def main():
    old.START=time.monotonic();stage=sys.argv[1]
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('NOC4 remaining combined wall cap')))
    signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in ledger()))))
    try:
        actions=dict(freeze=freeze,prepare=prepare,preflight=preflight,
            fit_synthetic=lambda:fit('synthetic'),predict_synthetic=lambda:old.predict('synthetic'),
            evaluate_synthetic=lambda:old.evaluate('synthetic'))
        actions[stage]()
    except Exception as ex:
        finish(stage,False,error=repr(ex));c.save(BASE/f'FAILURE_{stage}.json',dict(error=repr(ex),**usage()))
        c.status(BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)


if __name__=='__main__': main()
