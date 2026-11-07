"""Independent CPU artifact equations/census for NMR0; no torch import."""
import math
import numpy as np
import native_backward_reproducibility as r
import validate_native_backward as legacy

def validate():
    legacy.validate()
    result=r.read(r.BASE/'results.json'); core=r.read(r.BASE/'validation.json'); execution=r.read(r.BASE/'traces/execution.json')
    assert execution['backend_flags_restored'] and execution['backend_flags_before']==execution['backend_flags_after']
    for trace in execution['traces']:
        if trace['path']=='full' and trace['rep']==1:
            assert 'aten::_scaled_dot_product_attention_math' in trace['dispatched_ATen_names']
            assert not any('_scaled_dot_product_flash_attention' in x for x in trace['dispatched_ATen_names'])
    for row in result['default_control_comparisons']:
        for filename,values in row['details'].items():
            left=legacy.load(r.BASE/'traces'/row['name']/filename);right=legacy.load(r.PRIOR/'traces'/row['name']/filename)
            for key,stored in values.items():
                rebuilt=legacy.stats(left[key],right[key])
                for field,value in rebuilt.items():
                    assert abs(value-stored[field])<=1e-12*max(1.,abs(value)) if field=='relative_L2' else value==stored[field]
    directions=[]; loss_delta=0.; restored=True
    if result['all_instrumented_pairs_byte_equal']:
        r.check_seal(r.BASE/'directions','direction_seal.json'); data=r.read(r.BASE/'directions/execution.json')
        assert data['native_forwards']==24 and data['backwards']==data['optimizer_calls']==data['retained_updates']==0
        assert data['initial_parameters_restored_byteexact'] and data['backend_flags_restored']
        initial=legacy.load(r.OLD/'preflight/P/initial.npz');z=legacy.load(r.OLD/'bank/synthetic_fixture.npz');noise=legacy.load(r.OLD/'bank/noise/fit_00.npz')['noise']
        rng=np.random.default_rng(9417); vectors={}; lookup={}
        for group in ('final_mlp','LoRA_B'):
            vector={k:np.zeros_like(v) for k,v in initial.items()}
            for key,value in vector.items():
                if (group=='final_mlp' and key.startswith('final_mlp.')) or (group=='LoRA_B' and key.endswith('.B')):value[:]=rng.choice([-1.,1.],size=value.shape)
            norm=math.sqrt(sum(float(np.sum(v.astype(float)**2)) for v in vector.values()));assert norm>0
            vector={k:(v/norm).astype(v.dtype) for k,v in vector.items()};saved=legacy.load(r.BASE/f'directions/{group}.npz');assert all(np.array_equal(saved[k],v) for k,v in vector.items());vectors[group]=vector
        for row in data['records']:
            out=legacy.load(r.BASE/f"directions/{row['name']}.npz"); params=legacy.load(r.BASE/f"directions/{row['name']}_parameters.npz");vector=vectors[row['group']]
            assert all(np.array_equal(params[k],(v+row['sign']*row['step']*vector[k]).astype(v.dtype)) for k,v in initial.items())
            assert np.array_equal((noise-out['velocity']).astype(np.float32),out['output'])
            cost=legacy.objective(z,out['output'].astype(float)) if row['arm']=='P' else float(np.mean((out['velocity']-(noise-z['target']))**2))
            delta=abs(cost-row['loss']);assert delta<=1e-7;loss_delta=max(loss_delta,delta)
            grad=legacy.load(r.BASE/f"traces/{row['arm']}_full1/gradients.npz"); dot=sum(float(np.sum(grad[k].astype(float)*v.astype(float))) for k,v in vector.items());assert dot==row['analytic']
            key=(row['arm'],row['group'],row['step']); lookup.setdefault(key,{})[row['sign']]=cost
            r.cap()
        assert len(lookup)==12
        for (arm,group,step),costs in lookup.items():
            grad=legacy.load(r.BASE/f'traces/{arm}_full1/gradients.npz');dot=sum(float(np.sum(grad[k].astype(float)*v.astype(float))) for k,v in vectors[group].items())
            fd=(costs[1]-costs[-1])/(2*step);error=abs(fd-dot);bound=max(1e-3,.05*abs(dot))
            directions.append(dict(arm=arm,group=group,step=step,central_difference=fd,gradient_dot=dot,error=error,bound=bound,corroborated=error<=bound))
    all_directions=bool(directions) and all(x['corroborated'] for x in directions)
    decision='MATH_REPEAT_EXACT_DIRECTION_CORROBORATION_PASS' if all_directions else ('MATH_REPEAT_EXACT_DIRECTION_CORROBORATION_FAIL' if directions else 'MATH_NATIVE_REPEAT_PREREQUISITE_FAIL')
    r.verify();r.save(r.BASE/'math_validation.json',dict(utc=r.now(),passed=True,core_validation=core,default_backend_full_census_independent=True,actual_math_dispatch=True,backend_flags_restored=True,
        all_instrumented_pairs_byte_equal=result['all_instrumented_pairs_byte_equal'],directional_checks=directions,independent_direction_loss_max_delta=loss_delta,
        whole_direction_corroboration=all_directions,decision=decision,optimizer_calls=0,retained_updates=0,native_fit_admitted=False,independent_whole_transformer_backward=False))
    print('NMR0 independent CPU audit',decision,flush=True)
