"""Check all five restored launcher path contracts with numerical imports audited."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

PHASE = Path(__file__).resolve().parent

BOOTSTRAP = r'''
import json,runpy,sys
sys.argv=sys.argv[1:]
code=0
try:
    runpy.run_path(sys.argv[0],run_name="__main__")
except SystemExit as exc:
    code=exc.code if isinstance(exc.code,int) else 1
blocked=("torch","numpy","open3d","pytorch3d","lightning","pytorch_lightning")
loaded=sorted(k for k in sys.modules if k.split(".")[0] in blocked)
print("__A7_IMPORT_AUDIT__"+json.dumps({"numeric_or_model_modules_loaded":loaded,"exit_code":code}))
raise SystemExit(code if not loaded else 99)
'''


def main():
    assert json.loads((PHASE / "PROJECT_RESTORE.json").read_text(encoding="utf-8"))["passed"]
    root = Path(json.loads((PHASE / "RESTORE_DESTINATION.json").read_text(encoding="utf-8"))["directory"]) / "workspace"
    rap = root / "RAP-main"
    config = rap / "config/runtime.example.json"
    output = root / "RAP-runs"
    poses = rap / "docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam/poses"
    dataset = root / "Datasets/data_odometry_velodyne/dataset"
    cases = []
    for task in ("sample", "demo", "features"):
        cases.append((task, [task, "--paths", str(config), "--input", str(rap / "demo_example_data"), "--run-id", "a7-acceptance-" + task, "--check"]))
    cases.append(("slam", ["slam", "--paths", str(config), "--real-root", str(dataset.parent), "--run-id", "a7-acceptance-slam", "--check", "--",
                            "--source", "real", "--real-seq", "00", "--real-start", "0", "--real-end", "10", "--real-apply-calib"]))
    cases.append(("evaluate", ["evaluate", "--paths", str(config), "--poses-dir", str(poses), "--dataset-root", str(dataset), "--sequences", "00",
                                "--method-label", "a7-path-contract-only", "--run-id", "a7-acceptance-evaluate", "--check"]))
    env = {k: v for k, v in os.environ.items() if not k.startswith("RAP_")}
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1", "WANDB_MODE": "disabled"})
    folder = PHASE / "validation"
    folder.mkdir(exist_ok=True)
    results = []
    for name, args in cases:
        argv = [sys.executable, "-X", "utf8", "-I", "-B", "-c", BOOTSTRAP, str(rap / "scripts/run.py"), *args]
        ran = subprocess.run(argv, cwd=PHASE, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30)
        (folder / (name + ".stdout.txt")).write_bytes(ran.stdout.encode("utf-8"))
        (folder / (name + ".stderr.txt")).write_bytes(ran.stderr.encode("utf-8"))
        assert ran.returncode == 0, (name, ran.stderr, ran.stdout[-1500:])
        raw_plan, raw_audit = ran.stdout.split("__A7_IMPORT_AUDIT__", 1)
        plan, audit = json.loads(raw_plan), json.loads(raw_audit)
        assert not plan["errors"] and not audit["numeric_or_model_modules_loaded"]
        assert all(Path(r["path"]).resolve().is_relative_to(root.resolve()) for r in plan["required_paths"])
        assert Path(plan["cwd"]).resolve().is_relative_to(root.resolve())
        assert not Path(plan["output"]).exists()
        results.append({"task": name, "exit_code": 0, "required_path_count": len(plan["required_paths"]),
                        "required_paths_all_in_new_workspace": True, "numerical_modules_loaded": [], "model_or_child_task_execution": False})
    tests = []
    for name in ("test_runtime_paths.py", "test_environment_tools.py"):
        ran = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(rap / "tests" / name)], cwd=PHASE, env=env,
                             capture_output=True, text=True, encoding="utf-8", timeout=60)
        (folder / (name + ".stdout.txt")).write_bytes(ran.stdout.encode("utf-8"))
        (folder / (name + ".stderr.txt")).write_bytes(ran.stderr.encode("utf-8"))
        assert ran.returncode == 0, (name, ran.stderr[-2000:])
        tests.append({"file": name, "exit_code": ran.returncode, "summary": ran.stderr[-250:]})
    assert not output.exists(), "Path checks must not create output directories"
    git_results = []
    git = Path("C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe")
    expected = {(r["root"], r["path"]): r for r in [json.loads(line) for line in (PHASE / "PROJECT_FILES.jsonl").read_text(encoding="utf-8").splitlines()]}
    import hashlib
    for rid, folder_name in (("rap-main", "RAP-main"), ("rap-slam", "RAP-SLAM")):
        repository = root / folder_name
        index = repository / ".git/index"
        index_before = hashlib.sha256(index.read_bytes()).hexdigest()
        assert index_before == expected[(rid, ".git/index")]["sha256"]
        commands = []
        for argument in ("HEAD", "--show-toplevel"):
            ran = subprocess.run([str(git), "-c", "core.longpaths=true", "-c", "safe.directory=" + str(repository), "-C", str(repository), "rev-parse", argument],
                                 env=dict(env, GIT_OPTIONAL_LOCKS="0"), capture_output=True, text=True, encoding="utf-8", timeout=30)
            assert ran.returncode == 0, ran.stderr
            commands.append(ran.stdout.strip())
        assert Path(commands[1]).resolve() == repository.resolve()
        source_git_state = json.loads((PHASE.parents[3] / "docs/maintenance/2026-11-03/migration-audit-01/git" / rid / "STATE.json").read_text(encoding="utf-8"))
        assert commands[0] == source_git_state["head"] and hashlib.sha256(index.read_bytes()).hexdigest() == index_before
        git_results.append({"root": rid, "head": commands[0], "repository_root_is_restored_tree": True, "index_sha256_unchanged": index_before,
                            "network_hooks_filters_status_or_commits_run": False})
    result = {"passed": True, "observed_utc": datetime.now(timezone.utc).isoformat(), "cases": results, "restored_standard_library_tests": tests,
              "different_working_directory": str(PHASE), "all_runtime_required_paths_relocated": True,
              "original_source_runtime_paths_used": False, "outputs_created": False, "model_data_format_or_GPU_IO_validated": False,
              "training_or_scientific_execution": False, "restored_git_read_only_checks": git_results}
    (PHASE / "RELOCATED_CHECKS.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
