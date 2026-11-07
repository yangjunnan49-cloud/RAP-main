"""Scope the A4 Linux metadata start and restore the observed stopped state."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

PHASE = Path(__file__).resolve().parent


def query(argv, timeout=30):
    proc = subprocess.run(argv, capture_output=True, timeout=timeout)
    def decode(raw):
        return raw.decode("utf-16-le" if b"\x00" in raw else "utf-8", errors="replace").lstrip("\ufeff")
    return {"argv": argv, "exit_code": proc.returncode, "stdout": decode(proc.stdout), "stderr": decode(proc.stderr)}


def main():
    result = {"started_utc": datetime.now(timezone.utc).isoformat(), "scope": "A4_PLAN_ITEM_2_READ_ONLY_METADATA", "events": []}
    assert not (PHASE / "LINUX_OBSERVATION.json").exists(), "Refusing a second collection without review"
    before = query(["wsl.exe", "--list", "--running", "--quiet"])
    result["events"].append(before)
    assert before["exit_code"] == 0 and before["stdout"].strip() == "", "Expected no running distribution"
    path = "/mnt/e/githouse/RAP-main/docs/maintenance/2026-11-04/environment-readiness-01/collect_linux.py"
    argv = ["wsl.exe", "-d", "Ubuntu-24.04", "--user", "root", "--exec", "/usr/bin/env", "CUDA_VISIBLE_DEVICES=", "WANDB_MODE=disabled", "HF_HUB_OFFLINE=1",
            "/usr/bin/python3", "-I", "-S", "-B", path]
    try:
        result["events"].append(query(argv, timeout=150))
    except BaseException as exc:
        result["collection_error"] = repr(exc)
    finally:
        result["events"].append(query(["wsl.exe", "--terminate", "Ubuntu-24.04"]))
        result["events"].append(query(["wsl.exe", "--list", "--verbose"]))
        running = query(["wsl.exe", "--list", "--running", "--quiet"])
        result["events"].append(running)
        result["restored_initial_stopped_state"] = running["exit_code"] == 0 and not running["stdout"].strip()
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (PHASE / "LINUX_SESSION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    assert result["restored_initial_stopped_state"], "WSL state not restored"
    assert (PHASE / "LINUX_OBSERVATION.json").is_file(), "Linux collection did not complete"
    assert result["events"][1].get("exit_code") == 0, "Linux collector failed"


if __name__ == "__main__":
    main()
