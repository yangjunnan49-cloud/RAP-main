"""Artifact-only CPU audit of failed original probes and retained P replay mismatch."""
import json,resource,sys,time,traceback
from pathlib import Path
import numpy as np
import native_conditioned_comparison as r
import validate_native_pose_fit as v
c=r.c;ORIGINAL=r.BASE;BASE=ORIGINAL/'attempt-02';AUDIT=BASE/'execution-stop-audit-01'
r.BASE=r.old.BASE=BASE
LOG=c.MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-supervision-02/audit_stop'
START=time.monotonic();r.old.START=START

def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0)

def run():
    r.check();counts=r.old_deliveries()
    for row in c.read(ORIGINAL/'DELIVERY_SEAL.json')['files']:assert c.sha(ORIGINAL/row['path'])==row['sha256']
    (AUDIT/'failure_status_snapshot.json').write_bytes((BASE/'STATUS.json').read_bytes())
    files=dict(c.read(BASE/'freeze.json')['files'])
    for p in sorted(BASE.rglob('*')):
        if p.is_file() and not p.is_relative_to(AUDIT) and p.name!='STATUS.json':files[str(p)]=c.sha(p)
    for p in (Path(__file__),AUDIT/'PROTOCOL.md',AUDIT/'failure_status_snapshot.json'):files[str(p)]=c.sha(p)
    c.save(AUDIT/'freeze.json',dict(utc=c.now(),files=files,CPU_only=True,zero_additional_optimizer_backward_forward=True,
        limits=dict(wall_seconds=120,RSS_bytes=2**30,artifact_bytes=64*2**20)))
    for p,h in files.items():assert c.sha(p)==h,p
    r.noise_check();r.check_seal(BASE/'preflight')
    z=r.load(BASE/'bank/synthetic_fixture.npz');records=[];step_max=cost_max=0.
    original=c.read(BASE/'preflight/probes.json');assert not original['passed']
    for arm in ('V','P'):
        cached=BASE/'preflight'/arm;full=BASE/'preflight_replay'/arm;r.check_seal(full)
        info=c.read(cached/'probe.json');replay=c.read(full/'probe.json')
        assert set(k for k,x in info['tests'].items() if not x)=={'loss_decreases'}
        assert not replay['passed'] and not replay['tests']['loss_decreases']
        assert info['parameters_restored_byteexact'] and replay['parameters_restored_byteexact']
        diffs={};directions=[]
        for name in ('initial.npz','gradients.npz','parameters_after.npz','optimizer_final.npz','output_before.npz','output_after.npz'):
            a,b=r.load(cached/name),r.load(full/name);assert set(a)==set(b)
            diffs[name]=dict(byteexact=all(np.array_equal(a[k],b[k]) for k in a),
                changed_values=sum(int(np.count_nonzero(a[k]!=b[k])) for k in a),
                max_abs_delta=max(float(np.max(np.abs(a[k].astype(np.float64)-b[k].astype(np.float64)))) for k in a))
            assert all(np.isfinite(x).all() for x in list(a.values())+list(b.values()))
        assert diffs['initial.npz']['byteexact'] and diffs['output_before.npz']['byteexact']
        if arm=='V':assert all(x['byteexact'] for x in diffs.values())
        else:assert not diffs['gradients.npz']['byteexact'] and not diffs['parameters_after.npz']['byteexact']
        for folder,metadata in ((cached,info),(full,replay)):
            initial=r.load(folder/'initial.npz');g=r.load(folder/'gradients.npz');after=r.load(folder/'parameters_after.npz')
            dot=delta_norm=0.;groups={}
            for k in initial:
                grad=g[k].astype(np.float64);delta=after[k].astype(np.float64)-initial[k].astype(np.float64)
                expected=initial[k].astype(np.float64)-1e-4*grad/(np.abs(grad)+1e-8)
                d=float(abs(after[k].astype(np.float64)-expected).max());assert d<1.5e-7;step_max=max(step_max,d)
                dot+=float(np.sum(grad*delta));delta_norm+=float(np.sum(delta**2))
                group=r.group(k);groups[group]=groups.get(group,0.)+float(np.sum(grad**2))
                if group=='A':assert np.count_nonzero(grad)==np.count_nonzero(delta)==0
                if group=='B':assert np.count_nonzero(grad)>0 and np.count_nonzero(delta)>0
            assert metadata['FD_delta']<=max(2e-4,.02*abs(metadata['analytic']))
            for name,key in (('output_before.npz','loss_before'),('output_after.npz','loss_after')):
                q=r.load(folder/name)['output']
                if arm=='P':cost,_=v.objective(z,q);tolerance=1e-7
                else:cost=float(np.mean((q-z['target'])**2));tolerance=1e-8
                d=abs(cost-metadata[key]);assert d<tolerance,(arm,name,d);cost_max=max(cost_max,d)
            directions.append(dict(forward=metadata['forward'],gradient_dot_actual_update=dot,
                parameter_delta_L2=float(np.sqrt(delta_norm)),gradient_group_L2={k:float(np.sqrt(x)) for k,x in groups.items()},
                loss_before=metadata['loss_before'],loss_after=metadata['loss_after'],failed_tests=[k for k,x in metadata['tests'].items() if not x]))
        records.append(dict(arm=arm,array_differences=diffs,paths=directions))
    assert not (BASE/'bank/synthetic_V').exists() and not (BASE/'bank/synthetic_P').exists()
    assert not (BASE/'bank/synthetic_predictions').exists()
    assert not r.torch.cuda.is_initialized()
    u=usage();assert u['wall_seconds']<120 and u['peak_RSS_bytes']<=2**30
    result=dict(passed=True,decision='PROBE_LOSS_INCREASE_AND_P_REPLAY_MISMATCH',scientific_comparison_incomplete=True,
        original_numerical_gate_passed=False,original_full_forward_validator_passed=False,records=records,
        independent_numpy_first_Adam_step_max_delta=step_max,independent_stored_objective_max_delta=cost_max,
        optimizer_probe_calls_already_executed=4,retained_probe_updates=0,fit_updates=0,native_prediction_traces=0,
        additional_backward_optimizer_native_forward_calls=0,old_delivery_counts_unchanged=counts+[60],
        stored_FD_checks_only=True,no_unique_mismatch_or_loss_increase_cause_claim=True,**u)
    c.save(AUDIT/'validation.json',result)
    assert sum(p.stat().st_size for p in AUDIT.rglob('*') if p.is_file())<64*2**20
    r.seal(AUDIT);print('Retained preflight stop artifact audit PASSED',json.dumps(result),flush=True)

try:
    run();success=True;error=None
except BaseException as ex:
    traceback.print_exc();success=False;error=repr(ex)
finally:
    c.save(LOG/'child_exit.json',dict(success=success,error=error,full_resource_capture=True,**usage()))
if not success:sys.exit(1)
