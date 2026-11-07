"""FPC0 independent CPU equations/perturbations/census; no torch import."""
import math
import numpy as np
import native_precision_control as r
import validate_native_backward as e

def stats(a,b):
    assert a.shape==b.shape;d=a.astype(float)-b.astype(float)
    return dict(byte_equal=bool(a.dtype==b.dtype and np.array_equal(a,b)),different=int(np.sum(a!=b)),max_abs=float(np.max(abs(d))),left_dtype=str(a.dtype),right_dtype=str(b.dtype))

def validate(stage):
    r.verify();r.check_seal(r.BASE/'traces','trace_seal.json');ex=r.read(r.BASE/'traces/execution.json')
    assert ex['native_forwards']==ex['backwards']==16 and ex['prefix_forwards']==4 and ex['optimizer_calls']==ex['retained_updates']==0 and ex['initialized_trainables']==443904
    assert ex['strict_checkpoint']['strict'] and ex['strict_checkpoint']['weights_only'] and ex['backend_and_attention_dtype_restored'] and ex['frozen_parameters_and_modes_preserved']
    z=e.load(r.r.OLD/'bank/synthetic_fixture.npz');noise=e.load(r.r.OLD/'bank/noise/fit_00.npz')['noise'];initial=e.load(r.r.OLD/'preflight/P/initial.npz');costmax=0.;vmax=0.;output_fd=[]
    directions=[]
    for k,column in ((1,0),(2,1),(0,2)):
        d=np.zeros((3000,3));d[k*1000:(k+1)*1000,column]=1.;directions.append(d)
    rng=np.random.default_rng(417)
    for _ in range(9):
        d=rng.normal(size=(3000,3));d/=np.linalg.norm(d);directions.append(d)
    for row in ex['records']:
        folder=r.BASE/'traces'/row['name'];out=e.load(folder/'output.npz');grads=e.load(folder/'gradients.npz');after=e.load(folder/'parameters_after.npz')
        assert set(initial)==set(grads)==set(after) and all(np.array_equal(after[k],v) for k,v in initial.items())
        assert all(np.isfinite(a).all() for a in list(out.values())+list(grads.values()))
        expected=(noise-out['velocity']).astype(float) if row['condition']=='S' else noise.astype(float)-out['velocity'].astype(float);assert np.array_equal(out['output'],expected)
        if row['arm']=='V':
            residual=out['velocity']-(noise-z['target']) if row['condition']=='S' else out['velocity'].astype(float)-(noise.astype(float)-z['target'].astype(float))
            cost=float(np.mean(residual**2));grad=(-2*residual/9000).astype(np.float32);delta=float(np.max(abs(grad-out['upstream'])));assert delta<=1e-10;vmax=max(vmax,delta)
        else:
            cost=e.objective(z,out['output'])
            for j,d in enumerate(directions):
                fd=(e.objective(z,out['output']+1e-6*d)-e.objective(z,out['output']-1e-6*d))/2e-6;dot=float(np.sum(out['upstream'].astype(float)*d));error=abs(fd-dot);bound=max(1e-4,1e-5*abs(fd));assert error<=bound,(row['name'],j,error,bound)
                output_fd.append(dict(name=row['name'],direction=j,error=error,bound=bound))
        delta=abs(cost-row['loss']);assert delta<=1e-7;costmax=max(costmax,delta)
        assert all(v==dict(input='torch.float32',output='torch.float32') for v in row['linear_dtypes'].values()) and len(row['linear_dtypes'])==4
        if row['path']=='full' and row['rep']==1:
            assert 'aten::_scaled_dot_product_attention_math' in row['dispatched_ATen_names'] and not any('_scaled_dot_product_flash_attention' in x for x in row['dispatched_ATen_names'])
        r.cap()
    pairs=[];controls=[];seq=r.read(r.BASE/'freeze.json')['sequence']
    for condition in ('S','D'):
        for i,j in ((0,2),(1,3),(4,6),(5,7),(0,1),(2,3),(4,5),(6,7)):
            left=f'{condition}_{seq[i]}';right=f'{condition}_{seq[j]}';detail={}
            for file in ('output.npz','gradients.npz','parameters_after.npz'):
                a=e.load(r.BASE/'traces'/left/file);b=e.load(r.BASE/'traces'/right/file);detail[file]={k:stats(a[k],b[k]) for k in a}
            pairs.append(dict(left=left,right=right,details=detail,all_byteexact=all(x['byte_equal'] for values in detail.values() for x in values.values())))
        for name in seq:
            detail={}
            for file in ('output.npz','gradients.npz'):
                a=e.load(r.BASE/f'traces/{condition}_{name}'/file);b=e.load(r.PRIOR/'traces'/name/file);detail[file]={k:stats(a[k],b[k]) for k in b}
            controls.append(dict(condition=condition,name=name,details=detail))
    core=dict(passed=True,all_pairs_byteexact=all(x['all_byteexact'] for x in pairs),pairs=pairs,previous_NMR_controls=controls,independent_loss_max_delta=costmax,V_upstream_max_delta=vmax,P_output_FD=output_fd,independent_full_transformer_backward=False,optimizer_calls=0)
    if stage=='repeat':r.save(r.BASE/'repeat_validation.json',core);print('FPC0 independent repeat gate',core['all_pairs_byteexact'],flush=True);return
    previous=r.read(r.BASE/'repeat_validation.json');assert core==previous
    directional=[];direction_costmax=0.;nmrs=r.read(r.PRIOR/'math_validation.json')['directional_checks']
    if core['all_pairs_byteexact']:
        r.check_seal(r.BASE/'directions','direction_seal.json');dx=r.read(r.BASE/'directions/execution.json');assert dx['native_forwards']==24 and dx['backwards']==dx['optimizer_calls']==dx['retained_updates']==0 and dx['temporary_parameters_restored_byteexact'] and dx['backend_and_attention_dtype_restored']
        vectors={g:e.load(r.PRIOR/f'directions/{g}.npz') for g in ('final_mlp','LoRA_B')};lookup={}
        # Original NMR0 independent seed reconstruction is sealed; bind every unchanged vector/perturbation exactly.
        for row in dx['records']:
            out=e.load(r.BASE/f"directions/{row['name']}.npz");params=e.load(r.BASE/f"directions/{row['name']}_parameters.npz");vector=vectors[row['group']]
            assert all(np.array_equal(params[k],(v+row['sign']*row['step']*vector[k]).astype(v.dtype)) for k,v in initial.items())
            for condition in ('S','D'):
                q=(noise-out['velocity']).astype(float) if condition=='S' else noise.astype(float)-out['velocity'].astype(float);assert np.array_equal(q,out[condition+'_output'])
                if row['arm']=='P':cost=e.objective(z,q)
                else:
                    residual=out['velocity']-(noise-z['target']) if condition=='S' else out['velocity'].astype(float)-(noise.astype(float)-z['target'].astype(float));cost=float(np.mean(residual**2))
                delta=abs(cost-row['losses'][condition]);assert delta<=1e-7;direction_costmax=max(direction_costmax,delta)
                key=(condition,row['arm'],row['group'],row['step']);lookup.setdefault(key,{})[row['sign']]=cost
            r.cap()
        assert len(lookup)==24
        for (condition,arm,group,step),values in lookup.items():
            grad=e.load(r.BASE/f'traces/{condition}_{arm}_full1/gradients.npz');dot=sum(float(np.sum(grad[k].astype(float)*v.astype(float))) for k,v in vectors[group].items());fd=(values[1]-values[-1])/(2*step);error=abs(fd-dot);bound=max(1e-3,.05*abs(dot))
            reference=next(x for x in nmrs if (x['arm'],x['group'],x['step'])==(arm,group,step))
            directional.append(dict(condition=condition,arm=arm,group=group,step=step,central_difference=fd,gradient_dot=dot,error=error,bound=bound,corroborated=error<=bound,original_NMR=reference))
    conjunctions={c:bool(directional) and all(x['corroborated'] for x in directional if x['condition']==c) for c in ('S','D')}
    decision='PRECISION_CONTROLS_DIRECTION_CORROBORATION_PASS' if all(conjunctions.values()) else 'PRECISION_CONTROLS_RETAIN_DIRECTION_GAPS'
    if not core['all_pairs_byteexact']:decision='PRECISION_REPEAT_PREREQUISITE_FAIL'
    r.verify();r.save(r.BASE/'validation.json',dict(passed=True,core=core,directional_checks=directional,condition_conjunctions=conjunctions,independent_direction_loss_max_delta=direction_costmax,decision=decision,native_fit_admitted=False,optimizer_calls=0,retained_updates=0,unique_precision_cause_proved=False))
    print('FPC0 independent audit',decision,conjunctions,flush=True)
