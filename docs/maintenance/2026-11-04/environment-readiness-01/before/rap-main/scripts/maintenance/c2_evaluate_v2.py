"""C2 fixed-index composition amendment; no new generation or label change."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import c2_feature_channel as c2

BASE = c2.BASE


def evaluate():
    c2.verify()
    amendment = g0.read(BASE / "amendment_freeze.json")
    for name, digest in amendment["files"].items():
        assert g0.sha(Path(name)) == digest, name
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    bank = g0.read(BASE / "bank.json")
    rows = g0.read(BASE / "outcomes.json")
    assert len(bank) == len(rows) == 28
    assert all(a["pair"] == b["pair"] for a, b in zip(bank, rows))
    ordinary = [r for r in rows if r["stratum"] == "ordinary"]
    assert len(ordinary) == 7
    pose_count = sum(r["pose_response"] for r in ordinary)
    raw_count = sum(r["raw_response"] for r in ordinary)
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
    g0.save_new(BASE / "summary.json", {
        "scope": "fixed small observed-development feature-channel intervention",
        "decision": decision, "ordinary_pairs": len(ordinary),
        "ordinary_raw_responses": raw_count,
        "ordinary_pose_responses": pose_count, "groups": groups,
        "bank_sha256": seal["sha256"],
        "amendment": "AMENDMENT_01",
    })
    (BASE / "INCOMPLETE").unlink()
    print("C2 amended decision", decision, "ordinary", len(ordinary),
          "pose", pose_count, "raw", raw_count, flush=True)


if __name__ == "__main__":
    evaluate()
