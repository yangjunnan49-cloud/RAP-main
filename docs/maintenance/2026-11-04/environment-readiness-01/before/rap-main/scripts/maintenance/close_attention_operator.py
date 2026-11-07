"""AOD0 standard-library result/resource/preservation closure, no numerical replay."""
import json,resource,time
from pathlib import Path
import attention_operator_diagnosis as r
START=time.monotonic();base=r.BASE
r.verify();validation=r.read(base/'validation.json');binding=r.read(base/'INPUT_BINDING_AUDIT.json');assert validation['passed'] and binding['passed']
freeze=r.read(base/'freeze.json');extra=r.read(base/'INPUT_AUDIT_FREEZE.json')
for path,h in extra['files'].items():assert r.sha(r.MAIN/path)==h
receipts=[];retries=0;gaps=0
for stage in ('freeze','probe','validate','audit'):
    folder=r.SUP/stage;child=r.read(folder/'child_exit.json');host=r.read(folder/'exit.json');launch=r.read(folder/'launch.json')
    assert child['success'] and child['full_resource_capture'] and host['exit_code']==0 and child['optimizer_calls']==0
    assert child['peak_RSS_bytes']<=4*2**30 and max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=3*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()]
    assert len(samples)==host['host_memory_observations'] and samples and min(z['headroom_bytes'] for z in samples)>=4*2**30 and launch['headroom_before_bytes']>=12*2**30
    for name,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/name).exists():
            n=len((folder/name).read_text().splitlines());retries+=n if kind=='retry' else 0;gaps+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=child,host=host,launch=launch))
assert len([p for p in r.SUP.iterdir() if p.is_dir()])==4
seconds=sum(z['child']['wall_seconds'] for z in receipts);assert seconds<600
peak=max(z['child']['peak_RSS_bytes'] for z in receipts);allocated=max(z['child']['peak_GPU_allocated_bytes'] for z in receipts);reserved=max(z['child']['peak_GPU_reserved_bytes'] for z in receipts)
r.save(base/'RESOURCE_AUDIT.json',dict(passed=True,children=4,payload_seconds_including_imports=seconds,peak_RSS_bytes=peak,peak_GPU_allocated_bytes=allocated,peak_GPU_reserved_bytes=reserved,
    all_child_Windows_exits=True,logging_retries=retries,logging_gaps=gaps,receipts=receipts,old_caps_and_gaps_unchanged=True,setup_full_RSS_unknown=True,bookkeeping_separate=True))
r.save(base/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(freeze['files']),supplementary_source_entries=len(extra['files']),repositories=r.r.repos(),all_frozen_hashes_match=True))
lookup={(p['arm'],p['backend']):p['values'] for p in validation['pairs']};pd=lookup['P','default'];pm=lookup['P','math']
dispatch=[z['dispatched_ATen_names'] for z in validation['dispatch_records'] if z['backend']=='default' and z['rep']==1]
assert all('aten::_scaled_dot_product_flash_attention_backward' in names for names in dispatch)
decision='BOUNDED_DEFAULT_FLASH_VJP_VARIATION_MATH_REPEAT_EXACT' if not pd['normalized_gradient']['byte_equal'] and pm['normalized_gradient']['byte_equal'] else 'BOUNDED_OPERATOR_CENSUS_COMPLETE'
status=dict(status='VALIDATED_ISOLATED_ATTENTION_DIAGNOSIS_COMPLETE',decision=decision,unique_whole_model_cause_proved=False,native_fit_admitted=False,
    native_whole_forwards=0,prefix_calls=0,operator_VJPs=8,projection_VJPs=4,optimizer_calls=0,parameter_updates=0,production_backend_changed=False)
(base/'PREPARATION_STATUS.json').write_bytes((base/'STATUS.json').read_bytes());(base/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
r.save(base/'CHECKS.json',dict(passed=True,validation=validation,input_binding=binding,science_caps_passed=True,old_NOC4_INCOMPLETE_preserved=True,unique_whole_model_cause=False))
lines=['# AOD0 isolated last-block attention result','',f"Status: {status['status']}. Decision: {decision}.",'',
    'Fixed original layer11 global-attention boundary, sealed V_full1/P_full1 QKV and incoming cotangents. The exact archived raw/projection/cotangent and normalized-QKV bindings pass independently. Original strict model/initialization/mode source contract retained; no parameters or persistent backend changed.8 local attention VJPs plus4 input-projection VJPs,0 whole-native/explicit-prefix calls and0 optimizer/updates.',
    '', '|Cotangent/backend|Forward differing values|Raw-QKV gradient differing values|Normalized QKV gradient differing values|','|---|---:|---:|---:|']
for arm in ('V','P'):
    for backend in ('default','math'):
        z=lookup[arm,backend];lines.append(f"|{arm}/{backend}|{z['output']['different']}|{z['raw_gradient']['different']}|{z['normalized_gradient']['different']}|")
lines+=['', 'Actual CPU-profiler ATen dispatch records show scaled_dot_product_flash_attention and its backward for the default first repetitions. Default forward exactly matches the archived attention output. P default repeated raw-QKV gradients differ at2 values, normalized gradients at13 values, both max5.960464477539063e-8 (one fp16 minimum step, in the inherited scaled-cotangent units). V default and both math repeats are exact. Same normalized inputs and cotangents exclude an input change in this bounded local reproduction; the normalized-gradient differences occur within the observed SDPA VJP before QK-normalization backward. This does not prove the unique source of every historical whole-model mismatch.',
    '', 'The scoped math backend changes hidden forward activations by max.00390625 relative to the archive, despite repeatability. These are hidden activation units, not metres or pose scores. Math is therefore a distinct numerical path, not an established drop-in complete model repair. Both backend flags and original/frozen parameter values restore exactly. No production default switch occurred.',
    '', 'Independent explicit float64 softmax-Q equations check64 query rows/head for every case (4096 head-query rows). FP16 rounding differences/one-ULP counts are reported descriptively in validation.json. This is not full independent K/V/QK-normalization/projection or whole-transformer backward. No extra repetitions, targeted seeds or backend sweeps after outcomes.',
    '',f"482 identities plus2 separately frozen input-audit sources preserved.4 successful supervised children, {seconds:.6f}s incl imports; RSS {peak} bytes, GPU allocated/reserved {allocated}/{reserved}.600s/4GiB/3GiB/256MiB new caps pass; all child/Windows exits, {retries} logging retries/{gaps} gaps. Standard-library closure separate; ordinary setup full RSS unknown and old gaps/budgets unchanged. A normal first-backward cuBLAS primary-context warning was retained; no process restart or configuration repair occurred.",
    '', 'Original NOC4 loss-increase/P mismatch/INCOMPLETE, original NBR0 prerequisite failure and CCR0 negative remain. No learnability, physical truth, robustness, official metric/system or novelty gain; no production/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync.']
(base/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(base/'NEXT_ROUND_PLAN.md').write_text('# Next distinct full-native numerical prerequisite — DESIGN_ONLY\n\nThe observed local Flash backward variation and exact math repeats justify a separately scoped process-local math-backend full/native-cache repeatability test on the original fixture/initialization. It must freeze original default control, flag restoration, new forward differences, all gradients and whole-direction derivative checks, with zero updates and its own resource envelope before fitting. Isolated math stability does not certify full-model reproducibility or first-step descent. Preserve original NOC4 loss increases and failed gates; no rate/step/scale/noise/init rescue or automatic400-update fit. No new full-native math protocol/runner/freeze/backward was executed by AOD0.\n',encoding='utf-8')
r.save(base/'BOOKKEEPING.json',dict(standard_library_only=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,no_scientific_replay=True))
assert (base/'INCOMPLETE').read_text().startswith('AOD0');(base/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(base)),sha256=r.sha(p),bytes=p.stat().st_size) for p in sorted(base.rglob('*')) if p.is_file()];assert sum(z['bytes'] for z in files)<256*2**20
r.save(base/'DELIVERY_SEAL.json',dict(status=status['status'],decision=decision,files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=decision,deliveries=len(files),seconds=seconds,peak_RSS_bytes=peak,peak_GPU_allocated_bytes=allocated,peak_GPU_reserved_bytes=reserved),indent=2))
