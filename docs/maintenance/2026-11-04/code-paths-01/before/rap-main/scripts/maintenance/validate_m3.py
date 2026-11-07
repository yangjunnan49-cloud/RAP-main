"""Focused measurement regressions and non-destructive legacy quality audit."""
import json
import hashlib
import sys
from pathlib import Path
import numpy as np

ROOT=Path('/mnt/e/githouse/RAP-SLAM')
sys.path.insert(0,str(ROOT))
from rap_slam.measurement import *

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    checks=[]
    def reject(name,fn):
        try:fn()
        except ValueError:checks.append(name)
        else:raise AssertionError(name)
    identity=np.eye(4);wrong=identity.copy();wrong[0,3]=50
    gens=[dict(overlap=.9,mean_dist=2,T_rel=wrong),dict(overlap=.8,mean_dist=1,T_rel=identity)]
    assert best_generation(gens)==0
    record=make_measurement('test','kitti','02',[100,500],0,gens[0],identity,{})
    assert record['mean_dist']==2 and record['labels']['label']=='dangerous'
    checks.append('same_generation_metrics_and_label')
    other=make_measurement('test','kitti','02',[100,500],1,gens[1],identity,{})
    assert record['measurement_id']!=other['measurement_id'] and record['physical_pair_id']==other['physical_pair_id']
    checks.append('distinct_generation_common_physical_pair')
    assert pair_id('kitti','02',[100,500])==pair_id('kitti','02',[500,100])
    assert pair_id('kitti','02',[100,500])!=pair_id('kitti','06',[100,500])
    checks.append('reversed_pairs_and_physical_sequences')
    assert transform_label(wrong,wrong)['label']=='safe' and transform_label(wrong,wrong)['place_label']=='far'
    checks.append('place_proximity_not_pose_label')
    invalid=identity.copy();invalid[0,0]=1.001
    assert transform_label(invalid,identity)['label']=='unlabeled'
    assert transform_label(identity,None)['label']=='unlabeled'
    checks.append('invalid_rotation_and_missing_GT_never_borrow_labels')
    halfturn=identity.copy();halfturn[:3,:3]=np.diag([-1,-1,1])
    assert transform_label(halfturn,identity)['gt_rotation_error_deg']==180
    checks.append('rotation_halfturn')
    reject('empty_generation',lambda:best_generation([]))
    reject('nonfinite_diagnostics',lambda:best_generation([dict(overlap=.2,mean_dist=float('nan'))]))
    reject('negative_generation_id',lambda:make_measurement('test','kitti','02',[1,2],-1,gens[1],identity,{}))
    reject('fractional_generation_id',lambda:make_measurement('test','kitti','02',[1,2],.5,gens[1],identity,{}))
    reject('empty_run_id',lambda:make_measurement('','kitti','02',[1,2],0,gens[1],identity,{}))
    from scripts.build_s1_features import main as legacy_main
    try:legacy_main()
    except RuntimeError:checks.append('legacy_assembler_cannot_overwrite_or_relabel')
    else:raise AssertionError('Legacy assembler remained active')
    rng=np.random.default_rng(8)
    descriptors={i:rng.uniform(1,4,(20,60)) for i in [0,50,100,200,300,400,500,700]}
    descriptors[700]=descriptors[500].copy()
    feats=historical_margin(100,500,list(descriptors),descriptors)
    assert feats['sc_competitor_ids']==[0,200,300]
    assert 500 not in feats['sc_competitor_ids'] and 700 not in feats['sc_competitor_ids']
    checks.append('SC_excludes_self_future_temporal_neighbors_and_same_site')
    reject('SC_incomplete_pool_rejected',lambda:historical_margin(100,500,[0,100],{100:descriptors[100],500:descriptors[500]}))
    assert historical_margin(100,500,[100],descriptors)['sc_margin'] is None
    checks.append('no_distinct_site_is_missing_not_zero')
    reject('SC_reversed_time_rejected',lambda:historical_margin(500,100,[],descriptors))
    records=[record,other]
    for i in range(30):
        records.append(make_measurement('test','kitti','02',[i,600+i],0,gens[1],identity,{}))
    split=grouped_split(records)
    groups={name:{r['physical_pair_id'] for r in records if r['measurement_id'] in ids} for name,ids in split['measurement_ids'].items()}
    assert not (groups['fit']&groups['test'] or groups['fit']&groups['calibration'] or groups['test']&groups['calibration'])
    assert grouped_split(list(reversed(records)))['assignments']==split['assignments']
    checks.append('group_splits_disjoint_and_order_independent')
    reject('duplicate_measurement_rejected',lambda:grouped_split([record,record]))
    # Audit exact historical bytes; do not regenerate labels from another measurement.
    mg_path=ROOT/'output_multigen/multigen_samples.json'
    candidates_path=ROOT/'output_s1/candidates.json'
    entries=json.loads(mg_path.read_text())['entries']
    legacy=json.loads(candidates_path.read_text())
    rows=[]
    for entry in entries:
        best=best_generation(entry['gens'])
        chosen=entry['gens'][best]
        rows.append(dict(key=entry['key'],selected_generation=best,
                         selected_mean_dist=chosen['mean_dist'],legacy_min_mean_dist=min(g['mean_dist'] for g in entry['gens']),
                         mixed_mean_dist=chosen['mean_dist']!=min(g['mean_dist'] for g in entry['gens']),
                         rotation=rotation_validity(chosen['T_rel'])))
    audit=dict(legacy_candidate_count=len(legacy),multigen_pair_count=len(rows),
               mixed_mean_dist_pairs=sum(r['mixed_mean_dist'] for r in rows),
               selected_nonrigid_transforms=sum(not r['rotation']['valid'] for r in rows),
               candidates_without_T_rel=sum('T_rel' not in r for r in legacy),
               selfmatch_signature=sum(r.get('sc_margin') is not None and abs(r['sc_margin']+r['sc_d1'])<1e-5 for r in legacy),
               policy='No relabeling by physical-pair join or GT proximity; nonrigid legacy transforms require new inference',
               source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [mg_path,candidates_path]},rows=rows)
    (out/'legacy_audit.json').write_text(json.dumps(audit,indent=2))
    (out/'validation.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2))
    print(json.dumps(dict(status='passed',checks=checks,legacy={k:v for k,v in audit.items() if k not in ['rows','source_hashes']}),indent=2))

if __name__=='__main__':main()
