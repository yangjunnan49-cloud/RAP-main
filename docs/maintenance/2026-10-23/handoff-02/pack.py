"""Package immutable local closed-scope evidence, excluding live account state."""
import datetime as dt,hashlib,json,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;REPO=ROOT.parents[3];START=time.monotonic()
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
def write(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,indent=2)
sources=set()
for row in json.loads((DAY/'continuation-01/PAYLOAD_MANIFEST.json').read_text()):sources.add(Path(row['path']))
for name in ('feature-candidate-01','checkpoint-binding-01','checkpoint-archive-01','checkpoint-structure-01','tensor-transfer-01','public-reader-01','singleton-layout-01','inference-semantics-01','delivery-audit-02','account-boundary-02','context-wsl-review-01'):
    sources.update(p for p in (DAY/name).rglob('*') if p.is_file())
sources.update(p for p in (DAY/'continuation-02').iterdir() if p.is_file() and p.name not in ('CURRENT_ACCOUNT.json','ACCOUNT_STOP.json','OBSERVATION_STOP.json'))
sources.update((REPO/'AGENTS.md',DAY/'PHASE_RECORD.md'))
manifest=[]
for p in sorted(sources):
    assert p.resolve().is_relative_to(REPO.resolve()) and not p.is_symlink()
    rel=str(p.relative_to(REPO)).replace('\\','/');assert not rel.startswith('/') and '..' not in Path(rel).parts
    manifest.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha_file(p)))
assert len({r['path'] for r in manifest})==len(manifest)
assert sum(r['bytes'] for r in manifest)<8*2**20
metadata=dict(kind='PRE_BOUNDARY_CLOSED_SCOPE_SNAPSHOT',created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    current_account_excluded=True,actual_quota_exhaustion_claim=False,files=manifest)
raw=json.dumps(metadata,indent=2).encode()
archive=ROOT/'RAP_20261023_closed_scopes.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('_MANIFEST.json',raw)
    for row in manifest:z.write(REPO/row['path'],row['path'])
assert archive.stat().st_size<8*2**20
with zipfile.ZipFile(archive) as z:
    expected={'_MANIFEST.json',*(r['path'] for r in manifest)}
    assert len(z.namelist())==len(expected) and set(z.namelist())==expected
    assert z.read('_MANIFEST.json')==raw
    for row in manifest:
        h=hashlib.sha256();size=0
        with z.open(row['path']) as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
        assert size==row['bytes'] and h.hexdigest().upper()==row['sha256']
write('DELIVERY_MANIFEST.json',metadata)
write('ZIP_CHECKS.json',dict(passed=True,members=len(manifest)+1,source_files=len(manifest),source_bytes=sum(r['bytes'] for r in manifest),ZIP_bytes=archive.stat().st_size,ZIP_sha256=sha_file(archive),manifest_sha256=hashlib.sha256(raw).hexdigest().upper(),all_member_CRC_and_SHA_match=True,duplicate_members=0,live_account_excluded=True,actual_exhaustion_claim=False,elapsed_seconds=time.monotonic()-START,numeric_imports=False))
assert not any(k in sys.modules for k in ('numpy','torch'))
print((ROOT/'ZIP_CHECKS.json').read_text())
