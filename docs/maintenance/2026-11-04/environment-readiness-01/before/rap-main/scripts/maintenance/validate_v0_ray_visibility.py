"""Independent V0 hashes, ray spot checks, gates, labels and decision audit."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

MAIN = Path(__file__).resolve().parents[2]
BASE = MAIN / "docs/maintenance/2026-09-28/v0-ray-visibility-01"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
RAW = Path("/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset/sequences")
GRID = list(itertools.product((-1., 0., 1.), repeat=3))
GT = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def close(a, b, tol=1e-8):
    assert abs(float(a) - float(b)) <= tol, (a, b)


def corrected(seq, frame):
    path = RAW / seq / "velodyne" / f"{frame:06d}.bin"
    p = np.fromfile(path, dtype=np.float32).reshape(-1, 4)[:, :3]
    p = p[np.linalg.norm(p, axis=1) >= 1.5]
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    rho = np.hypot(x, y)
    safe = rho > 1e-6
    c, s = np.cos(np.deg2rad(.205)), np.sin(np.deg2rad(.205))
    den = np.maximum(rho, 1e-6)
    out = p.copy()
    out[:, 0] = np.where(safe, x*c - x*z/den*s, x)
    out[:, 1] = np.where(safe, y*c - y*z/den*s, y)
    out[:, 2] = np.where(safe, z*c + rho*s, z)
    return out


def sampled(seq, frame, points):
    seed = int(hashlib.sha256(f"V0|ray-query|{seq}|{frame}".encode()).hexdigest()[:8], 16)
    return points[np.random.default_rng(seed).choice(len(points), 4096, replace=False)]


def ray_counts(q, ref_points, ref_tree, ref_ranges):
    qr = np.linalg.norm(q, axis=1)
    dist, idx = ref_tree.query(q/qr[:, None], k=1, workers=1)
    observed = dist <= 2*np.sin(np.deg2rad(.4)/2)
    dr = qr - ref_ranges[idx]
    return (int(np.sum(observed & (np.abs(dr) <= .75))),
            int(np.sum(observed & (dr < -.75))),
            int(np.sum(observed & (dr > .75))),
            int(np.sum(~observed)))


def independent_candidate(seq, row, cand, target, source, ti, si, trees):
    pose = np.asarray(row["transforms"]["N"]["T"]).copy()
    delta = np.asarray(cand["delta_m"])
    pose[:3, 3] += delta
    src_in_tgt = si @ pose[:3, :3].T + pose[:3, 3]
    tgt_in_src = (ti - pose[:3, 3]) @ pose[:3, :3]
    counts = np.array(ray_counts(src_in_tgt, target, trees["target_ray"], trees["target_range"])) + \
             np.array(ray_counts(tgt_in_src, source, trees["source_ray"], trees["source_range"]))
    assert [cand[x] for x in ("agree", "free", "occluded", "unobserved")] == counts.tolist()
    close(cand["coverage"], 1-counts[3]/8192)
    penalty = .02*np.dot(delta, delta)
    close(cand["visibility_score"], (counts[1]-counts[0]+.25*counts[3])/8192+penalty)
    da = trees["target_point"].query(src_in_tgt, k=1, workers=1)[0]
    db = trees["source_point"].query(tgt_in_src, k=1, workers=1)[0]
    close(cand["nn_score"], (np.minimum(da,5).sum()+np.minimum(db,5).sum())/8192+penalty, 1e-6)


def metric(pose, truth):
    e = np.linalg.inv(truth) @ pose
    r = e[:3, :3]
    sine = np.linalg.norm([r[2,1]-r[1,2], r[0,2]-r[2,0], r[1,0]-r[0,1]])/2
    rte = float(np.linalg.norm(e[:3,3]))
    rre = float(np.degrees(np.arctan2(sine, np.clip((np.trace(r)-1)/2,-1,1))))
    return rte, rre


def main():
    assert not (BASE / "validation.json").exists()
    assert not (BASE / "INCOMPLETE").exists()
    checks = 0
    for name, digest in read(BASE / "freeze.json")["files"].items():
        assert sha(Path(name)) == digest, name
        checks += 1
    bank = read(BASE / "bank.json")
    seal = read(BASE / "bank_seal.json")
    outcomes = read(BASE / "outcomes.json")
    summary = read(BASE / "summary.json")
    assert sha(BASE / "bank.json") == seal["sha256"]
    assert len(bank) == len(outcomes) == 200
    assert seal["wall_s"] <= 1800 and seal["peak_rss_gib"] <= 4
    assert sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file()) <= 1024**3
    checks += 4
    for seq in ("00", "08"):
        parents = read(F2 / seq / "evaluator_only_decisions.json")
        records = read(F2 / seq / "records.json")
        gates = read(F2 / seq / "gates.json")
        gt = np.load(GT[seq], allow_pickle=False)
        rows = [r for r in bank if r["sequence"] == seq]
        labels = [r for r in outcomes if r["sequence"] == seq]
        assert len(rows) == len(labels) == len(parents) == 100
        for idx, (row, out, parent) in enumerate(zip(rows, labels, parents)):
            assert row["pair"] == out["pair"] == f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            assert out["stratum"] == parent["stratum"]
            assert (row["source_i"], row["source_j"]) == (parent["source_i"], parent["source_j"])
            native = [r for r in records if r["pair"] == row["pair"] and r["arm"] == "N"]
            assert len(native) == 4
            chosen = min(native, key=lambda r: (r["rigidity_rmse_m"],r["generation"]))
            assert row["native_generation"] == chosen["generation"]
            np.testing.assert_allclose(row["transforms"]["N"]["T"], chosen["T"], atol=1e-12, rtol=0)
            oldgate = gates[row["pair"]]["N"][str(chosen["generation"])]
            close(row["transforms"]["N"]["overlap"], oldgate["overlap_ratio"], 1e-5)
            close(row["transforms"]["N"]["mean_dist"], oldgate["mean_dist"], 1e-5)
            assert row["transforms"]["N"]["accepted"] == oldgate["accepted"]
            cand = row["candidates"]
            assert len(cand) == 27 and [x["delta_m"] for x in cand] == [list(x) for x in GRID]
            for c in cand:
                assert sum(c[k] for k in ("agree", "free", "occluded", "unobserved")) == 8192
                close(c["coverage"], 1-c["unobserved"]/8192)
                close(c["visibility_score"], (c["free"]-c["agree"]+.25*c["unobserved"])/8192+.02*sum(x*x for x in c["delta_m"]))
                assert np.isfinite(c["nn_score"])
            centre = 13
            possible = [k for k,c in enumerate(cand) if c["coverage"] >= .10]
            vi = centre if cand[centre]["coverage"] < .10 else min(possible, key=lambda k: (cand[k]["visibility_score"], sum(x*x for x in GRID[k]), GRID[k]))
            ni = min(range(27), key=lambda k: (cand[k]["nn_score"], sum(x*x for x in GRID[k]), GRID[k]))
            assert [row["transforms"][k]["candidate_index"] for k in ("N","V","NN")] == [centre,vi,ni]
            truth = np.linalg.inv(gt[row["source_i"]]) @ gt[row["source_j"]]
            for name in ("N", "V", "NN"):
                stored = row["transforms"][name]
                t = np.asarray(stored["T"])
                expected = np.asarray(chosen["T"]).copy(); expected[:3,3] += GRID[stored["candidate_index"]]
                np.testing.assert_allclose(t, expected, atol=1e-12, rtol=0)
                assert np.max(np.abs(t[:3,:3].T@t[:3,:3]-np.eye(3))) < 1e-4
                assert abs(np.linalg.det(t[:3,:3])-1) < 1e-4
                assert stored["accepted"] == (stored["overlap"] >= .7 and stored["mean_dist"] <= 2.5)
                rte,rre=metric(t,truth)
                label=out["methods"][name]
                close(label["RTE_m"],rte,1e-6); close(label["RRE_deg"],rre,1e-5)
                assert label["strict"] == (rte<=1 and rre<=5)
                close(label["clipped_error"],min(5,max(rte,rre/5)),1e-6)
                assert label["accepted"] == stored["accepted"]
                assert label["correct_accepted"] == (stored["accepted"] and label["strict"])
                assert label["incorrect_accepted"] == (stored["accepted"] and not label["strict"])
            close(out["centre_coverage"],cand[13]["coverage"])
            assert out["native_K4_unavailable"] == (not parent["methods"]["N-OR4"]["strict"])
            assert row["wall_s"] >= 0 and row["target_points"] > 4096 and row["source_points"] > 4096
            checks += 1
            if idx in (0,25,50,75):
                target = corrected(seq,row["source_i"]).astype(np.float64)
                source = corrected(seq,row["source_j"]).astype(np.float64)
                assert len(target) == row["target_points"] and len(source) == row["source_points"]
                ti,si=sampled(seq,row["source_i"],target),sampled(seq,row["source_j"],source)
                tr,sr=np.linalg.norm(target,axis=1),np.linalg.norm(source,axis=1)
                trees={"target_ray":cKDTree(target/tr[:,None]),"source_ray":cKDTree(source/sr[:,None]),
                       "target_range":tr,"source_range":sr,
                       "target_point":cKDTree(target),"source_point":cKDTree(source)}
                for c in cand:
                    independent_candidate(seq,row,c,target,source,ti,si,trees)
                    checks += 1
        positives = [x for x in labels if x["stratum"] != "confuser"]
        assert len(positives)==75 and len(labels)-len(positives)==25
        s = summary["sequences"][seq]
        assert s["coverage_ge_0p10"] == sum(x["centre_coverage"]>=.10 for x in labels)
        close(s["centre_coverage_median"],np.median([x["centre_coverage"] for x in labels]))
        for name in ("N","V","NN"):
            m=s["methods"][name]
            assert m["strict"] == sum(x["methods"][name]["strict"] for x in positives)
            assert m["correct_accepts"] == sum(x["methods"][name]["correct_accepted"] for x in positives)
            assert m["incorrect_accepts"] == sum(x["methods"][name]["incorrect_accepted"] for x in labels)
            assert m["confuser_accepts"] == sum(x["methods"][name]["accepted"] for x in labels if x["stratum"]=="confuser")
            assert m["ordinary_strict"] == sum(x["methods"][name]["strict"] for x in positives if x["stratum"]=="ordinary")
            close(m["clipped_error"],np.mean([x["methods"][name]["clipped_error"] for x in positives]))
        assert s["strict_gains"] == [x["pair"] for x in positives if x["methods"]["V"]["strict"] and not x["methods"]["N"]["strict"]]
        assert s["strict_losses"] == [x["pair"] for x in positives if x["methods"]["N"]["strict"] and not x["methods"]["V"]["strict"]]
        assert s["recovered_unavailable"] == [x["pair"] for x in positives if x["native_K4_unavailable"] and x["methods"]["V"]["strict"]]
        assert s["newly_incorrect_accepts"] == [x["pair"] for x in labels if x["methods"]["V"]["incorrect_accepted"] and not x["methods"]["N"]["incorrect_accepted"]]
        assert s["new_correct_accepts"] == [x["pair"] for x in positives if x["methods"]["V"]["correct_accepted"] and not x["methods"]["N"]["correct_accepted"]]
        assert s["lost_correct_accepts"] == [x["pair"] for x in positives if x["methods"]["N"]["correct_accepted"] and not x["methods"]["V"]["correct_accepted"]]
        assert s["ordinary_strict_losses"] == [x["pair"] for x in positives if x["stratum"]=="ordinary" and x["methods"]["N"]["strict"] and not x["methods"]["V"]["strict"]]
        checks += 1
    a,b=summary["sequences"]["08"],summary["sequences"]["00"]
    av,an,ann=(a["methods"][x] for x in ("V","N","NN"))
    bv,bn=(b["methods"][x] for x in ("V","N"))
    conditions={
        "coverage":a["coverage_ge_0p10"]>=90 and b["coverage_ge_0p10"]>=90,
        "08_recovery":len(a["recovered_unavailable"])>=5 and av["strict"]-an["strict"]>=5,
        "08_accept_safety":av["correct_accepts"]-an["correct_accepts"]>=2 and not a["newly_incorrect_accepts"],
        "00_accept_safety":len(b["lost_correct_accepts"])<=1 and not b["newly_incorrect_accepts"],
        "strict_regressions":bv["strict"]-bn["strict"]>=-2 and len(a["ordinary_strict_losses"])<=1 and len(b["ordinary_strict_losses"])<=1,
        "visibility_vs_nn":av["strict"]-ann["strict"]>=3 and av["correct_accepts"]-ann["correct_accepts"]>=1,
        "cost":seal["wall_s"]<=1800 and seal["peak_rss_gib"]<=4 and sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())<=1024**3,
    }
    assert summary["conditions"] == conditions
    assert summary["decision"] == ("RAY_INFORMATION_SIGNAL" if all(conditions.values()) else "NO_RAY_INFORMATION_SIGNAL")
    checks += 2
    output={"passed":True,"checks":checks,"decision":summary["decision"],"bank_sha256":seal["sha256"],
            "independent_candidate_spotchecks":8*27}
    with (BASE / "validation.json").open("x",encoding="utf-8") as f:
        json.dump(output,f,indent=2); f.write("\n")
    print("V0 validation passed",checks,"checks",flush=True)


if __name__ == "__main__":
    main()
