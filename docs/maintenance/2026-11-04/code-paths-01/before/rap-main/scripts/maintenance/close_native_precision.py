"""FPC0 standard-library metadata closure only."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/native-precision-control-01';START=time.monotonic()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
f=read(BASE/'freeze.json');v=read(BASE/'validation.json');ex=read(BASE/'traces/execution.json');assert v['passed']
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
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=6*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/filename).exists():
            n=len((folder/filename).read_text().splitlines());retry+=n if kind=='retry' else 0;gap+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}==set(stages)
seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<900
rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,scientific_children=len(receipts),combined_seconds=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,receipts=receipts,
    imports_included=True,full_child_and_Windows_exits=True,logging_retries=retry,logging_gaps=gap,setup_RSS_unknown=True,bookkeeping_separate=True,old_caps_and_gaps_preserved=True))
save(BASE/'CHECKS.json',dict(passed=True,validation=v,science_caps_pass=True,old_markers_and_repository_identity=True,native_fit_admitted=False))
status=dict(utc=now(),status='VALIDATED_BOUNDED_PRECISION_CONTROLS_COMPLETE',decision=v['decision'],condition_conjunctions=v['condition_conjunctions'],optimizer_calls=0,retained_updates=0,native_fit_admitted=False,production_backend_changed=False,old_NOC4='INCOMPLETE')
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# FPC0 whole-native precision controls','',f"Status: {status['status']}. Decision: {v['decision']}.",'',
    'Same original checkpoint/443904 initialized parameters/synthetic fixture/fit00 noise/modes/tau1/backward factors. Full model uses original float32 weights/inputs without autocast and temporary12-layer float32 attention dtype under scoped math/IEEE. All four adapter linear boundaries and prefixes verified float32; actual math dispatch recorded. Every attention dtype/backend flag restored, parameters/frozen digest/modes preserved. S retains original float32 endpoint/residual arithmetic; D computes endpoint/residual in float64. These are distinct numerical controls; original default/NMR0 conditions and failed gates stay sealed.',
    '',f"Sixteen full-or-tail forwards/backwards/four explicit prefixes; every{len(v['core']['pairs'])} repeat/full-cache pair byteexact: {v['core']['all_pairs_byteexact']}. All outputs/upstreams/trainable gradients/post parameters independently recounted. CPU Horn/direct loss max delta {v['core']['independent_loss_max_delta']:.9g}; V upstream {v['core']['V_upstream_max_delta']:.9g};96 pose-output directional FD checks pass. Equations are independent; complete transformer backward is not independently implemented.",
    '', '|Condition/direction|Step|CPU central difference|Saved gradient dot|Error|Bound|Corroborated|Original NMR error|','|---|---:|---:|---:|---:|---:|---|---:|']
for d in v['directional_checks']:lines.append(f"|{d['condition']}/{d['arm']}/{d['group']}|{d['step']:g}|{d['central_difference']:.9g}|{d['gradient_dot']:.9g}|{d['error']:.9g}|{d['bound']:.9g}|{d['corroborated']}|{d['original_NMR']['error']:.9g}|")
for condition in ('S','D'):
    checks=[x for x in v['directional_checks'] if x['condition']==condition];lines+=['',f"Condition{condition}: {sum(x['corroborated'] for x in checks)}/12 fixed whole-direction records corroborated; conjunction {v['condition_conjunctions'][condition]}."]
lines+=['', 'Twenty-four additional full forwards shared by S/D objectives; fixed original vectors/three step sizes/signs, every temporary parameter perturbation and output archived, all parameters restored after each call, zero direction backwards/optimizer. V absolute1e-3 criterion is coarse relative to tiny derivatives; passing it does not demonstrate relative accuracy. No step/precision condition selected posthoc for a fit and no tolerance adjusted. FP32 model jointly changes many operators; the S/D contrast isolates endpoint/objective arithmetic within that model, not every source of historical mismatch. Independent direction losses/perturbations/dots reproduced.',
    '',f"{len(f['files'])} frozen identities, {len(receipts)} supervised scientific children, {seconds:.6f}s incl imports, RSS {rss}, GPU allocated/reserved {ga}/{gr} bytes.900s/6GiB RSS/6GiB GPU/256MiB new caps pass; full child/Windows exits, {retry} logging retries/{gap} gaps. Setup RSS unknown; standard-library final closure separate; old caps/gaps unchanged.",
    '', 'No optimizer calls/retained updates/fits/new noise/real/nearby/trajectory, no functional-step descent/native learning/physical/generalization/system gain/novelty or unique historical cause. Original NOC4 loss-increase/P mismatch/INCOMPLETE, failed original NBR marker, CCR0 stop and all old seals remain. No production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next distinct prerequisite — DESIGN_ONLY\n\nPreserve every precision condition and all failures. A condition with complete fixed directional corroboration may support a separately scoped zero-retained-update functional-step diagnostic from original initialization, with a predetermined step rule/descent gate and independent output/parameter reconstruction. It does not admit400-update fitting or repair old AdamW/precision gates. If no condition passes, distinguish remaining roundoff/local derivatives before any step. No next protocol/runner/freeze/functional step/optimizer/fit executed here.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('FPC0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()];assert sum(x['bytes'] for x in files)<256*2**20
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=v['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=v['decision'],deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr),indent=2))
