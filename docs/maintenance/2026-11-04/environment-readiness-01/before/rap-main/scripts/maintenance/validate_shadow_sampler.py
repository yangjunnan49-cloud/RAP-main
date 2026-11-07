"""SAR0 independent CPU cast/Euler/rigidification/census, no torch or reference."""
import ast
import numpy as np
import shadow_sampler_extraction as r
import validate_native_backward as e
def validate():
    r.r.verify();r.r.check_seal(r.BASE/'bank','bank_seal.json');ex=r.read(r.BASE/'bank/execution.json')
    assert ex['no_truth_target_arrays_loaded'] and ex['no_losses_or_metrics'] and ex['backwards']==ex['optimizer_calls']==ex['retained_updates']==0 and ex['source_sampler_and_flags_and_values_restored']
    assert ex['counts']==dict(helper_prefix_calls=20,full_FP32_forward_calls=20,double_tail_calls=40,time_constant_promotions=160) and ex['nominal_trainables']==443904
    assert ex['checkpoint_source_model']==dict(steps=5,sampler='euler',rigidity_forcing=True) and ex['strict_checkpoint']['strict'] and ex['strict_checkpoint']['weights_only']
    observations=e.load(r.BASE/'bank/observations.npz');assert set(observations)=={'points','features','cond','scale','centers','counts'}
    with np.load(r.r.r.OLD/'bank/synthetic_fixture.npz',allow_pickle=False) as z:assert all(np.array_equal(z[k],v) for k,v in observations.items())
    condition=observations['cond'].astype(float);maxrig=0.;maxstate=0.;fits=0;casts=[]
    tree=ast.parse((r.MAIN/'rectified_point_flow/sampler.py').read_text());euler=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='euler_step')
    expected=ast.parse('v=flow_model_fn(x_t,t)\nx_0_hat=x_t-v*t\nx_t=x_t-dt*v\nreturn x_t,x_0_hat').body
    assert [ast.dump(x,include_attributes=False) for x in euler.body[1:]]==[ast.dump(x,include_attributes=False) for x in expected]
    for row in ex['records']:
        folder=r.BASE/'bank'/row['name'];meta=r.read(folder/'trace.json');source=e.load(folder/'source_trajectory.npz');noise=e.load(r.r.r.OLD/f"bank/noise/{row['noise']}.npz")['noise'].astype(float)
        assert meta['taus']==[1-i*.2 for i in range(5)] and meta['dt']==.2 and source['trajectory'].dtype==source['end_point_trajectory'].dtype==np.float32
        previous=None
        for i,tau in enumerate(meta['taus']):
            z=e.load(folder/f'step_{i}.npz');state=z['state'];vel=z['velocity'];assert state.dtype==vel.dtype==z['rigid'].dtype==np.float64 and z['prefix'].dtype==z['prefix_input'].dtype==z['timestep'].dtype==np.float32
            assert all(np.isfinite(v).all() for v in z.values()) and np.array_equal(z['prefix_input'],state.astype(np.float32)) and np.array_equal(z['timestep'],np.array([tau],np.float32))
            if i==0:assert np.array_equal(state,noise)
            else:
                delta=float(np.max(abs(state-previous)));assert delta<=1e-10;maxstate=max(maxstate,delta)
            endpoint=state-tau*vel;rigid=[]
            for k in range(3):
                x=condition[k*1000:(k+1)*1000];target=endpoint[k*1000:(k+1)*1000];rot,shift=e.horn(x,target);assert abs(np.linalg.det(rot)-1)<=1e-10 and np.max(abs(rot.T@rot-np.eye(3)))<=1e-10
                rigid.append(x@rot.T+shift);fits+=1
            rigid=np.concatenate(rigid);delta=float(np.max(abs(rigid-z['rigid'])));assert delta<=1e-10;maxrig=max(maxrig,delta)
            previous=rigid*(1-tau+.2)+noise*(tau-.2)
            for name,expected_array in [('end_point_trajectory',endpoint),('trajectory',previous)]:
                rounded=expected_array.astype(np.float32);actual=source[name][i];diff=abs(rounded.astype(float)-actual.astype(float));ulp=abs(np.spacing(actual).astype(float));outside=int(np.sum(diff>ulp));assert outside==0,(row['name'],i,name,outside)
                casts.append(dict(name=row['name'],step=i,buffer=name,byteequal=bool(np.array_equal(rounded,actual)),max_delta=float(np.max(diff)),outside_one_float32_ULP=outside))
            r.cap()
    pairs=[]
    for noise in ('fit_00','eval_00'):
        for left,right in (('helper1','helper2'),('hook1','hook2'),('helper1','hook1'),('helper2','hook2')):
            a=r.BASE/f'bank/{noise}_{left}';b=r.BASE/f'bank/{noise}_{right}';same=True;maxdelta=0.
            for file in ['source_trajectory.npz']+[f'step_{i}.npz' for i in range(5)]:
                x=e.load(a/file);y=e.load(b/file);assert set(x)==set(y)
                for k in x:
                    same=same and bool(x[k].dtype==y[k].dtype and np.array_equal(x[k],y[k]));maxdelta=max(maxdelta,float(np.max(abs(x[k].astype(float)-y[k].astype(float)))))
            pairs.append(dict(noise=noise,left=left,right=right,byteexact=same,max_delta=maxdelta))
    assert fits==120;passed=all(x['byteexact'] for x in pairs)
    r.r.verify();r.save(r.BASE/'validation.json',dict(passed=True,extraction_and_sampler_conjunction=passed,source_Euler_AST_exact=True,independent_Horn_part_fits=120,independent_rigid_max_delta=maxrig,independent_state_max_delta=maxstate,buffer_cast_checks=casts,pairs=pairs,
        decision='SHADOW_SOURCE_SAMPLER_EXTRACTION_AND_PRECISION_BINDINGS_VALID' if passed else 'SHADOW_SAMPLER_EXTRACTION_BINDING_FAIL',no_truth_target_metrics=True,backwards=0,optimizer_calls=0,retained_updates=0,fit_admitted=False,original_native_equivalence=False,independent_complete_model=False))
    print('SAR0 independent source extraction/sampler conjunction',passed,flush=True)
