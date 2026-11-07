"""FTI0 stdlib closure, explicit numerical versus physical evidence boundary."""
import time
START=time.monotonic()
import json
import resource
from pathlib import Path
import frame_time_identifiability as d

BASE=d.BASE
f=d.verify()
w,v=d.read(BASE/'witness.json'),d.read(BASE/'validation.json')
assert v['passed'] and d.sha(BASE/'witness.json')==d.read(BASE/'witness_seal.json')['sha256']
receipts=[]
retries=gaps=0
for stage in ('freeze','witness','validate'):
    q=BASE/'supervision'/stage
    child,windows,launch=[d.read(q/n) for n in ('child_exit.json','exit.json','launch.json')]
    assert child['success'] and child['full_resource_capture'] and windows['exit_code']==0
    assert child['peak_RSS_bytes']<=128*2**20
    assert child['peak_GPU_allocated_bytes']==child['peak_GPU_reserved_bytes']==0
    assert child['new_model_solver_fit_or_pose_metric_calls']==0
    samples=[json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert len(samples)==windows['host_memory_observations']>0
    assert min(r['headroom_bytes'] for r in samples)>=4*2**30
    assert launch['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            if name.startswith('logging_retry'):retries+=len((q/name).read_text().splitlines())
            else:gaps+=len((q/name).read_text().splitlines())
    receipts.append(dict(stage=stage,child=child,Windows=windows,launch=launch))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}=={'freeze','witness','validate'}
seconds=sum(r['Windows']['wall_seconds'] for r in receipts)
child_seconds=sum(r['child']['wall_seconds'] for r in receipts)
peak=max(r['child']['peak_RSS_bytes'] for r in receipts)
assert seconds<=300
status='VALIDATED_EXACT_FRAME_TIME_AMBIGUITY_CONTROLS_COMPLETE'
d.save('RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,attempts=3,successes=3,
    Windows_seconds_including_startup_imports=seconds,child_seconds_after_time_bootstrap=child_seconds,
    peak_RSS_bytes=peak,GPU_bytes=0,logging_retries=retries,logging_gaps=gaps,
    original_caps_unchanged=True,ordinary_preparation_RSS_unknown=True,stdlib_closure_separate=True))
d.save('CHECKS.json',dict(passed=True,controls=4,synthetic_poses=12,
    exact_rational_equalities=True,timestamp_rows=36924,distinct_Decimal_increments=132,
    no_physical_frame_or_clock_fault_identified=True,no_real_pose_or_point_numeric_read=True))
d.save('FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=f['repositories'],all_old_markers_and_stops_preserved=True))
d.save('STATUS.json',dict(status=status,decision=w['decision'],
    current_loader_wrong_proven=False,new_reference_or_timing_admitted=False,
    no_efficacy_or_retired_family_reopen=True))
report='\n'.join([
    '# FTI0 Exact Frame And Time Ambiguity Controls','',
    'Decision: '+w['decision']+'. All four predeclared controls pass exactly.','',
    'Sensor-frame counterexample: four planar positions are identical under a '
    'fixed right-composed90deg sensor orientation, while all three relative '
    'translations and rotations differ by exact conjugation. A horizontal '
    'position trace alone therefore does not identify local sensor axes. '
    'World-gauge counterexample rotates the same xy trace into xz with all '
    'three relative sensor poses exactly unchanged. No independent gravity '
    'or reference convention was supplied by these synthetic examples.','',
    'Clock counterexample uses four0.1s nominal stamps: a7s common offset '
    'retains increments/order/IDs; a rate factor2 retains order/IDs. Fixed '
    'four-return XYZI and one scan stamp also admit two distinct increasing '
    'per-return time lists. These are exact examples of non-identification, '
    'not an actual clock error, rate correction, motion estimate or assigned '
    'times for real points.','',
    'Every actual POSS00 timestamp row was parsed as Decimal:36924 finite, '
    'strictly increasing values, first0.000000/last2461.503,132 distinct exact '
    'increments, not an arithmetic grid. No hardware origin/rate/trigger, '
    'cross-sensor delay or per-return timing is authenticated from that '
    'structure. In particular, the synthetic0.1s example is not an assumption '
    'about these actual files.','',
    'Independent validator rebuilds every matrix inverse/product/conjugation '
    'using its own tuple/column implementation and sequential timestamp '
    'traversal. Twelve synthetic poses and nine relative-pose records satisfy '
    'their exact equations without tolerances or optimization. Current source '
    'descriptions/calibration readme/POP0 and RPC0 stops remain bound.','',
    f'All{len(f["files"])} frozen identities match; three successful supervised '
    f'CPU children: Windows{seconds:.9f}s including startup/imports, '
    f'child{child_seconds:.9f}s after bootstrap, peakRSS{peak}bytes/GPU0. '
    '300s/128MiB/8MiB caps pass, full native/Windows exits and host observations, '
    f'{retries} logging retries/{gaps} gaps. Ordinary preparation RSS unknown; '
    'stdlib closure separate; historical gaps remain.','',
    'This does not prove the current POSS loader or supplied calibration '
    'wrong, choose a new convention/reference, identify physical truth or '
    'the09 conflict cause. No real reference-pose/point coordinates, new '
    'model/learner/registration/pose metric, physical/system/generalization '
    'gain or acquisition/install/production/default/backbone/manuscript/'
    'restart/commit/Git sync. RPC0/BRF0/old retired families remain stopped.'
])
with (BASE/'REPORT.md').open('x',encoding='utf-8') as stream:stream.write(report+'\n')
with (BASE/'source_snapshot/closure_close_frame_time_identifiability.py').open('xb') as stream:
    stream.write(Path(__file__).read_bytes())
d.save('BOOKKEEPING.json',dict(stdlib_only=True,no_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert d.read(BASE/'INCOMPLETE')['scope']=='FTI0'
(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=d.sha(p),bytes=p.stat().st_size)
       for p in sorted(BASE.rglob('*')) if p.is_file()]
d.save('DELIVERY_SEAL.json',dict(status=status,entries=len(files),files=files,
    artifact_bytes_before_seal=d.size()))
assert d.size()<8*2**20
print(json.dumps(dict(status=status,entries=len(files),Windows_seconds=seconds,
    child_seconds=child_seconds,peak_RSS_bytes=peak,bytes=d.size())),flush=True)
