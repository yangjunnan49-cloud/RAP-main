#!/usr/bin/env python3
"""Inspect installed metadata with -I -S -B, without importing installed packages."""
import argparse
from datetime import datetime, timezone
import importlib.metadata as metadata
import json
from pathlib import Path
import sys


def inspect(site_paths):
    resolved = sorted({str(Path(path).expanduser().resolve()) for path in site_paths})
    packages = []
    for dist in metadata.distributions(path=resolved):
        direct = dist.read_text("direct_url.json")
        packages.append({"name": dist.metadata.get("Name"), "version": dist.version,
                         "metadata_path": str(getattr(dist, "_path", "")),
                         "requires_dist": dist.requires or [], "direct_url": json.loads(direct) if direct else None})
    return {"observed_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version, "executable": sys.executable,
            "site_paths": resolved, "packages": sorted(packages, key=lambda r: (r["name"] or "").lower()),
            "package_imports_performed": False, "model_loads": 0, "training_steps": 0}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site-path", action="append", required=True, help="Exact site-packages directory; repeat for multiple paths")
    p.add_argument("--output", type=Path, help="New JSON receipt; omit to print JSON")
    args = p.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        p.error("Run with python -I -S -B to avoid site initialization and bytecode writes")
    for path in args.site_path:
        if not Path(path).expanduser().is_dir():
            p.error("Missing site-packages directory: " + path)
    result = inspect(args.site_path)
    value = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(value)
    else:
        print(value, end="")


if __name__ == "__main__":
    main()
