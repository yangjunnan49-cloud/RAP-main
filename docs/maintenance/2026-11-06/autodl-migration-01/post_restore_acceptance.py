"""Wait for file/environment gates, then run the bounded target acceptance."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
WORKSPACE = Path("/root/autodl-tmp/rap-workspace-20261106")
PYTHON = "/root/autodl-tmp/rap-envs/rap-20261106/bin/python"


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if (ROOT / "FUNCTIONAL_STARTED.json").exists():
        raise RuntimeError("Acceptance has already been started")
    save("FUNCTIONAL_STARTED.json", dict(started_utc=utc(), pid=os.getpid(), training=False))
    start = time.monotonic()
    while True:
        for failure in (ROOT / "ENVIRONMENT_FAILURE.json", ROOT / "file-acceptance/FAILURE.json"):
            if failure.exists():
                raise RuntimeError("A prerequisite failed: " + str(failure))
        if (ROOT / "ENVIRONMENT_READY.json").exists() and (ROOT / "file-acceptance/ACCEPTANCE.json").exists():
            break
        if time.monotonic() - start > 48 * 3600:
            raise TimeoutError("File/environment prerequisite wait exceeded 48 hours")
        time.sleep(30)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("RAP_")}
    environment.update(PYTHONDONTWRITEBYTECODE="1", WANDB_MODE="disabled", WANDB_DISABLED="true",
                       HF_HUB_OFFLINE="1", MPLBACKEND="Agg", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    rap, slam = WORKSPACE / "RAP-main", WORKSPACE / "RAP-SLAM"
    config = rap / "config/runtime.example.json"
    dataset = WORKSPACE / "Datasets/data_odometry_velodyne/dataset"
    poses = rap / "docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam/poses"
    cases = []
    for task in ("sample", "demo", "features"):
        cases.append((task, [task, "--paths", str(config), "--input", str(rap / "demo_example_data"),
                             "--run-id", "a8-path-contract-" + task, "--check"]))
    cases.append(("slam", ["slam", "--paths", str(config), "--real-root", str(dataset.parent),
        "--run-id", "a8-path-contract-slam", "--check", "--", "--source", "real", "--real-seq", "00",
        "--real-start", "0", "--real-end", "10", "--real-apply-calib"]))
    cases.append(("evaluate", ["evaluate", "--paths", str(config), "--poses-dir", str(poses),
        "--dataset-root", str(dataset), "--sequences", "00", "--method-label", "a8-path-contract-only",
        "--run-id", "a8-path-contract-evaluate", "--check"]))
    path_results = []
    for task, args in cases:
        command = [PYTHON, "-I", "-B", str(rap / "scripts/run.py"), *args]
        completed = subprocess.run(command, cwd=ROOT, env=dict(environment, CUDA_VISIBLE_DEVICES=""),
                                   capture_output=True, text=True, timeout=45)
        (ROOT / "logs" / ("paths-" + task + ".stdout.txt")).write_text(completed.stdout, encoding="utf-8")
        (ROOT / "logs" / ("paths-" + task + ".stderr.txt")).write_text(completed.stderr, encoding="utf-8")
        assert completed.returncode == 0, task
        plan = json.loads(completed.stdout)
        assert not plan["errors"] and not Path(plan["output"]).exists()
        assert all(Path(row["path"]).resolve().is_relative_to(WORKSPACE.resolve()) for row in plan["required_paths"])
        path_results.append(dict(task=task, passed=True, execution=False))
    save("PATH_CHECKS.json", dict(passed=True, cases=path_results))
    commands = [
        ("cpu-probe", [PYTHON, "-I", "-B", str(rap / "scripts/environment/cpu_probe.py"),
             "--rap-root", str(rap), "--slam-root", str(slam), "--output", str(ROOT / "CPU_PROBE.json")],
             dict(environment, CUDA_VISIBLE_DEVICES=""), 180),
        ("gpu-model-probe", [PYTHON, "-I", "-B", str(ROOT / "gpu_model_probe.py"),
             "--workspace", str(WORKSPACE), "--inputs", str(ROOT / "SMOKE_INPUTS.json"),
             "--output", str(ROOT / "GPU_MODEL_PROBE.json")], environment, 600),
    ]
    for name, command, env, timeout in commands:
        with (ROOT / "logs" / (name + ".log")).open("x", encoding="utf-8") as stream:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        if completed.returncode:
            raise RuntimeError(name + " failed; no parameter or input fallback is authorized")
    cpu = json.loads((ROOT / "CPU_PROBE.json").read_text())
    gpu = json.loads((ROOT / "GPU_MODEL_PROBE.json").read_text())
    assert cpu["cpu_import_gate_passed"] and gpu["passed"]
    save("MIGRATION_ACCEPTANCE.json", dict(completed_utc=utc(), passed=True,
         file_restore_and_full_hash_gate_passed=True, five_path_contracts_passed=True,
         CPU_import_and_ABI_gate_passed=True, GPU_extension_and_one_pair_model_IO_passed=True,
         new_scientific_result_or_comparison=False, training_or_resume_validated=False,
         original_PyTorch3D_commit_recovered=False, original_image_or_local_assets_changed=False))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        save("FUNCTIONAL_FAILURE.json", dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise
