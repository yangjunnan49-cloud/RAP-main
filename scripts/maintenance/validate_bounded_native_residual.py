"""BRF0 independent polar/SE3/error/bound/aggregate reconstruction."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-native-residual-feasibility-01'
RLP=ROOT/'docs/maintenance/2026-10-08/motion-supervised-readout-01'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as stream:
        for body in iter(lambda:stream.read(131072),b''):h.update(body)
    return h.hexdigest()

def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def polar(a):
    import numpy as np
    a=np.array(a,dtype=float)
    assert a.shape==(4,4) and np.isfinite(a).all()
    assert np.linalg.det(a[:3,:3])>0 and np.max(np.abs(a[3]-[0,0,0,1]))<=1e-12
    gram=a[:3,:3].T@a[:3,:3];values,vectors=np.linalg.eigh(gram)
    assert min(values)>0
    inverse_root=(vectors*(1/np.sqrt(values))[None,:])@vectors.T
    out=a.copy();out[:3,:3]=a[:3,:3]@inverse_root;out[3]=[0,0,0,1]
    assert np.max(np.abs(out-a))<=1e-5
    assert np.max(np.abs(out[:3,:3].T@out[:3,:3]-np.eye(3)))<1e-10
    return out

def exp_closed(v,w):
    import numpy as np
    x,y,z=w;W=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    theta=math.sqrt(math.fsum(float(t)*float(t) for t in w))
    if theta==0:
        R=V=np.eye(3)
    else:
        R=np.eye(3)+(math.sin(theta)/theta)*W+((1-math.cos(theta))/theta**2)*(W@W)
        V=np.eye(3)+((1-math.cos(theta))/theta**2)*W+((theta-math.sin(theta))/theta**3)*(W@W)
    out=np.eye(4);out[:3,:3]=R;out[:3,3]=V@v
    return out

def err(g,p):
    import numpy as np
    g=np.asarray(g);p=np.asarray(p)
    translation=math.sqrt(math.fsum(float(x-y)**2 for x,y in zip(g[:3,3],p[:3,3])))
    d=g[:3,:3].T@p[:3,:3]
    sine=.5*math.sqrt(math.fsum(float(x)**2 for x in (d[2,1]-d[1,2],d[0,2]-d[2,0],d[1,0]-d[0,1])))
    cosine=.5*(math.fsum(float(d[i,i]) for i in range(3))-1)
    return [translation,math.degrees(math.atan2(sine,cosine))]

def compare(actual,expected,tolerance=1e-8):
    if isinstance(expected,dict):
        assert set(actual)==set(expected),(set(actual),set(expected))
        for key,value in expected.items():compare(actual[key],value,tolerance)
    elif isinstance(expected,(list,tuple)):
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected):compare(a,b,tolerance)
    elif isinstance(expected,bool) or isinstance(expected,str):assert actual==expected
    elif isinstance(expected,(int,float)):
        assert math.isfinite(actual) and abs(actual-expected)<=tolerance,(actual,expected)
    else:assert actual==expected

def check_poses():
    import numpy as np
    f=read(BASE/'freeze.json');seal=read(BASE/'pose_seal.json')
    assert sha(BASE/seal['path'])==seal['sha256'] and not seal['targets_loaded']
    bank=read(BASE/'pose_bank.json')
    assert len(bank['rows'])==len(f['rows'])==48
    assert not bank['targets_loaded'] and bank['native_model_or_head_calls']==0
    max_pose=max_fixture=0.;counts=dict(J=0,G3=0,KISS=0)
    for row,record in zip(f['rows'],bank['rows']):
        assert [record[k] for k in ('seq','t','ids')]==[row[k] for k in ('seq','t','ids')]
        expected={'J','G3'}|({'KISS'} if int(row['seq']) in (7,9,10) else set())
        assert set(record['poses'])==expected
        p=RLP/'full-bank/bank'/f'{row["seq"]}_{row["t"]:06d}.npz'
        with np.load(p,allow_pickle=False) as z:
            for arm,stored in record['poses'].items():
                original=z[arm+'_pose']
                assert np.array_equal(original,np.asarray(stored['original']))
                proper=polar(original)
                delta=float(np.max(np.abs(proper-np.asarray(stored['proper']))))
                assert delta<=1e-10
                max_pose=max(max_pose,delta);counts[arm]+=1
                compare(stored['proper_max_delta'],float(np.max(np.abs(np.asarray(stored['proper'])-original))),1e-12)
    assert counts==dict(J=48,G3=48,KISS=36)
    assert len(bank['fixtures'])==65
    for record in bank['fixtures']:
        expected=exp_closed(record['v'],record['w'])
        delta=float(np.max(np.abs(expected-np.asarray(record['exp']))))
        assert delta<=1e-10
        max_fixture=max(max_fixture,delta)
        errors=err(np.eye(4),expected)
        compare(errors,[record['translation_norm_m'],record['rotation_angle_deg']],1e-10)
        assert errors[0]<=math.sqrt(3)*.05+1e-10 and errors[1]<=math.sqrt(3)*.2+1e-10
    return dict(passed=True,native_poses=48,G3_poses=48,KISS_poses=36,target_free_fixtures=65,
        independent_polar_max_delta=max_pose,independent_closed_exp_max_delta=max_fixture,
        targets_loaded=False,head_or_model_calls=0)

def independent_summary(records):
    import numpy as np
    comparisons={}
    for name,minimum,count in [('G3',[.005,.01],48),('KISS',[.002,.005],36)]:
        rows=[r for r in records if name in r['control_errors']];assert len(rows)==count
        lo=np.array([r['optimistic_error_lower_bound'] for r in rows])
        other=np.array([r['control_errors'][name] for r in rows])
        gain=np.median(other-lo,axis=0).tolist()
        gain_possible=all(a>=b for a,b in zip(gain,minimum))
        optimistic=np.median(lo,axis=0).tolist();control=np.median(other,axis=0).tolist()
        ratio_possible=name=='G3' or all(a<=.9*b for a,b in zip(optimistic,control))
        safety={}
        for seq in sorted({r['seq'] for r in rows}):
            inds=[i for i,r in enumerate(rows) if r['seq']==seq]
            regression=[math.fsum(float(lo[i,k]-other[i,k]) for i in inds)/len(inds) for k in range(2)]
            safety[seq]=dict(optimistic_mean_regression=regression,
                possible=regression[0]<=.005 and regression[1]<=.02)
        possible=gain_possible and ratio_possible and all(s['possible'] for s in safety.values())
        comparisons[name]=dict(windows=count,optimistic_paired_median_gain=gain,
            optimistic_median_error=optimistic,control_median_error=control,
            required_paired_margins=minimum,paired_gain_possible=gain_possible,
            cohort_ratio_possible=ratio_possible,sequence_safety=safety,
            all_necessary_conditions_possible=possible)
    possible=all(r['all_necessary_conditions_possible'] for r in comparisons.values())
    return dict(decision='NECESSARY_CONDITIONS_NOT_RULED_OUT_NO_LEARNABILITY_OR_EFFICACY_ADMISSION' if possible else
        'BOUNDED_NATIVE_BASE_FAMILY_CANNOT_MEET_STRONG_CONTROL_GATES',
        all_necessary_conditions_possible=possible,comparisons=comparisons,
        no_head_fit_or_achieved_prediction=True,units=['translation_m','rotation_deg'])

def check_census():
    import numpy as np
    assert read(BASE/'pose_validation.json')['passed']
    seal=read(BASE/'census_seal.json');assert sha(BASE/seal['path'])==seal['sha256']
    c=read(BASE/'census.json');bank=read(BASE/'pose_bank.json');f=read(BASE/'freeze.json')
    assert len(c['records'])==len(bank['rows'])==48
    maximum=0.;rebuilt=[];error_count=0
    limits=(math.sqrt(3)*.05,math.sqrt(3)*.2)
    allowance=(1e-9,1e-7)
    for row,source,actual in zip(f['rows'],bank['rows'],c['records']):
        assert [actual[k] for k in ('seq','t','ids')]==[row[k] for k in ('seq','t','ids')]
        p=RLP/'pose-targets/bank'/f'{row["seq"]}_{row["t"]:06d}.npz'
        with np.load(p,allow_pickle=False) as z:original=z['angular_truth'][0]
        assert np.array_equal(original,np.asarray(actual['reference_original']))
        truth=polar(original)
        assert np.max(np.abs(truth-np.asarray(actual['reference_proper'])))<1e-10
        base=err(truth,polar(source['poses']['J']['original']))
        controls={name:err(truth,polar(value['original'])) for name,value in source['poses'].items() if name!='J'}
        compare(actual['native_base_error'],base)
        compare(actual['control_errors'],controls)
        lower=[max(0.,base[i]-limits[i]-allowance[i]) for i in range(2)]
        compare(actual['optimistic_error_lower_bound'],lower)
        maximum=max(maximum,max(abs(x-y) for x,y in zip(base,actual['native_base_error'])))
        for key in controls:
            maximum=max(maximum,max(abs(x-y) for x,y in zip(controls[key],actual['control_errors'][key])))
        error_count+=1+len(controls)
        rebuilt.append(dict(seq=row['seq'],t=row['t'],native_base_error=base,
            control_errors=controls,optimistic_error_lower_bound=lower))
    summary=independent_summary(rebuilt);compare(c['summary'],summary)
    assert error_count==132
    return dict(passed=True,decision=summary['decision'],all48_rows_and132_errors_verified=True,
        independent_error_max_delta=maximum,all_bound_and_control_conjunctions_verified=True,
        optimistic_family_not_achieved_predictions=True,summary=summary,
        head_fits=0,backwards=0,physical_truth_or_new_system_claim=False)

def validate(stage):
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    if stage=='validate_poses':
        result=check_poses();save('pose_validation.json',result)
    elif stage=='validate_census':
        result=check_census();save('validation.json',result)
    else:raise ValueError(stage)
    print(json.dumps(result),flush=True)
