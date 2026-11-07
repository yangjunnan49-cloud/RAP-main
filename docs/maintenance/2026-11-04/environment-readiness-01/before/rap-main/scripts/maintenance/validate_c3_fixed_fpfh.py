"""Independent full-pair metric and fixed-spot descriptor validation for C3."""

from __future__ import annotations

import hashlib
import os
import sys
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


def close(a, b, tol=1e-11):
    if a is None or b is None:
        assert a is None and b is None
    else:
        assert abs(float(a)-float(b)) <= tol, (a, b)


def own_fpfh(x):
    p = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(x.astype(np.float64)))
    p.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(2.0, 30))
    p.orient_normals_towards_camera_location(np.zeros(3))
    f = o3d.pipelines.registration.compute_fpfh_feature(
        p, o3d.geometry.KDTreeSearchParamHybrid(5.0, 100))
    return np.array(f.data.T, dtype=np.float64, copy=True)


def own_score(points, ft, fs, truth, pair):
    target = np.asarray(points[:2000], dtype=np.float64)
    source = np.asarray(points[4000:6000], dtype=np.float64)
    moved = (truth[:3, :3] @ source.T).T + truth[:3, 3]
    support = cKDTree(target).query(moved, k=1)[0] <= 1
    nt, ns = np.linalg.norm(ft, axis=1), np.linalg.norm(fs, axis=1)
    good_t, good_s = nt > 1e-12, ns > 1e-12
    matches = np.full(2000, -1, dtype=int)
    if np.any(good_t) and np.any(good_s):
        zt = ft[good_t] / nt[good_t, None]
        zs = fs[good_s] / ns[good_s, None]
        matches[good_s] = np.flatnonzero(good_t)[cKDTree(zt).query(zs, k=1)[1]]
    valid = matches != -1
    success = np.zeros(2000, dtype=bool)
    success[valid] = np.sum((target[matches[valid]] - moved[valid])**2, axis=1) <= 1
    n = int(np.count_nonzero(support))
    controls = []
    for k in range(16):
        digest = hashlib.sha256(f"C1|{pair}|{k}".encode()).digest()
        permutation = np.random.Generator(np.random.PCG64(int.from_bytes(digest[:8], "big"))).permutation(2000)
        shuffled = np.zeros(2000, dtype=bool)
        shuffled[valid] = np.sum((target[permutation[matches[valid]]] - moved[valid])**2, axis=1) <= 1
        controls.append(float(np.count_nonzero(shuffled & support)/n) if n else None)
    true = float(np.count_nonzero(success & support)/n) if n else None
    control = float(sum(controls)/16) if n else None
    return {"eligible_points": n, "eligible_fraction": n/2000,
            "true_recall": true, "control_recalls": controls,
            "control_mean_recall": control, "paired_difference": true-control if n else None,
            "unconditional_correct_fraction": float(np.count_nonzero(success)/2000)}


def own_summary(rows):
    present = [r for r in rows if r["eligible_points"] > 0]
    result = {"pairs": len(rows), "eligible_pairs": len(present),
              "adequate_pairs": sum(r["eligible_fraction"] >= .1 for r in rows)}
    for key in ("eligible_fraction", "true_recall", "control_mean_recall",
                "paired_difference", "advantage_over_c1"):
        values = [r[key] for r in present]
        result[key] = {"mean": float(np.mean(values)) if values else None,
                       "median": float(np.median(values)) if values else None}
    return result


def validate():
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    frozen = g0.read(BASE / "freeze.json")
    assert frozen["open3d"] == o3d.__version__ == "0.19.0"
    assert frozen["numpy"] == np.__version__ and frozen["scipy"] == scipy.__version__
    checks = 0
    for path, digest in frozen["files"].items():
        assert g0.sha(Path(path)) == digest, path
        checks += 1
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["bank_sha256"]
    assert seal["wall_s"] <= 1800 and seal["peak_rss_gib"] <= 2
    assert seal["artifact_bytes"] <= 2 * 2**30
    bank = g0.read(BASE / "bank.json")
    output = g0.read(BASE / "pairs.json")
    c1 = g0.read(C1 / "pairs.json")
    assert len(bank) == len(output) == len(c1) == 200
    assert len({r["pair"] for r in bank}) == 200
    all_rows = []
    for seq in ("00", "08"):
        labels = g0.read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        for ix, label in enumerate(labels):
            n = ix + (100 if seq == "08" else 0)
            item, row, old = bank[n], output[n], c1[n]
            pair = f'{seq}_{label["source_i"]}_{label["source_j"]}'
            assert pair == item["pair"] == row["pair"] == old["pair"] == frozen["pairs"][seq][ix]
            assert g0.sha(Path(item["file"])) == item["sha256"]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
                assert points.shape == (8000, 3)
            with np.load(item["file"], allow_pickle=False) as z:
                ft, fs = z["target"], z["source"]
                assert ft.shape == fs.shape == (2000, 33)
                assert np.isfinite(ft).all() and np.isfinite(fs).all()
            assert item["target_nonzero"] == np.count_nonzero(np.linalg.norm(ft, axis=1) > 1e-12)
            assert item["source_nonzero"] == np.count_nonzero(np.linalg.norm(fs, axis=1) > 1e-12)
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            actual = own_score(points, ft, fs, truth, pair)
            for key, value in actual.items():
                if isinstance(value, list):
                    assert len(value) == len(row[key]) == 16
                    for a, b in zip(value, row[key]):
                        close(a, b)
                        checks += 1
                else:
                    close(value, row[key])
                    checks += 1
            assert row["stratum"] == old["stratum"] == label["stratum"]
            assert row["native_candidate_available"] == old["native_candidate_available"] == label["methods"]["N-OR4"]["strict"]
            assert row["eligible_points"] == old["eligible_points"]
            close(row["c1_paired_difference"], old["paired_difference"])
            close(row["advantage_over_c1"],
                  actual["paired_difference"]-old["paired_difference"] if old["paired_difference"] is not None else None)
            checks += 6
            if ix in (0, 25, 50, 75):
                assert np.array_equal(ft, own_fpfh(points[:2000]))
                assert np.array_equal(fs, own_fpfh(points[4000:6000]))
                checks += 2
            all_rows.append(row)
    summary = g0.read(BASE / "summary.json")
    assert summary["bank_sha256"] == seal["bank_sha256"]
    for group, reported in summary["groups"].items():
        seq, kind = group.split("_", 1)
        if kind in ("available", "unavailable"):
            selected = [r for r in all_rows if r["sequence"] == seq and r["stratum"] != "confuser"
                        and r["native_candidate_available"] == (kind == "available")]
        else:
            selected = [r for r in all_rows if r["sequence"] == seq and r["stratum"] == kind]
        expected = own_summary(selected)
        for key in ("pairs", "eligible_pairs", "adequate_pairs"):
            assert reported[key] == expected[key]
            checks += 1
        for key in ("eligible_fraction", "true_recall", "control_mean_recall",
                    "paired_difference", "advantage_over_c1"):
            close(reported[key]["mean"], expected[key]["mean"])
            close(reported[key]["median"], expected[key]["median"])
            checks += 2
    adequate = [r for r in all_rows if r["sequence"] == "08" and r["stratum"] != "confuser"
                and not r["native_candidate_available"] and r["eligible_fraction"] >= .1]
    supported = [r for r in adequate if min(r["target_nonzero"], r["source_nonzero"]) >= 1900]
    assert len(adequate) == summary["primary_adequate_pairs"] == 33
    assert len(supported) == summary["primary_supported_pairs"]
    a = float(np.median([r["paired_difference"] for r in supported])) if supported else None
    b = float(np.median([r["advantage_over_c1"] for r in supported])) if supported else None
    close(a, summary["primary_fpfh_information_median"])
    close(b, summary["primary_fpfh_over_c1_median"])
    decision = ("INCONCLUSIVE_DESCRIPTOR_SUPPORT" if len(supported) < 20 else
                "MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE" if a >= .1 and b >= .05 else
                "NO_MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE")
    assert decision == summary["decision"]
    assert not (BASE / "INCOMPLETE").exists()
    g0.save_new(BASE / "validation.json", {
        "passed": True, "checks": checks, "decision": decision,
        "bank_sha256": seal["bank_sha256"], "open3d": o3d.__version__,
        "numpy": np.__version__, "scipy": scipy.__version__})
    print("C3 independently validated", checks, "checks", decision, flush=True)


if __name__ == "__main__":
    validate()
