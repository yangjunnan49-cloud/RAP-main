"""Read-only four-scope identity/resource/process recount and handoff seal."""
import time
START=time.monotonic()
import json
import os
import resource
from datetime import datetime,timezone
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/continuation-handoff-04'
SCOPES=(
    ('PSR0','physical-source-role-feasibility-01',('freeze','inventory','validate')),
    ('PCC0','physical-comparison-contract-01/layout-attempt-02',('bind','audit','validate')),
    ('BRF0','bounded-native-residual-feasibility-01',('freeze','poses','validate_poses','census','validate_census')),
    ('PEL0','poss-exposure-lineage-01',('freeze','freeze02','census','validate')))
read,sha=s.read,s.sha

def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def census_linux():
    names={'physical_source_role_feasibility.py','physical_comparison_contract.py',
        'physical_comparison_layout02.py','bounded_native_residual_feasibility.py',
        'poss_exposure_lineage.py','close_physical_source_roles.py',
        'close_physical_comparison_contract.py','close_bounded_native_residual.py',
        'close_poss_exposure_lineage.py'}
    checked=arguments=disappeared=0;matches=[];unreadable=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal():continue
        try:
            argv=(p/'cmdline').read_bytes().split(b'\0')
            argv=[b.decode('utf-8',errors='replace') for b in argv if b]
            checked+=1;arguments+=len(argv)
            if int(p.name)==os.getpid():continue
            for arg in argv:
                if Path(arg.replace('\\','/')).name in names:
                    matches.append(dict(pid=int(p.name),matched_argument=arg))
        except (FileNotFoundError,ProcessLookupError):disappeared+=1
        except PermissionError:unreadable.append(int(p.name))
    result=dict(utc=datetime.now(timezone.utc).isoformat(),processes_seen=checked,
        arguments_checked=arguments,all_available_arguments_checked=True,
        disappeared_during_census=disappeared,unreadable_processes=unreadable,
        owned_payload_matches=matches,scope='current continuation driver/closure basenames; self excluded')
    save('PROCESS_CENSUS_LINUX.json',result)
    assert not matches and not unreadable,result
    return result

files={};references=0;scope_rows=[];receipts=[]
for name,rel,stages in SCOPES:
    folder=ROOT/'docs/maintenance/2026-10-14'/rel
    f=read(folder/'freeze.json');v=read(folder/'validation.json');seal=read(folder/'DELIVERY_SEAL.json')
    assert v['passed'] and read(folder/'CHECKS.json')['passed']
    for p,h in f['files'].items():
        if p in files:assert files[p]==h,p
        files[p]=h
    for row in seal['files']:
        p=folder/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
        files[str(p)]=row['sha256'];references+=1
    files[str(folder/'DELIVERY_SEAL.json')]=sha(folder/'DELIVERY_SEAL.json')
    for stage in stages:
        q=folder/'supervision'/stage
        c,w=[read(q/n) for n in ('child_exit.json','exit.json')]
        expected=not(name=='PEL0' and stage=='freeze')
        assert c['success']==expected and w['exit_code']==(0 if expected else 1)
        assert c['full_resource_capture'] and c['peak_RSS_bytes']<=512*2**20
        assert c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==0
        receipts.append(dict(scope=name,stage=stage,child=c,Windows=w))
    scope_rows.append(dict(scope=name,path=rel,freeze_entries=len(f['files']),delivery_entries=seal['entries'],
        status=read(folder/'STATUS.json'),resources=read(folder/'RESOURCE_AUDIT.json')))
old=ROOT/'docs/maintenance/2026-10-14/physical-comparison-contract-01'
oldseal=read(old/'ORIGINAL_AVAILABLE_SEAL.json')
for row in oldseal['files']:
    p=old/row['path'];assert sha(p)==row['sha256'];files[str(p)]=row['sha256']
files[str(old/'ORIGINAL_AVAILABLE_SEAL.json')]=sha(old/'ORIGINAL_AVAILABLE_SEAL.json')
for stage in ('freeze','audit'):
    q=old/'supervision'/stage;c,w=[read(q/n) for n in ('child_exit.json','exit.json')]
    assert c['success']==(stage=='freeze') and w['exit_code']==(0 if stage=='freeze' else 1)
    receipts.append(dict(scope='PCC0_original',stage=stage,child=c,Windows=w))
contract=read(old/'layout-attempt-02/contract_audit.json')
for p,h in contract['selected_current_bank_hashes'].items():
    if p in files:assert files[p]==h,p
    files[p]=h
for p,h in files.items():assert sha(p)==h,p
repos=s.repositories()
assert all(read(ROOT/'docs/maintenance/2026-10-14'/rel/'freeze.json')['repositories']==repos for _,rel,_ in SCOPES)
markers=[ROOT/'docs/maintenance'/p for p in s.MARKERS]+[old/'INCOMPLETE']
assert all(p.exists() for p in markers)
windows=read(BASE/'PROCESS_CENSUS_WINDOWS.json')
assert windows['all_available_arguments_checked'] and not windows['owned_payload_matches'] and not windows['unreadable_relevant_interpreters']
linux=census_linux()
assert len(receipts)==17 and sum(r['child']['success'] for r in receipts)==15
assert all(r['child']['full_resource_capture'] for r in receipts)
windows_seconds=sum(r['Windows']['wall_seconds'] for r in receipts)
child_seconds=sum(r['child']['wall_seconds'] for r in receipts)
save('IDENTITY_CHECKS.json',dict(passed=True,unique_current_frozen_available_delivery_and_bank_paths=len(files),
    scoped_delivery_references=references,original_PCC_available_references=oldseal['entries'],
    selected_old_bank_identities=408,files=files,repositories=repos,
    original_five_plus_original_PCC_INCOMPLETE=[str(p) for p in markers],
    scoped_no_owned_payload_processes=True,no_all_history_or_numerical_replay=True))
save('CHECKS.json',dict(passed=True,scope='stored identity/resource recount and scoped all-argument process census',
    completed_scopes=4,attempted_scientific_children=17,success=15,retained_failures=2,
    aggregate_Windows_seconds_including_startup_imports=windows_seconds,
    aggregate_child_seconds_after_time_bootstrap=child_seconds,
    peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),GPU_bytes=0,
    aggregate_is_not_a_new_or_amended_historical_cap=True,
    native_model_forwards_or_backwards=0,head_backwards=0,new_retained_updates_or_fits=0,
    new_reference_error_diagnostics=132,old_HFIT40_updates_unchanged=True,
    complete_new_system_or_physical_or_independent_confirmation_result=False,
    ordinary_preparation_RSS_unknown=True,all_old_gaps_and_caps_unchanged=True,
    scopes=scope_rows,receipts=receipts))
status='READ_ONLY_FOUR_SCOPE_AUTONOMOUS_CONTINUATION_HANDOFF_COMPLETE'
save('STATUS.json',dict(status=status,new_scientific_replay=False,
    no_scoped_owned_payload_processes=True,original_HFIT='INCOMPLETE_ARTIFACT_CAP',
    original_LCP='INCOMPLETE_TIME_CAP',original_PCC='INCOMPLETE_SOURCE_LAYOUT_STOP',
    BRF0='BOUNDED_NATIVE_BASE_FAMILY_CANNOT_MEET_STRONG_CONTROL_GATES',
    next='DESIGN_ONLY_NEW_OBSERVABLE_SOURCE_AUTHENTICATION_AND_STRONG_CONTROL_CONTRACT',
    no_automatic_reset_resume=True,scientific_goal_complete=False))
snap=BASE/'source_snapshot';snap.mkdir()
for p in (ROOT/'AGENTS.md',ROOT/'docs/maintenance/2026-10-14/PHASE_RECORD.md',Path(__file__),
          Path(__file__).with_name('census_continuation_handoff04.ps1')):
    with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
save('BOOKKEEPING.json',dict(standard_library_only=True,stored_hash_resource_recount_not_science_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    Windows_startup_not_in_this_bookkeeping_timer=True,old_setup_RSS_unknown_retained=True))
entries=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size)
         for p in sorted(BASE.rglob('*')) if p.is_file()]
total=sum(p['bytes'] for p in entries);assert total<16*2**20
save('DELIVERY_SEAL.json',dict(status=status,entries=len(entries),files=entries,bytes_before_seal=total))
print(json.dumps(dict(status=status,identities=len(files),scoped_delivery_references=references,
    original_PCC_available_references=oldseal['entries'],handoff_entries=len(entries),
    Windows_seconds=windows_seconds,child_seconds=child_seconds,
    peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),scoped_payload_processes=0)),flush=True)
