"""NOC2 fixed tiny pose/velocity fits; isolated from production and old banks."""
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path
import numpy as np
import torch
import local_motion_common as c
import native_pose_objective as o

spec=importlib.util.spec_from_file_location('noc1_reuse',Path(__file__).with_name('native_noise_census.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
from native_output_capability import adapt,trainables,args,prefix,tail,frozen_digest,poses,errors
from rap_slam.rap_precision import ieee_matmul
BASE=c.MAIN/'docs/maintenance/2026-10-10/native-pose-objective-fit-01'
START=None


def noise_rows():
    rows=[dict(name=f'{role}_{i:02d}',role=role,index=i,seed=int.from_bytes(
        hashlib.sha256(f'NOC2|20261010|{role}|{i}'.encode()).digest()[:4],'big'))
        for role,count in (('fit',8),('eval',16)) for i in range(count)]
    values=[x['seed'] for x in rows]
    assert len(set(values))==24 and not set(values)&({x['seed'] for x in n.noise_rows()}|{20261010})
    return rows


def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_initialized() else 0,
        artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()))
def ledger(): return c.read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
def cap():
    u=usage();assert sum(x['wall_seconds'] for x in ledger())+u['wall_seconds']<=1800,'wall cap'
    assert u['peak_RSS_bytes']<=4*2**30 and max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=3*2**30
    assert u['artifact_bytes']<=512*2**20
def finish(stage,success=True,**kw):
    if success: cap()
    (BASE/'RESOURCE_LOG.json').write_text(json.dumps(ledger()+[dict(stage=stage,success=success,utc=c.now(),**usage(),**kw)],indent=2,allow_nan=False)+'\n')
def seal(folder):
    c.save(folder/'seal.json',dict(files={str(p.relative_to(folder)):c.sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def check_seal(folder):
    s=c.read(folder/'seal.json')
    for p,h in s['files'].items(): assert c.sha(folder/p)==h,p
def old_deliveries():
    counts=[]
    for folder,count in ((n.OLD,103),(n.BASE,188)):
        rows=c.read(folder/'DELIVERY_SEAL.json')['files'];assert len(rows)==count
        for row in rows: assert c.sha(folder/row['path'])==row['sha256'],row['path']
        counts.append(count)
    return counts
def check():
    f=c.read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert c.sha(p)==h,p
    assert f['noise_rows']==noise_rows() and f['runtime']['torch']==torch.__version__
    assert f['runtime']['numpy']==np.__version__ and torch.get_num_threads()==1
    return f
def freeze():
    old_deliveries();f=n.check();repos=n.noc.git_state();assert repos==f['repositories']
    files=dict(f['files'])
    for p in [Path(__file__),Path(__file__).with_name('native_pose_objective.py'),
        Path(__file__).with_name('validate_native_pose_fit.py'),Path(__file__).with_name('close_native_pose_fit.py'),
        BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',n.BASE/'DELIVERY_SEAL.json',n.BASE/'freeze.json',n.BASE/'results.json']:
        files[str(p)]=c.sha(p)
    snap=BASE/'source_snapshot';snap.mkdir()
    for name in ('native_pose_fit.py','native_pose_objective.py','validate_native_pose_fit.py','close_native_pose_fit.py'):
        (snap/name).write_bytes(Path(__file__).with_name(name).read_bytes())
    c.save(BASE/'freeze.json',dict(files=files,repositories=repos,noise_rows=noise_rows(),updates=400,
        native_params=443904,affine_params=36,objective_scales=dict(t_m=.05,R_deg=.2,shape_weight=.001),
        native_lr=1e-4,control_lr=1e-3,weight_decay=1e-4,clip_norm=1,velocity_backward_scale=1024,
        native_P_backward_scale=1,init_seed=20261010,training_tau=1,conditional_real_windows=1,
        limits=dict(wall_seconds=1800,GPU_bytes=3*2**30,RSS_bytes=4*2**30,artifact_bytes=512*2**20),
        runtime=dict(torch=torch.__version__,numpy=np.__version__,python=sys.version,threads=1,gpu=torch.cuda.get_device_name(0))))
    (BASE/'INCOMPLETE').write_text('NOC2 frozen; all declared prerequisites/fits/validation pending.\n')
    c.status(BASE,'frozen',status='AUTHORIZED_FROZEN');finish('freeze');print('NOC2 frozen',len(files),flush=True)
def tensors(z):
    return [torch.tensor(z[k],device='cuda') for k in ('cond','centers','scale','truth')]
def obj(z,q):
    cond,centers,scale,truth=tensors(z);return o.objective(cond,q,centers,scale,truth)
def model():
    m,audit=n.noc.load_model()
    with c.rng(20261010): adapt(m.flow_model)
    p=trainables(m.flow_model);initial=n.load(n.RETRY/'bank/synthetic_native_lr1e-4/initial.npz')
    assert all(np.array_equal(x.detach().cpu().numpy(),initial[k]) for k,x in p.items())
    assert sum(x.numel() for x in p.values())==443904
    return m,p,initial,audit
def assign(params,values):
    with torch.no_grad():
        for k,p in params.items(): p.copy_(torch.tensor(values[k],device=p.device))
def generate(m,b,noise):
    assert 'target' not in b and 'truth' not in b and b['pointclouds_gt'] is b['pointclouds']
    captured=[]
    def hook(module,inputs,kw,out):
        captured.append((kw['x'].detach().cpu().numpy().copy(),out.detach().cpu().numpy().copy(),kw['timesteps'].cpu().numpy().copy()))
    handle=m.flow_model.register_forward_hook(hook,with_kwargs=True)
    try:
        with c.rng(20261010),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
            native=m.sample_rectified_flow(b,None,x_1=noise,return_tarjectory=True)
    finally: handle.remove()
    assert len(captured)==5
    out={k:v.cpu().numpy().copy() for k,v in native.items()}
    out.update(input_states=np.stack([x[0] for x in captured]),velocities=np.stack([x[1] for x in captured]),taus=np.concatenate([x[2] for x in captured]))
    cap();return out
def mathematical(z):
    x=torch.tensor(z['cond'],dtype=torch.float64);centers=torch.tensor(z['centers']);scale=torch.tensor(z['scale']);truth=torch.tensor(z['truth'])
    y=torch.tensor(z['target'],dtype=torch.float64)
    loss,_=o.objective(x,y,centers,scale,truth);assert float(loss)<1e-8,float(loss)
    matrices=truth[:,:3,:3];bias=((matrices@centers.unsqueeze(2)).squeeze(2)+truth[:,:3,3]-centers[0])/scale
    exact=(x.reshape(3,1000,3)@matrices.transpose(1,2)+bias[:,None]).reshape(3000,3)
    affine_delta=float(abs(exact-y).max());assert affine_delta<2e-7
    # Nonzero loss avoids an uninformative finite difference at the optimum.
    q=x.clone().requires_grad_();cost,_=o.objective(x,q,centers,scale,truth);g=torch.autograd.grad(cost,q)[0]
    from scipy.spatial.transform import Rotation
    G=torch.tensor(Rotation.from_rotvec([.2,-.3,.1]).as_matrix());shift=torch.tensor([.4,-.2,.1])
    gauge,_=o.objective(x,q@G.T+shift,centers,scale,truth)
    gd=abs(float(gauge-cost));assert gd<1e-7,gd
    directions=[]
    rng=np.random.default_rng(417)
    d=torch.tensor(rng.normal(size=(3000,3)));d/=torch.linalg.norm(d);directions.append(d)
    d=torch.zeros_like(q);d[1000:2000,0]=1;directions.append(d)
    d=torch.zeros_like(q);d[2000:,1]=1;directions.append(d)
    checks=[]
    with torch.no_grad():
        for d in directions:
            h=1e-6;a=float((g*d).sum());plus=o.objective(x,q+h*d,centers,scale,truth)[0];minus=o.objective(x,q-h*d,centers,scale,truth)[0]
            fd=float((plus-minus)/(2*h));delta=abs(fd-a);assert delta<=max(1e-5,abs(a)*1e-6),(a,fd,delta)
            checks.append(dict(analytic=a,finite_difference=fd,absolute_delta=delta))
    return dict(exact_target_loss=float(loss),analytic_affine_max_delta=affine_delta,gauge_loss_delta=gd,
        output_directional_FD=checks,passed=True,model_loaded=False)
def prepare():
    check();(BASE/'bank').mkdir();(BASE/'bank/noise').mkdir()
    z=n.load(n.RETRY/'bank/synthetic_fixture.npz');(BASE/'bank/synthetic_fixture.npz').write_bytes((n.RETRY/'bank/synthetic_fixture.npz').read_bytes())
    c.save(BASE/'mathematical_preflight.json',mathematical(z))
    for row in noise_rows():
        with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda',dtype=torch.float32).cpu().numpy()
        np.savez(BASE/'bank/noise'/f"{row['name']}.npz",noise=noise);cap()
    c.save(BASE/'noise_seal.json',dict(rows=noise_rows(),files={str(p.relative_to(BASE)):c.sha(p) for p in sorted((BASE/'bank/noise').glob('*.npz'))}))
    folder=BASE/'bank/control';folder.mkdir();control=o.Affine();params=dict(control.named_parameters());assert sum(p.numel() for p in params.values())==36
    np.savez(folder/'initial.npz',**n.noc.numpy_state(params));opt=torch.optim.AdamW(params.values(),lr=1e-3,weight_decay=1e-4)
    x,centers,scale,truth=tensors(z);rows=[]
    for step in range(1,401):
        opt.zero_grad(set_to_none=True);q=control(x);loss,terms=o.objective(x,q,centers,scale,truth);loss.backward()
        assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in params.values())
        norm=float(torch.nn.utils.clip_grad_norm_(params.values(),1));opt.step();cap()
        rows.append(dict(step=step,loss=float(loss.detach()),terms={k:float(v.detach()) for k,v in terms.items()},norm=norm))
    with torch.no_grad(): q=control(x).cpu().numpy()
    err=errors(poses(z['cond'],q,z['centers'],float(z['scale'])),z['truth']);passed=all(e['t_m']<=.005 and e['R_deg']<=.05 for e in err)
    np.savez(folder/'parameters_0400.npz',**n.noc.numpy_state(params));np.savez(folder/'output.npz',output=q)
    n.noc.save_opt(folder,opt,params);c.save(folder/'fit.json',dict(updates=400,parameters=36,rows=rows,errors=err,passed=passed));seal(folder)
    c.status(BASE,'prepared',status='CONTROL_COMPLETE',control_passed=passed);finish('math_noise_control');print('NOC2 control',passed,err,flush=True)
def noise_check():
    s=c.read(BASE/'noise_seal.json');assert s['rows']==noise_rows()
    for p,h in s['files'].items(): assert c.sha(BASE/p)==h,p
def admit(fixture):
    if fixture=='synthetic':
        check_seal(BASE/'bank/control');assert c.read(BASE/'bank/control/fit.json')['passed'],'affine prerequisite failed'
    else:
        assert c.read(BASE/'validation_synthetic.json')['passed'] and c.read(BASE/'results_synthetic.json')['summary']['primary_conjunction']
def fit(fixture):
    check();noise_check();admit(fixture)
    if fixture=='real': (BASE/'bank/real_fixture.npz').write_bytes((n.RETRY/'bank/real_fixture.npz').read_bytes())
    z=n.load(BASE/f'bank/{fixture}_fixture.npz');m,params,initial,audit=model();b=n.noc.batch({k:z[k] for k in n.OBS})
    frozen=frozen_digest(m.flow_model);y=torch.tensor(z['target'],device='cuda');x,centers,scale,truth=tensors(z)
    cache=[];cfolder=BASE/'bank'/f'{fixture}_cache';cfolder.mkdir();prefix_deltas=[]
    with ieee_matmul(),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
        for row in noise_rows()[:8]:
            noise=torch.tensor(n.load(BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda');kw=args(b,noise,1.);e=prefix(m.flow_model,kw)
            delta=float(abs(tail(m.flow_model,e,kw)-m.flow_model(**kw)).max());assert delta==0,delta;prefix_deltas.append(delta)
            np.savez(cfolder/f"{row['name']}.npz",embedding=e.cpu().numpy());cache.append((e,kw,noise))
    seal(cfolder)
    with ieee_matmul():
        for arm in ('V','P'):
            assign(params,initial);folder=BASE/'bank'/f'{fixture}_{arm}';folder.mkdir();np.savez(folder/'initial.npz',**n.noc.numpy_state(params))
            opt=torch.optim.AdamW(params.values(),lr=1e-4,weight_decay=1e-4);rows=[]
            for step in range(1,401):
                e,kw,noise=cache[(step-1)%8];opt.zero_grad(set_to_none=True)
                with torch.autocast('cuda',dtype=torch.float16): velocity=tail(m.flow_model,e,kw)
                if arm=='V': loss=(velocity-(noise-y)).square().mean();terms=dict(velocity=loss);factor=1024
                else: loss,terms=o.objective(x,noise-velocity,centers,scale,truth);factor=1
                (loss*factor).backward()
                if factor!=1:
                    for p in params.values(): p.grad.div_(factor)
                groups=n.noc.inspect_grad(params);assert groups['B']>0 and groups['MLP']>0
                if step>1: assert groups['A']>0
                if step==1:
                    param=params['final_mlp.4.weight'];a=float(param.grad[0,0]);saved=float(param[0,0]);vals=[]
                    with torch.no_grad():
                        for sign in (-1,1):
                            param[0,0]=saved+sign*.001
                            with torch.autocast('cuda',dtype=torch.float16): vv=tail(m.flow_model,e,kw)
                            vals.append(float((vv-(noise-y)).square().mean()) if arm=='V' else float(o.objective(x,noise-vv,centers,scale,truth)[0]))
                        param[0,0]=saved
                    fd=(vals[1]-vals[0])/.002;assert abs(fd-a)<=max(2e-4,.02*abs(a)),(arm,fd,a)
                    c.save(folder/'gradient_preflight.json',dict(groups=groups,analytic=a,finite_difference=fd,absolute_delta=abs(fd-a),passed=True,optimizer_updates=0))
                norm=float(torch.nn.utils.clip_grad_norm_(params.values(),1));assert np.isfinite(norm);opt.step();cap()
                rows.append(dict(step=step,noise_index=(step-1)%8,loss=float(loss.detach()),terms={k:float(v.detach()) for k,v in terms.items()},norm=norm,groups=groups))
                if step in (100,400): np.savez(folder/f'parameters_{step:04d}.npz',**n.noc.numpy_state(params))
                if step%100==0: print('NOC2',fixture,arm,step,rows[-1]['loss'],flush=True)
            n.noc.save_opt(folder,opt,params);deltas=[]
            with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                for e,kw,noise in cache:
                    delta=float(abs(tail(m.flow_model,e,kw)-m.flow_model(**kw)).max());assert delta==0;deltas.append(delta)
            assert frozen_digest(m.flow_model)==frozen
            c.save(folder/'fit.json',dict(arm=arm,fixture=fixture,updates=400,parameters=443904,lr=1e-4,rows=rows,
                initial_cache_full_deltas=prefix_deltas,final_cache_full_deltas=deltas,frozen_parameters_sha256=frozen,
                objective='pure_noise_velocity_MSE' if arm=='V' else 'metric_relative_pose_plus_shape',checkpoint=audit));seal(folder)
    finish('fit_'+fixture);c.status(BASE,'fit_'+fixture,status='FITS_COMPLETE_PREDICTIONS_PENDING')
def predict(fixture):
    check();noise_check();admit(fixture);z=n.load(BASE/f'bank/{fixture}_fixture.npz')
    m,params,initial,audit=model();b=n.noc.batch({k:z[k] for k in n.OBS});folder=BASE/'bank'/f'{fixture}_predictions';folder.mkdir()
    frozen=frozen_digest(m.flow_model)
    for arm in ('B','V','P'):
        values=initial if arm=='B' else n.load(BASE/'bank'/f'{fixture}_{arm}/parameters_0400.npz')
        if arm!='B': check_seal(BASE/'bank'/f'{fixture}_{arm}')
        assign(params,values);before=n.param_digest(params)
        with ieee_matmul():
            for row in noise_rows():
                noise=torch.tensor(n.load(BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda')
                out=generate(m,b,noise);assert all(np.isfinite(a).all() for a in out.values())
                np.savez(folder/f"{arm}_{row['name']}.npz",**out);cap()
        assert before==n.param_digest(params) and frozen_digest(m.flow_model)==frozen
    seal(folder);finish('predict_'+fixture);print('NOC2',fixture,'72 predictions sealed',flush=True)
def stats(values): return n.distribution(values)
def summarize(records):
    cells=[]
    for part in (1,2):
        by={arm:[next(e for e in row['native'][-1]['errors'] if e['part']==part)
            for row in records if row['arm']==arm and row['role']=='eval'] for arm in ('B','V','P')}
        summaries={arm:{k:stats([v[key] for v in by[arm]]) for k,key in (('t','t_m'),('R','R_deg'))} for arm in by}
        comparisons={}
        for comp in ('B','V'):
            bt,br,pt,pr=([v[key] for v in by[arm]] for arm,key in ((comp,'t_m'),(comp,'R_deg'),('P','t_m'),('P','R_deg')))
            tests=o.gate(bt,br,pt,pr);comparisons[comp]=dict(tests=tests,passed=all(tests.values()),
                joint_nonworse=int(np.count_nonzero((np.array(pt)<=bt)&(np.array(pr)<=br))),
                paired_t_gain=stats(np.array(bt)-pt),paired_R_gain=stats(np.array(br)-pr))
        absolute={arm:sum(v['t_m']<=.05 and v['R_deg']<=.2 for v in vals) for arm,vals in by.items()}
        passed=absolute['P']>=12 and all(v['passed'] for v in comparisons.values())
        cells.append(dict(part=part,arms=summaries,comparisons=comparisons,absolute_pass=absolute,passed=passed))
    passed=all(x['passed'] for x in cells)
    return dict(cells=cells,primary_conjunction=passed,decision='FRESH_NOISE_POSE_OBJECTIVE_SIGNAL' if passed else 'NO_FRESH_NOISE_POSE_OBJECTIVE_CONJUNCTION')
def evaluate(fixture):
    check();folder=BASE/'bank'/f'{fixture}_predictions';check_seal(folder);z=n.load(BASE/f'bank/{fixture}_fixture.npz');records=[]
    for arm in ('B','V','P'):
        for row in noise_rows():
            a=n.load(folder/f"{arm}_{row['name']}.npz");native=[]
            for step in (0,4):
                part=poses(z['cond'],a['end_point_trajectory'][step],z['centers'],float(z['scale']))
                native.append(dict(step=step+1,parts=part.tolist(),errors=errors(part,z['truth'])))
            q=torch.tensor(a['end_point_trajectory'][0],device='cuda');loss,terms=obj(z,q)
            mse=float(np.mean((a['velocities'][0]-(n.load(BASE/'bank/noise'/f"{row['name']}.npz")['noise']-z['target']))**2))
            records.append(dict(arm=arm,**row,native=native,first_endpoint_pose_loss=float(loss),first_endpoint_terms={k:float(v) for k,v in terms.items()},velocity_MSE=mse))
    result=dict(fixture=fixture,records=records,summary=summarize(records));c.save(BASE/f'results_{fixture}.json',result)
    c.save(BASE/f'results_{fixture}_seal.json',dict(results_sha256=c.sha(BASE/f'results_{fixture}.json'),prediction_seal_sha256=c.sha(folder/'seal.json'),freeze_sha256=c.sha(BASE/'freeze.json')))
    finish('evaluate_'+fixture);print('NOC2',fixture,result['summary']['decision'],flush=True)


if __name__=='__main__':
    START=time.monotonic();stage=sys.argv[1]
    def alarm(signum,frame): raise TimeoutError('NOC2 combined remaining wall exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in ledger()))))
    try:
        if stage=='freeze': freeze()
        elif stage=='prepare': prepare()
        else:
            action,fixture=stage.split('_');{'fit':fit,'predict':predict,'evaluate':evaluate}[action](fixture)
    except Exception as ex:
        finish(stage,False,error=repr(ex));c.save(BASE/f'FAILURE_{stage}.json',dict(error=repr(ex),**usage()))
        c.status(BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)
