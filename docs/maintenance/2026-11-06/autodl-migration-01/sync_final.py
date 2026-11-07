"""Watch the authorized migration and sync only guarded current context files."""
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import time
import traceback
import importlib.util

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
spec = importlib.util.spec_from_file_location("migration_transport", PHASE / "transfer_client.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
REMOTE = transport.REMOTE
WORKSPACE = "/root/autodl-tmp/rap-workspace-20261106"
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "reports": REPO.parent / "RAP-SLAM-report", "workspace-root": REPO.parent}
LAYOUT = {"rap-main": "RAP-main", "rap-slam": "RAP-SLAM", "reports": "RAP-SLAM-report", "workspace-root": ""}
WRITABLE = {("rap-main", path) for path in ("AGENTS.md", "README.md", "docs/README.md", "docs/migration/README.md",
    "docs/CURRENT_STATE.json", "docs/CURRENT_STATE.md", "docs/migration/AUTODL.md", PHASE.relative_to(REPO).as_posix() + "/REPORT_CN.md")}
WRITABLE.update({("workspace-root", "AGENTS.md"), ("rap-slam", "AGENTS.md")})


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(sftp, path, optional=False):
    try:
        with sftp.open(path, "r") as source:
            return source.read()
    except FileNotFoundError:
        if optional:
            return None
        raise


def main():
    if (PHASE / "SYNC_STARTED.json").exists():
        raise RuntimeError("This synchronization attempt already exists")
    guards = {(row["root"], row["path"]): row["sha256"] for row in json.loads((PHASE / "LOCAL_SYNC_GUARDS.json").read_text())}
    transport.PASSWORD = getpass.getpass("SSH password (memory only): ")
    transport.save("SYNC_STARTED.json", dict(started_utc=utc(), password_persisted=False,
        allowed_local_context_writes=sorted(WRITABLE), unknown_or_user_modified_local_bytes_overwritten=False))
    deadline = time.monotonic() + 48 * 3600
    while True:
        client = None
        try:
            client = transport.connect()
            with client.open_sftp() as sftp:
                failed = read(sftp, REMOTE + "/FINALIZATION_FAILURE.json", optional=True)
                if failed:
                    (PHASE / "REMOTE_FINALIZATION_FAILURE.json").write_bytes(failed)
                    raise RuntimeError("Target finalization failed; original failure receipt downloaded")
                raw_final = read(sftp, REMOTE + "/SERVER_FINALIZED.json", optional=True)
                if raw_final:
                    final = json.loads(raw_final)
                    raw_authority = read(sftp, REMOTE + "/SERVER_AUTHORITY.json")
                    assert digest(raw_authority) == final["authority_sha256"]
                    authority = json.loads(raw_authority)
                    rows = {(row["root"], row["path"]): row for row in authority["current_files"]}
                    assert set(rows) == set(guards) and len(rows) == len(authority["current_files"])
                    staged = []
                    for key, row in rows.items():
                        rid, relative = key
                        name = PurePosixPath(relative)
                        assert not name.is_absolute() and ".." not in name.parts and "\\" not in relative
                        target = ROOTS[rid].joinpath(*name.parts)
                        assert target.resolve().is_relative_to(ROOTS[rid].resolve())
                        current = target.read_bytes()
                        if digest(current) == row["sha256"]:
                            continue
                        assert key in WRITABLE, "Refusing unexpected production/control write: " + str(key)
                        assert digest(current) == guards[key], "Local context changed during migration: " + str(target)
                        source = "/".join(part for part in (WORKSPACE, LAYOUT[rid], relative) if part)
                        data = read(sftp, source)
                        assert len(data) == row["bytes"] and digest(data) == row["sha256"]
                        staged.append((rid, relative, target, current, data))
                    # All guards are checked before the first current file is replaced.
                    for rid, relative, target, before, data in staged:
                        backup = PHASE / "before-sync" / rid / relative
                        backup.parent.mkdir(parents=True, exist_ok=True)
                        with backup.open("xb") as out:
                            out.write(before)
                        target.write_bytes(data)
                    for key, row in rows.items():
                        assert digest((ROOTS[key[0]] / key[1]).read_bytes()) == row["sha256"]
                    (PHASE / "AUTHORITY_PROOF.in-progress.json").write_bytes((PHASE / "AUTHORITY_PROOF.json").read_bytes())
                    (PHASE / "AUTHORITY_PROOF.json").write_bytes(raw_authority)
                    (PHASE / "REMOTE_FINALIZED.json").write_bytes(raw_final)
                    receipts = PHASE / "remote-final"
                    receipts.mkdir()
                    for folder in ("", "file-acceptance"):
                        destination = receipts / folder
                        destination.mkdir(exist_ok=True)
                        for entry in sftp.listdir_attr(REMOTE + ("/" + folder if folder else "")):
                            if entry.filename.endswith(".json") and "/" not in entry.filename and "\\" not in entry.filename:
                                payload = read(sftp, REMOTE + ("/" + folder if folder else "") + "/" + entry.filename)
                                (destination / entry.filename).write_bytes(payload)
                    result = dict(completed_utc=utc(), server_file_layer_passed=final["server_file_layer_passed"],
                        bounded_functional_gate_passed=final["bounded_functional_gate_passed"],
                        current_authority_files_synced=len(rows), changed_context_files=len(staged),
                        all_local_current_authority_hashes_match_server=True, training_or_resume_validated=False,
                        original_historical_PyTorch3D_commit_recovered=False)
                    transport.save("MIGRATION_COMPLETE.json", result)
                    print(json.dumps(result), flush=True)
                    return 0 if final["bounded_functional_gate_passed"] else 2
        except (AssertionError, RuntimeError):
            raise
        except Exception as exc:
            transport.save("SYNC_CONNECTION_RETRY.json", dict(observed_utc=utc(), error=repr(exc)))
        finally:
            if client:
                client.close()
        if time.monotonic() > deadline:
            raise TimeoutError("Target synchronization exceeded 48 hours")
        time.sleep(60)


if __name__ == "__main__":
    try:
        code = main()
    except BaseException as exc:
        transport.save("SYNC_FAILURE.json", dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise
    finally:
        transport.PASSWORD = None
    raise SystemExit(code)
