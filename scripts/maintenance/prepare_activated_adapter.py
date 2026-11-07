"""One-shot source preparation, no numerical imports/execution."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/activated-adapter-derivatives-01';BASE.mkdir(exist_ok=True)
p=ROOT/'scripts/maintenance/native_double_tail.py';old=p.read_text(encoding='utf-8');new=old.replace('native-double-tail-control-01','activated-adapter-derivatives-01').replace('DTC0','ADR0')
new=new.replace("PRIOR=MAIN/'docs/maintenance/2026-10-13/native-precision-control-01';NMR=r.BASE", "PRIOR=MAIN/'docs/maintenance/2026-10-13/native-precision-control-01';NMR=r.BASE\nPREDECESSOR=MAIN/'docs/maintenance/2026-10-13/native-shadow-step-control-01'\nDESIGN=MAIN/'docs/maintenance/2026-10-13/conditioning-comparison-design-01'")
new=new.replace("f=read(PRIOR/'freeze.json');files=dict(f['files']);seal=read(PRIOR/'DELIVERY_SEAL.json');assert len(seal['files'])==169", "assert read(PREDECESSOR/'validation.json')['functional_conjunction']\n    f=read(PREDECESSOR/'freeze.json');files=dict(f['files']);seal=read(PREDECESSOR/'DELIVERY_SEAL.json');assert len(seal['files'])==70")
new=new.replace("p=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in p.parents", "p=(PREDECESSOR/x['path'].replace(chr(92),'/')).resolve();assert PREDECESSOR.resolve() in p.parents")
new=new.replace("paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_native_double_tail.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PRIOR/'DELIVERY_SEAL.json',Path(inspect.getfile(Timesteps))]", "design=read(DESIGN/'DELIVERY_SEAL.json');assert len(design['files'])==5\n    for x in design['files']:\n        p=(DESIGN/x['path']).resolve();assert DESIGN.resolve() in p.parents and sha(p)==x['sha256'];files[str(p)]=x['sha256']\n    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'SOURCE_DIFF.json',Path(__file__),Path(__file__).with_name('validate_activated_adapter.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PREDECESSOR/'DELIVERY_SEAL.json',DESIGN/'DELIVERY_SEAL.json',Path(inspect.getfile(Timesteps))]")
new=new.replace('initial64={k:v.astype(np.float64) for k,v in initial.items()}', "initial64=activation(initial);np.savez(BASE/'activation_baseline.npz',**initial64)")
new=new.replace('initial64={k:v.astype(float) for k,v in initial.items()};vectors=', 'initial64=activation(initial);vectors=')
new=new.replace("    with double_tail(model.flow_model,params,n) as timecalls,torch.no_grad():", "    rng=np.random.default_rng(2026101308);vector={k:np.zeros_like(v,dtype=float) for k,v in initial.items()}\n    for k,v in vector.items():\n        if k.endswith('.A'):v[:]=rng.choice([-1.,1.],size=v.shape)\n    norm=np.sqrt(sum(float(np.sum(v*v)) for v in vector.values()));vectors['LoRA_A']={k:v/norm for k,v in vector.items()};np.savez(folder/'LoRA_A.npz',**vectors['LoRA_A'])\n    with double_tail(model.flow_model,params,n) as timecalls,torch.no_grad():")
new=new.replace("                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as profile:", "                captured={};handles=[]\n                def hook(key):\n                    def apply(mod,args,out):\n                        captured[key+'|input']=args[0].detach().cpu().numpy().copy()\n                        with torch.no_grad():captured[key+'|rank']=torch.nn.functional.linear(args[0],mod.A).cpu().numpy().copy()\n                        out.register_hook(lambda g:captured.__setitem__(key+'|scaled_gradient',g.detach().cpu().numpy().copy()))\n                    return apply\n                modules={k:v for k,v in model.flow_model.named_modules() if k in {f'transformer_layers.{i}.{j}' for i in (10,11) for j in ('global_qkv_proj','global_out_proj')}};assert len(modules)==4\n                for k,v in modules.items():handles.append(v.register_forward_hook(hook(k)))\n                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as profile:")
new=new.replace('                grad={k:p.grad', "                for h in handles:h.remove()\n                assert len(captured)==12\n                np.savez_compressed(dest/'hooks.npz',**captured)\n                grad={k:p.grad")
new=new.replace("del velocity,loss,q,grad;cap()", "del velocity,loss,q,grad,captured;cap()")
new=new.replace('        n.assign(params,initial64)\n    assert all', '        n.assign(params,{k:v.astype(float) for k,v in initial.items()})\n    assert all')
new=new.replace('        assert len(timecalls)==96\n    assert all', '        assert len(timecalls)==144\n        n.assign(params,{k:v.astype(float) for k,v in initial.items()})\n    assert all')
new=new.replace('shadow_tail_forwards=24','shadow_tail_forwards=36').replace('constant_float32_time_projection_promotions=96','constant_float32_time_projection_promotions=144')
new=new.replace('cap_artifact_bytes=256*2**20','cap_artifact_bytes=1024*2**20').replace("z['artifact_bytes']<=256*2**20","z['artifact_bytes']<=1024*2**20")
new=new.replace('import validate_native_double_tail as v','import validate_activated_adapter as v')
new=new.replace("assert read(BASE/'repeat_validation.json')['all_pairs_byteexact']", "assert read(BASE/'repeat_validation.json')['prerequisite_conjunction']")
new=new.replace("sys.modules['native_double_tail']=sys.modules[__name__]", "sys.modules['activated_adapter_derivatives']=sys.modules[__name__]")
index=new.index('\ndef probe():')
new=new[:index]+'''
def activation(initial):
    original={k:v.astype(float) for k,v in initial.items()};rng=np.random.default_rng(2026101307)
    keys=[k for k in original if k.endswith('.B')];assert len(keys)==4 and all(not np.any(original[k]) for k in keys)
    count=sum(original[k].size for k in keys);assert count==32768
    for key in keys:original[key]=rng.choice([-1.,1.],size=original[key].shape)*(1e-3/np.sqrt(count))
    assert abs(np.sqrt(sum(float(np.sum(original[k]**2)) for k in keys))-1e-3)<=1e-15
    return original
''' +new[index:]
ast.parse(new);target=ROOT/'scripts/maintenance/activated_adapter_derivatives.py';target.write_text(new,encoding='utf-8',newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(BASE/'SOURCE_DIFF.json').write_text(json.dumps(dict(original_path=str(p),original_sha256=sha(p),new_path=str(target),new_sha256=sha(target),diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=p.name,tofile=target.name))),indent=2)+'\n',encoding='utf-8')
print('ADR0 source prepared, no numerical execution')
