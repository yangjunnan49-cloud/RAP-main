"""Capture installed versions without credentials, package URLs, or env vars."""
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/maintenance/2026-09-09/environment.json"


def command(args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise RuntimeError(f"Version query failed: {args[0]} ({p.returncode})")
    return p.stdout.strip()


def main():
    conda = json.loads(command(["/root/miniconda3/bin/conda", "list",
                              "--prefix", sys.prefix, "--json"]))
    system = json.loads(command(["/usr/bin/python3", "-B", "-c",
        "import importlib.metadata as m,json,sys; print(json.dumps({'python':sys.version,'packages':sorted([(d.metadata['Name'],d.version) for d in m.distributions()])}))"]))
    record = {"captured_utc": datetime.now(timezone.utc).isoformat(),
              "purpose": "Observed installed versions; not an independently tested environment lock",
              "python": sys.version, "executable": sys.executable,
              "platform": platform.platform(),
              "python_packages": sorted((d.metadata["Name"], d.version)
                                        for d in importlib.metadata.distributions()),
              "conda_packages": [{k: p.get(k) for k in ("name", "version", "build_string")}
                                 for p in conda],
              "system_python": system,
              "gpu": command(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                              "--format=csv,noheader"]),
              "ros_debian_packages": command(["dpkg-query", "-W", "-f=${Package}\t${Version}\n", "ros-jazzy-*"]).splitlines()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    print(json.dumps({"written": str(OUT), "python_packages": len(record["python_packages"]),
                      "conda_packages": len(conda), "system_python_packages": len(system["packages"])}))


if __name__ == "__main__":
    main()
