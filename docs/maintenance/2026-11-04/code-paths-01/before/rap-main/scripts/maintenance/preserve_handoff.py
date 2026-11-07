"""Preserve legacy research products without modifying their source files.

Run under WSL Python. Planning is read-only; --execute creates an exclusive
snapshot, hashes both copies, and verifies source stability before completion.
Raw point clouds are excluded; all experiment outputs and weights are included.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone


RAP = Path(__file__).resolve().parents[2]
SLAM = RAP.parent / "RAP-SLAM"
REPORT = RAP.parent / "RAP-SLAM-report"
AUDIT = Path("/mnt/c/Users/AAA/.codex/visualizations/2026/09/09/"
             "01a08509-8142-73b3-849e-4b335531d9eb")
META_EXT = {".txt", ".json", ".yaml", ".yml", ".csv", ".md", ".xml",
            ".pkl", ".pickle", ".joblib", ".npz", ".npy", ".toml"}


def git(root, *args):
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), *args],
        text=True).strip()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def collect():
    selected = {}
    def add(p, label, root):
        if p.is_symlink():
            raise RuntimeError(f"Explicit symlink handling required: {p}")
        if p.is_file():
            selected[f"{label}/{p.relative_to(root).as_posix()}"] = p
    for root in (RAP, SLAM):
        for rel in git(root, "ls-files").splitlines():
            p = root / rel
            if not p.is_file():
                raise FileNotFoundError(p)
            add(p, root.name, root)
    for p in SLAM.glob("output*"):
        for f in (p.rglob("*") if p.is_dir() else [p]):
            add(f, SLAM.name, SLAM)
    for p in SLAM.glob("*.log"):
        add(p, SLAM.name, SLAM)
    for root, label in ((RAP / "weights", "weights"),
                        (REPORT, REPORT.name), (AUDIT, "original-audit")):
        if not root.is_dir():
            raise FileNotFoundError(root)
        for p in root.rglob("*"):
            add(p, label, root)
    for root, label in ((SLAM / "data", "SLAM-data-metadata"),
                        (RAP.parent / "Datasets", "Datasets-metadata")):
        for p in root.rglob("*"):
            if p.suffix.lower() in META_EXT:
                add(p, label, root)
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--snapshot", default="2026-09-09-m0")
    args = ap.parse_args()
    if Path(args.snapshot).name != args.snapshot or args.snapshot in (".", ".."):
        ap.error("snapshot must be a single directory name")
    selected = collect()
    total = sum(p.stat().st_size for p in selected.values())
    summary = {"files": len(selected), "bytes": total,
               "free_bytes": shutil.disk_usage(RAP).free,
               "scope": "all output* products, root logs, weights, reports, tracked code, audit, dataset metadata",
               "excluded": "raw point clouds, raw download archives, full Git object stores, installed environments",
               "storage_limitation": "same-volume preservation; not a disaster-recovery backup"}
    print(json.dumps(summary), flush=True)
    if not args.execute:
        return
    if total + 2_000_000_000 > summary["free_bytes"]:
        raise RuntimeError("Insufficient free space including reserve")
    dest = RAP / ".maintenance-archive" / args.snapshot
    dest.mkdir(parents=True, exist_ok=False)
    (dest / "INCOMPLETE").write_text("Do not treat as a verified snapshot.\n")
    records = []
    for i, (rel, src) in enumerate(sorted(selected.items())):
        before = src.stat()
        source_hash = sha(src)
        dst = dest / "files" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied_hash = sha(dst)
        after = src.stat()
        if source_hash != copied_hash or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"Unstable or mismatched copy: {src}")
        records.append({"source": str(src), "archived_path": f"files/{rel}",
                        "bytes": before.st_size, "sha256": source_hash,
                        "source_mtime_ns": before.st_mtime_ns})
        if (i + 1) % 200 == 0:
            print(f"Copied and hash-verified {i + 1}/{len(selected)}", flush=True)
    # Detect files added/removed or changed during the snapshot, not just per copy.
    if set(collect()) != set(selected):
        raise RuntimeError("Source inventory changed during snapshot")
    for rec in records:
        p = Path(rec["source"])
        if p.stat().st_mtime_ns != rec["source_mtime_ns"] or sha(p) != rec["sha256"]:
            raise RuntimeError(f"Source changed during snapshot: {p}")
    for root in (RAP, SLAM):
        summary[root.name] = {"head": git(root, "rev-parse", "HEAD"),
                              "working_tree": git(root, "status", "--short")}
    summary["completed_utc"] = datetime.now(timezone.utc).isoformat()
    summary["verified_files"] = len(records)
    summary["manifest_sha256"] = None
    manifest = dest / "manifest.json"
    manifest.write_text(json.dumps(records, indent=2) + "\n")
    summary["manifest_sha256"] = sha(manifest)
    (dest / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    # Exercise actual archived content without writing to the original products.
    loops = json.loads((dest / "files/RAP-SLAM/output_prods/poss/accepted_loops.json").read_text())
    assert len(loops) == 4 and all("T_rel" in e for e in loops)
    (dest / "INCOMPLETE").unlink()
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
