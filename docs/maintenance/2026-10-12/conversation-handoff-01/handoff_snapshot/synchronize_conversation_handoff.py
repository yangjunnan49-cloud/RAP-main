"""Bounded metadata/identity handoff audit. Standard library only; no science replay."""
import hashlib
import json
import math
import re
import resource
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATE=ROOT/'docs/maintenance/2026-10-12'
BASE=DATE/'conversation-handoff-01'
START=time.monotonic()
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(obj,f,indent=2,allow_nan=False); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()
def mapped(p):
    if p.startswith('E:\\') or p.startswith('E:/'): return Path('/mnt/e')/p[3:].replace('\\','/')
    return Path(p)
records=[]
def identity(p,expected,label):
    actual=sha(p); assert actual==expected,(label,str(p),actual,expected)
    records.append(dict(path=str(p),sha256=actual,binding=label)); return actual

deliveries=[]
for name,count in [('scan-level-graph-feasibility-01',147),('measured-gicp-registration-01',344),
    ('reference-physical-consistency-01',122),('reference-physical-consistency-delivery-note-01',2)]:
    folder=DATE/name; seal=read(folder/'DELIVERY_SEAL.json'); assert len(seal['files'])==count
    for row in seal['files']:
        path=(folder/row['path']).resolve(); assert folder.resolve() in path.parents
        identity(path,row['sha256'],name+' delivery')
    seal_hash=sha(folder/'DELIVERY_SEAL.json')
    records.append(dict(path=str(folder/'DELIVERY_SEAL.json'),sha256=seal_hash,binding='current delivery manifest'))
    deliveries.append(dict(stage=name,entries=count,seal_sha256=seal_hash,passed=True))

benchmark=ROOT/'docs/meeting_20261011/benchmark'
sources=read(benchmark/'freeze.json')['sources']; assert len(sources)==71
for path,h in sources.items(): identity(mapped(path),h,'benchmark source')
trajectories=read(benchmark/'attempt03/trajectory_seal.json'); assert len(trajectories)==144
for path,h in trajectories.items(): identity(mapped(path),h,'benchmark trajectory binding')
result=read(benchmark/'attempt03/results.json'); rows=result['rows']; assert len(rows)==result['complete_runs']==36 and result['independent_metrics_validated']
expected={(rep,s,model) for rep in (1,2,3) for s in ('00','05','06','07','09','10') for model in ('RAP-SLAM','KISS-SLAM')}
assert {(row['rep'],row['sequence'],row['model']) for row in rows}==expected
assert all(row['exit']==0 and row['resource']['complete'] for row in rows)
scalar={}
for model,ter,ate in [('RAP-SLAM',.447166761,1.091071657),('KISS-SLAM',.478613920,.699688694)]:
    selected=[row for row in rows if row['model']==model]; assert len(selected)==18
    scalar[model]={}
    for metric,target in [('ter',ter),('ate',ate)]:
        values=[float(row[metric]) for row in selected]; assert all(math.isfinite(v) for v in values)
        mean=statistics.fmean(values); assert abs(mean-target)<=5.1e-10
        cohort_means=[statistics.fmean(float(row[metric]) for row in selected if row['rep']==rep) for rep in (1,2,3)]
        scalar[model][metric]=dict(stored_row_mean=mean,three_complete_cohort_means=cohort_means,
            population_std_across_three_cohort_means=statistics.pstdev(cohort_means))

rpc=DATE/'reference-physical-consistency-01'; rpc_status=read(rpc/'STATUS.json'); assert rpc_status['diagnostic_complete'] and not rpc_status['physical_cause_resolved']
assert rpc_status['optimizer_neural_graph_calls']==0 and not rpc_status['new_system_metrics'] and not (rpc/'INCOMPLETE').exists()
native=ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01'
native_status=read(native/'attempt-02/STATUS.json'); assert native_status['keep_INCOMPLETE'] and not native_status['scientific_comparison_complete'] and native_status['fit_updates']==0 and native_status['optimizer_probe_calls']==4
for p in (native/'INCOMPLETE',native/'attempt-02/INCOMPLETE',native/'attempt-02/STATUS.json'):
    assert p.is_file(); records.append(dict(path=str(p),sha256=sha(p),binding='native stop and preserved marker'))
assert (DATE/'scan-level-graph-feasibility-01/STATUS.json').is_file()
assert read(DATE/'scan-level-graph-feasibility-01/STATUS.json')['decision']=='NO_SAFE_MATERIAL_SCAN_GRAPH_SIGNAL'
assert read(DATE/'measured-gicp-registration-01/STATUS.json')['decision']=='NO_SAFE_MEASURED_REGISTRATION_HEADROOM'

actual={}
for name,path in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',str(path),*args],text=True).strip()
    actual[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert actual==read(rpc/'freeze.json')['repositories']==read(DATE/'RPC0_FINAL_HANDOFF_CHECK.json')['repositories']

for name in ('START_HERE.md','HANDOFF.md'):
    p=BASE/name
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not target.startswith(('http:','https:','#')): assert (p.parent/target).resolve().is_file(),target
anchors=[benchmark/'REPORT.md',benchmark/'attempt03/validation.json',benchmark/'RESOURCE_AUDIT.json',
    rpc/'NEXT_ROUND_PLAN.md',rpc/'PROTOCOL.md',rpc/'AMENDMENT_01.md',rpc/'EXECUTION_NOTE.md',rpc/'validation.json',
    DATE/'metric-innovation-research-01/REPORT.md',DATE/'metric-innovation-research-01/NEXT_QUESTIONS.md',DATE/'stage-review-01/REPORT.md',
    ROOT/'docs/maintenance/2026-10-05/temporal-identity-audit-01/REPORT.md',ROOT/'docs/maintenance/2026-10-05/online-geometry-consistency-01/REPORT.md',
    ROOT/'scripts/maintenance/invoke_mgr_supervised_wsl.ps1',DATE/'RPC0_FINAL_HANDOFF_CHECK.json']
for p in anchors:
    assert p.is_file(); records.append(dict(path=str(p),sha256=sha(p),binding='handoff source anchor'))
assert (ROOT/'docs/maintenance/2026-10-05/online-geotransformer-01/input-bank').is_dir()
snapshot=BASE/'handoff_snapshot'; snapshot.mkdir()
for p in (ROOT/'AGENTS.md',DATE/'PHASE_RECORD.md',Path(__file__).resolve()):
    destination=snapshot/p.name; destination.write_bytes(p.read_bytes()); assert sha(destination)==sha(p)

identity_report=dict(utc=now(),passed=True,delivery_checks=deliveries,benchmark_source_entries=71,benchmark_trajectory_bindings=144,
    hash_references=len(records),distinct_paths=len({record['path'] for record in records}),files=records,repositories=actual,
    scope='bounded file SHA256/JSON identities and read-only Git; no Linux numerical-library import or scientific replay')
save(BASE/'IDENTITY_CHECKS.json',identity_report)
save(BASE/'CHECKS.json',dict(utc=now(),passed=True,selected_delivery_entries=615,delivery_seals=4,benchmark_sources=71,trajectory_bindings=144,
    stored36_run_grid_complete=True,stored_scalar_arithmetic=scalar,RPC0_complete_physical_cause_unresolved=True,native_NOC4_INCOMPLETE_preserved=True,
    source_links_and_anchors_checked=True,original_repositories_preserved=True,new_numerical_or_raw_replay=False,
    new_model_neural_optimizer_graph_trajectory_calls=0,install_config_process_mutation=False,commit_or_sync=False,
    bookkeeping_wall_seconds_before_delivery_seal=time.monotonic()-START,
    bookkeeping_RSS_observed_before_delivery_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    no_historical_scientific_budget_amendment=True))
save(BASE/'STATUS.json',dict(utc=now(),status='VALIDATED_INFORMATION_SYNC_COMPLETE',owner_request='Information synchronization before a new conversation',
    scientific_state_unchanged=True,current_latest_diagnostic='RPC0 complete,09 physical cause unresolved',latest_complete_system='2026-10-11 benchmark attempt03',
    native_NOC4='INCOMPLETE/P backward reproducibility prerequisite',next_route='DESIGN_ONLY causal context/submap feasibility, then conditional frozen-RAP residual',
    next_protocol_runner_freeze_or_execution=False,new_chat_created=False,new_neural_raw_optimizer_trajectory_calls=0,commit_or_sync=False))
seal_files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()]
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status='VALIDATED_INFORMATION_SYNC_COMPLETE',files=seal_files,entries=len(seal_files),scientific_state_unchanged=True))
print(json.dumps(dict(status='VALIDATED_INFORMATION_SYNC_COMPLETE',delivery_entries=len(seal_files),prior_delivery_entries_checked=615,
    benchmark_sources=71,trajectory_bindings=144,hash_references=len(records),distinct_paths=len({record['path'] for record in records}),new_scientific_calls=0),indent=2))
