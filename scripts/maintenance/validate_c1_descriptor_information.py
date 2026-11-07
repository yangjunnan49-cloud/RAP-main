"""Separate full-bank C1 validator with independent metric arithmetic."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import fullscan_global_baseline as g1

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
BASE = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"


def close(a, b, tol=1e-11):
    if a is None or b is None:
        assert a is None and b is None
    else:
        assert abs(float(a) - float(b)) <= tol, (a, b)


def own_match(points, features, truth, pair):
    t = np.asarray(points[:2000], dtype=np.float64)
    s = np.asarray(points[4000:6000], dtype=np.float64)
    fs = np.asarray(features[4000:6000], dtype=np.float64)
    ft = np.asarray(features[:2000], dtype=np.float64)
    fs /= np.linalg.norm(fs, axis=1)[:, None]
    ft /= np.linalg.norm(ft, axis=1)[:, None]
    xyz = (truth[:3, :3] @ s.T).T + truth[:3, 3]
    eligible = cKDTree(t).query(xyz, k=1)[0] <= 1
    matched = cKDTree(ft).query(fs, k=1)[1]
    actual = np.linalg.norm(t[matched] - xyz, axis=1) <= 1
    n = int(np.count_nonzero(eligible))
    controls = []
    for k in range(16):
        raw = hashlib.sha256(f"C1|{pair}|{k}".encode()).digest()
        rng = np.random.Generator(np.random.PCG64(int.from_bytes(raw[:8], "big")))
        mapping = rng.permutation(2000)
        ok = np.linalg.norm(t[mapping[matched]] - xyz, axis=1) <= 1
        controls.append(float(np.count_nonzero(ok & eligible) / n) if n else None)
    true = float(np.count_nonzero(actual & eligible) / n) if n else None
    mean_control = float(sum(controls) / 16) if n else None
    return {"eligible_points": n, "eligible_fraction": n / 2000,
            "true_recall": true, "control_recalls": controls,
            "control_mean_recall": mean_control,
            "paired_difference": true - mean_control if n else None,
            "unconditional_correct_fraction": float(np.count_nonzero(actual) / 2000)}


def own_summary(rows):
    with_support = [r for r in rows if r["eligible_points"] > 0]
    answer = {"pairs": len(rows), "eligible_pairs": len(with_support),
              "adequate_pairs": sum(r["eligible_fraction"] >= .1 for r in rows)}
    for key in ("eligible_fraction", "true_recall", "control_mean_recall", "paired_difference"):
        values = [r[key] for r in with_support]
        answer[key] = {"mean": float(np.mean(values)) if values else None,
                       "median": float(np.median(values)) if values else None}
    return answer


def spot_regeneration(bank):
    import torch
    sys.path[:0] = [str(MAIN), str(MAIN.parent / "RAP-SLAM"),
                    str(MAIN.parent / "RAP-SLAM" / "scripts")]
    from dataset_process.extract_sample_features import FeatureExtractor
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.rap_precision import ieee_matmul
    from hl0_preflight import request_rng

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
    raw = torch.load(MAIN / "weights/mini_spinnet_t.pth", map_location="cpu",
                     weights_only=True)
    weights = {k[5:]: v for k, v in raw.items() if k.startswith("Desc.")}
    backend.feature_extractor.model.load_state_dict(weights, strict=True)
    backend.feature_extractor.model.eval()
    items = {r["pair"]: r for r in bank}
    count = 0
    for seq in ("00", "08"):
        input_rows = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        order = g0.order(seq)
        for ix in (0, 25, 50, 75):
            pair = order[ix]
            inp = input_rows[pair]
            parts = []
            desc = []
            with request_rng(inp["seeds"][0], backend), ieee_matmul(), torch.inference_mode():
                backend.seed = 42
                for source, cap in zip(inp["scans"], (2000, 1000, 1000, 2000, 1000, 1000)):
                    assert g0.sha(Path(source["path"])) == source["sha256"]
                    points, features = backend.preprocess(g1.load_scan(Path(source["path"])), max_points=cap)
                    parts.append(points)
                    desc.append(features)
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                assert np.array_equal(np.concatenate(parts), z["points"])
            with np.load(items[pair]["file"], allow_pickle=False) as z:
                assert np.array_equal(np.concatenate(desc), z["features"])
            count += 1
    return count


def validate():
    checks = 0
    frozen = g0.read(BASE / "freeze.json")
    assert len(frozen["pairs"]["00"]) == len(frozen["pairs"]["08"]) == 100
    for name, digest in frozen["files"].items():
        assert g0.sha(Path(name)) == digest, name
        checks += 1
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 1800 and seal["peak_allocated_gib"] <= 12
    assert seal["artifact_bytes"] <= 2**30
    bank = g0.read(BASE / "bank.json")
    output = g0.read(BASE / "pairs.json")
    assert len(bank) == len(output) == 200
    by_pair = {r["pair"]: r for r in bank}
    assert len(by_pair) == 200
    outcomes = []
    for seq in ("00", "08"):
        labels = g0.read(F2 / seq / "evaluator_only_decisions.json")
        native = g0.read(F2 / seq / "records.json")
        gt = np.load(GT[seq], allow_pickle=False)
        for ix, label in enumerate(labels):
            pair = f'{seq}_{label["source_i"]}_{label["source_j"]}'
            row = output[100 * (seq == "08") + ix]
            item = by_pair[pair]
            assert pair == row["pair"] == frozen["pairs"][seq][ix]
            assert g0.sha(Path(item["file"])) == item["sha256"]
            with np.load(item["file"], allow_pickle=False) as z:
                features = z["features"]
            assert features.shape == (8000, 32) and np.isfinite(features).all()
            norms = np.linalg.norm(features.astype(np.float64), axis=1)
            assert np.min(norms) > 1e-8
            close(np.min(norms), item["min_feature_norm"], 1e-5)
            close(np.max(norms), item["max_feature_norm"], 1e-5)
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"]
                assert points.shape == (8000, 3)
                assert z["counts"].tolist() == [2000, 1000, 1000, 2000, 1000, 1000]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            metric = own_match(points, features, truth, pair)
            assert row["sequence"] == seq and row["stratum"] == label["stratum"]
            for name, value in metric.items():
                if isinstance(value, list):
                    for a, b in zip(value, row[name]):
                        close(a, b)
                else:
                    close(value, row[name])
                checks += 1
            four = [r for r in native if r["pair"] == pair and r["arm"] == "N"]
            assert len(four) == 4
            available = False
            for candidate in four:
                e = np.linalg.inv(truth) @ np.asarray(candidate["T"])
                rte = float(np.linalg.norm(e[:3, 3]))
                rre = float(np.degrees(np.arccos(np.clip((np.trace(e[:3, :3]) - 1) / 2, -1, 1))))
                available |= rte <= 1 and rre <= 5
            assert available == row["native_candidate_available"] == label["methods"]["N-OR4"]["strict"]
            outcomes.append(row)
            checks += 5
    summary = g0.read(BASE / "summary.json")
    assert summary["bank_sha256"] == seal["sha256"]
    for group, reported in summary["groups"].items():
        seq, kind = group.split("_", 1)
        if kind in ("available", "unavailable"):
            selected = [r for r in outcomes if r["sequence"] == seq and r["stratum"] != "confuser"
                        and r["native_candidate_available"] == (kind == "available")]
        else:
            selected = [r for r in outcomes if r["sequence"] == seq and r["stratum"] == kind]
        expected = own_summary(selected)
        assert expected["pairs"] == reported["pairs"]
        assert expected["eligible_pairs"] == reported["eligible_pairs"]
        assert expected["adequate_pairs"] == reported["adequate_pairs"]
        for metric in ("eligible_fraction", "true_recall", "control_mean_recall", "paired_difference"):
            close(expected[metric]["mean"], reported[metric]["mean"])
            close(expected[metric]["median"], reported[metric]["median"])
            checks += 2
    primary = [r for r in outcomes if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_candidate_available"] and r["eligible_fraction"] >= .1]
    assert len(primary) == summary["primary_adequate_pairs"]
    median = float(np.median([r["paired_difference"] for r in primary])) if primary else None
    close(median, summary["primary_adequate_paired_difference_median"])
    decision = ("INCONCLUSIVE_CORRESPONDENCE_SUPPORT" if len(primary) < 20 else
                "FEATURE_INFORMATION_PRESENT" if median >= .1 else "NO_FEATURE_INFORMATION_SIGNAL")
    assert decision == summary["decision"]
    regenerated = spot_regeneration(bank)
    assert regenerated == 8
    checks += regenerated
    assert not (BASE / "INCOMPLETE").exists()
    g0.save_new(BASE / "validation.json", {"passed": True, "checks": checks,
                                            "decision": decision,
                                            "bank_sha256": seal["sha256"]})
    print("C1 independent validation", checks, "checks", decision, flush=True)


if __name__ == "__main__":
    validate()
