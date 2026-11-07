"""Independent C6 identity, causal-policy, pose and decision recount."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "docs/maintenance/2026-09-29/c6-causal-pose-transport-01"
F2 = ROOT / "docs/maintenance/2026-09-27/f2-structured-dev-01"
ODOM = {"00": ROOT / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/odom.npy",
        "08": ROOT / "docs/maintenance/2026-09-14/support-control-01/data/08/odom.npy"}
GT = {"00": ROOT / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": ROOT / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}


def rd(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                return h.hexdigest()
            h.update(b)


def err(T, G):
    D = np.linalg.solve(G, T)
    R = D[:3, :3]
    theta = np.degrees(np.arctan2(np.linalg.norm([R[2,1]-R[1,2], R[0,2]-R[2,0], R[1,0]-R[0,1]])/2,
                                      (np.trace(R)-1)/2))
    return float(np.linalg.norm(D[:3, 3])), float(theta)


def main():
    freeze = rd(RUN / "freeze.json")
    checks = 0
    for name, hashval in freeze["files"].items():
        assert digest(Path(name)) == hashval, name
        checks += 1
    bank = rd(RUN / "bank.json")
    assert digest(RUN / "bank.json") == rd(RUN / "bank_seal.json")["sha256"]
    assert len(bank) == 200
    checks += 2
    outcomes = rd(RUN / "outcomes.json")
    assert len(outcomes) == 200 and [x["pair"] for x in outcomes] == [x["pair"] for x in bank]
    checks += 1
    for seq in ("00", "08"):
        inp = rd(F2 / f"inputs_{seq}.json")
        bykey = {x["key"]: x for x in inp}
        records = rd(F2 / seq / "records.json")
        gate = rd(F2 / seq / "gates.json")
        winners = {}
        for r in records:
            if r["arm"] != "N" or not r["valid"]:
                continue
            k = r["pair"]
            if k not in winners or (r["rigidity_rmse_m"], r["generation"]) < (winners[k]["rigidity_rmse_m"], winners[k]["generation"]):
                winners[k] = r
        assert len(winners) == 100
        labels = {f"{seq}_{x['source_i']}_{x['source_j']}": x for x in rd(F2 / seq / "evaluator_only_decisions.json")}
        odom = np.load(ODOM[seq], allow_pickle=False)
        gt = np.load(GT[seq], allow_pickle=False)
        for row, result in zip((x for x in bank if x["pair"].startswith(seq+"_")),
                               (x for x in outcomes if x["pair"].startswith(seq+"_"))):
            q = bykey[row["pair"]]
            i, j = q["source_i"], q["source_j"]
            eligible = []
            for d in inp:
                a, b = d["source_i"], d["source_j"]
                wr = winners[d["key"]]
                if a < i and b < j and i-a <= 50 and j-b <= 50 and gate[d["key"]]["N"][str(wr["generation"])]["accepted"]:
                    eligible.append((max(i-a,j-b), i-a+j-b, a, b, d["key"]))
            winner = min(eligible)[-1] if eligible else None
            assert row["donor"] == winner
            assert result["covered"] == (winner is not None)
            assert result["native_oracle_strict"] == labels[row["pair"]]["methods"]["N-OR4"]["strict"]
            checks += 3
            if winner is None:
                continue
            d = bykey[winner]
            a, b = d["source_i"], d["source_j"]
            assert row["donor_generation"] == winners[winner]["generation"]
            T = np.linalg.solve(odom[i], odom[a] @ np.asarray(winners[winner]["T"]) @ np.linalg.solve(odom[b], odom[j]))
            C = np.linalg.solve(odom[i], odom[j])
            assert np.max(np.abs(T - row["T_transport"])) < 1e-8
            assert np.max(np.abs(C - row["T_odom"])) < 1e-8
            G = np.linalg.solve(gt[i], gt[j])
            for name, pose in (("transport", T), ("odom", C)):
                t, aerr = err(pose, G)
                assert abs(t-result[f"{name}_rte_m"]) < 1e-8
                assert abs(aerr-result[f"{name}_rre_deg"]) < 1e-8
                assert result[f"{name}_strict"] == (t <= 1 and aerr <= 5)
                checks += 3
            assert result["donor_strict"] == labels[winner]["methods"]["N"]["strict"]
            checks += 4
    hard = [r for r in outcomes if r["pair"].startswith("08_") and r["stratum"] != "confuser" and not r["native_oracle_strict"]]
    exposed = [r for r in hard if r["covered"]]
    s = rd(RUN / "summary.json")
    t = sum(x["transport_strict"] for x in exposed)
    c = sum(x["odom_strict"] for x in exposed)
    assert (len(hard), len(exposed), t, c) == (s["hard08_total"], s["hard08_covered"], s["hard08_transport_strict"], s["hard08_odom_strict"])
    assert s["decision"] == ("CANDIDATE_INFORMATION_SIGNAL" if t >= 2 and t-c >= 2 else "NO_CAUSAL_TRANSPORT_SCREEN_SIGNAL")
    checks += 2
    with (RUN / "validation.json").open("x", encoding="utf-8") as f:
        json.dump({"passed": True, "checks": checks, "bank_sha256": digest(RUN / "bank.json")}, f, indent=2)
        f.write("\n")
    print("C6 independent validation", checks, "checks")


if __name__ == "__main__":
    main()
