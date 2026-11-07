"""Independent I0 source/summary crosscheck, with no evaluator or GT reads."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
F2 = ROOT / "docs/maintenance/2026-09-27/f2-structured-dev-01"
OUT = ROOT / "docs/maintenance/2026-09-29/i0-intensity-binding-01"


def rd(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def main():
    checks = 0
    frozen = rd(OUT / "freeze.json")
    for p, h in frozen["files"].items():
        assert digest(Path(p)) == h
        checks += 1
    bank = rd(OUT / "bank.json")
    assert digest(OUT / "bank.json") == rd(OUT / "bank_seal.json")["sha256"]
    assert len(bank) == 16
    checks += 2
    sys.path.insert(0, str(ROOT.parent / "RAP-SLAM"))
    from rap_slam.real_dataset import kitti_vertical_correction
    summaries = []
    for seq in ("00", "08"):
        pairs = rd(F2 / f"inputs_{seq}.json")[:4]
        for pair in pairs:
            with np.load(F2 / seq / pair["key"] / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
            for role, part, start in (("target", 0, 0), ("source", 3, 4000)):
                result = next(x for x in bank if x["pair"] == pair["key"] and x["role"] == role)
                assert result["scan"] == pair["scans"][part]["source_id"]
                raw = np.fromfile(pair["scans"][part]["path"], dtype="<f4").reshape((-1, 4))
                assert digest(Path(pair["scans"][part]["path"])) == pair["scans"][part]["sha256"]
                keep = np.linalg.norm(raw[:, :3], axis=1) >= 1.5
                kept = raw[keep]
                xyz = kitti_vertical_correction(kept[:, :3]).astype(np.float32)
                distances, indices = cKDTree(xyz).query(points[start:start+2000])
                assigned = kept[indices, 3]
                assert result["raw_after_range"] == len(kept)
                assert abs(result["nearest_median_m"]-np.median(distances)) < 1e-7
                assert abs(result["nearest_p95_m"]-np.percentile(distances, 95)) < 1e-7
                assert abs(result["within_0p5_fraction"]-np.mean(distances <= .5)) < 1e-12
                assert result["intensity_distinct"] == len(np.unique(assigned))
                assert result["intensity_min"] == np.min(assigned)
                assert result["intensity_max"] == np.max(assigned)
                summaries.append(result)
                checks += 8
    assert len(summaries) == 16
    s = rd(OUT / "summary.json")
    passed = all(x["within_0p5_fraction"] >= .95 and x["intensity_distinct"] >= 8 for x in summaries)
    assert s["decision"] == ("PASS_INTENSITY_BINDING_PREFLIGHT" if passed else "NO_INTENSITY_BINDING_FEASIBILITY")
    assert abs(s["minimum_within_0p5_fraction"]-min(x["within_0p5_fraction"] for x in summaries)) < 1e-12
    assert abs(s["maximum_nearest_p95_m"]-max(x["nearest_p95_m"] for x in summaries)) < 1e-12
    assert s["minimum_intensity_distinct"] == min(x["intensity_distinct"] for x in summaries)
    checks += 5
    with (OUT / "validation.json").open("x", encoding="utf-8") as f:
        json.dump({"passed": True, "checks": checks, "bank_sha256": digest(OUT / "bank.json")}, f, indent=2)
        f.write("\n")
    print("I0 independent validation", checks, "checks")


if __name__ == "__main__":
    main()
