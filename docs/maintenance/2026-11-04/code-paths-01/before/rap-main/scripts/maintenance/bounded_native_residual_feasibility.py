"""BRF0 necessary output-family bounds, not a fitted registration method."""
import time
START=time.monotonic()
import itertools
import json
import math
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-native-residual-feasibility-01'
SUP=BASE/'supervision'
PCC=ROOT/'docs/maintenance/2026-10-14/physical-comparison-contract-01/layout-attempt-02'
RLP=ROOT/'docs/maintenance/2026-10-08/motion-supervised-readout-01'
read,sha=s.read,s.sha
BOUNDS=(math.sqrt(3)*.05,math.sqrt(3)*.2)
PADDING=(1e-9,1e-7)

def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())

def save(p,v):
    body=(json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<32*2**20
    with Path(p).open('xb') as stream:stream.write(body)

def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert s.repositories()==f['repositories']
    return f

def freeze():
    assert read(PCC/'validation.json')['passed']
    assert read(PCC/'STATUS.json')['status']=='VALIDATED_COMMON_INPUT_STRONG_CONTROL_CONTRACT_WITH_RETAINED_LAYOUT_FAILURE'
    files={}
    for row in read(PCC/'DELIVERY_SEAL.json')['files']:
        p=PCC/row['path'];assert sha(p)==row['sha256'];files[str(p)]=row['sha256']
    selected=[r for r in read(PCC/'freeze.json')['rows'] if r['role']=='exposed_evaluation']
    assert len(selected)==48 and {seq:sum(r['seq']==seq for r in selected) for seq in ('07','08','09','10')}==dict.fromkeys(('07','08','09','10'),12)
    bound=read(PCC/'contract_audit.json')['selected_current_bank_hashes']
    for row in selected:
        for stage in ('full-bank','pose-targets'):
            p=RLP/stage/'bank'/f'{row["seq"]}_{row["t"]:06d}.npz'
            assert sha(p)==bound[str(p)];files[str(p)]=bound[str(p)]
    paths=[PCC/'DELIVERY_SEAL.json',BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),
        Path(__file__).with_name('validate_bounded_native_residual.py'),
        Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
        Path(__file__).with_name('rlp2_full_bank.py'),Path(__file__).with_name('rlp2_evaluate.py')]
    for p in paths:files[str(p)]=sha(p)
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
    save(BASE/'freeze.json',dict(files=files,repositories=s.repositories(),rows=selected,
        translation_component_bound_m=.05,rotation_component_bound_deg=.2,
        translation_norm_bound_m=BOUNDS[0],rotation_norm_bound_deg=BOUNDS[1],
        optimistic_numerical_allowance=PADDING,caps=dict(Windows_seconds=900,RSS_bytes=512*2**20,GPU_bytes=0,dossier_bytes=32*2**20),
        old_source_failures_and_scientific_stops_unchanged=True))
    save(BASE/'INCOMPLETE',dict(scope='BRF0',pending='proper poses/bound census/independent validation'))
    print('BRF0 frozen',len(files),'identities/48 exposed windows',flush=True)

def proper(value):
    import numpy as np
    a=np.asarray(value,dtype=np.float64)
    assert a.shape==(4,4) and np.isfinite(a).all()
    assert np.max(np.abs(a[3]-[0,0,0,1]))<=1e-12
    r=a[:3,:3];assert np.linalg.det(r)>0
    u,_,vt=np.linalg.svd(r)
    q=a.copy();q[:3,:3]=u@vt;q[3]=[0,0,0,1]
    delta=float(np.max(np.abs(q-a)));assert delta<=1e-5
    return q,delta

def poses():
    f=verify()
    import numpy as np
    from scipy.linalg import expm
    from scipy.spatial.transform import Rotation
    rows=[]
    for row in f['rows']:
        p=RLP/'full-bank/bank'/f'{row["seq"]}_{row["t"]:06d}.npz'
        arms=('J','G3','KISS') if row['seq']!='08' else ('J','G3')
        values={}
        with np.load(p,allow_pickle=False) as z:
            for arm in arms:
                raw=z[arm+'_pose'].copy();value,delta=proper(raw)
                values[arm]=dict(original=raw.tolist(),proper=value.tolist(),proper_max_delta=delta)
        rows.append(dict(seq=row['seq'],t=row['t'],ids=row['ids'],poses=values))
        cap()
    fixtures=[]
    twists=[([0.,0.,0.],[0.,0.,0.])]
    signs=list(itertools.product((-1.,1.),repeat=3))
    twists += [([.05*x for x in v],[math.radians(.2)*x for x in w]) for v in signs for w in signs]
    for v,w in twists:
        x,y,z=w;W=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        A=np.zeros((4,4));A[:3,:3]=W;A[:3,3]=v
        value=expm(A)
        t=float(np.linalg.norm(value[:3,3]));angle=float(Rotation.from_matrix(value[:3,:3]).magnitude()*180/math.pi)
        assert t<=BOUNDS[0]+1e-10 and angle<=BOUNDS[1]+1e-10
        fixtures.append(dict(v=v,w=w,exp=value.tolist(),translation_norm_m=t,rotation_angle_deg=angle))
    assert len(fixtures)==65
    save(BASE/'pose_bank.json',dict(rows=rows,fixtures=fixtures,targets_loaded=False,
        native_model_or_head_calls=0,base='common stored five-step unadapted J_pose'))
    save(BASE/'pose_seal.json',dict(path='pose_bank.json',sha256=sha(BASE/'pose_bank.json'),rows=48,
        native_poses=48,G3_poses=48,KISS_poses=36,targets_loaded=False))
    verify();print('BRF0 all48 native/G3+36 KISS poses sealed before targets',flush=True)

def error(reference,prediction):
    import numpy as np
    from scipy.spatial.transform import Rotation
    r=np.asarray(reference);p=np.asarray(prediction)
    return [float(np.linalg.norm(r[:3,3]-p[:3,3])),
            float(Rotation.from_matrix(r[:3,:3].T@p[:3,:3]).magnitude()*180/math.pi)]

def summarize(records):
    import numpy as np
    comparisons={}
    for control in ('G3','KISS'):
        chosen=[r for r in records if control in r['control_errors']]
        assert len(chosen)==(48 if control=='G3' else 36)
        lower=np.asarray([r['optimistic_error_lower_bound'] for r in chosen])
        ee=np.asarray([r['control_errors'][control] for r in chosen])
        margins=np.array([.005,.01]) if control=='G3' else np.array([.002,.005])
        median_gain=np.median(ee-lower,axis=0)
        gain_ok=bool(np.all(median_gain>=margins))
        ratio_ok=True if control=='G3' else bool(np.all(np.median(lower,axis=0)<=.9*np.median(ee,axis=0)))
        safety={}
        for seq in sorted({r['seq'] for r in chosen}):
            mask=np.array([r['seq']==seq for r in chosen]);regression=np.mean(lower[mask]-ee[mask],axis=0)
            safety[seq]=dict(optimistic_mean_regression=regression.tolist(),possible=bool(np.all(regression<=np.array([.005,.02]))))
        possible=gain_ok and ratio_ok and all(r['possible'] for r in safety.values())
        comparisons[control]=dict(windows=len(chosen),optimistic_paired_median_gain=median_gain.tolist(),
            optimistic_median_error=np.median(lower,axis=0).tolist(),control_median_error=np.median(ee,axis=0).tolist(),
            required_paired_margins=margins.tolist(),paired_gain_possible=gain_ok,
            cohort_ratio_possible=ratio_ok,sequence_safety=safety,all_necessary_conditions_possible=possible)
    possible=all(r['all_necessary_conditions_possible'] for r in comparisons.values())
    decision=('NECESSARY_CONDITIONS_NOT_RULED_OUT_NO_LEARNABILITY_OR_EFFICACY_ADMISSION' if possible else
              'BOUNDED_NATIVE_BASE_FAMILY_CANNOT_MEET_STRONG_CONTROL_GATES')
    return dict(decision=decision,all_necessary_conditions_possible=possible,comparisons=comparisons,
        no_head_fit_or_achieved_prediction=True,units=['translation_m','rotation_deg'])

def census():
    f=verify();assert read(BASE/'pose_validation.json')['passed']
    seal=read(BASE/'pose_seal.json');assert sha(BASE/seal['path'])==seal['sha256']
    import numpy as np
    bank=read(BASE/'pose_bank.json');rows=[]
    for fixed,source in zip(f['rows'],bank['rows']):
        assert (fixed['seq'],fixed['t'])==(source['seq'],source['t'])
        p=RLP/'pose-targets/bank'/f'{fixed["seq"]}_{fixed["t"]:06d}.npz'
        with np.load(p,allow_pickle=False) as z:raw=z['angular_truth'][0].copy()
        truth,delta=proper(raw)
        base=error(truth,source['poses']['J']['proper'])
        controls={arm:error(truth,value['proper']) for arm,value in source['poses'].items() if arm!='J'}
        lower=[max(0.,base[i]-BOUNDS[i]-PADDING[i]) for i in range(2)]
        rows.append(dict(seq=fixed['seq'],t=fixed['t'],ids=fixed['ids'],
            reference_original=raw.tolist(),reference_proper=truth.tolist(),reference_proper_delta=delta,
            native_base_error=base,control_errors=controls,optimistic_error_lower_bound=lower))
        cap()
    assert len(rows)==48
    summary=summarize(rows)
    save(BASE/'census.json',dict(records=rows,summary=summary,translation_norm_bound_m=BOUNDS[0],
        rotation_norm_bound_deg=BOUNDS[1],optimistic_allowance=PADDING,
        targets_only_after_pose_seal_and_independent_validation=True,
        official_reference_and_historical_metrics_unchanged=True,head_fits=0))
    save(BASE/'census_seal.json',dict(path='census.json',sha256=sha(BASE/'census.json'),records=48))
    verify();print('BRF0',summary['decision'],flush=True)

def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    native_model_calls=0,head_backwards=0,retained_updates=0,optimizer_calls=0)

def cap():
    u=usage();assert u['peak_RSS_bytes']<=512*2**20 and u['artifact_bytes']<32*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30

def run(stage):
    used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert used<900
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('BRF0 aggregate cap')))
    signal.alarm(max(1,int(900-used)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='poses':poses()
        elif stage=='census':census()
        elif stage in ('validate_poses','validate_census'):
            import validate_bounded_native_residual as v
            v.validate(stage)
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)

if __name__=='__main__':run(sys.argv[1])
