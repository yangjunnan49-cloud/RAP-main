"""Preserve installed build artifacts and resolve environment path aliases."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

PHASE = Path(__file__).resolve().parent
SITE = Path("/root/miniconda3/envs/rap-inference/lib/python3.10/site-packages")


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "path_aliases": [], "installed_artifacts": [], "wheel_inventory": [], "elf_architecture": []}
    raw = json.loads((PHASE / "LINUX_OBSERVATION.json").read_text(encoding="utf-8"))
    for env in raw["environments"]:
        for value in env["sites"]:
            path = Path(value)
            result["path_aliases"].append({"path": value, "resolved": str(path.resolve()), "inode": path.stat().st_ino, "device": path.stat().st_dev})
    for package in ("pytorch3d", "torch_cluster"):
        directory = SITE / package
        if not directory.is_dir():
            continue
        for source in sorted(directory.rglob("*")):
            if not source.is_file() or source.is_symlink() or "__pycache__" in source.parts:
                continue
            target = PHASE / "linux-preservation/installed-artifacts" / source.as_posix().lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            row = {"source": str(source), "copy": target.relative_to(PHASE).as_posix(), "bytes": source.stat().st_size, "sha256": sha(target)}
            result["installed_artifacts"].append(row)
            if source.suffix == ".so":
                tool = Path("/usr/local/cuda-12.8/bin/cuobjdump")
                if tool.is_file():
                    proc = subprocess.run([str(tool), "--list-elf", str(source)], capture_output=True, text=True, timeout=20)
                    result["elf_architecture"].append({"path": str(source), "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    for source in sorted(Path("/root/pytorch_wheels").glob("*.whl")):
        result["wheel_inventory"].append({"path": str(source), "bytes": source.stat().st_size, "sha256": sha(source), "copied_to_windows": False})
    (PHASE / "LINUX_SUPPLEMENT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"installed_artifacts_preserved": len(result["installed_artifacts"]), "wheels_fingerprinted": len(result["wheel_inventory"])}))


if __name__ == "__main__":
    main()
