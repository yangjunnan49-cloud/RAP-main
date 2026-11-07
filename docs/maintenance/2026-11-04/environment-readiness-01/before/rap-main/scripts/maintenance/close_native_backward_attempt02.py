"""NBR0 standard-library metadata closure; no model/array numerical imports."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'docs/maintenance/2026-10-13/native-backward-reproducibility-02'; PREVIOUS=ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01'; START=time.monotonic()
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
freeze=read(BASE/'freeze.json'); validation=read(BASE/'validation.json'); result=read(BASE/'results.json'); assert validation['passed'] and read(BASE/'mode_validation.json')['passed'] and (PREVIOUS/'INCOMPLETE').exists()
for p,h in freeze['files'].items(): assert sha(p)==h,p
repositories={}
for name,p in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a): return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*a],text=True).strip()
    repositories[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repositories==freeze['repositories']
old=ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01'; assert (old/'INCOMPLETE').exists() and (old/'attempt-02/INCOMPLETE').exists()
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(utc=now(),passed=True,frozen_identities=len(freeze['files']),repositories=repositories,old_native_INCOMPLETE_preserved=True))
receipts=[]; retries=0; gaps=0
for stage in ('freeze','freeze02','mode','validate_mode','diagnose','validate'):
    folder=BASE/'supervision'/stage; child=read(folder/'child_exit.json'); host=read(folder/'exit.json'); launch=read(folder/'launch.json')
    assert child['success']==(stage!='freeze') and host['exit_code']==(1 if stage=='freeze' else 0) and child['full_resource_capture'] and child['optimizer_calls']==0
    assert child['peak_RSS_bytes']<=4*2**30 and max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=3*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()]; assert len(samples)==host['host_memory_observations'] and samples
    assert min(x['headroom_bytes'] for x in samples)>=4*2**30 and launch['headroom_before_bytes']>=12*2**30
    for filename,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/filename).exists():
            n=len((folder/filename).read_text().splitlines()); retries+=n if kind=='retry' else 0;gaps+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=child,host=host,launch=launch))
assert len([p for p in (BASE/'supervision').iterdir() if p.is_dir()])==6
for stage in ('freeze','diagnose'):
    folder=PREVIOUS/'supervision'/stage; receipts.append(dict(stage='previous_'+stage,child=read(folder/'child_exit.json'),host=read(folder/'exit.json'),launch=read(folder/'launch.json')))
old_artifact_bytes=sum(p.stat().st_size for p in PREVIOUS.rglob('*') if p.is_file())
assert all(x['child']['artifact_bytes']+old_artifact_bytes<512*2**20 for x in receipts if not x['stage'].startswith('previous_'))
seconds=sum(x['child']['wall_seconds'] for x in receipts); assert seconds<1200
peak=max(x['child']['peak_RSS_bytes'] for x in receipts); ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts); gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(utc=now(),passed=True,scientific_children=8,combined_seconds=seconds,peak_RSS_bytes=peak,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,
    full_child_and_Windows_exits=True,imports_included_in_scientific_time=True,logging_retries=retries,logging_gaps=gaps,receipts=receipts,old_gaps_and_caps_unchanged=True,bookkeeping_separate=True))
save(BASE/'CHECKS.json',dict(utc=now(),passed=True,independent_artifact_validation=validation,native_NOC4_INCOMPLETE=True,optimizer_calls=0,retained_updates=0,
    unique_cause_resolved=False,native_fit_admitted=False,original_repository_identity=True,scientific_caps_pass=True))
status=dict(utc=now(),status='VALIDATED_BOUNDED_BACKWARD_DIAGNOSIS_COMPLETE',decision=result['decision'],diagnosis_complete=True,native_NOC4='INCOMPLETE',optimizer_calls=0,retained_updates=0,
    unique_cause_resolved=False,full_transformer_backward_independently_implemented=False,native_fit_admitted=False,commit_or_sync=False)
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# NBR0 mode-inventory repair and bounded backward reproducibility diagnosis','',f"Status: {status['status']}. Decision: {result['decision']}.",'',
    'Same exposed NOC4 known-transform/copy-descriptor synthetic fixture, fit00 noise and443904 original initialized native trainables. Eight supervised instrumented backwards: two full and two cached paths per V/P. Original fp16/IEEE/eval/loss/multipliers unchanged. Zero optimizer calls and all parameters unchanged byte-exactly. A strict weights_only checkpoint load passes; frozen parameters/modes preserved.',
    '', '|Comparison|Forward output differing values|Upstream endpoint differing values|Parameter gradient differing values|Max parameter gradient difference|','|---|---:|---:|---:|']
for p in result['pairs']:
    d=p['details']; output=d['output.npz']['output']['different']; upstream=d['output.npz']['upstream']['different']; gradients=d['gradients.npz']; count=sum(x['different'] for x in gradients.values()); maximum=max(x['max_abs'] for x in gradients.values())
    lines.append(f"|{p['left']} / {p['right']}|{output}|{upstream}|{count}|{maximum:.9g}|")
fdmax=max(x['delta'] for x in validation['P_output_directional_FD']); bad=sum(not x['within_one_fp16_ULP'] for x in validation['local_B_linear_checks'])
lines+=['',f"Independent Horn/direct loss max delta {validation['independent_loss_max_delta']:.9g}; V upstream max delta {validation['V_upstream_max_delta']:.9g};48 P output directional FD checks pass, max absolute delta {fdmax:.9g}. All difference censuses and unchanged parameters independently reproduce. Local B linear product checks have {bad}/32 outside the reported one-fp16-ULP bound; this is a disclosed local GEMM/reduction diagnostic, not independently implemented complete native backward.",
    '', 'Per-module input/output/scaled-gradient/rank activations and every trainable gradient are sealed. Hooks synchronize/capture identically but can affect scheduling; instrumented repeatability cannot certify historical uninstrumented determinism. Enabled SDPA flags do not identify actual dispatch. Compare existing old probe arrays descriptively in results.json. No unique cache/kernel/precision cause, derivative accuracy of all transformer operators, functional-step descent, native learning, robustness, physical accuracy or system gain is established.',
    '',f"{len(freeze['files'])} identities frozen, original204 NOC4 bindings/86 deliveries and40 runtime recovery deliveries preserved. Eight combined supervised scientific children (six new plus two retained original, two failures), {seconds:.6f}s incl imports; RSS {peak} bytes, GPU allocated/reserved {ga}/{gr} bytes.1200s/4GiB/3GiB/512MiB caps pass; full child/Windows exits, {retries} logging retries/{gaps} pointer gaps. Final standard-library bookkeeping separate; old supervision/budget gaps unchanged.",
    '', 'Exact independent four-wrapper/source-AST/initialized-parameter mode contract passes with0 mode mutations. Initial Windows path-separator freeze failure and all original sources/receipts remain. Original NOC4 loss-increase and replay-mismatch gates/INCOMPLETE markers remain. This closes only the new NBR0 mode-repair diagnosis; original NBR0 failed dossier/marker stays immutable. No optimizer/update/fit/new noise/real/nearby/trajectory, no production/default/backbone/manuscript/reference/install/restart/commit/Git synchronization. Both original HEADs/branches/two-nine tracked dirty sets preserved.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next distinct question — not executed\n\nUse the module/upstream census to specify a bounded operator/backend diagnosis only if it distinguishes a repeated path effect. Retain identical captured inputs and output cotangents for local operator contrasts; do not infer dispatch or switch production backends. Before any native adapter fitting, require reproducible justified parameter directions and a separate functional-step policy with whole-direction FD, original settings/stops preserved. NBR0 provides no optimizer policy, fit, or new stage freeze/execution.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,standard_library_only=True,no_scientific_replay=True))
assert (BASE/'INCOMPLETE').read_text().startswith('NBR0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()];assert sum(z['bytes'] for z in files)+old_artifact_bytes<512*2**20
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=result['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=result['decision'],delivery_entries=len(files),seconds=seconds,peak_RSS_bytes=peak,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr),indent=2))
