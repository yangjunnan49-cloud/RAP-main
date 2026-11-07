"""H06 read-only four-scope closure audit, no network/model/point decoding."""
import json
from pathlib import Path
import physical_source_role_feasibility as s
import demo_source_roles as ds

ROOT=s.ROOT
DAY=ROOT/'docs/maintenance/2026-10-15'
BASE=DAY/'continuation-handoff-06'
SCOPES=('public-release-identity-01/identity-attempt-02','demo-source-role-01/source-attempt-02',
 'release-backend-attribution-01','official-demo-metadata-01')


def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    references={};delivery_refs=0;available_refs=0;resources=[]
    def bind(q,sha,bytes):
        key=str(q);row=dict(sha256=sha,bytes=bytes)
        if key in references:assert references[key]==row
        references[key]=row
    for name in SCOPES:
        folder=DAY/name;f=s.read(folder/'freeze.json')
        for q,row in f['files'].items():bind(Path(q),row['sha256'],row['bytes'])
        seal=s.read(folder/'DELIVERY_SEAL.json')
        for row in seal['files']:
            bind(folder/row['path'],row['sha256'],row['bytes']);delivery_refs+=1
        q=folder/'DELIVERY_SEAL.json';bind(q,s.sha(q),q.stat().st_size)
        if (folder/'ORIGINAL_AVAILABLE_SEAL.json').exists():
            for rel,row in s.read(folder/'ORIGINAL_AVAILABLE_SEAL.json')['files'].items():
                bind(folder.parent/rel,row['sha256'],row['bytes']);available_refs+=1
        for binding in ('WINDOWS_BINDING.json','ENTRY02_BINDING.json'):
            if (folder/binding).exists():
                for q,row in s.read(folder/binding)['files'].items():bind(Path(q),row['sha256'],row['bytes'])
        r=s.read(folder/'RESOURCE_AUDIT.json');resources.append(dict(scope=name,**r))
        assert s.read(folder/'CHECKS.json')['passed'] and not (folder/'INCOMPLETE').exists()
    for name,row in references.items():
        q=Path(name);assert q.stat().st_size==row['bytes'] and s.sha(q)==row['sha256']
    repositories=s.repositories()
    assert repositories==s.read(DAY/SCOPES[0]/'freeze.json')['repositories']
    markers=[ROOT/'docs/maintenance'/q for q in ds.MARKERS]+[DAY/'demo-source-role-01/INCOMPLETE']
    assert len(markers)==10
    for q in markers:assert q.exists() and str(q) in references
    windows=s.read(BASE/'WINDOWS_PROCESS_CENSUS.json');assert not windows['scoped_payload_matches']
    identifiers=set(windows['scoped_identifiers']);processes=readable=argv=0;unreadable=[];matches=[]
    for d in Path('/proc').iterdir():
        if not d.name.isdigit():continue
        processes+=1
        try:args=[v.decode(errors='replace') for v in (d/'cmdline').read_bytes().split(b'\0') if v]
        except (PermissionError,FileNotFoundError,ProcessLookupError):unreadable.append(d.name);continue
        readable+=1;argv+=len(args)
        for arg in args:
            if Path(arg.replace('\\','/')).name in identifiers:matches.append(dict(pid=d.name,argument=arg));break
    assert not matches
    save('LINUX_PROCESS_CENSUS.json',dict(processes=processes,readable=readable,argv=argv,unreadable=unreadable,
        scoped_payload_matches=matches,unrelated_tasks_absence_claim=False))
    attempts=sum(r['attempt_count'] for r in resources);successes=sum(r['successes'] for r in resources)
    wall=sum(r['total_Windows_seconds'] for r in resources);linux=sum(r['total_Linux_child_seconds'] for r in resources)
    peak=max(r['maximum_Linux_RSS_bytes'] for r in resources)
    assert attempts==17 and successes==14
    save('IDENTITY_CHECKS.json',dict(unique_paths=len(references),delivery_references=delivery_refs,
        original_available_references=available_refs,all_match=True,files=references,repositories=repositories,
        retained_markers=[str(q) for q in markers]))
    save('CHECKS.json',dict(passed=True,scopes=4,enclosing_attempts=attempts,successes=successes,retained_failures=3,
        total_Windows_seconds=wall,total_Linux_child_seconds=linux,maximum_Linux_RSS_bytes=peak,GPU_bytes=0,
        nested_Windows_child_peak_bytes=166621184,nested_interval_enclosed_not_added_twice=True,
        observer_full_lifetime_peak='UNKNOWN',all_native_or_process_tree_memory_cap_claim=False,
        ordinary_preparation_closure_RSS='UNKNOWN',historical_gaps_unchanged=True,
        official_metadata_body_bytes=1273695,owner_body_cap_bytes=4194304,retained_markers=10,
        no_new_model_backward_update_fit_solver_pose_metric_trajectory=True,
        original_repositories_preserved=True,no_owned_scoped_payload_processes=True,
        windows_unreadable_relevant_interpreters=windows['unreadable_relevant_interpreters']))
    save('STATUS.json',dict(status='READ_ONLY_FOUR_SCOPE_NEW_DAY_HANDOFF_COMPLETE_WITH_UNKNOWN_RESOURCE_BOUNDARIES_PRESERVED',
        scientific_goal_complete=False,all_scopes_closed=True,automatic_quota_reset_resume=False))
    snap=BASE/'source_snapshot';snap.mkdir()
    for q in (Path(__file__),ROOT/'scripts/maintenance/census_continuation_handoff06.ps1',ROOT/'AGENTS.md',DAY/'PHASE_RECORD.md'):
        with (snap/q.name).open('xb') as out:out.write(q.read_bytes())
    files=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=s.sha(q)) for q in sorted(BASE.rglob('*')) if q.is_file()]
    save('DELIVERY_SEAL.json',dict(files=files,status='READ_ONLY_FOUR_SCOPE_NEW_DAY_HANDOFF_COMPLETE'))
    print(json.dumps(dict(unique_paths=len(references),delivery_refs=delivery_refs,available_refs=available_refs,
        handoff_entries=len(files),attempts=attempts,successes=successes,Windows_seconds=wall,Linux_child_seconds=linux,
        Linux_RSS=peak,Windows_processes=windows['processes'],Linux_processes=processes)),flush=True)


if __name__=='__main__':main()
