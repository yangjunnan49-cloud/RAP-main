"""SAR0 target-free source sampler / prefix extraction precision binding."""
import resource,signal,sys,time,traceback
from pathlib import Path
import native_double_tail as r
import native_precision_control as p
MAIN=r.MAIN;PRIOR=MAIN/'docs/maintenance/2026-10-13/activated-adapter-derivatives-01';BASE=MAIN/'docs/maintenance/2026-10-13/shadow-sampler-extraction-01';SUP=BASE/'supervision'
r.BASE=BASE;r.SUP=SUP
read,save,sha,now=r.read,r.save,r.sha,r.now
torch=None;START=None
def freeze():
    assert read(PRIOR/'validation.json')['all_directions_corroborated'];f=read(PRIOR/'freeze.json');files=dict(f['files']);seal=read(PRIOR/'DELIVERY_SEAL.json');assert len(seal['files'])==149
    for x in seal['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in q.parents and sha(q)==x['sha256'];files[str(q)]=x['sha256']
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_shadow_sampler.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PRIOR/'DELIVERY_SEAL.json',MAIN/'rectified_point_flow/sampler.py',MAIN/'rectified_point_flow/procrustes.py',MAIN/'rectified_point_flow/modeling.py']
    for q in paths:files[str(q)]=sha(q)
    for q,h in files.items():assert sha(q)==h,q
    assert r.r.repos()==f['repositories'];snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],cap_seconds=900,cap_RSS_bytes=6*2**30,cap_GPU_bytes=8*2**30,cap_artifact_bytes=512*2**20,
        noises=['fit_00','eval_00'],methods=['helper','hook'],repetitions=2,num_steps=5,rigidity_forcing=True,optimizer_calls=0))
    (BASE/'INCOMPLETE').write_text('SAR0 complete source-sampler traces and independent extraction/rigidity audit pending.\n');print('SAR0 frozen',len(files),'identities',flush=True)
def bank():
    global torch,np
    r.verify();import torch;import numpy as np;import native_conditioned_comparison as n
    import rectified_point_flow.sampler as sm
    r.torch=p.torch=r.r.torch=torch;r.r.BASE=BASE;model,params,initial,audit=n.model()
    assert r.r.mode_contract(model.flow_model)==read(r.r.PRIOR/'mode_inventory.json')['inventory']
    old=n.load(r.r.OLD/'preflight/P/initial.npz');assert all(np.array_equal(v,old[k]) for k,v in initial.items()) and sum(v.size for v in initial.values())==443904
    assert model.inference_sampling_steps==5 and model.inference_sampler=='euler' and model.rigidity_forcing is True
    with np.load(r.r.OLD/'bank/synthetic_fixture.npz',allow_pickle=False) as z:observations={k:z[k].copy() for k in n.n.OBS}
    assert set(observations)=={'points','features','cond','scale','centers','counts'};batch=n.n.noc.batch(observations);assert 'truth' not in batch and 'target' not in batch and batch['pointclouds_gt'] is batch['pointclouds']
    folder=BASE/'bank';folder.mkdir();np.savez(folder/'observations.npz',**observations);records=[];frozen=n.frozen_digest(model.flow_model);modes={k:v.training for k,v in model.flow_model.named_modules()};counts=dict(helper_prefix_calls=0,full_FP32_forward_calls=0,double_tail_calls=0,time_constant_promotions=0)
    original_rigid=sm.rigidify_prediction_with_procrustes
    with torch.no_grad():
        for noise_name in ('fit_00','eval_00'):
            noise_arr=n.load(r.r.OLD/f'bank/noise/{noise_name}.npz')['noise'];assert noise_arr.dtype==np.float32;noise=torch.tensor(noise_arr,device='cuda',dtype=torch.float64)
            for method in ('helper','hook'):
                for rep in (1,2):
                    name=f'{noise_name}_{method}{rep}';dest=folder/name;dest.mkdir();n.assign(params,initial);steps=[];rigid_records=[]
                    def rigid_wrapper(prediction,condition,points_per_part,cu_seqlens_batch):
                        assert prediction.dtype==condition.dtype==torch.float64
                        result=original_rigid(prediction,condition,points_per_part,cu_seqlens_batch)
                        rigid_records.append(result.detach().cpu().numpy().copy());return result
                    def callback(state,tau):
                        assert state.dtype==torch.float64 and len(steps)<5
                        kw=n.args(batch,state.float(),tau);assert kw['x'].dtype==kw['timesteps'].dtype==torch.float32
                        extracted=[]
                        with p.precision(model.flow_model):
                            if method=='helper':embedding=n.prefix(model.flow_model,kw);counts['helper_prefix_calls']+=1
                            else:
                                handle=model.flow_model.transformer_layers[9].register_forward_hook(lambda m,a,out:extracted.append(out.detach().clone()))
                                try:full=model.flow_model(**kw)
                                finally:handle.remove()
                                assert len(extracted)==1 and full.dtype==torch.float32;embedding=extracted[0];counts['full_FP32_forward_calls']+=1;del full
                        assert embedding.dtype==torch.float32
                        if noise_name=='fit_00' and len(steps)==0:
                            assert np.array_equal(embedding.cpu().numpy(),np.load(r.PRIOR/'traces/D_V_prefix.npy'))
                        with r.double_tail(model.flow_model,params,n) as timecalls:velocity=r.tail64(model.flow_model,embedding.double(),kw)
                        assert velocity.dtype==torch.float64 and len(timecalls)==4;counts['double_tail_calls']+=1;counts['time_constant_promotions']+=len(timecalls)
                        steps.append(dict(index=len(steps),tau=tau,state=state.detach().cpu().numpy().copy(),prefix_input=kw['x'].cpu().numpy().copy(),prefix=embedding.cpu().numpy().copy(),timestep=kw['timesteps'].cpu().numpy().copy(),velocity=velocity.cpu().numpy().copy()))
                        assert all(np.array_equal(v.detach().cpu().numpy(),initial[k]) for k,v in params.items());cap();return velocity
                    sm.rigidify_prediction_with_procrustes=rigid_wrapper
                    try:result=sm.flow_sampler(sm.euler_step,callback,noise,batch['pointclouds'].double(),batch['anchor_indices'],num_steps=5,points_per_part=batch['points_per_part'],cu_seqlens_batch=batch['cu_seqlens'],condition=batch['pointclouds'].double(),return_trajectory=True,rigidity_forcing=True,return_end_point_trajectory=model.return_end_point_trajectory)
                    finally:sm.rigidify_prediction_with_procrustes=original_rigid
                    assert len(steps)==len(rigid_records)==5 and all(v.dtype==torch.float32 for v in result.values())
                    for step,rigid in zip(steps,rigid_records):
                        i=step['index'];np.savez_compressed(dest/f'step_{i}.npz',state=step['state'],prefix_input=step['prefix_input'],prefix=step['prefix'],timestep=step['timestep'],velocity=step['velocity'],rigid=rigid)
                    np.savez(dest/'source_trajectory.npz',**{k:v.cpu().numpy().copy() for k,v in result.items()});save(dest/'trace.json',dict(name=name,noise=noise_name,method=method,rep=rep,taus=[x['tau'] for x in steps],dt=.2,source_return_buffers='float32',carried_state='float64',prefix_state_and_model='float32',tail_and_rigidity='float64'))
                    records.append(dict(name=name,noise=noise_name,method=method,rep=rep));torch.cuda.synchronize();cap();print('source shadow sampler',name,'5steps',flush=True)
    assert sm.rigidify_prediction_with_procrustes is original_rigid and n.frozen_digest(model.flow_model)==frozen and modes=={k:v.training for k,v in model.flow_model.named_modules()}
    assert all(np.array_equal(v.detach().cpu().numpy(),initial[k]) and v.grad is None for k,v in params.items())
    save(folder/'execution.json',dict(records=records,counts=counts,strict_checkpoint=audit,nominal_trainables=443904,checkpoint_source_model=dict(steps=model.inference_sampling_steps,sampler=model.inference_sampler,rigidity_forcing=model.rigidity_forcing),observation_fields=list(observations),no_truth_target_arrays_loaded=True,no_losses_or_metrics=True,backwards=0,optimizer_calls=0,retained_updates=0,source_sampler_and_flags_and_values_restored=True,original_native_equivalence=False))
    r.seal(folder,'bank_seal.json');r.verify()
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),optimizer_calls=0,imports_included=True)
def cap():
    z=usage();assert z['peak_RSS_bytes']<=6*2**30 and max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=8*2**30 and z['artifact_bytes']<=512*2**20,z
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('SAR0 combined cap')));signal.alarm(max(1,int(900-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='bank':bank()
        elif stage=='validate':
            import validate_shadow_sampler as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['shadow_sampler_extraction']=sys.modules[__name__];run(sys.argv[1])
