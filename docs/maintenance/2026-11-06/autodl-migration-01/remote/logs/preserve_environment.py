"""Preserve admitted target wheels, sources, and build inputs on the cloud disk."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import traceback

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
DEST = Path("/root/autodl-fs/rap-transfer-20261106/A8-environment-20261106")


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8388608), b""):
            value.update(block)
    return value.hexdigest()


def main():
    deadline = time.monotonic() + 3 * 3600
    while not (ROOT / "ENVIRONMENT_READY.json").exists():
        if (ROOT / "ENVIRONMENT_FAILURE.json").exists():
            raise RuntimeError("Environment construction failed; source assets remain in the migration directory")
        if time.monotonic() > deadline:
            raise TimeoutError("Environment preservation wait exceeded three hours")
        time.sleep(20)
    DEST.mkdir()
    sources = []
    for folder in ("gtsam-original-wheel", "gtsam-derived-wheel", "wheelhouse", "environment-inputs"):
        sources.extend(path for path in (ROOT / folder).rglob("*") if path.is_file() and not path.is_symlink())
    admitted = json.loads((ROOT / "TORCH_RANGED_DOWNLOAD.json").read_text())
    torch = Path(admitted["path"])
    assert sha(torch) == admitted["sha256"]
    sources.append(torch)
    sources.append(ROOT / "pytorch3d-local-source.tar.gz")
    for name in ("ENVIRONMENT_READY.json", "TARGET_GPU.json", "GTSAM_METADATA_REPAIR.json", "GTSAM_INSTALLED_BYTE_CHECKS.json",
                 "GTSAM_ORIGINAL_INPUT.json", "PROFILE_02_INPUT.json", "TORCH_RANGED_DOWNLOAD.json", "TORCH_WHEEL_SOURCE.json",
                 "PYTORCH3D_BUILD_INPUT.json", "PYTORCH3D_WHEEL.json", "logs/repair_gtsam_metadata.py",
                 "logs/finish_environment.py", "logs/ENVIRONMENT_FIXES.md", "logs/pip-freeze.log",
                 "logs/torch-install-report.json", "logs/profiles-install-report.json", "logs/pytorch3d-install-report.json"):
        sources.append(ROOT / name)
    records = []
    for source in sorted(set(sources)):
        assert source.is_file()
        relative = source.relative_to(ROOT)
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = sha(source)
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing, length=8388608)
        assert sha(target) == expected
        records.append(dict(path=relative.as_posix(), bytes=target.stat().st_size, sha256=expected))
    metadata = DEST / "conda-meta"
    shutil.copytree("/root/autodl-tmp/rap-envs/rap-20261106/conda-meta", metadata)
    for path in sorted(metadata.rglob("*")):
        if path.is_file():
            records.append(dict(path=path.relative_to(DEST).as_posix(), bytes=path.stat().st_size, sha256=sha(path)))
    explicit = subprocess.check_output(["/root/miniconda3/bin/conda", "list", "--prefix", "/root/autodl-tmp/rap-envs/rap-20261106", "--explicit", "--md5"])
    (DEST / "CONDA_EXPLICIT.txt").write_bytes(explicit)
    records.append(dict(path="CONDA_EXPLICIT.txt", bytes=len(explicit), sha256=hashlib.sha256(explicit).hexdigest()))
    value = dict(passed=True, completed_utc=datetime.now(timezone.utc).isoformat(), directory=str(DEST), files=records,
                 all_copied_bytes_read_back=True, complete_offline_wheelhouse=False,
                 CUDA_toolkit_driver_or_whole_OS_image_exported=False, training_or_resume_validated=False)
    (DEST / "MANIFEST.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    (ROOT / "ENVIRONMENT_ASSETS_PRESERVED.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        (ROOT / "ENVIRONMENT_PRESERVATION_FAILURE.json").write_text(json.dumps(dict(error=repr(exc), traceback=traceback.format_exc()), indent=2) + "\n")
        raise
