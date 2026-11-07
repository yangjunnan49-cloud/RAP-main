"""Six-scope current-window identity/resource/claim-boundary handoff audit."""
import time
START=time.monotonic()
import ast
import json
import os
import resource
import sys
from datetime import datetime,timezone
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/continuation-handoff-05'
DAY=BASE.parent
SCOPES=(('POP0','poss-outcome-provenance-01/layout-attempt-02','DELIVERY_SEAL.json'),
    ('FTI0','frame-time-identifiability-01','DELIVERY_SEAL.json'),
    ('BEJ0','bounded-evidence-journal-01','DELIVERY_SEAL.json'),
    ('BPC0','bounded-pipe-capture-01','DELIVERY_SEAL.json'),
    ('WPC0','windows-pipe-capture-01','AVAILABLE_DELIVERY_SEAL.json'),
    ('NMQ0','native-memory-query-01/validation-attempt-02','DELIVERY_SEAL.json'))
NAMES={'poss_outcome_provenance.py','validate_poss_outcome_provenance.py','poss_outcome_layout02.py',
    'close_poss_outcome_provenance.py','frame_time_identifiability.py','validate_frame_time_identifiability.py',
    'close_frame_time_identifiability.py','bounded_evidence_journal.py','evidence_journal_control.py',
    'validate_evidence_journal.py','close_evidence_journal.py','bounded_pipe_capture.py','pipe_capture_fixture.py',
    'pipe_capture_control.py','validate_pipe_capture.py','close_pipe_capture.py','windows_pipe_fixture.ps1',
    'windows_pipe_capture_control.ps1','windows_pipe_control.py','validate_windows_pipe.py','audit_windows_pipe_stop.py',
    'native_memory_fixture.ps1','native_memory_probe.ps1','native_memory_control.py','validate_native_memory.py',
    'native_memory_validation02.py','close_native_memory_query.py'}
read,sha=s.read,s.sha


def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as out:
        json.dump(value,out,indent=2,allow_nan=False);out.write('\n')


def census_linux():
    checked=arguments=disappeared=0;matches=[];unreadable=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal():continue
        try:
            argv=[x.decode('utf-8',errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
            checked+=1;arguments+=len(argv)
            if int(p.name)==os.getpid():continue
            for arg in argv:
                if Path(arg.replace('\\','/')).name in NAMES:
                    matches.append(dict(pid=int(p.name),matched_argument=arg))
        except (FileNotFoundError,ProcessLookupError):disappeared+=1
        except PermissionError:unreadable.append(int(p.name))
    result=dict(utc=datetime.now(timezone.utc).isoformat(),processes_seen=checked,
        arguments_checked=arguments,all_available_arguments_checked=True,
        disappeared_during_census=disappeared,unreadable_processes=unreadable,
        owned_payload_matches=matches,scope='27 resumed-scope basenames, self excluded; unrelated processes not classified')
    save('PROCESS_CENSUS_LINUX.json',result)
    assert not matches and not unreadable
    return result


def gather():
    files={};refs=0;available_refs=0;rows=[];receipts=[]
    def add(path,digest):
        path=str(path)
        if path in files:assert files[path]==digest,path
        files[path]=digest
    for name,relative,sealname in SCOPES:
        folder=DAY/relative
        f,seal,status,resources=[read(folder/n) for n in ('freeze.json',sealname,'STATUS.json','RESOURCE_AUDIT.json')]
        for path,row in f['files'].items():add(path,row['sha256'])
        for row in seal['files']:
            p=folder/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
            add(p,row['sha256']);refs+=1
        add(folder/sealname,sha(folder/sealname))
        assert seal['entries']==len(seal['files'])
        assert read(folder/'validation.json')['passed']
        if name=='WPC0':
            assert not resources['complete_resource_gate_passed'] and (folder/'INCOMPLETE').exists()
            assert not read(folder/'CHECKS.json')['complete_resource_gate_passed']
        else:assert read(folder/'CHECKS.json')['passed']
        for record in resources['receipts']:
            assert record['child']['full_resource_capture']
            assert record['child']['peak_GPU_allocated_bytes']==record['child']['peak_GPU_reserved_bytes']==0
            assert record['Windows']['exit_code']==(0 if record['child']['success'] else 1)
            receipts.append(dict(scope=name,**record))
        rows.append(dict(scope=name,path=relative,frozen_identities=len(f['files']),
            delivery_kind=sealname,delivery_entries=seal['entries'],status=status,resources=resources))
    for relative in ('poss-outcome-provenance-01','native-memory-query-01'):
        folder=DAY/relative;seal=read(folder/'ORIGINAL_AVAILABLE_SEAL.json')
        for row in seal['files']:
            p=folder/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
            add(p,row['sha256']);available_refs+=1
        add(folder/'ORIGINAL_AVAILABLE_SEAL.json',sha(folder/'ORIGINAL_AVAILABLE_SEAL.json'))
    markers=[ROOT/'docs/maintenance'/p for p in s.MARKERS]
    markers += [DAY/p/'INCOMPLETE' for p in ('physical-comparison-contract-01','poss-outcome-provenance-01',
                                                   'windows-pipe-capture-01','native-memory-query-01')]
    assert len(markers)==9 and all(p.exists() for p in markers)
    for p in markers:add(p,sha(p))
    source_reports=(
        '2026-10-08/motion-supervised-readout-01/REPORT.md',
        '2026-10-05/flow-directional-information-01/REPORT.md',
        '2026-10-07/geometric-information-screen-01/REPORT.md',
        '2026-10-12/reference-physical-consistency-01/REPORT.md',
        '2026-10-12/causal-context-registration-01/REPORT.md',
        '2026-10-13/geometry-signature-control-01/REPORT.md',
        '2026-10-14/bounded-native-residual-feasibility-01/REPORT.md')
    for relative in source_reports:
        p=ROOT/'docs/maintenance'/relative;add(p,sha(p))
    for p,h in files.items():assert sha(p)==h,p
    repos=s.repositories();assert all(read(DAY/rel/'freeze.json')['repositories']==repos for _,rel,_ in SCOPES)
    assert len(receipts)==22 and sum(r['child']['success'] for r in receipts)==20
    summary=dict(scopes=6,unique_frozen_available_delivery_and_report_paths=len(files),
        scoped_delivery_or_available_references=refs,original_available_references=available_refs,
        outer_attempts=22,outer_exit_successes=20,retained_original_implementation_or_validator_failures=2,
        aggregate_Windows_seconds_including_startup_imports=sum(r['Windows']['wall_seconds'] for r in receipts),
        aggregate_outer_Linux_child_seconds_after_time_bootstrap=sum(r['child']['wall_seconds'] for r in receipts),
        peak_outer_Linux_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),GPU_bytes=0,
        nested_Linux_fixtures=8,nested_Windows_fixtures=11,nested_Windows_observers=2,
        nested_intervals_already_enclosed_not_added_twice=True,
        WPC0_complete_native_resource_gate_passed=False,NMQ0_observer_complete_lifetime_peak_known=False,
        no_all_native_zero_gap_or_all_native_cap_claim=True,no_aggregate_historical_cap_amendment=True)
    return summary,files,rows,receipts,repos,markers


summary,files,rows,receipts,repos,markers=gather()
if '--preview' in sys.argv:
    print(json.dumps(summary),flush=True);sys.exit(0)
windows=read(BASE/'PROCESS_CENSUS_WINDOWS.json')
assert windows['all_available_arguments_checked'] and not windows['owned_payload_matches'] and not windows['unreadable_relevant_interpreters']
linux=census_linux()
save('IDENTITY_CHECKS.json',dict(passed=True,files=files,repositories=repos,
    retained_INCOMPLETE_paths=[str(p) for p in markers],**summary))
save('CHECKS.json',dict(passed=True,scope='read-only current identity/resource/claim boundary and all-argument process census',
    six_scoped_outcomes_verified=True,all_old_failures_and_unknowns_preserved=True,
    scoped_owned_payload_matches=0,new_model_backward_fit_metric_or_trajectory_calls=0,
    scopes=rows,receipts=receipts,**summary))
status='READ_ONLY_SIX_SCOPE_EXPLICIT_RESUME_HANDOFF_COMPLETE_WITH_RESOURCE_STOPS_PRESERVED'
save('STATUS.json',dict(status=status,scientific_goal_complete=False,quota_stop_not_goal_completion=True,
    no_automatic_quota_reset_resume=True,no_owned_scoped_payload_processes=True,
    WPC0='INCOMPLETE_FULL_NATIVE_RESOURCE_GATE_UNPROVEN',
    NMQ0_original='INCOMPLETE_NULLABLE_VALIDATOR_FAILURE_RETAINED',
    NMQ0_validation02='VALIDATED_DIRECT_FINAL_QUERY_CONTROL_OBSERVER_LIFETIME_UNKNOWN',
    next='DESIGN_ONLY_DISTINCT_OBSERVABLE_AND_AUTHENTICATED_SOURCE_STRONG_CONTROL_CONTRACT'))
snap=BASE/'source_snapshot';snap.mkdir()
for p in (ROOT/'AGENTS.md',DAY/'PHASE_RECORD.md',Path(__file__),Path(__file__).with_name('census_continuation_handoff05.ps1')):
    with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
syntax=[]
for p in sorted({Path(path) for path in files if Path(path).suffix=='.py'}|{Path(__file__)}):
    ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    syntax.append(dict(path=str(p),sha256=sha(p)))
save('PYTHON_SYNTAX_CHECKS.json',dict(passed=True,files=syntax,syntax_only_not_behavioral_test=True))
save('BOOKKEEPING.json',dict(stdlib_only=True,no_model_or_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    Windows_startup_outside_bookkeeping_timer=True,ordinary_setup_RSS_unknown=True,
    initial_sandbox_CIM_census_attempt_failed_before_output=True,
    initial_CIM_tool_exit=1,initial_CIM_tool_reported_wall_seconds=1.0568209,
    census_retry_requires_normal_approved_read_only_escalation=True,
    preparation_failure_not_a_scientific_child_or_zero_RSS_claim=True))
entries=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size)
         for p in sorted(BASE.rglob('*')) if p.is_file()]
assert sum(r['bytes'] for r in entries)<16*2**20
save('DELIVERY_SEAL.json',dict(status=status,entries=len(entries),files=entries,
    bytes_before_seal=sum(r['bytes'] for r in entries)))
print(json.dumps(dict(status=status,handoff_entries=len(entries),**summary)),flush=True)
