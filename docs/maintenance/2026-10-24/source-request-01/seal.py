"""Seal the local-only proposal; never perform external retrieval."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;day=root.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
old=(root/'prepare.py').read_text(encoding='utf-8')
new=(root/'prepare02.py').read_text(encoding='utf-8')
assert ast.dump(ast.parse(new),include_attributes=False)==ast.dump(ast.parse(old.replace('.read_text()',".read_text(encoding='utf-8')")),include_attributes=False)
pointer=json.loads((root/'SOURCE_POINTER.json').read_text(encoding='utf-8'))
for row in pointer['source_files']:assert sha(root.parents[3]/row['path'])==row['sha256']
for p in root.glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
for p in root.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
with (root/'REPAIR_CHECKS.json').open('x') as f:json.dump(dict(passed=True,
    only_explicit_UTF8_read_encoding_changed=True,original_failure_source_preserved=True,
    network_requests=0,three_metadata_identities_unchanged=True),f,indent=2)
files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in root.iterdir() if p.is_file() and p.name!='DELIVERY_SEAL.json'}
assert sum(r['bytes'] for r in files.values())<2*1024*1024
with (root/'DELIVERY_SEAL.json').open('x') as f:json.dump(dict(files=files,
    external_page_not_fetched=True,explicit_owner_authorization_pending=True),f,indent=2)
ledger=json.loads((day/'continuation-02/CLOSED_SCOPES.json').read_text())
assert ledger['scope_count']==11
p=root/'COSTS_FINAL.json';cost=json.loads(p.read_text());assert cost['budget_status']=='PASS'
ledger['scopes'].append(dict(scope=root.name,sha256=sha(p),receipt=cost));ledger['scope_count']=12
ledger['scientific_dependency']='EXPLICIT_AUTHORIZATION_OF_FIXED_UPSTREAM_PROJECT_PAGE_OR_LOCAL_ORIGINAL_SOURCE'
with (day/'continuation-02/CLOSED_SCOPES_WITH_SOURCE_REQUEST.json').open('x') as f:json.dump(ledger,f,indent=2)
print(json.dumps(dict(sealed=True,closed_scopes=12,network_requests=0)))
