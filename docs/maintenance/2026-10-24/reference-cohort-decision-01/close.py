"""Seal the completed source decision once; preserve all old receipts."""
import ast, datetime, hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parent
repo=root.parents[3]
seal=json.loads((root/'SOURCE_FREEZE.json').read_text())
for name,row in seal['files'].items():
    b=(repo/name).read_bytes()
    assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest().upper()==row['sha256']
assert json.loads((root/'RESULTS.json').read_text())['passed'] is True
for p in root.glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
for p in root.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
start=datetime.datetime(2026,10,24,7,18,58,tzinfo=datetime.timezone.utc)
elapsed=(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()
with (root/'COSTS_FINAL.json').open('x') as f:json.dump(dict(status='SOURCE_REFERENCE_COHORT_DECISION_CLOSED',
    elapsed_seconds=elapsed,cap_seconds=1200,budget_status='PASS' if elapsed<=1200 else 'FAIL',
    conservative_UTC_origin=start.isoformat(),all_source_preparation_included=True,
    old_caps_reset=False,real_model_or_metric_calls=0),f,indent=2)
files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest().upper())
    for p in root.iterdir() if p.is_file() and p.name!='DELIVERY_SEAL.json'}
assert sum(r['bytes'] for r in files.values())<4*1024*1024
with (root/'DELIVERY_SEAL.json').open('x') as f:json.dump(dict(files=files,
    source_files_verified_unchanged=22,physical_reference_or_confirmation_admitted=False),f,indent=2)
print(json.dumps(dict(closed=True,elapsed_seconds=elapsed,files=len(files))))
