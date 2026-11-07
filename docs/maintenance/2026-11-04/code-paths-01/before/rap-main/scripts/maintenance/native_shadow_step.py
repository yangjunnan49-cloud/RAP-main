"""SFC0 restored symmetric first-order functional probes; no optimizer API."""
import importlib.metadata,resource,signal,sys,time,traceback
from pathlib import Path
import native_double_tail as r
PRIOR=r.BASE;BASE=r.MAIN/'docs/maintenance/2026-10-13/native-shadow-step-control-01';SUP=BASE/'supervision'
r.BASE=BASE;r.SUP=SUP
read,save,sha,now=r.read,r.save,r.sha,r.now
torch=None;START=None
def freeze():
    v=read(PRIOR/'validation.json');assert v['passed'] and v['all_directions_corroborated'] and v['core']['all_pairs_byteexact']
    f=read(PRIOR/'freeze.json');files=dict(f['files']);seal=read(PRIOR/'DELIVERY_SEAL.json');assert len(seal['files'])==118
    for x in seal['files']:
        p=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in p.parents and sha(p)==x['sha256'];files[str(p)]=x['sha256']
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_native_shadow_step.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),PRIOR/'DELIVERY_SEAL.json']
    for p in paths:files[str(p)]=sha(p)
    for p,h in files.items():assert sha(p)==h,p
    assert r.r.repos()==f['repositories'];snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):(snap/p.name).write_bytes(p.read_bytes())
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],cap_seconds=600,cap_RSS_bytes=6*2**30,cap_GPU_bytes=8*2**30,cap_artifact_bytes=128*2**20,predicted_loss_fraction=.001,max_parameter_L2_radius=.001,Armijo_fraction=.5,optimizer_API_calls=0))
    (BASE/'INCOMPLETE').write_text('SFC0 symmetric restored functional probes and independent audit pending.\n');print('SFC0 frozen',len(files),'identities',flush=True)
def probe():
    global torch,np
    r.verify();n,model,params,initial,audit,z,noise,kw,embedding=r.model_data();torch=r.torch;np=r.np;folder=BASE/'bank';folder.mkdir();records=[];initial64={k:v.astype(float) for k,v in initial.items()}
    with r.double_tail(model.flow_model,params,n) as timecalls:
        for arm in ('V','P'):
            for rep in (1,2):
                name=f'{arm}{rep}';dest=folder/name;dest.mkdir();n.assign(params,initial64)
                for p in params.values():p.grad=None
                velocity=r.tail64(model.flow_model,embedding,kw);loss,q=r.loss_value(z,noise,velocity,arm,n);n.backward(params,loss,arm);torch.cuda.synchronize()
                gradients={k:p.grad.detach().cpu().numpy().copy() for k,p in params.items()};old=n.load(PRIOR/f'traces/{arm}1/gradients.npz');assert all(np.array_equal(gradients[k],old[k]) for k in old)
                L=float(loss);norm=np.sqrt(sum(float(np.sum(g*g)) for g in gradients.values()));assert norm>0 and L>0 and np.isfinite(norm)
                radius=min(.001,.001*L/norm);np.savez(dest/'gradients.npz',**gradients);np.savez(dest/'initial_output.npz',velocity=velocity.detach().cpu().numpy(),output=q.detach().cpu().numpy());deltas=[]
                del velocity,loss,q
                for sign in (-1,1):
                    proposed={k:v+sign*radius*gradients[k]/norm for k,v in initial64.items()};n.assign(params,proposed)
                    assert all(np.array_equal(p.detach().cpu().numpy(),proposed[k]) for k,p in params.items())
                    with torch.no_grad():velocity=r.tail64(model.flow_model,embedding,kw);loss,q=r.loss_value(z,noise,velocity,arm,n)
                    torch.cuda.synchronize();assert torch.isfinite(loss);np.savez(dest/f'parameters_{sign:+d}.npz',**proposed);np.savez(dest/f'output_{sign:+d}.npz',velocity=velocity.cpu().numpy(),output=q.cpu().numpy())
                    actual={k:proposed[k]-v for k,v in initial64.items()};dot=sum(float(np.sum(gradients[k]*d)) for k,d in actual.items());parameter_norm=np.sqrt(sum(float(np.sum(d*d)) for d in actual.values()))
                    deltas.append(dict(sign=sign,loss=float(loss),actual_gradient_dot=dot,actual_parameter_L2_norm=parameter_norm));n.assign(params,initial64);assert all(np.array_equal(p.detach().cpu().numpy(),initial64[k]) for k,p in params.items());del proposed,velocity,loss,q,actual
                with torch.no_grad():restored=r.tail64(model.flow_model,embedding,kw)
                old_velocity=n.load(dest/'initial_output.npz')['velocity'];assert np.array_equal(restored.cpu().numpy(),old_velocity);np.savez(dest/'restored_parameters.npz',**n.n.noc.numpy_state(params))
                row=dict(name=name,arm=arm,rep=rep,loss_before=L,gradient_L2_norm=norm,predetermined_radius=radius,steps=deltas,restored_output_byteexact=True,actual_transient_signed_parameter_steps=2,optimizer_API_calls=0,retained_updates=0)
                save(dest/'probe.json',row);records.append(row);del restored,gradients;cap();print('shadow symmetric step',name,'losses',[x['loss'] for x in deltas],flush=True)
        assert len(timecalls)==64
        for p in params.values():p.grad=None
    assert all(np.array_equal(p.detach().cpu().numpy(),initial[k]) for k,p in params.items())
    save(folder/'execution.json',dict(records=records,strict_checkpoint=audit,shadow_tail_forwards=16,backwards=4,whole_native_forwards=0,actual_transient_signed_parameter_steps=8,optimizer_API_calls=0,retained_updates=0,fit_iterations=0,parameters_dtype_flags_hooks_restored=True))
    r.seal(folder,'bank_seal.json');r.verify()
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0,peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch is not None and torch.cuda.is_initialized() else 0,artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),optimizer_API_calls=0,optimizer_calls=0,imports_included=True)
def cap():
    z=usage();assert z['peak_RSS_bytes']<=6*2**30 and max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=8*2**30 and z['artifact_bytes']<=128*2**20,z
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json'));assert used<600
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('SFC0 combined cap')));signal.alarm(max(1,int(600-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='probe':probe()
        elif stage=='validate':
            import validate_native_shadow_step as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['native_shadow_step']=sys.modules[__name__];run(sys.argv[1])
