"""Read the known build-evidence paths and restore stopped WSL state."""
from datetime import datetime, timezone
import json
import importlib.util
from pathlib import Path

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a4_host_command_helpers", PHASE / "run_cpu_audit.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
command = helpers.command


def main():
    assert not (PHASE / "BUILD_EVIDENCE.json").exists()
    result = {"started_utc": datetime.now(timezone.utc).isoformat(), "events": []}
    before = command(["wsl.exe", "--list", "--running", "--quiet"])
    result["events"].append(before)
    assert before["exit_code"] == 0 and not before["stdout"].strip()
    argv = ["wsl.exe", "-d", "Ubuntu-24.04", "--user", "root", "--exec", "/usr/bin/env", "CUDA_VISIBLE_DEVICES=", "HF_HUB_OFFLINE=1",
            "/usr/bin/python3", "-I", "-S", "-B", "/mnt/e/githouse/RAP-main/docs/maintenance/2026-11-04/environment-readiness-01/collect_build_evidence.py"]
    try:
        result["events"].append(command(argv, timeout=50))
    finally:
        result["events"].append(command(["wsl.exe", "--terminate", "Ubuntu-24.04"]))
        final = command(["wsl.exe", "--list", "--running", "--quiet"])
        result["events"].append(final)
        result["restored_initial_stopped_state"] = final["exit_code"] == 0 and not final["stdout"].strip()
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (PHASE / "BUILD_SESSION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    assert result["restored_initial_stopped_state"] and (PHASE / "BUILD_EVIDENCE.json").exists()


if __name__ == "__main__":
    main()
