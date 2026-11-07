"""Preserve late local migration evidence without replacing sealed controls."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile

phase = Path(__file__).resolve().parent
repo = phase.parents[3]
output = repo / ".maintenance-archive/migration/A8-closeout-20261106"
output.mkdir(exist_ok=False)
control = json.loads((repo / ".maintenance-archive/migration/A8-20261106/CONTROL.json").read_bytes())
initial = {row["path"]: row["sha256"] for row in control["files"]}
prefix = control["phase_prefix"] + "/"
records = []
archive = output / "closeout.tar.gz"
with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as package:
    for path in sorted(phase.rglob("*")):
        relative = path.relative_to(phase)
        if relative.parts[0] in {"remote", "remote-final"} or path.is_dir():
            continue
        assert not path.is_symlink() and path.is_file(), str(path)
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if initial.get(prefix + relative.as_posix()) == sha:
            continue
        member = tarfile.TarInfo(relative.as_posix())
        member.size, member.mode, member.mtime = len(data), 0o644, 0
        package.addfile(member, io.BytesIO(data))
        records.append(dict(path=relative.as_posix(), bytes=len(data), sha256=sha))
with tarfile.open(archive, "r:gz") as package:
    members = package.getmembers()
    assert len(members) == len(records)
    for member, row in zip(members, records):
        assert member.isfile() and member.name == row["path"]
        assert hashlib.sha256(package.extractfile(member).read()).hexdigest() == row["sha256"]
manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
    purpose="LATE_LOCAL_MIGRATION_EVIDENCE_ONLY", archive=archive.name,
    archive_bytes=archive.stat().st_size, archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    files=records, independently_read_back=True,
    remote_receipts_retained_separately=True, current_83_file_authority_replaced=False)
payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
(output / "CLOSEOUT.json").write_bytes(payload)
(phase / "CLOSEOUT.json").write_bytes(payload)
print(json.dumps(dict(files=len(records), archive_bytes=manifest["archive_bytes"],
    archive_sha256=manifest["archive_sha256"], output=str(output))))
