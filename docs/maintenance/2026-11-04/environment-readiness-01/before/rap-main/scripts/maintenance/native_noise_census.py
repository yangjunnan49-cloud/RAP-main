"""NOC1: frozen native paired-noise census, zero optimization."""
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path
import numpy as np
import local_motion_common as c

BASE=c.MAIN/'docs/maintenance/2026-10-10/native-noise-robustness-01'
OLD=c.MAIN/'docs/maintenance/2026-10-10/native-output-capability-01'
RETRY=OLD/'attempt-02'
HELPER=c.SLAM/'scripts/native_output_capability.py'
spec=importlib.util.spec_from_file_location('noc0_loader',Path(__file__).with_name('native_output_capability.py'))
noc=importlib.util.module_from_spec(spec);spec.loader.exec_module(noc)
START=None
OBS=('points','features','cond','scale','centers','counts')
FIXTURES=('synthetic','real')
ARMS=('B','A')
TAUS=(1.,.8,.6,.4,.2)


def load(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k].copy() for k in z.files}


def noise_rows():
    rows=[dict(name=f'fresh_{i:02d}',role='primary',index=i,
        seed=int.from_bytes(hashlib.sha256(f'NOC1-noise-census|20261010|{i}'.encode()).digest()[:4],'big')) for i in range(16)]
    seeds=[x['seed'] for x in rows];assert len(set(seeds))==16
    assert not set(seeds)&{850873755,20261010,20261011}
    return rows+[dict(name='training_reference',role='old_reference',index=None,seed=850873755),
        dict(name='old_unseen_reference',role='old_reference',index=None,seed=20261011)]


def fit_name(fixture): return 'synthetic_native_lr1e-4' if fixture=='synthetic' else 'real_native'


def usage():
    import torch
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_initialized() else 0,
        artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()))


def ledger(): return c.read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []


def cap():
    u=usage();assert sum(x['wall_seconds'] for x in ledger())+u['wall_seconds']<=900,'combined wall cap'
    assert u['peak_RSS_bytes']<=4*2**30,'RSS cap'
    assert max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=3*2**30,'GPU cap'
    assert u['artifact_bytes']<=512*2**20,'artifact cap'


def finish(stage,success=True,**kw):
    if success: cap()
    rows=ledger()+[dict(stage=stage,success=success,utc=c.now(),**usage(),**kw)]
    (BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')


def fail(stage,ex):
    finish(stage,False,error=repr(ex));c.save(BASE/f'FAILURE_{stage}.json',dict(error=repr(ex),utc=c.now(),**usage()))
    c.status(BASE,stage,status='INCOMPLETE',error=repr(ex))


def check():
    import torch
    f=c.read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert c.sha(p)==h,p
    assert f['noise_rows']==noise_rows()
    assert torch.__version__==f['runtime']['torch'] and np.__version__==f['runtime']['numpy']
    assert torch.get_num_threads()==f['runtime']['threads']==1
    return f


def check_old_delivery():
    rows=c.read(OLD/'DELIVERY_SEAL.json')['files']
    for x in rows: assert c.sha(OLD/x['path'])==x['sha256'],x['path']
    assert len(rows)==103;return len(rows)


def freeze():
    import ast
    import torch
    check_old_delivery();repo=noc.git_state();old=c.read(OLD/'REPOSITORY_STATE.json')['repositories'];assert repo==old
    files={}
    for f in (OLD/'freeze.json',RETRY/'freeze.json',RETRY/'validation-attempt-02/freeze.json'):
        for p,h in c.read(f)['files'].items():
            if p in files: assert files[p]==h
            files[p]=h
        files[str(f)]=c.sha(f)
    extra=[Path(__file__),Path(__file__).with_name('validate_native_noise_census.py'),
        BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',OLD/'DELIVERY_SEAL.json',OLD/'NOISE_PROVENANCE_NOTE.json',
        RETRY/'bank_seal.json',RETRY/'bank.json',RETRY/'validation-attempt-02/validation.json',
        RETRY/'validation-attempt-02/validation_seal.json']
    for fixture in FIXTURES:
        extra.append(RETRY/f'bank/{fixture}_fixture.npz')
        for name in ('initial.npz','parameters_0400.npz','evaluation_0000.npz','evaluation_0400.npz','fit.json','seal.json'):
            extra.append(RETRY/'bank'/fit_name(fixture)/name)
        extra+=[RETRY/f'bank/{fixture}_direct/evaluation_0400.npz',RETRY/f'bank/{fixture}_direct/evaluation_0400.json']
    for p in extra: files[str(p)]=c.sha(p)
    for p,h in files.items(): assert c.sha(p)==h,p
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in (Path(__file__),Path(__file__).with_name('validate_native_noise_census.py')):
        ast.parse(p.read_text())
        (snap/p.name).write_bytes(p.read_bytes())
    c.save(BASE/'freeze.json',dict(utc=c.now(),files=files,repositories=repo,noise_rows=noise_rows(),
        fixtures=list(FIXTURES),arms=list(ARMS),optimizer_updates=0,native_inferences=72,primary_draws=16,
        runtime=dict(python=sys.version,torch=torch.__version__,numpy=np.__version__,
            gpu=torch.cuda.get_device_name(0),threads=torch.get_num_threads()),
        gate=dict(mean_t_ratio=.9,median_t_gain_m=.005,mean_R_slack_deg=.01,median_R_gain_deg=0,
            joint_nonworse_min=12,q90_t_ratio=1.05,q90_R_slack_deg=.02),
        limits=dict(wall_seconds=900,GPU_bytes=3*2**30,RSS_bytes=4*2**30,artifact_bytes=512*2**20)))
    (BASE/'INCOMPLETE').write_text('NOC1 authorized and frozen; zero-update census/validation pending.\n')
    c.status(BASE,'frozen',status='AUTHORIZED_FROZEN',optimizer_updates=0,model_loaded=False)
    finish('freeze');print('NOC1 frozen',len(files),'files,16 fresh paired draws',flush=True)


def noise_bank():
    import torch
    check();(BASE/'bank').mkdir();(BASE/'bank/noise').mkdir();(BASE/'bank/predictions').mkdir()
    for fixture in FIXTURES:
        with np.load(RETRY/f'bank/{fixture}_fixture.npz',allow_pickle=False) as z:
            observation={k:z[k].copy() for k in OBS}
        np.savez(BASE/f'bank/observations_{fixture}.npz',**observation)
    with np.load(RETRY/'bank/synthetic_fixture.npz',allow_pickle=False) as z: train=z['noise'].copy()
    with np.load(RETRY/'bank/real_fixture.npz',allow_pickle=False) as z: assert np.array_equal(train,z['noise'])
    for row in noise_rows():
        if row['name']=='training_reference': noise=train
        else:
            with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda',dtype=torch.float32).cpu().numpy()
        assert noise.dtype==np.float32 and noise.shape==(3000,3) and np.isfinite(noise).all()
        np.savez(BASE/'bank/noise'/f"{row['name']}.npz",noise=noise);cap()
    c.save(BASE/'noise_seal.json',dict(files={str(p.relative_to(BASE)):c.sha(p)
        for p in sorted((BASE/'bank').rglob('*.npz'))},rows=noise_rows()))
    finish('noise_bank');print('NOC1 noise bank sealed',flush=True)


def check_noise():
    s=c.read(BASE/'noise_seal.json');assert s['rows']==noise_rows()
    for p,h in s['files'].items(): assert c.sha(BASE/p)==h,p


def base_digest(flow,excluded):
    h=hashlib.sha256()
    for n,p in flow.named_parameters():
        if n not in excluded: h.update(n.encode());h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def param_digest(params):
    h=hashlib.sha256()
    for n,p in params.items(): h.update(n.encode());h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def model():
    import torch
    from native_output_capability import adapt,trainables
    m,audit=noc.load_model()
    with c.rng(20261010): adapt(m.flow_model)
    params=trainables(m.flow_model);assert sum(p.numel() for p in params.values())==443904
    expected=c.read(RETRY/'bank/synthetic_native_lr1e-4/fit.json')['frozen_parameters_sha256']
    assert base_digest(m.flow_model,params)==expected
    m.requires_grad_(False);assert not any(p.requires_grad for p in m.parameters())
    return m,params,audit


def set_arm(m,params,fixture,arm):
    import torch
    path=RETRY/'bank'/fit_name(fixture)/('initial.npz' if arm=='B' else 'parameters_0400.npz')
    weights=load(path);assert set(weights)==set(params)
    with torch.no_grad():
        for n,p in params.items():
            assert weights[n].shape==tuple(p.shape) and weights[n].dtype==np.float32 and np.isfinite(weights[n]).all()
            p.copy_(torch.tensor(weights[n],device='cuda'))
    return param_digest(params)


def generate(m,b,noise):
    import torch
    assert 'target' not in b and 'truth' not in b and b['pointclouds_gt'] is b['pointclouds']
    captured=[]
    def hook(module,inputs,kw,out):
        captured.append((kw['x'].detach().cpu().numpy().copy(),out.detach().cpu().numpy().copy(),kw['timesteps'].cpu().numpy().copy()))
    handle=m.flow_model.register_forward_hook(hook,with_kwargs=True)
    try:
        with c.rng(20261010),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
            native=m.sample_rectified_flow(b,None,x_1=noise,return_tarjectory=True)
    finally: handle.remove()
    assert len(captured)==5
    out={k:v.cpu().numpy().copy() for k,v in native.items()}
    out.update(input_states=np.stack([x[0] for x in captured]),velocities=np.stack([x[1] for x in captured]),
        taus=np.concatenate([x[2] for x in captured]))
    cap();return out


def prediction_bank():
    import torch
    from rap_slam.rap_precision import ieee_matmul
    check();check_noise();m,params,audit=model();records=[]
    with ieee_matmul():
        for fixture in FIXTURES:
            z=load(BASE/f'bank/observations_{fixture}.npz');b=noc.batch(z)
            for arm in ARMS:
                before=set_arm(m,params,fixture,arm)
                for row in noise_rows():
                    noise=torch.tensor(load(BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda')
                    output=generate(m,b,noise);name=f"{fixture}_{arm}_{row['name']}"
                    np.savez(BASE/'bank/predictions'/f'{name}.npz',**output)
                    assert all(np.isfinite(x).all() for x in output.values()),name
                    if row['role']=='old_reference':
                        old=load(RETRY/'bank'/fit_name(fixture)/('evaluation_0000.npz' if arm=='B' else 'evaluation_0400.npz'))
                        prefix='train' if row['name']=='training_reference' else 'unseen'
                        assert all(np.array_equal(v,old[prefix+'_'+k]) for k,v in output.items()),name
                    records.append(dict(fixture=fixture,arm=arm,**row,file=f'bank/predictions/{name}.npz'))
                assert param_digest(params)==before
                assert base_digest(m.flow_model,params)==c.read(RETRY/'bank'/fit_name(fixture)/'fit.json')['frozen_parameters_sha256']
                cap();print('NOC1 native census',fixture,arm,'18 draws',flush=True)
    c.save(BASE/'predictions.json',dict(records=records,checkpoint=audit,no_target_in_inference=True,
        all_weights_frozen_and_unchanged=True,optimizer_updates=0,flow_calls=360,**usage()))
    c.save(BASE/'prediction_seal.json',dict(freeze_sha256=c.sha(BASE/'freeze.json'),noise_seal_sha256=c.sha(BASE/'noise_seal.json'),
        manifest_sha256=c.sha(BASE/'predictions.json'),files={str(p.relative_to(BASE)):c.sha(p)
            for p in sorted((BASE/'bank/predictions').glob('*.npz'))}))
    finish('native_predictions');print('NOC1 all72 prediction traces sealed before new pose metrics',flush=True)


def check_predictions():
    s=c.read(BASE/'prediction_seal.json')
    assert c.sha(BASE/'freeze.json')==s['freeze_sha256'] and c.sha(BASE/'noise_seal.json')==s['noise_seal_sha256']
    assert c.sha(BASE/'predictions.json')==s['manifest_sha256']
    for p,h in s['files'].items(): assert c.sha(BASE/p)==h,p


def diagnosis_bank():
    import torch
    from native_output_capability import args
    from rap_slam.rap_precision import ieee_matmul
    check();check_predictions();(BASE/'diagnosis').mkdir();m,params,audit=model();records=[]
    with ieee_matmul():
        for fixture in FIXTURES:
            observation=load(BASE/f'bank/observations_{fixture}.npz');b=noc.batch(observation)
            with np.load(RETRY/f'bank/{fixture}_fixture.npz',allow_pickle=False) as z: y=z['target'].copy()
            target=torch.tensor(y,device='cuda')
            for arm in ARMS:
                before=set_arm(m,params,fixture,arm)
                for row in noise_rows():
                    noise=torch.tensor(load(BASE/'bank/noise'/f"{row['name']}.npz")['noise'],device='cuda');vel=[];clean=[]
                    with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                        for tau in TAUS:
                            x=(1-tau)*target+tau*noise;v=m.flow_model(**args(b,x,tau))
                            vel.append(v.cpu().numpy().copy());clean.append((x-tau*v).cpu().numpy().copy())
                    output=dict(teacher_velocities=np.array(vel),teacher_clean=np.array(clean),taus=np.array(TAUS))
                    name=f"{fixture}_{arm}_{row['name']}";np.savez(BASE/'diagnosis'/f'{name}.npz',**output)
                    assert all(np.isfinite(v).all() for v in output.values()),name
                    if row['role']=='old_reference' and row['name']=='training_reference':
                        old=load(RETRY/'bank'/fit_name(fixture)/('evaluation_0000.npz' if arm=='B' else 'evaluation_0400.npz'))
                        assert np.array_equal(output['teacher_clean'],old['teacher'])
                    records.append(dict(fixture=fixture,arm=arm,**row,file=f'diagnosis/{name}.npz'));cap()
                assert param_digest(params)==before
                assert base_digest(m.flow_model,params)==c.read(RETRY/'bank'/fit_name(fixture)/'fit.json')['frozen_parameters_sha256']
                print('NOC1 separate teacher diagnosis',fixture,arm,flush=True)
    c.save(BASE/'diagnosis.json',dict(records=records,oracle_diagnostic_only=True,optimizer_updates=0,flow_calls=360,**usage()))
    c.save(BASE/'diagnosis_seal.json',dict(prediction_seal_sha256=c.sha(BASE/'prediction_seal.json'),
        manifest_sha256=c.sha(BASE/'diagnosis.json'),files={str(p.relative_to(BASE)):c.sha(p)
            for p in sorted((BASE/'diagnosis').glob('*.npz'))}))
    finish('teacher_diagnosis');print('NOC1 teacher diagnosis sealed',flush=True)


def scores(z,trace):
    from native_output_capability import poses,errors
    values=[]
    for step in (0,4):
        P=poses(z['cond'],trace['end_point_trajectory'][step],z['centers'],float(z['scale']))
        values.append(dict(step=step+1,parts=P.tolist(),errors=errors(P,z['truth'])))
    rigid=[]
    for raw in trace['end_point_trajectory']:
        P=poses(z['cond'],raw,z['centers'],float(z['scale']))
        fitted=np.concatenate([q.astype(np.float64)@T[:3,:3].T+
            (T[:3,3]+T[:3,:3]@center)/float(z['scale']) for q,T,center in zip(np.split(z['cond'],3),P,z['centers'])])
        rigid.append(float(np.sqrt(np.mean((raw-fitted)**2))*float(z['scale'])))
    return values,float(np.mean(rigid))


def distribution(values):
    a=np.array(values,dtype=float)
    return dict(mean=float(a.mean()),median=float(np.median(a)),q90=float(np.quantile(a,.9,method='linear')),
        std=float(a.std()),min=float(a.min()),max=float(a.max()))


def cell_gate(bt,br,at,ar):
    g=c.read(BASE/'freeze.json')['gate'];dt=np.array(bt)-np.array(at);dr=np.array(br)-np.array(ar)
    B=dict(t=distribution(bt),R=distribution(br));A=dict(t=distribution(at),R=distribution(ar))
    signs=int(np.count_nonzero((dt>=0)&(dr>=0)))
    tests=dict(mean_t=A['t']['mean']<=g['mean_t_ratio']*B['t']['mean'],median_t=float(np.median(dt))>=g['median_t_gain_m'],
        mean_R=A['R']['mean']<=B['R']['mean']+g['mean_R_slack_deg'],median_R=float(np.median(dr))>=g['median_R_gain_deg'],
        joint_signs=signs>=g['joint_nonworse_min'],q90_t=A['t']['q90']<=g['q90_t_ratio']*B['t']['q90'],
        q90_R=A['R']['q90']<=B['R']['q90']+g['q90_R_slack_deg'])
    return dict(B=B,A=A,paired_t_gain=distribution(dt),paired_R_gain=distribution(dr),joint_nonworse=signs,
        B_absolute_pass=int(np.count_nonzero((np.array(bt)<=.05)&(np.array(br)<=.2))),
        A_absolute_pass=int(np.count_nonzero((np.array(at)<=.05)&(np.array(ar)<=.2))),tests=tests,passed=all(tests.values()))


def spearman(a,b):
    from scipy.stats import spearmanr
    if np.ptp(a)==0 or np.ptp(b)==0: return None
    return float(spearmanr(a,b).statistic)


def dispersion(rows,part):
    from scipy.spatial.transform import Rotation
    relative=[]
    for row in rows:
        P=np.array(row['native'][-1]['parts']);relative.append(np.linalg.solve(P[0],P[part]))
    translation=[];rotation=[]
    for i in range(len(relative)):
        for j in range(i):
            a,b=relative[i],relative[j]
            translation.append(float(np.linalg.norm(a[:3,3]-b[:3,3])))
            rotation.append(float(np.degrees(np.linalg.norm(Rotation.from_matrix(a[:3,:3].T@b[:3,:3]).as_rotvec()))))
    return dict(pairwise_pairs=len(translation),translation_distance=distribution(translation),
        rotation_distance=distribution(rotation),dependent_pairs=True,no_mean_pose_candidate=True)


def summarize(records):
    cells=[];fresh=[x['name'] for x in noise_rows() if x['role']=='primary']
    for fixture in FIXTURES:
        for part in (1,2):
            rows={arm:[next(x for x in records if x['fixture']==fixture and x['arm']==arm and x['name']==name)
                for name in fresh] for arm in ARMS}
            def column(arm,key): return [next(e for e in r['native'][-1]['errors'] if e['part']==part)[key] for r in rows[arm]]
            bt,br,at,ar=column('B','t_m'),column('B','R_deg'),column('A','t_m'),column('A','R_deg')
            cell=dict(fixture=fixture,part=part,**cell_gate(bt,br,at,ar));secondary={}
            for arm in ARMS:
                rr=rows[arm];ts=column(arm,'t_m');rs=column(arm,'R_deg');loss=[r['teacher_mean_MSE'] for r in rr]
                rigidity=[r['raw_rigidity_RMS_m'] for r in rr]
                teacher_t=[next(e for e in r['teacher'][-1]['errors'] if e['part']==part)['t_m'] for r in rr]
                secondary[arm]=dict(teacher_mean_MSE=distribution(loss),teacher_native_final_t_gap=distribution(np.array(ts)-teacher_t),
                    native_noise_pose_dispersion=dispersion(rr,part),
                    teacher_loss_native_t_spearman=spearman(loss,ts),teacher_loss_native_R_spearman=spearman(loss,rs),
                    rigidity_native_t_spearman=spearman(rigidity,ts),rigidity_native_R_spearman=spearman(rigidity,rs))
            cell['secondary']=secondary
            refs=[]
            for name in ('training_reference','old_unseen_reference'):
                for arm in ARMS:
                    rr=next(x for x in records if x['fixture']==fixture and x['arm']==arm and x['name']==name)
                    e=next(e for e in rr['native'][-1]['errors'] if e['part']==part)
                    ts=column(arm,'t_m');rs=column(arm,'R_deg')
                    refs.append(dict(name=name,arm=arm,errors=e,
                        t_fresh_empirical_percentile=float(np.mean(np.array(ts)<=e['t_m'])),
                        R_fresh_empirical_percentile=float(np.mean(np.array(rs)<=e['R_deg']))))
            cell['references']=refs;cells.append(cell)
    passed=all(x['passed'] for x in cells)
    return dict(cells=cells,primary_conjunction=passed,
        decision='NOISE_CENSUS_SUPPORTS_NEARBY_EVALUATION_DESIGN' if passed else 'NO_STABLE_FRESH_NOISE_ADAPTER_CONJUNCTION',
        primary_draws=16,old_reference_draws_excluded=2,optimizer_updates=0,nearby_windows_executed=0,
        conditional_census_not_independent_generalization=True,no_noise_selection_or_pose_ensemble=True)


def evaluate():
    from native_output_capability import poses,errors
    check();check_predictions();d=c.read(BASE/'diagnosis_seal.json')
    assert c.sha(BASE/'diagnosis.json')==d['manifest_sha256']
    assert c.sha(BASE/'prediction_seal.json')==d['prediction_seal_sha256']
    for p,h in d['files'].items(): assert c.sha(BASE/p)==h,p
    records=[];controls=[]
    for fixture in FIXTURES:
        z=load(RETRY/f'bank/{fixture}_fixture.npz')
        control=load(RETRY/f'bank/{fixture}_direct/evaluation_0400.npz')
        controls.append(dict(fixture=fixture,errors=errors(poses(z['cond'],control['output'],z['centers'],float(z['scale'])),z['truth']),
            noise_independent=True,previously_exposed=True))
        for arm in ARMS:
            for row in noise_rows():
                key=f"{fixture}_{arm}_{row['name']}";trace=load(BASE/'bank/predictions'/f'{key}.npz')
                diag=load(BASE/'diagnosis'/f'{key}.npz');noise=load(BASE/'bank/noise'/f"{row['name']}.npz")['noise']
                native,rigidity=scores(z,trace);teacher=[];mse=[]
                target=z['target'];vtarget=noise-target
                for k,tau in enumerate(TAUS):
                    P=poses(z['cond'],diag['teacher_clean'][k],z['centers'],float(z['scale']))
                    teacher.append(dict(tau=tau,errors=errors(P,z['truth'])))
                    mse.append(float(np.mean((diag['teacher_velocities'][k]-vtarget)**2)))
                records.append(dict(fixture=fixture,arm=arm,**row,native=native,teacher=teacher,
                    teacher_MSE_by_tau=mse,teacher_mean_MSE=float(np.mean(mse)),raw_rigidity_RMS_m=rigidity));cap()
    result=dict(records=records,direct_controls=controls,summary=summarize(records),**usage())
    c.save(BASE/'results.json',result)
    c.save(BASE/'results_seal.json',dict(results_sha256=c.sha(BASE/'results.json'),
        prediction_seal_sha256=c.sha(BASE/'prediction_seal.json'),diagnosis_seal_sha256=c.sha(BASE/'diagnosis_seal.json')))
    c.status(BASE,'evaluated',status='COMPLETE_VALIDATION_PENDING',decision=result['summary']['decision'],optimizer_updates=0)
    finish('evaluation');print('NOC1 evaluated',result['summary']['decision'],flush=True)


if __name__=='__main__':
    import torch
    START=time.monotonic();stage=sys.argv[1]
    def alarm(signum,frame): raise TimeoutError('NOC1 combined remaining time exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(900-sum(x['wall_seconds'] for x in ledger()))))
    try: {'freeze':freeze,'noise':noise_bank,'predict':prediction_bank,'diagnose':diagnosis_bank,'evaluate':evaluate}[stage]()
    except Exception as ex: fail(stage,ex);raise
    finally: signal.alarm(0)
