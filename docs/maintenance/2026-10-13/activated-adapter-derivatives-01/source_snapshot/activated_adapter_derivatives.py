"""ADR0 fixed-prefix FP64 trainable-tail derivative control; zero optimizer."""
import inspect,importlib.metadata,resource,signal,sys,time,traceback
from contextlib import contextmanager
from pathlib import Path
import native_math_reproducibility as r
MAIN=r.MAIN; PRIOR=MAIN/'docs/maintenance/2026-10-13/native-precision-control-01';NMR=r.BASE
PREDECESSOR=MAIN/'docs/maintenance/2026-10-13/native-shadow-step-control-01'
DESIGN=MAIN/'docs/maintenance/2026-10-13/conditioning-comparison-design-01'
BASE=MAIN/'docs/maintenance/2026-10-13/activated-adapter-derivatives-01';SUP=BASE/'supervision'
read,save,sha,now=r.read,r.save,r.sha,r.now
torch=None;START=None
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert r.repos()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')}
    assert (r.OLD/'INCOMPLETE').exists() and (r.OLD.parent/'INCOMPLETE').exists() and (r.PREVIOUS/'INCOMPLETE').exists()
def freeze():
    from diffusers.models.embeddings import Timesteps
    assert read(PREDECESSOR/'validation.json')['functional_conjunction']
    f=read(PREDECESSOR/'freeze.json');files=dict(f['files']);seal=read(PREDECESSOR/'DELIVERY_SEAL.json');assert len(seal['files'])==70
    for x in seal['files']:
        p=(PREDECESSOR/x['path'].replace(chr(92),'/')).resolve();assert PREDECESSOR.resolve() in p.parents and sha(p)==x['sha256'];files[str(p)]=x['sha256']
    design=read(DESIGN/'DELIVERY_SEAL.json');assert len(design['files'])==5
    for x in design['files']:
        p=(DESIGN/x['path']).resolve();assert DESIGN.resolve() in p.parents and sha(p)==x['sha256'];files[str(p)]=x['sha256']
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'SOURCE_DIFF.json',Path(__file__),Path(__file__).with_name('validate_activated_adapter.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PREDECESSOR/'DELIVERY_SEAL.json',DESIGN/'DELIVERY_SEAL.json',Path(inspect.getfile(Timesteps))]
    for p in paths:files[str(p)]=sha(p)
    for p,h in files.items():assert sha(p)==h,p
    assert r.repos()==f['repositories'];snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):(snap/p.name).write_bytes(p.read_bytes())
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=f['repositories'],packages=f['packages'],cap_seconds=900,cap_RSS_bytes=6*2**30,cap_GPU_bytes=8*2**30,cap_artifact_bytes=1024*2**20,optimizer_calls=0))
    (BASE/'INCOMPLETE').write_text('ADR0 fixed-prefix derivative control and independent audit pending.\n');print('ADR0 frozen',len(files),'identities',flush=True)

def flags():return [torch.backends.cuda.flash_sdp_enabled(),torch.backends.cuda.mem_efficient_sdp_enabled(),torch.backends.cuda.math_sdp_enabled(),torch.backends.cuda.cudnn_sdp_enabled()]

@contextmanager
def double_tail(flow,params,n):
    from rap_slam.rap_precision import ieee_matmul
    from torch.nn.attention import sdpa_kernel,SDPBackend
    from diffusers.models.embeddings import Timesteps
    layers=list(flow.transformer_layers[10:]);modules=layers+[flow.final_mlp];original_dtypes=[x.attn_dtype for x in layers];incoming=flags();handles=[];calls=[]
    assert len(layers)==2 and all(x==torch.float16 for x in original_dtypes) and all(p.dtype==torch.float32 for p in flow.parameters())
    frozen=n.frozen_digest(flow);modes={k:v.training for k,v in flow.named_modules()}
    def cast(key):
        def hook(mod,args,out):
            assert type(mod) is Timesteps and out.dtype==torch.float32
            calls.append(key);return out.double()
        return hook
    try:
        for module in modules:module.double()
        for i,layer in enumerate(layers,10):
            layer.attn_dtype=torch.float64
            for name in ('self_prenorm','global_prenorm'):
                module=getattr(layer,name).timestep_proj;assert type(module) is Timesteps and not list(module.parameters())
                handles.append(module.register_forward_hook(cast(f'{i}.{name}.timestep_proj')))
        assert all(p.dtype==torch.float64 and dict(flow.named_parameters())[k] is p for k,p in params.items())
        with ieee_matmul(),sdpa_kernel(SDPBackend.MATH),torch.autocast('cuda',enabled=False):yield calls
    finally:
        for h in handles:h.remove()
        for module in modules:module.float()
        for layer,dtype in zip(layers,original_dtypes):layer.attn_dtype=dtype
        assert flags()==incoming and all(p.dtype==torch.float32 for p in flow.parameters())
        assert n.frozen_digest(flow)==frozen and modes=={k:v.training for k,v in flow.named_modules()}

def tail64(flow,embedding,kw):
    # Exact original tail layer loop; final input remains double instead of e.float().
    for layer in flow.transformer_layers[10:]:
        embedding=layer(embedding,kw['timesteps'],kw['cu_seqlens_batch'],kw['cu_seqlens_part'])
    with torch.autocast('cuda',enabled=False):return flow.final_mlp(embedding.double())

def loss_value(z,noise,velocity,arm,n):
    assert noise.dtype==velocity.dtype==torch.float64
    q=noise-velocity
    if arm=='V':value=(velocity-(noise-torch.tensor(z['target'],device='cuda').double())).square().mean()
    else:value,_=n.old.obj(z,q)
    return value,q

def seal(folder,name):save(BASE/name,dict(freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def check_seal(folder,name):
    z=read(BASE/name);assert z['freeze_sha256']==sha(BASE/'freeze.json') and z['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}

def model_data():
    global torch,np
    import torch;import numpy as np;import native_conditioned_comparison as n
    r.torch=torch;r.BASE=BASE;model,params,initial,audit=n.model();assert r.mode_contract(model.flow_model)==read(r.PRIOR/'mode_inventory.json')['inventory']
    previous=n.load(r.OLD/'preflight/P/initial.npz');assert set(initial)==set(previous) and all(np.array_equal(v,previous[k]) for k,v in initial.items())
    z=n.load(r.OLD/'bank/synthetic_fixture.npz');noise=torch.tensor(n.load(r.OLD/'bank/noise/fit_00.npz')['noise'],device='cuda',dtype=torch.float64)
    kw=n.args(n.n.noc.batch({k:z[k] for k in n.n.OBS}),noise,1.)
    # Timesteps emits the same frozen float32 sine/cosine constants; promotion is explicit above.
    kw['timesteps']=kw['timesteps'].float();embedding=np.load(PRIOR/'traces/D_V_prefix.npy')
    assert embedding.dtype==np.float32 and np.array_equal(embedding,np.load(PRIOR/'traces/D_P_prefix.npy'))
    return n,model,params,initial,audit,z,noise,kw,torch.tensor(embedding,device='cuda',dtype=torch.float64)

def activation(initial):
    original={k:v.astype(float) for k,v in initial.items()};rng=np.random.default_rng(2026101307)
    keys=[k for k in original if k.endswith('.B')];assert len(keys)==4 and all(not np.any(original[k]) for k in keys)
    count=sum(original[k].size for k in keys);assert count==32768
    for key in keys:original[key]=rng.choice([-1.,1.],size=original[key].shape)*(1e-3/np.sqrt(count))
    assert abs(np.sqrt(sum(float(np.sum(original[k]**2)) for k in keys))-1e-3)<=1e-15
    return original

def probe():
    verify();n,model,params,initial,audit,z,noise,kw,embedding=model_data();folder=BASE/'traces';folder.mkdir();records=[];initial64=activation(initial);np.savez(BASE/'activation_baseline.npz',**initial64)
    with double_tail(model.flow_model,params,n) as timecalls:
        for arm in ('V','P'):
            for rep in (1,2):
                name=f'{arm}{rep}';dest=folder/name;dest.mkdir();n.assign(params,initial64)
                for p in params.values():p.grad=None
                captured={};handles=[]
                def hook(key):
                    def apply(mod,args,out):
                        captured[key+'|input']=args[0].detach().cpu().numpy().copy()
                        with torch.no_grad():captured[key+'|rank']=torch.nn.functional.linear(args[0],mod.A).cpu().numpy().copy()
                        out.register_hook(lambda g:captured.__setitem__(key+'|scaled_gradient',g.detach().cpu().numpy().copy()))
                    return apply
                modules={k:v for k,v in model.flow_model.named_modules() if k in {f'transformer_layers.{i}.{j}' for i in (10,11) for j in ('global_qkv_proj','global_out_proj')}};assert len(modules)==4
                for k,v in modules.items():handles.append(v.register_forward_hook(hook(k)))
                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as profile:
                    velocity=tail64(model.flow_model,embedding,kw);velocity.retain_grad();loss,q=loss_value(z,noise,velocity,arm,n);assert torch.isfinite(loss)
                    n.backward(params,loss,arm);torch.cuda.synchronize()
                for h in handles:h.remove()
                assert len(captured)==12
                np.savez_compressed(dest/'hooks.npz',**captured)
                grad={k:p.grad.detach().cpu().numpy().copy() for k,p in params.items()};assert all(v.dtype==np.float64 and np.isfinite(v).all() for v in grad.values())
                assert all(np.array_equal(p.detach().cpu().numpy(),initial64[k]) for k,p in params.items())
                np.savez(dest/'output.npz',velocity=velocity.detach().cpu().numpy(),output=q.detach().cpu().numpy(),upstream=-velocity.grad.detach().cpu().numpy()/n.SETTINGS['backward_multipliers'][arm]);np.savez(dest/'gradients.npz',**grad);np.savez(dest/'parameters_after.npz',**n.n.noc.numpy_state(params))
                row=dict(name=name,arm=arm,rep=rep,loss=float(loss),factor=n.SETTINGS['backward_multipliers'][arm],dispatched_ATen_names=sorted({x.name for x in profile.events() if 'scaled_dot_product' in x.name}));save(dest/'trace.json',row);records.append(row);del velocity,loss,q,grad,captured;cap();print('double tail backward',name,flush=True)
        assert len(timecalls)==16 and set(timecalls)=={f'{i}.{s}.timestep_proj' for i in (10,11) for s in ('self_prenorm','global_prenorm')}
        for p in params.values():p.grad=None
        n.assign(params,{k:v.astype(float) for k,v in initial.items()})
    assert all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items())
    save(folder/'execution.json',dict(records=records,strict_checkpoint=audit,shadow_tail_forwards=4,backwards=4,whole_native_forwards=0,prefix_forwards=0,optimizer_calls=0,retained_updates=0,initialized_trainables=443904,parameter_values_unchanged_and_dtype_restored=True,backend_and_attention_dtype_restored=True,constant_float32_time_projection_promotions=16))
    seal(folder,'trace_seal.json');verify()

def directions():
    verify();check_seal(BASE/'traces','trace_seal.json');assert read(BASE/'repeat_validation.json')['prerequisite_conjunction']
    n,model,params,initial,audit,z,noise,kw,embedding=model_data();folder=BASE/'directions';folder.mkdir();records=[];initial64=activation(initial);vectors={g:n.load(NMR/f'directions/{g}.npz') for g in ('final_mlp','LoRA_B')}
    rng=np.random.default_rng(2026101308);vector={k:np.zeros_like(v,dtype=float) for k,v in initial.items()}
    for k,v in vector.items():
        if k.endswith('.A'):v[:]=rng.choice([-1.,1.],size=v.shape)
    norm=np.sqrt(sum(float(np.sum(v*v)) for v in vector.values()));vectors['LoRA_A']={k:v/norm for k,v in vector.items()};np.savez(folder/'LoRA_A.npz',**vectors['LoRA_A'])
    with double_tail(model.flow_model,params,n) as timecalls,torch.no_grad():
        for arm in ('V','P'):
            for group,vector in vectors.items():
                for step in (1e-3,3e-4,1e-4):
                    for sign in (-1,1):
                        name=f'{arm}_{group}_{step:g}_{sign:+d}';proposed={k:v+sign*step*vector[k].astype(float) for k,v in initial64.items()};n.assign(params,proposed)
                        assert all(np.array_equal(p.detach().cpu().numpy(),proposed[k]) for k,p in params.items())
                        velocity=tail64(model.flow_model,embedding,kw);loss,q=loss_value(z,noise,velocity,arm,n);torch.cuda.synchronize();assert torch.isfinite(loss)
                        np.savez(folder/f'{name}.npz',velocity=velocity.cpu().numpy(),output=q.cpu().numpy());np.savez(folder/f'{name}_parameters.npz',**proposed)
                        records.append(dict(name=name,arm=arm,group=group,step=step,sign=sign,loss=float(loss)));n.assign(params,initial64)
                        assert all(np.array_equal(p.detach().cpu().numpy(),initial64[k]) for k,p in params.items());del velocity,q,loss,proposed;cap();print('double tail fixed direction',name,flush=True)
        assert len(timecalls)==144
        n.assign(params,{k:v.astype(float) for k,v in initial.items()})
    assert all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items()) and all(p.grad is None for p in params.values())
    save(folder/'execution.json',dict(records=records,shadow_tail_forwards=36,whole_native_forwards=0,backwards=0,optimizer_calls=0,retained_updates=0,parameter_values_and_dtype_restored=True,backend_and_attention_dtype_restored=True,constant_float32_time_projection_promotions=144));seal(folder,'direction_seal.json')

def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),optimizer_calls=0,imports_included=True)
def cap():
    z=usage();assert z['peak_RSS_bytes']<=6*2**30 and max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=8*2**30 and z['artifact_bytes']<=1024*2**20,z
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json'));assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('ADR0 combined cap')));signal.alarm(max(1,int(900-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='probe':probe()
        elif stage in ('repeat','validate'):
            import validate_activated_adapter as v;v.validate(stage)
        elif stage=='directions':directions()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['activated_adapter_derivatives']=sys.modules[__name__];run(sys.argv[1])
