"""Independent frozen C2 geometry, pairing and decision validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import fullscan_global_baseline as g1
import v0_ray_visibility as v0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
BASE = MAIN / "docs/maintenance/2026-09-28/c2-feature-channel-01"
C1 = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
INDICES = (0, 1, 25, 26, 27, 28, 50, 51, 52, 53, 75, 76, 77, 78)


def rigid(source, target, center, scale):
    x, y = source.astype(np.float64), target.astype(np.float64)
    mean_x, mean_y = np.mean(x, axis=0), np.mean(y, axis=0)
    u, _, vt = np.linalg.svd((x - mean_x).T @ (y - mean_y))
    diag = np.diag([1., 1., np.linalg.det(vt.T @ u.T)])
    rotation = vt.T @ diag @ u.T
    translation = mean_y - rotation @ mean_x
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = scale * translation - rotation @ center
    return matrix


def decode(cond, raw, centers, counts, scale):
    offsets = np.r_[0, np.cumsum(counts)]
    poses = [rigid(cond[a:b], raw[a:b], centers[k], scale)
             for k, (a, b) in enumerate(zip(offsets[:-1], offsets[1:]))]
    return np.linalg.inv(poses[0]) @ poses[3]


def rotation_angle(matrix):
    return float(np.degrees(np.arccos(np.clip((np.trace(matrix[:3, :3]) - 1) / 2, -1, 1))))


def strict(pose, truth):
    e = np.linalg.inv(truth) @ pose
    return bool(np.linalg.norm(e[:3, 3]) <= 1 and rotation_angle(e) <= 5)


def validate():
    checks = 0
    frozen = g0.read(BASE / "freeze.json")
    for name, digest in frozen["files"].items():
        assert g0.sha(Path(name)) == digest, name
        checks += 1
    for seq in ("00", "08"):
        assert frozen["pairs"][seq] == [g0.order(seq)[i] for i in INDICES]
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 600 and seal["peak_allocated_gib"] <= 12
    assert seal["artifact_bytes"] <= 512 * 2**20
    bank = g0.read(BASE / "bank.json")
    outcomes = g0.read(BASE / "outcomes.json")
    assert len(bank) == len(outcomes) == 28
    gate = v0.gate_backend()
    groups = {}
    for seq in ("00", "08"):
        parent = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                  g0.read(F2 / seq / "evaluator_only_decisions.json")}
        input_rows = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        gt = np.load(GT[seq], allow_pickle=False)
        for ix, pair in enumerate(frozen["pairs"][seq]):
            row = bank[14 * (seq == "08") + ix]
            outcome = outcomes[14 * (seq == "08") + ix]
            assert pair == row["pair"] == outcome["pair"]
            assert g0.sha(Path(row["file"])) == row["sha256"]
            with np.load(row["file"], allow_pickle=False) as z:
                rt, st, rq, sq = (z[k] for k in ("raw_true", "state_true", "raw_q", "state_q"))
                perm = z["permutation"]
                q_saved = z["pose_q"]
            for tensor in (rt, st, rq, sq):
                assert tensor.shape == (5, 8000, 3) and np.isfinite(tensor).all()
            with np.load(F2 / seq / pair / "N0.npz", allow_pickle=False) as z:
                exact_delta = max(float(np.max(np.abs(rt - z["end_point_trajectory"]))),
                                  float(np.max(np.abs(st - z["trajectory"]))))
            assert exact_delta <= 1e-5 and abs(exact_delta - row["reproduction_max_delta"]) <= 1e-12
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                cond, counts, centers, scale = (z["cond"], z["counts"], z["centers"], float(z["scale"]))
            offsets = np.r_[0, np.cumsum(counts)]
            assert perm.shape == (8000,)
            for part, (a, b) in enumerate(zip(offsets[:-1], offsets[1:])):
                seed = int.from_bytes(hashlib.sha256(f"C2|{pair}|{part}".encode()).digest()[:8], "big")
                expected = np.random.default_rng(seed).permutation(int(counts[part])) + int(a)
                assert np.array_equal(perm[a:b], expected)
                checks += 1
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                features = z["features"]
            assert features.shape == (8000, 32)
            assert np.array_equal(np.sort(features[perm[:2000]], axis=0),
                                  np.sort(features[:2000], axis=0))
            pose_t = decode(cond, rt[-1], centers, counts, scale)
            pose_q = decode(cond, rq[-1], centers, counts, scale)
            assert np.max(np.abs(pose_t - np.asarray(row["pose_true"]))) <= 1e-4
            assert np.max(np.abs(pose_q - np.asarray(row["pose_q"]))) <= 1e-4
            assert np.max(np.abs(q_saved - np.asarray(row["pose_q"]))) == 0
            e = np.linalg.inv(np.asarray(row["pose_true"])) @ np.asarray(row["pose_q"])
            trans = float(np.linalg.norm(e[:3, 3]))
            angle = rotation_angle(e)
            rms = float(np.sqrt(np.mean(np.sum((rq[-1].astype(np.float64) -
                                                rt[-1].astype(np.float64)) ** 2, axis=1))))
            assert abs(trans - row["pose_delta_m"]) <= 1e-9
            assert abs(angle - row["pose_delta_deg"]) <= 1e-6
            assert abs(rms - row["raw_final_rms"]) <= 1e-12
            scans = input_rows[pair]["scans"]
            target = gate.preprocess(g1.load_scan(Path(scans[0]["path"])))[0]
            source = gate.preprocess(g1.load_scan(Path(scans[3]["path"])))[0]
            overlap, distance = gate._alignment_metrics(target, source, q_saved, thresh=1.)
            assert abs(overlap - row["overlap"]) <= 1e-9
            assert abs(distance - row["mean_dist"]) <= 1e-9
            accepted = overlap >= .7 and distance <= 2.5
            assert accepted == row["accepted"] == outcome["shuffled_accepted"]
            label = parent[pair]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            assert outcome["stratum"] == label["stratum"]
            assert outcome["native_candidate_available"] == label["methods"]["N-OR4"]["strict"]
            assert outcome["true_strict"] == strict(np.asarray(row["pose_true"]), truth)
            assert outcome["shuffled_strict"] == strict(q_saved, truth)
            assert outcome["true_accepted"] == label["methods"]["N"]["accepted"]
            assert outcome["raw_response"] == (rms >= .005)
            assert outcome["pose_response"] == (rms >= .005 and (trans >= .25 or angle >= .25))
            groups.setdefault(f'{seq}_{label["stratum"]}', []).append(outcome)
            checks += 19
    summary = g0.read(BASE / "summary.json")
    assert summary["bank_sha256"] == seal["sha256"]
    ordinary = [r for r in outcomes if r["stratum"] == "ordinary"]
    assert len(ordinary) == 8
    pose_count = sum(r["pose_response"] for r in ordinary)
    raw_count = sum(r["raw_response"] for r in ordinary)
    assert summary["ordinary_pose_responses"] == pose_count
    assert summary["ordinary_raw_responses"] == raw_count
    decision = ("POSE_LEVEL_FEATURE_RELIANCE" if pose_count >= 6 else
                "FLOW_ONLY_FEATURE_RELIANCE" if raw_count >= 6 else
                "NO_MATERIAL_FEATURE_RELIANCE")
    assert summary["decision"] == decision
    for group, reported in summary["groups"].items():
        sample = groups[group]
        assert reported["pairs"] == len(sample)
        for field, key in (("raw_responses", "raw_response"),
                           ("pose_responses", "pose_response"),
                           ("true_strict", "true_strict"),
                           ("shuffled_strict", "shuffled_strict"),
                           ("true_accepted", "true_accepted"),
                           ("shuffled_accepted", "shuffled_accepted")):
            assert reported[field] == sum(r[key] for r in sample)
            checks += 1
    assert not (BASE / "INCOMPLETE").exists()
    g0.save_new(BASE / "validation.json", {"passed": True, "checks": checks,
                                            "decision": decision,
                                            "bank_sha256": seal["sha256"]})
    print("C2 independent validation", checks, decision, flush=True)


if __name__ == "__main__":
    validate()
