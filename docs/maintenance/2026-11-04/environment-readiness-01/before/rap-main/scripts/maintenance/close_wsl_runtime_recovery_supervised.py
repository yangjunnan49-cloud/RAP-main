"""Audit recovery with retained failed supervisor and two fully supervised runs."""
import local_motion_common as c
BASE=c.MAIN/'docs/maintenance/2026-10-10/wsl-runtime-recovery-01'
for name in ('freeze.json','amendment_freeze.json','supervision_repair_freeze.json'):
    for p,h in c.read(BASE/name)['files'].items():assert c.sha(p)==h,p
records=[];files=[]
for stage in ('verify02','verify03'):
    folder=BASE/'supervision'/stage
    host=c.read(folder/'exit.json');child=c.read(folder/'child_exit.json');v=c.read(folder/'verification.json')
    assert host['exit_code']==0 and child['success'] and child['full_resource_capture'] and v['passed']
    assert host['minimum_observed_headroom_bytes']>=4*2**30
    assert v['optimizer_calls']==v['backward_calls']==0 and v['actual_native_steps']==5
    records.append(dict(stage=stage,host=host,child=child,verification=v))
first=c.read(BASE/'supervision/verify01/child_exit.json')
assert first['success'] and first['full_resource_capture']
children=[first]+[x['child'] for x in records]
for child in children:
    assert child['peak_RSS_bytes']<=4*2**30
    assert max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=3*2**30
assert records[0]['verification']['output_sha256']==records[1]['verification']['output_sha256']==first['result']['output_sha256']
wall=sum(x['wall_seconds'] for x in children);assert wall<=600
remediation=c.read(BASE/'HOST_REMEDIATION.json')
assert remediation['CAD_process_preserved'] and remediation['CAD_stop_calls']==0
assert remediation['after_memory']['CommitLimit']-remediation['after_memory']['CommittedBytes']>=12*2**30
for p in sorted(BASE.rglob('*')):
    if p.is_file() and p.name not in ('validation.json','REPORT.md','STATUS.json','DELIVERY_SEAL.json'):
        files.append(dict(path=str(p.relative_to(BASE)),sha256=c.sha(p)))
result=dict(passed=True,decision='HOST_COMMIT_HEADROOM_RECOVERED_NATIVE_RUNTIME_VERIFIED',records=records,
    retained_supervisor_failure=dict(stage='verify01',native_child=first,host_exit_status_unknown=True,periodic_host_observation_gap=True),
    full_resource_capture=True,all_three_native_payload_resource_peaks_captured=True,two_full_supervised_processes=True,
    no_optimizer_or_backward_calls=True,CAD_stop_calls=0,prior_CAD_already_absent_before_action=True,
    repeated_native_output_identity=True,Windows_Event2004_correlated_prior_exits=True,
    exact_prior_exit_mechanism_not_traced=True,new_payload_wall_seconds=wall,
    peak_RSS_bytes=max(x['peak_RSS_bytes'] for x in children),
    peak_GPU_allocated_bytes=max(x['peak_GPU_allocated_bytes'] for x in children),
    peak_GPU_reserved_bytes=max(x['peak_GPU_reserved_bytes'] for x in children),files=files)
c.save(BASE/'validation.json',result)
report=f'''# WSL host-memory recovery

**{result['decision']}**. Historical WSL exits coincide with Windows resource-exhaustion Event2004 and host commit near its limit. This supports host memory pressure; the exact internal mechanism of each old exit was not traced.

The owner approved the targeted NVIDIA Overlay restart. The exact five-process old overlay tree was restarted; observed host commit dropped{remediation['commit_released_bytes']/2**30:.3f}GiB. The fresh pre-action census already found no SOLIDWORKS process; the agent did not stop CAD and its previous closure/save status is unknown. No driver/runtime installation, global WSL restart, page-file/configuration change or historical NOC4 dossier alteration occurred.

Three target-free native processes now finish strict344-key original model loading, three byte-exact cached/full forwards and the unchanged five-step sampler; all three output checksums agree. No backward/optimizer or performance evaluation. The first supervisor failed a log-write compatibility check, but that native child completed and retained full resource peaks. Its Windows exit and periodic host observation gap remain explicitly unknown. Separate logging repair sources/freeze and two subsequent fully supervised success/exit/resource receipts are preserved. The initial CAD-PID protection-check failure also preceded any process mutation.

All three native payloads total{wall:.6f}s; maximum RSS{result['peak_RSS_bytes']}bytes, GPU allocated/reserved{result['peak_GPU_allocated_bytes']}/{result['peak_GPU_reserved_bytes']}bytes. Full native child resource peaks pass600s/3GiB GPU/4GiB RSS/64MiB ceilings, including the failed-supervisor payload. Only the latter two have complete Windows supervisor evidence. Startup/imports/design/docs/final seal bookkeeping are excluded from payload time, with available external Windows walls retained separately; not production latency.

The corrected supervisor checks>=12GiB host commit headroom before launch, saves periodic host memory/stdout/stderr/exit, and the child stops subsequent work under4GiB host headroom. The runtime verification permits a separate output-routed NOC4 attempt using unchanged scientific settings/noises/gates. Historical missing resources and stops remain unchanged. No future lifetime guarantee or native learning gain is inferred.

Microsoft's [Event2004 guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-application-service-memory-leaks) identifies system commit exhaustion and distinguishes commit from working set. See AMENDMENT_01/02 for retained failures and prospective operational corrections.
'''
(BASE/'REPORT.md').write_text(report)
c.status(BASE,'complete',status='VALIDATED_RUNTIME_RECOVERY_WITH_SUPERVISOR_REPAIR',decision=result['decision'],optimizer_calls=0)
entries=[dict(path=str(p.relative_to(BASE)),sha256=c.sha(p),bytes=p.stat().st_size)
    for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
assert sum(x['bytes'] for x in entries)<64*2**20
c.save(BASE/'DELIVERY_SEAL.json',dict(status='VALIDATED_RUNTIME_RECOVERY_WITH_SUPERVISOR_REPAIR',files=entries,
    native_payload_caps_pass=True,first_supervisor_host_exit_unknown=True))
print('Runtime recovery audited and sealed',wall,'seconds',flush=True)
