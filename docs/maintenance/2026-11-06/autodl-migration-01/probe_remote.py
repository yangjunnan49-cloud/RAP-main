"""Read target hardware/storage/package metadata without loading models or datasets."""
from datetime import datetime, timezone
import importlib.metadata as md
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def command(argv):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=20)
        return {"argv": argv, "exit_code": r.returncode, "stdout": r.stdout[:12000], "stderr": r.stderr[:2000]}
    except Exception as error:
        return {"argv": argv, "error": repr(error)}


def main():
    disks = []
    for name in ("/", "/root", "/root/autodl-tmp", "/root/autodl-fs", "/autodl-fs", "/data", "/workspace"):
        p = Path(name)
        if p.is_dir():
            d = shutil.disk_usage(p)
            disks.append({"path": name, "total": d.total, "used": d.used, "free": d.free, "device": p.stat().st_dev,
                          "top_level_names": sorted(x.name for x in p.iterdir())[:45]})
    packages = {}
    for name in ("torch", "torchvision", "torchaudio", "numpy", "scipy", "pytorch3d", "torch-cluster", "kiss-icp", "gtsam", "open3d", "evo",
                 "lightning", "pytorch-lightning", "hydra-core", "omegaconf", "diffusers", "muon", "transformers", "h5py", "einops", "timm", "paramiko"):
        try:
            packages[name] = md.version(name)
        except md.PackageNotFoundError:
            packages[name] = None
    envs = []
    for folder in ("/root/miniconda3/envs", "/opt/conda/envs", "/root/venvs"):
        p = Path(folder)
        if p.is_dir():
            envs += [str(x) for x in p.iterdir() if x.is_dir()]
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "uname": platform.uname()._asdict(), "python": sys.version,
              "python_executable": sys.executable, "os_release": Path("/etc/os-release").read_text() if Path("/etc/os-release").exists() else None,
              "disks": disks, "environment_directories": envs, "installed_metadata_versions_current_python": packages,
              "commands": [command(["df", "-hT"]), command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
                           command(["nvcc", "--version"]), command(["git", "--version"])],
              "models_datasets_checkpoints_or_training_loaded": False}
    Path("/tmp/rap-migration-20261106-preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    print("__RAP_PREFLIGHT_DONE__", flush=True)


if __name__ == "__main__":
    main()
