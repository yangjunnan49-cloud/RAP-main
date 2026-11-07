"""SAR0 standard-library metadata closure only, no numerical/model imports."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/shadow-sampler-extraction-01';START=time.monotonic()
def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
f=read(BASE/'freeze.json');v=read(BASE/'validation.json');ex=read(BASE/'bank/execution.json');assert v['passed']
for q,h in f['files'].items():assert sha(q)==h,q
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
for q in [ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert q.exists()
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),repositories=repos,old_markers_preserved=True))
receipts=[];retries=0;gaps=0
for stage in ('freeze','bank','validate'):
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json');assert c['success'] and h['exit_code']==0 and c['full_resource_capture'] and c['optimizer_calls']==0
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=8*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/filename).exists():
            n=len((folder/filename).read_text().splitlines());retries+=n if kind=='retry' else 0;gaps+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {q.name for q in (BASE/'supervision').iterdir() if q.is_dir()}=={'freeze','bank','validate'}
seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<900
rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,scientific_children=3,combined_seconds=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,receipts=receipts,imports_included=True,full_child_and_Windows_exits=True,logging_retries=retries,logging_gaps=gaps,setup_RSS_unknown=True,bookkeeping_separate=True,old_caps_and_gaps_preserved=True))
save(BASE/'CHECKS.json',dict(passed=True,validation=v,science_caps_pass=True,old_repository_identity_and_markers=True,no_losses_truth_targets=True,backwards=0,optimizer_calls=0,retained_updates=0,fit_admitted=False))
status=dict(utc=now(),status='VALIDATED_SHADOW_SOURCE_SAMPLER_BINDINGS_COMPLETE',decision=v['decision'],extraction_and_sampler_conjunction=v['extraction_and_sampler_conjunction'],backwards=0,optimizer_calls=0,retained_updates=0,fit_admitted=False,original_native_equivalence=False,old_NOC4='INCOMPLETE')
(BASE/'PREPARATION_STATUS.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# SAR0 target-free source sampler/extraction precision bindings','',f"Status: {status['status']}. Decision: {v['decision']}.",'',
    'Original checkpoint/443904 initial parameters/B=0/modes. Two already generated original noise00 arrays fit/eval, two prefix paths (unchanged helper versus original full-FP32 layer9 hook), two repeats each. Eight complete five-step source Euler+rigidity-forcing rollouts; no truth/target arrays/losses/pose metrics/backwards/optimizer/retained updates. Prefix state/model float32, carried state/double-tail/rigidification float64, original source output buffers float32. Four float32 time constants explicitly promoted within double tail. Model values/dtypes/modes/hook/backend and original rigidifier callback binding restored.',
    '',f"20 prefix helper calls/20 complete-FP32 flow forwards/40 double tails/40 rigidifications/160 time-constant promotions. Independent Horn eigensystem reconstructs120 part rigidifications, max delta {v['independent_rigid_max_delta']:.9g}; state recurrence max {v['independent_state_max_delta']:.9g}. Source Euler AST exact; input/timestep casts and every raw endpoint/forced-state/source-buffer precision independently reconstructed. All{len(v['buffer_cast_checks'])} float32 buffer comparisons within one ULP, {sum(x['byteequal'] for x in v['buffer_cast_checks'])} byteequal. Fit00 tau1 prefixes exactly bind prior FPC0 D. This is source/extraction/arithmetic validation, not independent complete neural implementation.",
    '', '|Noise|Left|Right|Complete arrays byteexact|Max delta|','|---|---|---|---|---:|']
for row in v['pairs']:lines.append(f"|{row['noise']}|{row['left']}|{row['right']}|{row['byteexact']}|{row['max_delta']:.9g}|")
lines+=['', 'All noise/path/repeat bindings reported, no output selection or gate relaxation. Full-hook path evaluates additional frozen model work; this is a control, not an equal-work or latency comparison. Original configured5-step Euler/rigidity=True retained, no anchor or rigidification deletion. The explicit mixed-precision function differs from original native fp16/FP32, and source float32 return buffers still limit stored precision. Passing at initial state does not prove post-fit equivalence, rank/active capacity, learning, fresh-noise robustness, physical/generalization/system gains or novelty.',
    '',f"{len(f['files'])} frozen identities,3 supervised scientific children,{seconds:.6f}s incl imports; RSS {rss}, GPU allocated/reserved {ga}/{gr} bytes.900s/6GiB RSS/8GiB GPU/512MiB prospective caps pass/full child-Windows exits/{retries} logging retries/{gaps} gaps. Setup RSS unknown, standard-library final closure separate, old caps/gaps unchanged.",
    '', 'All original NOC4 loss-increase/P replay/INCOMPLETE, failed original NBR marker, NMR/FPC direction gaps and CCR0 retired family/09 physical unknown remain. No fit/new noise/real/nearby/trajectory benchmark/production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next retained-update feasibility — DESIGN_ONLY\n\nWith ADR0 activated derivatives and SAR0 original-state sampler/extraction bindings complete, design a separate small bounded retained-update comparison on the explicitly defined shadow function. Preserve double learned parameter states instead of rounding them through per-step float32 restoration; a separate frozen-prefix instance or explicit lifecycle is required. Predeclare optimizer policy/exposure/capacity/update/heldout/sampler/metric gates and independently reconstruct every update and full paired predictions before any reference errors. Do not start original400 fits or rescue failed native conditions. No next fit protocol/runner/freeze/retained update/heldout pose metric executed by SAR0.\n')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('SAR0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()];assert sum(x['bytes'] for x in files)<512*2**20
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=v['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=v['decision'],deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr),indent=2))
