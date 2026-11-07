"""NOC2 independent Horn geometry/cost/gradient checks and bounded forwards."""
import importlib.util
import math
import signal
import sys
import time
from pathlib import Path
import numpy as np
import torch
import local_motion_common as c
import native_pose_fit as r
from native_output_capability import args,prefix,tail,frozen_digest
from rap_slam.rap_precision import ieee_matmul

spec=importlib.util.spec_from_file_location('noc0_horn',Path(__file__).with_name('validate_native_output_capability.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def objective(z,q):
    part=v.parts(z,q);metric=v.metric(part,z['truth']);shape=[]
    for k in range(3):
        sl=slice(k*1000,(k+1)*1000);R,b,gap=v.horn(z['cond'][sl],q[sl]);assert gap>1e-6
        residual=float(z['scale'])*(q[sl]-z['cond'][sl]@R.T-b);shape.append(float(np.mean(residual**2)))
    translation=float(np.mean([(e['t_m']/.05)**2 for e in metric]))
    rotation=[]
    for k in (1,2):
        rel=np.linalg.solve(part[0],part[k]);delta=z['truth'][k,:3,:3].T@rel[:3,:3]-np.eye(3)
        rotation.append(float(np.sum(delta**2)/(2*math.radians(.2)**2)))
    terms=dict(translation=translation,rotation=float(np.mean(rotation)),shape=.001*float(np.mean(shape))/.05**2)
    return sum(terms.values()),terms
def duplicated_gate(bt,br,at,ar):
    bt,br,at,ar=map(np.asarray,(bt,br,at,ar));dt=bt-at;dr=br-ar
    return {k:bool(x) for k,x in dict(mean_t=at.mean()<=.9*bt.mean(),median_t=np.median(dt)>=.005,
        mean_R=ar.mean()<=br.mean()+.01,median_R=np.median(dr)>=0,
        joint_signs=np.count_nonzero((at<=bt)&(ar<=br))>=12,
        q90_t=np.percentile(at,90)<=1.05*np.percentile(bt,90),q90_R=np.percentile(ar,90)<=np.percentile(br,90)+.02).items()}
def difference(a,b):
    if isinstance(a,dict): assert set(a)==set(b);return max([difference(a[k],b[k]) for k in a]+[0])
    if isinstance(a,list): assert len(a)==len(b);return max([difference(x,y) for x,y in zip(a,b)]+[0])
    if isinstance(a,(bool,str)) or a is None: assert a==b;return 0
    return abs(float(a)-float(b))
def trace(z,noise,a):
    assert np.array_equal(noise,a['input_states'][0]);maximum=0
    assert abs(a['taus']-np.array([1,.8,.6,.4,.2])).max()<3e-8
    for i in range(5):
        t=1-i*.2;raw=a['end_point_trajectory'][i]
        assert abs(raw-(a['input_states'][i]-t*a['velocities'][i])).max()<1e-6
        projected=[]
        for k in range(3):
            sl=slice(k*1000,(k+1)*1000);R,b,gap=v.horn(z['cond'][sl],raw[sl]);assert gap>1e-6
            projected.append(z['cond'][sl]@R.T+b)
        expected=np.concatenate(projected)*(1-t+.2)+noise*(t-.2)
        d=float(abs(expected-a['trajectory'][i]).max());assert d<3e-5;maximum=max(maximum,d)
        if i<4: assert np.array_equal(a['input_states'][i+1],a['trajectory'][i])
    return maximum
def control():
    r.check_seal(r.BASE/'bank/control');z=r.n.load(r.BASE/'bank/synthetic_fixture.npz')
    f=c.read(r.BASE/'bank/control/fit.json');assert f['updates']==400 and f['parameters']==36
    assert [x['step'] for x in f['rows']]==list(range(1,401))
    assert all(np.isfinite(x['loss']) and np.isfinite(x['norm']) for x in f['rows'])
    values=r.n.load(r.BASE/'bank/control/parameters_0400.npz');x=z['cond'].reshape(3,1000,3)
    q=(x@values['matrix'].transpose(0,2,1)+values['bias'][:,None]).reshape(3000,3)
    stored=r.n.load(r.BASE/'bank/control/output.npz')['output'];assert abs(q-stored).max()<2e-7
    errors=v.metric(v.parts(z,stored),z['truth']);v.compare_m(errors,f['errors'])
    passed=all(e['t_m']<=.005 and e['R_deg']<=.05 for e in errors);assert passed==f['passed']
    math_original=c.read(r.BASE/'mathematical_preflight.json');math_again=r.mathematical(z)
    assert difference(math_original,math_again)<1e-10
    return dict(passed=passed,errors=errors,affine_forward_max_delta=float(abs(q-stored).max()),math_preflight_reproduced=True)
def run(fixture):
    r.check();r.old_deliveries();r.noise_check();ctrl=control()
    if fixture=='control':
        c.save(r.BASE/'validation_control.json',dict(passed=True,control=ctrl,**r.usage()))
        c.save(r.BASE/'validation_control_seal.json',dict(validation_sha256=c.sha(r.BASE/'validation_control.json'),control_seal_sha256=c.sha(r.BASE/'bank/control/seal.json'),freeze_sha256=c.sha(r.BASE/'freeze.json')))
        r.finish('validate_control');print('NOC2 control independently validated',ctrl,flush=True);return
    assert ctrl['passed'];r.admit(fixture)
    rs=c.read(r.BASE/f'results_{fixture}_seal.json');result=c.read(r.BASE/f'results_{fixture}.json')
    assert c.sha(r.BASE/f'results_{fixture}.json')==rs['results_sha256']
    folder=r.BASE/'bank'/f'{fixture}_predictions';r.check_seal(folder)
    assert c.sha(folder/'seal.json')==rs['prediction_seal_sha256'] and c.sha(r.BASE/'freeze.json')==rs['freeze_sha256']
    z=r.n.load(r.BASE/f'bank/{fixture}_fixture.npz');centers=np.array([p.mean(0) for p in np.split(z['points'].astype(np.float64),3)])
    assert abs(centers-z['centers']).max()<1e-10
    target=np.concatenate([(p@T[:3,:3].T+T[:3,3]-centers[0])/float(z['scale']) for p,T in zip(np.split(z['points'],3),z['truth'])]).astype(np.float32)
    assert np.array_equal(target,z['target']);assert all(e['t_m']<1e-5 and e['R_deg']<1e-5 for e in v.metric(v.parts(z,target),z['truth']))
    pose_delta=metric_delta=recurrence_delta=cost_delta=0.;independent=[]
    for record in result['records']:
        a=r.n.load(folder/f"{record['arm']}_{record['name']}.npz");noise=r.n.load(r.BASE/'bank/noise'/f"{record['name']}.npz")['noise']
        recurrence_delta=max(recurrence_delta,trace(z,noise,a));native=[]
        for step,old in zip((0,4),record['native']):
            part=v.parts(z,a['end_point_trajectory'][step]);metric=v.metric(part,z['truth'])
            pd=float(abs(part-np.array(old['parts'])).max());assert pd<1e-8;pose_delta=max(pose_delta,pd)
            metric_delta=max(metric_delta,v.compare_m(metric,old['errors']));native.append(dict(step=step+1,parts=part.tolist(),errors=metric))
        cost,terms=objective(z,a['end_point_trajectory'][0]);d=max(abs(cost-record['first_endpoint_pose_loss']),difference(terms,record['first_endpoint_terms']))
        assert d<1e-7,d;cost_delta=max(cost_delta,d)
        mse=float(np.mean((a['velocities'][0]-(noise-z['target']))**2));assert abs(mse-record['velocity_MSE'])<1e-10
        independent.append(dict(record,native=native));r.cap()
    summary=r.summarize(independent);aggregate_delta=difference(summary,result['summary']);assert aggregate_delta<1e-8
    for cell in summary['cells']:
        def values(arm,key):
            return [next(e[key] for e in row['native'][-1]['errors'] if e['part']==cell['part']) for row in independent if row['arm']==arm and row['role']=='eval']
        for comp in ('B','V'):
            tests=duplicated_gate(values(comp,'t_m'),values(comp,'R_deg'),values('P','t_m'),values('P','R_deg'))
            assert tests==cell['comparisons'][comp]['tests']
    m,params,initial,audit=r.model();b=r.n.noc.batch({k:z[k] for k in r.n.OBS});full_replays=prefix_replays=0;max_forward=0
    with ieee_matmul():
        for row in r.noise_rows():
            with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda',dtype=torch.float32).cpu().numpy()
            assert np.array_equal(noise,r.n.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise'])
        for arm in ('B','V','P'):
            values=initial if arm=='B' else r.n.load(r.BASE/'bank'/f'{fixture}_{arm}/parameters_0400.npz')
            if arm!='B':
                fitted=r.BASE/'bank'/f'{fixture}_{arm}';r.check_seal(fitted);fit=c.read(fitted/'fit.json')
                assert fit['updates']==400 and fit['parameters']==443904 and fit['lr']==1e-4
                assert [x['step'] for x in fit['rows']]==list(range(1,401))
                assert all(x['noise_index']==(x['step']-1)%8 and np.isfinite(x['loss']) and np.isfinite(x['norm']) for x in fit['rows'])
                assert all(x['groups']['B']>0 and x['groups']['MLP']>0 for x in fit['rows'])
                assert all(x['groups']['A']>0 for x in fit['rows'][1:])
                opt=r.n.load(fitted/'optimizer_final.npz');assert all(np.isfinite(a).all() for a in opt.values())
            r.assign(params,values);before=r.n.param_digest(params)
            if arm!='B': assert frozen_digest(m.flow_model)==fit['frozen_parameters_sha256']
            for row in (r.noise_rows()[8],r.noise_rows()[23]):
                noise=torch.tensor(r.n.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda');a=r.generate(m,b,noise)
                saved=r.n.load(folder/f"{arm}_{row['name']}.npz");assert all(np.array_equal(a[k],saved[k]) for k in a);full_replays+=1
            if arm!='B':
                with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                    for row in (r.noise_rows()[0],r.noise_rows()[7]):
                        noise=torch.tensor(r.n.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda');kw=args(b,noise,1.)
                        embedding=prefix(m.flow_model,kw);stored=r.n.load(r.BASE/'bank'/f'{fixture}_cache'/f"{row['name']}.npz")['embedding']
                        assert np.array_equal(embedding.cpu().numpy(),stored)
                        vv=tail(m.flow_model,embedding,kw);whole=m.flow_model(**kw)
                        d=float(abs(vv-whole).max());assert d==0;max_forward=max(max_forward,d);prefix_replays+=1
                # Repeat selected first-update gradient at the exact initialized parameter array, zero updates.
                r.assign(params,initial);noise=torch.tensor(r.n.load(r.BASE/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=args(b,noise,1.)
                with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16): e=prefix(m.flow_model,kw)
                for p in params.values(): p.grad=None
                with torch.autocast('cuda',dtype=torch.float16): vv=tail(m.flow_model,e,kw)
                loss=(vv-(noise-torch.tensor(z['target'],device='cuda'))).square().mean() if arm=='V' else r.obj(z,noise-vv)[0]
                factor=1024 if arm=='V' else 1;(loss*factor).backward()
                if factor!=1:
                    for p in params.values(): p.grad.div_(factor)
                preflight=c.read(fitted/'gradient_preflight.json');assert abs(float(params['final_mlp.4.weight'].grad[0,0])-preflight['analytic'])<1e-7
                r.assign(params,values)
            assert before==r.n.param_digest(params)
    r.check();r.old_deliveries()
    validation=dict(passed=True,fixture=fixture,control=ctrl,traces=len(independent),noise_replays=24,full_native_replays=full_replays,
        cache_full_replays=prefix_replays,selected_initial_gradients_reproduced=2,max_pose_delta=pose_delta,max_metric_delta=metric_delta,
        max_recurrence_delta=recurrence_delta,max_cost_delta=cost_delta,max_aggregate_delta=aggregate_delta,max_forward_delta=max_forward,
        aggregate_code_shared_gate_independently_duplicated=True,full_optimizer_replay=False,full_census_replay=False,
        primary_conjunction=summary['primary_conjunction'],decision=summary['decision'],**r.usage())
    c.save(r.BASE/f'validation_{fixture}.json',validation)
    c.save(r.BASE/f'validation_{fixture}_seal.json',dict(validation_sha256=c.sha(r.BASE/f'validation_{fixture}.json'),results_seal_sha256=c.sha(r.BASE/f'results_{fixture}_seal.json')))
    r.finish('validate_'+fixture);print('NOC2 VALIDATED',fixture,validation,flush=True)


if __name__=='__main__':
    r.START=time.monotonic();fixture=sys.argv[1]
    def alarm(signum,frame): raise TimeoutError('NOC2 validation remaining wall exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in r.ledger()))))
    try: run(fixture)
    except Exception as ex:
        r.finish('validate_'+fixture,False,error=repr(ex));c.save(r.BASE/f'FAILURE_validate_{fixture}.json',dict(error=repr(ex),**r.usage()))
        c.status(r.BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)
