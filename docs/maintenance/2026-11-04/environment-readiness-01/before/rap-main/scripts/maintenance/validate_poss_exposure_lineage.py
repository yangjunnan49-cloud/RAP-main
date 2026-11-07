"""Independent PEL0 discovery, historical source-ID and role reconstruction."""
import fnmatch
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/poss-exposure-lineage-01'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as stream:
        for body in iter(lambda:stream.read(65536),b''):h.update(body)
    return h.hexdigest()

def intervals(ids):
    ordered=sorted(set(ids));result=[];i=0
    while i<len(ordered):
        begin=ordered[i];end=begin;i+=1
        while i<len(ordered) and ordered[i]==end+1:end=ordered[i];i+=1
        result.append([begin,end])
    return result

def source(value):
    if not isinstance(value,str):return False
    p=value.replace('\\','/').lower()
    return '/data/poss/' in p or p.endswith('/data/poss')

def scan_id(value):
    if not source(value):return None
    chunks=value.replace('\\','/').split('/')
    if len(chunks)<3 or chunks[-2:] == []:return None
    name=chunks[-1]
    if chunks[-2]!='velodyne' or chunks[-3]!='00' or not name.endswith('.bin'):return None
    stem=name[:-4]
    return int(stem) if stem.isdecimal() else None

def flatten(value):
    stack=[value];all_nodes=[]
    while stack:
        node=stack.pop();all_nodes.append(node)
        if isinstance(node,dict):
            stack.extend(node.keys());stack.extend(reversed(list(node.values())))
        elif isinstance(node,list):stack.extend(reversed(node))
    return all_nodes

def validate():
    f=read(BASE/'freeze.json')
    found=[]
    for root in f['discovery_roots']:
        for folder,dirs,names in os.walk(root):
            dirs[:]=[n for n in dirs if n not in f['excluded_directory_names']]
            for n in names:
                if any(fnmatch.fnmatchcase(n,pattern) for pattern in f['patterns']):
                    found.append(str(Path(folder)/n))
    assert sorted(set(found))==f['candidate_paths']
    for p,h in f['files'].items():assert sha(p)==h,p
    seal=read(BASE/'census_seal.json');assert sha(BASE/seal['path'])==seal['sha256']
    c=read(BASE/'source_census.json');actual=set();bound=set();configured=set();evidence={}
    for path in f['candidate_paths']:
        data=read(path);parts=[]
        if isinstance(data,dict) and isinstance(data.get('source_frame_ids'),list):
            paths=data.get('scan_files',[])
            if paths and all(source(p) for p in paths):
                ids=data['source_frame_ids']
                assert ids==[scan_id(p) for p in paths]
                actual.update(ids);parts.append(dict(kind='ACTUAL_SOURCE_FRAME_MANIFEST',ids=ids))
        nodes=flatten(data)
        ids=sorted({scan_id(node) for node in nodes if isinstance(node,str) and scan_id(node) is not None})
        if ids:bound.update(ids);parts.append(dict(kind='BOUND_RAW_INPUT_IDENTITY',ids=ids))
        for node in nodes:
            if not isinstance(node,dict) or not source(node.get('real_root')):continue
            begin,end,step=node.get('real_start'),node.get('real_end'),node.get('real_stride',1)
            if all(isinstance(n,int) for n in (begin,end,step)) and 0<=begin<=end and step>0:
                ids=list(range(begin,end+1,step));configured.update(ids)
                parts.append(dict(kind='CONFIGURED_RANGE_ONLY',ids=ids))
        if parts:evidence[path]=parts
    assert set(evidence)=={r['path'] for r in c['evidence']}
    for record in c['evidence']:
        assert record['sha256']==f['files'][record['path']]
        canonical=lambda rows:sorted(json.dumps(r,sort_keys=True) for r in rows)
        assert canonical(record['records'])==canonical(evidence[record['path']])
    raw=ROOT.parent/'RAP-SLAM/data/poss/dataset/sequences/00/velodyne'
    metadata=sorted([[n,os.stat(raw/n).st_size] for n in os.listdir(raw)
                     if n.endswith('.bin') and os.path.isfile(raw/n)])
    assert metadata==c['current_scans']
    present={int(name[:-4]) for name,_ in metadata};assert len(present)==4170
    assert intervals(present)==c['current_contiguous_runs']
    known=present.intersection(actual.union(bound))
    possible=present.intersection(configured)-known
    unknown=present-known-possible
    categories=dict(known_source_exposure_or_binding=sorted(known),
        configured_only_execution_unproven=sorted(possible),surviving_records_unclassified=sorted(unknown))
    assert categories==c['categories']
    assert {k:intervals(v) for k,v in categories.items()}==c['category_runs']
    assert {k:len(v) for k,v in categories.items()}==c['category_counts']
    assert sum(len(v) for v in categories.values())==4170
    assert c['actual_manifest_union_count']==len(actual) and c['bound_input_union_count']==len(bound)
    assert c['configured_range_union_count']==len(configured)
    for r in c['tables']:
        assert sha(r['path'])==r['sha256']
        text=Path(r['path']).read_text()
        assert sum(bool(line.strip()) for line in text.splitlines())==r['nonempty_rows']
        if r['lineage_text'] is not None:assert text==r['lineage_text']
    names=('oxts','velodyne/timestamps.txt','velodyne/timestamps_start.txt',
        'velodyne/timestamps_end.txt','calib_velo_to_cam.txt','calib_imu_to_velo.txt',
        'calib_cam_to_cam.txt','tracklet_labels.xml','labels','archive_receipt.json')
    assert [r['relative_path'] for r in c['provenance_queries']]==list(names)
    for r in c['provenance_queries']:assert r['exists']==os.path.exists(raw.parent/r['relative_path'])
    assert c['decision']=='BOUNDED_POSS_EXPOSURE_CENSUS_COMPLETE_NO_UNSEEN_CONFIRMATION_ADMISSION'
    assert not c['all_surviving_historical_accesses_proven_complete']
    assert not c['checkpoint_exclusion_or_physical_site_separation_authenticated']
    assert not c['physical_pose_frame_or_sensor_timing_authenticated'] and not c['new_model_solver_metrics_or_cohort']
    result=dict(passed=True,decision=c['decision'],frozen_identities=len(f['files']),
        candidate_files=len(found),candidate_bytes=f['candidate_bytes'],evidence_files=len(evidence),
        current_scans=4170,current_contiguous_runs=c['current_contiguous_runs'],
        category_counts=c['category_counts'],category_runs=c['category_runs'],
        all_ID_unions_and_partition_denominators_verified=True,
        surviving_records_are_not_all_history_or_unseen_certificate=True,
        pose_numeric_or_model_metric_replay=False)
    with (BASE/'validation.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(result),flush=True)
