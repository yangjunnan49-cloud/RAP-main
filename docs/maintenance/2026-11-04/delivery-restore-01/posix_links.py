"""Recreate only restored internal links and test modes in a disposable POSIX fixture."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

PHASE = Path(__file__).resolve().parent
RESTORE = Path("/mnt/e/githouse/RAP-main/.maintenance-archive/migration/A7-restore-20261104-02/workspace")


def main():
    assert os.name == "posix" and RESTORE.resolve().is_relative_to(Path("/mnt/e/githouse/RAP-main/.maintenance-archive/migration"))
    assert json.loads((PHASE / "PROJECT_RESTORE.json").read_text(encoding="utf-8"))["passed"]
    assert not (PHASE / "POSIX_LINK_CHECKS.json").exists()
    spec = importlib.util.spec_from_file_location("link_restore_only", PHASE / "used/delivery-longpath.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    project = json.loads((PHASE / "PROJECT_FREEZE.json").read_text(encoding="utf-8"))
    plan = json.loads((PHASE / "LINK_PLAN.json").read_text(encoding="utf-8"))
    outcomes = tool.apply_links(RESTORE, project["layout"], plan, create=True)
    assert sum(r["state"] == "created_and_resolved" for r in outcomes) == 25
    assert sum(r["state"] == "external_dependency_not_recreated" for r in outcomes) == 2
    for r in outcomes:
        if r["state"] == "created_and_resolved":
            target = tool.mapped(RESTORE, project["layout"], r)
            assert target.is_symlink() and target.resolve().is_relative_to(RESTORE.resolve())
    scratch = Path(tempfile.mkdtemp(prefix="a7-posix-modes-", dir="/tmp"))
    assert scratch.resolve().parent == Path("/tmp") and scratch.name.startswith("a7-posix-modes-")
    try:
        (scratch / "RAP-main").mkdir()
        script, regular = scratch / "RAP-main/mode-probe.sh", scratch / "RAP-main/regular.txt"
        script.write_bytes(b"#!/bin/sh\nprintf 'A7_POSIX_OK\\n'\n")
        regular.write_bytes(b"A7 permission fixture only\n")
        permission_spec = importlib.util.spec_from_file_location("tested_permission_policy", PHASE / "updates/scripts/migration/delivery.py")
        permission_tool = importlib.util.module_from_spec(permission_spec)
        permission_spec.loader.exec_module(permission_tool)
        fixture_rows = [{"root": "rap-main", "path": f.name, "bytes": f.stat().st_size, "sha256": permission_tool.sha(f)} for f in (script, regular)]
        policy = permission_tool.apply_permissions(scratch, {"rap-main": "RAP-main"}, fixture_rows, [], {"git_tracked_modes": {"rap-main:mode-probe.sh": "100755"}})
        assert policy["applied"] and policy["files"] == 2
        ran = subprocess.run([str(script)], capture_output=True, text=True, timeout=5, env={"PATH": "/usr/bin:/bin"})
        assert ran.returncode == 0 and ran.stdout.strip() == "A7_POSIX_OK"
        assert stat.S_IMODE(script.stat().st_mode) == 0o755 and stat.S_IMODE(regular.stat().st_mode) == 0o644
        mode_result = {"script_mode": oct(stat.S_IMODE(script.stat().st_mode)), "regular_mode": oct(stat.S_IMODE(regular.stat().st_mode)),
                       "directory_mode": oct(stat.S_IMODE(scratch.stat().st_mode)), "fixed_fixture_script_execution_exit": ran.returncode,
                       "actual_delivery_permission_function_tested": True,
                       "fixture_device": scratch.stat().st_dev, "restored_NTFS_device": RESTORE.stat().st_dev,
                       "restored_NTFS_tree_POSIX_modes_or_ACLs_certified": False}
    finally:
        assert scratch.resolve().parent == Path("/tmp") and scratch.name.startswith("a7-posix-modes-")
        shutil.rmtree(scratch)
    result = {"passed": True, "observed_utc": datetime.now(timezone.utc).isoformat(), "restored_relative_internal_links": outcomes,
              "internal_links_created_resolved_and_contained": 25, "external_runtime_junctions_not_recreated": 2,
              "original_source_links_followed_or_modified": False, "POSIX_fixture": mode_result, "scratch_copies_cleaned": True,
              "original_modes_and_owners_for_all_untracked_files_known": False,
              "target_Linux_server_permissions_GPU_environment_or_training_validated": False,
              "model_scientific_array_checkpoint_or_training_loads": 0}
    (PHASE / "POSIX_LINK_CHECKS.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"passed": True, "relative_links": 25, "junctions_deferred": 2, "POSIX_fixture_passed": True}), flush=True)


if __name__ == "__main__":
    main()
