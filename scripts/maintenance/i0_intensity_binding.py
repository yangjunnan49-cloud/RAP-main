"""I0 frozen GT-free KITTI intensity-to-F2-anchor binding preflight."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / "RAP-SLAM"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
BASE = MAIN / "docs/maintenance/2026-09-29/i0-intensity-binding-01"


def rd(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save(p, x):
    with p.open("x", encoding="utf-8") as f:
        json.dump(x, f, indent=2, allow_nan=False)
        f.write("\n")


def cohort():
    return {seq: rd(F2 / f"inputs_{seq}.json")[:4] for seq in ("00", "08")}


def frozen_files():
    out = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
           MAIN / "scripts/maintenance/validate_i0_intensity_binding.py",
           SLAM / "rap_slam/real_dataset.py"]
    for seq, pairs in cohort().items():
        out.append(F2 / f"inputs_{seq}.json")
        assert len(pairs) == 4
        for row in pairs:
            out.append(F2 / seq / row["key"] / "inputs.npz")
            for idx in (0, 3):
                scan = row["scans"][idx]
                p = Path(scan["path"])
                assert sha(p) == scan["sha256"] and p.stat().st_size == scan["bytes"]
                out.append(p)
    return out


def freeze():
    assert not (BASE / "freeze.json").exists()
    paths = frozen_files()
    assert len(paths) == len(set(paths)), "Repeated raw scan in fixed cohort"
    save(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
                                    "files": {str(p): sha(p) for p in paths}})


def verify():
    for name, h in rd(BASE / "freeze.json")["files"].items():
        assert sha(Path(name)) == h, name


def run():
    verify()
    sys.path.insert(0, str(SLAM))
    from rap_slam.real_dataset import kitti_vertical_correction
    start = time.monotonic()
    rows = []
    for seq, pairs in cohort().items():
        for pair in pairs:
            with np.load(F2 / seq / pair["key"] / "inputs.npz", allow_pickle=False) as v:
                counts = v["counts"].tolist()
                pts = v["points"]
            assert counts == [2000, 1000, 1000, 2000, 1000, 1000]
            for role, scan_index, lo in (("target", 0, 0), ("source", 3, 4000)):
                raw = np.fromfile(pair["scans"][scan_index]["path"], dtype=np.float32).reshape(-1, 4)
                assert np.isfinite(raw).all()
                raw = raw[np.linalg.norm(raw[:, :3], axis=1) >= 1.5]
                xyz = np.ascontiguousarray(kitti_vertical_correction(raw[:, :3]), dtype=np.float32)
                dist, nearest = cKDTree(xyz).query(pts[lo:lo+2000], k=1, workers=1)
                intensity = raw[nearest, 3]
                assert np.isfinite(dist).all() and np.isfinite(intensity).all()
                rows.append({"pair": pair["key"], "role": role,
                             "scan": pair["scans"][scan_index]["source_id"],
                             "raw_after_range": int(len(raw)), "anchor_count": 2000,
                             "nearest_median_m": float(np.median(dist)),
                             "nearest_p95_m": float(np.percentile(dist, 95)),
                             "within_0p5_fraction": float(np.mean(dist <= 0.5)),
                             "intensity_min": float(np.min(intensity)),
                             "intensity_max": float(np.max(intensity)),
                             "intensity_distinct": int(len(np.unique(intensity)))})
    assert len(rows) == 16
    save(BASE / "bank.json", rows)
    save(BASE / "bank_seal.json", {"sha256": sha(BASE / "bank.json"),
                                   "rows": len(rows), "gt_parsed": False,
                                   "wall_s": time.monotonic()-start})
    passed = all(r["within_0p5_fraction"] >= .95 and r["intensity_distinct"] >= 8 for r in rows)
    save(BASE / "summary.json", {"decision": "PASS_INTENSITY_BINDING_PREFLIGHT" if passed else "NO_INTENSITY_BINDING_FEASIBILITY",
                                      "scans": len(rows),
                                      "minimum_within_0p5_fraction": min(r["within_0p5_fraction"] for r in rows),
                                      "maximum_nearest_p95_m": max(r["nearest_p95_m"] for r in rows),
                                      "minimum_intensity_distinct": min(r["intensity_distinct"] for r in rows)})
    print(rd(BASE / "summary.json"))


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
