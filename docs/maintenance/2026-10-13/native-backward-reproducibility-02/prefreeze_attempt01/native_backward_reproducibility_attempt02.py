"""NBR0 zero optimizer calls, fixed instrumented native backward census."""
import hashlib
import importlib.metadata
import json
import resource
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime,timezone
from pathlib import Path

MAIN=Path(__file__).resolve().parents[2]; SLAM=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-10-13/native-backward-reproducibility-02'; SUP=BASE/'supervision'
PREVIOUS=MAIN/'docs/maintenance/2026-10-12/native-backward-reproducibility-01'
OLD=MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02'
RECOVERY=MAIN/'docs/maintenance/2026-10-10/wsl-runtime-recovery-01'
START=None; torch=None
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,z):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(z,f,indent=2,allow_nan=False); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''): h.update(x)
    return h.hexdigest()
def repos():
    out={}
    for name,p in [('main',MAIN),('slam',SLAM)]:
        def git(*a): return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*a],text=True).strip()
        out[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
    return out
def freeze():
    original=read(OLD/'freeze.json'); assert len(original['files'])==204; files=dict(read(PREVIOUS/'freeze.json')['files'])
    for folder,count in ((OLD,86),(RECOVERY,40),(PREVIOUS,32)):
        seal=read(folder/'DELIVERY_SEAL.json'); assert len(seal['files'])==count
        for x in seal['files']:
            p=folder/x['path']; assert sha(p)==x['sha256']; files[str(p)]=x['sha256']
        files[str(folder/'DELIVERY_SEAL.json')]=sha(folder/'DELIVERY_SEAL.json')
    paths=[BASE/name for name in ('OWNER_SCOPE.md','PROTOCOL.md','SOURCE_DIFF.json')]
    paths += [Path(__file__),Path(__file__).with_name('validate_native_backward.py'),Path(__file__).with_name('validate_native_mode_inventory.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
        OLD/'bank/synthetic_fixture.npz',OLD/'bank/noise/fit_00.npz',OLD/'preflight/P/initial.npz']
    for p in paths: files[str(p)]=sha(p)
    for p,h in files.items(): assert sha(p)==h,p
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    for k,p in enumerate(paths):
        if p.suffix in ('.py','.ps1'): (snapshot/f'{k:02d}_{p.name}').write_bytes(p.read_bytes())
    expected=read(MAIN/'docs/maintenance/2026-10-12/reference-physical-consistency-01/freeze.json')['repositories']; assert repos()==expected
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=expected,original_NOC4_identities=204,original_NOC4_deliveries=86,recovery_deliveries=40,
        packages={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')},sequence=[f'{arm}_{path}{rep}' for arm in ('V','P') for rep in (1,2) for path in ('full','cache')],
        optimizer_calls=0,retained_updates=0,cap_seconds=1200,cap_GPU_bytes=3*2**30,cap_RSS_bytes=4*2**30,cap_artifact_bytes=512*2**20))
    (BASE/'INCOMPLETE').write_text('NBR0 backward census and independent artifact validation pending.\n'); print('NBR0 frozen',len(files),'identities,0 optimizer calls',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert repos()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')}
    assert (OLD/'INCOMPLETE').exists() and (OLD.parent/'INCOMPLETE').exists()
def seal(folder,name): save(BASE/name,dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def check_seal(folder,name):
    value=read(BASE/name); assert value['freeze_sha256']==sha(BASE/'freeze.json')
    assert value['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def difference(a,b):
    a,b=np.asarray(a),np.asarray(b); assert a.shape==b.shape and a.dtype==b.dtype
    delta=a.astype(float)-b.astype(float); return dict(byte_equal=bool(np.array_equal(a,b)),different=int(np.count_nonzero(a!=b)),size=a.size,max_abs=float(np.max(abs(delta))),
        relative_L2=float(np.linalg.norm(delta)/max(np.linalg.norm(b.astype(float)),1e-30)))
def comparisons(folder):
    sequence=read(BASE/'freeze.json')['sequence']; pairs=[(sequence[a],sequence[b]) for a,b in ((0,2),(1,3),(4,6),(5,7),(0,1),(2,3),(4,5),(6,7))]; results=[]
    for left,right in pairs:
        detail={}
        for filename in ('output.npz','gradients.npz','hooks.npz'):
            with np.load(folder/left/filename) as a,np.load(folder/right/filename) as b:
                assert set(a.files)==set(b.files); detail[filename]={key:difference(a[key],b[key]) for key in a.files}
        results.append(dict(left=left,right=right,details=detail,all_byte_equal=all(z['byte_equal'] for values in detail.values() for z in values.values())))
    return results
def mode_contract(flow):
    import ast,inspect
    from native_output_capability import LowRank
    expected={f'transformer_layers.{k}.{a}' for k in (10,11) for a in ('global_qkv_proj','global_out_proj')}
    modules=dict(flow.named_modules()); modes={name:mod.training for name,mod in modules.items()}
    assert {name for name,value in modes.items() if value}==expected and flow.training is False
    source=Path(inspect.getfile(LowRank)).resolve(); assert sha(source)==read(BASE/'freeze.json')['files'][str(source)]
    tree=ast.parse(source.read_text()); cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='LowRank')
    forward=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='forward')
    reference=ast.parse('return self.base(x) + F.linear(F.linear(x, self.A), self.B)').body
    assert [ast.dump(x,include_attributes=False) for x in forward.body]==[ast.dump(x,include_attributes=False) for x in reference]
    assert [x.arg for x in forward.args.args]==['self','x']
    exceptions=[]
    for name in sorted(expected):
        module=modules[name]; assert type(module) is LowRank
        assert list(module._modules)==['base'] and type(module.base) is torch.nn.Linear and module.base.training is False
        assert tuple(module.A.shape)==(8,module.base.in_features) and tuple(module.B.shape)==(module.base.out_features,8)
        assert torch.count_nonzero(module.B).item()==0
        exceptions.append(dict(name=name,type_module=type(module).__module__,type_name=type(module).__name__,training=module.training,
            children=[dict(name='base',type='Linear',training=module.base.training)],A_shape=list(module.A.shape),B_shape=list(module.B.shape),B_nonzero=0))
    return dict(modes=modes,exceptions=exceptions,source_path=str(source),source_sha256=sha(source),forward_AST_exact=True,mode_mutations=0)
def mode_inventory():
    global torch,np
    verify(); import numpy as np; import torch; import native_conditioned_comparison as n
    model,params,initial,audit=n.model(); reference=n.load(OLD/'preflight/P/initial.npz')
    assert set(initial)==set(reference) and all(np.array_equal(initial[k],reference[k]) for k in initial)
    inventory=mode_contract(model.flow_model); state=n.n.noc.numpy_state(params)
    hashes={k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.tobytes()).hexdigest()) for k,v in state.items()}
    save(BASE/'mode_inventory.json',dict(utc=now(),inventory=inventory,strict_checkpoint=audit,trainable_count=sum(v.numel() for v in params.values()),
        trainable_hashes=hashes,frozen_parameters_sha256=n.frozen_digest(model.flow_model),native_forwards=0,backwards=0,optimizer_calls=0))
    print('Exact mode inventory passes: four source-proven linear wrappers, all other modules eval;0 forwards/backwards',flush=True)
def diagnose():
    global torch,np
    verify(); import numpy as np; import torch
    import native_conditioned_comparison as n
    from rap_slam.rap_precision import ieee_matmul
    assert torch.__version__=='2.7.0+cu128' and torch.get_num_threads()==1
    folder=BASE/'traces'; folder.mkdir(); model,params,initial,audit=n.model(); z=n.load(OLD/'bank/synthetic_fixture.npz'); noise=torch.tensor(n.load(OLD/'bank/noise/fit_00.npz')['noise'],device='cuda')
    old_initial=n.load(OLD/'preflight/P/initial.npz'); assert set(initial)==set(old_initial) and all(np.array_equal(initial[k],old_initial[k]) for k in initial)
    assert sum(p.numel() for p in params.values())==443904
    batch=n.n.noc.batch({k:z[k] for k in n.n.OBS}); assert 'truth' not in batch and 'target' not in batch
    kw=n.args(batch,noise,1.); frozen=n.frozen_digest(model.flow_model); metadata=[]
    assert read(BASE/'mode_validation.json')['passed']; mode_data=mode_contract(model.flow_model); modes=mode_data['modes']; assert mode_data==read(BASE/'mode_inventory.json')['inventory']
    settings=dict(tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),cudnn_deterministic=torch.backends.cudnn.deterministic,
        flash_sdp=torch.backends.cuda.flash_sdp_enabled(),memory_efficient_sdp=torch.backends.cuda.mem_efficient_sdp_enabled(),math_sdp=torch.backends.cuda.math_sdp_enabled(),
        cudnn_sdp=torch.backends.cuda.cudnn_sdp_enabled(),active_SDPA_backend='not profiled; enabled flags do not prove dispatch')
    with ieee_matmul():
        for arm in ('V','P'):
            n.assign(params,initial)
            with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16): embedding=n.prefix(model.flow_model,kw)
            np.save(folder/f'{arm}_prefix.npy',embedding.cpu().numpy()); modules={name:mod for name,mod in model.flow_model.named_modules() if name in [f'transformer_layers.{k}.{a}' for k in (10,11) for a in ('global_qkv_proj','global_out_proj')]}
            assert len(modules)==4
            for rep in (1,2):
                for path in ('full','cache'):
                    name=f'{arm}_{path}{rep}'; dest=folder/name; dest.mkdir(); n.assign(params,initial)
                    for p in params.values(): p.grad=None
                    captured={}; handles=[]
                    def hook(key):
                        def apply(mod,args,out):
                            x=args[0]
                            with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16): rank=torch.nn.functional.linear(x,mod.A)
                            captured[key+'|input']=x.detach().cpu().numpy().copy(); captured[key+'|rank']=rank.detach().cpu().numpy().copy(); captured[key+'|output']=out.detach().cpu().numpy().copy()
                            out.register_hook(lambda g: captured.__setitem__(key+'|scaled_gradient',g.detach().cpu().numpy().copy()))
                        return apply
                    try:
                        for key,mod in modules.items(): handles.append(mod.register_forward_hook(hook(key)))
                        with torch.autocast('cuda',dtype=torch.float16): velocity=model.flow_model(**kw) if path=='full' else n.tail(model.flow_model,embedding,kw)
                        velocity.retain_grad(); loss,terms=n.loss_value(z,noise,velocity,arm); assert bool(torch.isfinite(loss))
                        n.backward(params,loss,arm); torch.cuda.synchronize()
                    finally:
                        for handle in handles: handle.remove()
                    gradients={key:p.grad.detach().cpu().numpy().copy() for key,p in params.items()}; assert all(np.isfinite(g).all() for g in gradients.values())
                    factor=n.SETTINGS['backward_multipliers'][arm]; upstream=(-velocity.grad.detach().cpu().numpy()/factor).copy(); output=(noise-velocity).detach().cpu().numpy().copy()
                    assert np.isfinite(upstream).all() and set(captured)=={key+'|'+field for key in modules for field in ('input','rank','output','scaled_gradient')}
                    assert all(np.array_equal(p.detach().cpu().numpy(),initial[key]) for key,p in params.items())
                    np.savez(dest/'output.npz',output=output,velocity=velocity.detach().cpu().numpy(),upstream=upstream); np.savez(dest/'gradients.npz',**gradients); np.savez_compressed(dest/'hooks.npz',**captured)
                    np.savez(dest/'parameters_after.npz',**n.n.noc.numpy_state(params))
                    meta=dict(name=name,arm=arm,path=path,rep=rep,loss=float(loss.detach()),terms={k:float(v.detach()) for k,v in terms.items()},factor=factor,
                        parameters_unchanged_byteexact=True,optimizer_calls=0,hook_modules=list(modules),rank_linear_extra_calls=4)
                    save(dest/'trace.json',meta); metadata.append(meta); cap(); print('zero-update backward',name,'loss',meta['loss'],flush=True)
                    del velocity,loss,gradients,captured,upstream,output
    assert n.frozen_digest(model.flow_model)==frozen and modes=={key:mod.training for key,mod in model.flow_model.named_modules()}
    save(folder/'execution.json',dict(utc=now(),traces=metadata,strict_checkpoint=audit,frozen_parameters_sha256=frozen,native_forwards=8,prefix_forwards=2,
        backwards=8,optimizer_calls=0,retained_updates=0,settings_before=settings,initialized_trainables=443904,instrumented=True,mode_inventory_sha256=sha(BASE/'mode_inventory.json'),mode_validation_sha256=sha(BASE/'mode_validation.json')))
    seal(folder,'trace_seal.json'); compare=comparisons(folder)
    old_comparisons=[]
    for arm in ('V','P'):
        for path,oldpath in [('cache',OLD/'preflight'/arm),('full',OLD/'preflight_replay'/arm)]:
            with np.load(folder/f'{arm}_{path}1/gradients.npz') as a,np.load(oldpath/'gradients.npz') as b:
                old_comparisons.append(dict(arm=arm,path=path,gradients={key:difference(a[key],b[key]) for key in a.files}))
    save(BASE/'results.json',dict(utc=now(),pairs=compare,old_comparisons=old_comparisons,all_instrumented_pairs_byte_equal=all(z['all_byte_equal'] for z in compare),
        decision='INSTRUMENTED_BACKWARD_REPRODUCIBLE' if all(z['all_byte_equal'] for z in compare) else 'INSTRUMENTED_BACKWARD_MISMATCH_LOCALIZED',
        unique_cause_resolved=False,native_fit_admitted=False,optimizer_calls=0)); cap()
def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,
        artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),optimizer_calls=0,imports_included_in_time=True)
def cap():
    u=usage(); assert u['peak_RSS_bytes']<=4*2**30 and max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=3*2**30 and u['artifact_bytes']<=512*2**20,u
    if (SUP/'host_latest.json').exists(): assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START,np
    START=time.monotonic(); used=sum(read(p)['wall_seconds'] for folder in (SUP,PREVIOUS/'supervision') for p in folder.glob('*/child_exit.json')); assert used<1200
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('NBR0 combined child cap'))); signal.alarm(max(1,int(1200-used))); ok=False; error=None
    try:
        if stage=='freeze': freeze()
        elif stage=='mode': mode_inventory()
        elif stage=='validate_mode':
            import validate_native_mode_inventory as v; v.validate()
        elif stage=='diagnose': diagnose()
        elif stage=='validate':
            import numpy as np; import validate_native_backward as v; v.validate()
        else: raise ValueError(stage)
        cap(); ok=True
    except BaseException as ex:
        error=repr(ex); traceback.print_exc(); save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error,**usage()))
    finally:
        signal.alarm(0); save(SUP/stage/'child_exit.json',dict(utc=now(),success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok: sys.exit(1)
if __name__=='__main__':
    sys.modules['native_backward_reproducibility']=sys.modules[__name__]; run(sys.argv[1])
