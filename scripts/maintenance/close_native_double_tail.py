"""DTC0 standard-library final metadata closure; no scientific replay."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/native-double-tail-control-01';START=time.monotonic()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
f=read(BASE/'freeze.json');v=read(BASE/'validation.json');assert v['passed']
for p,h in f['files'].items():assert sha(p)==h,p
repos={}
for name,p in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
for p in [ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert p.exists()
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),repositories=repos,old_markers_preserved=True))
stages=['freeze','probe','repeat']+(['directions'] if v['directional_checks'] else [])+['validate'];receipts=[];retry=0;gap=0
for stage in stages:
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json');assert c['success'] and h['exit_code']==0 and c['full_resource_capture'] and c['optimizer_calls']==0
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=8*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/filename).exists():
            n=len((folder/filename).read_text().splitlines());retry+=n if kind=='retry' else 0;gap+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}==set(stages)
seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<900
rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,scientific_children=len(receipts),combined_seconds=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,receipts=receipts,imports_included=True,full_child_and_Windows_exits=True,logging_retries=retry,logging_gaps=gap,setup_RSS_unknown=True,bookkeeping_separate=True,old_caps_and_gaps_preserved=True))
save(BASE/'CHECKS.json',dict(passed=True,validation=v,science_caps_pass=True,old_markers_and_repository_identity=True,native_fit_admitted=False))
status=dict(utc=now(),status='VALIDATED_FIXED_PREFIX_DOUBLE_TAIL_CONTROL_COMPLETE',decision=v['decision'],all_directions_corroborated=v['all_directions_corroborated'],optimizer_calls=0,retained_updates=0,native_fit_admitted=False,whole_native_function_equivalence=False,old_NOC4='INCOMPLETE')
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# DTC0 fixed-prefix double trainable-tail derivative control','',f"Status: {status['status']}. Decision: {v['decision']}.",'',
    'Frozen archived FPC0 D_V/D_P float32 first10-layer prefixes match exactly and are promoted to double. Original initialized443904 trainable values/checkpoint/modes retained, last2 complete layers/final_mlp promoted to double, math/IEEE/no autocast. Original tail layer-loop AST independently matches, with sole final input float-to-double change. Four original parameter-free Timesteps modules still compute float32 constants, explicitly promoted via temporary hooks; no derivative wrt timestep or fully double upstream claimed. All parameter values/dtypes, hooks, attention dtypes/backend flags/frozen digest/modes restored after scoped control.',
    '',f"Four shadow-tail backwards,0 whole-native/prefix forwards or optimizers/retained updates. V/P repeated outputs/upstreams/all gradients/post parameters byteexact: {v['core']['all_pairs_byteexact']}. Independent CPU Horn/direct loss max delta {v['core']['independent_loss_max_delta']:.9g}; V upstream {v['core']['V_upstream_max_delta']:.9g};24 P output-direction FD checks pass. No whole/full-cache function-equivalence claim.",
    '', '|Direction|Step|CPU central difference|Saved gradient dot|Error|Stricter bound|Corroborated|Prior FPC D error|','|---|---:|---:|---:|---:|---:|---|---:|']
for d in v['directional_checks']:lines.append(f"|{d['arm']}/{d['group']}|{d['step']:g}|{d['central_difference']:.12g}|{d['gradient_dot']:.12g}|{d['error']:.9g}|{d['bound']:.9g}|{d['corroborated']}|{d['original_FPC_D']['error']:.9g}|")
lines+=['',f"{sum(x['corroborated'] for x in v['directional_checks'])}/12 predeclared double-control direction checks corroborated.24 temporary symmetric shadow forwards, same original vectors/three steps/signs; all perturbations/output costs/dots independently rebuilt, loss max delta {v['independent_direction_loss_max_delta']:.9g}. Every temporary parameter value restored per call and original float32 dtype restored on context exit. A positive result is bounded derivative feasibility of this changed fixed-prefix function. It does not repair former native conditions, isolate one unique precision cause, implement independent complete transformer backward, certify functional-step descent, fit/generalization or system/physical gain.",
    '',f"{len(f['files'])} frozen identities, {len(receipts)} successful supervised scientific children, {seconds:.6f}s incl imports; RSS {rss}, GPU allocated/reserved {ga}/{gr} bytes.900s/6GiB RSS/8GiB GPU/256MiB prospective caps pass, full child/Windows exits, {retry} retries/{gap} logging gaps. Setup RSS unknown; standard-library closure separate, all old caps/gaps remain.",
    '', 'Original NOC4 loss-increase/P replay/INCOMPLETE, original failed NBR marker, NMR/FPC failed directions and CCR0 stop remain. No optimizer/retained updates/functional step/fit/new noise/real/nearby/trajectory, no production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next distinct question — DESIGN_ONLY\n\nIf every fixed-prefix double derivative prerequisite passes, a separately scoped zero-retained-update functional-step diagnostic of this shadow function can test a predetermined normalized first-order policy and independent actual descent. It cannot certify production/native fp16/FP32 fitting or rescue old AdamW gates; preserve all failed conditions. No next step rule/protocol/runner/freeze/parameter step/optimizer/fit executed by DTC0.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('DTC0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()];assert sum(x['bytes'] for x in files)<256*2**20
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=v['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=v['decision'],deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr),indent=2))
