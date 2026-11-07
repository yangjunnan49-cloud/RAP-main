"""SR1 bounded double-shadow adapter restart; old experiments remain read-only."""
import importlib.metadata,resource,signal,sys,time,traceback
from pathlib import Path
import shadow_conditioned_fit as impl

MAIN=impl.MAIN
PRIOR=impl.PRIOR
BASE=MAIN/'docs/maintenance/2026-10-25/shadow-adapter-restart-01'
SUP=BASE/'supervision'
r=impl.r
p=impl.p
read,save,sha,now=impl.read,impl.save,impl.sha,impl.now
torch=None
START=None
CAP_ARTIFACT=4*2**30

# The reused numerical functions retain their original globals; bind only this
# process's output paths and resource cap to the new prospective dossier.
impl.BASE=BASE
impl.SUP=SUP
r.BASE=BASE
r.SUP=SUP


def freeze():
    assert read(PRIOR/'validation.json')['extraction_and_sampler_conjunction']
    f=read(PRIOR/'freeze.json');files=dict(f['files'])
    seal=read(PRIOR/'DELIVERY_SEAL.json');assert len(seal['files'])==97
    for x in seal['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve()
        assert PRIOR.resolve() in q.parents and sha(q)==x['sha256']
        files[str(q)]=x['sha256']
    sources=[MAIN/'scripts/maintenance/shadow_conditioned_fit.py',
        MAIN/'scripts/maintenance/validate_shadow_fit.py',Path(__file__),
        Path(__file__).with_name('validate_shadow_adapter_restart.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',*sources,PRIOR/'DELIVERY_SEAL.json',
        MAIN/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/FAILURE_predict.json',
        MAIN/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/fit_validation.json',
        MAIN/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/fits/execution.json']
    for q in paths:files[str(q)]=sha(q)
    for q,h in files.items():assert sha(q)==h,q
    assert r.r.repos()==f['repositories']
    snap=BASE/'source_snapshot';snap.mkdir()
    for q in sources:
        (snap/q.name).write_bytes(q.read_bytes())
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=f['repositories'],
        packages=f['packages'],cap_seconds=1800,cap_RSS_bytes=6*2**30,
        cap_GPU_bytes=8*2**30,cap_artifact_bytes=CAP_ARTIFACT,updates_per_arm=20,
        fit_noise='fit_00',eval_noises=[f'eval_{i:02d}' for i in range(16)],
        gate=read(MAIN/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/METRIC_GATE.json')['gate'],
        optimizer_API_calls=0,old_HFIT0_cap_unchanged=True,old_partial_predictions_admitted=False))
    (BASE/'INCOMPLETE').write_text('SR1 model/backward/fit/complete-noise stages pending.\n')
    print('SR1 frozen',len(files),'identities',flush=True)


def verify():
    impl.verify()
    f=read(BASE/'freeze.json')
    assert f['cap_artifact_bytes']==CAP_ARTIFACT and f['old_HFIT0_cap_unchanged']
    assert (MAIN/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/INCOMPLETE').exists()


def usage():
    engine=impl.torch
    return dict(wall_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=engine.cuda.max_memory_allocated() if engine is not None and engine.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=engine.cuda.max_memory_reserved() if engine is not None and engine.cuda.is_initialized() else 0,
        artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),
        optimizer_calls=0,imports_included=True)


def cap():
    z=usage()
    assert z['peak_RSS_bytes']<=6*2**30,z
    assert max(z['peak_GPU_allocated_bytes'],z['peak_GPU_reserved_bytes'])<=8*2**30,z
    assert z['artifact_bytes']<=CAP_ARTIFACT,z
    if (SUP/'host_latest.json').exists():
        assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30


impl.cap=cap


def backward():
    global torch
    verify()
    n,prefix,tail,params,initial,audit,paudit,z,batch,frozen=impl.setup(True)
    torch=impl.torch
    import numpy as np
    folder=BASE/'backward';folder.mkdir()
    initial64={k:v.astype(np.float64) for k,v in initial.items()}
    noise=torch.tensor(n.load(r.r.OLD/'bank/noise/fit_00.npz')['noise'],device='cuda',dtype=torch.float64)
    embedding,kw=impl.extracted(n,prefix,batch,noise,1.)
    records=[]
    with r.double_tail(tail.flow_model,params,n):
        for arm in ('V','P'):
            n.assign(params,initial64)
            for value in params.values():value.grad=None
            velocity=r.tail64(tail.flow_model,embedding,kw)
            loss,q=r.loss_value(z,noise,velocity,arm,n)
            n.backward(params,loss,arm);torch.cuda.synchronize()
            gradients={k:v.grad.detach().cpu().numpy().copy() for k,v in params.items()}
            assert all(v.dtype==np.float64 and np.isfinite(v).all() for v in gradients.values())
            old=n.load(MAIN/f'docs/maintenance/2026-10-13/native-double-tail-control-01/traces/{arm}1/gradients.npz')
            assert all(np.array_equal(g,old[k]) for k,g in gradients.items())
            assert all(np.array_equal(v.detach().cpu().numpy(),initial64[k]) for k,v in params.items())
            norms={group:float(np.sqrt(sum(float(np.sum(g*g)) for k,g in gradients.items()
                if (k.endswith('.'+group) if group in ('A','B') else k.startswith('final_mlp.')))))
                for group in ('A','B','MLP')}
            assert norms['A']==0 and norms['B']>0 and norms['MLP']>0
            np.savez(folder/f'{arm}_gradients.npz',**gradients)
            row=dict(arm=arm,loss=float(loss),gradient_norms=norms,
                gradient_values=sum(v.size for v in gradients.values()),
                exact_DTC0_initial_gradient_replay=True,finite_float64=True,
                retained_updates=0,parameters_unchanged=True)
            records.append(row)
            print('SR1 backward',arm,'loss',row['loss'],'norms',norms,flush=True)
            del velocity,loss,q,gradients
        for value in params.values():value.grad=None
        n.assign(params,initial64)
    assert n.frozen_digest(prefix.flow_model)==frozen
    assert all(np.array_equal(v.detach().cpu().numpy(),initial[k]) for k,v in params.items())
    save(folder/'execution.json',dict(passed=True,records=records,strict_tail=audit,
        strict_prefix=paudit,initialized_trainables=443904,shadow_tail_forwards=2,
        backwards=2,actual_retained_updates=0,optimizer_API_calls=0,
        original_live_values_dtypes_restored=True))
    r.seal(folder,'backward_seal.json')


def fit():
    verify();r.check_seal(BASE/'backward','backward_seal.json')
    assert read(BASE/'backward/execution.json')['passed']
    impl.fit()


def run(stage):
    global START,torch
    START=time.monotonic();impl.START=START
    used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'))
    assert used<1800
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('SR1 combined cap')))
    signal.alarm(max(1,int(1800-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='preflight':impl.preflight()
        elif stage=='backward':backward()
        elif stage=='fit':fit()
        elif stage=='predict':impl.predict()
        elif stage in ('validate_fit','evaluate'):
            import validate_shadow_adapter_restart as v
            v.validate(stage)
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc()
        save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0)
        save(SUP/stage/'child_exit.json',dict(success=ok,error=error,
            full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':
    sys.modules['shadow_adapter_restart']=sys.modules[__name__]
    run(sys.argv[1])
