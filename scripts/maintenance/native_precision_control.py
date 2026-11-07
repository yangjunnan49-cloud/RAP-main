"""FPC0 fixed precision controls, no optimizer or retained parameter updates."""
import importlib.metadata,json,resource,signal,sys,time,traceback
from contextlib import contextmanager
from pathlib import Path
import native_math_reproducibility as r
MAIN=r.MAIN; PRIOR=r.BASE; BASE=MAIN/'docs/maintenance/2026-10-13/native-precision-control-01';SUP=BASE/'supervision'
read,save,sha,now=r.read,r.save,r.sha,r.now
torch=None; START=None

def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert r.repos()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')}
    assert (r.OLD/'INCOMPLETE').exists() and (r.OLD.parent/'INCOMPLETE').exists() and (r.PREVIOUS/'INCOMPLETE').exists()

def freeze():
    previous=read(PRIOR/'freeze.json');files=dict(previous['files']);delivery=read(PRIOR/'DELIVERY_SEAL.json');assert len(delivery['files'])==142
    for x in delivery['files']:
        p=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in p.parents and sha(p)==x['sha256'];files[str(p)]=x['sha256']
    paths=[BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',Path(__file__),Path(__file__).with_name('validate_native_precision.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PRIOR/'DELIVERY_SEAL.json']
    for p in paths:files[str(p)]=sha(p)
    for p,h in files.items():assert sha(p)==h,p
    assert r.repos()==previous['repositories'];snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):(snap/p.name).write_bytes(p.read_bytes())
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=previous['repositories'],packages=previous['packages'],conditions=['S','D'],sequence=[f'{a}_{b}{c}' for a in ('V','P') for c in (1,2) for b in ('full','cache')],
        cap_seconds=900,cap_RSS_bytes=6*2**30,cap_GPU_bytes=6*2**30,cap_artifact_bytes=256*2**20,optimizer_calls=0,retained_updates=0))
    (BASE/'INCOMPLETE').write_text('FPC0 scoped precision controls and independent artifact validation pending.\n');print('FPC0 frozen',len(files),'identities',flush=True)

def flags():return [torch.backends.cuda.flash_sdp_enabled(),torch.backends.cuda.mem_efficient_sdp_enabled(),torch.backends.cuda.math_sdp_enabled(),torch.backends.cuda.cudnn_sdp_enabled()]

@contextmanager
def precision(flow):
    from rap_slam.rap_precision import ieee_matmul
    from torch.nn.attention import sdpa_kernel,SDPBackend
    original=[layer.attn_dtype for layer in flow.transformer_layers];incoming=flags();assert len(original)==12 and all(x==torch.float16 for x in original)
    try:
        for layer in flow.transformer_layers:layer.attn_dtype=torch.float32
        with ieee_matmul(),sdpa_kernel(SDPBackend.MATH),torch.autocast('cuda',enabled=False):
            assert flags()==[False,False,True,False];yield
    finally:
        for layer,value in zip(flow.transformer_layers,original):layer.attn_dtype=value
        assert [layer.attn_dtype for layer in flow.transformer_layers]==original and flags()==incoming

def loss_value(z,noise,velocity,arm,condition,n):
    assert velocity.dtype==torch.float32
    if condition=='S':value,terms=n.loss_value(z,noise,velocity,arm);q=(noise-velocity).double()
    else:
        assert condition=='D';q=noise.double()-velocity.double()
        if arm=='V':value=(velocity.double()-(noise.double()-torch.tensor(z['target'],device='cuda').double())).square().mean();terms=dict(velocity=value)
        else:value,terms=n.old.obj(z,q)
    return value,terms,q

def seal(folder,name):save(BASE/name,dict(freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))

def check_seal(folder,name):
    value=read(BASE/name);assert value['freeze_sha256']==sha(BASE/'freeze.json') and value['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}

def model_data():
    global torch,np
    import torch;import numpy as np;import native_conditioned_comparison as n
    r.torch=torch;r.BASE=BASE
    model,params,initial,audit=n.model();old=n.load(r.OLD/'preflight/P/initial.npz');assert all(np.array_equal(initial[k],v) for k,v in old.items()) and set(initial)==set(old)
    assert sum(p.numel() for p in params.values())==443904 and r.mode_contract(model.flow_model)==read(r.PRIOR/'mode_inventory.json')['inventory']
    z=n.load(r.OLD/'bank/synthetic_fixture.npz');noise=torch.tensor(n.load(r.OLD/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=n.args(n.n.noc.batch({k:z[k] for k in n.n.OBS}),noise,1.)
    return n,model,params,initial,audit,z,noise,kw

def probe():
    verify();n,model,params,initial,audit,z,noise,kw=model_data();folder=BASE/'traces';folder.mkdir();records=[]
    frozen=n.frozen_digest(model.flow_model);modes={k:v.training for k,v in model.flow_model.named_modules()};incoming=flags()
    with precision(model.flow_model):
        for condition in ('S','D'):
            for arm in ('V','P'):
                n.assign(params,initial)
                with torch.no_grad():embedding=n.prefix(model.flow_model,kw)
                assert embedding.dtype==torch.float32;np.save(folder/f'{condition}_{arm}_prefix.npy',embedding.cpu().numpy())
                for rep in (1,2):
                    for path in ('full','cache'):
                        name=f'{condition}_{arm}_{path}{rep}';dest=folder/name;dest.mkdir();n.assign(params,initial)
                        for p in params.values():p.grad=None
                        dtypes={};handles=[]
                        def capture(key):
                            def hook(mod,args,out):
                                assert args[0].dtype==out.dtype==torch.float32;dtypes[key]=dict(input=str(args[0].dtype),output=str(out.dtype))
                            return hook
                        modules={k:v for k,v in model.flow_model.named_modules() if k in {f'transformer_layers.{i}.{j}' for i in (10,11) for j in ('global_qkv_proj','global_out_proj')}};assert len(modules)==4
                        try:
                            for k,v in modules.items():handles.append(v.register_forward_hook(capture(k)))
                            profile=torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) if rep==1 and path=='full' else None
                            if profile:profile.__enter__()
                            try:
                                velocity=model.flow_model(**kw) if path=='full' else n.tail(model.flow_model,embedding,kw)
                                velocity.retain_grad();loss,terms,q=loss_value(z,noise,velocity,arm,condition,n);assert torch.isfinite(loss)
                                n.backward(params,loss,arm);torch.cuda.synchronize()
                            finally:
                                if profile:profile.__exit__(None,None,None)
                            dispatch=sorted({x.name for x in profile.events() if 'scaled_dot_product' in x.name}) if profile else []
                        finally:
                            for h in handles:h.remove()
                        assert len(dtypes)==4 and all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items())
                        grads={k:p.grad.detach().cpu().numpy().copy() for k,p in params.items()};assert all(np.isfinite(g).all() for g in grads.values())
                        factor=n.SETTINGS['backward_multipliers'][arm];upstream=(-velocity.grad.detach().cpu().numpy()/factor).copy()
                        np.savez(dest/'output.npz',velocity=velocity.detach().cpu().numpy(),output=q.detach().cpu().numpy(),upstream=upstream);np.savez(dest/'gradients.npz',**grads);np.savez(dest/'parameters_after.npz',**n.n.noc.numpy_state(params))
                        record=dict(name=name,condition=condition,arm=arm,path=path,rep=rep,loss=float(loss),terms={k:float(v.detach()) for k,v in terms.items()},linear_dtypes=dtypes,dispatched_ATen_names=dispatch,factor=factor)
                        save(dest/'trace.json',record);records.append(record);cap();print('precision backward',name,'loss',record['loss'],flush=True)
                        del velocity,loss,q,grads,upstream
    assert flags()==incoming and frozen==n.frozen_digest(model.flow_model) and modes=={k:v.training for k,v in model.flow_model.named_modules()}
    save(folder/'execution.json',dict(utc=now(),records=records,strict_checkpoint=audit,native_forwards=16,backwards=16,prefix_forwards=4,initialized_trainables=443904,optimizer_calls=0,retained_updates=0,backend_and_attention_dtype_restored=True,frozen_parameters_and_modes_preserved=True))
    seal(folder,'trace_seal.json');verify()

def directions():
    verify();check_seal(BASE/'traces','trace_seal.json');assert read(BASE/'repeat_validation.json')['all_pairs_byteexact']
    n,model,params,initial,audit,z,noise,kw=model_data();folder=BASE/'directions';folder.mkdir();records=[];frozen=n.frozen_digest(model.flow_model)
    # Reuse the already predeclared NMR0 directions, never select or tune them.
    vectors={group:n.load(PRIOR/f'directions/{group}.npz') for group in ('final_mlp','LoRA_B')}
    with precision(model.flow_model),torch.no_grad():
        for arm in ('V','P'):
            for group,vector in vectors.items():
                for step in (1e-3,3e-4,1e-4):
                    for sign in (-1,1):
                        name=f'{arm}_{group}_{step:g}_{sign:+d}';proposed={k:(v+sign*step*vector[k]).astype(v.dtype) for k,v in initial.items()};n.assign(params,proposed)
                        assert all(np.array_equal(p.detach().cpu().numpy(),proposed[k]) for k,p in params.items())
                        velocity=model.flow_model(**kw);values={};outputs={'velocity':velocity.cpu().numpy()}
                        for condition in ('S','D'):
                            loss,terms,q=loss_value(z,noise,velocity,arm,condition,n);assert torch.isfinite(loss);values[condition]=float(loss);outputs[condition+'_output']=q.cpu().numpy()
                        torch.cuda.synchronize();np.savez(folder/f'{name}.npz',**outputs);np.savez(folder/f'{name}_parameters.npz',**proposed)
                        records.append(dict(name=name,arm=arm,group=group,step=step,sign=sign,losses=values));n.assign(params,initial)
                        assert all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items());del velocity,q,loss,outputs,proposed;cap();print('precision fixed direction',name,flush=True)
    assert frozen==n.frozen_digest(model.flow_model) and all(p.grad is None for p in params.values())
    save(folder/'execution.json',dict(records=records,native_forwards=24,backwards=0,optimizer_calls=0,retained_updates=0,temporary_parameters_restored_byteexact=True,backend_and_attention_dtype_restored=True));seal(folder,'direction_seal.json')

def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),optimizer_calls=0,imports_included=True)
def cap():
    z=usage();assert z['peak_RSS_bytes']<=6*2**30 and max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=6*2**30 and z['artifact_bytes']<=256*2**20,z
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json'));assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('FPC0 combined cap')));signal.alarm(max(1,int(900-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='probe':probe()
        elif stage in ('repeat','validate'):
            import validate_native_precision as v;v.validate(stage)
        elif stage=='directions':directions()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['native_precision_control']=sys.modules[__name__];run(sys.argv[1])
