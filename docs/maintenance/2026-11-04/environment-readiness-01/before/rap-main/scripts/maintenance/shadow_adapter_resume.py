"""SR1 additive completion of exactly nine missing predictions after outer kill."""
import resource,signal,sys,time,traceback
from pathlib import Path
import shadow_adapter_restart as s

BASE=s.BASE
START=None


def usage():
    engine=s.impl.torch
    return dict(wall_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=engine.cuda.max_memory_allocated() if engine is not None and engine.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=engine.cuda.max_memory_reserved() if engine is not None and engine.cuda.is_initialized() else 0,
        artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),
        optimizer_calls=0,imports_included=True)


def resume():
    s.verify();s.r.check_seal(BASE/'fits','fit_seal.json')
    assert s.read(BASE/'fit_validation.json')['fit_conjunction']
    folder=BASE/'predictions';assert folder.is_dir()
    assert not (folder/'execution.json').exists() and not (BASE/'prediction_seal.json').exists()
    expected=[dict(arm=arm,noise=name,role='fit_diagnostic' if name=='fit_00' else 'old_eval')
        for arm in ('U','V','P') for name in ['fit_00']+[f'eval_{i:02d}' for i in range(16)]]
    present=[row for row in expected if (folder/f"{row['arm']}_{row['noise']}").is_dir()]
    missing=[row for row in expected if not (folder/f"{row['arm']}_{row['noise']}").is_dir()]
    assert len(present)==42 and [x['arm'] for x in missing]==['P']*9
    assert [x['noise'] for x in missing]==[f'eval_{i:02d}' for i in range(7,16)]
    assert {q.name for q in folder.iterdir() if q.is_dir()}=={f"{x['arm']}_{x['noise']}" for x in present}
    existing={}
    expected_names={'source_trajectory.npz','trace.json'}|{f'step_{i}.npz' for i in range(5)}
    for row in present:
        case=folder/f"{row['arm']}_{row['noise']}"
        assert {q.name for q in case.iterdir() if q.is_file()}==expected_names
        for q in sorted(case.iterdir()):
            if q.is_file():existing[str(q.relative_to(folder))]=s.sha(q)
    protocol=BASE/'PREDICT_RECOVERY_PROTOCOL.md'
    recovery=dict(utc=s.now(),runner_sha256=s.sha(Path(__file__)),
        protocol_sha256=s.sha(protocol),original_freeze_sha256=s.sha(BASE/'freeze.json'),
        external_predict_wall_seconds=300,existing_cases=42,missing_cases=9,
        missing=[f"{x['arm']}_{x['noise']}" for x in missing],existing_files=existing,
        partial_evaluation_performed=False,old_experiments_modified=False)
    s.save(BASE/'PREDICT_RECOVERY_FREEZE.json',recovery)
    n,prefix,tail,params,initial,audit,paudit,z,batch,frozen=s.impl.setup()
    import numpy as np
    initial64={k:v.astype(float) for k,v in initial.items()}
    with s.r.double_tail(tail.flow_model,params,n):
        state=n.load(BASE/'fits/P/parameters_20.npz');n.assign(params,state)
        for row in missing:
            name=f"{row['arm']}_{row['noise']}"
            s.impl.rollout(n,prefix,tail,batch,row['noise'],folder/name)
            assert all(np.array_equal(value.detach().cpu().numpy(),state[k]) for k,value in params.items())
            print('SR1 recovered prediction',name,flush=True)
        for value in params.values():value.grad=None
        n.assign(params,initial64)
    assert n.frozen_digest(prefix.flow_model)==frozen
    assert all(np.array_equal(value.detach().cpu().numpy(),initial[k]) for k,value in params.items())
    for path,digest in existing.items():assert s.sha(folder/path)==digest,path
    assert all((folder/f"{x['arm']}_{x['noise']}").is_dir() for x in expected)
    s.save(folder/'execution.json',dict(records=expected,complete_source_sampler_traces=51,
        shadow_tail_forwards=255,prefix_calls=255,backwards=0,optimizer_API_calls=0,
        retained_updates=0,no_truth_target_arrays_loaded=True,all_live_values_restored=True,
        additive_recovery_existing_cases=42,additive_recovery_new_cases=9))
    s.r.seal(folder,'prediction_seal.json')


def run():
    global START
    START=time.monotonic();s.START=START;s.impl.START=START
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('SR1 recovery cap')))
    signal.alarm(600);ok=False;error=None
    try:
        resume();s.cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc()
        s.save(BASE/'FAILURE_predict_resume.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0)
        s.save(BASE/'supervision/predict_resume/child_exit.json',dict(success=ok,error=error,
            full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run()
