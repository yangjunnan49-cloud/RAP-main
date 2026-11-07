"""Frozen V0 sensor-ray score and same-grid NN comparator."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fullscan_global_baseline as g1
import global_proposal_baseline as g0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
BASE = MAIN / "docs/maintenance/2026-09-28/v0-ray-visibility-01"
GRID = list(itertools.product((-1., 0., 1.), repeat=3))
ANGLE_CHORD = 2 * np.sin(np.deg2rad(.4) / 2)


def query_indices(seq: str, frame: int, n: int) -> np.ndarray:
    seed = int(hashlib.sha256(f"V0|ray-query|{seq}|{frame}".encode()).hexdigest()[:8], 16)
    assert n >= 4096
    return np.random.default_rng(seed).choice(n, 4096, replace=False)


def cloud(points: np.ndarray) -> dict:
    p = np.asarray(points, dtype=np.float64)
    ranges = np.linalg.norm(p, axis=1)
    assert np.isfinite(p).all() and np.min(ranges) >= 1.499
    unit = p / ranges[:, None]
    return {"points": p, "ranges": ranges, "unit": unit,
            "ray_tree": cKDTree(unit), "point_tree": cKDTree(p)}


def classify(query_points: np.ndarray, reference: dict) -> tuple[int, int, int, int]:
    q = np.asarray(query_points, dtype=np.float64)
    ranges = np.linalg.norm(q, axis=1)
    assert np.all(ranges > 0)
    chord, index = reference["ray_tree"].query(q / ranges[:, None], k=1, workers=1)
    seen = chord <= ANGLE_CHORD
    difference = ranges - reference["ranges"][index]
    agree = int(np.sum(seen & (np.abs(difference) <= .75)))
    free = int(np.sum(seen & (difference < -.75)))
    occluded = int(np.sum(seen & (difference > .75)))
    unknown = int(np.sum(~seen))
    assert agree + free + occluded + unknown == len(q)
    return agree, free, occluded, unknown


def score_pair(target: dict, source: dict, ti: np.ndarray, si: np.ndarray, pose: np.ndarray, delta: tuple) -> dict:
    r, t = pose[:3, :3], pose[:3, 3]
    src_in_tgt = si @ r.T + t
    tgt_in_src = (ti - t) @ r
    a = classify(src_in_tgt, target)
    b = classify(tgt_in_src, source)
    counts = np.asarray(a) + np.asarray(b)
    coverage = float(1 - counts[3] / 8192)
    penalty = .02 * float(np.dot(delta, delta))
    visibility = float((counts[1] - counts[0] + .25 * counts[3]) / 8192 + penalty)
    ds = target["point_tree"].query(src_in_tgt, k=1, workers=1)[0]
    dt = source["point_tree"].query(tgt_in_src, k=1, workers=1)[0]
    nn = float((np.minimum(ds, 5).sum() + np.minimum(dt, 5).sum()) / 8192 + penalty)
    return {"delta_m": list(delta), "agree": int(counts[0]), "free": int(counts[1]),
            "occluded": int(counts[2]), "unobserved": int(counts[3]),
            "coverage": coverage, "visibility_score": visibility, "nn_score": nn}


def winner(candidates: list[dict], kind: str) -> int:
    usable = [i for i, x in enumerate(candidates) if x["coverage"] >= .10] if kind == "visibility_score" else list(range(27))
    if not usable:
        return GRID.index((0., 0., 0.))
    return min(usable, key=lambda i: (candidates[i][kind],
        sum(x * x for x in GRID[i]), GRID[i]))


def synthetic() -> None:
    # No real data or GT. Verify all four ray categories and score direction.
    ref = cloud(np.array([[2., 0, 0], [0, 3., 0], [0, 0, 4.]], dtype=np.float32))
    assert classify(np.array([[2., 0, 0]]), ref) == (1, 0, 0, 0)
    assert classify(np.array([[1., 0, 0]]), ref) == (0, 1, 0, 0)
    assert classify(np.array([[4., 0, 0]]), ref) == (0, 0, 1, 0)
    assert classify(np.array([[-2., 0, 0]]), ref) == (0, 0, 0, 1)
    p = np.stack([np.cos(np.linspace(0, 2*np.pi, 4096, endpoint=False))*10,
                  np.sin(np.linspace(0, 2*np.pi, 4096, endpoint=False))*10,
                  np.linspace(-2, 2, 4096)], axis=1)
    shift = np.array([1.2, -.5, .3])
    source = cloud(p - shift)
    target = cloud(p)
    good = np.eye(4); good[:3, 3] = shift
    bad = good.copy(); bad[0, 3] += 1
    g = score_pair(target, source, target["points"], source["points"], good, (0.,0.,0.))
    b = score_pair(target, source, target["points"], source["points"], bad, (0.,0.,0.))
    assert g["agree"] == 8192 and g["free"] == 0 and g["unobserved"] == 0
    assert g["visibility_score"] < b["visibility_score"]
    assert g["nn_score"] < b["nn_score"]
    print("V0 synthetic ray checks passed", flush=True)


def frozen_files() -> list[Path]:
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_v0_ray_visibility.py",
             MAIN / "scripts/maintenance/fullscan_global_baseline.py",
             MAIN / "scripts/maintenance/global_proposal_baseline.py",
             MAIN.parent / "RAP-SLAM/rap_slam/real_dataset.py",
             MAIN.parent / "RAP-SLAM/rap_slam/rap_backend.py",
             F2 / "decision.json", F2 / "validation.json",
             g1.BASE / "freeze.json"]
    for seq in ("00", "08"):
        files += [F2 / seq / "records.json", F2 / seq / "gates.json",
                  F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        files += [p for pair in g0.order(seq) for p in g1.pair_scans(seq, pair)]
    return list(dict.fromkeys(files))


def freeze() -> None:
    assert not (BASE / "freeze.json").exists()
    synthetic()
    assert g0.read(F2 / "validation.json")["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
        "numpy": np.__version__, "scipy": __import__("scipy").__version__,
        "open3d": __import__("open3d").__version__, "files": {str(p): g0.sha(p) for p in files}})
    print("V0 frozen", len(files), "files", flush=True)


def verify() -> None:
    for name, digest in g0.read(BASE / "freeze.json")["files"].items():
        assert g0.sha(Path(name)) == digest, name


def gate_backend():
    sys.path.insert(0, str(MAIN.parent / "RAP-SLAM"))
    from rap_slam.rap_backend import RAPBackend
    g = RAPBackend.__new__(RAPBackend)
    g.voxel_size = .4
    g.remove_outliers = True
    g.max_points_per_scan = 4000
    g.seed = 42
    g.feature_extractor = None
    return g


def run() -> None:
    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    synthetic()
    (BASE / "INCOMPLETE").write_text("V0 bank started\n", encoding="utf-8")
    g = gate_backend()
    start = time.monotonic()
    bank = []
    for seq in ("00", "08"):
        records = g0.read(F2 / seq / "records.json")
        gates = g0.read(F2 / seq / "gates.json")
        for idx, pair in enumerate(g0.order(seq)):
            t0 = time.monotonic()
            i, j = (int(x) for x in pair.split("_")[1:])
            tp, sp = g1.pair_scans(seq, pair)
            target_raw, source_raw = g1.load_scan(tp), g1.load_scan(sp)
            target, source = cloud(target_raw), cloud(source_raw)
            ti, si = target["points"][query_indices(seq, i, len(target_raw))], source["points"][query_indices(seq, j, len(source_raw))]
            choices = [r for r in records if r["pair"] == pair and r["arm"] == "N"]
            assert len(choices) == 4 and all(r["valid"] for r in choices)
            n = min(choices, key=lambda r: (r["rigidity_rmse_m"], r["generation"]))
            native = np.asarray(n["T"], dtype=np.float64)
            candidates = []
            for delta in GRID:
                pose = native.copy(); pose[:3, 3] += delta
                candidates.append(score_pair(target, source, ti, si, pose, delta))
            centre = GRID.index((0., 0., 0.))
            vis_idx = centre if candidates[centre]["coverage"] < .10 else winner(candidates, "visibility_score")
            nn_idx = winner(candidates, "nn_score")
            gate_t, gate_s = g.preprocess(target_raw)[0], g.preprocess(source_raw)[0]
            transforms = {}
            for name, k in (("N", centre), ("V", vis_idx), ("NN", nn_idx)):
                pose = native.copy(); pose[:3, 3] += GRID[k]
                overlap, mean_dist = g._alignment_metrics(gate_t, gate_s, pose, thresh=1.)
                transforms[name] = {"candidate_index": k, "T": pose.tolist(),
                    "overlap": float(overlap), "mean_dist": float(mean_dist),
                    "accepted": bool(overlap >= .7 and mean_dist <= 2.5)}
            old = gates[pair]["N"][str(n["generation"])]
            assert abs(transforms["N"]["overlap"] - old["overlap_ratio"]) <= 1e-5
            assert abs(transforms["N"]["mean_dist"] - old["mean_dist"]) <= 1e-5
            assert transforms["N"]["accepted"] == old["accepted"]
            bank.append({"sequence": seq, "pair": pair, "source_i": i, "source_j": j,
                "native_generation": n["generation"], "target_points": len(target_raw),
                "source_points": len(source_raw), "candidates": candidates,
                "transforms": transforms, "wall_s": time.monotonic() - t0})
            if (idx + 1) % 10 == 0:
                print("V0 bank", seq, idx + 1, "elapsed", round(time.monotonic() - start, 1), flush=True)
            assert time.monotonic() - start <= 1800
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2 <= 4
    g0.save_new(BASE / "bank.json", bank)
    g0.save_new(BASE / "bank_seal.json", {"sha256": g0.sha(BASE / "bank.json"),
        "utc": datetime.now(timezone.utc).isoformat(), "wall_s": time.monotonic() - start,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2})
    print("V0 bank sealed", flush=True)


def label(pose: np.ndarray, truth: np.ndarray) -> dict:
    error = np.linalg.inv(truth) @ pose
    r = error[:3, :3]
    sine = np.linalg.norm([r[2,1]-r[1,2], r[0,2]-r[2,0], r[1,0]-r[0,1]]) / 2
    rte = float(np.linalg.norm(error[:3, 3]))
    rre = float(np.degrees(np.arctan2(sine, np.clip((np.trace(r)-1)/2, -1, 1))))
    return {"RTE_m": rte, "RRE_deg": rre, "strict": bool(rte <= 1 and rre <= 5),
            "clipped_error": float(min(5, max(rte, rre/5)))}


def evaluate() -> None:
    verify()
    assert g0.sha(BASE / "bank.json") == g0.read(BASE / "bank_seal.json")["sha256"]
    bank = g0.read(BASE / "bank.json")
    outcomes = []
    for seq in ("00", "08"):
        old = g0.read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        rows = [r for r in bank if r["sequence"] == seq]
        assert len(rows) == len(old) == 100
        for row, parent in zip(rows, old):
            assert row["pair"] == f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            truth = np.linalg.inv(gt[row["source_i"]]) @ gt[row["source_j"]]
            methods = {}
            for name in ("N", "V", "NN"):
                gate = row["transforms"][name]
                result = label(np.asarray(gate["T"]), truth)
                result["accepted"] = gate["accepted"]
                result["correct_accepted"] = bool(gate["accepted"] and result["strict"])
                result["incorrect_accepted"] = bool(gate["accepted"] and not result["strict"])
                methods[name] = result
            assert abs(methods["N"]["RTE_m"] - parent["methods"]["N"]["RTE_m"]) < 1e-6
            assert abs(methods["N"]["RRE_deg"] - parent["methods"]["N"]["RRE_deg"]) < 1e-5
            assert methods["N"]["accepted"] == parent["methods"]["N"]["accepted"]
            outcomes.append({"sequence": seq, "pair": row["pair"], "stratum": parent["stratum"],
                "native_K4_unavailable": not parent["methods"]["N-OR4"]["strict"],
                "centre_coverage": row["candidates"][13]["coverage"], "methods": methods})
    g0.save_new(BASE / "outcomes.json", outcomes)
    summary = {"scope": "observed-development V0 sensor-ray information; no RAP inference", "sequences": {}}
    for seq in ("00", "08"):
        rows = [r for r in outcomes if r["sequence"] == seq]
        positives = [r for r in rows if r["stratum"] != "confuser"]
        methods = {}
        for name in ("N", "V", "NN"):
            methods[name] = {"strict": sum(r["methods"][name]["strict"] for r in positives),
                "correct_accepts": sum(r["methods"][name]["correct_accepted"] for r in positives),
                "incorrect_accepts": sum(r["methods"][name]["incorrect_accepted"] for r in rows),
                "confuser_accepts": sum(r["methods"][name]["accepted"] for r in rows if r["stratum"] == "confuser"),
                "clipped_error": float(np.mean([r["methods"][name]["clipped_error"] for r in positives])),
                "ordinary_strict": sum(r["methods"][name]["strict"] for r in positives if r["stratum"] == "ordinary")}
        gains = [r["pair"] for r in positives if r["methods"]["V"]["strict"] and not r["methods"]["N"]["strict"]]
        losses = [r["pair"] for r in positives if r["methods"]["N"]["strict"] and not r["methods"]["V"]["strict"]]
        newly_incorrect = [r["pair"] for r in rows if r["methods"]["V"]["incorrect_accepted"] and not r["methods"]["N"]["incorrect_accepted"]]
        lost_correct_accept = [r["pair"] for r in positives if r["methods"]["N"]["correct_accepted"] and not r["methods"]["V"]["correct_accepted"]]
        new_correct_accept = [r["pair"] for r in positives if r["methods"]["V"]["correct_accepted"] and not r["methods"]["N"]["correct_accepted"]]
        ordinary_losses = [r["pair"] for r in positives if r["stratum"] == "ordinary" and r["methods"]["N"]["strict"] and not r["methods"]["V"]["strict"]]
        recovered = [r["pair"] for r in positives if r["native_K4_unavailable"] and r["methods"]["V"]["strict"]]
        summary["sequences"][seq] = {"coverage_ge_0p10": sum(r["centre_coverage"] >= .10 for r in rows),
            "centre_coverage_median": float(np.median([r["centre_coverage"] for r in rows])),
            "methods": methods, "strict_gains": gains, "strict_losses": losses,
            "recovered_unavailable": recovered, "newly_incorrect_accepts": newly_incorrect,
            "new_correct_accepts": new_correct_accept, "lost_correct_accepts": lost_correct_accept,
            "ordinary_strict_losses": ordinary_losses}
    a, b = summary["sequences"]["08"], summary["sequences"]["00"]
    av, an, ann = (a["methods"][x] for x in ("V", "N", "NN"))
    bv, bn = (b["methods"][x] for x in ("V", "N"))
    conditions = {
        "coverage": a["coverage_ge_0p10"] >= 90 and b["coverage_ge_0p10"] >= 90,
        "08_recovery": len(a["recovered_unavailable"]) >= 5 and av["strict"] - an["strict"] >= 5,
        "08_accept_safety": av["correct_accepts"] - an["correct_accepts"] >= 2 and not a["newly_incorrect_accepts"],
        "00_accept_safety": len(b["lost_correct_accepts"]) <= 1 and not b["newly_incorrect_accepts"],
        "strict_regressions": bv["strict"] - bn["strict"] >= -2 and
            len(a["ordinary_strict_losses"]) <= 1 and len(b["ordinary_strict_losses"]) <= 1,
        "visibility_vs_nn": av["strict"] - ann["strict"] >= 3 and
            av["correct_accepts"] - ann["correct_accepts"] >= 1,
        "cost": g0.read(BASE / "bank_seal.json")["wall_s"] <= 1800 and
            g0.read(BASE / "bank_seal.json")["peak_rss_gib"] <= 4 and
            sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file()) <= 1024**3,
    }
    summary["conditions"] = conditions
    summary["decision"] = "RAY_INFORMATION_SIGNAL" if all(conditions.values()) else "NO_RAY_INFORMATION_SIGNAL"
    g0.save_new(BASE / "summary.json", summary)
    print(summary["decision"], conditions, flush=True)


if __name__ == "__main__":
    {"synthetic": synthetic, "freeze": freeze, "run": run, "evaluate": evaluate}[sys.argv[1]]()
