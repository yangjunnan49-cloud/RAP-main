"""NOC3 independent scipy/Horn/FD audit and complete deterministic replay."""
import signal
import time
import numpy as np
import torch
import local_motion_common as c
import rigid_control_conditioning as r
import rigid_metric_control as m
import rigid_control_reference as ref


def run():
    r.check();r.old_deliveries();r.preflight_check();r.bank_check();z=r.load(r.BASE/'fixture.npz')
    rs=c.read(r.BASE/'results_seal.json');assert c.sha(r.BASE/'results.json')==rs['results_sha256']
    assert c.sha(r.BASE/'bank_seal.json')==rs['bank_seal_sha256'];result=c.read(r.BASE/'results.json')
    pf=r.load(r.BASE/'preflight.npz');preflight=c.read(r.BASE/'preflight.json')
    cost_delta=grad_delta=pose_delta=output_delta=0.;trial_count=0;hessian_delta=0.
    for label in ('zero','probe','reference'):
        p=pf[label+'_parameters'];fd=ref.gradient(z,p)
        for route in ('DIRECT','DECODE'):
            g=pf[f'{label}_{route}_gradient'];d=float(abs(g-fd).max())
            assert np.all(abs(g-fd)<=np.maximum(5e-5,abs(g)*1e-6));grad_delta=max(grad_delta,d)
        record=next(x for x in preflight['probes'] if x['probe']==label)
        for v in record['costs'].values(): cost_delta=max(cost_delta,abs(v-ref.direct_cost(z,p)))
    independent_hessian=ref.hessian_zero(z)
    for name in m.CASES:
        d=m.units(name).numpy().reshape(12);expected=independent_hessian*d[:,None]*d[None,:]
        H=pf[name+'_hessian'];delta=float(abs(H-expected).max())
        assert delta<=max(.001,abs(H).max()*1e-6),(name,delta);hessian_delta=max(hessian_delta,delta)
        eigen=np.linalg.eigvalsh((H+H.T)/2);assert eigen.min()>1e-8
        stored=next(x for x in preflight['hessian_summary'] if x['case']==name)
        assert abs(eigen-np.array(stored['eigenvalues'])).max()<1e-9
    replay_delta=0.;replayed=0;all_gate=[];replay_iterations=0;replay_closures=0
    for name in m.CASES:
        a=r.load(r.BASE/'bank'/name/'trace.npz');unit=m.units(name).numpy();record=next(x for x in result['records'] if x['case']==name)
        assert np.array_equal(a['units'],unit) and np.array_equal(a['trace_solver'][0],np.zeros((2,6)))
        assert abs(a['trace_solver']*unit-a['trace_physical']).max()==0
        for i,p in enumerate(a['trace_physical']):
            direct=ref.direct_cost(z,p);q=ref.output(z,p);T,shape=ref.decode(z,q)
            decoded=ref.cost_from_poses(z,T,shape);pd=float(abs(T-ref.poses(p)).max());assert pd<1e-10
            cost_delta=max(cost_delta,abs(direct-a['trace_cost'][i]),abs(decoded-a['trace_cost'][i]));pose_delta=max(pose_delta,pd)
            fd=ref.gradient(z,p)*unit;g=a['trace_gradient'][i];d=float(abs(fd-g).max())
            assert np.all(abs(fd-g)<=np.maximum(5e-5,abs(g)*1e-6)),(name,i,d)
            grad_delta=max(grad_delta,d);trial_count+=1;r.cap()
        assert cost_delta<1e-7,cost_delta
        expected=ref.output(z,a['final_physical']);od=float(abs(expected-a['final_output']).max());assert od<1e-12;output_delta=max(output_delta,od)
        T,shape=ref.decode(z,a['final_output']);physical=ref.poses(a['final_physical']);pd=float(abs(T-physical).max());assert pd<1e-10;pose_delta=max(pose_delta,pd)
        assert abs(a['final_rotations']-physical[:,:3,:3]).max()<1e-12
        assert abs(a['final_translations']-physical[:,:3,3]).max()<1e-12
        errors=ref.metrics(z,T)
        for e,saved in zip(errors,record['errors']):
            assert e['part']==saved['part'] and max(abs(e[k]-saved[k]) for k in ('t_m','R_deg'))<1e-12
        gradient=ref.gradient(z,a['final_physical'])*m.units('SCALED_DIRECT').numpy()
        analytic=a['final_gradient']/unit*m.units('SCALED_DIRECT').numpy()
        assert abs(gradient-analytic).max()<5e-6
        proper=abs(physical[:,:3,:3].transpose(0,2,1)@physical[:,:3,:3]-np.eye(3)).max()<1e-10 and abs(np.linalg.det(physical[:,:3,:3])-1).max()<1e-10
        tests=dict(pose=all(e['t_m']<=.005 and e['R_deg']<=.05 for e in errors),stationarity=float(abs(gradient).max())<=1e-5,
            proper=bool(proper),finite_cost=bool(np.isfinite(ref.direct_cost(z,a['final_physical']))))
        assert tests==record['tests'] and all(tests.values())==record['passed'];all_gate.append((name,all(tests.values())))
        replay,state=m.solve(z,name,r.cap)
        assert set(replay)==set(a)
        for key in a:
            assert np.array_equal(a[key],replay[key]),(name,key)
            replay_delta=max(replay_delta,float(abs(a[key]-replay[key]).max()))
        assert state==c.read(r.BASE/'bank'/name/'optimizer_state.json')
        replayed+=1;replay_iterations+=state['n_iter'];replay_closures+=state['func_evals']
    primary=all(passed for name,passed in all_gate if name.startswith('SCALED'))
    assert primary==result['primary_conjunction']
    r.check();r.old_deliveries()
    validation=dict(passed=True,primary_conjunction=primary,decision=result['decision'],independent_trial_records=trial_count,
        all12_trial_gradients_FD_checked=True,independent_hessian_zero_checked=True,full_optimizer_replays=replayed,
        replay_iterations=replay_iterations,replay_closure_evaluations=replay_closures,
        optimizer_replay_uses_same_source_and_library=True,not_independently_implemented_LBFGS=True,
        max_cost_delta=cost_delta,max_gradient_FD_delta=grad_delta,max_pose_delta=pose_delta,max_output_delta=output_delta,
        max_hessian_FD_delta=hessian_delta,replay_max_delta=replay_delta,all_final_gates_duplicated=True,**r.usage())
    c.save(r.BASE/'validation.json',validation)
    c.save(r.BASE/'validation_seal.json',dict(validation_sha256=c.sha(r.BASE/'validation.json'),results_seal_sha256=c.sha(r.BASE/'results_seal.json'),freeze_sha256=c.sha(r.BASE/'freeze.json')))
    r.finish('independent_validation_and_full_replay');print('NOC3 VALIDATED',validation,flush=True)


if __name__=='__main__':
    r.START=time.monotonic()
    def alarm(signum,frame): raise TimeoutError('NOC3 validation remaining wall exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(600-sum(x['wall_seconds'] for x in r.ledger()))))
    try: run()
    except Exception as ex:
        r.finish('validation',False,error=repr(ex));c.save(r.BASE/'FAILURE_validation.json',dict(error=repr(ex),**r.usage()))
        c.status(r.BASE,'failure',status='INCOMPLETE',error=repr(ex));raise
    finally: signal.alarm(0)
