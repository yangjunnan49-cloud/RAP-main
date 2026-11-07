"""I1 fixed GT-blind intensity bank, followed by evaluator-only audit."""
from __future__ import annotations

import hashlib
import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
SLAM = ROOT.parent / "RAP-SLAM"
F2 = ROOT / "docs/maintenance/2026-09-27/f2-structured-dev-01"
C1 = ROOT / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
BASE = ROOT / "docs/maintenance/2026-09-29/i1-intensity-information-01"
GT = {"00": ROOT / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": ROOT / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}


def rd(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p, obj):
    with p.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def inputs(seq):
    return rd(F2 / f"inputs_{seq}.json")


def identities():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             ROOT / "scripts/maintenance/validate_i1_intensity_information.py",
             SLAM / "rap_slam/real_dataset.py", C1 / "pairs.json", C1 / "validation.json"]
    for seq in ("00", "08"):
        files += [F2 / f"inputs_{seq}.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        rows = inputs(seq)
        assert len(rows) == 100
        for row in rows:
            files.append(F2 / seq / row["key"] / "inputs.npz")
            for idx in (0, 3):
                scan = row["scans"][idx]
                p = Path(scan["path"])
                assert p.stat().st_size == scan["bytes"] and sha(p) == scan["sha256"]
                files.append(p)
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert rd(C1 / "validation.json")["passed"]
    files = identities()
    save(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
                                    "files": {str(p): sha(p) for p in files}})
    print("I1 frozen", len(files), "identities", flush=True)


def verify():
    for name, expected in rd(BASE / "freeze.json")["files"].items():
        assert sha(Path(name)) == expected, name


def assign(raw_path, anchors, correct):
    raw = np.fromfile(raw_path, dtype=np.float32).reshape(-1, 4)
    assert np.isfinite(raw).all() and len(raw) > 200
    raw = raw[np.linalg.norm(raw[:, :3], axis=1) >= 1.5]
    xyz = np.ascontiguousarray(correct(raw[:, :3]), dtype=np.float32)
    d, ix = cKDTree(xyz).query(anchors, k=1, workers=1)
    assigned = np.ascontiguousarray(raw[ix, 3], dtype=np.float32)
    assert np.isfinite(d).all() and np.isfinite(assigned).all()
    return assigned, d


def bank():
    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    sys.path.insert(0, str(SLAM))
    from rap_slam.real_dataset import kitti_vertical_correction
    assert not (BASE / "INCOMPLETE").exists() and not (BASE / "bank_seal.json").exists()
    (BASE / "INCOMPLETE").write_text("I1 intensity bank in progress\n", encoding="utf-8")
    start = time.monotonic()
    rows = []
    for seq in ("00", "08"):
        folder = BASE / seq
        folder.mkdir(exist_ok=False)
        for pos, row in enumerate(inputs(seq)):
            pair = row["key"]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
                counts = z["counts"].tolist()
            assert counts == [2000, 1000, 1000, 2000, 1000, 1000]
            anchor = (points[:2000], points[4000:6000])
            results = []
            for idx, p in zip((0, 3), anchor):
                raw = row["scans"][idx]
                path = Path(raw["path"])
                assert sha(path) == raw["sha256"] and path.stat().st_size == raw["bytes"]
                results.append(assign(path, p, kitti_vertical_correction))
            intensities = np.stack([results[0][0], results[1][0]])
            distances = np.stack([results[0][1], results[1][1]])
            out = folder / f"{pair}.npz"
            np.savez_compressed(out, intensities=intensities, distances=distances)
            rows.append({"pair": pair, "file": str(out), "sha256": sha(out),
                         "within_0p5": [float(np.mean(x <= .5)) for x in distances],
                         "distinct": [int(len(np.unique(x))) for x in intensities],
                         "p95_m": [float(np.percentile(x, 95)) for x in distances]})
            assert time.monotonic()-start < 600
            if (pos+1) % 25 == 0:
                print("I1 bank", seq, pos+1, flush=True)
    assert len(rows) == 200
    save(BASE / "bank.json", rows)
    artifact_bytes = sum(Path(r["file"]).stat().st_size for r in rows) + (BASE / "bank.json").stat().st_size
    seal = {"sha256": sha(BASE / "bank.json"), "rows": len(rows),
            "wall_s": time.monotonic()-start,
            "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
            "artifact_bytes": artifact_bytes, "gt_parsed": False}
    assert seal["wall_s"] <= 600 and seal["peak_rss_gib"] <= 2 and artifact_bytes <= 100_000_000
    save(BASE / "bank_seal.json", seal)
    print("I1 bank sealed", seal, flush=True)


def metric(points, intensity, truth, pair):
    target, source = points[:2000].astype(np.float64), points[4000:6000].astype(np.float64)
    moved = source @ truth[:3, :3].T + truth[:3, 3]
    distance, nearest = cKDTree(target).query(moved, k=1, workers=1)
    eligible = distance <= 1.0
    n = int(np.count_nonzero(eligible))
    if not n:
        return {"eligible_points": 0, "eligible_fraction": 0.0,
                "true_difference": None, "control_differences": [None]*16,
                "control_mean_difference": None, "advantage": None}
    t, s = intensity
    true = float(np.mean(np.abs(s[eligible].astype(np.float64)-t[nearest[eligible]].astype(np.float64))))
    ranges = np.linalg.norm(target, axis=1)
    bins = np.searchsorted(np.array([20., 40., 60., 80.]), ranges, side="right")
    controls = []
    for k in range(16):
        seed = int(hashlib.sha256(f"I1|{pair}|{k}".encode()).hexdigest()[:16], 16)
        rng = np.random.Generator(np.random.PCG64(seed))
        perm = np.arange(2000)
        for b in range(5):
            ids = np.flatnonzero(bins == b)
            perm[ids] = rng.permutation(ids)
        controls.append(float(np.mean(np.abs(s[eligible].astype(np.float64)-t[perm[nearest[eligible]]].astype(np.float64)))))
    mean_control = float(np.mean(controls))
    return {"eligible_points": n, "eligible_fraction": n/2000,
            "true_difference": true, "control_differences": controls,
            "control_mean_difference": mean_control, "advantage": mean_control-true}


def summarize(rows):
    adequate = [r for r in rows if r["eligible_fraction"] >= .1]
    vals = [r["advantage"] for r in adequate]
    return {"pairs": len(rows), "adequate_pairs": len(adequate),
            "median_advantage": float(np.median(vals)) if vals else None,
            "mean_advantage": float(np.mean(vals)) if vals else None,
            "positive_advantage_pairs": sum(v > 0 for v in vals),
            "median_true_difference": float(np.median([r["true_difference"] for r in adequate])) if vals else None,
            "median_control_difference": float(np.median([r["control_mean_difference"] for r in adequate])) if vals else None}


def evaluate():
    verify()
    assert (BASE / "INCOMPLETE").exists()
    manifest = rd(BASE / "bank.json")
    assert sha(BASE / "bank.json") == rd(BASE / "bank_seal.json")["sha256"] and len(manifest) == 200
    assert all(sha(Path(r["file"])) == r["sha256"] for r in manifest)
    c1 = {r["pair"]: r for r in rd(C1 / "pairs.json")}
    results = []
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        bypair = {r["key"]: r for r in inputs(seq)}
        for entry in (r for r in manifest if r["pair"].startswith(seq+"_")):
            pair = entry["pair"]
            row = bypair[pair]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
            with np.load(entry["file"], allow_pickle=False) as z:
                intensity = z["intensities"]
            truth = np.linalg.inv(gt[row["source_i"]]) @ gt[row["source_j"]]
            m = metric(points, intensity, truth, pair)
            assert m["eligible_points"] == c1[pair]["eligible_points"]
            results.append({"pair": pair, "sequence": seq, "stratum": c1[pair]["stratum"],
                            "native_candidate_available": c1[pair]["native_candidate_available"], **m})
    save(BASE / "pairs.json", results)
    binding = all(min(r["within_0p5"]) >= .95 and min(r["distinct"]) >= 8 for r in manifest)
    primary = [r for r in results if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_candidate_available"] and r["eligible_fraction"] >= .1]
    assert len([r for r in results if r["sequence"] == "08" and r["stratum"] != "confuser" and not r["native_candidate_available"]]) == 41
    p = summarize(primary)
    if not binding:
        decision = "INCONCLUSIVE_INTENSITY_BINDING"
    elif p["pairs"] < 20:
        decision = "INCONCLUSIVE_CORRESPONDENCE_SUPPORT"
    elif p["median_advantage"] >= .03 and p["positive_advantage_pairs"]*3 >= p["pairs"]*2:
        decision = "INTENSITY_INFORMATION_SIGNAL"
    else:
        decision = "NO_INTENSITY_INFORMATION_SIGNAL"
    groups = {}
    for seq in ("00", "08"):
        for avail in (False, True):
            subset = [r for r in results if r["sequence"] == seq and r["stratum"] != "confuser"
                      and r["native_candidate_available"] == avail]
            groups[f"{seq}_{'available' if avail else 'unavailable'}"] = summarize(subset)
    summary = {"decision": decision, "binding_adequate": binding, "primary": p,
               "groups": groups, "bank_sha256": sha(BASE / "bank.json")}
    save(BASE / "summary.json", summary)
    print(summary, flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
