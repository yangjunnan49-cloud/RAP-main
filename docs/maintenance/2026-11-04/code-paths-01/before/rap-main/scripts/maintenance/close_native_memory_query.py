"""Close NMQ0 query evidence, preserving old nullable failure and WPC0 gap."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import native_memory_validation02 as d

OLD,BASE=d.OLD,d.BASE
f=d.check();v=d.read(BASE/'validation.json');n=d.read(BASE/'native_queries.json')
assert v['passed'] and v['native_children']==3
assert all(r['final_peak_available'] for r in v['results'])
receipts=[];retries=gaps=0
expected=[(OLD/'supervision','freeze',True),(OLD/'supervision','exercise',True),
    (OLD/'supervision','validate',False),(BASE/'supervision','bind',True),(BASE/'supervision','validate',True)]
for sup,stage,success in expected:
    q=sup/stage
    child,windows,launch=[d.read(q/name) for name in ('child_exit.json','exit.json','launch.json')]
    assert child['success'] is success and child['full_resource_capture']
    assert windows['exit_code']==(0 if success else 1) and child['peak_RSS_bytes']<=128*2**20
    assert child['peak_GPU_allocated_bytes']==child['peak_GPU_reserved_bytes']==0
    samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert len(samples)==windows['host_memory_observations']>0
    assert min(r['headroom_bytes'] for r in samples)>=4*2**30 and launch['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            if name.startswith('logging_retry'):retries+=len((q/name).read_text().splitlines())
            else:gaps+=len((q/name).read_text().splitlines())
    receipts.append(dict(directory=str(q.relative_to(OLD)),child=child,Windows=windows,launch=launch))
assert {p.name for p in (OLD/'supervision').iterdir() if p.is_dir()}=={'freeze','exercise','validate'}
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}=={'bind','validate'}
seconds=sum(r['Windows']['wall_seconds'] for r in receipts)
child_seconds=sum(r['child']['wall_seconds'] for r in receipts)
assert seconds<=300
peak=max(r['child']['peak_RSS_bytes'] for r in receipts)
assert n['observer_to_snapshot']['peak_working_set']<=256*2**20
running=sum(r['running_query_count'] for r in n['cases'])
assert running==69 and sum(r['running_query_failures'] for r in n['cases'])==0
assert all(r['refreshed_dotnet']['success'] and r['refreshed_dotnet']['peak_working_set'] is None for r in n['cases'])
status='VALIDATED_DIRECT_NATIVE_PEAK_QUERY_CONTROL_COMPLETE_OBSERVER_LIFETIME_UNKNOWN'


def save(name,value):d.save(BASE/name,value)


save('RESOURCE_AUDIT.json',dict(declared_scoped_checks_passed=True,receipts=receipts,
    outer_attempts=5,outer_successes=4,retained_original_nullable_validator_failure=1,
    Windows_seconds_including_startup_imports=seconds,Linux_child_seconds_after_time_bootstrap=child_seconds,
    Linux_peak_RSS_bytes=peak,GPU_bytes=0,native_children=3,native_child_final_peaks=[r['post_exit_queries'][0]['peak_working_set'] for r in n['cases']],
    native_child_wall_seconds_nested_not_added=sum(r['wall_seconds'] for r in n['cases']),
    observer_observed_to_snapshot_peak_bytes=n['observer_to_snapshot']['peak_working_set'],
    observer_complete_lifetime_peak_known=False,full_all_native_resource_guarantee=False,
    all69_running_and6_final_OS_query_results_recorded=True,new_OS_query_failures=0,
    new_outer_logging_retries=retries,new_outer_logging_gaps=gaps,
    old_WPC0_query_gap_count_still_unknown=True,ordinary_preparation_RSS_unknown=True,stdlib_closure_separate=True))
save('CHECKS.json',dict(passed=True,frozen_identities=len(f['files']),native_children=3,
    running_queries=69,final_queries=6,self_query=1,refreshed_dotnet_null_observations=3,
    exact_nullable_AST_assertion_change=1,output_route_change=1,no_native_replay_by_repair=True,
    old_WPC0_gate_repaired=False,observer_full_lifetime_peak_known=False))
save('FINAL_IDENTITY_CHECK.json',dict(passed=True,repositories=f['repositories'],frozen_identities=len(f['files']),
    original_failure_source_freeze_and_INCOMPLETE_preserved=True,all_old_caps_markers_and_unknowns_retained=True))
save('STATUS.json',dict(status=status,decision=v['decision'],original_NMQ0_INCOMPLETE_retained=True,
    old_WPC0_complete_resource_gate_repaired=False,observer_full_lifetime_peak_known=False,
    production_or_supervisor_integration=False))
report='\n'.join([
    '# NMQ0 Direct Native Peak Query Controls','',
    'Decision: DIRECT_FINAL_NATIVE_PEAK_AVAILABLE_IN_FIXED_CONTROLS. This '
    'closes only the new observation/interpretation control; the observer '
    'full-lifetime peak and old WPC0 missing-query history remain unknown.','',
    'New baseline/early64MiB touch/late64MiB touch children each exit0. A native '
    'handle is retained through two post-exit GetProcessMemoryInfo calls '
    'around an explicit Process.Refresh. Their final OS peaks are respectively '
    '91844608/168058880/164286464bytes, each identical on both final queries '
    'and not below any successful running query.69 running queries plus6 '
    'post-exit queries are recorded with return/error/field values; all75 '
    'return success. One observer self-query is separately retained. ABI '
    'structure is72bytes on64bit. Win32 errors are interpreted only on failure.','',
    'All3 refreshed .NET PeakWorkingSet64 accesses return null without an '
    'exception under the PowerShell expression used. The source success flag '
    'means no exception, not a usable numeric measurement. Null is not zero '
    'memory or evidence of OS counter failure. Original independent validator '
    'incorrectly assumed success implied numeric and raised TypeError. Its '
    'source/freeze/failure/full receipts/INCOMPLETE remain. Separate validator '
    'AST changes exactly one null-or-nonnegative interpretation assertion '
    'and one output route. Native observations are copied byteexact, no child '
    'or memory query rerun, no source/cap/scientific criterion amendment.','',
    'Independent validation rebuilds every query count/conditional denominator '
    'and final-peak predicate. The baseline passed the prospective gate, so '
    'both burst controls ran; no favorable case was selected afterward. '
    'These3 children have final OS peak observations under256MiB. That is '
    'new API behavior evidence, not a reconstruction of WPC0 or old gaps.','',
    f'All{len(f["files"])} frozen identities match. Five enclosing attempts/'
    f'four successes/one retained validator failure: Windows{seconds:.9f}s '
    f'incl startup/imports,Linux-child{child_seconds:.9f}s after bootstrap, '
    f'Linux peakRSS{peak}bytes/GPU0. Original300s/128MiB Linux/8MiB dossier '
    'and conditional256MiB final-child checks pass. Observer peak174235648bytes '
    'is observed-to-snapshot only, under its prospectively declared observed '
    '256MiB guard; its complete lifetime peak is UNKNOWN, not a full all-native '
    f'cap guarantee. New outer{retries} logging retries/{gaps} gaps; new OS '
    'query failures0 with all returns recorded. Old WPC0 query gaps unknown '
    'and ordinary setup RSS unknown remain. Nested Windows observer/child '
    'durations are already within enclosing intervals, not added again.','',
    'No production/current-supervisor integration or Windows memory-statistics '
    'behavior guarantee for arbitrary children/handles/access rights. No '
    'resource record is backfilled into old runs. No RAP/model/fit/archive/'
    'metric/reference/default/backbone/manuscript/acquisition/install/restart/'
    'commit/Git sync; all old scientific stops and09 unknown remain.'
])
with (BASE/'REPORT.md').open('x',encoding='utf-8') as out:out.write(report+'\n')
with (BASE/'source_snapshot/closure_close_native_memory_query.py').open('xb') as out:out.write(Path(__file__).read_bytes())
save('BOOKKEEPING.json',dict(stdlib_only=True,no_native_or_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert d.read(BASE/'INCOMPLETE')['scope']=='NMQ0_NULLABLE02';(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=d.sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
save('DELIVERY_SEAL.json',dict(status=status,entries=len(files),files=files,
    artifact_bytes_before_seal=d.size(),original_failure_and_INCOMPLETE_retained=True))
assert d.size()<8*2**20
print(json.dumps(dict(status=status,entries=len(files),Windows_seconds=seconds,
    Linux_child_seconds=child_seconds,bytes=d.size())),flush=True)
