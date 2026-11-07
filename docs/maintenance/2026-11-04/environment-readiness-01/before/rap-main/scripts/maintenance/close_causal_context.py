"""CCR0 standard-library closure, no scientific imports or replay."""
import hashlib
import json
import resource
import subprocess
import time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'docs/maintenance/2026-10-12/causal-context-registration-01'
START=time.monotonic()
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(v,f,indent=2,allow_nan=False); f.write('\n')

validation=read(BASE/'result_validation.json'); assert validation['passed']
result=read(BASE/'results.json'); freeze=read(BASE/'freeze.json'); identities=[]
for p,h in freeze['files'].items():
    assert sha(p)==h,p; identities.append(dict(path=p,sha256=h))
actual={}
for name,folder in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',str(folder),*args],text=True).strip()
    actual[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert actual==freeze['repositories']
assert sha(ROOT/'.gitignore')==sha(BASE/'owner_boundary_snapshot/gitignore')
native=ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01'
assert (native/'INCOMPLETE').is_file() and (native/'attempt-02/INCOMPLETE').is_file()
assert not read(native/'attempt-02/STATUS.json')['scientific_comparison_complete']
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(utc=now(),passed=True,frozen_identities=len(identities),files=identities,repositories=actual,native_NOC4_INCOMPLETE=True))

receipts=[]; total=0.; peak=0; retries=0; gaps=0
for folder in sorted((BASE/'supervision').iterdir()):
    if not folder.is_dir(): continue
    child=read(folder/'child_exit.json'); host=read(folder/'exit.json'); launch=read(folder/'launch.json')
    assert child['full_resource_capture'] and child['peak_RSS_bytes']<=4*2**30 and child['GPU_calls']==0
    assert child['success']==(host['exit_code']==0)
    assert launch['headroom_before_bytes']>=12*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()]
    assert len(samples)==host['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30
    assert host['minimum_observed_headroom_bytes']==min(x['headroom_bytes'] for x in samples)
    total+=child['wall_seconds']; peak=max(peak,child['peak_RSS_bytes'])
    for name,target in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/name).exists():
            count=sum(bool(x.strip()) for x in (folder/name).read_text().splitlines()); retries+=count if target=='retry' else 0; gaps+=count if target=='gap' else 0
    receipts.append(dict(stage=folder.name,child=child,host=host,launch=launch))
assert total<5400 and sum(not x['child']['success'] for x in receipts)==1
assert next(x for x in receipts if x['stage']=='freeze')['child']['success'] is False
audit=dict(utc=now(),passed=True,children=len(receipts),successful_children=sum(x['child']['success'] for x in receipts),retained_prefreeze_failures=1,
    combined_scientific_child_seconds=total,peak_RSS_bytes=peak,GPU_calls=0,all_child_and_Windows_exits_captured=True,
    imports_included_in_scientific_time=True,logging_retries=retries,logging_gaps=gaps,receipts=receipts,
    setup_full_RSS_unknown=True,bookkeeping_excluded_from_scientific_budget=True,old_gaps_and_caps_unchanged=True)
save(BASE/'RESOURCE_AUDIT.json',audit)
checks=dict(utc=now(),passed=True,preflight=read(BASE/'preflight_validation.json'),input_validation=read(BASE/'input_validation.json'),
    pilot_validation=read(BASE/'pilot_validation.json'),result_validation=validation,full58=result['full58'],physical_truth_certified=False,
    native_NOC4_INCOMPLETE_preserved=True,scientific_caps_passed=True,original_repositories_preserved=True,commit_or_sync=False)
if result['full58']: checks['bank_validation']=read(BASE/'bank_validation.json')
save(BASE/'CHECKS.json',checks)
prior_status=BASE/'STATUS.json'; previous=prior_status.read_bytes(); (BASE/'INITIAL_STATUS.json').write_bytes(previous)
status=dict(utc=now(),status='VALIDATED_CAUSAL_CONTEXT_COMPARISON_COMPLETE' if result['full58'] else 'VALIDATED_CAUSAL_CONTEXT_PILOT_PREREQUISITE_STOP',
    decision=result['decision'],stage_complete=True,full58=result['full58'],physical09_cause_resolved=False,native_NOC4='INCOMPLETE',
    new_system_trajectory_metrics=False,neural_or_training_calls=0,old_stops_and_seals_preserved=True,commit_or_sync=False)
prior_status.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
inp=read(BASE/'input/execution.json'); points=sum(a['points'] for t in inp['timings'] if 'arms' in t for a in t['arms']); raw_returns=sum(x['total'] for x in inp['raw_census'])
predfolder=BASE/('bank' if result['full58'] else 'pilot'); preds=[read(p) for p in sorted(predfolder.glob('*_*.json'))]
candidates=[c for z in preds for arm in z['arms'].values() for c in arm['candidates'].values()]
complete=sum(c['status']=='completed' for c in candidates); failed=len(candidates)-complete
selectors={arm:{bundle:{name:sum(z['arms'][arm]['selector_'+bundle]['selected']==name for z in preds) for name in ('RI','GI','GK','GF','N')} for bundle in ('J','W')} for arm in ('A','S','C','D','F')}
save(BASE/'CENSUS.json',dict(utc=now(),raw_frames=len(inp['raw_census']),raw_returns=raw_returns,endpoints=sum(map(len,freeze['endpoints'].values())),
    total_arm_points=points,edges=len(preds),candidate_outputs=len(candidates),completed_candidates=complete,failed_candidates=failed,selectors=selectors,
    timings=inp['timings'],no_unique_scene_independence_claim=True))
report=['# CCR0 causal physical-return context result','',f"Status: {status['status']}. Decision: {result['decision']}.",'',
    'Owner authorized autonomous rounds until the current five-hour usage allowance is exhausted. This stage changes the causal physical observation, with all original endpoints/admissions/reference retained and no new RAP generation or training.',
    '',f"Frozen {len(identities)} identities; {len(inp['raw_census'])} causal raw scans / {raw_returns} returns; {sum(map(len,freeze['endpoints'].values()))} endpoints / {points} point instances across five arms. {len(preds)} original loops / {complete} completed and {failed} failed candidate outputs. Input construction uses current and two previous frames, original frontend transport, actual row IDs and matched-count controls; endpoint0 retains reduced history.",
    '', 'A is the original MGR0 physical cache; S single-scan4000 actual returns; C causal4000; F4000 per available frame; D single-scan count matched to F. Source-ID controls differ from historical A preprocessing, so S-vs-A is not context evidence. Fixed GICP/FGR/normals/support/selection settings remain unchanged. J and W match maximum three-refinement work within an arm; total RAP/pipeline time is not matched.',
    '', 'All eight synthetic transport/source-ID/correction fixtures and independent Cholesky derivative/support checks pass. Every raw selection, corrected coordinate and frontend transport is independently reconstructed; all point PCA/covariances reconstructed from stored neighbors, with32 brute-force membership rows per cloud. This is bounded neighborhood checking, not full independent neighborhood/solver replay. Predictions were sealed before numerical reference. Independent support/selector/objective and reference metrics validate; shared Open3D replays are labelled, not an independent optimizer.', '']
if result['full58']:
    gate=result['gate']; report+=['|Prediction|Mean translation (m)|Mean rotation (deg)|','|---|---:|---:|']
    for key in ('N','A_J','S_J','C_J','D_J','F_J','S_W','C_W','D_W','F_W'):
        d=gate['means'][key]; report.append(f"|{key}|{d['t']:.9f}|{d['R']:.9f}|")
    bad=[key for key,v in gate['engineering_tests'].items() if not v]; inc=[key for key,v in gate['initializer_tests'].items() if not v]
    report+=['',f"Engineering conjunction: {gate['engineering_passed']}; {len(bad)}/{len(gate['engineering_tests'])} tests fail. Initializer increment: {gate['initializer_passed']}; {len(inc)}/{len(gate['initializer_tests'])} tests fail. Exact failures: "+', '.join(bad)+'.',
        '', 'Both matched-count context contrasts and original-native safety are required. Extra-work F-vs-C response cannot rescue a failed primary control. Generic submaps have prior art; no novelty, physical truth, independent scene generalization or system gain is claimed.']
else:
    bad=[x for x in checks['pilot_validation']['checks'] if not x['supported_prerequisite']]; report+=['Pilot support prerequisite fails on '+', '.join(f"{z['seq']} index{z['index']} arm{z['arm']}" for z in bad)+'. Full58 was not admitted. This is a bounded pilot stop, not a universal context failure. Every pilot result/failure remains.']
report+=['', '09 reference physical accuracy/synchronization/dynamics/upstream compensation remains unresolved. Preserve official labels/all edges, including adverse09. Lower physical NN residual is not physical truth. NOC4 stays INCOMPLETE with P-backward reproducibility prerequisite.',
    '', 'The first prefreeze child failed on historical RPC0 validator mapping; original source/receipt retained. AMENDMENT_01 separately binds the original validator snapshot and13 existing amendment identities. New scientific settings/data/gates remain unchanged; no numeric or gate rescue.',
    '',f"{len(receipts)} supervised children include one retained prefreeze failure. Combined {total:.6f}s including imports, peak full RSS {peak} bytes, GPU0; prospective5400s/4GiB/1GiB caps pass. Every child/Windows exit and host observation recorded; {retries} logging retries, {gaps} pointer gaps. Setup full RSS remains unknown; final bookkeeping recorded separately. Old gaps/budgets unchanged; offline timing is not production latency.",
    '', 'Both original HEADs/branches/two-nine tracked dirty sets and historical artifacts remain. No acquisition/install/persistent configuration/process restart/production/default/backbone/manuscript/reference/commit/Git synchronization. See CHECKS, RESOURCE_AUDIT, FINAL_IDENTITY_CHECK, CENSUS and DELIVERY_SEAL.']
(BASE/'REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
nexttext='# Next distinct question\n\n'
if result['full58'] and result['gate']['engineering_passed']:
    nexttext+='CCR0 engineering conjunction passes. A separately scoped unchanged-graph complete-trajectory test can assess whether the measured context improves system metrics before a learned residual. No automatic graph or training has run.\n'
else:
    nexttext+='Stop this exact three-frame/source-ID context construction; no history/cap/radius/normal/FGR/selector/initializer/gate rescue or dependent residual/graph. A distinct independent question is the preserved NOC4 P-backward replay mismatch: inspect the old frozen source/arrays, then prospectively scope target-free restored/no-retained-update upstream/per-parameter reproducibility diagnosis. It must not tune the old learning rate, step scale, noise, initialization or loss-decrease gates, and must preserve original failed probes. This is not an assumption that backward is repaired. No new native protocol or execution is supplied by CCR0 closure.\n'
(BASE/'NEXT_ROUND_PLAN.md').write_text(nexttext,encoding='utf-8')
save(BASE/'BOOKKEEPING.json',dict(utc=now(),wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    standard_library_only=True,no_scientific_replay=True,excluded_from_scientific_child_budget=True))
assert (BASE/'INCOMPLETE').read_text().startswith('CCR0'); (BASE/'INCOMPLETE').unlink()
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()]
assert sum(z['bytes'] for z in files)<2**30
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=result['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],decision=result['decision'],delivery_entries=len(files),children=len(receipts),payload_seconds=total,peak_RSS_bytes=peak),indent=2))
