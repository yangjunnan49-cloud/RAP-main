"""Independent C5 geometry-mask, bank, pose and decision validator."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
BASE = MAIN / "docs/maintenance/2026-09-29/c5-temporal-persistence-01"
C4 = MAIN / "docs/maintenance/2026-09-29/c4-support-feature-role-01"
INDEX = (0, 1, 25, 26, 27, 28, 50, 51, 52, 53, 75, 76, 77, 78)
EDGES = (0, 10, 20, 30, 40, 60, 80, 100, float("inf"))


def own_masks(pair, points, counts, motions):
    offsets = np.r_[0, np.cumsum(counts)]
    actual = np.ones(8000, dtype=bool)
    random_control = np.ones(8000, dtype=bool)
    shares = []
    for part in (1, 2, 4, 5):
        base = points[0 if part < 3 else 3].astype(np.float64)
        x = points[part].astype(np.float64)
        L = np.asarray(motions[part], dtype=np.float64)
        aligned = (L[:3, :3] @ x.T).T + L[:3, 3]
        match = cKDTree(base).query(aligned, k=1)[0] <= 1
        radii = np.linalg.norm(x, axis=1)
        chosen = np.zeros(len(x), dtype=bool)
        for b in range(8):
            ids = np.flatnonzero((radii >= EDGES[b]) & (radii < EDGES[b+1]))
            n = int(np.count_nonzero(match[ids]))
            seed = int.from_bytes(hashlib.sha256(f"C5|{pair}|{part}|{b}".encode()).digest()[:8], "big")
            take = np.random.Generator(np.random.PCG64(seed)).choice(ids, n, replace=False)
            chosen[take] = True
            assert np.count_nonzero(chosen[ids]) == n
        a, e = int(offsets[part]), int(offsets[part+1])
        actual[a:e] = match
        random_control[a:e] = chosen
        shares.append(float(np.count_nonzero(match)/len(match)))
    return actual, random_control, shares


def rigid(x, y, center, scale):
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    mx, my = x.mean(axis=0), y.mean(axis=0)
    u, _, vt = np.linalg.svd((x-mx).T @ (y-my))
    r = vt.T @ np.diag([1., 1., np.linalg.det(vt.T @ u.T)]) @ u.T
    t = my-r@mx
    out = np.eye(4)
    out[:3, :3] = r
    out[:3, 3] = scale*t-r@center
    return out


def pose_from_raw(cond, raw, centers, counts, scale):
    off = np.r_[0, np.cumsum(counts)]
    ts = [rigid(cond[int(off[k]):int(off[k+1])], raw[int(off[k]):int(off[k+1])],
                centers[k], scale) for k in range(6)]
    return np.linalg.inv(ts[0])@ts[3]


def strict(pose, truth):
    e = np.linalg.inv(truth)@pose
    rte = np.linalg.norm(e[:3, 3])
    rre = np.degrees(np.arccos(np.clip((np.trace(e[:3, :3])-1)/2, -1, 1)))
    return bool(rte <= 1 and rre <= 5)


def validate():
    frozen = g0.read(BASE / "freeze.json")
    checks = 0
    for path, digest in frozen["files"].items():
        assert g0.sha(Path(path)) == digest, path
        checks += 1
    for seq in ("00", "08"):
        assert frozen["pairs"][seq] == [g0.order(seq)[i] for i in INDEX]
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 600 and seal["peak_allocated_gib"] <= 12
    assert seal["artifact_bytes"] <= 512*2**20
    bank, output = g0.read(BASE / "bank.json"), g0.read(BASE / "outcomes.json")
    assert len(bank) == len(output) == 28
    c4 = {r["pair"]: r for r in g0.read(C4 / "outcomes.json")}
    observed = []
    fractions = []
    for seq in ("00", "08"):
        inputs = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        labels = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                  g0.read(F2 / seq / "evaluator_only_decisions.json")}
        gt = np.load(GT[seq], allow_pickle=False)
        for ix, pair in enumerate(frozen["pairs"][seq]):
            n = ix + (14 if seq == "08" else 0)
            row, outcome = bank[n], output[n]
            assert pair == row["pair"] == outcome["pair"]
            assert g0.sha(Path(row["file"])) == row["sha256"]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                xyz = z["points"]
                cond, counts, centers, scale = z["cond"], z["counts"], z["centers"], float(z["scale"])
            off = np.r_[0, np.cumsum(counts)]
            parts = [xyz[int(a):int(e)] for a, e in zip(off[:-1], off[1:])]
            pm, rm, shares = own_masks(pair, parts, counts, inputs[pair]["motions"])
            assert np.allclose(row["support_keep_fractions"], shares, atol=0, rtol=0)
            fractions.extend(shares)
            with np.load(row["file"], allow_pickle=False) as z:
                assert np.array_equal(z["mask_p"], pm)
                assert np.array_equal(z["mask_r"], rm)
                raw = {a: z[f"raw_{a}"] for a in ("t", "p", "r")}
                state = {a: z[f"state_{a}"] for a in ("t", "p", "r")}
                saved = {a: z[f"pose_{a}"] for a in ("t", "p", "r")}
            checks += 4
            for a in ("t", "p", "r"):
                assert raw[a].shape == state[a].shape == (5, 8000, 3)
                assert np.isfinite(raw[a]).all() and np.isfinite(state[a]).all()
                independent = pose_from_raw(cond, raw[a][-1], centers, counts, scale)
                assert np.max(np.abs(independent-saved[a])) <= 1e-4
                assert np.array_equal(saved[a], np.asarray(row[f"pose_{a}"]))
                checks += 4
            with np.load(F2 / seq / pair / "N0.npz", allow_pickle=False) as z:
                delta = max(float(np.max(np.abs(raw["t"]-z["end_point_trajectory"]))),
                            float(np.max(np.abs(state["t"]-z["trajectory"]))))
            assert delta <= 1e-5 and abs(delta-row["reproduction_max_delta"]) <= 1e-12
            label = labels[pair]
            truth = np.linalg.inv(gt[label["source_i"]])@gt[label["source_j"]]
            assert outcome["stratum"] == label["stratum"]
            assert outcome["native_candidate_available"] == label["methods"]["N-OR4"]["strict"]
            for a, key in (("t", "true_strict"), ("p", "persistent_strict"), ("r", "random_strict")):
                assert outcome[key] == strict(saved[a], truth)
                checks += 1
            assert outcome["true_strict"] == c4[pair]["true_strict"]
            observed.append(outcome)
    assert len(fractions) == 112
    primary = [r for r in observed if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_candidate_available"]]
    assert len(primary) == 6 and all(not r["true_strict"] for r in primary)
    p_recover = sum(r["persistent_strict"] for r in primary)
    r_recover = sum(r["random_strict"] for r in primary)
    losses = {seq: sum(r["true_strict"] and not r["persistent_strict"] for r in observed
                       if r["sequence"] == seq and r["stratum"] != "confuser") for seq in ("00", "08")}
    ordinary = {seq: sum(r["true_strict"] and not r["persistent_strict"] for r in observed
                         if r["sequence"] == seq and r["stratum"] == "ordinary") for seq in ("00", "08")}
    median = float(np.median(fractions))
    decision = ("INCONCLUSIVE_MASK_SUPPORT" if not (.10 <= median <= .90) else
                "PROMISING_TEMPORAL_PERSISTENCE_SCREEN" if p_recover >= 2 and
                p_recover-r_recover >= 2 and all(losses[s] <= 1 and ordinary[s] <= 1 for s in ("00", "08")) else
                "NO_TEMPORAL_PERSISTENCE_SCREEN_SIGNAL")
    summary = g0.read(BASE / "summary.json")
    assert summary["bank_sha256"] == seal["sha256"]
    assert summary["decision"] == decision and summary["primary_pairs"] == 6
    assert summary["primary_p_recoveries"] == p_recover and summary["primary_r_recoveries"] == r_recover
    assert summary["support_fraction_median"] == median
    assert summary["positive_losses"] == losses and summary["ordinary_losses"] == ordinary
    for name, stats in summary["groups"].items():
        seq, stratum = name.split("_", 1)
        sample = [r for r in observed if r["sequence"] == seq and r["stratum"] == stratum]
        expected = {"pairs": len(sample), "t_strict": sum(r["true_strict"] for r in sample),
                    "p_strict": sum(r["persistent_strict"] for r in sample),
                    "r_strict": sum(r["random_strict"] for r in sample),
                    "p_gains": sum(r["persistent_strict"] and not r["true_strict"] for r in sample),
                    "p_losses": sum(r["true_strict"] and not r["persistent_strict"] for r in sample)}
        assert stats == expected
        checks += len(expected)
    assert not (BASE / "INCOMPLETE").exists()
    g0.save_new(BASE / "validation.json", {"passed": True, "checks": checks,
                                            "decision": decision, "bank_sha256": seal["sha256"]})
    print("C5 independent validation", checks, decision, flush=True)


if __name__ == "__main__":
    validate()
