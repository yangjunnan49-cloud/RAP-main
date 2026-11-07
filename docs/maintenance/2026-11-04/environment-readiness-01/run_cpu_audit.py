"""Run the narrowly scoped CPU dependency gate and restore WSL's stopped state."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

PHASE = Path(__file__).resolve().parent


def command(argv, timeout=30):
    proc = subprocess.run(argv, capture_output=True, timeout=timeout)
    def decode(value):
        return value.decode("utf-16-le" if b"\x00" in value else "utf-8", errors="replace").lstrip("\ufeff")
    return {"argv": argv, "exit_code": proc.returncode, "stdout": decode(proc.stdout), "stderr": decode(proc.stderr)}


def main():
    assert not (PHASE / "CPU_PROBE.json").exists()
    result = {"started_utc": datetime.now(timezone.utc).isoformat(), "events": []}
    before = command(["wsl.exe", "--list", "--running", "--quiet"])
    result["events"].append(before)
    assert before["exit_code"] == 0 and not before["stdout"].strip()
    base = ["wsl.exe", "-d", "Ubuntu-24.04", "--user", "root", "--exec", "/usr/bin/env", "CUDA_VISIBLE_DEVICES=", "WANDB_MODE=disabled", "HF_HUB_OFFLINE=1", "MPLBACKEND=Agg"]
    main = "/mnt/e/githouse/RAP-main"
    phase = main + "/docs/maintenance/2026-11-04/environment-readiness-01"
    try:
        result["events"].append(command(base + ["/usr/bin/python3", "-I", "-S", "-B", phase + "/collect_supplement.py"], timeout=100))
        result["events"].append(command(base + ["/root/miniconda3/envs/rap-inference/bin/python", "-I", "-B", main + "/scripts/environment/cpu_probe.py",
                                                 "--rap-root", main, "--slam-root", "/mnt/e/githouse/RAP-SLAM", "--output", phase + "/CPU_PROBE.json"], timeout=90))
    except BaseException as exc:
        result["error"] = repr(exc)
    finally:
        result["events"].append(command(["wsl.exe", "--terminate", "Ubuntu-24.04"]))
        final = command(["wsl.exe", "--list", "--running", "--quiet"])
        result["events"].append(final)
        result["restored_initial_stopped_state"] = final["exit_code"] == 0 and not final["stdout"].strip()
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (PHASE / "CPU_SESSION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    assert result["restored_initial_stopped_state"]
    assert (PHASE / "CPU_PROBE.json").exists(), "CPU probe did not finish"


if __name__ == "__main__":
    main()
