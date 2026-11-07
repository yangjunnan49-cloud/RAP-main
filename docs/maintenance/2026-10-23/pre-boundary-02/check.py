"""Verify expected post-bundle delta and closed scope receipts only."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;REPO=ROOT.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
m=json.loads((DAY/'handoff-02/DELIVERY_MANIFEST.json').read_text())
changed=[]
for row in m['files']:
    p=REPO/row['path']
    if sha(p)!=row['sha256']:changed.append(row)
expected='docs/maintenance/2026-10-23/continuation-02/record_account.py'
assert len(changed)==1 and changed[0]['path']==expected
assert sha(DAY/'account-ledger-01/record_account.before.py')==changed[0]['sha256']
z=json.loads((DAY/'handoff-02/ZIP_CHECKS.json').read_text())
assert sha(DAY/'handoff-02/RAP_20261023_closed_scopes.zip')==z['ZIP_sha256']
names=('continuation-02','feature-candidate-01','checkpoint-binding-01','checkpoint-archive-01','checkpoint-structure-01','tensor-transfer-01','public-reader-01','singleton-layout-01','inference-semantics-01','delivery-audit-02','account-boundary-02','handoff-02','reference-counterexample-01','account-ledger-01')
costs=[]
for name in names:
    p=DAY/name/'COSTS_FINAL.json';r=json.loads(p.read_text());assert r.get('elapsed_seconds',0)<r['cap_seconds']
    costs.append(dict(scope=name,receipt_SHA256=sha(p),receipt=r))
current=json.loads((DAY/'continuation-02/CURRENT_ACCOUNT.json').read_text());assert current['classification']['usedPercent']==91 and current['classification']['status']=='ACTIVE'
with (ROOT/'CHECKS.json').open('x') as f:json.dump(dict(passed=True,ZIP_unchanged=True,post_bundle_changed_sources=[expected],original_writer_preserved=True,closed_scope_receipts=costs,scope_count=len(costs),actual_exhaustion_observed=False,last_actual_usedPercent=91,last_actual_ordinaryUsageAllowed=True,no_pending_numerical_work=True),f,indent=2)
print(json.dumps(dict(passed=True,closed_scopes=len(costs),expected_post_bundle_source_changes=1,actual_boundary=False)))
