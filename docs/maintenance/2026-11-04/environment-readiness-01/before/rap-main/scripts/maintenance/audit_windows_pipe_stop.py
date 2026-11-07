"""Seal WPC0 available byte controls without claiming complete native peaks."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import windows_pipe_control as d

BASE=d.BASE
f=d.verify();v=d.read(BASE/'validation.json');n=d.read(BASE/'native_controller.json')
assert v['passed'] and n['success']
source=d.NATIVE.read_text()
assert source.count('catch{}')==2
assert '$process.Refresh()' in source and '$process.WaitForExit();$reaped=$true' in source
receipts=[];retries=gaps=0
for stage in ('freeze','exercise','validate'):
    q=BASE/'supervision'/stage
    child,windows,launch=[d.read(q/name) for name in ('child_exit.json','exit.json','launch.json')]
    assert child['success'] and child['full_resource_capture'] and windows['exit_code']==0
    assert child['peak_RSS_bytes']<=128*2**20
    assert child['peak_GPU_allocated_bytes']==child['peak_GPU_reserved_bytes']==child['old_model_archive_or_fit_calls']==0
    samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert len(samples)==windows['host_memory_observations']>0
    assert min(row['headroom_bytes'] for row in samples)>=4*2**30 and launch['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            if name.startswith('logging_retry'):retries+=len((q/name).read_text().splitlines())
            else:gaps+=len((q/name).read_text().splitlines())
    receipts.append(dict(stage=stage,child=child,Windows=windows,launch=launch))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}=={'freeze','exercise','validate'}
seconds=sum(row['Windows']['wall_seconds'] for row in receipts)
child_seconds=sum(row['child']['wall_seconds'] for row in receipts)
assert seconds<=600
status='AUDITED_WINDOWS_PIPE_BYTE_CONTROLS_PASS_NATIVE_PEAK_COMPLETENESS_STOP'
d.save('RESOURCE_AUDIT.json',dict(complete_resource_gate_passed=False,receipts=receipts,
    outer_attempts=3,outer_exit_successes=3,inner_Windows_children=8,
    Windows_seconds_including_startup_imports=seconds,Linux_child_seconds_after_time_bootstrap=child_seconds,
    Linux_driver_peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),
    native_controller_observed_peak_working_set_bytes=n['peak_working_set_bytes'],
    maximum_inner_observed_peak_working_set_bytes=max(r['peak_working_set_bytes'] for r in n['cases']),
    inner_wall_seconds_nested_not_added=sum(r['wall_seconds'] for r in n['cases']),
    GPU_bytes=0,outer_logging_retries=retries,outer_logging_gaps=gaps,
    native_stat_query_failures_or_staleness_completeness='UNKNOWN',
    native_stat_query_failures_count=None,full_lifetime_native_working_set_cap_proven=False,
    actual_native_cap_exceedance_proven=False,ordinary_preparation_RSS_unknown=True,stdlib_audit_separate=True))
d.save('CHECKS.json',dict(binary_pipe_and_native_exit_checks_passed=True,
    complete_resource_gate_passed=False,cases=8,native_child_exit_records=8,
    cooperating_case_envelope_bytes=3072,source_silent_query_catches=2,
    full_native_peak_and_stat_query_logging_unproven=True))
d.save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=f['repositories'],original_sources_and_all_evidence_unchanged=True,
    WPC0_INCOMPLETE_retained=True,old_markers_and_caps_unchanged=True))
d.save('STATUS.json',dict(status=status,byte_controls_complete=True,resource_gate_complete=False,
    native_peak_completeness_unproven=True,INCOMPLETE_retained=True,
    old_source_or_production_retry=False))
report='\n'.join([
    '# WPC0 Windows Byte Controls And Resource Stop','',
    'Decision: '+status+'. Byte/native-exit validation passes, but the complete '
    'native working-set gate is NOT established. Keep WPC0 INCOMPLETE.','',
    'All8 fixed Windows children have native exit codes, pipe EOF and binary '
    'journal/terminal files within3072 cooperating bytes. Normal/empty/binary '
    'cases are byte-admitted; three overflows/exit7/timeout are not. Original '
    'validation.json records these local assertions; it is not a certificate '
    'of complete native resource capture or successful whole-scope admission.','',
    'Source review found two empty catch blocks around native memory/CPU '
    'queries. The loop uses Process.Refresh(), but post-exit peak access is '
    'not independently shown fresh; query failures and final-observation '
    'coverage were not logged. Process-group property caching is documented '
    'by Microsoft; without explicit final-query evidence the maximum observed '
    'PeakWorkingSet64 is not admitted as the full-lifetime peak. No specific '
    'number of actual query failures, unique cause, or real cap overrun is '
    'inferred. This is a completeness stop, not a measured cap exceedance.','',
    'Native controller observed peak126459904bytes; the individual observed '
    'peaks are retained in native_controller.json. These observed values '
    'remain descriptive, not proof of the original256MiB full-lifetime caps. '
    'The original frozen source, scope, validator, all8 outcomes and receipts '
    'remain unchanged; no threshold downgrade or rerun makes the original '
    'resource gate pass.','',
    f'All{len(f["files"])} frozen identities match. Three successful enclosing '
    f'commands take Windows{seconds:.9f}s incl startup/imports, '
    f'Linux-child{child_seconds:.9f}s after bootstrap. Linux-driver RSS'
    f'{max(r["child"]["peak_RSS_bytes"] for r in receipts)}bytes/GPU0; '
    'time/Linux-RSS/new-dossier caps pass. Full outer native/Windows exits/'
    f'host samples,{retries} outer logging retries/{gaps} outer gaps. '
    'Native statistics query gap count/completeness UNKNOWN; it must not '
    'be merged into an all-native zero-gap claim. Nested Windows controller '
    'and8 child intervals are not added again to the enclosing duration. '
    'Ordinary setup RSS unknown/stdlib stop audit separate/old gaps unchanged.','',
    'Next separate DESIGN_ONLY question: can an explicitly retained native '
    'process handle and direct OS memory query return valid final peak '
    'statistics after exit, with every return/error recorded? No conclusion '
    'or retry is authorized by this report alone. No Windows supervisor/'
    'real-model/archive/fit integration, old LCP0/HFIT0 repair, physical/system '
    'gain or acquisition/install/reference/default/backbone/manuscript/'
    'restart/commit/Git sync.'
])
with (BASE/'REPORT.md').open('x',encoding='utf-8') as out:out.write(report+'\n')
with (BASE/'source_snapshot/audit_windows_pipe_stop.py').open('xb') as out:out.write(Path(__file__).read_bytes())
d.save('BOOKKEEPING.json',dict(stdlib_only=True,no_model_or_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert d.read(BASE/'INCOMPLETE')['scope']=='WPC0'
files=[dict(path=str(p.relative_to(BASE)),sha256=d.sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
d.save('AVAILABLE_DELIVERY_SEAL.json',dict(status=status,entries=len(files),files=files,
    artifact_bytes_before_seal=d.size(),INCOMPLETE_retained=True))
print(json.dumps(dict(status=status,entries=len(files),Windows_seconds=seconds,
    Linux_child_seconds=child_seconds,bytes=d.size(),complete_resource_gate_passed=False)),flush=True)
