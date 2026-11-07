"""SFC0 independent CPU parameter-step and metric cost reconstruction."""
import math
import numpy as np
import native_shadow_step as r
import validate_native_backward as e
def validate():
    r.r.verify();r.r.check_seal(r.BASE/'bank','bank_seal.json');ex=r.read(r.BASE/'bank/execution.json')
    assert ex['shadow_tail_forwards']==16 and ex['backwards']==4 and ex['actual_transient_signed_parameter_steps']==8 and ex['whole_native_forwards']==ex['optimizer_API_calls']==ex['retained_updates']==ex['fit_iterations']==0 and ex['parameters_dtype_flags_hooks_restored']
    z=e.load(r.r.r.OLD/'bank/synthetic_fixture.npz');noise=e.load(r.r.r.OLD/'bank/noise/fit_00.npz')['noise'].astype(float);initial={k:v.astype(float) for k,v in e.load(r.r.r.OLD/'preflight/P/initial.npz').items()};rows=[];costmax=0.
    for row in ex['records']:
        folder=r.BASE/'bank'/row['name'];grad=e.load(folder/'gradients.npz');old=e.load(r.PRIOR/f"traces/{row['arm']}1/gradients.npz");assert all(np.array_equal(grad[k],v) for k,v in old.items())
        norm=math.sqrt(sum(float(np.sum(g*g)) for g in grad.values()));assert norm==row['gradient_L2_norm'];radius=min(.001,.001*row['loss_before']/norm);assert radius==row['predetermined_radius']
        restored=e.load(folder/'restored_parameters.npz');assert all(np.array_equal(restored[k],v) for k,v in initial.items()) and row['restored_output_byteexact']
        def cost(out):
            assert np.array_equal(noise-out['velocity'],out['output'])
            return e.objective(z,out['output']) if row['arm']=='P' else float(np.mean((out['velocity']-(noise-z['target'].astype(float)))**2))
        before=cost(e.load(folder/'initial_output.npz'));delta=abs(before-row['loss_before']);assert delta<=1e-7;costmax=max(costmax,delta);checks=[]
        for s in row['steps']:
            sign=s['sign'];params=e.load(folder/f'parameters_{sign:+d}.npz');out=e.load(folder/f'output_{sign:+d}.npz');assert all(np.array_equal(params[k],v+sign*radius*grad[k]/norm) for k,v in initial.items())
            actual={k:params[k]-v for k,v in initial.items()};dot=sum(float(np.sum(grad[k]*d)) for k,d in actual.items());length=math.sqrt(sum(float(np.sum(d*d)) for d in actual.values()));assert dot==s['actual_gradient_dot'] and length==s['actual_parameter_L2_norm'] and length<=radius*(1+1e-10)
            after=cost(out);delta=abs(after-s['loss']);assert delta<=1e-7;costmax=max(costmax,delta)
            passing=dot<0 and after<=before+.5*dot if sign==-1 else dot>0 and after>=before+.5*dot
            checks.append(dict(sign=sign,loss_before=before,loss_after=after,actual_dot=dot,parameter_L2_norm=length,Armijo_pass=passing));r.cap()
        rows.append(dict(name=row['name'],arm=row['arm'],radius=radius,checks=checks,all_pass=all(x['Armijo_pass'] for x in checks)))
    repeat=True
    for arm in ('V','P'):
        for file in ('gradients.npz','initial_output.npz','parameters_-1.npz','parameters_+1.npz','output_-1.npz','output_+1.npz','restored_parameters.npz'):
            a=e.load(r.BASE/f'bank/{arm}1'/file);b=e.load(r.BASE/f'bank/{arm}2'/file);repeat=repeat and all(np.array_equal(a[k],b[k]) for k in a)
    passed=repeat and all(x['all_pass'] for x in rows);r.r.verify();r.save(r.BASE/'validation.json',dict(passed=True,functional_conjunction=passed,repeat_byteexact=repeat,rows=rows,independent_loss_max_delta=costmax,actual_signed_steps=8,optimizer_API_calls=0,retained_updates=0,fit_admitted=False,decision='SHADOW_FIXED_FIRST_ORDER_DESCENT_ASCENT_WITNESS' if passed else 'SHADOW_FUNCTIONAL_STEP_PREREQUISITE_FAIL'))
    print('SFC0 independent functional conjunction',passed,flush=True)
