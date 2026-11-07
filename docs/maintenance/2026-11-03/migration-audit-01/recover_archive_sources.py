"""Search source members of existing ZIP/TAR archives for exact missing source hashes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tarfile
import zipfile

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    state = audit.read_json(PHASE / "RECOVERED_SOURCES.json")
    shutil.copyfile(PHASE / "RECOVERED_SOURCES.json", PHASE / "recovered-sources/GIT_RECOVERY_ORIGINAL.json")
    wanted = set(state["unrecovered_sha256"])
    source_names = {".gitignore", "AGENTS.md"}
    receipts = []
    hashes = {audit.key(r["root"], r["path"]): r for r in audit.load_jsonl(PHASE / "HASHES.jsonl")}
    for row in audit.metadata():
        name = row["path"].lower()
        if row["kind"] != "file" or row["reparse_point"] or audit.opaque(name):
            continue
        is_zip = name.endswith(".zip")
        is_tar = name.endswith((".tar", ".tar.gz", ".tgz")) and not name.endswith(".pth.tar")
        if not (is_zip or is_tar):
            continue
        path = audit.file_path(row)
        receipt = {"asset": audit.key(row["root"], row["path"]), "archive_sha256": hashes[audit.key(row["root"], row["path"])]["sha256"],
                   "source_members_hashed": 0, "source_member_bytes": 0, "recovered": [], "array_or_result_members_read": False}
        try:
            with (zipfile.ZipFile(path) if is_zip else tarfile.open(path, "r:*")) as archive:
                for member in (archive.infolist() if is_zip else archive):
                    filename = member.filename if is_zip else member.name
                    size = member.file_size if is_zip else member.size
                    if audit.opaque(filename) or size > 2 * 1024 * 1024:
                        continue
                    if Path(filename).suffix.lower() not in audit.SOURCE_EXTS and Path(filename).name not in source_names:
                        continue
                    if is_zip:
                        if member.is_dir():
                            continue
                        content = archive.read(member)
                    else:
                        if not member.isfile():
                            continue
                        content = archive.extractfile(member).read()
                    sha = hashlib.sha256(content).hexdigest()
                    receipt["source_members_hashed"] += 1
                    receipt["source_member_bytes"] += len(content)
                    if sha in wanted:
                        target = PHASE / "recovered-sources" / (sha + ".source")
                        target.write_bytes(content)
                        state["recovered"].append({"sha256": sha, "bytes": len(content), "backup": target.relative_to(PHASE).as_posix(),
                                                   "archive_asset": receipt["asset"], "archive_sha256": receipt["archive_sha256"],
                                                   "archive_member": filename, "source_or_repository_rewritten": False,
                                                   "member_semantically_evaluated": False})
                        wanted.remove(sha)
                        receipt["recovered"].append(sha)
            receipt["status"] = "source_members_checked"
        except (zipfile.BadZipFile, tarfile.TarError) as exc:
            receipt.update(status="unreadable_archive", error=str(exc))
        receipts.append(receipt)
    state["unrecovered_sha256"] = sorted(wanted)
    state["archive_search"] = {"archives_checked": len(receipts), "opaque_PGC1_archives_opened": False,
                               "no_result_arrays_or_accuracies_interpreted": True}
    audit.write_json("RECOVERED_SOURCES.json", state)
    audit.write_json("ARCHIVE_SOURCE_SEARCH.json", receipts)
    print(json.dumps({"archives_checked": len(receipts), "recovered_total": len(state["recovered"]),
                      "still_missing": len(wanted), "source_members_hashed": sum(r["source_members_hashed"] for r in receipts)}), flush=True)


if __name__ == "__main__":
    main()
