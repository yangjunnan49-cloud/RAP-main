"""Frozen C3 FPFH bank, then evaluator-only correspondence comparison."""

from __future__ import annotations

import hashlib
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import open3d as o3d
import scipy
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
C1 = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
BASE = MAIN / "docs/maintenance/2026-09-29/c3-fixed-fpfh-01"
NORMAL_RADIUS, NORMAL_MAX = 2.0, 30
FEATURE_RADIUS, FEATURE_MAX = 5.0, 100


def inputs():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_c3_fixed_fpfh.py",
             C1 / "bank_seal.json", C1 / "bank.json", C1 / "pairs.json",
             C1 / "summary.json", C1 / "validation.json",
             F2 / "freeze.json", F2 / "validation.json"]
    for seq in ("00", "08"):
        files += [F2 / seq / "records.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        files += [F2 / seq / pair / "inputs.npz" for pair in g0.order(seq)]
    assert len(files) == len(set(files))
    return files


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert g0.read(C1 / "validation.json")["passed"]
    assert g0.read(F2 / "validation.json")["passed"]
    assert o3d.__version__ == "0.19.0"
    files = inputs()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": {s: g0.order(s) for s in ("00", "08")},
        "files": {str(p): g0.sha(p) for p in files},
        "open3d": o3d.__version__, "numpy": np.__version__,
        "scipy": scipy.__version__, "python": sys.version,
        "normal_radius_m": NORMAL_RADIUS, "normal_max_nn": NORMAL_MAX,
        "feature_radius_m": FEATURE_RADIUS, "feature_max_nn": FEATURE_MAX,
    })
    print("C3 frozen", len(files), "identities", flush=True)


def verify():
    frozen = g0.read(BASE / "freeze.json")
    assert frozen["pairs"] == {s: g0.order(s) for s in ("00", "08")}
    assert frozen["open3d"] == o3d.__version__ == "0.19.0"
    assert (frozen["normal_radius_m"], frozen["normal_max_nn"],
            frozen["feature_radius_m"], frozen["feature_max_nn"]) == (2.0, 30, 5.0, 100)
    for path, digest in frozen["files"].items():
        assert g0.sha(Path(path)) == digest, path


def describe(points):
    assert points.shape == (2000, 3) and np.isfinite(points).all()
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=2.0, max_nn=30))
    cloud.orient_normals_towards_camera_location(np.zeros(3))
    features = o3d.pipelines.registration.compute_fpfh_feature(
        cloud, o3d.geometry.KDTreeSearchParamHybrid(radius=5.0, max_nn=100))
    result = np.asarray(features.data, dtype=np.float64).T.copy()
    assert result.shape == (2000, 33) and np.isfinite(result).all()
    return result


def synthetic():
    rng = np.random.default_rng(7)
    x = rng.uniform(-10, 10, (2000, 3))
    y = x.copy()
    ang = .3
    rotation = np.array([[np.cos(ang), -np.sin(ang), 0],
                         [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
    y = y @ rotation.T + [2.0, -1.0, .5]
    truth = np.eye(4)
    truth[:3, :3] = rotation.T
    truth[:3, 3] = -rotation.T @ [2.0, -1.0, .5]
    assert np.max(np.abs(y @ truth[:3, :3].T + truth[:3, 3] - x)) < 1e-12
    a, b = describe(x), describe(y)
    assert a.shape == b.shape == (2000, 33)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    print("C3 synthetic geometry/FPFH passed", flush=True)


def bank():
    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert not (BASE / "INCOMPLETE").exists() and not (BASE / "bank.json").exists()
    (BASE / "INCOMPLETE").write_text("C3 descriptor bank in progress\n", encoding="utf-8")
    started = time.monotonic()
    rows = []
    for seq in ("00", "08"):
        for ix, pair in enumerate(g0.order(seq)):
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
                assert points.shape == (8000, 3)
                assert z["counts"].tolist() == [2000, 1000, 1000, 2000, 1000, 1000]
            target = describe(points[:2000])
            source = describe(points[4000:6000])
            destination = BASE / seq / f"{pair}.npz"
            destination.parent.mkdir(parents=True, exist_ok=True)
            assert not destination.exists()
            np.savez_compressed(destination, target=target, source=source)
            tn = np.linalg.norm(target, axis=1)
            sn = np.linalg.norm(source, axis=1)
            rows.append({"sequence": seq, "pair": pair, "file": str(destination),
                         "sha256": g0.sha(destination),
                         "target_nonzero": int(np.count_nonzero(tn > 1e-12)),
                         "source_nonzero": int(np.count_nonzero(sn > 1e-12))})
            if (ix + 1) % 10 == 0:
                print("C3 bank", seq, ix + 1, "elapsed", round(time.monotonic()-started, 1), flush=True)
            assert time.monotonic() - started <= 1800
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2 <= 2
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 2 * 2**30
    g0.save_new(BASE / "bank.json", rows)
    g0.save_new(BASE / "bank_seal.json", {
        "bank_sha256": g0.sha(BASE / "bank.json"),
        "utc": datetime.now(timezone.utc).isoformat(),
        "wall_s": time.monotonic() - started,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz")),
    })
    print("C3 bank sealed", flush=True)


def permutation(pair, k):
    seed = int.from_bytes(hashlib.sha256(f"C1|{pair}|{k}".encode()).digest()[:8], "big")
    return np.random.default_rng(seed).permutation(2000)


def score(points, target_feature, source_feature, truth, pair):
    target = points[:2000].astype(np.float64)
    source = points[4000:6000].astype(np.float64)
    moved = source @ truth[:3, :3].T + truth[:3, 3]
    eligible = cKDTree(target).query(moved, k=1, workers=1)[0] <= 1.0
    target_norm = np.linalg.norm(target_feature, axis=1)
    source_norm = np.linalg.norm(source_feature, axis=1)
    valid_t, valid_s = target_norm > 1e-12, source_norm > 1e-12
    chosen = np.full(2000, -1, dtype=np.int64)
    if np.any(valid_t) and np.any(valid_s):
        ft = target_feature[valid_t] / target_norm[valid_t, None]
        fs = source_feature[valid_s] / source_norm[valid_s, None]
        chosen[valid_s] = np.flatnonzero(valid_t)[cKDTree(ft).query(fs, k=1, workers=1)[1]]
    correct = np.zeros(2000, dtype=bool)
    used = chosen >= 0
    correct[used] = np.linalg.norm(target[chosen[used]] - moved[used], axis=1) <= 1
    count = int(np.count_nonzero(eligible))
    controls = []
    for k in range(16):
        ok = np.zeros(2000, dtype=bool)
        mapped = permutation(pair, k)[chosen[used]]
        ok[used] = np.linalg.norm(target[mapped] - moved[used], axis=1) <= 1
        controls.append(float(np.mean(ok[eligible])) if count else None)
    true = float(np.mean(correct[eligible])) if count else None
    control = float(np.mean(controls)) if count else None
    return {"eligible_points": count, "eligible_fraction": count / 2000,
            "true_recall": true, "control_recalls": controls,
            "control_mean_recall": control, "paired_difference": true-control if count else None,
            "unconditional_correct_fraction": float(np.mean(correct))}


def summarize(rows):
    present = [r for r in rows if r["true_recall"] is not None]
    answer = {"pairs": len(rows), "eligible_pairs": len(present),
              "adequate_pairs": sum(r["eligible_fraction"] >= .1 for r in rows)}
    for key in ("eligible_fraction", "true_recall", "control_mean_recall",
                "paired_difference", "advantage_over_c1"):
        values = [r[key] for r in present]
        answer[key] = {"mean": float(np.mean(values)) if values else None,
                       "median": float(np.median(values)) if values else None}
    return answer


def evaluate():
    verify()
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["bank_sha256"]
    bank = g0.read(BASE / "bank.json")
    c1 = g0.read(C1 / "pairs.json")
    assert len(bank) == len(c1) == 200
    rows = []
    for seq in ("00", "08"):
        labels = g0.read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        for ix, label in enumerate(labels):
            n = ix + (100 if seq == "08" else 0)
            pair = f'{seq}_{label["source_i"]}_{label["source_j"]}'
            item, old = bank[n], c1[n]
            assert pair == item["pair"] == old["pair"]
            assert g0.sha(Path(item["file"])) == item["sha256"]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
            with np.load(item["file"], allow_pickle=False) as z:
                target, source = z["target"], z["source"]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            metric = score(points, target, source, truth, pair)
            assert metric["eligible_points"] == old["eligible_points"]
            assert label["stratum"] == old["stratum"]
            assert label["methods"]["N-OR4"]["strict"] == old["native_candidate_available"]
            rows.append({"sequence": seq, "pair": pair, "stratum": old["stratum"],
                         "native_candidate_available": old["native_candidate_available"],
                         "target_nonzero": item["target_nonzero"],
                         "source_nonzero": item["source_nonzero"],
                         "c1_paired_difference": old["paired_difference"],
                         "advantage_over_c1": metric["paired_difference"] - old["paired_difference"]
                         if metric["paired_difference"] is not None else None,
                         **metric})
    g0.save_new(BASE / "pairs.json", rows)
    groups = {}
    for seq in ("00", "08"):
        for available in (False, True):
            group = [r for r in rows if r["sequence"] == seq and r["stratum"] != "confuser"
                     and r["native_candidate_available"] == available]
            groups[f"{seq}_{'available' if available else 'unavailable'}"] = summarize(group)
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            groups[f"{seq}_{stratum}"] = summarize(
                [r for r in rows if r["sequence"] == seq and r["stratum"] == stratum])
    primary_all = [r for r in rows if r["sequence"] == "08" and r["stratum"] != "confuser"
                   and not r["native_candidate_available"] and r["eligible_fraction"] >= .1]
    assert len(primary_all) == 33
    primary = [r for r in primary_all if min(r["target_nonzero"], r["source_nonzero"]) >= 1900]
    median_info = float(np.median([r["paired_difference"] for r in primary])) if primary else None
    median_advantage = float(np.median([r["advantage_over_c1"] for r in primary])) if primary else None
    decision = ("INCONCLUSIVE_DESCRIPTOR_SUPPORT" if len(primary) < 20 else
                "MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE" if median_info >= .1 and
                median_advantage >= .05 else "NO_MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE")
    g0.save_new(BASE / "summary.json", {
        "decision": decision, "bank_sha256": seal["bank_sha256"],
        "primary_adequate_pairs": len(primary_all), "primary_supported_pairs": len(primary),
        "primary_fpfh_information_median": median_info,
        "primary_fpfh_over_c1_median": median_advantage, "groups": groups})
    print("C3 evaluator", decision, flush=True)


if __name__ == "__main__":
    {"synthetic": synthetic, "freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
