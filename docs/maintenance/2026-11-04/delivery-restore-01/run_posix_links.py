"""Bound a filesystem-only WSL session and restore the observed stopped state."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

PHASE = Path(__file__).resolve().parent


def query(argv, timeout=30):
    p = subprocess.run(argv, capture_output=True, timeout=timeout)
    def decode(b):
        return b.decode("utf-16-le" if b"\x00" in b else "utf-8", errors="replace").lstrip("\ufeff")
    return {"argv": argv, "exit_code": p.returncode, "stdout": decode(p.stdout), "stderr": decode(p.stderr)}


def main():
    assert json.loads((PHASE / "PROJECT_RESTORE.json").read_text(encoding="utf-8"))["passed"]
    assert not (PHASE / "WSL_LINK_SESSION.json").exists()
    result = {"started_utc": datetime.now(timezone.utc).isoformat(), "scope": "A7_PLAN_ITEM_3_LOCAL_FILESYSTEM_LINK_AND_MODE_ACCEPTANCE_ONLY", "events": []}
    before = query(["wsl.exe", "--list", "--running", "--quiet"])
    result["events"].append(before)
    assert before["exit_code"] == 0 and not before["stdout"].strip(), "Initial stopped-state guard"
    try:
        path = "/mnt/e/githouse/RAP-main/docs/maintenance/2026-11-04/delivery-restore-01/posix_links.py"
        result["events"].append(query(["wsl.exe", "-d", "Ubuntu-24.04", "--user", "root", "--exec", "/usr/bin/env", "CUDA_VISIBLE_DEVICES=", "WANDB_MODE=disabled", "HF_HUB_OFFLINE=1",
                                       "/usr/bin/python3", "-I", "-S", "-B", path], timeout=45))
    except BaseException as error:
        result["error"] = repr(error)
    finally:
        result["events"].append(query(["wsl.exe", "--terminate", "Ubuntu-24.04"]))
        after = query(["wsl.exe", "--list", "--running", "--quiet"])
        result["events"].append(after)
        result["restored_initial_stopped_state"] = after["exit_code"] == 0 and not after["stdout"].strip()
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (PHASE / "WSL_LINK_SESSION.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False), flush=True)
    assert result["restored_initial_stopped_state"]
    assert (PHASE / "POSIX_LINK_CHECKS.json").exists() and result["events"][1]["exit_code"] == 0


if __name__ == "__main__":
    main()
