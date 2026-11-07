"""Independent GT/error/aggregation/gate reconstruction for RLP2."""
import sys
import numpy as np
import local_motion_common as c
import rlp2_common as r
import rlp2_independent as v

def validate():
    f=r.check(r.EVAL);r.check_seal(r.EVAL);result=c.read(r.EVAL/'bank/results.json')
    maximum=0.;groups={};reference={};permutation={};coverage=True
    for row in f['rows']:
        _,proper=v.targets(c.DATA,row);truth=proper[0];key=(row['seq'],row['t'])
        with np.load(r.LAB/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:assert abs(truth-z['angular_truth'][0]).max()<1e-8
        for arm in ('D','I','J'):
            groups[key,arm]=[]
            for seed in r.SEEDS:
                with np.load(r.PRED/'bank'/f'{seed}_{arm}_{r.stem(row)}.npz',allow_pickle=False) as z:
                    if bool(z['valid']):ee=v.errors(truth,z['pose']);value=[ee['translation_m'],ee['rotation_deg']]
                    else:value=None;coverage=False
                old=next(x for x in result['records'] if x['kind']=='primary' and x['seed']==seed and x['arm']==arm and (x['seq'],x['t'])==key)
                if value is None:assert old['error'] is None
                else:
                    d=float(abs(np.array(value)-old['error']).max());maximum=max(maximum,d);assert d<1e-8
                groups[key,arm].append(value)
        with np.load(r.FULL/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:
            for arm in ('G3','KISS','identity'):
                if arm=='KISS' and row['seq']=='08':continue
                pose=np.eye(4) if arm=='identity' else z[arm+'_pose'];ee=v.errors(truth,pose)
                reference[key,arm]=[ee['translation_m'],ee['rotation_deg']]
                old=next(x for x in result['records'] if x['kind']=='reference' and x['arm']==arm and (x['seq'],x['t'])==key)
                d=float(abs(np.array(reference[key,arm])-old['error']).max());maximum=max(maximum,d);assert d<1e-8
        permutation[key]=[]
        for seed in r.SEEDS:
            with np.load(r.DIAG/'bank'/f'{seed}_J_{r.stem(row)}.npz',allow_pickle=False) as z:
                if bool(z['valid']):ee=v.errors(truth,z['pose']);value=[ee['translation_m'],ee['rotation_deg']]
                else:value=None
            old=next(x for x in result['records'] if x['kind']=='permuted' and x['seed']==seed and (x['seq'],x['t'])==key)
            if value is None:assert old['error'] is None
            else:
                d=float(abs(np.array(value)-old['error']).max());maximum=max(maximum,d);assert d<1e-8
            permutation[key].append(value)
        r.cap()
    keys=[(x['seq'],x['t']) for x in f['rows']];summary=result['summary']
    assert summary['gates']['coverage']==coverage
    if coverage:
        med={a:np.array([np.median(groups[k,a],axis=0) for k in keys]) for a in ('D','I','J')}
        for arm in med:assert abs(np.median(med[arm],axis=0)-summary['cohort_medians'][arm]).max()<1e-8
        gates={}
        for arm in ('I','D','G3','KISS'):
            ids=[i for i,k in enumerate(keys) if arm!='KISS' or k[0]!='08']
            other=med[arm][ids] if arm in med else np.array([reference[keys[i],arm] for i in ids])
            joint=med['J'][ids];gain=other-joint;old=summary['comparisons'][arm]
            for name,value in (('paired_median_gain',np.median(gain,axis=0)),('J_median',np.median(joint,axis=0)),
                               ('control_median',np.median(other,axis=0)),('positive_fraction',np.mean(gain>0,axis=0))):
                assert abs(value-old[name]).max()<1e-8
            threshold=np.array([.002,.005] if arm=='KISS' else [.005,.01]);passed=bool((np.median(gain,axis=0)>=threshold).all())
            if arm!='G3':passed=passed and bool((np.median(joint,axis=0)<=.9*np.median(other,axis=0)).all())
            if arm in ('I','D'):passed=passed and bool((np.mean(gain>0,axis=0)>=.60).all())
            for s in sorted({keys[i][0] for i in ids}):
                kk=[j for j,i in enumerate(ids) if keys[i][0]==s];reg=np.mean(joint[kk]-other[kk],axis=0)
                safe=bool((reg<=[.005,.02]).all());assert safe==old['sequence_safety'][s]['passed']
                assert abs(reg-old['sequence_safety'][s]['mean_regression']).max()<1e-8;passed=passed and safe
            assert passed==old['passed']==summary['gates'][arm];gates[arm]=passed
        joint=gates['D'] and gates['I'];useful=joint and gates['G3'] and gates['KISS']
        decision='PASS_USEFUL_LOCAL_MOTION' if useful else 'REPRESENTATION_ONLY_NO_USEFUL_LOCAL_GAIN' if joint else 'NO_COUPLED_JOINT_READOUT_SIGNAL'
        assert decision==summary['decision'] and joint==summary['joint_pass'] and useful==summary['useful_pass']
        for s in ('07','08','09','10'):
            ids=[i for i,k in enumerate(keys) if k[0]==s]
            for arm in med:
                assert abs(med[arm][ids].mean(0)-summary['sequence'][s][arm]['mean']).max()<1e-8
                assert abs(np.median(med[arm][ids],axis=0)-summary['sequence'][s][arm]['median']).max()<1e-8
        assert abs(np.median([reference[k,'identity'] for k in keys],axis=0)-summary['identity_median']).max()<1e-8
        if all(all(x is not None for x in permutation[k]) for k in keys):
            p=np.array([np.median(permutation[k],axis=0) for k in keys])
            assert abs(np.median(p,axis=0)-summary['permutation']['median_error']).max()<1e-8
            assert abs(np.median(p-med['J'],axis=0)-summary['permutation']['median_permuted_minus_J']).max()<1e-8
    else:assert summary['decision']=='COVERAGE_INCONCLUSIVE'
    assert len(result['records'])==708
    r.pass_validation(r.EVAL,dict(decision=summary['decision'],metric_records=708,maximum_error_delta=maximum,
        all_gates_independently_reconstructed=True,physical_GT_verified=False,trajectory_run=False,**r.usage()))
    r.finish('evaluation_validation');print('RLP2 final results independently VALIDATED',summary['decision'],maximum,flush=True)

if __name__=='__main__':
    try:validate()
    except Exception as ex:r.fail('evaluation_validation',ex);raise
