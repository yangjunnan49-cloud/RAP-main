"""One-shot preparation only; new bounded math census, no numerical imports."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-13/native-math-reproducibility-01'
BASE.mkdir()
source=ROOT/'scripts/maintenance/native_backward_reproducibility_attempt02.py'
old=source.read_text(encoding='utf-8'); new=old
new=new.replace('"""NBR0 zero optimizer calls, fixed instrumented native backward census."""','"""NMR0 whole-native scoped math attention census, zero optimizer updates."""')
new=new.replace("BASE=MAIN/'docs/maintenance/2026-10-13/native-backward-reproducibility-02'; SUP=BASE/'supervision'", "BASE=MAIN/'docs/maintenance/2026-10-13/native-math-reproducibility-01'; SUP=BASE/'supervision'\nPRIOR=MAIN/'docs/maintenance/2026-10-13/native-backward-reproducibility-02'\nAOD=MAIN/'docs/maintenance/2026-10-13/attention-operator-diagnosis-01'")
a=new.index('def freeze():'); b=new.index('\ndef verify():',a)
new=new[:a]+'''def freeze():
    original=read(AOD/'freeze.json'); files=dict(original['files'])
    for folder,count in ((PRIOR,110),(AOD,55)):
        delivery=read(folder/'DELIVERY_SEAL.json'); assert len(delivery['files'])==count
        for x in delivery['files']:
            p=(folder/x['path'].replace(chr(92),'/')).resolve(); assert folder.resolve() in p.parents
            assert sha(p)==x['sha256']; files[str(p)]=x['sha256']
        files[str(folder/'DELIVERY_SEAL.json')]=sha(folder/'DELIVERY_SEAL.json')
    paths=[BASE/name for name in ('OWNER_SCOPE.md','PROTOCOL.md','SOURCE_DIFF.json')]
    paths += [Path(__file__),Path(__file__).with_name('validate_native_math.py'),Path(__file__).with_name('validate_native_backward.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    for p in paths: files[str(p)]=sha(p)
    for p,h in files.items(): assert sha(p)==h,p
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    for k,p in enumerate(paths):
        if p.suffix in ('.py','.ps1'): (snapshot/f'{k:02d}_{p.name}').write_bytes(p.read_bytes())
    assert repos()==original['repositories']
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=original['repositories'],packages=original['packages'],sequence=[f'{arm}_{path}{rep}' for arm in ('V','P') for rep in (1,2) for path in ('full','cache')],
        optimizer_calls=0,retained_updates=0,cap_seconds=1200,cap_GPU_bytes=6*2**30,cap_RSS_bytes=6*2**30,cap_artifact_bytes=512*2**20,backend='process-local SDPA MATH'))
    (BASE/'INCOMPLETE').write_text('NMR0 bounded math census and independent artifact validation pending.\\n'); print('NMR0 frozen',len(files),'identities',flush=True)

def backend_flags():
    return dict(flash=torch.backends.cuda.flash_sdp_enabled(),efficient=torch.backends.cuda.mem_efficient_sdp_enabled(),math=torch.backends.cuda.math_sdp_enabled(),cudnn=torch.backends.cuda.cudnn_sdp_enabled())
''' +new[b:]
new=new.replace("assert read(BASE/'mode_validation.json')['passed']; mode_data=mode_contract(model.flow_model); modes=mode_data['modes']; assert mode_data==read(BASE/'mode_inventory.json')['inventory']", "assert read(PRIOR/'mode_validation.json')['passed']; mode_data=mode_contract(model.flow_model); modes=mode_data['modes']; assert mode_data==read(PRIOR/'mode_inventory.json')['inventory']")
new=new.replace("active_SDPA_backend='not profiled; enabled flags do not prove dispatch'", "active_SDPA_backend='scoped math, first full trace per arm profiled'")
new=new.replace('    with ieee_matmul():\n        for arm', "    from torch.nn.attention import sdpa_kernel,SDPBackend\n    from contextlib import nullcontext\n    incoming=backend_flags()\n    with ieee_matmul(),sdpa_kernel(SDPBackend.MATH):\n        assert backend_flags()==dict(flash=False,efficient=False,math=True,cudnn=False)\n        for arm")
new=new.replace("                        with torch.autocast('cuda',dtype=torch.float16): velocity=model.flow_model(**kw) if path=='full' else n.tail(model.flow_model,embedding,kw)\n                        velocity.retain_grad(); loss,terms=n.loss_value(z,noise,velocity,arm); assert bool(torch.isfinite(loss))\n                        n.backward(params,loss,arm); torch.cuda.synchronize()", "                        profiler=torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) if rep==1 and path=='full' else nullcontext()\n                        with profiler:\n                            with torch.autocast('cuda',dtype=torch.float16): velocity=model.flow_model(**kw) if path=='full' else n.tail(model.flow_model,embedding,kw)\n                            velocity.retain_grad(); loss,terms=n.loss_value(z,noise,velocity,arm); assert bool(torch.isfinite(loss))\n                            n.backward(params,loss,arm); torch.cuda.synchronize()\n                        dispatch=sorted({x.name for x in profiler.events() if 'scaled_dot_product' in x.name}) if rep==1 and path=='full' else []")
new=new.replace('rank_linear_extra_calls=4)', 'rank_linear_extra_calls=4,dispatched_ATen_names=dispatch)')
new=new.replace('    assert n.frozen_digest(model.flow_model)==frozen and modes==', '    assert backend_flags()==incoming\n    assert n.frozen_digest(model.flow_model)==frozen and modes==')
new=new.replace("mode_inventory_sha256=sha(BASE/'mode_inventory.json'),mode_validation_sha256=sha(BASE/'mode_validation.json')", "mode_inventory_sha256=sha(PRIOR/'mode_inventory.json'),mode_validation_sha256=sha(PRIOR/'mode_validation.json'),backend_flags_before=incoming,backend_flags_after=backend_flags(),backend_flags_restored=True")
new=new.replace("    save(BASE/'results.json',dict(utc=now(),pairs=compare", "    default_comparisons=[]\n    for name in read(BASE/'freeze.json')['sequence']:\n        details={}\n        for filename in ('output.npz','gradients.npz','hooks.npz'):\n            with np.load(folder/name/filename) as left,np.load(PRIOR/'traces'/name/filename) as right:\n                details[filename]={key:difference(left[key],right[key]) for key in left.files}\n        default_comparisons.append(dict(name=name,details=details))\n    save(BASE/'results.json',dict(utc=now(),default_control_comparisons=default_comparisons,pairs=compare")
new=new.replace("<=4*2**30 and max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=3*2**30", "<=6*2**30 and max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=6*2**30")
new=new.replace("for folder in (SUP,PREVIOUS/'supervision') for p", "for folder in (SUP,) for p")
new=new.replace("import numpy as np; import validate_native_backward as v; v.validate()", "import numpy as np; import validate_native_math as v; v.validate()")
new=new.replace("elif stage=='diagnose': diagnose()", "elif stage=='diagnose': diagnose()\n        elif stage=='directions': directions()")
new=new.replace("NBR0 combined child cap", "NMR0 combined child cap")
# The legacy CPU equation validator deliberately remains immutable and is routed by its canonical import.
insert=new.index('\ndef usage():')
new=new[:insert]+'''
def directions():
    global torch,np
    verify(); check_seal(BASE/'traces','trace_seal.json'); assert read(BASE/'results.json')['all_instrumented_pairs_byte_equal']
    import numpy as np;import torch;import native_conditioned_comparison as n
    from rap_slam.rap_precision import ieee_matmul
    from torch.nn.attention import sdpa_kernel,SDPBackend
    model,params,initial,audit=n.model(); assert mode_contract(model.flow_model)==read(PRIOR/'mode_inventory.json')['inventory']
    frozen=n.frozen_digest(model.flow_model); modes={k:v.training for k,v in model.flow_model.named_modules()}; incoming=backend_flags()
    z=n.load(OLD/'bank/synthetic_fixture.npz');noise=torch.tensor(n.load(OLD/'bank/noise/fit_00.npz')['noise'],device='cuda');batch=n.n.noc.batch({k:z[k] for k in n.n.OBS});kw=n.args(batch,noise,1.)
    folder=BASE/'directions';folder.mkdir();rng=np.random.default_rng(9417);vectors={}
    for group in ('final_mlp','LoRA_B'):
        vector={k:np.zeros_like(v) for k,v in initial.items()}
        for key,value in vector.items():
            if (group=='final_mlp' and key.startswith('final_mlp.')) or (group=='LoRA_B' and key.endswith('.B')):
                value[:]=rng.choice([-1.,1.],size=value.shape)
        norm=np.sqrt(sum(float(np.sum(v.astype(float)**2)) for v in vector.values()));assert norm>0
        vectors[group]={k:(v/norm).astype(v.dtype) for k,v in vector.items()};np.savez(folder/f'{group}.npz',**vectors[group])
    records=[]
    with ieee_matmul(),sdpa_kernel(SDPBackend.MATH),torch.no_grad():
        for arm in ('V','P'):
            gradients=n.load(BASE/f'traces/{arm}_full1/gradients.npz')
            for group,vector in vectors.items():
                analytic=sum(float(np.sum(gradients[k].astype(float)*v.astype(float))) for k,v in vector.items())
                for step in (1e-3,3e-4,1e-4):
                    for sign in (-1,1):
                        name=f'{arm}_{group}_{step:g}_{sign:+d}'
                        proposed={k:(v+sign*step*vector[k]).astype(v.dtype) for k,v in initial.items()};n.assign(params,proposed)
                        assert all(np.array_equal(p.detach().cpu().numpy(),proposed[k]) for k,p in params.items())
                        with torch.autocast('cuda',dtype=torch.float16): velocity=model.flow_model(**kw)
                        loss,terms=n.loss_value(z,noise,velocity,arm);torch.cuda.synchronize();assert torch.isfinite(loss)
                        np.savez(folder/f'{name}.npz',output=(noise-velocity).cpu().numpy(),velocity=velocity.cpu().numpy())
                        np.savez(folder/f'{name}_parameters.npz',**proposed)
                        records.append(dict(name=name,arm=arm,group=group,step=step,sign=sign,loss=float(loss),analytic=analytic,parameter_perturbations_only=True))
                        n.assign(params,initial);assert all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items())
                        del velocity,loss,proposed;cap();print('fixed directional forward',name,flush=True)
    assert backend_flags()==incoming and n.frozen_digest(model.flow_model)==frozen and modes=={k:v.training for k,v in model.flow_model.named_modules()}
    assert all(p.grad is None for p in params.values())
    save(folder/'execution.json',dict(utc=now(),records=records,native_forwards=24,backwards=0,optimizer_calls=0,retained_updates=0,initial_parameters_restored_byteexact=True,backend_flags_restored=True))
    seal(folder,'direction_seal.json')
''' +new[insert:]
target=ROOT/'scripts/maintenance/native_math_reproducibility.py';ast.parse(new);target.write_text(new,encoding='utf-8',newline='\n')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(BASE/'SOURCE_DIFF.json').write_text(json.dumps(dict(original_path=str(source),original_sha256=digest(source),new_path=str(target),new_sha256=digest(target),diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=source.name,tofile=target.name))),indent=2)+'\n',encoding='utf-8')
print('Prepared new NMR0 source only; no numerical execution')
