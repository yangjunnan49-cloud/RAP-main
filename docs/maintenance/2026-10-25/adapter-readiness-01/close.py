"""Close the environment-only assessment and retain all earlier failure evidence."""
import ast,datetime,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;day=root.parent;repo=root.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(n,v):
    with (root/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
for run,rt in [('run01','runtime'),('run02','runtime02')]:
    freeze=json.loads((root/run/'SOURCE_FREEZE.json').read_text(encoding='utf-8'))
    for n,h in freeze['files'].items():assert sha(root/rt/n)==h
    assert sha(root/'PROTOCOL.md')==freeze['protocol_sha256']
assert json.loads((root/'run01/capability/worker_exit.json').read_text())['success'] is False
r=json.loads((root/'run02/capability/RESULTS.json').read_text());assert r['passed'] and len(r['probes'])==4
assert r['actual_RAP_model_or_checkpoint_loads']==r['adapter_training_or_optimizer_calls']==0
assert json.loads((root/'SCOPED_PROCESS_CHECK.json').read_text())['exact_scoped_script_matches']==[]
assert json.loads((root/'WSL_FINAL.json').read_text())['initial_stopped_restored'] is True
history=repo/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/execution-stop-audit-01/RESOURCE_AUDIT.json'
h=json.loads(history.read_text(encoding='utf-8'))
timings=[dict(stage=x['stage'],child_wall_seconds=x['child']['wall_seconds']) for x in h['receipts']]
write('HISTORICAL_TIMING_BASIS.json',dict(source=str(history.relative_to(repo)),sha256=sha(history),
    original_combined_seconds=h['combined_seconds'],stages=timings,prediction_incomplete=True,
    estimates_not_fresh_full_training_benchmark=True))
old=(repo/'AGENTS.md').read_bytes()
with (root/'AGENTS.before.md').open('xb') as f:f.write(old)
header=b'''# October25 adapter restart environment assessment, no training

Owner asked whether adapter work can restart, requested live environment checks and time to a result. AR1 report: docs/maintenance/2026-10-25/adapter-readiness-01/REPORT.md. Existing RTX5070/Torch2.7+cu128 passes unchanged9216MiB gate with9554/9556MiB free; host commit97.5GiB/E free501GiB. Four tiny CUDA float32/64 matrix, double math-SDPA and SVD backward probes PASS. No actual RAP/model/checkpoint/data load or optimizer/adapter update. Generic runtime is capable; full model loading, native adapter gradient replay and functional descent remain unvalidated. No training is pending/admitted automatically.

First metadata query failure for missing einops preserved before Torch/CUDA; runtime02 only records missing distribution instead of aborting, other worker AST/origin identical. No installation. Selected direct source imports Torch/diffusers, not einops; no full dependency-graph assertion. Full original600s check includes failures/repair. Old native NOC4 loss-increase/replay failure, HFIT0 original2GiB artifact stop/INCOMPLETE, RLP2/BRF0 negative routes/caps remain unchanged. Ample disk does not cure an artifact-cap stop. Conditional new-experiment estimates:15-30min model-level go/no-go,30-60min first20-40update loss/checkpoint,1-3h complete same-task16-noise comparison; not guaranteed gain/real-scene efficacy. Historical fit40updates102.67s/audit74.16s supports minute-scale arithmetic only.

AR1 closed after exact scoped helper0 and initial WSLStopped restoration; E image/backup/Junction retained. No environment/default/production/Git/outreach/scheduler/goal-status change. Research UNRESOLVED/manuscript PAUSED; prior pre-quota closeout remains closed and no automatic reset continuation exists. Earlier AGENTS bytes remain verbatim below/backed up.

---

'''
(repo/'AGENTS.md').write_bytes(header+old);assert (repo/'AGENTS.md').read_bytes().endswith(old)
phase=day/'PHASE_RECORD.md';previous=phase.read_bytes()
with (root/'PHASE_RECORD.before.md').open('xb') as f:f.write(previous)
phase.write_bytes(previous+b'''

# AR1 adapter environment and schedule assessment

User requested restart feasibility/current resources/time estimate, not actual fitting. Hardware9556MiB GPU free/97.5GiB commit/501GiB E free; four tiny CUDA backward probes PASS in existing Torch2.7+cu128. No real model/weights/data load or optimizer update. Initial einops metadata error retained; path-independent inventory correction only, other worker AST/origin identical, no install. Model-level load/replay/descent still require a separate bounded preflight; old NOC4/HFIT/RLP2/BRF0 stops remain. Historical40update fit102.67s/audit74.16s; conditional30-60min first trace/checkpoint,1-3h complete fixed-task evaluation, no promised efficacy. Initial WSLStopped restored/helper0/E backup+Junction retained. No automatic training or quota-reset continuation; research UNRESOLVED/manuscript PAUSED.
''')
for p in root.rglob('*.json'):json.loads(p.read_text(encoding='utf-8'))
for p in root.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime(2026,10,25,3,51,2,tzinfo=datetime.timezone.utc)).total_seconds()
write('COSTS_FINAL.json',dict(status='ENVIRONMENT_ASSESSMENT_COMPLETE_NO_ADAPTER_TRAINING',
    elapsed_seconds=elapsed,cap_seconds=600,budget_status='PASS' if elapsed<600 else 'FAIL',
    original_UTC_origin='2026-10-25T03:51:02+00:00',all_attempts_and_repairs_included=True,
    actual_model_loads=0,actual_training_updates=0,old_caps_reset=False,WSL_initial_stopped_restored=True))
files={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in root.rglob('*') if p.is_file() and p.name!='DELIVERY_SEAL.json'}
assert sum(x['bytes'] for x in files.values())<2*1024*1024
write('DELIVERY_SEAL.json',dict(files=files,original_metadata_failure_preserved=True,
    no_model_level_or_full_training_readiness_claim=True))
print(json.dumps(dict(closed=True,elapsed_seconds=elapsed,generic_CUDA_probes=4,actual_training_updates=0)))
