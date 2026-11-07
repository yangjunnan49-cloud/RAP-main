"""Read back final migration authority and existing acceptance receipts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

local = "--local" in sys.argv
phase = Path(__file__).resolve().parent
workspace = Path("E:/githouse") if local else Path("/root/autodl-tmp/rap-workspace-20261106")
control = phase if local else Path("/root/autodl-tmp/rap-migration-20261106")
authority_path = phase / "AUTHORITY_PROOF.json" if local else control / "SERVER_AUTHORITY.json"
authority_bytes = authority_path.read_bytes()
authority = json.loads(authority_bytes)
roots = {"rap-main": workspace / "RAP-main", "rap-slam": workspace / "RAP-SLAM",
         "reports": workspace / "RAP-SLAM-report", "workspace-root": workspace}
for row in authority["current_files"]:
    data = (roots[row["root"]] / row["path"]).read_bytes()
    assert len(data) == row["bytes"]
    assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
assert len(authority["current_files"]) == 83
result = dict(observed_utc=datetime.now(timezone.utc).isoformat(),
              scope="FINAL_AUTHORITY_AND_EXISTING_RECEIPTS_READBACK",
              current_authority_files_freshly_rehashed=83,
              authority_sha256=hashlib.sha256(authority_bytes).hexdigest(),
              passed=True, training_or_resume_validated=False)
if local:
    receipt = json.loads((phase / "MIGRATION_COMPLETE.json").read_bytes())
    assert receipt["server_file_layer_passed"] and receipt["bounded_functional_gate_passed"]
    assert receipt["all_local_current_authority_hashes_match_server"]
    destination = phase / "FINAL_LOCAL_READBACK.json"
else:
    finalized = json.loads((control / "SERVER_FINALIZED.json").read_bytes())
    assert finalized["authority_sha256"] == result["authority_sha256"]
    files = json.loads((control / "file-acceptance/ACCEPTANCE.json").read_bytes())
    functional = json.loads((control / "MIGRATION_ACCEPTANCE.json").read_bytes())
    assert files["actual_server_file_restore_and_rehash_passed"] and functional["passed"]
    result["file_and_bounded_functional_receipts_passed"] = True
    result["disk_usage_bytes"] = {str(p): dict(zip(("total", "used", "free"), shutil.disk_usage(p)))
        for p in (Path("/root/autodl-tmp"), Path("/root/autodl-fs"))}
    gpu = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
        "--format=csv,noheader"], capture_output=True, text=True, timeout=15)
    assert gpu.returncode == 0, gpu.stderr
    result["observed_GPU_compute_processes"] = gpu.stdout.strip().splitlines()
    names = {"receive_and_restore.py", "finish_environment.py", "post_restore_acceptance.py",
             "apply_control.py", "preserve_environment.py", "rebuild_public_volumes.py"}
    running = []
    for command in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            args = command.read_bytes().split(b"\0")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(Path(arg.decode(errors="replace")).name in names for arg in args):
            running.append(int(command.parent.name))
    result["observed_active_migration_pipeline_pids"] = running
    destination = control / "FINAL_SERVER_READBACK.json"
with destination.open("x", encoding="utf-8") as output:
    json.dump(result, output, ensure_ascii=False, indent=2)
    output.write("\n")
print(json.dumps(result, ensure_ascii=False))
