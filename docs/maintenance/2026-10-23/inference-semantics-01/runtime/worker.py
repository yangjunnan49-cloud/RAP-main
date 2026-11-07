"""Actual source inference semantics with deterministic synthetic velocity fields."""
import ast,hashlib,json,math,os,resource,sys,time
from functools import partial
from pathlib import Path
from types import MethodType,SimpleNamespace
from typing import Callable
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent;OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
SELECT={'point_clouds.py':['split_parts'],'procrustes.py':['solve_procrustes','fit_transformations','rigidify_prediction_with_procrustes'],'sampler.py':['flow_sampler','euler_step','get_sampler'],'modeling.py':['_sample_timesteps','_prepare_data','sample_rectified_flow']}
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(raw):return hashlib.sha256(raw).hexdigest().upper()
def win(p):return Path('/mnt/'+p[0].lower()+'/'+p[3:].replace('\\','/'))
def audit(event,args):
    if event=='socket.connect':raise PermissionError('IS1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if p.endswith(('.ckpt','.pth')) or 'regx-interface-contract-01' in p or 'regx-reference-' in p:raise PermissionError('IS1 weights/points/reference forbidden')
sys.addaudithook(audit)
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text());assert sha((SCOPE/'SOURCE_POINTERS.json').read_bytes())==freeze['pointer_sha256']
    functions={};bindings=[]
    for row in json.loads((SCOPE/'SOURCE_POINTERS.json').read_text()):
        raw=win(row['snapshot']).read_bytes();assert sha(raw)==row['sha256'] and sha(win(row['source']).read_bytes())==row['sha256']
        name=win(row['snapshot']).name
        for fn in SELECT[name]:
            nodes=[n for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and n.name==fn];assert len(nodes)==1
            functions[fn]=nodes[0];compile(ast.Module(body=nodes,type_ignores=[]),fn,'exec')
            bindings.append(dict(function=fn,source_sha256=row['sha256'],line=nodes[0].lineno,AST_sha256=sha(ast.dump(nodes[0],include_attributes=False).encode())))
    assert len(functions)==10
    if CASE=='preflight':
        assert 'torch' not in sys.modules
        write('RESULTS.json',dict(passed=True,stdlib_only=True,bindings=bindings))
    else:
        import torch
        assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
        ns=dict(torch=torch,nn=torch.nn,math=math,Callable=Callable,partial=partial)
        for names in SELECT.values():
            for fn in names:exec(compile(ast.Module(body=[functions[fn]],type_ignores=[]),fn,'exec'),ns)
        source_sample=ns['sample_rectified_flow'];controls=[]
        def setup(B,mode,rigid,mask_variant=0):
            P=3;N=6;total=B*P*N
            cond=torch.tensor([[((i%7)-3)/4.,((i*i%11)-5)/8.,((i*3%13)-6)/16.] for i in range(total)],dtype=torch.float32)
            velocity=torch.tensor([[((i%5)-2)/8.,((i*2%7)-3)/16.,((i*i%9)-4)/32.] for i in range(total)],dtype=torch.float32)
            noise=torch.arange(total*3,dtype=torch.float32).reshape(total,3)/16.
            mask=torch.zeros(total,dtype=torch.bool)
            if mask_variant<3:
                for b in range(B):mask[b*P*N+mask_variant*N:b*P*N+(mask_variant+1)*N]=True
            counts=torch.full((B,P),N,dtype=torch.int64);cu=torch.arange(B+1,dtype=torch.int64)*(P*N)
            batch=dict(pointclouds=cond,pointclouds_gt=cond.clone(),features=torch.ones(total,32),scales=torch.ones(B),anchor_indices=mask,points_per_part=counts,cu_seqlens=cu)
            obj=SimpleNamespace(device=torch.device('cpu'),timestep_sampling=mode,inference_sampling_steps=4,inference_sampler='euler',rigidity_forcing=rigid,return_end_point_trajectory=True)
            obj._sample_timesteps=MethodType(ns['_sample_timesteps'],obj);obj._prepare_data=MethodType(ns['_prepare_data'],obj)
            records=[]
            def flow(**kw):
                assert kw['cond_coord'] is cond and kw['anchor_indices'] is mask and torch.equal(kw['local_features'],batch['features'])
                records.append(dict(x=kw['x'].clone(),t=kw['timesteps'].clone()))
                return velocity.clone()
            obj.flow_model=flow
            return obj,batch,velocity,noise,records
        for B in (1,2):
            for mode in ('u_shaped','uniform','mode','logit_normal'):
                for explicit in (False,True):
                    for rigid in (False,True):
                        obj,batch,v,noise,records=setup(B,mode,rigid)
                        seed=82010+B;torch.manual_seed(seed);g=torch.Generator().manual_seed(seed)
                        before=sha(torch.get_rng_state().numpy().tobytes())
                        if mode=='logit_normal':torch.normal(mean=0.,std=1.,size=(B,),generator=g)
                        else:torch.rand(B,generator=g)
                        expected_initial=noise if explicit else torch.randn(batch['pointclouds'].shape,generator=g)
                        expected_state=g.get_state().clone()
                        out=source_sample(obj,batch,None,x_1=noise if explicit else None,return_tarjectory=True)
                        assert len(records)==4 and torch.equal(records[0]['x'],expected_initial)
                        assert torch.equal(torch.get_rng_state(),expected_state),'RNG consumption differs from independent generator'
                        assert [float(r['t'][0]) for r in records]==[1.,.75,.5,.25]
                        if not rigid:
                            expected=expected_initial-v
                            budget=128*torch.finfo(torch.float32).eps*max(1.,float(expected_initial.abs().max()),float(v.abs().max()))
                            error=float((out['end_point_trajectory']-expected).abs().max());assert error<=budget
                        else:error=None;budget=None
                        controls.append(dict(case='RNG_and_initial_input',B=B,mode=mode,explicit_noise=explicit,rigidity=rigid,passed=True,RNG_before=before,RNG_after=sha(torch.get_rng_state().numpy().tobytes()),independent_final_RNG_match=True,velocity_calls=4,endpoint_error=error,budget=budget))
        for rigid in (False,True):
            baseline=None
            for variant in range(4):
                obj,batch,v,noise,records=setup(1,'u_shaped',rigid,variant)
                out=source_sample(obj,batch,None,x_1=noise,return_tarjectory=True)
                if baseline is None:baseline=out
                else:
                    assert torch.equal(out['end_point_trajectory'],baseline['end_point_trajectory']) and torch.equal(out['trajectory'],baseline['trajectory'])
                controls.append(dict(case='mask_reaches_stub_integrator_not_clamped',rigidity=rigid,mask_variant=variant,passed=True,learned_flow_mask_independence_claim=False))
        obj,batch,v,noise,records=setup(1,'u_shaped',True)
        out=source_sample(obj,batch,None,x_1=noise,return_tarjectory=False)
        assert isinstance(out,dict) and set(out)=={'trajectory','end_point_trajectory'}
        delta=float((out['trajectory'][-1]-out['end_point_trajectory'][-1]).abs().max());assert delta>.001
        r0,t0=ns['fit_transformations'](batch['pointclouds'],out['end_point_trajectory'][-1],batch['points_per_part'],batch['cu_seqlens'].to(torch.int32))
        r1,t1=ns['fit_transformations'](batch['pointclouds'],out['trajectory'][-1],batch['points_per_part'],batch['cu_seqlens'].to(torch.int32))
        matrix_delta=max(float((r0-r1).abs().max()),float((t0-t1).abs().max()));assert matrix_delta<=2e-5
        controls.append(dict(case='full_method_returns_dict_despite_false_flag',passed=True,raw_vs_projected_coordinate_difference=delta,refit_transform_difference=matrix_delta,refit_budget=2e-5))
        for flag in (False,True):
            direct=ns['get_sampler']('euler')(flow_model_fn=lambda x,t:v.clone(),x_1=noise,x_0=batch['pointclouds'],condition=batch['pointclouds'],points_per_part=batch['points_per_part'],cu_seqlens_batch=batch['cu_seqlens'].to(torch.int32),anchor_indices=batch['anchor_indices'],num_steps=4,return_trajectory=flag,rigidity_forcing=True,return_end_point_trajectory=False)
            if flag:
                assert isinstance(direct,dict) and set(direct)=={'trajectory','end_point_trajectory'}
                assert torch.equal(direct['trajectory'][-1],last)
            else:last=direct;assert torch.equal(last,out['trajectory'][-1])
            controls.append(dict(case='sampler_flags_actual_semantics',return_trajectory=flag,passed=True))
        assert not torch.cuda.is_initialized()
        write('RESULTS.json',dict(passed=True,count=len(controls),controls=controls,bindings=bindings,torch_version=torch.__version__,CUDA_initialized=False,actual_neural_model_calls=0,actual_weight_reads=0,point_or_reference_reads=0,claim='Source integration semantics with fixed synthetic fields only; no actual RAP efficacy or old native-cause attribution'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='IS1_source_synthetic_RNG_sampler_semantics'))
