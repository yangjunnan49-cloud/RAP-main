"""C6 fixed causal transport bank and later evaluator; no RAP inference."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
BASE = MAIN / "docs/maintenance/2026-09-29/c6-causal-pose-transport-01"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
DATA = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_new(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def files():
    paths = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_c6_causal_pose_transport.py",
             F2 / "validation.json"]
    for seq in ("00", "08"):
        paths += [F2 / f"inputs_{seq}.json", F2 / seq / "records.json",
                  F2 / seq / "gates.json", F2 / seq / "evaluator_only_decisions.json",
                  DATA[seq] / "odom.npy", DATA[seq] / "evaluator_gt.npy"]
    return paths


def verify():
    for name, digest in read(BASE / "freeze.json")["files"].items():
        assert sha(Path(name)) == digest, name


def freeze():
    assert read(F2 / "validation.json")["passed"]
    assert not (BASE / "freeze.json").exists()
    p = files()
    assert len(p) == len(set(p)) and all(x.is_file() for x in p)
    save_new(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
                                    "files": {str(x): sha(x) for x in p}})


def selected(seq):
    records = read(F2 / seq / "records.json")
    gates = read(F2 / seq / "gates.json")
    groups = {}
    for row in records:
        if row["arm"] == "N":
            groups.setdefault(row["pair"], []).append(row)
    out = {}
    for key, group in groups.items():
        good = [r for r in group if r["valid"]]
        assert len(good) == 4
        best = min(good, key=lambda r: (r["rigidity_rmse_m"], r["generation"]))
        out[key] = {"T": np.asarray(best["T"], dtype=np.float64),
                    "generation": best["generation"],
                    "accepted": gates[key]["N"][str(best["generation"])]["accepted"]}
    assert len(out) == 100
    return out


def valid(T):
    return (T.shape == (4, 4) and np.isfinite(T).all() and
            np.max(np.abs(T[3] - [0, 0, 0, 1])) < 1e-7 and
            np.max(np.abs(T[:3, :3].T @ T[:3, :3] - np.eye(3))) < 1e-3 and
            abs(np.linalg.det(T[:3, :3]) - 1) < 1e-3)


def bank():
    verify()
    start = time.monotonic()
    rows = []
    for seq in ("00", "08"):
        inputs = read(F2 / f"inputs_{seq}.json")
        assert len(inputs) == 100
        chosen = selected(seq)
        odom = np.load(DATA[seq] / "odom.npy", allow_pickle=False)
        assert odom.ndim == 3 and odom.shape[1:] == (4, 4)
        for q in inputs:
            i, j = q["source_i"], q["source_j"]
            assert q["key"] == f"{seq}_{i}_{j}" and valid(odom[i]) and valid(odom[j])
            donors = [d for d in inputs if chosen[d["key"]]["accepted"] and
                      0 < i-d["source_i"] <= 50 and 0 < j-d["source_j"] <= 50]
            if not donors:
                rows.append({"pair": q["key"], "donor": None})
                continue
            d = min(donors, key=lambda x: (max(i-x["source_i"], j-x["source_j"]),
                                         i-x["source_i"]+j-x["source_j"],
                                         x["source_i"], x["source_j"]))
            a, b = d["source_i"], d["source_j"]
            T = np.linalg.inv(odom[i]) @ odom[a] @ chosen[d["key"]]["T"] @ np.linalg.inv(odom[b]) @ odom[j]
            C = np.linalg.inv(odom[i]) @ odom[j]
            assert valid(T) and valid(C)
            rows.append({"pair": q["key"], "donor": d["key"],
                         "donor_generation": chosen[d["key"]]["generation"],
                         "T_transport": T.tolist(), "T_odom": C.tolist()})
    assert len(rows) == 200
    assert {s: sum(r["donor"] is not None for r in rows if r["pair"].startswith(s+"_"))
            for s in ("00", "08")} == {"00": 22, "08": 15}
    save_new(BASE / "bank.json", rows)
    save_new(BASE / "bank_seal.json", {"sha256": sha(BASE / "bank.json"),
                                       "rows": len(rows), "wall_s": time.monotonic()-start,
                                       "gt_parsed": False})


def pose_error(T, G):
    E = np.linalg.inv(G) @ T
    R = E[:3, :3]
    sine = np.linalg.norm([R[2,1]-R[1,2], R[0,2]-R[2,0], R[1,0]-R[0,1]]) / 2
    deg = float(np.degrees(np.arctan2(sine, np.clip((np.trace(R)-1)/2, -1, 1))))
    return float(np.linalg.norm(E[:3, 3])), deg


def evaluate():
    verify()
    assert sha(BASE / "bank.json") == read(BASE / "bank_seal.json")["sha256"]
    bankrows = read(BASE / "bank.json")
    out = []
    for seq in ("00", "08"):
        gt = np.load(DATA[seq] / "evaluator_gt.npy", allow_pickle=False)
        labels = {f"{seq}_{r['source_i']}_{r['source_j']}": r for r in
                  read(F2 / seq / "evaluator_only_decisions.json")}
        for row in (r for r in bankrows if r["pair"].startswith(seq+"_")):
            key = row["pair"]
            lab = labels[key]
            if row["donor"] is None:
                out.append({"pair": key, "covered": False, "stratum": lab["stratum"],
                            "native_oracle_strict": lab["methods"]["N-OR4"]["strict"]})
                continue
            _, i, j = key.split("_")
            G = np.linalg.inv(gt[int(i)]) @ gt[int(j)]
            t, a = pose_error(np.asarray(row["T_transport"]), G)
            ct, ca = pose_error(np.asarray(row["T_odom"]), G)
            donor = labels[row["donor"]]
            out.append({"pair": key, "covered": True, "stratum": lab["stratum"],
                        "native_oracle_strict": lab["methods"]["N-OR4"]["strict"],
                        "donor": row["donor"], "donor_strict": donor["methods"]["N"]["strict"],
                        "transport_rte_m": t, "transport_rre_deg": a,
                        "transport_strict": t <= 1 and a <= 5,
                        "odom_rte_m": ct, "odom_rre_deg": ca,
                        "odom_strict": ct <= 1 and ca <= 5})
    save_new(BASE / "outcomes.json", out)
    hard = [r for r in out if r["pair"].startswith("08_") and
            r["stratum"] != "confuser" and not r["native_oracle_strict"]]
    exposed = [r for r in hard if r["covered"]]
    assert len(hard) == 41 and len(exposed) == 8
    transport = sum(r["transport_strict"] for r in exposed)
    control = sum(r["odom_strict"] for r in exposed)
    decision = "CANDIDATE_INFORMATION_SIGNAL" if transport >= 2 and transport-control >= 2 else "NO_CAUSAL_TRANSPORT_SCREEN_SIGNAL"
    summary = {"decision": decision, "hard08_total": len(hard), "hard08_covered": len(exposed),
               "hard08_transport_strict": transport, "hard08_odom_strict": control,
               "by_sequence": {s: {"covered": sum(r["covered"] for r in out if r["pair"].startswith(s+"_")),
                                  "transport_strict": sum(r.get("transport_strict", False) for r in out if r["pair"].startswith(s+"_")),
                                  "odom_strict": sum(r.get("odom_strict", False) for r in out if r["pair"].startswith(s+"_"))}
                               for s in ("00", "08")}}
    save_new(BASE / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    {"freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
