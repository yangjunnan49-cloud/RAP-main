"""Fixed same-visit persistence feature mask and radial-matched control."""

from __future__ import annotations

import hashlib
import os
import random
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c2_feature_channel as c2
import global_proposal_baseline as g0

MAIN, F2, GT, C1, RAP = c2.MAIN, c2.F2, c2.GT, c2.C1, c2.RAP
C4 = MAIN / "docs/maintenance/2026-09-29/c4-support-feature-role-01"
BASE = MAIN / "docs/maintenance/2026-09-29/c5-temporal-persistence-01"
BINS = np.array([0, 10, 20, 30, 40, 60, 80, 100, np.inf], dtype=np.float64)
SUPPORT_PARTS = (1, 2, 4, 5)


def frozen_files():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_c5_temporal_persistence.py",
             MAIN / "scripts/maintenance/c2_feature_channel.py",
             MAIN / "scripts/maintenance/global_proposal_baseline.py",
             MAIN / "scripts/maintenance/s1_stepcount_dev_v2.py",
             C4 / "validation.json", C4 / "outcomes.json", C4 / "bank_seal.json",
             C1 / "validation.json", C1 / "bank_seal.json",
             F2 / "freeze.json", F2 / "validation.json",
             MAIN / "weights/rap_model_12.ckpt", MAIN / "weights/mini_spinnet_t.pth",
             RAP / "rap_slam/rap_backend.py", RAP / "rap_slam/structured_motion.py",
             RAP / "rap_slam/rap_precision.py", RAP / "scripts/hl0_preflight.py"]
    files += list((MAIN / "rectified_point_flow").rglob("*.py"))
    files += list((MAIN / "dataset_process").rglob("*.py"))
    files += list((MAIN / "config").rglob("*.yaml"))
    for seq, pairs in c2.selected().items():
        files += [F2 / f"inputs_{seq}.json", F2 / seq / "records.json",
                  F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        for pair in pairs:
            files += [F2 / seq / pair / "inputs.npz", F2 / seq / pair / "N0.npz",
                      C1 / seq / f"{pair}.npz"]
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE / "freeze.json").exists()
    for p in (C4 / "validation.json", C1 / "validation.json", F2 / "validation.json"):
        assert g0.read(p)["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "pairs": c2.selected(),
        "files": {str(p): g0.sha(p) for p in files}})
    print("C5 frozen", len(files), "identities", flush=True)


def verify():
    f = g0.read(BASE / "freeze.json")
    assert f["pairs"] == c2.selected()
    for name, digest in f["files"].items():
        assert g0.sha(Path(name)) == digest, name


def masks(pair, points, counts, motions):
    assert len(points) == len(counts) == len(motions) == 6
    offsets = np.r_[0, np.cumsum(counts)]
    persistent = np.ones(8000, dtype=bool)
    random_match = np.ones(8000, dtype=bool)
    fractions = []
    for part in SUPPORT_PARTS:
        anchor = 0 if part < 3 else 3
        L = np.asarray(motions[part], dtype=np.float64)
        assert L.shape == (4, 4) and np.isfinite(L).all()
        assert np.max(np.abs(L[3] - [0, 0, 0, 1])) < 1e-10
        xyz = points[part].astype(np.float64)
        moved = xyz @ L[:3, :3].T + L[:3, 3]
        keep = cKDTree(points[anchor].astype(np.float64)).query(moved, k=1, workers=1)[0] <= 1.0
        radial = np.linalg.norm(xyz, axis=1)
        bin_id = np.searchsorted(BINS[1:-1], radial, side="right")
        control = np.zeros(len(xyz), dtype=bool)
        for b in range(8):
            candidates = np.flatnonzero(bin_id == b)
            n = int(np.count_nonzero(keep[candidates]))
            seed = int.from_bytes(hashlib.sha256(f"C5|{pair}|{part}|{b}".encode()).digest()[:8], "big")
            choice = np.random.Generator(np.random.PCG64(seed)).choice(candidates, size=n, replace=False)
            control[choice] = True
            assert np.count_nonzero(control[candidates]) == n
        a, e = int(offsets[part]), int(offsets[part+1])
        persistent[a:e] = keep
        random_match[a:e] = control
        fractions.append(float(np.mean(keep)))
    assert np.all(persistent[:2000]) and np.all(persistent[4000:6000])
    assert np.all(random_match[:2000]) and np.all(random_match[4000:6000])
    return persistent, random_match, fractions


def synthetic():
    rng = np.random.default_rng(29)
    parts = [rng.uniform(-15, 15, (2000, 3)).astype(np.float32)]
    parts += [parts[0][:1000].copy()+np.array([1, 0, 0], np.float32),
              parts[0][1000:].copy()+np.array([1, 0, 0], np.float32)]
    parts += [parts[0].copy(), parts[1].copy(), parts[2].copy()]
    motions = [np.eye(4) for _ in range(6)]
    for part in SUPPORT_PARTS:
        motions[part][:3, 3] = [-1, 0, 0]
    p, r, fractions = masks("synthetic", parts, [len(x) for x in parts], motions)
    assert p.shape == r.shape == (8000,)
    assert all(x == 1.0 for x in fractions)
    assert np.array_equal(p, r)
    print("C5 synthetic support transform/mask passed", flush=True)


def bank():
    import torch
    sys.path[:0] = [str(MAIN), str(RAP), str(RAP / "scripts")]
    from rap_slam.rap_precision import ieee_matmul
    from rap_slam.structured_motion import build_batch, decode_parts
    from hl0_preflight import request_rng
    from rap_slam.measurement import rotation_validity

    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert torch.cuda.is_available()
    assert not (BASE / "bank.json").exists() and not (BASE / "INCOMPLETE").exists()
    (BASE / "INCOMPLETE").write_text("C5 bank in progress\n", encoding="utf-8")
    started = time.monotonic()
    backend = c2.make_backend()
    torch.cuda.reset_peak_memory_stats()
    rows = []

    def state():
        return (torch.get_rng_state().clone(), torch.cuda.get_rng_state().clone(),
                random.getstate(), np.random.get_state(), backend.seed,
                torch.get_float32_matmul_precision())

    def same(a, b):
        assert torch.equal(a[0], b[0]) and torch.equal(a[1], b[1]) and a[2] == b[2]
        assert a[3][0] == b[3][0] and np.array_equal(a[3][1], b[3][1]) and a[3][2:] == b[3][2:]
        assert a[4:] == b[4:]

    for seq, pairs in c2.selected().items():
        inputs = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        native = g0.read(F2 / seq / "records.json")
        for pair in pairs:
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                all_points, cond, counts = z["points"], z["cond"], z["counts"]
                centers, scale = z["centers"], float(z["scale"])
                noise = torch.from_numpy(z["noise"][0]).to(backend.device)
            assert all_points.shape == (8000, 3) and counts.tolist() == list(c2.CAPS)
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                features = z["features"]
            assert features.shape == (8000, 32)
            offsets = np.r_[0, np.cumsum(counts)]
            points = [all_points[int(a):int(e)] for a, e in zip(offsets[:-1], offsets[1:])]
            keep_p, keep_r, fractions = masks(pair, points, counts, inputs[pair]["motions"])
            batches = {}
            for arm, keep in (("T", np.ones(8000, dtype=bool)), ("P", keep_p), ("R", keep_r)):
                chosen = features * keep[:, None]
                chunks = [chosen[int(a):int(e)] for a, e in zip(offsets[:-1], offsets[1:])]
                batch, s, centers_new, counts_new = build_batch(backend, points, chunks)
                assert s == scale and np.array_equal(centers_new, centers)
                assert np.array_equal(counts_new, counts)
                assert np.array_equal(batch["pointclouds"].cpu().numpy(), cond)
                if arm != "T":
                    for key in ("pointclouds", "anchor_indices", "points_per_part", "scales", "cu_seqlens"):
                        assert torch.equal(batch[key], batches["T"][key])
                batches[arm] = batch
            raw, traj, poses = {}, {}, {}
            for arm in ("T", "P", "R"):
                before = state()
                with request_rng(inputs[pair]["seeds"][0], backend), ieee_matmul(), torch.inference_mode(), \
                     torch.autocast(device_type="cuda", dtype=torch.float16):
                    output = backend.model.sample_rectified_flow(
                        batches[arm], None, x_1=noise, return_tarjectory=True)
                torch.cuda.synchronize()
                same(before, state())
                raw[arm] = output["end_point_trajectory"].detach().float().cpu().numpy()
                traj[arm] = output["trajectory"].detach().float().cpu().numpy()
                assert raw[arm].shape == traj[arm].shape == (5, 8000, 3)
                assert np.isfinite(raw[arm]).all() and np.isfinite(traj[arm]).all()
                with ieee_matmul(), torch.inference_mode():
                    part_poses = decode_parts(batches[arm], output["end_point_trajectory"][-1], centers, scale)
                poses[arm] = np.linalg.inv(part_poses[0]) @ part_poses[3]
                assert rotation_validity(poses[arm])["valid"]
            with np.load(F2 / seq / pair / "N0.npz", allow_pickle=False) as z:
                reproduction = max(float(np.max(np.abs(raw["T"]-z["end_point_trajectory"]))),
                                   float(np.max(np.abs(traj["T"]-z["trajectory"]))))
            assert reproduction <= 1e-5, (pair, reproduction)
            parent = next(r for r in native if r["pair"] == pair and r["arm"] == "N" and r["generation"] == 0)
            assert np.max(np.abs(poses["T"]-np.asarray(parent["T"]))) <= 1e-5
            artifact = BASE / seq / f"{pair}.npz"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            assert not artifact.exists()
            np.savez_compressed(artifact, raw_t=raw["T"], state_t=traj["T"],
                                raw_p=raw["P"], state_p=traj["P"],
                                raw_r=raw["R"], state_r=traj["R"],
                                mask_p=keep_p, mask_r=keep_r,
                                pose_t=poses["T"], pose_p=poses["P"], pose_r=poses["R"])
            rows.append({"sequence": seq, "pair": pair, "file": str(artifact),
                         "sha256": g0.sha(artifact), "reproduction_max_delta": reproduction,
                         "support_keep_fractions": fractions,
                         "pose_t": poses["T"].tolist(), "pose_p": poses["P"].tolist(),
                         "pose_r": poses["R"].tolist()})
            print("C5 bank", seq, pair, "elapsed", round(time.monotonic()-started, 1), flush=True)
            assert time.monotonic()-started <= 600
            assert torch.cuda.max_memory_allocated() <= 12*2**30
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 512*2**20
    g0.save_new(BASE / "bank.json", rows)
    g0.save_new(BASE / "bank_seal.json", {
        "sha256": g0.sha(BASE / "bank.json"), "utc": datetime.now(timezone.utc).isoformat(),
        "wall_s": time.monotonic()-started,
        "peak_allocated_gib": torch.cuda.max_memory_allocated()/2**30,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz"))})
    print("C5 bank sealed", flush=True)


def evaluate():
    import s1_stepcount_dev_v2 as s1

    verify()
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    bank = g0.read(BASE / "bank.json")
    assert len(bank) == 28
    prior = {r["pair"]: r for r in g0.read(C4 / "outcomes.json")}
    rows = []
    for seq in ("00", "08"):
        labels = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                  g0.read(F2 / seq / "evaluator_only_decisions.json")}
        gt = np.load(GT[seq], allow_pickle=False)
        for item in (r for r in bank if r["sequence"] == seq):
            assert g0.sha(Path(item["file"])) == item["sha256"]
            label = labels[item["pair"]]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            strict = {a: bool(s1.label(np.asarray(item[f"pose_{a}"]), truth)["strict"])
                      for a in ("t", "p", "r")}
            assert strict["t"] == prior[item["pair"]]["true_strict"]
            rows.append({"sequence": seq, "pair": item["pair"], "stratum": label["stratum"],
                         "native_candidate_available": bool(label["methods"]["N-OR4"]["strict"]),
                         "true_strict": strict["t"], "persistent_strict": strict["p"],
                         "random_strict": strict["r"]})
    g0.save_new(BASE / "outcomes.json", rows)
    primary = [r for r in rows if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_candidate_available"]]
    assert len(primary) == 6 and all(not r["true_strict"] for r in primary)
    p_recover = sum(r["persistent_strict"] for r in primary)
    r_recover = sum(r["random_strict"] for r in primary)
    losses = {seq: sum(r["true_strict"] and not r["persistent_strict"] for r in rows
                       if r["sequence"] == seq and r["stratum"] != "confuser") for seq in ("00", "08")}
    ordinary_losses = {seq: sum(r["true_strict"] and not r["persistent_strict"] for r in rows
                                if r["sequence"] == seq and r["stratum"] == "ordinary")
                       for seq in ("00", "08")}
    keep = [x for item in bank for x in item["support_keep_fractions"]]
    assert len(keep) == 112
    median_keep = float(np.median(keep))
    decision = ("INCONCLUSIVE_MASK_SUPPORT" if not (.10 <= median_keep <= .90) else
                "PROMISING_TEMPORAL_PERSISTENCE_SCREEN" if p_recover >= 2 and
                p_recover-r_recover >= 2 and all(losses[s] <= 1 and ordinary_losses[s] <= 1
                                              for s in ("00", "08")) else
                "NO_TEMPORAL_PERSISTENCE_SCREEN_SIGNAL")
    groups = {}
    for seq in ("00", "08"):
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            subset = [r for r in rows if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = {
                "pairs": len(subset),
                "t_strict": sum(r["true_strict"] for r in subset),
                "p_strict": sum(r["persistent_strict"] for r in subset),
                "r_strict": sum(r["random_strict"] for r in subset),
                "p_gains": sum(r["persistent_strict"] and not r["true_strict"] for r in subset),
                "p_losses": sum(r["true_strict"] and not r["persistent_strict"] for r in subset),
            }
    g0.save_new(BASE / "summary.json", {
        "decision": decision, "primary_pairs": 6,
        "primary_p_recoveries": p_recover, "primary_r_recoveries": r_recover,
        "support_fraction_median": median_keep,
        "positive_losses": losses, "ordinary_losses": ordinary_losses,
        "groups": groups, "bank_sha256": seal["sha256"]})
    (BASE / "INCOMPLETE").unlink()
    print("C5 decision", decision, "P/R recoveries", p_recover, r_recover, flush=True)


if __name__ == "__main__":
    {"synthetic": synthetic, "freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
