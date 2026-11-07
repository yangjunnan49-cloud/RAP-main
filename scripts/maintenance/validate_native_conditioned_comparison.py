"""Independent Horn/NumPy audit plus bounded deterministic native replays for NOC4."""
import signal
import sys
import time
import numpy as np
import torch
import native_conditioned_comparison as r
import validate_native_pose_fit as v
from native_output_capability import args,prefix,tail,frozen_digest
from rap_slam.rap_precision import ieee_matmul
c=r.c


def arrays_equal(a,b):
    x,y=r.load(a),r.load(b);assert set(x)==set(y)
    for k in x: assert np.array_equal(x[k],y[k]),(str(a),k)


def preflight():
    r.check();r.old_deliveries();r.noise_check();r.check_seal(r.BASE/'preflight')
    z=r.load(r.BASE/'bank/synthetic_fixture.npz');original=c.read(r.BASE/'preflight/probes.json')
    mathematical=r.old.mathematical(z);assert v.difference(mathematical,c.read(r.BASE/'mathematical_preflight.json'))<1e-10
    m,params,initial,audit=r.model();b=r.n.noc.batch({k:z[k] for k in r.n.OBS})
    optimizer_max=cost_max=0.;records=[]
    with ieee_matmul():
        for arm in ('V','P'):
            folder=r.BASE/'preflight'/arm;replay=r.BASE/'preflight_replay'/arm
            info=r.probe(m,params,initial,z,b,arm,replay,full=True)
            stored=c.read(folder/'probe.json');a=dict(info);a.pop('forward');s=dict(stored);s.pop('forward')
            assert v.difference(a,s)==0
            for name in ('initial.npz','gradients.npz','parameters_after.npz','optimizer_final.npz','output_before.npz','output_after.npz'):
                arrays_equal(folder/name,replay/name)
            gradients=r.load(folder/'gradients.npz');after=r.load(folder/'parameters_after.npz')
            for k in initial:
                g=gradients[k].astype(np.float64)
                expected=initial[k].astype(np.float64)-1e-4*g/(np.abs(g)+1e-8)
                d=float(abs(after[k].astype(np.float64)-expected).max());assert d<1.5e-7,(k,d)
                optimizer_max=max(optimizer_max,d)
            for name,reference in (('output_before.npz',stored['loss_before']),('output_after.npz',stored['loss_after'])):
                if arm=='P':
                    cost,_=v.objective(z,r.load(folder/name)['output']);d=abs(cost-reference)
                    assert d<1e-7;cost_max=max(cost_max,d)
            records.append(info)
    assert original['passed']==all(x['passed'] for x in records)
    result=dict(passed=True,numerical_gate_passed=original['passed'],full_forward_probe_replays=2,
        gradient_parameter_output_optimizer_arrays_byteexact=True,NumPy_first_Adam_step_max_delta=optimizer_max,
        independent_Horn_objective_max_delta=cost_max,mathematics_repeated=True,
        optimizer_validation_probe_calls=2,retained_updates=0,not_independent_Adam_implementation=True,**r.usage())
    c.save(r.BASE/'validation_preflight.json',result)
    c.save(r.BASE/'validation_preflight_seal.json',dict(validation_sha256=c.sha(r.BASE/'validation_preflight.json'),
        preflight_seal_sha256=c.sha(r.BASE/'preflight/seal.json'),freeze_sha256=c.sha(r.BASE/'freeze.json')))
    r.finish('independent_preflight_audit');print('NOC4 preflight VALIDATED',result,flush=True)


def evaluate():
    r.check();r.old_deliveries();r.noise_check();r.admit('synthetic')
    rs=c.read(r.BASE/'results_synthetic_seal.json');result=c.read(r.BASE/'results_synthetic.json')
    assert c.sha(r.BASE/'results_synthetic.json')==rs['results_sha256']
    folder=r.BASE/'bank/synthetic_predictions';r.check_seal(folder)
    assert c.sha(folder/'seal.json')==rs['prediction_seal_sha256'] and c.sha(r.BASE/'freeze.json')==rs['freeze_sha256']
    z=r.load(r.BASE/'bank/synthetic_fixture.npz');centers=np.array([p.mean(0) for p in np.split(z['points'].astype(np.float64),3)])
    assert abs(centers-z['centers']).max()<1e-10
    target=np.concatenate([(p@T[:3,:3].T+T[:3,3]-centers[0])/float(z['scale'])
        for p,T in zip(np.split(z['points'],3),z['truth'])]).astype(np.float32)
    assert np.array_equal(target,z['target'])
    pose_delta=metric_delta=recurrence_delta=cost_delta=0.;independent=[]
    for record in result['records']:
        a=r.load(folder/f"{record['arm']}_{record['name']}.npz")
        noise=r.load(r.BASE/'bank/noise'/f"{record['name']}.npz")['noise']
        recurrence_delta=max(recurrence_delta,v.trace(z,noise,a));native=[]
        for step,stored in zip((0,4),record['native']):
            part=v.v.parts(z,a['end_point_trajectory'][step]);metric=v.v.metric(part,z['truth'])
            pd=float(abs(part-np.array(stored['parts'])).max());assert pd<1e-8;pose_delta=max(pose_delta,pd)
            metric_delta=max(metric_delta,v.v.compare_m(metric,stored['errors']))
            native.append(dict(step=step+1,parts=part.tolist(),errors=metric))
        cost,terms=v.objective(z,a['end_point_trajectory'][0])
        d=max(abs(cost-record['first_endpoint_pose_loss']),v.difference(terms,record['first_endpoint_terms']))
        assert d<1e-7;cost_delta=max(cost_delta,d)
        mse=float(np.mean((a['velocities'][0]-(noise-z['target']))**2));assert abs(mse-record['velocity_MSE'])<1e-10
        independent.append(dict(record,native=native));r.cap()
    summary=r.summarize(independent);aggregate_delta=v.difference(summary,result['summary']);assert aggregate_delta<1e-8
    for cell in summary['cells']:
        def values(arm,key):
            return [next(e[key] for e in row['native'][-1]['errors'] if e['part']==cell['part'])
                for row in independent if row['arm']==arm and row['role']=='eval']
        for comp in ('B','V'):
            tests=v.duplicated_gate(values(comp,'t_m'),values(comp,'R_deg'),values('P','t_m'),values('P','R_deg'))
            assert tests==cell['comparisons'][comp]['tests']
        absolute=sum(t<=.05 and a<=.2 for t,a in zip(values('P','t_m'),values('P','R_deg')))
        assert absolute==cell['absolute_pass']['P']
        assert cell['passed']==(absolute>=12 and all(x['passed'] for x in cell['comparisons'].values()))
    m,params,initial,audit=r.model();b=r.n.noc.batch({k:z[k] for k in r.n.OBS});full_replays=cache_replays=0
    with ieee_matmul():
        for row in r.noise_rows():
            with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda',dtype=torch.float32).cpu().numpy()
            assert np.array_equal(noise,r.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise'])
        for arm in ('B','V','P'):
            values=initial if arm=='B' else r.load(r.BASE/'bank'/f'synthetic_{arm}/parameters_0400.npz')
            if arm!='B':
                fitted=r.BASE/'bank'/f'synthetic_{arm}';r.check_seal(fitted);fit=c.read(fitted/'fit.json')
                arrays_equal(fitted/'initial.npz',r.BASE/'preflight'/arm/'initial.npz')
                assert fit['settings']==r.SETTINGS and fit['updates']==400 and fit['parameters']==443904
                assert [x['step'] for x in fit['rows']]==list(range(1,401))
                assert all(x['noise_index']==(x['step']-1)%8 and np.isfinite(x['loss']) and np.isfinite(x['norm']) for x in fit['rows'])
                assert all(x['groups']['B']>0 and x['groups']['MLP']>0 and x['parameter_change_norms']['B']>0
                    and x['parameter_change_norms']['MLP']>0 for x in fit['rows'])
                assert all(x['groups']['A']>0 for x in fit['rows'][1:])
                assert all(np.isfinite(a).all() for a in r.load(fitted/'optimizer_final.npz').values())
            r.assign(params,values);before=r.n.param_digest(params)
            if arm!='B': assert frozen_digest(m.flow_model)==fit['frozen_parameters_sha256']
            for row in (r.noise_rows()[8],r.noise_rows()[23]):
                noise=torch.tensor(r.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda')
                actual=r.generate(m,b,noise);stored=r.load(folder/f"{arm}_{row['name']}.npz")
                assert set(actual)==set(stored) and all(np.array_equal(actual[k],stored[k]) for k in actual);full_replays+=1
            if arm!='B':
                with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                    for row in (r.noise_rows()[0],r.noise_rows()[7]):
                        noise=torch.tensor(r.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda')
                        kw=args(b,noise,1.);e=prefix(m.flow_model,kw)
                        assert np.array_equal(e.cpu().numpy(),r.load(r.BASE/'bank/synthetic_cache'/f"{row['name']}.npz")['embedding'])
                        assert float(abs(tail(m.flow_model,e,kw)-m.flow_model(**kw)).max())==0;cache_replays+=1
            assert before==r.n.param_digest(params)
    r.check();r.old_deliveries()
    validation=dict(passed=True,traces=72,noise_replays=24,full_native_replays=full_replays,cache_full_replays=cache_replays,
        max_pose_delta=pose_delta,max_metric_delta=metric_delta,max_recurrence_delta=recurrence_delta,
        max_cost_delta=cost_delta,max_aggregate_delta=aggregate_delta,native_replays_byteexact=True,
        aggregate_code_shared_gate_independently_duplicated=True,full_optimizer_replay=False,
        full_census_replay=False,primary_conjunction=summary['primary_conjunction'],decision=summary['decision'],**r.usage())
    c.save(r.BASE/'validation_synthetic.json',validation)
    c.save(r.BASE/'validation_synthetic_seal.json',dict(validation_sha256=c.sha(r.BASE/'validation_synthetic.json'),
        results_seal_sha256=c.sha(r.BASE/'results_synthetic_seal.json')))
    r.finish('independent_synthetic_audit');print('NOC4 synthetic VALIDATED',validation,flush=True)


if __name__=='__main__':
    r.old.START=time.monotonic();stage=sys.argv[1]
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('NOC4 audit remaining combined wall')))
    signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in r.ledger()))))
    try: {'preflight':preflight,'synthetic':evaluate}[stage]()
    except Exception as ex:
        r.finish('validate_'+stage,False,error=repr(ex));c.save(r.BASE/f'FAILURE_validate_{stage}.json',dict(error=repr(ex),**r.usage()))
        c.status(r.BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)
