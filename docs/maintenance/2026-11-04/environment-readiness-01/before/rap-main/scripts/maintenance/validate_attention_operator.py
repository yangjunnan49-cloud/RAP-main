"""AOD0 CPU explicit sampled softmax-Q derivative and independent artifact census."""
import numpy as np
from scipy.special import softmax
import attention_operator_diagnosis as r
def load(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def validate():
    r.verify();seal=r.read(r.BASE/'bank_seal.json');assert seal['freeze_sha256']==r.sha(r.BASE/'freeze.json')
    assert seal['files']=={p.name:r.sha(p) for p in (r.BASE/'bank').iterdir() if p.is_file()}
    ex=r.read(r.BASE/'bank/execution.json');assert ex['operator_VJPs']==8 and ex['projection_VJPs']==4 and ex['native_whole_forwards']==ex['prefix_calls']==ex['optimizer_calls']==ex['parameter_updates']==0
    assert ex['backend_flags_restored'] and all(z['cotangent_repeated_byteexact'] for z in ex['projection']);records=[];pairs=[]
    for row in ex['records']:
        z=load(r.BASE/f"bank/{row['name']}.npz");inputs=load(r.BASE/f"bank/{row['arm']}_input.npz");n=len(z['normalized']); ids=np.unique(np.linspace(0,n-1,64,dtype=int));maxdelta=0.;outside=0
        q,k,v=(z['normalized'][:,j].astype(float) for j in range(3)); cot=inputs['cotangent'].astype(np.float16).astype(float).reshape(n,row['heads'],row['head_dim'])
        for h in range(row['heads']):
            p=softmax(q[ids,h]@k[:,h].T/np.sqrt(row['head_dim']),axis=1);dp=cot[ids,h]@v[:,h].T;ds=p*(dp-np.sum(p*dp,axis=1,keepdims=True))
            expected=(ds@k[:,h]/np.sqrt(row['head_dim'])).astype(np.float16);actual=z['normalized_gradient'][ids,0,h]
            delta=np.abs(expected.astype(float)-actual.astype(float));ulp=np.abs(np.spacing(expected).astype(float));outside+=int(np.sum(delta>ulp));maxdelta=max(maxdelta,float(delta.max()))
        assert np.isfinite(z['raw_gradient']).all();forward_delta=float(np.max(abs(z['output']-inputs['saved_out'])));assert forward_delta==row['archive_forward_max_delta']
        records.append(dict(name=row['name'],explicit_Q_query_rows=len(ids)*row['heads'],rounded_softmax_Q_max_delta=maxdelta,outside_one_fp16_ULP=outside,scope='sampled Q derivative, not complete raw/QK-norm/K/V derivative'))
        r.cap()
    for arm in ('V','P'):
        for backend in ('default','math'):
            a=load(r.BASE/f'bank/{arm}_{backend}1.npz');b=load(r.BASE/f'bank/{arm}_{backend}2.npz');values={}
            for key in ('output','raw_gradient','normalized_gradient'):
                d=a[key].astype(float)-b[key].astype(float);values[key]=dict(byte_equal=bool(np.array_equal(a[key],b[key])),different=int(np.count_nonzero(d)),max_abs=float(np.max(abs(d))))
            pairs.append(dict(arm=arm,backend=backend,values=values))
    r.verify();r.save(r.BASE/'validation.json',dict(passed=True,records=records,pairs=pairs,dispatch_records=ex['records'],independent_artifact_census=True,
        independent_full_attention_backward=False,unique_whole_model_cause_proved=False,optimizer_calls=0))
    print('Independent operator artifact/softmax-Q census passes',pairs,flush=True)
