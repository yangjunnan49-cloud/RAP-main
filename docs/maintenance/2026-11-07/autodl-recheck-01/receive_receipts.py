"""Verify the returned server archive and merge only identical or new audit files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

root = Path(__file__).resolve().parent
repo = root.parents[3]
package = repo / '.maintenance-archive/migration/A8-recheck-20261107-01'
manifest_raw = (package / 'MANIFEST.json').read_bytes()
manifest = json.loads(manifest_raw)
archive = package / 'receipts.tar.gz'
archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
assert archive_sha == manifest['archive_sha256'] == '674404f54c4eb7e3cee9bfcce99e385d5d848d73415db159d0d0653ea7be48bd'
staged = []
with tarfile.open(archive, 'r:gz') as stream:
    members = stream.getmembers()
    assert len(members) == len(manifest['files']) == 60
    for member, row in zip(members, manifest['files']):
        name = PurePosixPath(row['path'])
        assert member.isfile() and member.name == row['path']
        assert not name.is_absolute() and '..' not in name.parts and '\\' not in row['path']
        data = stream.extractfile(member).read()
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
        target = root.joinpath(*name.parts)
        assert target.resolve().is_relative_to(root.resolve()) and not target.is_symlink()
        if target.exists():
            assert target.read_bytes() == data, 'Preserving differing local file: ' + str(target)
        staged.append((target, data))
for target, data in staged:
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    assert target.read_bytes() == data
with (root / 'ARCHIVE.json').open('xb') as stream:
    stream.write(manifest_raw)
assert json.loads((root / 'RECHECK_RESULT.json').read_bytes())['passed']
assert json.loads((root / 'STRUCTURE_AND_EXTRAS.json').read_bytes())['passed']
receipt = dict(completed_utc=datetime.now(timezone.utc).isoformat(), passed=True,
    archive_sha256=archive_sha, archive_members_independently_verified=60,
    original_A8_core_context_or_assets_overwritten=False)
with (root / 'LOCAL_ARCHIVE_READBACK.json').open('x', encoding='utf-8') as stream:
    json.dump(receipt, stream, indent=2)
    stream.write('\n')
print(json.dumps(receipt))
