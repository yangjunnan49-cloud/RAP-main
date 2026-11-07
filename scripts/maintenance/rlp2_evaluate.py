"""RLP2 evaluation after both complete prediction banks seal."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp2_common as r

def freeze():
    extra=[]
    for base in (r.PRED,r.DIAG,r.LAB,r.FULL):
        r.check(base);r.check_seal(base);r.validated(base)
        extra += [base/name for name in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
        extra += list((base/'bank').glob('*'))
    selected=[x for x in r.rows() if x['role']=='exposed_evaluation']
    r.freeze(r.EVAL,selected,__file__,Path(__file__).with_name('validate_rlp2_evaluation.py'),gt=True,references=True,
        extra_files=extra,primary_predictions=432,diagnostic_predictions=144)
    r.finish('evaluation_freeze')

def error(gt,pred):
    delta=gt[:3,:3].T@pred[:3,:3]
    sine=float(np.linalg.norm(delta-delta.T)/(2*np.sqrt(2.)))
    cosine=float((np.trace(delta)-1)/2)
    return [float(np.sqrt(np.sum((gt[:3,3]-pred[:3,3])**2))),float(np.degrees(np.arctan2(sine,cosine)))]

def summarize(records,selected):
    primary=[x for x in records if x['kind']=='primary']
    coverage=all(x['error'] is not None for x in primary) and len(primary)==432
    if not coverage:return dict(decision='COVERAGE_INCONCLUSIVE',gates=dict(coverage=False),valid=sum(x['error'] is not None for x in primary),total=432)
    model={a:[] for a in ('D','I','J')};reference={a:[] for a in ('G3','KISS','identity')};permuted=[]
    for row in selected:
        s,t=row['seq'],row['t']
        for a in model:
            values=[x['error'] for x in primary if x['arm']==a and x['seq']==s and x['t']==t]
            assert len(values)==3;model[a].append(np.median(values,axis=0))
        for a in reference:
            value=[x['error'] for x in records if x['kind']=='reference' and x['arm']==a and x['seq']==s and x['t']==t]
            reference[a].append(value[0] if value else [np.nan,np.nan])
        values=[x['error'] for x in records if x['kind']=='permuted' and x['seq']==s and x['t']==t]
        permuted.append(np.median(values,axis=0) if len(values)==3 and all(x is not None for x in values) else [np.nan,np.nan])
    model={k:np.array(v) for k,v in model.items()};reference={k:np.array(v) for k,v in reference.items()}
    comparisons={};gates=dict(coverage=True)
    for control in ('I','D','G3','KISS'):
        mask=np.array([x['seq'] in ('07','09','10') for x in selected]) if control=='KISS' else np.ones(48,bool)
        other=(model if control in model else reference)[control];gain=other[mask]-model['J'][mask]
        jm=np.median(model['J'][mask],axis=0);cm=np.median(other[mask],axis=0)
        margins=np.array([.002,.005]) if control=='KISS' else np.array([.005,.01])
        safety={}
        for s in sorted({selected[i]['seq'] for i in np.flatnonzero(mask)}):
            seqmask=np.array([x['seq']==s for x in selected]);reg=(model['J'][seqmask]-other[seqmask]).mean(0)
            safety[s]=dict(mean_regression=reg.tolist(),passed=bool(np.all(reg<=np.array([.005,.02]))))
        passed=bool(np.all(np.median(gain,axis=0)>=margins)) and all(x['passed'] for x in safety.values())
        if control in ('I','D','KISS'):passed=passed and bool(np.all(jm<=.9*cm))
        if control in ('I','D'):passed=passed and bool(np.all((gain>0).mean(0)>=.60))
        comparisons[control]=dict(windows=int(mask.sum()),paired_median_gain=np.median(gain,axis=0).tolist(),
            J_median=jm.tolist(),control_median=cm.tolist(),positive_fraction=(gain>0).mean(0).tolist(),
            sequence_safety=safety,passed=passed);gates[control]=passed
    joint=gates['I'] and gates['D'];useful=joint and gates['G3'] and gates['KISS']
    decision='PASS_USEFUL_LOCAL_MOTION' if useful else 'REPRESENTATION_ONLY_NO_USEFUL_LOCAL_GAIN' if joint else 'NO_COUPLED_JOINT_READOUT_SIGNAL'
    p=np.array(permuted);pmask=np.isfinite(p).all(1)
    diag=dict(total=144,valid=sum(x['error'] is not None for x in records if x['kind']=='permuted'),complete_window_medians=int(pmask.sum()))
    if pmask.all():diag.update(median_error=np.median(p,axis=0).tolist(),median_permuted_minus_J=np.median(p-model['J'],axis=0).tolist())
    sequence={s:{a:dict(mean=model[a][np.array([x['seq']==s for x in selected])].mean(0).tolist(),
        median=np.median(model[a][np.array([x['seq']==s for x in selected])],axis=0).tolist()) for a in model} for s in ('07','08','09','10')}
    return dict(decision=decision,gates=gates,joint_pass=joint,useful_pass=useful,comparisons=comparisons,
        cohort_medians={k:np.median(a,axis=0).tolist() for k,a in model.items()},sequence=sequence,permutation=diag,
        identity_median=np.median(reference['identity'],axis=0).tolist(),units=['translation_m','rotation_deg'])

def run():
    f=r.check(r.EVAL);(r.EVAL/'bank').mkdir();records=[]
    for row in f['rows']:
        with np.load(r.LAB/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:truth=z['angular_truth'][0]
        for mode,base,arms in (('primary',r.PRED,('D','I','J')),('permuted',r.DIAG,('J',))):
            for seed in r.SEEDS:
                for arm in arms:
                    with np.load(base/'bank'/f'{seed}_{arm}_{r.stem(row)}.npz',allow_pickle=False) as z:
                        ee=error(truth,z['pose']) if bool(z['valid']) else None
                    records.append(dict(kind=mode,seed=seed,arm=arm,seq=row['seq'],t=row['t'],error=ee))
        with np.load(r.FULL/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:
            for arm in ('G3','KISS','identity'):
                if arm=='KISS' and row['seq']=='08':continue
                ee=error(truth,np.eye(4) if arm=='identity' else z[arm+'_pose'])
                records.append(dict(kind='reference',arm=arm,seq=row['seq'],t=row['t'],error=ee))
        r.cap()
    summary=summarize(records,f['rows'])
    c.save(r.EVAL/'bank/results.json',dict(utc=c.now(),records=records,summary=summary))
    c.save(r.EVAL/'bank.json',dict(utc=c.now(),metric_records=len(records),decision=summary['decision'],**r.usage()))
    r.seal(r.EVAL);r.finish('evaluation');print('RLP2 sealed evaluator result',summary['decision'],summary.get('cohort_medians'),flush=True)

if __name__=='__main__':
    try:{'freeze':freeze,'run':run}[sys.argv[1]]()
    except Exception as ex:r.fail('evaluation_'+sys.argv[1],ex);raise
