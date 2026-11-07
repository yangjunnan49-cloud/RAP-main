"""PEL0 source-role audit closure with retained prefreeze discovery failure."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/poss-exposure-lineage-01'
read,sha=s.read,s.sha

def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def text(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:stream.write(value+'\n')

f=read(BASE/'freeze.json');v=read(BASE/'validation.json');c=read(BASE/'source_census.json')
assert v['passed']
for p,h in f['files'].items():assert sha(p)==h,p
assert s.repositories()==f['repositories']
receipts=[];retries=gaps=0
for stage in ('freeze','freeze02','census','validate'):
    q=BASE/'supervision'/stage
    child,windows,launch=[read(q/n) for n in ('child_exit.json','exit.json','launch.json')]
    expected=stage!='freeze'
    assert child['success']==expected and windows['exit_code']==(0 if expected else 1)
    assert child['full_resource_capture'] and child['peak_RSS_bytes']<=512*2**20
    assert child['peak_GPU_allocated_bytes']==child['peak_GPU_reserved_bytes']==child['model_calls']==child['optimizer_calls']==0
    samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert samples and len(samples)==windows['host_memory_observations']
    assert min(r['headroom_bytes'] for r in samples)>=4*2**30 and launch['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            n=len((q/name).read_text().splitlines())
            if name.startswith('logging_retry'):retries+=n
            else:gaps+=n
    receipts.append(dict(stage=stage,child=child,Windows=windows,launch=launch))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}=={'freeze','freeze02','census','validate'}
seconds=sum(r['Windows']['wall_seconds'] for r in receipts);assert seconds<=900
child_seconds=sum(r['child']['wall_seconds'] for r in receipts)
status='VALIDATED_BOUNDED_POSS_EXPOSURE_AND_LINEAGE_CENSUS_COMPLETE'
save('RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,attempts=4,success=3,
    retained_prefreeze_missing_rg_failure=1,Windows_seconds_including_startup_imports=seconds,
    child_seconds_after_time_bootstrap=child_seconds,peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),
    GPU_bytes=0,logging_retries=retries,logging_gaps=gaps,original_caps_unchanged=True,
    ordinary_preparation_RSS_unknown=True,stdlib_closure_separate=True))
save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=f['repositories'],retained_original_prefreeze_sources_and_receipts=True,
    old_stops_and_INCOMPLETE_markers_unchanged=True))
save('CHECKS.json',dict(passed=True,candidate_files=v['candidate_files'],
    source_evidence_files=v['evidence_files'],current_scans=4170,
    independent_source_ID_unions_runs_and_denominators=True,
    all_unclassified_ids_remain_unknown=True,no_unseen_or_physical_confirmation_admission=True,
    model_solver_or_metric_calls=0))
save('STATUS.json',dict(status=status,decision=v['decision'],
    category_counts=v['category_counts'],independent_confirmation_admitted=False,
    new_scientific_cohort_or_fit_admitted=False))
table=['| Surviving local evidence category | Current scan IDs |','|---|---:|']
for name,count in v['category_counts'].items():table.append(f'|{name}|{count}|')
text('REPORT.md','\n'.join([
    '# PEL0 POSS surviving-local exposure and lineage', '',
    'Decision: '+v['decision']+'. No new scientific cohort or fitting is admitted.', '',
    f'All{len(f["files"])} frozen identities match. Independent os.walk/fnmatch '
    f'discovery checks{v["candidate_files"]} candidate source/configuration JSON '
    f'files/{v["candidate_bytes"]}bytes;{v["evidence_files"]} files contain '
    'eligible POSS scan-path/ID/range evidence. Sources span all declared historic '
    'maintenance directories and current sibling output* roots, with exact '
    'name-pattern/directory exclusions in freeze.json. This is a surviving-local '
    'record census, not proof that all historical accesses were logged.', '',
    'All4170 current scan filenames/sizes match PCC0. Exact contiguous availability '
    'runs: '+json.dumps(v['current_contiguous_runs'])+'. Min/max alone must not '
    'be interpreted as a complete sequence.', '',
    '\n'.join(table), '',
    'Exact category runs: '+json.dumps(v['category_runs'])+'. Every current ID '
    'appears once in the complete partition. Explicit source-frame manifests '
    'and bound raw-input identities establish information exposure/binding; '
    'a configured range alone is not a proven model execution. Unclassified '
    'IDs are UNKNOWN, not newly discovered unseen or independent data.', '',
    'Current pose/time/calibration hashes and row counts match their bound '
    'files. The calibration readme describes LiDAR-to-camera projection; it '
    'does not authenticate the pose table frame, raw archive identity or '
    'sensor trigger/time/deskew lineage. The ten exact provenance queries '
    'apply only to the specified POSS00 paths. No numeric pose values, raw '
    'point arrays or new relative labels/errors were interpreted/calculated. '
    'The existing loader LiDAR-pose convention is inherited engineering '
    'evidence, not a new physical provenance certificate. Checkpoint/site '
    'exclusion and independent confirmation remain unestablished.', '',
    'Original prefreeze discovery failed because rg was absent in WSL, before '
    'candidate discovery/input freeze/source-role calculation. Exact failed '
    'source/protocol, native/Windows failure receipts and failure snapshot '
    'are preserved and bound by new freeze02. Driver recursive os.scandir '
    'fallback retains the same roots/patterns/limits; independent os.walk '
    'remains separate. No install/restart or scientific data/gate rescue.', '',
    f'Four attempted supervised CPU children/three successes/one retained '
    f'prefreeze failure: Windows{seconds:.9f}s including startup/imports, '
    f'child{child_seconds:.9f}s after bootstrap; '
    f'peakRSS{max(r["child"]["peak_RSS_bytes"] for r in receipts)},GPU0; '
    '900s/512MiB/32MiB original caps pass, all native/Windows exits/host '
    f'observations present,{retries} logging retries/{gaps} gaps. Ordinary '
    'preparation RSS unknown/stdlib final closure separate; historical gaps '
    'and stops remain.', '',
    'BRF0 bounded-native family remains stopped at its independently verified '
    'necessary-condition failure. No resizing/initializer/window rescue, '
    'RLP2/CCR0/GICP/graph/native/HFIT/LCP retry or actual new learner/solver '
    'was executed. All official references/09 unknown/original repositories/'
    'tracked dirty sets and latest2026-10-11 complete system benchmark '
    'persist. No physical/generalization/system/novelty gain or production/'
    'default/manuscript/environment/acquisition/restart/commit/Git sync.'
]))
text('NEXT_ROUND_PLAN.md','# Next design boundary\n\n'
    'Do not promote the newly inventoried POSS remainder to confirmation. '
    'Use the complete source/exposure partition in future role assignments. '
    'Any further efficacy experiment needs a distinct measurable physical '
    'question and an explicit common-input/strong-control/total-work contract '
    'that does not rescue retired families. Source/pose-frame/timing '
    'authentication and actual untouched confirmation are separate unresolved '
    'evidence dependencies. No acquisition or new experiment follows '
    'automatically; first consolidate these completed prerequisites and '
    'the BRF0 family stop into the current handoff.\n')
with (BASE/'source_snapshot/closure_close_poss_exposure_lineage.py').open('xb') as out:
    out.write(Path(__file__).read_bytes())
save('BOOKKEEPING.json',dict(stdlib_only=True,no_numeric_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert read(BASE/'INCOMPLETE')['scope']=='PEL0';(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
size=sum(r['bytes'] for r in files);assert size<32*2**20
save('DELIVERY_SEAL.json',dict(status=status,decision=v['decision'],entries=len(files),files=files,artifact_bytes_before_seal=size))
print(json.dumps(dict(status=status,entries=len(files),bytes=size,Windows_seconds=seconds,
                      child_seconds=child_seconds,category_counts=v['category_counts'])),flush=True)
