"""PCC0 layout02 closure retaining original failed archive-layout audit."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
OLD=ROOT/'docs/maintenance/2026-10-14/physical-comparison-contract-01'
BASE=OLD/'layout-attempt-02'
read,sha=s.read,s.sha

def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def text(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:stream.write(value+'\n')

f=read(BASE/'freeze.json');v=read(BASE/'validation.json')
assert v['passed'] and (OLD/'INCOMPLETE').exists()
for p,h in f['files'].items():assert sha(p)==h,p
for row in read(OLD/'ORIGINAL_AVAILABLE_SEAL.json')['files']:
    assert sha(OLD/row['path'])==row['sha256']
assert s.repositories()==f['repositories']
receipts=[];retries=gaps=0
for label,folder,stages in [('original',OLD,('freeze','audit')),('layout02',BASE,('bind','audit','validate'))]:
    for stage in stages:
        q=folder/'supervision'/stage
        c,w,l=[read(q/n) for n in ('child_exit.json','exit.json','launch.json')]
        expected=not(label=='original' and stage=='audit')
        assert c['success']==expected and w['exit_code']==(0 if expected else 1)
        assert c['full_resource_capture'] and c['peak_RSS_bytes']<=512*2**20
        assert c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==c['model_calls']==c['optimizer_calls']==0
        samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
        assert samples and len(samples)==w['host_memory_observations']
        assert min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
        for name in ('logging_retry.jsonl','logging_gap.jsonl'):
            if (q/name).exists():
                n=len((q/name).read_text().splitlines())
                if name.startswith('logging_retry'):retries+=n
                else:gaps+=n
        receipts.append(dict(attempt=label,stage=stage,child=c,Windows=w,launch=l))
windows=sum(r['Windows']['wall_seconds'] for r in receipts)
child=sum(r['child']['wall_seconds'] for r in receipts)
assert windows<=900
status='VALIDATED_COMMON_INPUT_STRONG_CONTROL_CONTRACT_WITH_RETAINED_LAYOUT_FAILURE'
save('RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,attempts=5,success=4,
    retained_original_layout_failure=1,combined_Windows_seconds_including_startup_imports=windows,
    child_seconds_after_time_bootstrap=child,peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),
    GPU_bytes=0,logging_retries=retries,logging_gaps=gaps,original900s_cap_unchanged=True,
    ordinary_setup_RSS_unknown=True,stdlib_closure_separate=True))
save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    original_source_and_available_seal_match=True,repositories=f['repositories'],
    original_PCC0_INCOMPLETE_retained=True))
save('CHECKS.json',dict(passed=True,independent_current_NPZ_files=v['current_NPZ_files'],
    independent_member_headers=v['independent_member_headers'],
    additional_scan_metadata_files=v['additional_scan_metadata_files'],
    original_layout_failure_retained=True,only_two_layout_lists_and_one_output_route_changed_per_source=True,
    numerical_or_model_replay=False,independent_confirmation_or_equal_pipeline_work_proven=False))
save('STATUS.json',dict(status=status,decision=v['decision'],
    original_PCC0_status='INCOMPLETE_SOURCE_LAYOUT_ASSERTION_STOP',head_fitting_admitted=False,
    next=v['summary']['next_admitted']))
text('REPORT.md','\n'.join([
    '# PCC0 current physical comparison contract / layout02', '',
    f'All{len(f["files"])} frozen identities and original available files match. '
    f'Independent validator checks{v["current_NPZ_files"]} complete existing NPZ hashes/'
    f'{v["independent_member_headers"]} literal NPY headers and '
    f'{v["additional_scan_metadata_files"]} additional raw filename-size records. '
    'No numeric point/pose/feature values parsed. Inherited scientific validators '
    'and all old model/solver outcomes are not replayed.', '',
    'Original PCC0 froze72 identities then failed before numeric payload because '
    'the new auditor expected flat tokens. Source and NPY headers both establish '
    'the actual(3,1000,512) layout. Original source/freeze/failure/receipts/INCOMPLETE '
    'remain immutable. This separate prospectively frozen attempt derives executable '
    'sources with exactly two token-shape AST list changes and one output-route '
    'constant per driver/independent validator; actual arrays/headers are unchanged. '
    'No scientific bounds/data/metric gate/cap changed.', '',
    'All204 old windows retain144 fit/12 development/48 exposed evaluation roles '
    'and612 distinct raw paths. Complete same-point G3 references exist for48 '
    'evaluation windows and KISS for36 matched07/09/10 endpoints. Stored unadapted '
    'J_pose exists for every window; D/I/J can share it, but that comparison is '
    'incremental information conditional on a joint base. Old full-flow tokens '
    'are not FCE0 first10 FP32 features; FHR0 derivatives do not cover a new '
    'head/normalizer/bound. Equal full-pipeline work is not established.', '',
    'POSS local/prior exposed scan counts and exact intervals: '+json.dumps({k:v['summary'][k]
        for k in ('POSS_local_scans','POSS_prior_exposed_scans','POSS_prior_exposed_IDs','POSS_current_IDs')})+'. '
    'POSS metadata alone does not supply checkpoint/site exclusion or new '
    'independent confirmation. Sibling KITTI matching names/sizes are not raw-byte '
    'identity or separate acquisition. No new complete independent confirmation '
    'source is established.', '',
    'Only next admitted question: a separately frozen optimistic mathematical '
    'feasibility census for the explicitly NEW component-bounded right-body '
    'residual(v_i<=.05m,w_i<=.2deg) around the common stored native pose. '
    'The entire family must be capable of meeting strong G3/KISS paired margins '
    'before a head is implemented. These are not bounds on old FHR0 outputs. '
    'A failed necessary condition stops this family without radius/initializer '
    'rescue or fitting; passing it still proves no learnability/efficacy.', '',
    f'Five total supervised CPU attempts/four successes/one retained source-layout '
    f'failure: Windows{windows:.9f}s including startup/imports, child{child:.9f}s '
    'after bootstrap;512MiB RSS/GPU0/32MiB combined dossier/original900s caps pass; '
    f'full child/Windows exits and host observations,{retries} logging retries/{gaps} gaps. '
    'Preparation/diagnostic RSS unknown and final stdlib closure separate.', '',
    'RLP2/CCR0/MGR0/GSG0 scientific stops, five historical NOC4/NBR/HFIT/LCP '
    'markers,09 unknown/official references/latest2026-10-11 system result and '
    'original HEADs/branches/two-nine dirty sets persist. No new model, backward, '
    'fit, trajectory, physical/system/novelty claim or production/install/acquisition/restart/commit/Git sync.'
]))
text('NEXT_ROUND_PLAN.md','# Next bounded question\n\n'
    'Freeze the complete48 stored native/G3 and36 KISS poses before any new '
    'target calculation. Validate proper rotations and translation/rotation '
    'triangle-inequality lower bounds independently. Compare the optimistic '
    'component-bounded family with all predeclared strong-control conditions; '
    'retain every window and adverse sequence. Stop on impossible necessary '
    'conditions, without fitting or enlarged bounds. All future learned '
    'common-stat/normalizer/capacity/work designs remain conditional.\n')
with (BASE/'source_snapshot/closure_close_physical_comparison_contract.py').open('xb') as out:
    out.write(Path(__file__).read_bytes())
save('BOOKKEEPING.json',dict(stdlib_only=True,wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,no_numeric_replay=True))
assert read(BASE/'INCOMPLETE')['scope']=='PCC0_LAYOUT02'
(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
whole=sum(p.stat().st_size for p in OLD.rglob('*') if p.is_file());assert whole<32*2**20
save('DELIVERY_SEAL.json',dict(status=status,entries=len(files),files=files,combined_bytes_before_seal=whole))
print(json.dumps(dict(status=status,entries=len(files),combined_bytes_before_seal=whole,
                      combined_Windows_seconds=windows)),flush=True)
