"""A4 read-only Linux metadata/source collection; stdlib only, no site initialization."""
import base64
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

PHASE = Path(__file__).resolve().parent
STORE = PHASE / "linux-preservation"
PREFIXES = [Path("/root/miniconda3/envs/rap-inference"), Path("/root/venvs/kiss-slam-hc1"), Path("/root/miniconda3"), Path("/usr")]
CORE = {"torch", "pytorch3d", "lightning", "pytorch-lightning", "torchmetrics", "diffusers", "hydra-core", "omegaconf",
        "open3d", "kiss-icp", "gtsam", "muon", "torch-cluster", "torch-scatter", "torch-sparse", "torch-spline-conv"}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def preserve(path, group):
    target = STORE / group / path.as_posix().lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    return {"source": str(path), "copy": target.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(target)}


def command(argv, timeout=15, cwd=None):
    try:
        env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", CUDA_VISIBLE_DEVICES="", WANDB_MODE="disabled", HF_HUB_OFFLINE="1")
        proc = subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=timeout, cwd=cwd, env=env)
        return {"argv": argv, "cwd": str(cwd) if cwd else None, "exit_code": proc.returncode, "stdout": proc.stdout[:2000000], "stderr": proc.stderr[:200000],
                "stdout_truncated": len(proc.stdout) > 2000000}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "error": repr(exc)}


def processes():
    found = []
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            found.append({"pid": int(entry.name), "uid": entry.stat().st_uid, "comm": (entry / "comm").read_text().strip()})
        except OSError:
            pass
    return found


def main():
    assert sys.flags.no_site and sys.flags.isolated and sys.dont_write_bytecode
    assert not any(name in sys.modules for name in ("torch", "numpy", "hydra", "lightning", "open3d"))
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "collector_python": sys.version,
              "site_initialization_disabled": True, "package_imports": False, "gpu_queries_or_model_loads": False,
              "processes_before": processes(), "environments": [], "claims": [], "source_trees": [], "preserved_files": [], "commands": []}
    for source in (Path("/etc/os-release"), Path("/etc/wsl.conf"), Path("/usr/local/cuda/version.json"), Path("/usr/local/cuda-12.8/version.json")):
        if source.is_file():
            result["preserved_files"].append(preserve(source, "system"))
    result["commands"] = [command(args) for args in (["uname", "-a"], ["gcc", "--version"], ["g++", "--version"],
                                                      ["ldd", "--version"], ["cmake", "--version"], ["/usr/local/cuda-12.8/bin/nvcc", "--version"])]
    for prefix in PREFIXES:
        sites = sorted(prefix.glob("lib/python*/site-packages"))
        if prefix == Path("/usr"):
            sites += [Path("/usr/local/lib/python3.12/dist-packages"), Path("/usr/lib/python3/dist-packages")]
        env = {"prefix": str(prefix), "sites": [str(p) for p in sites if p.is_dir()], "packages": [], "record_checks": []}
        exe = prefix / "bin/python" if prefix != Path("/usr") else prefix / "bin/python3"
        if exe.is_file():
            env["interpreter"] = {"path": str(exe), "resolved": str(exe.resolve()), "sha256": sha(exe),
                                  "version_query": command([str(exe), "-I", "-S", "-B", "-c", "import sys,json; print(json.dumps({'version':sys.version,'executable':sys.executable}))"])}
        for dist in metadata.distributions(path=env["sites"]):
            name = dist.metadata.get("Name", "")
            normalized = re.sub(r"[-_.]+", "-", name.lower())
            item = {"name": name, "version": dist.version, "metadata_path": str(getattr(dist, "_path", "")), "requires_dist": dist.requires or []}
            direct = dist.read_text("direct_url.json")
            if direct:
                item["direct_url"] = json.loads(direct)
            env["packages"].append(item)
            if normalized not in CORE:
                continue
            for member in ("METADATA", "RECORD", "direct_url.json", "INSTALLER", "WHEEL"):
                source = Path(getattr(dist, "_path", ".")) / member
                if source.is_file():
                    result["preserved_files"].append(preserve(source, "distribution-metadata"))
            for member in dist.files or []:
                if member.suffix != ".py":
                    continue
                source = Path(dist.locate_file(member))
                if not source.is_file():
                    env["record_checks"].append({"distribution": name, "path": str(source), "state": "MISSING_RECORD_FILE"})
                    continue
                observed = sha(source)
                expected = None
                if member.hash and member.hash.mode == "sha256":
                    expected = base64.urlsafe_b64decode(member.hash.value + "=" * (-len(member.hash.value) % 4)).hex()
                row = {"distribution": name, "path": str(source), "bytes": source.stat().st_size, "sha256": observed,
                       "record_sha256": expected, "state": "MATCH" if expected == observed else "NO_RECORD_HASH" if expected is None else "MODIFIED"}
                env["record_checks"].append(row)
                if row["state"] == "MODIFIED":
                    result["preserved_files"].append(preserve(source, "installed-modifications"))
        conda = prefix / "conda-meta"
        if conda.is_dir():
            env["conda_packages"] = []
            for source in sorted(conda.glob("*.json")):
                raw = json.loads(source.read_text())
                env["conda_packages"].append({k: raw.get(k) for k in ("name", "version", "build", "channel", "subdir", "url", "sha256")})
                if raw.get("name") in {"python", "gcc", "gxx", "cuda", "cudatoolkit", "libstdcxx", "libgcc"}:
                    result["preserved_files"].append(preserve(source, "conda-metadata"))
        result["environments"].append(env)
    claims = json.loads((PHASE / "LINUX_HASH_CLAIMS.json").read_text(encoding="utf-8"))
    for raw in claims:
        source = Path(raw["recorded_path"])
        row = dict(raw)
        if source.is_file():
            row.update(observed_sha256=sha(source), bytes=source.stat().st_size, resolved=str(source.resolve()))
            row["a4_state"] = "EXACT_MATCH" if row["observed_sha256"] == raw["sha256"].lower() else "DIFFERENT_BYTES"
        else:
            row["a4_state"] = "MISSING_OR_UNREADABLE"
        result["claims"].append(row)
    # Preserve each observed historical environment claim, including shared-library bytes.
    for source in sorted({Path(r["recorded_path"]) for r in claims}):
        if source.is_file():
            result["preserved_files"].append(preserve(source, "historical-claims"))
    candidates = {Path("/tmp/pytorch3d-build"), Path("/root/pytorch3d"), Path("/tmp/Muon"), Path("/root/Muon")}
    for env in result["environments"]:
        for dist in env["packages"]:
            url = dist.get("direct_url", {}).get("url", "")
            if url.startswith("file://") and dist["name"].lower() in {"pytorch3d", "muon"}:
                from urllib.parse import unquote
                candidates.add(Path(unquote(url[7:])))
    allowed_suffixes = {".py", ".c", ".cpp", ".cu", ".cuh", ".h", ".hpp", ".cmake", ".toml", ".txt", ".json", ".yaml", ".yml", ".cfg", ".in", ".md", ".ninja"}
    for directory in sorted(candidates):
        if not directory.is_dir():
            continue
        row = {"path": str(directory), "git": [], "copies": [], "excluded": [], "total_source_bytes": 0}
        if (directory / ".git").exists():
            for args in (["rev-parse", "HEAD"], ["status", "--porcelain=v1", "--untracked-files=all"], ["diff", "--no-ext-diff", "--binary", "HEAD"]):
                row["git"].append(command(["git", "--no-optional-locks", "-C", str(directory), *args]))
        for parent, dirs, names in os.walk(directory, followlinks=False):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache", "node_modules", "dist", ".eggs"} and not (Path(parent) / d).is_symlink()]
            for name in names:
                source = Path(parent) / name
                if source.is_symlink() or not source.is_file():
                    continue
                if source.suffix not in allowed_suffixes and name not in {"LICENSE", "CMakeLists.txt"}:
                    row["excluded"].append({"path": str(source), "bytes": source.stat().st_size})
                    continue
                size = source.stat().st_size
                if size > 8 * 1024 * 1024 or row["total_source_bytes"] + size > 100 * 1024 * 1024:
                    row["excluded"].append({"path": str(source), "bytes": size, "reason": "bounded_source_capture"})
                    continue
                row["copies"].append(preserve(source, "source-trees"))
                row["total_source_bytes"] += size
        result["source_trees"].append(row)
    status = Path("/var/lib/dpkg/status")
    if status.is_file():
        system = []
        for block in status.read_text(errors="replace").split("\n\n"):
            fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line and not line.startswith(" "))
            name = fields.get("Package", "")
            if name.startswith(("ros-jazzy-", "cuda-", "libnvidia-", "libstdc++", "libgcc", "libgl", "libegl", "libgomp")) or name in {"gcc", "g++", "cmake", "ninja-build", "build-essential", "libc6"}:
                system.append({k: fields.get(k) for k in ("Package", "Version", "Architecture", "Status")})
        result["system_packages_selected"] = system
    result["processes_after"] = processes()
    assert not any(name in sys.modules for name in ("torch", "numpy", "hydra", "lightning", "open3d"))
    result["collector_finished_utc"] = datetime.now(timezone.utc).isoformat()
    save(PHASE / "LINUX_OBSERVATION.json", result)
    print(json.dumps({"environments": len(result["environments"]), "claim_occurrences": len(result["claims"]),
                      "source_trees": len(result["source_trees"]), "preserved_files": len(result["preserved_files"]),
                      "model_imports_or_training": False}))


if __name__ == "__main__":
    main()
