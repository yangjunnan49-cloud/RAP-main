"""BEJ0 prototype-only closure; no whole-namespace or integrated guarantee."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import evidence_journal_control as d

BASE=d.BASE
f=d.verify();v=d.read(BASE/'validation.json')
assert v['passed'] and len(v['results'])==15
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
status='VALIDATED_BOUNDED_SINGLE_FILE_EVIDENCE_JOURNAL_PROTOTYPE_COMPLETE'
d.save('RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,attempts=3,successes=3,
    Windows_seconds_including_startup_imports=seconds,child_seconds_after_time_bootstrap=child_seconds,
    peak_RSS_bytes=peak,GPU_bytes=0,logging_retries=retries,logging_gaps=gaps,
    ordinary_preparation_RSS_unknown=True,stdlib_closure_separate=True))
d.save('CHECKS.json',dict(passed=True,cases=15,exclusive_single_file_bound=True,
    all_overflows_fail_closed=True,torn_record_retained_and_unadmitted=True,
    external_namespace_cap_guarantee=False,old_archive_or_fit_retry=False))
d.save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=f['repositories'],old_payloads_and_markers_unchanged=True))
d.save('STATUS.json',dict(status=status,controlled_single_file_bound=True,
    whole_dossier_or_arbitrary_external_writer_guarantee=False,
    production_or_current_supervisor_integration=False,no_old_archive_retry=True))
report='\n'.join([
    '# BEJ0 Bounded Evidence Journal Prototype','',
    'All15 predeclared tiny-byte controls pass independent byte-level decoding '
    'and complete fixture directory reconciliation. This is a new artifact-only '
    'prototype, not a whole-dossier guarantee or old archive retry.','',
    'One exclusive file holds payload/stdout/stderr/metadata records. The16-byte '
    'header and64-byte terminal footer are reserved first, and every5-byte frame '
    'header plus payload is charged before writing. No refunds after partial '
    'failure. Both per-channel and global budgets must pass. Rejected logs are '
    'not silently truncated or called complete: the journal fails and later '
    'body writes are refused. The exact-fill case occupies its full256-byte '
    'cap with a171-byte payload and all framing/terminal bytes included.','',
    'Normal4-channel completion, stdout/stderr/metadata overflow, global cap, '
    'preexisting collision, injected short body write, copied corruption, '
    'truncated footer, external file, invalid type, after-close write, exact '
    'fill, second-constructor collision and invalid channel all retained. '
    'The injected short write retains3 actual bytes while charging the full '
    'intended record; failed status/torn decode prohibit admission. The '
    'corrupt and truncated copies are unsealed. Every expected negative is '
    'a validated control, not a failed supervised stage.','',
    'An untracked external file deliberately makes its directory exceed the '
    'journal cap while the journal itself remains valid. Complete directory '
    'reconciliation detects the extra file and denies whole-namespace '
    'admission. This does not prevent arbitrary external writers, enforce '
    'an OS directory quota or solve a census race. Reserved footer space '
    'does not guarantee successful I/O, crash durability or power-loss '
    'atomicity; a missing/bad footer remains unsealed. Concurrent appends '
    'to one Journal instance are not implemented or claimed.','',
    f'All{len(f["files"])} frozen identities match. Three successful supervised '
    f'CPU children: Windows{seconds:.9f}s incl startup/imports, '
    f'child{child_seconds:.9f}s after bootstrap,RSS{peak}bytes/GPU0. '
    '300s/128MiB/8MiB caps pass, all native/Windows exits/host observations, '
    f'{retries} logging retries/{gaps} gaps. Current supervisor logs are '
    'observed under this scope cap, not routed through the prototype. '
    'Ordinary preparation RSS unknown/stdlib closure separate/old gaps remain.','',
    'Next distinct feasibility boundary is a synthetic child stdout/stderr '
    'pipe adapter with explicit exit/overflow/timeout semantics. Any actual '
    'pipeline adoption requires exclusive ownership, all outputs routed, '
    'complete process-tree accounting and measured lifecycle controls. '
    'Neither this prototype nor a later adapter automatically authorizes '
    'LCP0/HFIT0 packing/fitting retries, old cap changes or production rollout. '
    'No old corpus, model, new metric, acquisition/install/reference/default/'
    'backbone/manuscript/restart/commit/Git sync.'
])
with (BASE/'REPORT.md').open('x',encoding='utf-8') as out:out.write(report+'\n')
with (BASE/'source_snapshot/closure_close_evidence_journal.py').open('xb') as out:
    out.write(Path(__file__).read_bytes())
d.save('BOOKKEEPING.json',dict(stdlib_only=True,no_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert d.read(BASE/'INCOMPLETE')['scope']=='BEJ0';(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=d.sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
d.save('DELIVERY_SEAL.json',dict(status=status,entries=len(files),files=files,
    artifact_bytes_before_seal=d.size()))
assert d.size()<8*2**20
print(json.dumps(dict(status=status,entries=len(files),Windows_seconds=seconds,
    child_seconds=child_seconds,peak_RSS_bytes=peak,bytes=d.size())),flush=True)
