"""BPC0 closure, nested child records are not double-counted elapsed time."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import pipe_capture_control as d

BASE=d.BASE
f=d.verify();v=d.read(BASE/'validation.json');e=d.read(BASE/'exercise.json')
assert v['passed'] and v['inner_children_reaped']==8
assert d.sha(BASE/'exercise.json')==d.read(BASE/'exercise_seal.json')['sha256']
receipts=[];retries=gaps=0
for stage in ('freeze','exercise','validate'):
    q=BASE/'supervision'/stage
    child,windows,launch=[d.read(q/n) for n in ('child_exit.json','exit.json','launch.json')]
    assert child['success'] and child['full_resource_capture'] and windows['exit_code']==0
    assert child['peak_RSS_bytes']<=128*2**20
    assert child['peak_GPU_allocated_bytes']==child['peak_GPU_reserved_bytes']==0
    assert child['old_archive_or_model_or_fit_calls']==0
    samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert len(samples)==windows['host_memory_observations']>0
    assert min(r['headroom_bytes'] for r in samples)>=4*2**30
    assert launch['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            if name.startswith('logging_retry'):retries+=len((q/name).read_text().splitlines())
            else:gaps+=len((q/name).read_text().splitlines())
    receipts.append(dict(stage=stage,child=child,Windows=windows,launch=launch))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}=={'freeze','exercise','validate'}
seconds=sum(r['Windows']['wall_seconds'] for r in receipts)
child_seconds=sum(r['child']['wall_seconds'] for r in receipts)
peak=max(r['child']['peak_RSS_bytes'] for r in receipts)
assert seconds<=300
inner=[r['receipt'] for r in e['cases']]
assert len(inner)==8 and all(r['native']['peak_RSS_bytes']<=64*2**20 for r in inner)
inner_seconds=sum(r['wall_seconds'] for r in inner)
status='VALIDATED_SYNTHETIC_BOUNDED_PIPE_AND_NATIVE_EXIT_CONTROL_COMPLETE'
d.save('RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,outer_attempts=3,outer_successes=3,
    inner_synthetic_children=8,inner_native_exits_and_RSS=[r['native'] for r in inner],
    Windows_seconds_including_startup_imports=seconds,outer_child_seconds_after_time_bootstrap=child_seconds,
    inner_child_wall_seconds_nested_not_added=inner_seconds,
    peak_outer_RSS_bytes=peak,peak_inner_RSS_bytes=max(r['native']['peak_RSS_bytes'] for r in inner),
    GPU_bytes=0,logging_retries=retries,logging_gaps=gaps,
    ordinary_preparation_RSS_unknown=True,stdlib_closure_separate=True))
d.save('CHECKS.json',dict(passed=True,cases=8,inner_native_exits=8,
    success_cases=3,expected_unadmitted_cases=5,cooperating_file_envelope_bytes=3072,
    all_stdout_stderr_binary_bytes_and_native_RSS_checked=True,
    external_writer_or_arbitrary_process_tree_guarantee=False,production_or_RAP_integration=False))
d.save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=f['repositories'],all_old_sources_markers_and_stops_preserved=True))
d.save('STATUS.json',dict(status=status,prototype_cases=8,all_inner_children_reaped=True,
    whole_dossier_or_external_writer_guarantee=False,production_or_RAP_integration=False,
    old_archive_or_fit_retry=False))
report='\n'.join([
    '# BPC0 Synthetic Bounded Pipe And Exit Controls','',
    'All8 fixed synthetic children have complete native wait4 exits/peakRSS, '
    'observed stdout/stderr EOF, sealed binary journals and bounded terminal '
    'receipts. Three clean modes(normal/empty/invalidUTF8+NUL) are admitted; '
    'five overflow/nonzero/timeout modes are explicitly unadmitted.','',
    'One selector serializes64-byte pipe chunks. The fixed per-case namespace '
    'has exactly evidence.rdj<=2048bytes and exit.json<=1024bytes, within3072 '
    'cooperating bytes including logs, frames, footer and native exit metadata. '
    'Independent decoding/reconstruction verifies exact bytes for clean '
    'modes and all observed discarded counts for failures.','',
    'stdout overflow and both-stream flood happened to exit0 in this run, '
    'but remain unadmitted because logging failed. stderr overflow and timeout '
    'exit-15; planned nonzero exits7. Exit0 alone is not a complete-evidence '
    'gate. Timeout elapsed is recorded, not treated as successful performance. '
    'An overflow termination may prevent intended future writes; observed '
    'bytes are not a claim that all intended flood output was captured.','',
    'Termination targets only each newly launched fixed child session; no '
    'unrelated process was targeted. The source fixtures spawn no descendants. '
    'Arbitrary process trees, inherited external pipes, concurrent appenders, '
    'power-loss durability and OS directory quotas are outside this control. '
    'A complete journal also needs native exit/lifecycle/namespace admission. '
    'BEJ0 external-writer negative remains, and arbitrary external files are '
    'not prevented. Current outer Windows logs do not use this prototype.','',
    f'All{len(f["files"])} frozen identities match. Three successful outer '
    f'supervised CPU children: Windows{seconds:.9f}s including startup/imports, '
    f'outer child{child_seconds:.9f}s after bootstrap,RSS{peak}bytes. '
    f'Eight nested children sum{inner_seconds:.9f}s,peakRSS'
    f'{max(r["native"]["peak_RSS_bytes"] for r in inner)}bytes; those durations '
    'are already within the parent interval and are not added again. '
    '300s/128MiB parent/64MiB each inner/GPU0/8MiB caps pass, all native/'
    f'Windows exits/host observations,{retries} logging retries/{gaps} gaps. '
    'Ordinary preparation RSS unknown/stdlib closure separate/old gaps persist.','',
    'No real model, archive, fit, GT, solver, trajectory, production integration '
    'or old cap amendment. This distinct prototype does not repair LCP0/HFIT0 '
    'or authorize their retries. Physical/efficacy/novelty goals remain '
    'unresolved; source/measurement controls and all retired scientific '
    'families/official references/09 unknown/original HEADs/branches/dirty '
    'sets remain. No acquisition/install/restart/commit/Git sync.'
])
with (BASE/'REPORT.md').open('x',encoding='utf-8') as out:out.write(report+'\n')
with (BASE/'source_snapshot/closure_close_pipe_capture.py').open('xb') as out:
    out.write(Path(__file__).read_bytes())
d.save('BOOKKEEPING.json',dict(stdlib_only=True,no_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert d.read(BASE/'INCOMPLETE')['scope']=='BPC0';(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=d.sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
d.save('DELIVERY_SEAL.json',dict(status=status,entries=len(files),files=files,
    artifact_bytes_before_seal=d.size()))
assert d.size()<8*2**20
print(json.dumps(dict(status=status,entries=len(files),Windows_seconds=seconds,
    outer_child_seconds=child_seconds,inner_nested_seconds=inner_seconds,
    peak_outer_RSS_bytes=peak,bytes=d.size())),flush=True)
