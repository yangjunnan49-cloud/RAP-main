"""HFIT0 available-evidence stop closure, standard library only, no replay."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01';AUDIT=BASE/'execution-stop-audit-01';START=time.monotonic();AUDIT.mkdir()
def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
f=read(BASE/'freeze.json');fit=read(BASE/'fit_validation.json');assert fit['fit_conjunction'] and fit['actual_retained_updates']==40
for q,h in f['files'].items():assert sha(q)==h,q
assert (BASE/'INCOMPLETE').exists() and not (BASE/'prediction_seal.json').exists() and not (BASE/'results.json').exists() and not (BASE/'validation.json').exists()
for folder,seal in [(BASE/'preflight','preflight_seal.json'),(BASE/'fits','fit_seal.json')]:
    value=read(BASE/seal);assert value['freeze_sha256']==sha(BASE/'freeze.json') and value['files']=={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
markers=[ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE'];assert all(q.exists() for q in markers)
receipts=[];retry=0;gap=0
for stage in ('freeze','preflight','fit','validate_fit','predict'):
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json');expected=stage!='predict';assert c['success']==expected and h['exit_code']==(0 if expected else 1) and c['full_resource_capture']
    assert c['peak_RSS_bytes']<=6*2**30 and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=8*2**30
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert len(samples)==h['host_memory_observations'] and samples and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for name,kind in [('logging_retry.jsonl','retry'),('logging_gap.jsonl','gap')]:
        if (folder/name).exists():
            n=len((folder/name).read_text().splitlines());retry+=n if kind=='retry' else 0;gap+=n if kind=='gap' else 0
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {q.name for q in (BASE/'supervision').iterdir() if q.is_dir()}=={x['stage'] for x in receipts}
failure=read(BASE/'FAILURE_predict.json');cap=2*2**30;assert failure['artifact_bytes']>cap and 'artifact_bytes' in failure['error'];seconds=sum(x['child']['wall_seconds'] for x in receipts);assert seconds<1800
cases=[]
for folder in sorted((BASE/'predictions').iterdir()):
    if folder.is_dir():cases.append(dict(name=folder.name,step_files=len(list(folder.glob('step_*.npz'))),source_trajectory_present=(folder/'source_trajectory.npz').exists(),trace_present=(folder/'trace.json').exists(),numerically_validated=False))
assert len(cases)==37 and all(x['step_files']==5 and x['source_trajectory_present'] and x['trace_present'] for x in cases)
status=dict(utc=now(),status='AUDITED_SHADOW_FIT_PILOT_STOP_AT_PREDICTION_ARTIFACT_CAP',decision='COMPLETE40_UPDATES_PARTIAL_UNSEALED37_PREDICTIONS_NO_NOISE_RESULT',scientific_comparison='INCOMPLETE',actual_retained_updates=40,optimizer_API_calls=0,partial_trace_directories=37,complete_prediction_bank=False,conditional_noise_gate_evaluated=False,resource_artifact_cap_pass=False,old_NOC4='INCOMPLETE')
save(AUDIT/'IDENTITY_CHECKS.json',dict(passed=True,frozen_identities=len(f['files']),repositories=repos,old_markers_preserved=True,preflight_fit_seals_match=True))
save(AUDIT/'RESOURCE_AUDIT.json',dict(available_receipts_complete=True,whole_cap_pass=False,artifact_cap_bytes=cap,failure_artifact_bytes=failure['artifact_bytes'],failure_excess_bytes=failure['artifact_bytes']-cap,combined_seconds=seconds,time_RSS_GPU_caps_pass=True,receipts=receipts,logging_retries=retry,logging_gaps=gap,setup_RSS_unknown=True,old_caps_and_gaps_unchanged=True,bookkeeping_separate=True))
save(AUDIT/'CHECKS.json',dict(passed=True,scope='identity/count/resource available-evidence audit only',no_model_numpy_or_numerical_replay=True,fit_validation=fit,partial_case_census=cases,complete_prediction_or_noise_metric_result=False))
save(AUDIT/'STATUS.json',status);(BASE/'STATUS_before_stop_audit.json').write_bytes((BASE/'STATUS.json').read_bytes());(BASE/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
lines=['# HFIT0 stop at prospective prediction artifact cap','',f"Status: {status['status']}. Scientific comparison remains INCOMPLETE.",'',
    'Two-instance preflight byteexact; all40 isolated retained manual double-shadow updates and independent update/Armijo/loss-term/local-matrix gates pass. V fit loss7.22996671078e-6->7.08712625394e-6; P198.329989556->194.401887634. This is numerical fitting feasibility on the exposed synthetic function, not original native repair or a motion/generalization/system gain.',
    '',f"Predict stopped at frozen2GiB artifact cap. Recorded failure {failure['artifact_bytes']} bytes exceeds {cap} by {failure['artifact_bytes']-cap} bytes.37 directories contain all five step files/source trajectory/trace metadata (U17/V17/P3), but no complete51-case execution manifest/prediction seal/results/heldout metric evaluation. These partial files are retained available evidence, not admitted numerical predictions or a selected evaluation subset. No conditional-noise conclusion. No cap increase, prefix deletion, scientific retry or partial GT evaluation.",
    '',f"Five attempted children (four success/one retained cap failure),{seconds:.6f}s incl imports; all full native resource and Windows exits/host observations captured, time/RSS/GPU pass, artifact scope fails. Logging{retry} retries/{gap} gaps. Old caps/gaps unchanged; ordinary setup RSS unknown/final standard-library bookkeeping separate. Live model process exited. Exception cleanup restores source hooks/flags/frozen values/dtypes by code; learned live values after interrupted inference are not asserted restored to initialization, and no such model remains. Checkpoint/production/repository files match frozen identities.",
    '', 'Original NOC4 and failed NBR INCOMPLETE markers, all earlier native/precision/geometry failures and09 physical unknown preserved. HFIT0 INCOMPLETE marker remains. No original-native function equivalence/full-rank capacity/novelty, no production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.']
(AUDIT/'REPORT.md').write_text('\n'.join(lines)+'\n');(AUDIT/'NEXT_ROUND_PLAN.md').write_text('# Next distinct storage prerequisite — DESIGN_ONLY\n\nAudit lossless artifact representation and complete-bank storage requirements prospectively on already available immutable files. Original2GiB failure/full-budget cap remains failed; do not delete prefixes/increase cap/resume the partial scientific bank or infer heldout gains. A distinct redesigned protocol would need new identity/exposure/lifecycle/resource gates before any payload; no exact rate/update/noise/gate rescue. No next runner/freeze/compression/numerical/model/metric execution here.\n')
(AUDIT/'audit_source.py').write_bytes(Path(__file__).read_bytes());save(AUDIT/'BOOKKEEPING.json',dict(standard_library_only=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
files=[dict(path=str(q.relative_to(AUDIT)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(AUDIT.rglob('*')) if q.is_file()];save(AUDIT/'DELIVERY_SEAL.json',dict(status=status['status'],files=files,entries=len(files)))
available=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file() and q.name!='AVAILABLE_DELIVERY_SEAL.json'];save(BASE/'AVAILABLE_DELIVERY_SEAL.json',dict(status=status['status'],scientific_complete=False,files=available,entries=len(available),original_artifact_cap_still_failed=True))
print(json.dumps(dict(status=status['status'],actual_retained_updates=40,partial_unsealed_traces=37,seconds=seconds,artifact_cap_failed=True,audit_deliveries=len(files),available_deliveries=len(available)),indent=2))
