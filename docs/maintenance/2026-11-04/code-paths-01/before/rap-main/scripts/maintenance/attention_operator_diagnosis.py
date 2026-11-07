"""AOD0 fixed local attention VJPs; no whole-native inference or parameter updates."""
import importlib.metadata,inspect,json,resource,signal,sys,time,traceback
from contextlib import nullcontext
from pathlib import Path
import native_backward_reproducibility_attempt02 as r
MAIN=r.MAIN; PRIOR=MAIN/'docs/maintenance/2026-10-13/native-backward-reproducibility-02'
BASE=MAIN/'docs/maintenance/2026-10-13/attention-operator-diagnosis-01'; SUP=BASE/'supervision'
read,save,sha,now=r.read,r.save,r.sha,r.now
torch=None; START=None
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert r.repos()==f['repositories']
    assert f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')}
def freeze():
    global torch
    import torch
    f=read(PRIOR/'freeze.json'); files=dict(f['files']); seal=read(PRIOR/'DELIVERY_SEAL.json'); assert len(seal['files'])==110
    for z in seal['files']:
        p=(PRIOR/z['path']).resolve(); assert PRIOR.resolve() in p.parents and sha(p)==z['sha256']; files[str(p)]=z['sha256']
    paths=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_attention_operator.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
        PRIOR/'DELIVERY_SEAL.json',Path(inspect.getfile(torch.nn.attention.sdpa_kernel))]
    for p in paths: files[str(p)]=sha(p)
    for p,h in files.items(): assert sha(p)==h,p
    assert r.repos()==f['repositories']; snap=BASE/'source_snapshot';snap.mkdir()
    for k,p in enumerate(paths):
        if p.suffix in ('.py','.ps1'): (snap/f'{k:02d}_{p.name}').write_bytes(p.read_bytes())
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=f['repositories'],packages={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')},
        boundary='transformer_layers.11 global attention',arms=['V','P'],backends=['default','math'],repetitions=2,cap_seconds=600,cap_GPU_bytes=3*2**30,cap_RSS_bytes=4*2**30,cap_artifacts=256*2**20))
    (BASE/'INCOMPLETE').write_text('AOD0 isolated operator measurement and independent CPU audit pending.\n');print('AOD0 frozen',len(files),'identities',flush=True)
def flags():
    return [torch.backends.cuda.flash_sdp_enabled(),torch.backends.cuda.mem_efficient_sdp_enabled(),torch.backends.cuda.math_sdp_enabled(),torch.backends.cuda.cudnn_sdp_enabled()]
def probe():
    global torch,np
    verify(); import torch;import numpy as np;import native_conditioned_comparison as n
    import rectified_point_flow.flow_model.layer as layer_source
    from rap_slam.rap_precision import ieee_matmul
    from torch.nn.attention import sdpa_kernel,SDPBackend
    r.torch=torch; model,params,initial,audit=n.model(); assert r.mode_contract(model.flow_model)==read(PRIOR/'mode_inventory.json')['inventory']
    layer=model.flow_model.transformer_layers[11]; assert layer.qk_norm; frozen=n.frozen_digest(model.flow_model); incoming_flags=flags(); folder=BASE/'bank'; folder.mkdir(); rows=[]; projection=[]
    module='transformer_layers.11'; projection_name=module+'.global_out_proj'; qkv_name=module+'.global_qkv_proj'
    with ieee_matmul():
        for arm in ('V','P'):
            with np.load(PRIOR/f'traces/{arm}_full1/hooks.npz') as z:
                raw=z[qkv_name+'|output'].copy(); saved_out=z[projection_name+'|input'].copy(); go=z[projection_name+'|scaled_gradient'].copy()
            cotangents=[]
            for rep in (1,2):
                leaf=torch.tensor(saved_out,device='cuda',requires_grad=True)
                with torch.autocast('cuda',dtype=torch.float16): y=layer.global_out_proj(leaf)
                cot=torch.autograd.grad(y,leaf,torch.tensor(go,device='cuda'))[0]; cotangents.append(cot.detach().cpu().numpy().copy())
                assert torch.isfinite(cot).all(); del leaf,y,cot
            assert np.array_equal(*cotangents); projection.append(dict(arm=arm,cotangent_repeated_byteexact=True))
            np.savez_compressed(folder/f'{arm}_input.npz',raw=raw,saved_out=saved_out,go=go,cotangent=cotangents[0])
            for backend in ('default','math'):
                for rep in (1,2):
                    name=f'{arm}_{backend}{rep}'; leaf=torch.tensor(raw,device='cuda',requires_grad=True); cot=torch.tensor(cotangents[0],device='cuda')
                    profiler=torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) if rep==1 else nullcontext()
                    context=sdpa_kernel(SDPBackend.MATH) if backend=='math' else nullcontext(); started=time.monotonic()
                    with context,profiler:
                        with torch.autocast('cuda',dtype=torch.float16):
                            qkv=leaf.reshape(-1,3,layer.num_heads,layer.head_dim); normalized=layer._qk_norm(qkv,layer.global_q_norm,layer.global_k_norm)
                            out=layer_source._flash_attn_varlen(normalized.to(layer.attn_dtype),torch.tensor([0,len(raw)],dtype=torch.int32,device='cuda'),layer.max_points_per_batch,layer.softcap)
                            out=out.reshape(len(raw),layer.dim).to(cot.dtype)
                        raw_grad,norm_grad=torch.autograd.grad(out,(leaf,normalized),cot);torch.cuda.synchronize()
                    assert flags()==incoming_flags and all(torch.isfinite(z).all() for z in (out,raw_grad,norm_grad))
                    np.savez_compressed(folder/f'{name}.npz',output=out.detach().cpu().numpy(),raw_gradient=raw_grad.cpu().numpy(),normalized=normalized.detach().cpu().numpy(),normalized_gradient=norm_grad.cpu().numpy())
                    names=sorted({z.name for z in profiler.events() if 'scaled_dot_product' in z.name}) if rep==1 else []
                    delta=float(np.max(abs(out.detach().cpu().numpy()-saved_out))); rows.append(dict(name=name,arm=arm,backend=backend,rep=rep,wall_seconds=time.monotonic()-started,
                        dispatched_ATen_names=names,archive_forward_max_delta=delta,heads=layer.num_heads,head_dim=layer.head_dim))
                    del leaf,cot,out,raw_grad,norm_grad,normalized;cap();print('isolated attention',name,'archive delta',delta,'dispatch',names,flush=True)
    assert flags()==incoming_flags and all(p.grad is None for p in params.values()) and all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items())
    assert n.frozen_digest(model.flow_model)==frozen
    save(folder/'execution.json',dict(utc=now(),records=rows,projection=projection,strict_checkpoint=audit,operator_VJPs=8,projection_VJPs=4,native_whole_forwards=0,prefix_calls=0,optimizer_calls=0,parameter_updates=0,backend_flags_restored=True))
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={p.name:sha(p) for p in sorted(folder.iterdir()) if p.is_file()}));verify()
def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),optimizer_calls=0,imports_included=True)
def cap():
    z=usage();assert z['peak_RSS_bytes']<=4*2**30 and max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=3*2**30 and z['artifact_bytes']<=256*2**20,z
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json'));assert used<600
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('AOD0 combined cap')));signal.alarm(max(1,int(600-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='probe':probe()
        elif stage=='validate':import validate_attention_operator as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['attention_operator_diagnosis']=sys.modules[__name__];run(sys.argv[1])
