"""HFIT0 isolated retained-update shadow feasibility, explicit two-instance lifecycle."""
import importlib.metadata,resource,signal,sys,time,traceback
from pathlib import Path
import native_double_tail as r
import native_precision_control as p
MAIN=r.MAIN;PRIOR=MAIN/'docs/maintenance/2026-10-13/shadow-sampler-extraction-01';BASE=MAIN/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01';SUP=BASE/'supervision'
r.BASE=BASE;r.SUP=SUP
read,save,sha,now=r.read,r.save,r.sha,r.now
torch=None;START=None
def freeze():
    assert read(PRIOR/'validation.json')['extraction_and_sampler_conjunction'];f=read(PRIOR/'freeze.json');files=dict(f['files']);seal=read(PRIOR/'DELIVERY_SEAL.json');assert len(seal['files'])==97
    for x in seal['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in q.parents and sha(q)==x['sha256'];files[str(q)]=x['sha256']
    paths=[BASE/name for name in ('OWNER_SCOPE.md','PROTOCOL.md','METRIC_GATE.json')]+[Path(__file__),Path(__file__).with_name('validate_shadow_fit.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PRIOR/'DELIVERY_SEAL.json']
    for q in paths:files[str(q)]=sha(q)
    for q,h in files.items():assert sha(q)==h,q
    assert r.r.repos()==f['repositories'];snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],cap_seconds=1800,cap_RSS_bytes=6*2**30,cap_GPU_bytes=8*2**30,cap_artifact_bytes=2*2**30,updates_per_arm=20,fit_noise='fit_00',eval_noises=[f'eval_{i:02d}' for i in range(16)],gate=read(BASE/'METRIC_GATE.json')['gate'],optimizer_API_calls=0))
    (BASE/'INCOMPLETE').write_text('HFIT0 two-instance preflight,40 retained updates and paired sampling/independent audit pending.\n');print('HFIT0 frozen',len(files),'identities',flush=True)
def verify():r.verify()
def setup(targets=False):
    global torch,np
    import torch;import numpy as np;import native_conditioned_comparison as n
    r.torch=p.torch=r.r.torch=torch;r.r.BASE=BASE
    prefix,pparams,pinitial,paudit=n.model();tail,params,initial,audit=n.model()
    assert all(np.array_equal(v,pinitial[k]) for k,v in initial.items()) and sum(v.size for v in initial.values())==443904
    reference=n.load(r.r.OLD/'preflight/P/initial.npz');assert all(np.array_equal(v,reference[k]) for k,v in initial.items())
    expected=read(r.r.PRIOR/'mode_inventory.json')['inventory'];assert r.r.mode_contract(prefix.flow_model)==r.r.mode_contract(tail.flow_model)==expected
    assert all(pparams[k] is not v and pparams[k].data_ptr()!=v.data_ptr() for k,v in params.items());prefix.requires_grad_(False)
    with np.load(r.r.OLD/'bank/synthetic_fixture.npz',allow_pickle=False) as source:z={k:source[k].copy() for k in source.files if targets or k in n.n.OBS}
    observations={k:z[k] for k in n.n.OBS};batch=n.n.noc.batch(observations);assert 'truth' not in batch and 'target' not in batch and batch['pointclouds_gt'] is batch['pointclouds']
    frozen=n.frozen_digest(prefix.flow_model);return n,prefix,tail,params,initial,audit,paudit,z,batch,frozen
def extracted(n,prefix,batch,state,tau):
    kw=n.args(batch,state.float(),tau)
    with torch.no_grad(),p.precision(prefix.flow_model):embedding=n.prefix(prefix.flow_model,kw)
    assert embedding.dtype==kw['x'].dtype==kw['timesteps'].dtype==torch.float32;return embedding.double(),kw
def rollout(n,prefix,tail,batch,noise_name,dest):
    import rectified_point_flow.sampler as sm
    noise=torch.tensor(n.load(r.r.OLD/f'bank/noise/{noise_name}.npz')['noise'],device='cuda',dtype=torch.float64);steps=[];rigids=[];original=sm.rigidify_prediction_with_procrustes
    def capture_rigid(prediction,condition,points,seq):
        output=original(prediction,condition,points,seq);rigids.append(output.cpu().numpy().copy());return output
    def callback(state,tau):
        embedding,kw=extracted(n,prefix,batch,state,tau);velocity=r.tail64(tail.flow_model,embedding,kw);assert velocity.dtype==state.dtype==torch.float64
        steps.append(dict(state=state.cpu().numpy().copy(),prefix_input=kw['x'].cpu().numpy().copy(),prefix=embedding.float().cpu().numpy().copy(),timestep=kw['timesteps'].cpu().numpy().copy(),velocity=velocity.cpu().numpy().copy(),tau=tau));return velocity
    with torch.no_grad():
        sm.rigidify_prediction_with_procrustes=capture_rigid
        try:result=sm.flow_sampler(sm.euler_step,callback,noise,batch['pointclouds'].double(),batch['anchor_indices'],num_steps=5,points_per_part=batch['points_per_part'],cu_seqlens_batch=batch['cu_seqlens'],condition=batch['pointclouds'].double(),return_trajectory=True,rigidity_forcing=True,return_end_point_trajectory=True)
        finally:sm.rigidify_prediction_with_procrustes=original
    assert len(steps)==len(rigids)==5;dest.mkdir()
    for i,(s,rigid) in enumerate(zip(steps,rigids)):
        np.savez_compressed(dest/f'step_{i}.npz',state=s['state'],prefix_input=s['prefix_input'],prefix=s['prefix'],timestep=s['timestep'],velocity=s['velocity'],rigid=rigid)
    np.savez(dest/'source_trajectory.npz',**{k:v.cpu().numpy().copy() for k,v in result.items()});save(dest/'trace.json',dict(noise=noise_name,taus=[s['tau'] for s in steps],two_instances=True,source_buffers='float32',carried_state='float64'));cap()
def preflight():
    verify();n,prefix,tail,params,initial,audit,paudit,z,batch,frozen=setup();folder=BASE/'preflight';folder.mkdir();initial64={k:v.astype(float) for k,v in initial.items()}
    with r.double_tail(tail.flow_model,params,n):
        for name in ('fit_00','eval_00'):
            rollout(n,prefix,tail,batch,name,folder/name)
            for file in ['source_trajectory.npz']+[f'step_{i}.npz' for i in range(5)]:
                a=n.load(folder/name/file);b=n.load(PRIOR/f'bank/{name}_helper1'/file);assert set(a)==set(b) and all(np.array_equal(v,b[k]) for k,v in a.items())
        n.assign(params,initial64)
    assert n.frozen_digest(prefix.flow_model)==frozen and all(np.array_equal(v.detach().cpu().numpy(),initial[k]) for k,v in params.items())
    save(folder/'execution.json',dict(two_instance_initial_sampler_byteexact=True,strict_tail=audit,strict_prefix=paudit,shadow_tail_forwards=10,prefix_calls=10,backwards=0,actual_retained_updates=0,optimizer_API_calls=0));r.seal(folder,'preflight_seal.json')
def fit():
    verify();r.check_seal(BASE/'preflight','preflight_seal.json');assert read(BASE/'preflight/execution.json')['two_instance_initial_sampler_byteexact']
    n,prefix,tail,params,initial,audit,paudit,z,batch,frozen=setup(True);folder=BASE/'fits';folder.mkdir();initial64={k:v.astype(float) for k,v in initial.items()};noise=torch.tensor(n.load(r.r.OLD/'bank/noise/fit_00.npz')['noise'],device='cuda',dtype=torch.float64)
    embedding,kw=extracted(n,prefix,batch,noise,1.);records=[]
    with r.double_tail(tail.flow_model,params,n):
        for arm in ('V','P'):
            n.assign(params,initial64);armfolder=folder/arm;armfolder.mkdir()
            for step in range(1,21):
                dest=armfolder/f'step_{step:02d}';dest.mkdir();before=n.n.noc.numpy_state(params)
                for value in params.values():value.grad=None
                captured={};handles=[]
                if step in (1,20):
                    def hook(key):
                        def apply(module,args,out):
                            captured[key+'|input']=args[0].detach().cpu().numpy().copy()
                            with torch.no_grad():captured[key+'|rank']=torch.nn.functional.linear(args[0],module.A).cpu().numpy().copy()
                            out.register_hook(lambda g:captured.__setitem__(key+'|scaled_gradient',g.detach().cpu().numpy().copy()))
                        return apply
                    for key,module in tail.flow_model.named_modules():
                        if key in {f'transformer_layers.{i}.{a}' for i in (10,11) for a in ('global_qkv_proj','global_out_proj')}:handles.append(module.register_forward_hook(hook(key)))
                try:
                    velocity=r.tail64(tail.flow_model,embedding,kw);velocity.retain_grad();loss,q=r.loss_value(z,noise,velocity,arm,n);n.backward(params,loss,arm);torch.cuda.synchronize()
                finally:
                    for handle in handles:handle.remove()
                gradients={key:value.grad.detach().cpu().numpy().copy() for key,value in params.items()};assert all(np.isfinite(g).all() for g in gradients.values())
                with torch.no_grad():
                    if arm=='P':_,terms_before=n.old.obj(z,q)
                    else:terms_before=dict(velocity=loss.detach())
                terms_before={k:float(v) for k,v in terms_before.items()}
                L=float(loss);norm=np.sqrt(sum(float(np.sum(g*g)) for g in gradients.values()));assert np.isfinite(L) and L>0 and np.isfinite(norm) and norm>0
                if step==1:
                    old=n.load(r.MAIN/f'docs/maintenance/2026-10-13/native-double-tail-control-01/traces/{arm}1/gradients.npz');assert all(np.array_equal(g,old[k]) for k,g in gradients.items())
                radius=min(.001,.001*L/norm);after={k:v-radius*gradients[k]/norm for k,v in before.items()};actual={k:after[k]-v for k,v in before.items()};dot=sum(float(np.sum(gradients[k]*d)) for k,d in actual.items());length=np.sqrt(sum(float(np.sum(d*d)) for d in actual.values()));assert dot<0 and length<=radius*(1+1e-10)
                np.savez(dest/'before.npz',**before);np.savez(dest/'gradients.npz',**gradients);np.savez(dest/'output_before.npz',velocity=velocity.detach().cpu().numpy(),output=q.detach().cpu().numpy(),upstream=-velocity.grad.detach().cpu().numpy()/n.SETTINGS['backward_multipliers'][arm])
                if captured:assert len(captured)==12;np.savez_compressed(dest/'hooks.npz',**captured)
                n.assign(params,after)
                with torch.no_grad():
                    post_velocity=r.tail64(tail.flow_model,embedding,kw);post_loss,post_q=r.loss_value(z,noise,post_velocity,arm,n)
                    if arm=='P':_,terms_after=n.old.obj(z,post_q)
                    else:terms_after=dict(velocity=post_loss)
                terms_after={k:float(v) for k,v in terms_after.items()}
                torch.cuda.synchronize();np.savez(dest/'after.npz',**n.n.noc.numpy_state(params));np.savez(dest/'output_after.npz',velocity=post_velocity.cpu().numpy(),output=post_q.cpu().numpy())
                activity={group:dict(nonzero=sum(int(np.count_nonzero(g)) for k,g in gradients.items() if (k.endswith('.'+group) if group in ('A','B') else k.startswith('final_mlp.'))),norm=np.sqrt(sum(float(np.sum(g*g)) for k,g in gradients.items() if (k.endswith('.'+group) if group in ('A','B') else k.startswith('final_mlp.'))))) for group in ('A','B','MLP')}
                row=dict(arm=arm,step=step,loss_before=L,loss_after=float(post_loss),terms_before=terms_before,terms_after=terms_after,gradient_norm=float(norm),radius=float(radius),actual_dot=dot,actual_parameter_norm=float(length),activity=activity,actual_retained_update=True,optimizer_API_calls=0,Armijo_pass=bool(float(post_loss)<=L+.5*dot));save(dest/'update.json',row);records.append(row)
                assert torch.isfinite(post_loss) and row['Armijo_pass'];assert all(np.array_equal(value.detach().cpu().numpy(),after[k]) for k,value in params.items())
                del velocity,loss,q,post_velocity,post_loss,post_q,before,after,actual,gradients,captured;cap();print('retained shadow update',arm,step,'loss',row['loss_after'],flush=True)
            np.savez(armfolder/'parameters_20.npz',**n.n.noc.numpy_state(params))
        for value in params.values():value.grad=None
        n.assign(params,initial64)
    assert n.frozen_digest(prefix.flow_model)==frozen and all(np.array_equal(value.detach().cpu().numpy(),initial[k]) for k,value in params.items())
    save(folder/'execution.json',dict(records=records,actual_retained_updates=40,optimizer_API_calls=0,prefix_calls=1,shadow_tail_forwards=80,backwards=40,double_artifact_states_preserved=True,original_live_values_dtypes_restored=True));r.seal(folder,'fit_seal.json')
def predict():
    verify();r.check_seal(BASE/'fits','fit_seal.json');assert read(BASE/'fit_validation.json')['fit_conjunction']
    n,prefix,tail,params,initial,audit,paudit,z,batch,frozen=setup();folder=BASE/'predictions';folder.mkdir();records=[];initial64={k:v.astype(float) for k,v in initial.items()}
    with r.double_tail(tail.flow_model,params,n):
        for arm in ('U','V','P'):
            state=initial64 if arm=='U' else n.load(BASE/f'fits/{arm}/parameters_20.npz');n.assign(params,state)
            for name in ['fit_00']+[f'eval_{i:02d}' for i in range(16)]:
                rollout(n,prefix,tail,batch,name,folder/f'{arm}_{name}');assert all(np.array_equal(value.detach().cpu().numpy(),state[k]) for k,value in params.items())
                records.append(dict(arm=arm,noise=name,role='fit_diagnostic' if name=='fit_00' else 'old_eval'));print('paired shadow prediction',arm,name,flush=True)
            for value in params.values():value.grad=None
        n.assign(params,initial64)
    assert n.frozen_digest(prefix.flow_model)==frozen and all(np.array_equal(value.detach().cpu().numpy(),initial[k]) for k,value in params.items())
    save(folder/'execution.json',dict(records=records,complete_source_sampler_traces=51,shadow_tail_forwards=255,prefix_calls=255,backwards=0,optimizer_API_calls=0,retained_updates=0,no_truth_target_arrays_loaded=True,all_live_values_restored=True));r.seal(folder,'prediction_seal.json')
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),optimizer_calls=0,imports_included=True)
def cap():
    z=usage();assert z['peak_RSS_bytes']<=6*2**30 and max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=8*2**30 and z['artifact_bytes']<=2*2**30,z
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<1800
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('HFIT0 combined cap')));signal.alarm(max(1,int(1800-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='preflight':preflight()
        elif stage=='fit':fit()
        elif stage=='predict':predict()
        elif stage in ('validate_fit','evaluate'):
            import validate_shadow_fit as v;v.validate(stage)
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['shadow_conditioned_fit']=sys.modules[__name__];run(sys.argv[1])
