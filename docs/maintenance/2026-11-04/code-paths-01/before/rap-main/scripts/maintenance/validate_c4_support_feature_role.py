"""Independent C4 permutation, trajectory, pose, label and decision validation."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
C1 = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
C2 = MAIN / "docs/maintenance/2026-09-28/c2-feature-channel-01"
BASE = MAIN / "docs/maintenance/2026-09-29/c4-support-feature-role-01"
INDICES = (0, 1, 25, 26, 27, 28, 50, 51, 52, 53, 75, 76, 77, 78)


def own_permutation(pair, counts, selected):
    offsets = np.r_[0, np.cumsum(counts)]
    output = np.arange(int(offsets[-1]), dtype=np.int64)
    for part in selected:
        a, b = int(offsets[part]), int(offsets[part+1])
        seed = int.from_bytes(hashlib.sha256(f"C2|{pair}|{part}".encode()).digest()[:8], "big")
        output[a:b] = np.random.Generator(np.random.PCG64(seed)).permutation(b-a)+a
    return output


def rigid(source, target, center, scale):
    x, y = np.asarray(source, np.float64), np.asarray(target, np.float64)
    mean_x, mean_y = np.mean(x, axis=0), np.mean(y, axis=0)
    u, _, vt = np.linalg.svd((x-mean_x).T @ (y-mean_y))
    d = np.diag([1., 1., np.linalg.det(vt.T @ u.T)])
    rotation = vt.T @ d @ u.T
    translation = mean_y - rotation @ mean_x
    pose = np.eye(4)
    pose[:3, :3] = rotation
    pose[:3, 3] = scale*translation - rotation @ center
    return pose


def decode(cond, final, centers, counts, scale):
    offsets = np.r_[0, np.cumsum(counts)]
    parts = [rigid(cond[int(offsets[k]):int(offsets[k+1])],
                   final[int(offsets[k]):int(offsets[k+1])], centers[k], scale)
             for k in range(6)]
    return np.linalg.inv(parts[0]) @ parts[3]


def angle(pose):
    return float(np.degrees(np.arccos(np.clip((np.trace(pose[:3, :3])-1)/2, -1, 1))))


def strict(pose, truth):
    e = np.linalg.inv(truth) @ pose
    return bool(np.linalg.norm(e[:3, 3]) <= 1 and angle(e) <= 5)


def validate():
    checks = 0
    frozen = g0.read(BASE / "freeze.json")
    for path, digest in frozen["files"].items():
        assert g0.sha(Path(path)) == digest, path
        checks += 1
    for seq in ("00", "08"):
        assert frozen["pairs"][seq] == [g0.order(seq)[ix] for ix in INDICES]
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 600 and seal["peak_allocated_gib"] <= 12
    assert seal["artifact_bytes"] <= 512*2**20
    bank = g0.read(BASE / "bank.json")
    outcomes = g0.read(BASE / "outcomes.json")
    assert len(bank) == len(outcomes) == 28
    checked = []
    for seq in ("00", "08"):
        labels = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                  g0.read(F2 / seq / "evaluator_only_decisions.json")}
        native = g0.read(F2 / seq / "records.json")
        gt = np.load(GT[seq], allow_pickle=False)
        for ix, pair in enumerate(frozen["pairs"][seq]):
            n = ix + (14 if seq == "08" else 0)
            row, outcome = bank[n], outcomes[n]
            assert row["pair"] == outcome["pair"] == pair
            assert g0.sha(Path(row["file"])) == row["sha256"]
            with np.load(row["file"], allow_pickle=False) as z:
                raw = {a: z[f"raw_{a}"] for a in ("t", "a", "s")}
                state = {a: z[f"state_{a}"] for a in ("t", "a", "s")}
                permutations = {a: z[f"perm_{a}"] for a in ("a", "s")}
                stored_pose = {a: z[f"pose_{a}"] for a in ("t", "a", "s")}
            for a in ("t", "a", "s"):
                assert raw[a].shape == state[a].shape == (5, 8000, 3)
                assert np.isfinite(raw[a]).all() and np.isfinite(state[a]).all()
                checks += 1
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                cond, counts, centers, scale = z["cond"], z["counts"], z["centers"], float(z["scale"])
                assert z["points"].shape == (8000, 3)
                assert z["noise"].shape[1:] == (8000, 3)
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                features = z["features"]
            assert features.shape == (8000, 32)
            with np.load(C2 / seq / f"{pair}.npz", allow_pickle=False) as z:
                full = z["permutation"]
                assert np.array_equal(raw["t"], z["raw_true"])
                assert np.array_equal(state["t"], z["state_true"])
            pa = own_permutation(pair, counts, (0, 3))
            ps = own_permutation(pair, counts, (1, 2, 4, 5))
            assert np.array_equal(permutations["a"], pa)
            assert np.array_equal(permutations["s"], ps)
            assert np.array_equal(full, pa[ps])
            offsets = np.r_[0, np.cumsum(counts)]
            for k in range(6):
                a, b = int(offsets[k]), int(offsets[k+1])
                if k in (0, 3):
                    assert np.array_equal(features[ps[a:b]], features[a:b])
                else:
                    assert np.array_equal(features[pa[a:b]], features[a:b])
                assert np.array_equal(np.sort(features[pa[a:b]], axis=0),
                                      np.sort(features[a:b], axis=0))
                assert np.array_equal(np.sort(features[ps[a:b]], axis=0),
                                      np.sort(features[a:b], axis=0))
                checks += 3
            with np.load(F2 / seq / pair / "N0.npz", allow_pickle=False) as z:
                reproduction = max(float(np.max(np.abs(raw["t"]-z["end_point_trajectory"]))),
                                   float(np.max(np.abs(state["t"]-z["trajectory"]))))
            assert reproduction <= 1e-5 and abs(reproduction-row["reproduction_max_delta"]) <= 1e-12
            poses = {a: decode(cond, raw[a][-1], centers, counts, scale) for a in ("t", "a", "s")}
            for a in ("t", "a", "s"):
                assert np.max(np.abs(poses[a]-stored_pose[a])) <= 1e-4
                assert np.array_equal(stored_pose[a], np.asarray(row[f"pose_{a}"]))
                checks += 2
            parent = next(r for r in native if r["pair"] == pair and r["arm"] == "N" and r["generation"] == 0)
            assert np.max(np.abs(poses["t"]-np.asarray(parent["T"]))) <= 1e-4
            for arm in ("a", "s"):
                e = np.linalg.inv(stored_pose["t"]) @ stored_pose[arm]
                translation = float(np.linalg.norm(e[:3, 3]))
                rotation = angle(e)
                rms = float(np.sqrt(np.mean(np.sum((raw[arm][-1].astype(np.float64)-
                                                    raw["t"][-1].astype(np.float64))**2, axis=1))))
                assert abs(translation-row[f"{arm}_pose_delta_m"]) <= 1e-9
                assert abs(rotation-row[f"{arm}_pose_delta_deg"]) <= 1e-6
                assert abs(rms-row[f"{arm}_raw_final_rms"]) <= 1e-12
                assert outcome["anchor_pose_response" if arm == "a" else "support_pose_response"] == (
                    rms >= .005 and (translation >= .25 or rotation >= .25))
                checks += 4
            label = labels[pair]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            assert outcome["stratum"] == label["stratum"]
            assert outcome["native_candidate_available"] == label["methods"]["N-OR4"]["strict"]
            for arm, name in (("t", "true_strict"), ("a", "anchor_strict"), ("s", "support_strict")):
                assert outcome[name] == strict(stored_pose[arm], truth)
                checks += 1
            checked.append(outcome)
    summary = g0.read(BASE / "summary.json")
    assert summary["bank_sha256"] == seal["sha256"]
    ordinary = [r for r in checked if r["stratum"] == "ordinary"]
    positives = [r for r in checked if r["stratum"] != "confuser"]
    assert len(ordinary) == summary["ordinary_pairs"] == 7
    assert len(positives) == summary["positive_pairs"] == 22
    anchors = sum(r["anchor_pose_response"] for r in ordinary)
    supports = sum(r["support_pose_response"] for r in ordinary)
    flips = sum(r["support_strict"] != r["true_strict"] for r in positives)
    assert anchors == summary["ordinary_anchor_pose_responses"]
    assert supports == summary["ordinary_support_pose_responses"]
    assert flips == summary["positive_support_strict_flips"]
    decision = ("INCONCLUSIVE_ANCHOR_CONTROL" if anchors < 5 else
                "SUPPORT_FEATURE_CANDIDATE_RELIANCE" if supports >= 6 and flips >= 3 else
                "SUPPORT_FEATURE_POSE_RELIANCE_ONLY" if supports >= 6 else
                "NO_MATERIAL_SUPPORT_FEATURE_RELIANCE")
    assert summary["decision"] == decision
    for group, reported in summary["groups"].items():
        seq, stratum = group.split("_", 1)
        sample = [r for r in checked if r["sequence"] == seq and r["stratum"] == stratum]
        expected = {"pairs": len(sample),
                    "anchor_pose_responses": sum(r["anchor_pose_response"] for r in sample),
                    "support_pose_responses": sum(r["support_pose_response"] for r in sample),
                    "true_strict": sum(r["true_strict"] for r in sample),
                    "anchor_strict": sum(r["anchor_strict"] for r in sample),
                    "support_strict": sum(r["support_strict"] for r in sample),
                    "support_strict_gains": sum(r["support_strict"] and not r["true_strict"] for r in sample),
                    "support_strict_losses": sum(r["true_strict"] and not r["support_strict"] for r in sample)}
        assert reported == expected
        checks += len(expected)
    assert not (BASE / "INCOMPLETE").exists()
    g0.save_new(BASE / "validation.json", {"passed": True, "checks": checks,
                                            "decision": decision,
                                            "bank_sha256": seal["sha256"]})
    print("C4 independent validation", checks, "checks", decision, flush=True)


if __name__ == "__main__":
    validate()
