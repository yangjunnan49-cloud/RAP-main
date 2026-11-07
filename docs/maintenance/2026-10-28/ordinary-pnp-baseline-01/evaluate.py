"""Reference-only readout after the complete200 prediction seal."""
import collections
import math
import statistics
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import numpy as np

OUT=lib.ROOT/'evaluate'


def summarize(rows,name):
    valid=[r for r in rows if r['status']=='POSE']
    r=[x['rotation_error_deg'] for x in valid];t=[x['translation_error_m'] for x in valid]
    d=[x['direction_error_deg'] for x in valid if x['direction_error_deg'] is not None]
    return {'group':name,'pairs':len(rows),'pose_outputs':len(valid),'no_evidence':len(rows)-len(valid),
        'status_counts':dict(collections.Counter(x['status'] for x in rows)),
        'rotation_translation_denominator':len(valid),'direction_denominator':len(d),
        'rotation_mean_deg':statistics.mean(r) if r else None,'rotation_median_deg':statistics.median(r) if r else None,
        'translation_mean_m':statistics.mean(t) if t else None,'translation_median_m':statistics.median(t) if t else None,
        'direction_mean_deg':statistics.mean(d) if d else None,'direction_median_deg':statistics.median(d) if d else None,
        'bin_denominator_all_pairs':len(rows),'bin_counts':{
            'R5_t2':sum(x['rotation_error_deg']<=5 and x['translation_error_m']<=2 for x in valid),
            'R10_t5':sum(x['rotation_error_deg']<=10 and x['translation_error_m']<=5 for x in valid),
            'R5_d15':sum(x['rotation_error_deg']<=5 and x['direction_error_deg'] is not None and x['direction_error_deg']<=15 for x in valid),
            'R10_d30':sum(x['rotation_error_deg']<=10 and x['direction_error_deg'] is not None and x['direction_error_deg']<=30 for x in valid)}}


try:
    frozen=lib.verify_freeze('evaluation');seal=lib.verify_seal(lib.ROOT/'predict')
    assert lib.load(lib.ROOT/'predict/RESULT.json')['pairs']==200
    lib.save(OUT/'REFERENCE_READ_BEGIN.json',{'utc':lib.stamp(),'prediction_sealed_utc':seal['sealed_utc'],
        'prediction_seal_sha256':lib.sha(lib.ROOT/'predict/SEAL.json'),'complete_predictions':200})
    binding=lib.load(lib.ROOT/'EVALUATION_INPUTS.json');inputs=lib.load(lib.ROOT/'PREDICTION_INPUTS.json')
    predictions=lib.load(lib.ROOT/'predict/PREDICTIONS.json');method=lib.load(lib.ROOT/'METHOD.json')
    assert [r['key'] for r in predictions]==[r['key'] for r in inputs['pairs']]
    tables={};labels={};precision={}
    for entry in binding['poses']:
        path=Path(entry['path']);assert path.stat().st_size==entry['bytes'] and lib.sha(path)==entry['sha256']
        values=np.loadtxt(path,dtype=np.float64);assert values.shape==({'00':4541,'08':4071}[entry['sequence']],12) and np.isfinite(values).all()
        table=np.tile(np.eye(4),(len(values),1,1));table[:,:3]=values.reshape(-1,3,4);tables[entry['sequence']]=table
        ids=sorted({int(p[f]) for p in inputs['pairs'] if p['sequence']==entry['sequence'] for f in ('source_i','source_j')})
        rotations=table[ids,:3,:3];orth=float(np.max(np.abs(np.swapaxes(rotations,1,2)@rotations-np.eye(3))))
        det=float(np.max(np.abs(np.linalg.det(rotations)-1)));assert max(orth,det)<1e-5
        precision[entry['sequence']]={'selected_reference_RtR_deviation':orth,'selected_reference_det_deviation':det,'no_projection':True}
    for entry in binding['labels']:
        path=Path(entry['path']);assert lib.sha(path)==entry['sha256']
        for row in lib.load(path):
            key='%s_%s_%s'%(row['sequence'],row['source_i'],row['source_j']);assert key not in labels;labels[key]=row['stratum']
    assert set(labels)=={p['key'] for p in predictions}
    rows=[]
    for pred in predictions:
        table=tables[pred['sequence']];q=np.linalg.solve(table[int(pred['source_j'])],table[int(pred['source_i'])])
        assert np.array_equal(q[3],[0.,0.,0.,1.]) and np.max(np.abs(q[:3,:3].T@q[:3,:3]-np.eye(3)))<1e-5
        r,t,d=None,None,None
        if pred['status']=='POSE':
            unit=pred['unit_t_i_to_j'];rotation=np.asarray(pred['R_i_to_j']);translation=np.asarray(pred['t_i_to_j_m'])
            r,d0=lib.angles(np,rotation,np.asarray(unit) if unit is not None else np.array([1.,0.,0.]),q,method['translation_epsilon_m'])
            d=d0 if unit is not None else None;t=float(np.linalg.norm(translation-q[:3,3]))
            assert math.isfinite(r) and math.isfinite(t) and (d is None or math.isfinite(d))
        rows.append({**{k:pred[k] for k in ('key','sequence','source_i','source_j','status','input_hypotheses','native_inliers','verified_inliers')},
            'stratum':labels[pred['key']],'reference_Q_i_to_j':q.tolist(),
            'reference_translation_norm_m':float(np.linalg.norm(q[:3,3])),
            'rotation_error_deg':r,'translation_error_m':t,'direction_error_deg':d})
    groups=[summarize(rows,'all200')]
    for seq in ('00','08'):
        data=[r for r in rows if r['sequence']==seq];assert len(data)==100
        groups.append(summarize(data,seq+'/all100'))
        positive=[r for r in data if r['stratum']!='confuser'];confusers=[r for r in data if r['stratum']=='confuser']
        assert len(positive)==75 and len(confusers)==25
        groups.extend([summarize(positive,seq+'/positive75'),summarize(confusers,seq+'/confuser25')])
        for stratum in sorted({r['stratum'] for r in data}):
            cell=[r for r in data if r['stratum']==stratum];assert len(cell)==25;groups.append(summarize(cell,seq+'/'+stratum))
    lib.save(OUT/'ROWS.json',rows);lib.save(OUT/'SUMMARY.json',{'groups':groups,'reference_precision':precision,
        'role':'Exposed supplied-reference numerical camera metric-pose comparison, no corrected-LiDAR equivalence or physical/RAP claim'})
    lib.complete(OUT,{'pairs':200,'source_freeze_sha256':frozen,'prediction_before_reference':True})
    print('PR1 evaluation complete200/200')
except BaseException as error:
    lib.failure(OUT,error);raise
