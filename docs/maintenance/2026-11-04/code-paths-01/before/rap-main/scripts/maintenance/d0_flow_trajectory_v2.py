"""Prospective CPU audit of saved native RAP flow checkpoints."""

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import fullscan_global_baseline as g1
import v0_ray_visibility as v0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
BASE = MAIN / "docs/maintenance/2026-09-28/d0-flow-trajectory-01"


def verify_amendment() -> None:
    for name, digest in g0.read(BASE / "amendment_freeze.json")["files"].items():
        assert g0.sha(Path(name)) == digest, name


def kabsch(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y = np.asarray(source, dtype=np.float64), np.asarray(target, dtype=np.float64)
    assert x.shape == y.shape and x.ndim == 2 and x.shape[1] == 3 and len(x) >= 3
    xm, ym = x.mean(axis=0), y.mean(axis=0)
    u, _, vt = np.linalg.svd((x - xm).T @ (y - ym))
    sign = 1.0 if np.linalg.det(vt.T @ u.T) >= 0 else -1.0
    r = vt.T @ np.diag([1., 1., sign]) @ u.T
    t = ym - xm @ r.T
    return r, t


def decode_one(cond: np.ndarray, raw: np.ndarray, counts: np.ndarray,
               centers: np.ndarray, scale: float) -> np.ndarray:
    cuts = np.r_[0, np.cumsum(counts)]
    parts = []
    for part in (0, 3):
        sl = slice(int(cuts[part]), int(cuts[part + 1]))
        r, t = kabsch(cond[sl], raw[sl])
        pose = np.eye(4)
        pose[:3, :3] = r
        pose[:3, 3] = scale * t - r @ centers[part]
        parts.append(pose)
    return np.linalg.inv(parts[0]) @ parts[1]


def synthetic() -> None:
    rng = np.random.default_rng(402)
    p = rng.normal(size=(100, 3)) * 3
    c = np.array([1.4, -2.1, .8])
    scale = 7.0
    q = (p - c) / scale
    ang = .37
    r = np.array([[np.cos(ang), -np.sin(ang), 0],
                  [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
    t = np.array([2., -.7, 1.1])
    y = (p @ r.T + t) / scale
    rf, tf = kabsch(q, y)
    np.testing.assert_allclose(rf, r, atol=1e-12)
    np.testing.assert_allclose(scale * tf - rf @ c, t, atol=1e-12)
    print("D0 synthetic normalized rigid decode passed", flush=True)


def frozen_files() -> list[Path]:
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_d0_flow_trajectory.py",
             MAIN / "scripts/maintenance/global_proposal_baseline.py",
             MAIN / "scripts/maintenance/fullscan_global_baseline.py",
             MAIN / "scripts/maintenance/v0_ray_visibility.py",
             MAIN.parent / "RAP-SLAM/rap_slam/rap_backend.py",
             MAIN.parent / "RAP-SLAM/rap_slam/real_dataset.py",
             MAIN.parent / "RAP-SLAM/rap_slam/structured_motion.py",
             MAIN / "rectified_point_flow/procrustes.py",
             F2 / "validation.json", F2 / "decision.json", F2 / "freeze.json"]
    for seq in ("00", "08"):
        files += [F2 / seq / "records.json", F2 / seq / "gates.json",
                  F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        for pair in g0.order(seq):
            folder = F2 / seq / pair
            files.append(folder / "inputs.npz")
            files.extend(folder / f"N{k}.npz" for k in range(4))
            files.extend(g1.pair_scans(seq, pair))
    return list(dict.fromkeys(files))


def freeze() -> None:
    assert not (BASE / "freeze.json").exists()
    synthetic()
    assert g0.read(F2 / "validation.json")["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
        "numpy": np.__version__, "scipy": __import__("scipy").__version__,
        "open3d": __import__("open3d").__version__,
        "files": {str(p): g0.sha(p) for p in files}})
    print("D0 frozen", len(files), "files", flush=True)


def verify() -> None:
    for name, digest in g0.read(BASE / "freeze.json")["files"].items():
        assert g0.sha(Path(name)) == digest, name


def limits(start: float) -> None:
    assert time.monotonic() - start <= 1200, "CPU wall cap"
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2 <= 4, "RSS cap"


def run() -> None:
    verify()
    verify_amendment()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    synthetic()
    (BASE / "INCOMPLETE").write_text("D0 decoded bank started\n", encoding="utf-8")
    start = time.monotonic()
    g = v0.gate_backend()
    bank = []
    max_final_delta = 0.0
    for seq in ("00", "08"):
        records = g0.read(F2 / seq / "records.json")
        gates = g0.read(F2 / seq / "gates.json")
        for idx, pair in enumerate(g0.order(seq)):
            folder = F2 / seq / pair
            with np.load(folder / "inputs.npz", allow_pickle=False) as inp:
                cond = inp["cond"].astype(np.float64)
                counts = inp["counts"].astype(np.int64)
                centers = inp["centers"].astype(np.float64)
                scale = float(inp["scale"])
            assert counts.tolist() == [2000, 1000, 1000, 2000, 1000, 1000]
            assert cond.shape == (8000, 3) and centers.shape == (6, 3) and scale > 0
            parent = [r for r in records if r["pair"] == pair and r["arm"] == "N"]
            assert len(parent) == 4 and all(r["valid"] for r in parent)
            parent.sort(key=lambda r: r["generation"])
            assert [r["generation"] for r in parent] == list(range(4))
            generations = []
            for k in range(4):
                with np.load(folder / f"N{k}.npz", allow_pickle=False) as z:
                    raw = z["end_point_trajectory"]
                    steps = z["rigidity_steps"]
                    saved = z["T"]
                    assert raw.shape == (5, 8000, 3) and steps.shape == (5,)
                    poses = [decode_one(cond, raw[s], counts, centers, scale) for s in range(5)]
                delta = float(np.max(np.abs(poses[4] - np.asarray(parent[k]["T"]))))
                max_final_delta = max(max_final_delta, delta)
                assert delta <= 1e-4
                assert np.max(np.abs(saved - np.asarray(parent[k]["T"]))) <= 1e-10
                assert abs(float(np.mean(steps)) - parent[k]["rigidity_rmse_m"]) <= 1e-6
                generations.append({"generation": k, "rigidity_steps_m": steps.tolist(),
                                    "T_steps": [p.tolist() for p in poses], "final_decode_delta": delta})
            selected = min(parent, key=lambda r: (r["rigidity_rmse_m"], r["generation"]))["generation"]
            target_path, source_path = g1.pair_scans(seq, pair)
            gate_t = g.preprocess(g1.load_scan(target_path))[0]
            gate_s = g.preprocess(g1.load_scan(source_path))[0]
            selected_gates = {}
            for key, s in (("penultimate", 3), ("final", 4)):
                pose = (np.asarray(generations[selected]["T_steps"][s]) if s == 3
                        else np.asarray(parent[selected]["T"], dtype=np.float64))
                overlap, mean_dist = g._alignment_metrics(gate_t, gate_s, pose, thresh=1.)
                selected_gates[key] = {"step": s, "T": pose.tolist(),
                    "overlap": float(overlap), "mean_dist": float(mean_dist),
                    "accepted": bool(overlap >= .7 and mean_dist <= 2.5)}
            old = gates[pair]["N"][str(selected)]
            assert abs(selected_gates["final"]["overlap"] - old["overlap_ratio"]) <= 1e-5
            assert abs(selected_gates["final"]["mean_dist"] - old["mean_dist"]) <= 1e-5
            assert selected_gates["final"]["accepted"] == old["accepted"]
            bank.append({"sequence": seq, "pair": pair, "selected_generation": selected,
                         "generations": generations, "selected_gates": selected_gates})
            if (idx + 1) % 10 == 0:
                print("D0 bank", seq, idx + 1, "elapsed", round(time.monotonic()-start, 1), flush=True)
            limits(start)
    g0.save_new(BASE / "bank.json", bank)
    g0.save_new(BASE / "bank_seal.json", {"sha256": g0.sha(BASE / "bank.json"),
        "utc": datetime.now(timezone.utc).isoformat(), "wall_s": time.monotonic()-start,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        "max_final_decode_delta": max_final_delta})
    print("D0 bank sealed", flush=True)


def label(pose: np.ndarray, truth: np.ndarray) -> dict:
    e = np.linalg.inv(truth) @ pose
    r = e[:3, :3]
    sine = np.linalg.norm([r[2,1]-r[1,2], r[0,2]-r[2,0], r[1,0]-r[0,1]])/2
    rte = float(np.linalg.norm(e[:3,3]))
    rre = float(np.degrees(np.arctan2(sine, np.clip((np.trace(r)-1)/2,-1,1))))
    return {"RTE_m": rte, "RRE_deg": rre, "strict": bool(rte <= 1 and rre <= 5),
            "clipped_error": float(min(5, max(rte, rre/5)))}


def evaluate() -> None:
    verify()
    verify_amendment()
    assert g0.sha(BASE / "bank.json") == g0.read(BASE / "bank_seal.json")["sha256"]
    bank = g0.read(BASE / "bank.json")
    outcomes = []
    for seq in ("00", "08"):
        parents = g0.read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        rows = [r for r in bank if r["sequence"] == seq]
        assert len(rows) == len(parents) == 100
        for row, parent in zip(rows, parents):
            assert row["pair"] == f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            truth = np.linalg.inv(gt[parent["source_i"]]) @ gt[parent["source_j"]]
            grid = [[label(np.asarray(p), truth) for p in generation["T_steps"]]
                    for generation in row["generations"]]
            selected = {}
            for name in ("penultimate", "final"):
                result = label(np.asarray(row["selected_gates"][name]["T"]), truth)
                result["accepted"] = row["selected_gates"][name]["accepted"]
                result["correct_accepted"] = bool(result["strict"] and result["accepted"])
                result["incorrect_accepted"] = bool(not result["strict"] and result["accepted"])
                selected[name] = result
            assert abs(selected["final"]["RTE_m"] - parent["methods"]["N"]["RTE_m"]) <= 1e-4
            assert abs(selected["final"]["RRE_deg"] - parent["methods"]["N"]["RRE_deg"]) <= 1e-4
            assert selected["final"]["accepted"] == parent["methods"]["N"]["accepted"]
            assert selected["final"]["strict"] == parent["methods"]["N"]["strict"]
            assert any(g[4]["strict"] for g in grid) == parent["methods"]["N-OR4"]["strict"]
            outcomes.append({"sequence": seq, "pair": row["pair"], "stratum": parent["stratum"],
                "step_oracle": [any(g[s]["strict"] for g in grid) for s in range(5)],
                "early_strict_steps": [s for s in range(4) if any(g[s]["strict"] for g in grid)],
                "grid": grid, "selected": selected})
    g0.save_new(BASE / "outcomes.json", outcomes)
    summary = {"scope": "observed-development saved native trajectory diagnosis", "sequences": {}}
    for seq in ("00", "08"):
        rows = [r for r in outcomes if r["sequence"] == seq]
        pos = [r for r in rows if r["stratum"] != "confuser"]
        missing = [r for r in pos if not r["step_oracle"][4]]
        transient = [r["pair"] for r in missing if r["early_strict_steps"]]
        methods = {}
        for name in ("penultimate", "final"):
            methods[name] = {"strict": sum(r["selected"][name]["strict"] for r in pos),
                "correct_accepts": sum(r["selected"][name]["correct_accepted"] for r in pos),
                "incorrect_accepts": sum(r["selected"][name]["incorrect_accepted"] for r in rows),
                "confuser_accepts": sum(r["selected"][name]["accepted"] for r in rows if r["stratum"]=="confuser"),
                "clipped_error": float(np.mean([r["selected"][name]["clipped_error"] for r in pos]))}
        summary["sequences"][seq] = {"final_K4_unavailable": len(missing),
            "oracle_strict_by_step": [sum(r["step_oracle"][s] for r in pos) for s in range(5)],
            "transient_missing_final": transient,
            "first_last_early_step": {r["pair"]: [min(r["early_strict_steps"]), max(r["early_strict_steps"])]
                                      for r in missing if r["early_strict_steps"]},
            "methods": methods,
            "strict_gains": [r["pair"] for r in pos if r["selected"]["penultimate"]["strict"] and not r["selected"]["final"]["strict"]],
            "strict_losses": [r["pair"] for r in pos if r["selected"]["final"]["strict"] and not r["selected"]["penultimate"]["strict"]],
            "new_correct_accepts": [r["pair"] for r in pos if r["selected"]["penultimate"]["correct_accepted"] and not r["selected"]["final"]["correct_accepted"]],
            "lost_correct_accepts": [r["pair"] for r in pos if r["selected"]["final"]["correct_accepted"] and not r["selected"]["penultimate"]["correct_accepted"]],
            "newly_incorrect_accepts": [r["pair"] for r in rows if r["selected"]["penultimate"]["incorrect_accepted"] and not r["selected"]["final"]["incorrect_accepted"]],
            "ordinary_strict_losses": [r["pair"] for r in pos if r["stratum"]=="ordinary" and r["selected"]["final"]["strict"] and not r["selected"]["penultimate"]["strict"]],
            "by_stratum": {st: {"n": sum(r["stratum"]==st for r in rows),
                "oracle_by_step": [sum(r["stratum"]==st and r["step_oracle"][s] for r in rows) for s in range(5)],
                "selected_step3_strict": sum(r["stratum"]==st and r["selected"]["penultimate"]["strict"] for r in rows),
                "selected_final_strict": sum(r["stratum"]==st and r["selected"]["final"]["strict"] for r in rows)}
                for st in ("confuser", "ambiguous_positive", "low_overlap", "ordinary")}}
    a, b = summary["sequences"]["08"], summary["sequences"]["00"]
    ap, af = a["methods"]["penultimate"], a["methods"]["final"]
    bp, bf = b["methods"]["penultimate"], b["methods"]["final"]
    conditions = {"transient_08": len(a["transient_missing_final"]) >= 5,
        "fixed_step3_08": ap["strict"]-af["strict"] >= 5 and ap["correct_accepts"]-af["correct_accepts"] >= 2,
        "accept_safety": not a["newly_incorrect_accepts"] and not b["newly_incorrect_accepts"],
        "00_guard": bp["strict"]-bf["strict"] >= -2,
        "ordinary_guard": len(a["ordinary_strict_losses"]) <= 1 and len(b["ordinary_strict_losses"]) <= 1,
        "cost": g0.read(BASE/"bank_seal.json")["wall_s"] <= 1200 and
                g0.read(BASE/"bank_seal.json")["peak_rss_gib"] <= 4 and
                sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file()) <= 50*1024**2}
    summary["conditions"] = conditions
    summary["decision"] = ("NO_TRANSIENT_CANDIDATE_EVIDENCE" if not conditions["transient_08"] else
        "CHECKPOINT_EXECUTABLE_SIGNAL" if all(conditions.values()) else "TRANSIENT_ONLY")
    g0.save_new(BASE / "summary.json", summary)
    print("D0", summary["decision"], conditions, flush=True)


if __name__ == "__main__":
    {"synthetic": synthetic, "freeze": freeze, "run": run, "evaluate": evaluate}[sys.argv[1]]()
