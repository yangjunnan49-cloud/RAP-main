"""Audit supervised read-only native verifications and seal host runtime recovery."""
import json
from pathlib import Path
import local_motion_common as c
BASE=c.MAIN/'docs/maintenance/2026-10-10/wsl-runtime-recovery-01'
records=[];files=[]
for stage in ('verify01','verify02'):
    folder=BASE/'supervision'/stage
    host=c.read(folder/'exit.json');child=c.read(folder/'child_exit.json');v=c.read(folder/'verification.json')
    assert host['exit_code']==0 and child['success'] and child['full_resource_capture'] and v['passed']
    assert child['peak_RSS_bytes']<=4*2**30
    assert max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=3*2**30
    assert v['optimizer_calls']==v['backward_calls']==0 and v['actual_native_steps']==5
    assert host['minimum_observed_headroom_bytes']>=4*2**30
    records.append(dict(stage=stage,host=host,child=child,verification=v))
    for p in sorted(folder.iterdir()):
        if p.is_file():files.append(dict(path=str(p.relative_to(BASE)),sha256=c.sha(p)))
assert records[0]['verification']['output_sha256']==records[1]['verification']['output_sha256']
wall=sum(x['child']['wall_seconds'] for x in records);assert wall<=600
remediation=c.read(BASE/'HOST_REMEDIATION.json');assert remediation['CAD_process_preserved']
assert remediation['after_memory']['CommitLimit']-remediation['after_memory']['CommittedBytes']>=12*2**30
supplement=c.read(BASE/'amendment_freeze.json')
for p,h in supplement['files'].items():assert c.sha(p)==h,p
freeze=c.read(BASE/'freeze.json')
for p,h in freeze['files'].items():assert c.sha(p)==h,p
for name in ('HOST_BEFORE.json','HOST_REMEDIATION.json','PROTOCOL.md','freeze.json','amendment_freeze.json','AMENDMENT_01.md','HOST_REFRESH.json'):
    files.append(dict(path=name,sha256=c.sha(BASE/name)))
result=dict(passed=True,decision='HOST_COMMIT_HEADROOM_RECOVERED_NATIVE_RUNTIME_VERIFIED',records=records,
    full_resource_capture=True,no_optimizer_or_backward_calls=True,current_CAD_preserved=True,prior_CAD_already_absent_before_action=True,pre_action_guard_failure_retained=True,
    repeated_native_output_identity=True,Windows_Event2004_correlated_prior_exits=True,
    exact_prior_exit_mechanism_not_traced=True,new_payload_wall_seconds=wall,
    peak_RSS_bytes=max(x['child']['peak_RSS_bytes'] for x in records),
    peak_GPU_allocated_bytes=max(x['child']['peak_GPU_allocated_bytes'] for x in records),
    peak_GPU_reserved_bytes=max(x['child']['peak_GPU_reserved_bytes'] for x in records),files=files)
c.save(BASE/'validation.json',result)
report=f'''# WSL host-memory recovery

**{result['decision']}**. Original exits coincide with Windows resource-exhaustion Event2004. Host commit before recovery was close to its limit; NVIDIA Overlay alone consumed about16.3GiB private committed memory and SOLIDWORKS about63.3GiB with an unsaved document. The exact internal cause of each historical exit was not traced. Event/time/commit evidence supports host memory pressure rather than a native objective failure.

Owner approved a targeted NVIDIA Overlay restart. Commit released:{remediation['commit_released_bytes']/2**30:.3f}GiB. A fresh census before this action already found no SOLIDWORKS process. The agent did not stop CAD; its prior closure/save status is unknown. The original restart helper failed its old-PID protection check before any process mutation; the unchanged failed helper and supplementary protection-check correction are retained. No WSL/driver/runtime installation or page-file/configuration change. Historical NOC4 stop/resources are retained unchanged.

Two independently launched, supervised Python processes each strict-load the original344-key RAP model/initialization, perform three identical full forwards with byte-exact cached/full equality and complete the unchanged five-step sampler. Across processes the full-forward checksum matches. No gradient/optimizer, evaluation-noise selection or pose-performance result. Both complete resource/exit records pass600s/3GiB GPU/4GiB RSS; payload{wall:.6f}s, peak RSS{result['peak_RSS_bytes']}bytes, GPU allocated/reserved{result['peak_GPU_allocated_bytes']}/{result['peak_GPU_reserved_bytes']}bytes. Complete Windows walls/commit samples are separately retained. No future lifetime guarantee is inferred.

The new launcher checks at least12GiB Windows commit headroom before native stages and retains host samples/stdout/stderr/exit; the child records full resource peaks and stops subsequent work below4GiB headroom. A separate output-routed NOC4 retry may proceed with unchanged scientific source/settings/noises/gates. Original all-attempt resource gaps are not repaired retrospectively.

Microsoft's [Event2004 guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-application-service-memory-leaks) identifies system commit exhaustion and distinguishes commit from working set. This explains why modest physical working-set sizes did not rule out host virtual-memory pressure.
'''
(BASE/'REPORT.md').write_text(report)
c.status(BASE,'complete',status='VALIDATED_RUNTIME_RECOVERY',decision=result['decision'],optimizer_calls=0)
entries=[dict(path=str(p.relative_to(BASE)),sha256=c.sha(p),bytes=p.stat().st_size)
    for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
assert sum(x['bytes'] for x in entries)<64*2**20
c.save(BASE/'DELIVERY_SEAL.json',dict(status='VALIDATED_RUNTIME_RECOVERY',files=entries,new_caps_pass=True))
print('Runtime recovery independently checked and sealed',wall,'seconds',flush=True)
