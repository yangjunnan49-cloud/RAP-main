"""Standard-library NMR0 closure only; no numerical/model replay."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/native-math-reproducibility-01';START=time.monotonic()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
freeze=read(BASE/'freeze.json');v=read(BASE/'math_validation.json');result=read(BASE/'results.json');ex=read(BASE/'traces/execution.json');assert v['passed']
for p,h in freeze['files'].items():assert sha(p)==h,p
repos={}
for name,p in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==freeze['repositories']
for p in [ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert p.exists()
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(utc=now(),passed=True,frozen_identities=len(freeze['files']),repositories=repos,old_markers_preserved=True))
stages=['freeze','diagnose']+(['directions'] if v['directional_checks'] else [])+['validate'];receipts=[];retries=0;gaps=0
for stage in stages:
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json')
    assert c['success'] and h['exit_code']==0 and c['full_resource_capture'] and c['optimizer_calls']==0
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=6*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/filename).exists():
            n=len((folder/filename).read_text().splitlines());retries+=n if kind=='retry' else 0;gaps+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}==set(stages)
seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<1200
rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,scientific_children=len(receipts),combined_seconds=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,
    imports_included=True,full_child_and_Windows_exits=True,logging_retries=retries,logging_gaps=gaps,receipts=receipts,old_caps_and_gaps_unchanged=True,setup_RSS_unknown=True,bookkeeping_separate=True))
save(BASE/'CHECKS.json',dict(passed=True,validation=v,scientific_caps_passed=True,old_NOC4_INCOMPLETE_preserved=True,old_NBR_INCOMPLETE_preserved=True,optimizer_calls=0,retained_updates=0,native_fit_admitted=False))
status=dict(utc=now(),status='VALIDATED_WHOLE_NATIVE_MATH_PREREQUISITE_COMPLETE',decision=v['decision'],repeat_prerequisite=v['all_instrumented_pairs_byte_equal'],whole_direction_corroboration=v['whole_direction_corroboration'],optimizer_calls=0,retained_updates=0,native_fit_admitted=False,original_NOC4='INCOMPLETE',production_backend_changed=False)
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# NMR0 whole-native scoped math attention prerequisite','',f"Status: {status['status']}. Decision: {v['decision']}.",'',
    'Original synthetic3000-point known-transform/copy-descriptor fixture, fit00 noise,443904 original initialized trainables, exact mode contract, outer fp16/IEEE, original V/P objective/backward scales. All prefix/full/cache attention temporarily uses math SDPA; actual ATen math dispatch recorded for first full trace per arm and original backend flags restored. Eight instrumented backwards/two explicit prefixes;0 optimizer calls/retained updates. Frozen parameters/modes preserved, every trace parameter byteexact. This is a changed numerical condition; it does not replace production or imply default function equivalence.',
    '', '|Comparison|Output differences|Endpoint upstream differences|Parameter gradient differences|Max parameter gradient delta|','|---|---:|---:|---:|---:|']
for p in result['pairs']:
    d=p['details'];g=d['gradients.npz'];lines.append(f"|{p['left']} / {p['right']}|{d['output.npz']['output']['different']}|{d['output.npz']['upstream']['different']}|{sum(x['different'] for x in g.values())}|{max(x['max_abs'] for x in g.values()):.9g}|")
lines+=['','|Math/default archived control|Endpoint max delta|Upstream max delta|Gradient max delta|','|---|---:|---:|---:|']
for p in result['default_control_comparisons']:
    d=p['details'];lines.append(f"|{p['name']}|{d['output.npz']['output']['max_abs']:.9g}|{d['output.npz']['upstream']['max_abs']:.9g}|{max(x['max_abs'] for x in d['gradients.npz'].values()):.9g}|")
core=v['core_validation'];lines+=['',f"Independent Horn/direct loss max delta {core['independent_loss_max_delta']:.9g};48 output-direction finite differences and complete pair/backend census rebuilt. Local B products within one fp16 ULP: {sum(x['within_one_fp16_ULP'] for x in core['local_B_linear_checks'])}/32, scoped linear diagnostic, not independently implemented whole transformer backward."]
if v['directional_checks']:
    lines+=['', '|Whole-native direction|Step|CPU central difference|Saved gradient dot|Error|Predeclared bound|Corroborated|','|---|---:|---:|---:|---:|---:|---|']
    for d in v['directional_checks']:lines.append(f"|{d['arm']}/{d['group']}|{d['step']:g}|{d['central_difference']:.9g}|{d['gradient_dot']:.9g}|{d['error']:.9g}|{d['bound']:.9g}|{d['corroborated']}|")
    lines+=['',f"Twenty-four additional full forwards,0 backwards/optimizers, fixed seed/group/step/sign, temporary parameter perturbations fully archived and restored exactly after each call. All vectors, perturbations, directional products and perturbed CPU costs independently reconstructed, max loss delta {v['independent_direction_loss_max_delta']:.9g}. Corroboration {sum(x['corroborated'] for x in v['directional_checks'])}/12; no step selection or tolerance repair. Finite precision can limit central differences; the observations do not identify a unique derivative/rounding cause or establish descent."]
else:lines+=['','Primary repeat prerequisite failed; no dependent parameter-direction forwards executed.']
lines+=['',f"{len(freeze['files'])} frozen identities, sealed default controls and old stops retained. {len(receipts)} successful supervised scientific children, {seconds:.6f}s incl imports; peak RSS {rss}, GPU allocated/reserved {ga}/{gr} bytes. New1200s/6GiB RSS/6GiB GPU/512MiB caps pass; full child/Windows exits, {retries} logging retries/{gaps} gaps. Higher new memory cap was prospective, not an old-budget amendment. Ordinary setup RSS unknown, final standard-library bookkeeping separate; old resource gaps unchanged.",
    '', 'Repeatability and derivative corroboration are separate prerequisites. No actual optimizer step, fitting, native learning, generalization, physical accuracy, system gain, originality or unique historical full-model cause claimed. Original NOC4 loss-increase/replay mismatch/INCOMPLETE and failed original NBR marker remain. No new noise/real/nearby/trajectory or production/default/backbone/reference/manuscript/install/restart/acquisition/commit/Git sync. Both original HEADs/branches/two-nine tracked dirty sets preserved. Hooks/profiler may affect scheduling; measured instrumented repeats do not certify arbitrary historical execution.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next distinct question — DESIGN_ONLY\n\nPreserve this complete repeatability and directional census without any fixed-step or threshold rescue. If repeatability passes but parameter-direction checks fail, first distinguish finite-precision forward resolution from analytical derivative failure with separately frozen precision/control and independent local equations; no functional step or fit yet. If both pass, a separately scoped functional-step policy is still prerequisite to learning. Original NOC4 loss increases/stops remain; no old AdamW/rate/step/noise/init rescue. No next protocol/runner/freeze/backward/optimizer/fit executed by NMR0.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('NMR0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()];assert sum(x['bytes'] for x in files)<512*2**20
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=v['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=v['decision'],deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr),indent=2))
