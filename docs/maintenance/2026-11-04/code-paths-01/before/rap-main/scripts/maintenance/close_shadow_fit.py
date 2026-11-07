"""HFIT0 standard-library scientific metadata closure, no numerical/model replay."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01';START=time.monotonic()
def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
f=read(BASE/'freeze.json');v=read(BASE/'validation.json');result=read(BASE/'results.json');fit=read(BASE/'fits/execution.json');assert v['passed'] and v['fit_validation']['fit_conjunction'] and fit['actual_retained_updates']==40
for q,h in f['files'].items():assert sha(q)==h,q
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
for q in [ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert q.exists()
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),repositories=repos,old_markers_preserved=True))
receipts=[];retries=0;gaps=0
stages=('freeze','preflight','fit','validate_fit','predict','evaluate')
for stage in stages:
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json');assert c['success'] and h['exit_code']==0 and c['full_resource_capture'] and c['optimizer_calls']==0
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=8*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/filename).exists():
            n=len((folder/filename).read_text().splitlines());retries+=n if kind=='retry' else 0;gaps+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {q.name for q in (BASE/'supervision').iterdir() if q.is_dir()}==set(stages)
seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<1800
rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,scientific_children=6,combined_seconds=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,receipts=receipts,imports_included=True,full_child_and_Windows_exits=True,logging_retries=retries,logging_gaps=gaps,setup_RSS_unknown=True,bookkeeping_separate=True,old_caps_and_gaps_preserved=True))
save(BASE/'CHECKS.json',dict(passed=True,validation=v,science_caps_pass=True,old_repository_identity_and_markers=True,actual_retained_updates=40,optimizer_API_calls=0,original_NOC4_INCOMPLETE=True,real_or_system_expansion_admitted=False))
status=dict(utc=now(),status='VALIDATED_BOUNDED_SHADOW_CONDITIONED_FIT_PILOT_COMPLETE',decision=result['decision'],fit_feasibility=True,conditional_noise_conjunction=v['conditional_noise_conjunction'],actual_retained_updates=40,optimizer_API_calls=0,original_native_equivalence=False,real_or_system_expansion_admitted=False,old_NOC4='INCOMPLETE')
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# HFIT0 twenty-update shadow conditioning pilot','',f"Status: {status['status']}. Decision: {result['decision']}.",'',
    'Two strict original instances separate frozen-float32-prefix from learned-double-tail lifecycle. Original initialized443904 trainable values/B=0/copy-descriptor known synthetic3000-point fixture; old fit00/tau1 only, original V/P objectives/backward factors. Zero-update lifecycle exactly reproduces both SAR0 source-sampler traces. Fixed normalized first-order radius min(.001,.001*L/G),20 actual retained manual gradient updates per arm;40total,0 optimizer API calls. Float64 learned states are saved in isolated artifacts and preserved without intermediate float32 rounding; all original live values/dtypes/modes/hooks/attention/backend bindings restored. This is a changed shadow function, not original native fitting/400 updates or a production checkpoint change.',
    '', '|Arm|Original fit loss|After20|Relative loss decrease|Accepted update gates|','|---|---:|---:|---:|---:|']
for arm in ('V','P'):
    rows=[x for x in fit['records'] if x['arm']==arm];before=rows[0]['loss_before'];after=rows[-1]['loss_after'];lines.append(f"|{arm}|{before:.12g}|{after:.12g}|{100*(before-after)/before:.6f}%|{sum(x['Armijo_pass'] for x in rows)}/20|")
fv=v['fit_validation'];lines+=['',f"Every40 before/gradient/after array, actual step/norm/dot/Armijo/source term/continuation independently reconstructed. Horn/direct weighted-loss terms max delta {fv['independent_loss_terms_max_delta']:.9g};240 P output-direction FD checks pass; first/final32 complete local A/B products max {max(x['delta'] for x in fv['local_A_B_checks']):.9g}. Initial gradients exactly bind prior DTC0; A starts inactive at B=0 and all group activities are reported. Nominal equal parameter/update counts do not prove full-rank/equal active capacity or equal total work. Parameter-rule replay uses stored gradients and shared neural implementation, not independent full neural optimizer replay.",
    '', '51 complete paired five-step source Euler+rigidity=True traces: U/V20/P20 onfit00 and all16 old eval noises. Full prediction bank sealed before new pose errors. No truth/target/cache in inference, no new noise draw/scene, no seed/iteration/pose selection. Float64 carried state/velocity/rigidity, float32 prefix/model/timestep and original source output buffers retained. Independent765 Horn part fits and all state/cast/source-return bindings pass.',
    '', '|Arm/part|Baseline mean t(m)|Student mean t(m)|Baseline mean R(deg)|Student mean R(deg)|Joint nonworse/16|Cell pass|','|---|---:|---:|---:|---:|---:|---|']
for c in result['summary']['cells']:lines.append(f"|{c['arm']}/{c['part']}|{c['B']['t']['mean']:.9g}|{c['A']['t']['mean']:.9g}|{c['B']['R']['mean']:.9g}|{c['A']['R']['mean']:.9g}|{c['joint_nonworse']}|{c['passed']}|")
failed=[f"{c['arm']}/part{c['part']}:{k}" for c in result['summary']['cells'] for k,value in c['tests'].items() if not value]
lines+=['',f"Conditional old-noise four-cell conjunction {v['conditional_noise_conjunction']}; failed checks {failed}. Original frozen NOC1 gate formula/values applied prospectively to this distinct new function/noise set without threshold rescue. Fit00 diagnostics separate; all16 evaluation results reported. This is one exposed synthetic fixture, not independent scenes/fresh-noise/site robustness. A positive training-loss curve does not establish material pose/physical/generalization/system/RAP increment or novelty.",
    '',f"{len(f['files'])} frozen identities,6 supervised scientific children,{seconds:.6f}s incl imports; RSS {rss}, GPU allocated/reserved {ga}/{gr} bytes.1800s/6GiB RSS/8GiB GPU/2GiB new prospective caps pass/full child-Windows exits/{retries} logging retries/{gaps} gaps. Setup RSS unknown, standard-library final closure separate, old caps/gaps remain.",
    '', 'All original NOC4 native AdamW/fp16/FP32 loss-increase/replay/INCOMPLETE, failed original NBR marker, earlier direction failures and CCR0/SGC0/MGR0 retired families/09 physical unknown remain. No exact pilot rate/update/noise/init/gate rescue or automatic nearby/real/trajectory expansion. No production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next boundary — DESIGN_ONLY\n\nKeep complete numerical-fit and complete conditional-noise evidence separate. If the material noise conjunction fails, retire this exact20-update/fit00/shadow-policy family without step/rate/noise/precision/gate rescue; no nearby/real/system expansion. Any distinct observation/objective/representation feasibility proposal needs equal-active-capacity/strong-geometry controls and new prospective source/derivative/sampler/exposure/heldout rules. Synthetic fit success does not bypass CCR0 failed headroom or original native INCOMPLETE. No next protocol/runner/freeze/fit/real/trajectory executed by HFIT0.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('HFIT0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()];assert sum(x['bytes'] for x in files)<2*2**30
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=result['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=result['decision'],deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr),indent=2))
