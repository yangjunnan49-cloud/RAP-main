"""Seal completed recheck evidence on cloud storage and install its new document directory."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

root = Path(__file__).resolve().parent
assert json.loads((root / 'RECHECK_RESULT.json').read_bytes())['passed']
assert json.loads((root / 'STRUCTURE_AND_EXTRAS.json').read_bytes())['passed']
assert (root / 'REPORT_CN.md').is_file()
destination = Path('/root/autodl-fs/rap-transfer-20261106/A8-recheck-20261107-01')
project = Path('/root/autodl-tmp/rap-workspace-20261106/RAP-main/docs/maintenance/2026-11-07/autodl-recheck-01')
assert not destination.exists() and not project.exists(), 'Refusing to replace existing evidence'
assert not any(path.is_symlink() for path in root.rglob('*'))
sources = sorted(path for path in root.rglob('*') if path.is_file())
assert all(not path.name.endswith('.tmp') for path in sources)
records = []
for path in sources:
    data = path.read_bytes()
    records.append(dict(path=path.relative_to(root).as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
destination.mkdir()
archive = destination / 'receipts.tar.gz'
with tarfile.open(archive, 'w:gz', format=tarfile.PAX_FORMAT) as package:
    for path in sources:
        package.add(path, arcname=path.relative_to(root).as_posix(), recursive=False)
with tarfile.open(archive, 'r:gz') as package:
    members = package.getmembers()
    assert len(members) == len(records)
    for member, record in zip(members, records):
        assert member.isfile() and member.name == record['path']
        data = package.extractfile(member).read()
        assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256']
manifest = dict(completed_utc=datetime.now(timezone.utc).isoformat(), passed=True,
    archive=archive.name, archive_bytes=archive.stat().st_size,
    archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), files=records,
    archive_members_independently_read_back=True, original_assets_or_A8_receipts_overwritten=False)
payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
with (destination / 'MANIFEST.json').open('xb') as stream:
    stream.write(payload)
with (root / 'ARCHIVE.json').open('xb') as stream:
    stream.write(payload)
project.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(root, project)
for record in records:
    assert hashlib.sha256((project / record['path']).read_bytes()).hexdigest() == record['sha256']
assert (project / 'ARCHIVE.json').read_bytes() == payload
print(json.dumps(dict(passed=True, cloud=str(destination), project=str(project),
    archive_bytes=manifest['archive_bytes'], archive_sha256=manifest['archive_sha256'], files=len(records))))
