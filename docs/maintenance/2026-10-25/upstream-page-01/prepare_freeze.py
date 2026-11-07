"""Bind the owner-approved literal object before its first network request."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
proposal=REPO/'docs/maintenance/2026-10-24/source-request-01/REQUEST_PLAN.json'
pointer=REPO/'docs/maintenance/2026-10-24/source-request-01/SOURCE_POINTER.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
for r in json.loads(pointer.read_text(encoding='utf-8'))['source_files']:
    p=REPO/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
plan=json.loads(proposal.read_text(encoding='utf-8'))
assert plan['object']['url']=='https://npm3d.fr/parisluco3d'
assert plan['max_requests']==4 and plan['max_redirects']==3 and plan['cumulative_delivered_body_cap_bytes']==262144
assert plan['network_worker_deadline_seconds']==60 and plan['whole_attempt_seconds']==120
for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
names=['fetch.py','host.ps1','PROTOCOL.md','AUTHORIZATION.json','prepare_freeze.py','CLOSEOUT_DIRECTION.json']
freeze=dict(files={n:sha(ROOT/n) for n in names},proposal_path=str(proposal),
    proposal_sha256=sha(proposal),source_pointer_path=str(pointer),source_pointer_sha256=sha(pointer),
    original3_metadata_identities_match=True,network_requests_before_freeze=0)
with (ROOT/'SOURCE_FREEZE.json').open('x',encoding='utf-8') as f:json.dump(freeze,f,indent=2)
print(json.dumps(dict(frozen_files=len(names),source_metadata_identities=3,network_requests=0)))
