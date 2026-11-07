"""SR1 additive fixed-arm complete evaluator; identical numerical formulas."""
import resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
import shadow_adapter_restart as s
import validate_shadow_adapter_restart as v
import validate_native_backward as e

BASE=s.BASE
START=None


def usage():
    return dict(wall_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,
        artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),
        optimizer_calls=0,imports_included=True)


def evaluate_arm(arm):
    s.verify()
    ex=s.read(BASE/'predictions/execution.json')
    assert ex['complete_source_sampler_traces']==51
    seal=s.read(BASE/'prediction_seal.json')
    assert seal['freeze_sha256']==s.sha(BASE/'freeze.json')
    rows=[row for row in ex['records'] if row['arm']==arm];assert len(rows)==17
    z=e.load(s.r.r.OLD/'bank/synthetic_fixture.npz');condition=z['cond'].astype(float)
    records=[];maxrig=0.;maxstate=0.;buffer_outside=0;part_fits=0;checked_files=0
    for row in rows:
        folder=BASE/f"predictions/{row['arm']}_{row['noise']}"
        relative=folder.relative_to(BASE/'predictions')
        for q in sorted(folder.iterdir()):
            if q.is_file():
                key=str(q.relative_to(BASE/'predictions'))
                assert seal['files'][key]==s.sha(q);checked_files+=1
        source=e.load(folder/'source_trajectory.npz');meta=s.read(folder/'trace.json')
        noise=e.load(s.r.r.OLD/f"bank/noise/{row['noise']}.npz")['noise'].astype(float)
        assert meta['taus']==[1-i*.2 for i in range(5)];previous=None;first=None
        for i,tau in enumerate(meta['taus']):
            x=e.load(folder/f'step_{i}.npz')
            assert np.array_equal(x['prefix_input'],x['state'].astype(np.float32))
            assert np.array_equal(x['timestep'],np.array([tau],np.float32))
            if i==0:assert np.array_equal(x['state'],noise);first=x
            else:
                delta=float(np.max(abs(x['state']-previous)));assert delta<=1e-10
                maxstate=max(maxstate,delta)
            endpoint=x['state']-tau*x['velocity'];rigid=[]
            for k in range(3):
                cond=condition[k*1000:(k+1)*1000]
                rot,shift=e.horn(cond,endpoint[k*1000:(k+1)*1000])
                rigid.append(cond@rot.T+shift);part_fits+=1
            rigid=np.concatenate(rigid);delta=float(np.max(abs(rigid-x['rigid'])))
            assert delta<=1e-10;maxrig=max(maxrig,delta)
            previous=rigid*(1-tau+.2)+noise*(tau-.2)
            for name,expected in [('end_point_trajectory',endpoint),('trajectory',previous)]:
                actual=source[name][i]
                difference=abs(expected.astype(np.float32).astype(float)-actual.astype(float))
                outside=int(np.sum(difference>abs(np.spacing(actual).astype(float))))
                assert outside==0;buffer_outside+=outside
        records.append(dict(row,first=v.pose_metrics(z,source['end_point_trajectory'][0].astype(float)),
            final=v.pose_metrics(z,source['end_point_trajectory'][-1].astype(float)),
            first_velocity_MSE=float(np.mean((first['velocity']-(noise-z['target'].astype(float)))**2)),
            first_buffer_pose_loss=e.objective(z,source['end_point_trajectory'][0].astype(float))))
        print('SR1 evaluated',arm,row['noise'],flush=True)
    assert part_fits==255 and checked_files==119
    chunk=dict(arm=arm,records=records,independent_Horn_part_fits=part_fits,
        independent_rigid_max_delta=maxrig,independent_state_max_delta=maxstate,
        float32_buffer_outside_ULP=buffer_outside,sha256_files_checked=checked_files,
        formulas='unchanged frozen evaluator',complete_arm=True)
    (BASE/'evaluation_chunks').mkdir(exist_ok=True)
    s.save(BASE/f'evaluation_chunks/{arm}.json',chunk)


def summarize():
    s.verify();ex=s.read(BASE/'predictions/execution.json')
    chunks=[s.read(BASE/f'evaluation_chunks/{arm}.json') for arm in ('U','V','P')]
    assert all(x['complete_arm'] and x['independent_Horn_part_fits']==255 and x['sha256_files_checked']==119 for x in chunks)
    records=[row for chunk in chunks for row in chunk['records']]
    assert [(x['arm'],x['noise']) for x in records]==[(x['arm'],x['noise']) for x in ex['records']]
    gate=s.read(BASE/'freeze.json')['gate'];cells=[]
    for arm in ('V','P'):
        for part in (1,2):
            def values(a,key):
                return [next(x[key] for x in row['final'] if x['part']==part)
                    for row in records if row['arm']==a and row['role']=='old_eval']
            cells.append(dict(arm=arm,part=part,**v.cell_gate(values('U','t_m'),values('U','R_deg'),
                values(arm,'t_m'),values(arm,'R_deg'),gate)))
    summary=dict(cells=cells,conditional_noise_conjunction=all(x['passed'] for x in cells),
        fit_diagnostics=[x for x in records if x['role']=='fit_diagnostic'],
        old_eval_noises=16,independent_scenes=1,not_fresh_noise=True)
    decision='BOUNDED_SHADOW_FIT_COMPLETE_WITH_CONDITIONAL_NOISE_SIGNAL' if summary['conditional_noise_conjunction'] else 'BOUNDED_SHADOW_FIT_COMPLETE_NO_SAFE_MATERIAL_NOISE_CONJUNCTION'
    s.save(BASE/'results.json',dict(records=records,summary=summary,decision=decision,
        actual_retained_updates=40,original_native_equivalence=False,system_or_physical_gain_claim=False))
    s.save(BASE/'validation.json',dict(passed=True,fit_validation=s.read(BASE/'fit_validation.json'),
        complete_paired_traces=51,independent_Horn_part_fits=765,
        independent_rigid_max_delta=max(x['independent_rigid_max_delta'] for x in chunks),
        independent_state_max_delta=max(x['independent_state_max_delta'] for x in chunks),
        float32_buffer_outside_ULP=sum(x['float32_buffer_outside_ULP'] for x in chunks),
        all_prediction_bindings_and_counts=True,sha256_files_checked=sum(x['sha256_files_checked'] for x in chunks),
        metrics_and_gates_independently_reconstructed=True,independent_complete_model=False,
        additive_fixed_arm_chunks=['U','V','P'],two_external_timeouts_preserved=True,
        decision=decision,conditional_noise_conjunction=summary['conditional_noise_conjunction']))
    print('SR1 chunked independent complete pilot',decision,flush=True)


def run(stage):
    global START
    START=time.monotonic();s.START=START;s.impl.START=START
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('SR1 chunk cap')))
    signal.alarm(600);ok=False;error=None
    try:
        if stage in ('evaluate_U','evaluate_V','evaluate_P'):evaluate_arm(stage[-1])
        elif stage=='summarize':summarize()
        else:raise ValueError(stage)
        s.cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc()
        s.save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);folder=BASE/'supervision'/stage;folder.mkdir(parents=True,exist_ok=True)
        s.save(folder/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run(sys.argv[1])
