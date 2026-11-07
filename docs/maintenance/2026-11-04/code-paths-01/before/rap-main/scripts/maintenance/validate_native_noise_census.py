"""NOC1 independent Horn geometry/aggregate checks and bounded native replays."""
import importlib.util
import signal
import time
from pathlib import Path
import numpy as np
import local_motion_common as c
spec=importlib.util.spec_from_file_location('noc1',Path(__file__).with_name('native_noise_census.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
spec_v=importlib.util.spec_from_file_location('noc0_independent',Path(__file__).with_name('validate_native_output_capability.py'))
v=importlib.util.module_from_spec(spec_v);spec_v.loader.exec_module(v)


def delta(a,b):
    if isinstance(a,dict):
        assert isinstance(b,dict) and set(a)==set(b)
        return max([delta(a[k],b[k]) for k in a]+[0.])
    if isinstance(a,list):
        assert isinstance(b,list) and len(a)==len(b)
        return max([delta(x,y) for x,y in zip(a,b)]+[0.])
    if a is None or isinstance(a,(str,bool)) or isinstance(b,(str,bool)):
        assert a==b,(a,b);return 0.
    d=abs(float(a)-float(b));assert np.isfinite(d);return d


def trace(z,noise,a):
    assert np.array_equal(a['input_states'][0],noise)
    maximum=0.
    assert np.max(abs(a['taus']-np.array(n.TAUS)))<3e-8
    rigid=[]
    for i in range(5):
        t=1-i*.2;raw=a['end_point_trajectory'][i]
        assert np.max(abs(raw-(a['input_states'][i]-a['velocities'][i]*t)))<1e-6
        fit=[]
        for k in range(3):
            sl=slice(k*1000,(k+1)*1000);R,b,gap=v.horn(z['cond'][sl],raw[sl]);assert gap>1e-6
            fit.append(z['cond'][sl].astype(np.float64)@R.T+b)
        fit=np.concatenate(fit)
        reconstructed=fit*(1-t+.2)+noise*(t-.2)
        d=float(abs(reconstructed-a['trajectory'][i]).max());maximum=max(maximum,d);assert d<3e-5,d
        if i<4: assert np.array_equal(a['input_states'][i+1],a['trajectory'][i])
        rigid.append(float(np.sqrt(np.mean((raw-fit)**2))*float(z['scale'])))
    return maximum,float(np.mean(rigid))


def independent_cell(bt,br,at,ar):
    bt,br,at,ar=map(np.asarray,(bt,br,at,ar));dt=bt-at;dr=br-ar
    tests=dict(mean_t=at.mean()<=.9*bt.mean(),median_t=np.median(dt)>=.005,
        mean_R=ar.mean()<=br.mean()+.01,median_R=np.median(dr)>=0,
        joint_signs=np.count_nonzero((at<=bt)&(ar<=br))>=12,
        q90_t=np.percentile(at,90)<=1.05*np.percentile(bt,90),q90_R=np.percentile(ar,90)<=np.percentile(br,90)+.02)
    return {k:bool(x) for k,x in tests.items()}


def run():
    import torch
    from native_output_capability import args
    from rap_slam.rap_precision import ieee_matmul
    n.check();n.check_noise();n.check_predictions();n.check_old_delivery()
    rs=c.read(n.BASE/'results_seal.json');result=c.read(n.BASE/'results.json')
    assert c.sha(n.BASE/'results.json')==rs['results_sha256']
    assert c.sha(n.BASE/'prediction_seal.json')==rs['prediction_seal_sha256']
    assert c.sha(n.BASE/'diagnosis_seal.json')==rs['diagnosis_seal_sha256']
    ds=c.read(n.BASE/'diagnosis_seal.json');assert c.sha(n.BASE/'diagnosis.json')==ds['manifest_sha256']
    for p,h in ds['files'].items(): assert c.sha(n.BASE/p)==h,p
    max_pose=0.;max_metric=0.;max_rec=0.;max_rigid=0.;max_teacher=0.;checked=0;independent=[]
    # Geometry is separately reconstructed; old synthetic/real observation arrays are exact bindings.
    for fixture in n.FIXTURES:
        z=n.load(n.RETRY/f'bank/{fixture}_fixture.npz');obs=n.load(n.BASE/f'bank/observations_{fixture}.npz')
        assert set(obs)==set(n.OBS) and all(np.array_equal(obs[k],z[k]) for k in n.OBS)
        pts=z['points'].astype(np.float64);centers=np.array([p.mean(0) for p in np.split(pts,3)])
        assert np.max(abs(centers-z['centers']))<1e-10
        scale=1.5*abs(pts[:1000]-centers[0]).max();assert abs(scale-float(z['scale']))<1e-10
        condition=np.concatenate([(p-center)/scale for p,center in zip(np.split(pts,3),centers)]).astype(np.float32)
        assert np.max(abs(condition-z['cond']))<1e-7
        target=np.concatenate([(p@T[:3,:3].T+T[:3,3]-centers[0])/scale for p,T in zip(np.split(pts,3),z['truth'])]).astype(np.float32)
        assert np.array_equal(target,z['target'])
        assert all(x['t_m']<1e-5 and x['R_deg']<1e-5 for x in v.metric(v.parts(z,target),z['truth']))
        for arm in n.ARMS:
            for row in n.noise_rows():
                key=f"{fixture}_{arm}_{row['name']}";saved=next(x for x in result['records'] if x['fixture']==fixture and x['arm']==arm and x['name']==row['name'])
                a=n.load(n.BASE/'bank/predictions'/f'{key}.npz');noise=n.load(n.BASE/'bank/noise'/f"{row['name']}.npz")['noise']
                d,rigid=trace(z,noise,a);max_rec=max(max_rec,d);max_rigid=max(max_rigid,abs(rigid-saved['raw_rigidity_RMS_m']))
                assert abs(rigid-saved['raw_rigidity_RMS_m'])<1e-9
                native=[]
                for step in (0,4):
                    P=v.parts(z,a['end_point_trajectory'][step]);metric=v.metric(P,z['truth']);old=saved['native'][0 if step==0 else 1]
                    dp=float(abs(P-np.array(old['parts'])).max());max_pose=max(max_pose,dp);assert dp<1e-8
                    dm=v.compare_m(metric,old['errors']);max_metric=max(max_metric,dm)
                    native.append(dict(step=step+1,parts=P.tolist(),errors=metric))
                diag=n.load(n.BASE/'diagnosis'/f'{key}.npz');teacher=[];mse=[]
                assert np.array_equal(diag['taus'],np.array(n.TAUS))
                for i,tau in enumerate(n.TAUS):
                    x=(1-tau)*z['target']+tau*noise
                    dc=float(abs((x-tau*diag['teacher_velocities'][i])-diag['teacher_clean'][i]).max())
                    max_teacher=max(max_teacher,dc);assert dc<1e-6
                    P=v.parts(z,diag['teacher_clean'][i]);metric=v.metric(P,z['truth'])
                    max_metric=max(max_metric,v.compare_m(metric,saved['teacher'][i]['errors']))
                    teacher.append(dict(tau=tau,errors=metric))
                    mse.append(float(np.mean((diag['teacher_velocities'][i].astype(np.float64)-(noise-z['target']))**2)))
                assert np.max(abs(np.array(mse)-saved['teacher_MSE_by_tau']))<1e-8
                independent.append(dict(fixture=fixture,arm=arm,**row,native=native,teacher=teacher,
                    teacher_MSE_by_tau=mse,teacher_mean_MSE=float(np.mean(mse)),raw_rigidity_RMS_m=rigid))
                checked+=1;n.cap()
        control=n.load(n.RETRY/f'bank/{fixture}_direct/evaluation_0400.npz');old=next(x for x in result['direct_controls'] if x['fixture']==fixture)
        max_metric=max(max_metric,v.compare_m(v.metric(v.parts(z,control['output']),z['truth']),old['errors']))
    # Numerical stats and correlations use the separate reconstructed records; the gate is duplicated explicitly.
    reconstructed=n.summarize(independent);aggregate_delta=delta(reconstructed,result['summary']);assert aggregate_delta<2e-8,aggregate_delta
    fresh=[x['name'] for x in n.noise_rows() if x['role']=='primary']
    for cell in result['summary']['cells']:
        def values(arm,key):
            return [next(e[key] for e in next(x for x in independent if x['fixture']==cell['fixture'] and x['arm']==arm and x['name']==name)['native'][-1]['errors'] if e['part']==cell['part']) for name in fresh]
        tests=independent_cell(values('B','t_m'),values('B','R_deg'),values('A','t_m'),values('A','R_deg'))
        assert tests==cell['tests'] and all(tests.values())==cell['passed']
    m,params,audit=n.model();replays=0;teacher_replays=0
    with ieee_matmul():
        for row in n.noise_rows():
            noise=n.load(n.BASE/'bank/noise'/f"{row['name']}.npz")['noise']
            if row['name']=='training_reference':
                with np.load(n.RETRY/'bank/synthetic_fixture.npz',allow_pickle=False) as z: expected=z['noise']
                assert np.array_equal(noise,expected)
            else:
                with c.rng(row['seed']): regenerated=torch.randn((3000,3),device='cuda',dtype=torch.float32).cpu().numpy()
                assert np.array_equal(noise,regenerated)
        for fixture in n.FIXTURES:
            z=n.load(n.RETRY/f'bank/{fixture}_fixture.npz');b=n.noc.batch({k:z[k] for k in n.OBS});target=torch.tensor(z['target'],device='cuda')
            for arm in n.ARMS:
                before=n.set_arm(m,params,fixture,arm)
                for row in (n.noise_rows()[0],n.noise_rows()[15]):
                    noise=torch.tensor(n.load(n.BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda')
                    a=n.generate(m,b,noise);key=f"{fixture}_{arm}_{row['name']}";stored=n.load(n.BASE/'bank/predictions'/f'{key}.npz')
                    assert all(np.array_equal(a[k],stored[k]) for k in a);replays+=1
                    diag=n.load(n.BASE/'diagnosis'/f'{key}.npz')
                    with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                        for i,tau in enumerate(n.TAUS):
                            vel=m.flow_model(**args(b,(1-tau)*target+tau*noise,tau)).cpu().numpy()
                            assert np.array_equal(vel,diag['teacher_velocities'][i]);teacher_replays+=1
                    n.cap()
                assert n.param_digest(params)==before
    n.check();n.check_old_delivery()
    result=dict(passed=True,census_trace_records=checked,all_raw_geometry_metrics_and_recurrences_reconstructed=True,
        independent_aggregate_gate=True,statistical_summary_recomputed_from_independent_Horn_records=True,
        aggregate_code_shared_but_gate_independently_duplicated=True,
        exact_noise_replays=18,exact_full_native_replays=replays,exact_teacher_forward_replays=teacher_replays,
        full_census_native_replayed=False,optimizer_updates=0,
        max_pose_delta=max_pose,max_metric_delta=max_metric,max_recurrence_delta=max_rec,
        max_rigidity_delta=max_rigid,max_teacher_algebra_delta=max_teacher,max_aggregate_delta=aggregate_delta,
        decision=result['summary']['decision'],**n.usage())
    c.save(n.BASE/'validation.json',result)
    c.save(n.BASE/'validation_seal.json',dict(validation_sha256=c.sha(n.BASE/'validation.json'),
        results_seal_sha256=c.sha(n.BASE/'results_seal.json'),freeze_sha256=c.sha(n.BASE/'freeze.json')))
    n.finish('independent_validation');(n.BASE/'INCOMPLETE').unlink()
    c.status(n.BASE,'validated',status='VALIDATED_ZERO_UPDATE_NOISE_CENSUS_COMPLETE',decision=result['decision'],optimizer_updates=0)
    print('NOC1 VALIDATED',result,flush=True)


if __name__=='__main__':
    import torch
    n.START=time.monotonic()
    def alarm(signum,frame): raise TimeoutError('NOC1 validation remaining time exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(900-sum(x['wall_seconds'] for x in n.ledger()))))
    try: run()
    except Exception as ex: n.fail('validation',ex);raise
    finally: signal.alarm(0)
