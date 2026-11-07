"""Verify exact closed evidence and make a nonrecursive additive review snapshot."""
import ast,datetime,hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent;day=root.parent;repo=root.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
old=json.loads((day/'continuation-01/CLOSED_SCOPES.json').read_text())
scopes=old['scopes'].copy()
for row in scopes:assert sha(day/row['scope']/'COSTS_FINAL.json')==row['sha256']
for name in ('continuation-02','reference-cohort-decision-01','output-visualization-01'):
    p=day/name/'COSTS_FINAL.json';cost=json.loads(p.read_text())
    assert cost['budget_status']=='PASS' and cost['elapsed_seconds']<cost['cap_seconds']
    scopes.append(dict(scope=name,sha256=sha(p),receipt=cost))
packages=json.loads((day/'continuation-02/RECOVERY_CHECKS.json').read_text())['package_hashes']
for name,expected in packages.items():assert sha(day/name)==expected
rc2=day/'reference-cohort-decision-01'
for name,row in json.loads((rc2/'SOURCE_FREEZE.json').read_text())['files'].items():assert sha(repo/name)==row['sha256']
ov=day/'output-visualization-01'
for row in json.loads((ov/'INPUTS.json').read_text()):assert sha(Path(row['path']))==row['sha256']
runtime_checks=[]
for run,rt in [('run01','runtime'),('run02','runtime02')]:
    f=json.loads((ov/run/'SOURCE_FREEZE.json').read_text())
    for n,h in f['files'].items():assert sha(ov/rt/n)==h
    runtime_checks.append(dict(run=run,files=len(f['files']),unchanged=True))
code=json.loads((day/'real-interface-02/CODE_BINDINGS.json').read_text())
for row in code:assert sha(Path(row['path']))==row['sha256']
previous=(root/'AGENTS.before.md').read_bytes()
assert (repo/'AGENTS.md').read_bytes().endswith(previous)
assert (day/'PHASE_RECORD.md').read_bytes().startswith((root/'PHASE_RECORD.before.md').read_bytes())
assert json.loads((root/'PLATFORM_CHECKS.json').read_text())['passed']
write(root/'PRE_PACKAGE_CHECKS.json',dict(passed=True,prior_closed_costs=7,new_closed_costs=3,
    original_source_config_hashes=len(code),original_package_hashes=packages,
    RC2_sources=22,OV1_input_hashes=10,runtime_checks=runtime_checks,
    old_AGENTS_and_phase_verbatim=True,platform_passed=True,
    weights_or_raw_or_private_reference_rehashed_or_decoded=False,model_or_metric_calls=0))
snapshot=json.loads((day/'continuation-02/CURRENT_ACCOUNT.json').read_text())
write(root/'ACCOUNT_PRE_BOUNDARY_SNAPSHOT.json',snapshot)
files=[]
for folder in (rc2,ov):files.extend(p for p in folder.rglob('*') if p.is_file())
for n in ('CURRENT_HANDOFF.md','STATUS_REPORT.md','PROTOCOL.md','PRIOR_BOUNDARY_GAP.json','RECOVERY_CHECKS.json','COSTS_FINAL.json'):
    files.append(day/'continuation-02'/n)
for n in ('PROTOCOL.md','REPORT.md','platform.ps1','assemble.py','pack.py','ADDITIVE_POINTER_CHECKS.json','PLATFORM_CHECKS.json','PRE_PACKAGE_CHECKS.json','ACCOUNT_PRE_BOUNDARY_SNAPSHOT.json'):
    files.append(root/n)
assert len(files)==len(set(files))
for p in files:
    assert p.is_relative_to(repo) and p.is_file() and not p.is_symlink()
    if p.suffix=='.json':json.loads(p.read_text(encoding='utf-8'))
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'))
manifest={str(p.relative_to(repo)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)}
target=root/'RAP_20261024_source_review_and_figures.zip'
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(files):z.write(p,str(p.relative_to(repo)).replace('\\','/'))
    z.writestr('MANIFEST.json',json.dumps(dict(files=manifest,
        companion_original_packages=packages,pre_account_boundary_snapshot_only=True,
        final_handoff_cost_and_latest_account_records_are_separate=True),indent=2))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(manifest)|{'MANIFEST.json'}
    for n,row in manifest.items():
        b=z.read(n);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest().upper()==row['sha256']
    assert json.loads(z.read('MANIFEST.json'))['files']==manifest
checks=dict(passed=True,file=target.name,bytes=target.stat().st_size,sha256=sha(target),
    member_count=len(manifest)+1,all_member_names_CRC_size_SHA256_verified=True,
    original_packages_unchanged=True,mutable_account_pointer_excluded=True)
write(root/'ZIP_CHECKS.json',checks)
start=datetime.datetime(2026,10,24,7,28,47,tzinfo=datetime.timezone.utc)
elapsed=(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()
write(root/'COSTS_FINAL.json',dict(status='COMPACT_HANDOFF_ADDITIVE_REVIEW_DELIVERY_COMPLETE',
    elapsed_seconds=elapsed,cap_seconds=900,budget_status='PASS' if elapsed<=900 else 'FAIL',
    original_UTC_origin=start.isoformat(),package_creation_and_verification_included=True,
    old_caps_reset=False,model_or_metric_calls=0))
p=root/'COSTS_FINAL.json'
scopes.append(dict(scope=root.name,sha256=sha(p),receipt=json.loads(p.read_text())))
write(day/'continuation-02/CLOSED_SCOPES.json',dict(scopes=scopes,scope_count=len(scopes),
    all_original_time_budgets_pass=all(r['receipt']['budget_status']=='PASS' for r in scopes),
    original_failures_preserved=True,pending_real_computation=False,
    scientific_dependency='OWNER_SOURCE_REFERENCE_COHORT_RECORD_AND_MECHANISM_REVIEW',
    actual_account_exhaustion_must_be_observed_separately=True,no_automatic_resume=True,
    research='UNRESOLVED',manuscript='PAUSED'))
print(json.dumps(dict(package=checks,closed_scopes=len(scopes),elapsed_seconds=elapsed)))
