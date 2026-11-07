"""PEL0 surviving-local-source exposure census, no point/pose numerics."""
import time
START=time.monotonic()
import fnmatch
import json
import os
import resource
import signal
import subprocess
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
SLAM=s.SLAM
BASE=ROOT/'docs/maintenance/2026-10-14/poss-exposure-lineage-01'
SUP=BASE/'supervision'
PCC=ROOT/'docs/maintenance/2026-10-14/physical-comparison-contract-01/layout-attempt-02'
BRF=ROOT/'docs/maintenance/2026-10-14/bounded-native-residual-feasibility-01'
POSS=SLAM/'data/poss/dataset'
PATTERNS=('source_frames.json','run_manifest.json','summary.json','*manifest*.json','command.json')
SKIP=('2026-10-14','source_snapshot','source_staging')
read,sha=s.read,s.sha

def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())

def save(p,v):
    body=(json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<32*2**20
    with Path(p).open('xb') as stream:stream.write(body)

def output_roots():return sorted(p for p in SLAM.iterdir() if p.is_dir() and p.name.startswith('output'))

def discover(roots):
    found=[]
    for folder in roots:
        pending=[folder]
        while pending:
            current=pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False) and entry.name not in SKIP:
                        pending.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False) and any(fnmatch.fnmatchcase(entry.name,p) for p in PATTERNS):
                        found.append(Path(entry.path))
    return sorted(set(found))

def freeze():
    assert read(BRF/'STATUS.json')['family_retired']
    roots=[ROOT/'docs/maintenance']+output_roots()
    candidates=discover(roots)
    assert 0<len(candidates)<=3000
    lengths=[p.stat().st_size for p in candidates]
    assert max(lengths)<=16*2**20 and sum(lengths)<=256*2**20
    files={str(p):sha(p) for p in candidates}
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'PREFREEZE_DISCOVERY_REPAIR.md',Path(__file__),
        Path(__file__).with_name('validate_poss_exposure_lineage.py'),
        Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
        PCC/'contract_audit.json',SLAM/'rap_slam/real_dataset.py']
    for folder in (s.BASE,PCC,BRF):
        paths += [folder/n for n in ('REPORT.md','STATUS.json','CHECKS.json','DELIVERY_SEAL.json')]
    paths += [POSS/n for n in ('poses/00.txt','sequences/00/calib.txt',
                              'sequences/00/times.txt','sequences/00/calib_readme.txt')]
    paths += sorted((BASE/'prefreeze-attempt01').iterdir())
    paths += sorted((SUP/'freeze').glob('*'))
    paths += [BASE/'FAILURE_freeze.json']
    for p in paths:files[str(p)]=sha(p)
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            name=('prefreeze01_' if 'prefreeze-attempt01' in p.parts else '')+p.name
            with (snap/name).open('xb') as stream:stream.write(p.read_bytes())
    save(BASE/'freeze.json',dict(files=files,repositories=s.repositories(),
        discovery_roots=[str(p) for p in roots],candidate_paths=[str(p) for p in candidates],
        candidate_bytes=sum(lengths),patterns=PATTERNS,excluded_directory_names=SKIP,
        caps=dict(Windows_seconds=900,RSS_bytes=512*2**20,GPU_bytes=0,dossier_bytes=32*2**20),
        no_full_history_access_or_independence_claim=True))
    save(BASE/'INCOMPLETE',dict(scope='PEL0',pending='source census/independent validation'))
    print('PEL0 frozen',len(files),'identities/',len(candidates),'candidate metadata files',flush=True)

def verify():
    f=read(BASE/'freeze.json')
    assert discover([Path(p) for p in f['discovery_roots']])==[Path(p) for p in f['candidate_paths']]
    assert output_roots()==[Path(p) for p in f['discovery_roots'][1:]]
    for p,h in f['files'].items():assert sha(p)==h,p
    assert s.repositories()==f['repositories']
    return f

def runs(values):
    rows=[]
    for value in sorted(set(values)):
        if rows and value==rows[-1][1]+1:rows[-1][1]=value
        else:rows.append([value,value])
    return rows

def poss_path(value):
    if not isinstance(value,str):return False
    text=value.replace('\\','/').lower()
    return '/data/poss/' in text or text.endswith('/data/poss')

def raw_id(value):
    if not poss_path(value):return None
    path=Path(value.replace('\\','/'))
    if path.suffix!='.bin' or path.parent.name!='velodyne' or path.parent.parent.name!='00':return None
    return int(path.stem) if path.stem.isdecimal() else None

def nodes(value):
    yield value
    if isinstance(value,dict):
        for k,v in value.items():
            yield k
            yield from nodes(v)
    elif isinstance(value,list):
        for child in value:yield from nodes(child)

def census():
    f=verify();evidence=[]
    actual_ids=set();bound_ids=set();configured_ids=set()
    for path in f['candidate_paths']:
        data=read(path)
        records=[]
        if isinstance(data,dict) and isinstance(data.get('source_frame_ids'),list):
            paths=data.get('scan_files',[])
            if paths and all(poss_path(p) for p in paths):
                ids=data['source_frame_ids']
                assert all(isinstance(i,int) and i>=0 for i in ids)
                assert len(ids)==len(paths) and ids==[raw_id(p) for p in paths]
                actual_ids.update(ids)
                records.append(dict(kind='ACTUAL_SOURCE_FRAME_MANIFEST',ids=ids))
        raw_ids=sorted({raw_id(n) for n in nodes(data) if isinstance(n,str) and raw_id(n) is not None})
        if raw_ids:
            bound_ids.update(raw_ids)
            records.append(dict(kind='BOUND_RAW_INPUT_IDENTITY',ids=raw_ids))
        for node in nodes(data):
            if not isinstance(node,dict) or not poss_path(node.get('real_root')):continue
            first,last,step=node.get('real_start'),node.get('real_end'),node.get('real_stride',1)
            if all(isinstance(x,int) for x in (first,last,step)) and 0<=first<=last and step>0:
                assert last-first<=100000
                ids=list(range(first,last+1,step));configured_ids.update(ids)
                records.append(dict(kind='CONFIGURED_RANGE_ONLY',ids=ids))
        if records:evidence.append(dict(path=path,sha256=f['files'][path],records=records))
        cap()
    folder=POSS/'sequences/00/velodyne'
    with os.scandir(folder) as entries:
        scans=sorted([[e.name,e.stat().st_size] for e in entries if e.is_file() and e.name.endswith('.bin')])
    prior=read(PCC/'contract_audit.json')['POSS_metadata'][0]['names_and_sizes']
    assert scans==prior
    current={int(Path(n).stem) for n,_ in scans}
    known=(actual_ids|bound_ids)&current
    configuration_only=(configured_ids-current.intersection(actual_ids|bound_ids))&current
    unknown=current-known-configuration_only
    categories=dict(known_source_exposure_or_binding=sorted(known),
        configured_only_execution_unproven=sorted(configuration_only),
        surviving_records_unclassified=sorted(unknown))
    tables=[]
    for name in ('poses/00.txt','sequences/00/calib.txt','sequences/00/times.txt','sequences/00/calib_readme.txt'):
        p=POSS/name;body=p.read_text()
        tables.append(dict(path=str(p),sha256=sha(p),nonempty_rows=sum(bool(x.strip()) for x in body.splitlines()),
                           lineage_text=body if p.name=='calib_readme.txt' else None))
    queries=[dict(relative_path=name,exists=(POSS/'sequences/00'/name).exists()) for name in s.QUERIES]
    result=dict(candidate_files=len(f['candidate_paths']),candidate_bytes=f['candidate_bytes'],
        evidence_files=len(evidence),evidence=evidence,current_scans=scans,
        current_contiguous_runs=runs(current),categories=categories,
        category_runs={name:runs(ids) for name,ids in categories.items()},
        category_counts={name:len(ids) for name,ids in categories.items()},
        actual_manifest_union_count=len(actual_ids),bound_input_union_count=len(bound_ids),
        configured_range_union_count=len(configured_ids),tables=tables,provenance_queries=queries,
        decision='BOUNDED_POSS_EXPOSURE_CENSUS_COMPLETE_NO_UNSEEN_CONFIRMATION_ADMISSION',
        all_surviving_historical_accesses_proven_complete=False,
        checkpoint_exclusion_or_physical_site_separation_authenticated=False,
        physical_pose_frame_or_sensor_timing_authenticated=False,
        new_model_solver_metrics_or_cohort=False)
    assert set().union(*(set(v) for v in categories.values()))==current
    assert sum(map(len,categories.values()))==len(current)==4170
    save(BASE/'source_census.json',result)
    save(BASE/'census_seal.json',dict(path='source_census.json',sha256=sha(BASE/'source_census.json')))
    verify();print('PEL0 source roles',json.dumps(result['category_counts']),flush=True)

def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    raw_or_reference_pose_numeric_values_parsed=False,model_calls=0,optimizer_calls=0)

def cap():
    u=usage();assert u['peak_RSS_bytes']<=512*2**20 and u['artifact_bytes']<32*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30

def run(stage):
    spent=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert spent<900
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('PEL0 aggregate cap')))
    signal.alarm(max(1,int(900-spent)));ok,error=False,None
    try:
        if stage in ('freeze','freeze02'):freeze()
        elif stage=='census':census()
        elif stage=='validate':
            import validate_poss_exposure_lineage as v
            v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)

if __name__=='__main__':run(sys.argv[1])
