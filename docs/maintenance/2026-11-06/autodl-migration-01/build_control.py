"""Freeze A8 current additions and evidence without changing the A5/A7 packages."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
LAYOUT = {"rap-main": "RAP-main", "rap-slam": "RAP-SLAM", "reports": "RAP-SLAM-report",
          "datasets": "Datasets", "codex-records": "archives/Codex", "workspace-root": ""}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    target = REPO / ".maintenance-archive/migration/A8-20261106"
    target.mkdir()
    audit = json.loads((PHASE / "CURRENT_AUDIT.json").read_text(encoding="utf-8"))
    assert audit["complete"] and audit["missing_current_identities"] == 0
    assert json.loads((PHASE / "CURRENT_LINK_BYTE_CHECKS.json").read_text())["passed"]
    roots = {rid: Path(path) for rid, path in audit["source_roots"].items()}
    rows = []
    inputs = []
    for row in json.loads((PHASE / "CURRENT_DELTA.json").read_text(encoding="utf-8")):
        source = roots[row["root"]] / row["path"]
        mapped = "/".join(part for part in (LAYOUT[row["root"]], row["path"]) if part)
        inputs.append((source, mapped, row["A7_before_sha256"], row["sha256"], "current_delta"))
    prefix = "RAP-main/" + PHASE.relative_to(REPO).as_posix() + "/"
    # Read each late evidence file into a fixed byte snapshot. Live client status
    # snapshots retain their observation time; no atomic global snapshot is claimed.
    for source in sorted(PHASE.rglob("*")):
        if source.is_file() and not source.is_symlink() and source.name not in {"CONTROL_READY.json", "LOCAL_SYNC_GUARDS.json"}:
            inputs.append((source, prefix + source.relative_to(PHASE).as_posix(), None, None, "A8_evidence_snapshot"))
    archive = target / "control.tar.gz"
    with tarfile.open(archive, "w:gz", compresslevel=3) as out:
        for source, path, old_sha, audited_sha, role in inputs:
            data = source.read_bytes()
            value = sha(data)
            if audited_sha:
                assert value == audited_sha, "Current delta drifted after the fresh audit: " + str(source)
            info = tarfile.TarInfo(path)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            out.addfile(info, io.BytesIO(data))
            rows.append(dict(path=path, bytes=len(data), sha256=value, before_sha256=old_sha, role=role))
    baseline = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    controls = [dict(root=row["root"], path=row["path"]) for row in baseline["backups"]]
    controls.extend([dict(root="rap-main", path="docs/migration/AUTODL.md"),
                     dict(root="rap-main", path=PHASE.relative_to(REPO).as_posix() + "/REPORT_CN.md")])
    guards = []
    for row in controls:
        source = roots[row["root"]] / row["path"]
        guards.append(dict(row, sha256=sha(source.read_bytes())))
    (PHASE / "LOCAL_SYNC_GUARDS.json").write_text(json.dumps(guards, indent=2) + "\n", encoding="utf-8")
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), layout=LAYOUT,
                  phase_prefix=prefix.rstrip("/"), archive="control.tar.gz", archive_bytes=archive.stat().st_size,
                  archive_sha256=sha(archive.read_bytes()), files=rows, current_controls=controls,
                  A7_delivery_sha256=baseline["previous_delivery_sha256"],
                  delta_current_files=audit["delta_files"], source_missing_files=0,
                  original_packages_or_Git_index_refs_history_modified=False)
    manifest = target / "CONTROL.json"
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Independent readback of every member before making the layer available.
    expected = {row["path"]: row for row in rows}
    seen = set()
    with tarfile.open(archive) as stream:
        for member in stream:
            assert member.isfile() and member.name in expected and member.name not in seen
            data = stream.extractfile(member).read()
            assert len(data) == expected[member.name]["bytes"] and sha(data) == expected[member.name]["sha256"]
            seen.add(member.name)
    assert seen == set(expected)
    ready = dict(package=str(target), manifest_sha256=sha(manifest.read_bytes()), archive_sha256=result["archive_sha256"],
                 files=len(rows), archive_bytes=result["archive_bytes"], independent_readback_passed=True)
    (PHASE / "CONTROL_READY.json").write_text(json.dumps(ready, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(ready))


if __name__ == "__main__":
    main()
