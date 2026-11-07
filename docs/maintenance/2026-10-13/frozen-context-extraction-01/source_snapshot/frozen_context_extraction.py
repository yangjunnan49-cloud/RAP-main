"""FCE0 fixed RAP pointwise/joint/separated context feature bindings, zero fitting."""
import importlib.metadata,resource,signal,sys,time,traceback
from pathlib import Path
import shadow_prefix_storage_codec as s
ROOT=s.ROOT;OLD=s.OLD;SOURCE=ROOT/'docs/maintenance/2026-10-13/shadow-sampler-extraction-01'
BASE=ROOT/'docs/maintenance/2026-10-13/frozen-context-extraction-01';SUP=BASE/'supervision';START=None;torch=None
read,save,sha,digest=s.read,s.save,s.sha,s.digest
def freeze():
    f=read(OLD/'freeze.json');files=dict(f['files']);assert read(SOURCE/'validation.json')['extraction_and_sampler_conjunction']
    paths=[Path(__file__),Path(__file__).with_name('validate_frozen_context.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md']+[ROOT/'rectified_point_flow'/q for q in ('flow_model/layer.py','flow_model/norm.py','flow_model/point_cloud_dit.py','flow_model/embedding.py','utils/point_clouds.py')]
    snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        files[str(q)]=sha(q)
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    for q,h in files.items():assert sha(q)==h,q
    assert s.repositories()==f['repositories']
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],noise_names=['fit_00','eval_00'],tau=1,layouts=['J_joint','I_separated'],cap_seconds=900,cap_RSS_bytes=6*2**30,cap_GPU_bytes=6*2**30,cap_artifact_bytes=256*2**20,no_training_GT_or_sampler=True))
    (BASE/'INCOMPLETE').write_text('FCE0 frozen-context source extraction and isolation prerequisites pending.\n');print('FCE0 frozen',len(files),'identities',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for q,h in f['files'].items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')}
    assert (OLD/'INCOMPLETE').exists() and not (OLD/'prediction_seal.json').exists()
def extract():
    global torch
    verify()
    import torch,numpy as np
    import native_conditioned_comparison as n
    import native_precision_control as p
    model,params,initial,audit=n.model();flow=model.flow_model
    assert sum(v.size for v in initial.values())==443904
    original_initial=n.load(n.c.MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/preflight/P/initial.npz')
    assert initial.keys()==original_initial.keys() and all(np.array_equal(v,original_initial[k]) for k,v in initial.items())
    expected=read(ROOT/'docs/maintenance/2026-10-13/native-backward-reproducibility-02/mode_inventory.json')['inventory']
    import native_math_reproducibility as mr
    mr.torch=torch;mr.BASE=BASE
    assert mr.mode_contract(flow)==expected
    p.torch=torch;frozen=n.frozen_digest(flow);modes={k:v.training for k,v in flow.named_modules()}
    source=n.c.MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/bank'
    with np.load(source/'synthetic_fixture.npz',allow_pickle=False) as z:observations={k:z[k].copy() for k in n.n.OBS}
    assert set(observations)=={'points','features','cond','scale','centers','counts'}
    batch=n.n.noc.batch(observations);folder=BASE/'features';folder.mkdir();np.savez(folder/'observations.npz',**observations);records=[];helper_calls=full_calls=0
    def run(kw,full=False):
        captured={}
        def first(mod,args):captured['D_pointwise']=args[0].detach().cpu().numpy().copy()
        def tenth(mod,args,out):captured['prefix']=out.detach().cpu().numpy().copy()
        handles=[flow.transformer_layers[0].register_forward_pre_hook(first)]
        if full:handles.append(flow.transformer_layers[9].register_forward_hook(tenth))
        try:
            with torch.no_grad(),p.precision(flow):
                value=flow(**kw) if full else n.prefix(flow,kw)
                torch.cuda.synchronize()
            if full:captured['velocity']=value.cpu().numpy().copy()
            else:captured['prefix']=value.cpu().numpy().copy()
            assert set(captured)==({'D_pointwise','prefix','velocity'} if full else {'D_pointwise','prefix'})
            assert all(v.dtype==np.float32 and np.isfinite(v).all() for v in captured.values())
            return captured
        finally:
            for h in handles:h.remove()
    for noise_name in ('fit_00','eval_00'):
        noise=n.load(source/f'noise/{noise_name}.npz')['noise'];x=torch.tensor(noise,device='cuda');base=n.args(batch,x,1.)
        for layout in ('J_joint','I_separated'):
            kw=dict(base)
            if layout=='I_separated':kw.update(cu_seqlens_batch=base['cu_seqlens_part'].clone(),timesteps=base['timesteps'].repeat(3),scales=base['scales'].repeat(3))
            dest=folder/f'{noise_name}_{layout}';dest.mkdir()
            np.savez(dest/'inputs.npz',**{k:v.detach().cpu().numpy().copy() for k,v in kw.items() if isinstance(v,torch.Tensor)})
            for rep in (1,2):
                value=run(kw);helper_calls+=1;np.savez(dest/f'helper{rep}.npz',**value);cap()
            value=run(kw,full=True);full_calls+=1;np.savez(dest/'hook.npz',**value);cap()
            changed=dict(kw);changed['x']=kw['x'].clone();changed['x'][1000:]+=torch.tensor([.125,-.0625,.03125],device='cuda')
            value=run(changed);helper_calls+=1;np.savez(dest/'perturbed.npz',**value);np.savez(dest/'perturbed_input.npz',x=changed['x'].cpu().numpy());cap()
            records.append(dict(noise=noise_name,layout=layout,perturbation='only_nonanchor_x_add_[.125,-.0625,.03125]',tau=1.,prefix_layers=10));print('FCE0 fixed context extracted',noise_name,layout,flush=True)
    assert helper_calls==12 and full_calls==4
    assert n.frozen_digest(flow)==frozen and mr.mode_contract(flow)==expected and modes=={k:v.training for k,v in flow.named_modules()}
    assert all(v.dtype==torch.float32 and v.grad is None and np.array_equal(v.detach().cpu().numpy(),initial[k]) for k,v in params.items())
    save(folder/'execution.json',dict(records=records,strict_checkpoint=audit,prefix_helper_calls=helper_calls,full_FP32_flow_forwards=full_calls,native_backwards=0,head_backwards=0,optimizer_calls=0,retained_updates=0,source_sampler_calls=0,truth_target_arrays_loaded=False,model_values_modes_attention_flags_hooks_restored=True,original_initialized_trainables=443904,parameter_updates=0,original_native_FP16_equivalence=False,fixture_independent_scenes=1))
    save(BASE/'feature_seal.json',dict(files={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()},freeze_sha256=sha(BASE/'freeze.json')));verify()
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),imports_included=True,optimizer_calls=0)
def cap():
    u=usage();assert u['peak_RSS_bytes']<=6*2**30 and max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=6*2**30 and u['artifact_bytes']<=256*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('FCE0 aggregate child time cap')));signal.alarm(max(1,int(900-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='extract':extract()
        elif stage=='validate':
            import validate_frozen_context as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['frozen_context_extraction']=sys.modules[__name__];run(sys.argv[1])
