"""Build the isolated, versioned AutoDL migration environment; never train."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import traceback

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
ENV = Path("/root/autodl-tmp/rap-envs/rap-20261106")
PYTHON = str(ENV / "bin/python")
COMMIT = "33824be3cbc87a7dd1db0f6a9a9de9ac81b2d0ba"
SOURCE_SHA = "3c7076b9007e1994234e3461081c5394dbfe75966192fe258e336322869fe77d"


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(name, args, *, environment=None, cwd=None, timeout=7200):
    log = ROOT / "logs" / (name + ".log")
    with log.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(dict(started_utc=utc(), command=args, cwd=str(cwd))) + "\n")
        stream.flush()
        completed = subprocess.run(args, cwd=cwd, env=environment, stdout=stream,
                                   stderr=subprocess.STDOUT, timeout=timeout)
    save("logs/" + name + ".result.json", dict(completed_utc=utc(), returncode=completed.returncode))
    if completed.returncode:
        raise RuntimeError(name + " failed; see preserved log")


def main():
    if (ROOT / "ENVIRONMENT_STARTED.json").exists():
        raise SystemExit("Environment receipt already exists")
    save("ENVIRONMENT_STARTED.json", dict(started_utc=utc(), pid=os.getpid(), isolated_environment=str(ENV),
         attempt="02_hash_pinned_mirror", base_Python_packages_intentionally_modified=False, training=False))
    started = time.monotonic()
    while not (ROOT / "logs/torch-install.exit").exists():
        if time.monotonic() - started > 3 * 3600:
            raise TimeoutError("Initial Torch installation wait exceeded three hours")
        time.sleep(20)
    if (ROOT / "logs/torch-install.exit").read_text().strip() != "0":
        raise RuntimeError("Initial Torch installation failed")
    environment = dict(os.environ)
    environment.update(PATH=str(ENV / "bin") + ":/usr/local/cuda-12.8/bin:" + environment.get("PATH", ""),
                       CUDA_HOME="/usr/local/cuda-12.8", PYTHONDONTWRITEBYTECODE="1",
                       MAX_JOBS="4", WANDB_MODE="disabled", HF_HUB_OFFLINE="1", MPLBACKEND="Agg")
    inputs = ROOT / "environment-inputs"
    run("build-tools-02", [PYTHON, "-m", "pip", "install", "--no-cache-dir", "--no-deps",
        "--require-hashes", "--no-build-isolation", "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
        "--report", str(ROOT / "logs/build-tools-02-report.json"), "-r", str(inputs / "build-tools-02.txt")], environment=environment)
    run("profiles-install", [PYTHON, "-m", "pip", "install", "--no-cache-dir", "--report",
        str(ROOT / "logs/profiles-install-report.json"), "--no-deps", "--require-hashes", "--no-build-isolation",
        "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
        "-r", str(inputs / "resolved-profile-02.txt")], environment=environment)
    run("profiles-pip-check", [PYTHON, "-m", "pip", "check"], environment=environment, timeout=120)
    gpu_code = """import torch,json,sys
assert sys.version_info[:3] == (3,10,20), sys.version
assert torch.__version__ == '2.7.0+cu128', torch.__version__
assert torch.cuda.is_available()
p=torch.cuda.get_device_properties(0)
print(json.dumps({'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':p.name,
 'memory_bytes':p.total_memory,'capability':list(torch.cuda.get_device_capability(0))}))
"""
    gpu = json.loads(subprocess.check_output([PYTHON, "-B", "-c", gpu_code], env=environment, text=True))
    save("TARGET_GPU.json", gpu)
    arch = ".".join(map(str, gpu["capability"]))
    environment.update(TORCH_CUDA_ARCH_LIST=arch, FORCE_CUDA="1")
    cub = Path("/usr/local/cuda-12.8/include")
    if (cub / "cub").is_dir():
        environment["CUB_HOME"] = str(cub)
    archive = ROOT / "pytorch3d-local-source.tar.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == SOURCE_SHA
    sources = ROOT / "sources"
    sources.mkdir()
    with tarfile.open(archive) as stream:
        assert all(member.name.startswith("pytorch3d-" + COMMIT + "/") or
                   member.name == "pytorch3d-" + COMMIT for member in stream.getmembers())
        stream.extractall(sources, filter="data")
    source = sources / ("pytorch3d-" + COMMIT)
    wheelhouse = ROOT / "wheelhouse"
    wheelhouse.mkdir()
    save("PYTORCH3D_BUILD_INPUT.json", dict(source_commit=COMMIT, archive_sha256=SOURCE_SHA,
        source_url="https://codeload.github.com/facebookresearch/pytorch3d/tar.gz/" + COMMIT,
        patches=[], CUDA_HOME=environment["CUDA_HOME"], TORCH_CUDA_ARCH_LIST=arch, MAX_JOBS=4,
        original_historical_build_commit_recovered=False, byte_identical_historical_binary_claimed=False))
    run("pytorch3d-wheel", [PYTHON, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
        str(source), "--wheel-dir", str(wheelhouse)], environment=environment, cwd=source)
    wheels = list(wheelhouse.glob("pytorch3d-*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]
    save("PYTORCH3D_WHEEL.json", dict(path=str(wheel), bytes=wheel.stat().st_size,
         sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(), source_commit=COMMIT, arch=arch))
    run("pytorch3d-install", [PYTHON, "-m", "pip", "install", "--no-deps", "--report",
        str(ROOT / "logs/pytorch3d-install-report.json"), str(wheel)], environment=environment, timeout=300)
    run("final-pip-check", [PYTHON, "-m", "pip", "check"], environment=environment, timeout=120)
    run("pip-freeze", [PYTHON, "-m", "pip", "freeze", "--all"], environment=environment, timeout=120)
    save("ENVIRONMENT_READY.json", dict(completed_utc=utc(), isolated_environment=str(ENV),
        dependency_install_and_pip_check_passed=True, gpu_properties=gpu,
        base_Python_packages_intentionally_modified=False, GPU_extension_execution_validated=False,
        model_IO_validated=False, training_or_resume_validated=False))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        save("ENVIRONMENT_FAILURE.json", dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise
