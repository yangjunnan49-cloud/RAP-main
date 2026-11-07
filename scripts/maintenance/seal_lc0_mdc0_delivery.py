"""Seal final documentation and verify scientific identities without reruns."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
MAIN=Path(__file__).resolve().parents[2];SLAM=MAIN.parent/'RAP-SLAM';ROOT=MAIN/'docs/maintenance/2026-10-07'
LC=ROOT/'retrieval-placement-audit-01';MD=ROOT/'metric-conflict-decomposition-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
files=[MAIN/'AGENTS.md',ROOT/'PHASE_RECORD.md',Path(__file__)]
for base in [LC,MD]:
    assert read(base/'validation.json')['passed'] and not (base/'INCOMPLETE').exists()
    freeze=read(base/'freeze.json');raw=set(freeze.get('raw_files',[]))
    for p,h in freeze['files'].items():
        if p not in raw:assert sha(Path(p))==h,p
    for sealname,folder in ([('bank_seal.json','bank'),('evaluation_seal.json','evaluation')] if base==LC else [('output_seal.json','output')]):
        seal=read(base/sealname);payload=base/folder
        assert set(seal['files'])=={str(p.relative_to(payload)) for p in payload.rglob('*') if p.is_file()}
        for p,h in seal['files'].items():assert sha(payload/p)==h,p
    files += [p for p in base.iterdir() if p.is_file()]
    bytes_total=sum(p.stat().st_size for p in base.rglob('*') if p.is_file())
    assert bytes_total<=(500 if base==LC else 100)*2**20
    print(base.name,'validated final bytes',bytes_total)
files += [SLAM/'scripts'/n for n in ['retrieval_exposure.py','metric_error_decomposition.py']]
files += [MAIN/'scripts/maintenance'/n for n in ['retrieval_placement_audit.py','validate_retrieval_placement_audit.py','finalize_retrieval_placement_audit.py','metric_conflict_decomposition.py','validate_metric_conflict_decomposition.py','finalize_metric_conflict_decomposition.py']]
seal=dict(utc=datetime.now(timezone.utc).isoformat(),scope='LC0/MDC0 final documentation snapshot; scientific bank/output seals separately authoritative; AGENTS/PHASE are mutable future handoff records',files={str(p):sha(p) for p in files},scientific_results_unchanged=True,no_running_stage=True)
dest=ROOT/'LC0_MDC0_DELIVERY_SEAL.json';save(dest,seal)
for p,h in read(dest)['files'].items():assert sha(Path(p))==h,p
print('LC0/MDC0 delivery seal verified',len(seal['files']),'identities')
