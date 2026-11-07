"""Read-only local report, archive, original AGENTS history and owned-exit verification."""
import datetime,hashlib,json,zipfile
from pathlib import Path
base=Path(__file__).resolve().parent.parent;current=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
checks=archives=0;verified=[];owned={}
for name in ('MAC准入_2026-10-31','portable_graph_20261031','reference_gate_20261031','correspondence_score_20261031'):
    root=base/name;s=read(root/'DELIVERY_SEAL.json')
    for e in s['files']:
        p=(root/e['path']).resolve();assert p.is_relative_to(root.resolve());assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];checks+=1
    with zipfile.ZipFile(root/'SOURCE_BUNDLE.zip') as z:assert z.testzip() is None
    archives+=1;verified.append(dict(directory=name,entries=len(s['files']),seal_sha256=sha(root/'DELIVERY_SEAL.json')))
    for p in root.rglob('OWNED_PROCESS.json'):
        v=read(p);h=read(p.parent/'HOST_EXIT.json');assert h['owned_child_reaped'];assert sha(v['program'])==v['program_sha256'];key=(v['pid'],v['launched_utc'],v['program_sha256']);owned[key]=dict(pid=v['pid'],program=v['program'],exit_code=h['exit_code'],reaped=True)
for name in ('DECISION_SEAL.json','HANDOFF_SEAL.json'):
    for e in read(current/name)['files']:
        p=(current/e['path']).resolve();assert p.is_relative_to(current.resolve());assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];checks+=1
with zipfile.ZipFile(current/'PROJECT_REVIEW_BUNDLE.zip') as z:assert z.testzip() is None
archives+=1
proof=read(current/'E_DRIVE_HANDOFF_PROOF.json');record=Path(proof['maintenance_directory']);backup=record/'AGENTS.before.md';agents=Path('E:/githouse/RAP-main/AGENTS.md');assert sha(backup)==proof['backup_sha256']==proof['previous_sha256'];assert sha(agents)==proof['new_sha256'];assert agents.read_bytes().endswith(backup.read_bytes());assert len(owned)==15
print(json.dumps(dict(passed=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),delivery_entries_verified=checks,archives_CRC_verified=archives,source_program_hashes_verified=True,owned_unique_identities=len(owned),owned_exit_receipts=list(owned.values()),not_global_process_absence_certificate=True,AGENTS_exact_backup_and_suffix_verified=True,verified=verified,verifier_sha256=sha(Path(__file__)),read_only=True,no_numerical_reexecution=True,mutable_account_status_excluded=True),ensure_ascii=False,indent=2))
