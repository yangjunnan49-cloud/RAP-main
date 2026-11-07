"""BRF0 stdlib final identity/resource/negative-feasibility documentation."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-native-residual-feasibility-01'
read,sha=s.read,s.sha

def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def text(name,value):
    with (BASE/name).open('x',encoding='utf-8') as stream:stream.write(value+'\n')

f=read(BASE/'freeze.json');v=read(BASE/'validation.json');census=read(BASE/'census.json')
assert v['passed'] and read(BASE/'pose_validation.json')['passed']
for p,h in f['files'].items():assert sha(p)==h,p
assert s.repositories()==f['repositories']
receipts=[];retries=gaps=0
for stage in ('freeze','poses','validate_poses','census','validate_census'):
    q=BASE/'supervision'/stage
    c,w,l=[read(q/n) for n in ('child_exit.json','exit.json','launch.json')]
    assert c['success'] and w['exit_code']==0 and c['full_resource_capture']
    assert c['peak_RSS_bytes']<=512*2**20
    assert c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==c['native_model_calls']==c['head_backwards']==c['retained_updates']==c['optimizer_calls']==0
    samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert samples and len(samples)==w['host_memory_observations']
    assert min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            n=len((q/name).read_text().splitlines())
            if name.startswith('logging_retry'):retries+=n
            else:gaps+=n
    receipts.append(dict(stage=stage,child=c,Windows=w,launch=l))
windows=sum(r['Windows']['wall_seconds'] for r in receipts);assert windows<=900
child=sum(r['child']['wall_seconds'] for r in receipts)
possible=v['summary']['all_necessary_conditions_possible']
status='VALIDATED_BOUNDED_NATIVE_RESIDUAL_NECESSARY_CONDITION_CENSUS_COMPLETE'
save('RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,
    Windows_seconds_including_startup_imports=windows,child_seconds_after_time_bootstrap=child,
    peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts),GPU_bytes=0,
    logging_retries=retries,logging_gaps=gaps,ordinary_setup_RSS_unknown=True,
    stdlib_closure_separate=True,historical_caps_and_gaps_unchanged=True))
save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=f['repositories'],all_original_scientific_stops_and_markers_preserved=True))
save('CHECKS.json',dict(passed=True,complete_exposed_windows=48,native_G3_KISS_poses=132,
    target_free_SE3_fixtures=65,all132_reference_errors_and_lower_bounds_independently_verified=True,
    matrix_and_scalar_tolerances_pass=True,head_fits=0,native_or_head_backwards=0,
    necessary_condition_conjunction_possible=possible,no_new_system_or_physical_claim=True))
save('STATUS.json',dict(status=status,decision=v['decision'],
    family_retired=not possible,head_fit_admitted=False,
    native_model_repaired=False,physical_or_system_gain=False))
table=['| Control | Windows | Optimistic paired t gain m | Optimistic paired R gain deg | Necessary conjunction possible |',
       '|---|---:|---:|---:|---|']
for name,row in v['summary']['comparisons'].items():
    gains=row['optimistic_paired_median_gain']
    table.append(f'|{name}|{row["windows"]}|{gains[0]:.9g}|{gains[1]:.9g}|{row["all_necessary_conditions_possible"]}|')
interpretation=('Retire this exact small component-bounded residual family around the stored native base before any head implementation/fitting. '
    'Even mutually optimistic per-window corrections cannot satisfy all required strong-control comparisons. '
    'No radius/initializer/window/metric rescue follows; this is not a theorem about all residual models or RAP representations.' if not possible else
    'These necessary conditions do not rule out this family. They establish neither a realizable common head nor learning/physical/efficacy admission. '
    'A future exact head would still require derivative/activity/common-input/equal-work/source gates before any fit.')
text('REPORT.md','\n'.join([
    '# BRF0 bounded native-base residual feasibility', '',
    'Decision: '+v['decision']+'. '+interpretation, '',
    f'All{len(f["files"])} frozen source identities match. All48 fixed exposed '
    'RLP2 evaluation windows07/08/09/10 retained,12 per sequence; native/G3 '
    'poses48 each and KISS36 identical07/09/10 endpoints. Complete poses were '
    'sealed and independently validated before any new reference calculation. '
    'No source sampling/model/feature/solver/head/training replay.', '',
    'The NEW proposed tanh family bounds each right-body translation component '
    'by.05m and rotation component by.2deg. SE3 translation-integral and SO3 '
    'triangle inequalities give optimistic norm limits '
    f'{f["translation_norm_bound_m"]:.12g}m/{f["rotation_norm_bound_deg"]:.12g}deg. '
    'The lower bound subtracts an additional1e-9m/1e-7deg numerical allowance. '
    'These are neither original FHR0 linear-head bounds nor achieved predictions.', '',
    '\n'.join(table), '',
    'Complete per-window base/control errors, optimistic lower bounds and all '
    'sequence safety/ratio/margin conditions are in census.json. Optimistic errors '
    'can be mutually unrealizable by a common head, so passing would not prove '
    'learnability; failing a required optimistic condition excludes this fixed '
    'family from the predeclared engineering gates without fitting.', '',
    'All stored rotations are explicitly mapped to nearest proper SO3 for this '
    'new mathematical scoring contract only, max matrix correction<=1e-5; '
    'translations retained, no official/reference/file or historical metric '
    'change. Independent symmetric-eigen polar factors, fsum translation and '
    'atan2 geodesics verify all132 errors and necessary conjunctions. '
    'Independent closed Rodrigues/V checks all65 target-free exponential fixtures. '
    f'Pose-mapping max delta{read(BASE/"pose_validation.json")["independent_polar_max_delta"]:.12g}; '
    f'exp max delta{read(BASE/"pose_validation.json")["independent_closed_exp_max_delta"]:.12g}; '
    f'reference-error max delta{v["independent_error_max_delta"]:.12g}. '
    'This is numerical corroboration of the analytic argument, not certified '
    'interval arithmetic or independent physical truth.', '',
    f'Five successful supervised CPU children, Windows{windows:.9f}s including '
    f'startup/imports, child{child:.9f}s after time bootstrap; '
    f'peakRSS{max(r["child"]["peak_RSS_bytes"] for r in receipts)},GPU0; '
    '900s/512MiB/32MiB caps pass, complete native/Windows exits/host records, '
    f'{retries} logging retries/{gaps} gaps. Ordinary preparation RSS unknown, '
    'final stdlib closure separate; all old caps/failures/gaps preserved.', '',
    'No actual head backward/retained update/fit, no native repair or real '
    'physical/generalization/system/novelty gain. Existing data/checkpoint/site '
    'exposure and09 physical cause remain unresolved. Latest complete system '
    'benchmark stays2026-10-11 attempt03. All old failures/markers/retired routes '
    'and original repositories/dirty sets retained; no production/default/'
    'reference/manuscript/environment/acquisition/restart/commit/Git sync.'
]))
text('NEXT_ROUND_PLAN.md','# Next route\n\n'+interpretation+'\n\n'
    'A distinct next useful source question is the remaining POSS metadata: '
    '4170 locally available scans versus1419 explicitly bound by the old '
    'full-poss study. Audit all existing historical source-ID manifests and '
    'calibration/timestamp lineage before assigning remaining intervals a role. '
    'Unmatched retained files are not automatically unseen or independent. '
    'No new data, raw geometry/model execution or replacement residual follows '
    'from that read-only source question.\n')
with (BASE/'source_snapshot/closure_close_bounded_native_residual.py').open('xb') as out:
    out.write(Path(__file__).read_bytes())
save('BOOKKEEPING.json',dict(stdlib_only=True,no_numeric_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert read(BASE/'INCOMPLETE')['scope']=='BRF0';(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
size=sum(r['bytes'] for r in files);assert size<32*2**20
save('DELIVERY_SEAL.json',dict(status=status,decision=v['decision'],entries=len(files),files=files,artifact_bytes_before_seal=size))
print(json.dumps(dict(status=status,decision=v['decision'],entries=len(files),
    bytes=size,Windows_seconds=windows,child_seconds=child)),flush=True)
