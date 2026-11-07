"""Resume target construction after the recorded GTSAM metadata-only repair."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import traceback

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
ENV = Path("/root/autodl-tmp/rap-envs/rap-20261106")
PYTHON = str(ENV / "bin/python")
COMMIT = "33824be3cbc87a7dd1db0f6a9a9de9ac81b2d0ba"
SOURCE_SHA = "3c7076b9007e1994234e3461081c5394dbfe75966192fe258e336322869fe77d"


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    assert not (ROOT / "ENVIRONMENT_STARTED.json").exists()
    repair = json.loads((ROOT / "GTSAM_METADATA_REPAIR.json").read_text())
    assert repair["passed"] and repair["all_other_member_bytes_unchanged"]
    save("ENVIRONMENT_STARTED.json", dict(started_utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
        attempt="03_metadata_repair_then_native_build", isolated_environment=str(ENV),
        base_Python_packages_intentionally_modified=False, training=False))
    spec = importlib.util.spec_from_file_location("bootstrap_functions", ROOT / "bootstrap_environment.py")
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
    environment = dict(os.environ)
    environment.update(PATH=str(ENV / "bin") + ":/usr/local/cuda-12.8/bin:" + environment.get("PATH", ""),
        CUDA_HOME="/usr/local/cuda-12.8", PYTHONDONTWRITEBYTECODE="1", MAX_JOBS="4",
        WANDB_MODE="disabled", HF_HUB_OFFLINE="1", MPLBACKEND="Agg")
    bootstrap.run("profiles-pip-check-03", [PYTHON, "-m", "pip", "check"], environment=environment, timeout=120)
    gpu_code = """import torch,json,sys
assert sys.version_info[:3]==(3,10,20)
assert torch.__version__=='2.7.0+cu128'
assert torch.cuda.is_available()
p=torch.cuda.get_device_properties(0)
print(json.dumps({'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':p.name,
'memory_bytes':p.total_memory,'capability':list(torch.cuda.get_device_capability(0))}))
"""
    gpu = json.loads(subprocess.check_output([PYTHON, "-B", "-c", gpu_code], env=environment, text=True))
    save("TARGET_GPU.json", gpu)
    arch = ".".join(map(str, gpu["capability"]))
    environment.update(TORCH_CUDA_ARCH_LIST=arch, FORCE_CUDA="1")
    if Path("/usr/local/cuda-12.8/include/cub").is_dir():
        environment["CUB_HOME"] = "/usr/local/cuda-12.8/include"
    archive = ROOT / "pytorch3d-local-source.tar.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == SOURCE_SHA
    sources, wheelhouse = ROOT / "sources", ROOT / "wheelhouse"
    sources.mkdir()
    wheelhouse.mkdir()
    with tarfile.open(archive) as stream:
        assert all(member.name == "pytorch3d-" + COMMIT or member.name.startswith("pytorch3d-" + COMMIT + "/") for member in stream.getmembers())
        stream.extractall(sources, filter="data")
    source = sources / ("pytorch3d-" + COMMIT)
    save("PYTORCH3D_BUILD_INPUT.json", dict(source_commit=COMMIT, archive_sha256=SOURCE_SHA,
        source_url="https://codeload.github.com/facebookresearch/pytorch3d/tar.gz/" + COMMIT,
        patches=[], CUDA_HOME=environment["CUDA_HOME"], TORCH_CUDA_ARCH_LIST=arch, MAX_JOBS=4,
        original_historical_build_commit_recovered=False, byte_identical_historical_binary_claimed=False))
    bootstrap.run("pytorch3d-wheel", [PYTHON, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", str(source),
        "--wheel-dir", str(wheelhouse)], environment=environment, cwd=source)
    wheels = list(wheelhouse.glob("pytorch3d-*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]
    save("PYTORCH3D_WHEEL.json", dict(path=str(wheel), bytes=wheel.stat().st_size,
        sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(), source_commit=COMMIT, arch=arch))
    bootstrap.run("pytorch3d-install", [PYTHON, "-m", "pip", "install", "--no-deps", "--report",
        str(ROOT / "logs/pytorch3d-install-report.json"), str(wheel)], environment=environment, timeout=300)
    bootstrap.run("final-pip-check", [PYTHON, "-m", "pip", "check"], environment=environment, timeout=120)
    bootstrap.run("pip-freeze", [PYTHON, "-m", "pip", "freeze", "--all"], environment=environment, timeout=120)
    save("ENVIRONMENT_READY.json", dict(completed_utc=datetime.now(timezone.utc).isoformat(), isolated_environment=str(ENV),
        dependency_install_and_pip_check_passed=True, gpu_properties=gpu,
        GTSAM_metadata_only_repair_runtime_bytes_unchanged=True, base_Python_packages_intentionally_modified=False,
        GPU_extension_execution_validated=False, model_IO_validated=False, training_or_resume_validated=False))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        save("ENVIRONMENT_FAILURE.json", dict(error=repr(exc), traceback=traceback.format_exc()))
        raise
