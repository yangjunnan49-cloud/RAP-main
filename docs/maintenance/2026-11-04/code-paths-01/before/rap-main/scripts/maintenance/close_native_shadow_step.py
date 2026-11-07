"""SFC0 standard-library metadata closure, no model/numerical replay."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/native-shadow-step-control-01';START=time.monotonic()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
f=read(BASE/'freeze.json');v=read(BASE/'validation.json');ex=read(BASE/'bank/execution.json');assert v['passed']
for p,h in f['files'].items():assert sha(p)==h,p
repos={}
for name,p in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
for p in [ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert p.exists()
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),repositories=repos,old_markers_preserved=True))
receipts=[]
for stage in ('freeze','probe','validate'):
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json');assert c['success'] and h['exit_code']==0 and c['full_resource_capture'] and c['optimizer_calls']==0
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=8*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    assert not (folder/'logging_retry.jsonl').exists() and not (folder/'logging_gap.jsonl').exists();receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()}=={'freeze','probe','validate'}
seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<600
rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,scientific_children=3,combined_seconds=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,receipts=receipts,imports_included=True,full_child_and_Windows_exits=True,logging_retries=0,logging_gaps=0,setup_RSS_unknown=True,bookkeeping_separate=True,old_caps_and_gaps_unchanged=True))
save(BASE/'CHECKS.json',dict(passed=True,validation=v,science_caps_pass=True,old_repository_identity_and_markers=True,actual_signed_steps=8,optimizer_API_calls=0,retained_updates=0,fit_admitted=False))
status=dict(utc=now(),status='VALIDATED_SHADOW_FUNCTIONAL_STEP_CONTROL_COMPLETE',decision=v['decision'],functional_conjunction=v['functional_conjunction'],actual_transient_signed_steps=8,optimizer_API_calls=0,retained_updates=0,fit_iterations=0,fit_admitted=False,old_NOC4='INCOMPLETE')
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# SFC0 restored symmetric first-order functional control','',f"Status: {status['status']}. Decision: {v['decision']}.",'',
    'Same DTC0 changed fixed-prefix double shadow tail/original443904 promoted initialized values/fixture/fit00/V-P objectives. Each gradient exactly equals prior sealed DTC0. Predetermined normalized first-order radius min(1e-3,1e-3*L/gradient_norm), both negative and positive signs. Four independent restored probes,16 shadow forwards/four backwards,8 actual signed transient parameter-step evaluations,0 optimizer API calls/retained updates/fit iterations. Every parameter and original output restored byteexact; original float32 values/dtypes/hooks/attention/backend flags/modes/frozen digest restored on exit.',
    '', '|Probe|Radius|Before|Minus|Plus|Descent/ascent gates|','|---|---:|---:|---:|---:|---|']
for row in v['rows']:
    minus=next(x for x in row['checks'] if x['sign']==-1);plus=next(x for x in row['checks'] if x['sign']==1);lines.append(f"|{row['name']}|{row['radius']:.12g}|{minus['loss_before']:.12g}|{minus['loss_after']:.12g}|{plus['loss_after']:.12g}|{row['all_pass']}|")
lines+=['',f"All four independent functional conjunctions {v['functional_conjunction']}; repeated complete arrays byteexact {v['repeat_byteexact']}. CPU NumPy reconstructs every actual signed parameter array/norm/radius/gradient-dot-step, and independent Horn/direct costs, max delta {v['independent_loss_max_delta']:.9g}. Fixed Armijo half-linear-decrease/increase and actual parameter-radius bounds retained, no step search/tolerance repair. This is a finite descent/ascent witness on an exposed synthetic shadow function, not optimizer fitting, native fp16/FP32 repair, physical/generalization/system gain or original method.",
    '',f"{len(f['files'])} frozen identities,3 supervised scientific children,{seconds:.6f}s incl imports; RSS {rss}, GPU allocated/reserved {ga}/{gr} bytes.600s/6GiB RSS/8GiB GPU/128MiB new caps pass/full child-Windows exits/0 logging retries-gaps. Setup RSS unknown, standard-library closure separate, old caps/gaps unchanged.",
    '', 'All NOC4 original loss-increase/replay/INCOMPLETE, NBR failed marker, NMR/FPC direction failures and CCR0 stop remain. No retained updates/fits/new noise/real/nearby/trajectory, no production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next bounded comparison — DESIGN_ONLY\n\nA finite shadow descent witness supports designing a separate conditioning/fit feasibility comparison, with explicit precision/function/capacity controls, fixed exposure and independent retained-update/sampler/heldout gates. Do not run original400 fits or treat this shadow as original native forward. Before useful real metric claims, still need measured incremental RAP value versus strong geometry, untouched official references/edges and complete trajectories; CCR0 retired family cannot be rescued. No next protocol/runner/freeze/fit/trajectory executed here.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('SFC0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()];assert sum(x['bytes'] for x in files)<128*2**20
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=v['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=v['decision'],deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr),indent=2))
