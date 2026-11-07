"""Evaluator-only C2 N0 acceptance correction; preserves old outputs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import c2_feature_channel as c2

BASE, F2 = c2.BASE, c2.F2


def correct():
    c2.verify()
    for name, digest in g0.read(BASE / "amendment_02_freeze.json")["files"].items():
        assert g0.sha(Path(name)) == digest, name
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    bank = g0.read(BASE / "bank.json")
    old = g0.read(BASE / "outcomes.json")
    assert len(bank) == len(old) == 28
    rows = []
    for entry, item in zip(bank, old):
        assert entry["pair"] == item["pair"]
        seq, pair = item["sequence"], item["pair"]
        gate = g0.read(F2 / seq / "gates.json")[pair]["N"]["0"]
        assert gate["accepted"] == (gate["overlap_ratio"] >= .7 and gate["mean_dist"] <= 2.5)
        revised = dict(item)
        revised["true_accepted"] = bool(gate["accepted"])
        revised["shuffled_accepted"] = bool(entry["accepted"])
        rows.append(revised)
    g0.save_new(BASE / "outcomes_v3.json", rows)
    ordinary = [r for r in rows if r["stratum"] == "ordinary"]
    assert len(ordinary) == 7
    raw_count = sum(r["raw_response"] for r in ordinary)
    pose_count = sum(r["pose_response"] for r in ordinary)
    decision = ("POSE_LEVEL_FEATURE_RELIANCE" if pose_count >= 6 else
                "FLOW_ONLY_FEATURE_RELIANCE" if raw_count >= 6 else
                "NO_MATERIAL_FEATURE_RELIANCE")
    groups = {}
    for seq in ("00", "08"):
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            subset = [r for r in rows if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = {
                "pairs": len(subset), "raw_responses": sum(r["raw_response"] for r in subset),
                "pose_responses": sum(r["pose_response"] for r in subset),
                "true_strict": sum(r["true_strict"] for r in subset),
                "shuffled_strict": sum(r["shuffled_strict"] for r in subset),
                "true_accepted": sum(r["true_accepted"] for r in subset),
                "shuffled_accepted": sum(r["shuffled_accepted"] for r in subset),
            }
    g0.save_new(BASE / "summary_v3.json", {
        "scope": "fixed small observed-development feature-channel intervention",
        "decision": decision, "ordinary_pairs": 7,
        "ordinary_raw_responses": raw_count,
        "ordinary_pose_responses": pose_count,
        "groups": groups, "bank_sha256": seal["sha256"],
        "amendments": ["AMENDMENT_01", "AMENDMENT_02"],
    })
    print("C2 corrected acceptance, decision", decision, flush=True)


if __name__ == "__main__":
    correct()
