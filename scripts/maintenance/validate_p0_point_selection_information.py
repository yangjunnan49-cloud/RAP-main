"""Independent full-bank and evaluator validation for the P0 information audit."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

MAIN = Path(__file__).resolve().parents[2]
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
C1 = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
P2 = MAIN / "docs/maintenance/2026-09-29/p0-point-selection-preflight-02"
BASE = MAIN / "docs/maintenance/2026-09-29/p0-point-selection-information-01"
GT = {"00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}
CAPS = (2000, 1000, 1000, 2000, 1000, 1000)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def score(points, desc, transform, pair):
    target = np.asarray(points[:2000], dtype=np.float64)
    source = np.asarray(points[4000:6000], dtype=np.float64)
    moved = source @ transform[:3, :3].T + transform[:3, 3]
    eligible = cKDTree(target).query(moved, k=1, workers=1)[0] <= 1.0
    f = np.asarray(desc, dtype=np.float64)
    assert f.shape == (8000, 32) and np.isfinite(f).all()
    norm = np.linalg.norm(f, axis=1)
    assert np.all(norm > 1e-8)
    ft, fs = f[:2000]/norm[:2000, None], f[4000:6000]/norm[4000:6000, None]
    nearest_feature = cKDTree(ft).query(fs, k=1, workers=1)[1]
    true = np.linalg.norm(target[nearest_feature]-moved, axis=1) <= 1.0
    controls = []
    for k in range(16):
        seed = int.from_bytes(hashlib.sha256(f"C1|{pair}|{k}".encode()).digest()[:8], "big")
        mapping = np.random.default_rng(seed).permutation(2000)
        correct = np.linalg.norm(target[mapping[nearest_feature]]-moved, axis=1) <= 1.0
        controls.append(float(np.mean(correct[eligible])) if eligible.any() else None)
    covered = int(eligible.sum())
    recall = float(np.mean(true[eligible])) if covered else None
    control = float(np.mean(controls)) if covered else None
    return {"eligible_points": covered, "eligible_fraction": covered/2000,
            "true_recall": recall, "control_recalls": controls,
            "control_mean_recall": control,
            "paired_difference": recall-control if covered else None,
            "unconditional_correct_fraction": float(np.mean(true))}


def close(a, b):
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        for key in a:
            close(a[key], b[key])
    elif isinstance(a, list):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            close(x, y)
    elif a is None or isinstance(a, (str, bool)):
        assert a == b
    elif isinstance(a, (int, float)):
        assert abs(a-b) <= 1e-12, (a, b)
    else:
        assert a == b


def validate():
    frozen = read(BASE / "freeze.json")
    assert frozen["unique_raw_scans"] == 796
    checks = 0
    for name, digest in frozen["files"].items():
        assert sha(Path(name)) == digest, name
        checks += 1
    seal = read(BASE / "bank_seal.json")
    assert sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 1800 and seal["peak_allocated_gib"] <= 12
    assert seal["artifact_bytes"] <= 2**30
    bank = read(BASE / "bank.json")
    pair_rows = read(BASE / "pairs.json")
    result = read(BASE / "summary.json")
    assert len(bank) == len(pair_rows) == 200
    old = {r["pair"]: r for r in read(C1 / "pairs.json")}
    preflight = {(r["sequence"], r["pair"]): r for r in read(P2 / "bank.json")}
    assert len(preflight) == 4 and read(P2 / "validation.json")["passed"]
    assert result["bank_sha256"] == seal["sha256"]
    expected_order = [(s, r) for s in ("00", "08") for r in read(F2 / f"inputs_{s}.json")]
    assert len(expected_order) == 200
    gts = {s: np.load(GT[s], allow_pickle=False) for s in ("00", "08")}
    labels = {s: read(F2 / s / "evaluator_only_decisions.json") for s in ("00", "08")}
    for idx, ((seq, input_row), bank_row, row) in enumerate(zip(expected_order, bank, pair_rows)):
        pair = input_row["key"]
        assert bank_row["sequence"] == row["sequence"] == seq
        assert bank_row["pair"] == row["pair"] == pair
        assert sha(Path(bank_row["file"])) == bank_row["sha256"]
        assert len(bank_row["counts"]) == 6
        for info, cap in zip(bank_row["counts"], CAPS):
            assert cap <= info["post_outlier"] <= info["voxel"] <= 400000
        with np.load(bank_row["file"], allow_pickle=False) as z:
            points, features = z["points"], z["features"]
        assert points.shape == (8000, 3) and features.shape == (8000, 32)
        assert np.isfinite(points).all() and np.isfinite(features).all()
        assert np.min(np.linalg.norm(features, axis=1)) > 1e-8
        assert abs(float(np.min(np.linalg.norm(features, axis=1)))-bank_row["min_feature_norm"]) <= 1e-7
        if (seq, pair) in preflight:
            prior = preflight[(seq, pair)]
            assert bank_row["counts"] == prior["counts"]
            with np.load(prior["file"], allow_pickle=False) as z:
                assert np.array_equal(points, z["points"])
                assert np.array_equal(features, z["features"])
            checks += 3
        with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
            f2_points = z["points"]
            assert tuple(z["counts"].tolist()) == CAPS
        with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
            f2_features = z["features"]
        label = labels[seq][idx % 100]
        assert pair == f'{seq}_{label["source_i"]}_{label["source_j"]}'
        assert row["stratum"] == label["stratum"]
        assert row["native_candidate_available"] == bool(label["methods"]["N-OR4"]["strict"])
        transform = np.linalg.inv(gts[seq][label["source_i"]]) @ gts[seq][label["source_j"]]
        f2_metric = score(f2_points, f2_features, transform, pair)
        p0_metric = score(points, features, transform, pair)
        close(f2_metric, row["f2"])
        close(p0_metric, row["p0"])
        close(f2_metric, {k: old[pair][k] for k in f2_metric})
        gain = (p0_metric["paired_difference"]-f2_metric["paired_difference"]
                if p0_metric["paired_difference"] is not None and f2_metric["paired_difference"] is not None
                else None)
        close(gain, row["information_gain"])
        close(p0_metric["eligible_fraction"]-f2_metric["eligible_fraction"], row["coverage_gain"])
        checks += 10
    assert sum(Path(r["file"]).stat().st_size for r in bank) == seal["artifact_bytes"]
    hard = [r for r in pair_rows if r["sequence"] == "08" and r["stratum"] != "confuser"
            and not r["native_candidate_available"]]
    assert len(hard) == result["hard08_pairs"] == 41
    common = [r for r in hard if r["f2"]["eligible_fraction"] >= .1
              and r["p0"]["eligible_fraction"] >= .1]
    signs = sum(r["information_gain"] > 0 for r in common)
    close(len(common), result["primary_common_adequate"])
    close(signs, result["primary_positive_signs"])
    close(float(np.median([r["information_gain"] for r in common])) if common else None,
          result["primary_median_information_gain"])
    guards = {}
    for seq in ("00", "08"):
        ordinary = [r for r in pair_rows if r["sequence"] == seq and r["stratum"] == "ordinary"]
        assert len(ordinary) == 25
        both = [r for r in ordinary if r["information_gain"] is not None]
        guards[seq] = {"common_nonzero": len(both),
                       "median_gain": float(np.median([r["information_gain"] for r in both])) if both else None}
    close(guards, result["ordinary_guards"])
    if len(common) < 20 or any(v["common_nonzero"] < 20 for v in guards.values()):
        decision = "INCONCLUSIVE_COMMON_SUPPORT"
    elif (np.median([r["information_gain"] for r in common]) >= .10
          and 3*signs >= 2*len(common)
          and all(v["median_gain"] >= -.05 for v in guards.values())):
        decision = "MATERIAL_INFORMATION_SIGNAL"
    else:
        decision = "NO_MATERIAL_INFORMATION_SIGNAL"
    assert decision == result["decision"]
    checks += 12
    with (BASE / "validation.json").open("x", encoding="utf-8") as f:
        json.dump({"passed": True, "checks": checks,
                   "bank_sha256": seal["sha256"], "decision": decision}, f, indent=2)
        f.write("\n")
    (BASE / "INCOMPLETE").unlink()
    print("P0 full validation passed", checks, "checks", flush=True)


if __name__ == "__main__":
    validate()
