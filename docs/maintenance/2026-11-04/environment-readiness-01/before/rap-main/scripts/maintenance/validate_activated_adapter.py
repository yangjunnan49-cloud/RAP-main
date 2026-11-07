"""ADR0 independent CPU fixed-function/direction/equation census, no torch."""
import ast,math
import numpy as np
import activated_adapter_derivatives as r
import validate_native_backward as e

def validate(stage):
    r.verify();r.check_seal(r.BASE/'traces','trace_seal.json');ex=r.read(r.BASE/'traces/execution.json')
    assert ex['shadow_tail_forwards']==ex['backwards']==4 and ex['whole_native_forwards']==ex['prefix_forwards']==ex['optimizer_calls']==ex['retained_updates']==0
    assert ex['initialized_trainables']==443904 and ex['parameter_values_unchanged_and_dtype_restored'] and ex['backend_and_attention_dtype_restored'] and ex['constant_float32_time_projection_promotions']==16
    assert ex['strict_checkpoint']['strict'] and ex['strict_checkpoint']['weights_only']
    original=ast.parse((r.r.SLAM/'scripts/native_output_capability.py').read_text());old=next(x for x in original.body if isinstance(x,ast.FunctionDef) and x.name=='tail')
    new=next(x for x in ast.parse(r.Path(r.__file__).read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='tail64')
    class Normalize(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id=='embedding':node.id='e'
            return node
        def visit_Attribute(self,node):
            self.generic_visit(node)
            if node.attr=='double':node.attr='float'
            return node
    normalized=Normalize().visit(new);assert [ast.dump(x,include_attributes=False) for x in old.body]==[ast.dump(x,include_attributes=False) for x in normalized.body]
    z=e.load(r.r.OLD/'bank/synthetic_fixture.npz');noise=e.load(r.r.OLD/'bank/noise/fit_00.npz')['noise'].astype(float);initial={k:v.astype(float) for k,v in e.load(r.r.OLD/'preflight/P/initial.npz').items()};costmax=0.;upmax=0.;fdoutput=[];linear=[];activated=[]
    original=dict(initial);rng=np.random.default_rng(2026101307);keys=[k for k in initial if k.endswith('.B')];assert sum(initial[k].size for k in keys)==32768
    for key in keys:initial[key]=rng.choice([-1.,1.],size=initial[key].shape)*(1e-3/np.sqrt(32768))
    saved=e.load(r.BASE/'activation_baseline.npz');assert all(np.array_equal(saved[k],v) for k,v in initial.items())
    for arm in ('V','P'):
        old=e.load(r.MAIN/f'docs/maintenance/2026-10-13/native-double-tail-control-01/traces/{arm}1/gradients.npz')
        assert all(not np.any(v) for k,v in old.items() if k.endswith('.A'))
    prefixes=[np.load(r.PRIOR/f'traces/D_{arm}_prefix.npy') for arm in ('V','P')];assert prefixes[0].dtype==np.float32 and np.array_equal(*prefixes)
    dirs=[]
    for k,column in ((1,0),(2,1),(0,2)):
        d=np.zeros((3000,3));d[k*1000:(k+1)*1000,column]=1.;dirs.append(d)
    rng=np.random.default_rng(417)
    for _ in range(9):
        d=rng.normal(size=(3000,3));d/=np.linalg.norm(d);dirs.append(d)
    for row in ex['records']:
        folder=r.BASE/'traces'/row['name'];out=e.load(folder/'output.npz');grad=e.load(folder/'gradients.npz');after=e.load(folder/'parameters_after.npz')
        assert set(initial)==set(after)==set(grad) and all(np.array_equal(after[k],v) for k,v in initial.items()) and all(a.dtype==np.float64 and np.isfinite(a).all() for a in list(out.values())+list(grad.values()))
        hooks=e.load(folder/'hooks.npz');assert len(hooks)==12 and all(v.dtype==np.float64 and np.isfinite(v).all() for v in hooks.values())
        for module in sorted({k.split('|')[0] for k in hooks}):
            x=hooks[module+'|input'];go=hooks[module+'|scaled_gradient'];rank=hooks[module+'|rank'];B=initial[module+'.B'];A=initial[module+'.A'];expected_rank=x@A.T
            rank_delta=float(np.max(abs(expected_rank-rank)));assert rank_delta<=max(1e-10,1e-10*float(np.max(abs(rank))))
            expected={'A':(go@B).T@x/row['factor'],'B':go.T@rank/row['factor']}
            nonzero=int(np.count_nonzero(grad[module+'.A']));activated.append(dict(trace=row['name'],module=module,A_nonzero=nonzero))
            for group,value in expected.items():
                actual=grad[module+'.'+group];delta=float(np.max(abs(value-actual)));bound=max(1e-10,1e-10*float(np.max(abs(actual))));linear.append(dict(trace=row['name'],module=module,group=group,delta=delta,bound=bound,pass_bound=delta<=bound,rank_delta=rank_delta))
        assert np.array_equal(noise-out['velocity'],out['output'])
        if row['arm']=='V':
            residual=out['velocity']-(noise-z['target'].astype(float));cost=float(np.mean(residual**2));delta=float(np.max(abs(-2*residual/9000-out['upstream'])));assert delta<=1e-14;upmax=max(upmax,delta)
        else:
            cost=e.objective(z,out['output'])
            for j,d in enumerate(dirs):
                fd=(e.objective(z,out['output']+1e-6*d)-e.objective(z,out['output']-1e-6*d))/2e-6;dot=float(np.sum(out['upstream']*d));error=abs(fd-dot);bound=max(1e-4,1e-5*abs(fd));assert error<=bound;fdoutput.append(dict(name=row['name'],direction=j,error=error,bound=bound))
        delta=abs(cost-row['loss']);assert delta<=1e-7;costmax=max(costmax,delta)
        assert 'aten::_scaled_dot_product_attention_math' in row['dispatched_ATen_names'] and not any('_scaled_dot_product_flash_attention' in x for x in row['dispatched_ATen_names']);r.cap()
    pairs=[]
    for arm in ('V','P'):
        detail={}
        for filename in ('output.npz','gradients.npz','parameters_after.npz','hooks.npz'):
            a=e.load(r.BASE/f'traces/{arm}1'/filename);b=e.load(r.BASE/f'traces/{arm}2'/filename);detail[filename]={k:e.stats(a[k],b[k]) for k in a}
        pairs.append(dict(arm=arm,details=detail,all_byteexact=all(x['byte_equal'] for values in detail.values() for x in values.values())))
    core=dict(passed=True,all_pairs_byteexact=all(p['all_byteexact'] for p in pairs),pairs=pairs,tail_AST_only_final_float_to_double=True,independent_loss_max_delta=costmax,V_upstream_max_delta=upmax,P_output_FD=fdoutput,original_prefix_byteexact=True,original_A_gradient_zero=True,local_A_B_checks=linear,activated_A=activated,prerequisite_conjunction=all(p['all_byteexact'] for p in pairs) and all(x['pass_bound'] for x in linear) and all(x['A_nonzero']>0 for x in activated))
    if stage=='repeat':r.save(r.BASE/'repeat_validation.json',core);print('ADR0 independent repeat gate',core['all_pairs_byteexact'],flush=True);return
    assert core==r.read(r.BASE/'repeat_validation.json');checks=[];costdir=0.
    if core['prerequisite_conjunction']:
        r.check_seal(r.BASE/'directions','direction_seal.json');dx=r.read(r.BASE/'directions/execution.json');assert dx['shadow_tail_forwards']==36 and dx['whole_native_forwards']==dx['backwards']==dx['optimizer_calls']==dx['retained_updates']==0 and dx['parameter_values_and_dtype_restored'] and dx['backend_and_attention_dtype_restored'] and dx['constant_float32_time_projection_promotions']==144
        vectors={g:e.load(r.NMR/f'directions/{g}.npz') for g in ('final_mlp','LoRA_B')};lookup={}
        rng=np.random.default_rng(2026101308);vector={k:np.zeros_like(v) for k,v in original.items()}
        for k,v in vector.items():
            if k.endswith('.A'):v[:]=rng.choice([-1.,1.],size=v.shape)
        assert sum(v.size for k,v in vector.items() if k.endswith('.A'))==16384
        norm=math.sqrt(sum(float(np.sum(v*v)) for v in vector.values()));vectors['LoRA_A']={k:v/norm for k,v in vector.items()};saved=e.load(r.BASE/'directions/LoRA_A.npz');assert all(np.array_equal(saved[k],v) for k,v in vectors['LoRA_A'].items())
        for row in dx['records']:
            out=e.load(r.BASE/f"directions/{row['name']}.npz");params=e.load(r.BASE/f"directions/{row['name']}_parameters.npz");vector=vectors[row['group']]
            assert all(np.array_equal(params[k],v+row['sign']*row['step']*vector[k].astype(float)) for k,v in initial.items()) and np.array_equal(noise-out['velocity'],out['output'])
            cost=e.objective(z,out['output']) if row['arm']=='P' else float(np.mean((out['velocity']-(noise-z['target'].astype(float)))**2));delta=abs(cost-row['loss']);assert delta<=1e-7;costdir=max(costdir,delta)
            lookup.setdefault((row['arm'],row['group'],row['step']),{})[row['sign']]=cost;r.cap()
        assert len(lookup)==18;prior=r.read(r.PRIOR/'validation.json')['directional_checks']
        for (arm,group,step),costs in lookup.items():
            grad=e.load(r.BASE/f'traces/{arm}1/gradients.npz');dot=sum(float(np.sum(grad[k]*v.astype(float))) for k,v in vectors[group].items());fd=(costs[1]-costs[-1])/(2*step);error=abs(fd-dot);bound=max(1e-12 if arm=='V' else 1e-6,.05*abs(dot));old=next((x for x in prior if (x['condition'],x['arm'],x['group'],x['step'])==('D',arm,group,step)),None)
            checks.append(dict(arm=arm,group=group,step=step,central_difference=fd,gradient_dot=dot,error=error,bound=bound,corroborated=error<=bound,original_FPC_D=old))
    allchecks=bool(checks) and all(x['corroborated'] for x in checks);decision='ACTIVATED_ADAPTER_ALL_GROUP_DERIVATIVE_CORROBORATION_PASS' if allchecks else 'ACTIVATED_ADAPTER_DERIVATIVE_GAPS_RETAINED'
    r.verify();r.save(r.BASE/'validation.json',dict(passed=True,core=core,directional_checks=checks,all_directions_corroborated=allchecks,independent_direction_loss_max_delta=costdir,decision=decision,optimizer_calls=0,retained_updates=0,native_fit_admitted=False,independent_complete_transformer_backward=False,whole_native_function_equivalence=False,unique_original_precision_cause=False))
    print('ADR0 independent audit',decision,flush=True)
