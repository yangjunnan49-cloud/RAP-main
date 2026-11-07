"""Frozen C1 descriptor bank and evaluator-only correspondence audit."""

from __future__ import annotations

import hashlib
import json
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
import global_proposal_baseline as g0
import fullscan_global_baseline as g1

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
RAP = MAIN.parent / "RAP-SLAM"
BASE = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
CAPS = (2000, 1000, 1000, 2000, 1000, 1000)


def frozen_files():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_c1_descriptor_information.py",
             MAIN / "weights/mini_spinnet_t.pth",
             F2 / "validation.json", F2 / "freeze.json",
             RAP / "rap_slam/rap_backend.py", RAP / "rap_slam/structured_motion.py",
             RAP / "rap_slam/real_dataset.py", RAP / "rap_slam/rap_precision.py",
             RAP / "scripts/hl0_preflight.py"]
    files += list((MAIN / "dataset_process").rglob("*.py"))
    files += list((MAIN / "rectified_point_flow").rglob("*.py"))
    files += list((MAIN / "config").rglob("*.yaml"))
    for seq in ("00", "08"):
        files += [F2 / f"inputs_{seq}.json", F2 / seq / "records.json",
                  F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        rows = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        for pair in g0.order(seq):
            files.append(F2 / seq / pair / "inputs.npz")
            files.extend(Path(e["path"]) for e in rows[pair]["scans"])
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert g0.read(F2 / "validation.json")["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": {seq: g0.order(seq) for seq in ("00", "08")},
        "files": {str(p): g0.sha(p) for p in files},
        "numpy": np.__version__,
    })
    print("C1 frozen", len(files), "identities", flush=True)


def verify():
    frozen = g0.read(BASE / "freeze.json")
    assert frozen["pairs"] == {seq: g0.order(seq) for seq in ("00", "08")}
    for name, digest in frozen["files"].items():
        assert g0.sha(Path(name)) == digest, name


def unit(features):
    f = np.asarray(features, dtype=np.float64)
    assert f.ndim == 2 and f.shape[1] == 32 and np.isfinite(f).all()
    norms = np.linalg.norm(f, axis=1)
    assert np.all(norms > 1e-8)
    return f / norms[:, None]


def permutation(pair, k):
    seed = int.from_bytes(hashlib.sha256(f"C1|{pair}|{k}".encode()).digest()[:8], "big")
    return np.random.default_rng(seed).permutation(2000)


def synthetic():
    target = np.array([[0., 0., 0.], [2., 0., 0.], [4., 0., 0.]])
    source = target + np.array([1., 2., 0.])
    pose = np.eye(4)
    pose[:3, 3] = [-1., -2., 0.]
    moved = source @ pose[:3, :3].T + pose[:3, 3]
    assert np.max(np.abs(moved - target)) < 1e-12
    f = np.zeros((3, 32))
    f[np.arange(3), np.arange(3)] = 1
    assert np.array_equal(cKDTree(unit(f)).query(unit(f))[1], np.arange(3))
    assert sorted(permutation("synthetic", 0)) == list(range(2000))


def bank():
    import torch
    sys.path[:0] = [str(MAIN), str(RAP), str(RAP / "scripts")]
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.rap_precision import ieee_matmul
    from rap_slam.structured_motion import build_batch
    from hl0_preflight import request_rng
    from dataset_process.extract_sample_features import FeatureExtractor

    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert torch.cuda.is_available()
    (BASE / "INCOMPLETE").write_text("C1 descriptor bank started\n", encoding="utf-8")
    started = time.monotonic()
    # Use the exact backend preprocessing method without constructing its
    # unused flow model or invoking its permissive checkpoint loader.
    backend = RAPBackend.__new__(RAPBackend)
    backend.voxel_size = .4
    backend.remove_outliers = True
    backend.max_points_per_scan = 4000
    backend.seed = 42
    backend.device = torch.device("cuda")
    backend.feature_extractor = FeatureExtractor(
        model_config={"num_points_per_patch": 512, "is_aligned_to_global_z": True,
                      "des_r": 5.0}, des_r=5.0, is_aligned_to_global_z=True,
        checkpoint_path=None, device="cuda")
    saved = torch.load(MAIN / "weights/mini_spinnet_t.pth", map_location="cpu",
                       weights_only=True)
    desc = {key[5:]: value for key, value in saved.items() if key.startswith("Desc.")}
    backend.feature_extractor.model.load_state_dict(desc, strict=True)
    backend.feature_extractor.model.eval()
    assert backend.device.type == "cuda"
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

    for seq in ("00", "08"):
        inputs = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        for ix, pair in enumerate(g0.order(seq)):
            row = inputs[pair]
            scans = []
            for e in row["scans"]:
                path = Path(e["path"])
                assert g0.sha(path) == e["sha256"]
                scans.append(g1.load_scan(path))
            before = state()
            with request_rng(row["seeds"][0], backend), ieee_matmul(), torch.inference_mode():
                backend.seed = 42
                points, features = [], []
                for scan, cap in zip(scans, CAPS):
                    p, f = backend.preprocess(scan, max_points=cap)
                    assert len(p) == cap and f.shape == (cap, 32)
                    unit(f)
                    points.append(p)
                    features.append(f)
            same(before, state())
            batch, scale, centers, counts = build_batch(backend, points, features)
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                assert np.array_equal(np.concatenate(points), z["points"])
                assert np.array_equal(counts, z["counts"])
                assert np.array_equal(batch["pointclouds"].cpu().numpy(), z["cond"])
                assert np.array_equal(centers, z["centers"]) and scale == float(z["scale"])
            dest = BASE / seq / f"{pair}.npz"
            dest.parent.mkdir(parents=True, exist_ok=True)
            assert not dest.exists()
            feature_array = np.concatenate(features)
            np.savez_compressed(dest, features=feature_array)
            rows.append({"sequence": seq, "pair": pair, "file": str(dest),
                         "sha256": g0.sha(dest),
                         "min_feature_norm": float(np.min(np.linalg.norm(feature_array, axis=1))),
                         "max_feature_norm": float(np.max(np.linalg.norm(feature_array, axis=1)))})
            if (ix + 1) % 10 == 0:
                print("C1 bank", seq, ix + 1, "elapsed", round(time.monotonic() - started, 1), flush=True)
            assert time.monotonic() - started <= 1800
            assert torch.cuda.max_memory_allocated() <= 12 * 2**30
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 2**30
    g0.save_new(BASE / "bank.json", rows)
    g0.save_new(BASE / "bank_seal.json", {
        "sha256": g0.sha(BASE / "bank.json"), "utc": datetime.now(timezone.utc).isoformat(),
        "wall_s": time.monotonic() - started,
        "peak_allocated_gib": torch.cuda.max_memory_allocated() / 2**30,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz")),
    })
    print("C1 bank sealed", flush=True)


def score(points, features, truth, pair):
    target, source = points[:2000].astype(np.float64), points[4000:6000].astype(np.float64)
    ft, fs = unit(features[:2000]), unit(features[4000:6000])
    moved = source @ truth[:3, :3].T + truth[:3, 3]
    eligible = cKDTree(target).query(moved, k=1, workers=1)[0] <= 1.0
    indices = cKDTree(ft).query(fs, k=1, workers=1)[1]
    true_match = np.linalg.norm(target[indices] - moved, axis=1) <= 1.0
    controls = []
    for k in range(16):
        mapped = permutation(pair, k)[indices]
        match = np.linalg.norm(target[mapped] - moved, axis=1) <= 1.0
        controls.append(float(np.mean(match[eligible])) if np.any(eligible) else None)
    covered = int(np.sum(eligible))
    recall = float(np.mean(true_match[eligible])) if covered else None
    control = float(np.mean(controls)) if covered else None
    return {"eligible_points": covered, "eligible_fraction": covered / 2000,
            "true_recall": recall, "control_recalls": controls,
            "control_mean_recall": control,
            "paired_difference": recall - control if covered else None,
            "unconditional_correct_fraction": float(np.mean(true_match))}


def summarize(rows):
    present = [r for r in rows if r["true_recall"] is not None]
    def stat(key):
        vals = [r[key] for r in present]
        return {"mean": float(np.mean(vals)) if vals else None,
                "median": float(np.median(vals)) if vals else None}
    return {"pairs": len(rows), "eligible_pairs": len(present),
            "adequate_pairs": sum(r["eligible_fraction"] >= .10 for r in rows),
            "eligible_fraction": stat("eligible_fraction"),
            "true_recall": stat("true_recall"),
            "control_mean_recall": stat("control_mean_recall"),
            "paired_difference": stat("paired_difference")}


def evaluate():
    verify()
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    bank = g0.read(BASE / "bank.json")
    assert len(bank) == 200
    rows = []
    for seq in ("00", "08"):
        parent = g0.read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        selected = [r for r in bank if r["sequence"] == seq]
        assert len(parent) == len(selected) == 100
        for saved, label in zip(selected, parent):
            pair = f'{seq}_{label["source_i"]}_{label["source_j"]}'
            assert saved["pair"] == pair and g0.sha(Path(saved["file"])) == saved["sha256"]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
            with np.load(saved["file"], allow_pickle=False) as z:
                features = z["features"]
            assert features.shape == (8000, 32)
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            metric = score(points, features, truth, pair)
            rows.append({"sequence": seq, "pair": pair, "stratum": label["stratum"],
                         "native_candidate_available": bool(label["methods"]["N-OR4"]["strict"]),
                         **metric})
    g0.save_new(BASE / "pairs.json", rows)
    groups = {}
    for seq in ("00", "08"):
        for availability in (False, True):
            subset = [r for r in rows if r["sequence"] == seq and r["stratum"] != "confuser"
                      and r["native_candidate_available"] == availability]
            groups[f"{seq}_{'available' if availability else 'unavailable'}"] = summarize(subset)
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            subset = [r for r in rows if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = summarize(subset)
    primary = [r for r in rows if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_candidate_available"] and r["eligible_fraction"] >= .10]
    assert len([r for r in rows if r["sequence"] == "08" and r["stratum"] != "confuser"
                and not r["native_candidate_available"]]) == 41
    if len(primary) < 20:
        decision = "INCONCLUSIVE_CORRESPONDENCE_SUPPORT"
    elif np.median([r["paired_difference"] for r in primary]) >= .10:
        decision = "FEATURE_INFORMATION_PRESENT"
    else:
        decision = "NO_FEATURE_INFORMATION_SIGNAL"
    summary = {"scope": "observed-development descriptor information diagnostic",
               "decision": decision, "primary_adequate_pairs": len(primary),
               "primary_adequate_paired_difference_median": (
                   float(np.median([r["paired_difference"] for r in primary])) if primary else None),
               "groups": groups, "bank_sha256": seal["sha256"]}
    g0.save_new(BASE / "summary.json", summary)
    (BASE / "INCOMPLETE").unlink()
    print("C1 decision", decision, "primary adequate", len(primary), flush=True)


if __name__ == "__main__":
    {"synthetic": synthetic, "freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
