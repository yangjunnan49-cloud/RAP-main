"""Independent C2 N0 acceptance correction and decision validation."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import c2_feature_channel as c2

BASE, F2, GT = c2.BASE, c2.F2, c2.GT


def strict(pose, truth):
    delta = np.linalg.inv(truth) @ pose
    t = float(np.linalg.norm(delta[:3, 3]))
    r = float(np.degrees(np.arccos(np.clip((np.trace(delta[:3, :3]) - 1) / 2, -1, 1))))
    return t <= 1 and r <= 5


def validate():
    checks = 0
    c2.verify()
    assert g0.read(BASE / "validation_v2.json")["passed"]
    for name, digest in g0.read(BASE / "amendment_02_freeze.json")["files"].items():
        assert g0.sha(Path(name)) == digest, name
        checks += 1
    bank = g0.read(BASE / "bank.json")
    prior = g0.read(BASE / "outcomes.json")
    corrected = g0.read(BASE / "outcomes_v3.json")
    summary = g0.read(BASE / "summary_v3.json")
    assert len(bank) == len(prior) == len(corrected) == 28
    groups = {}
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        labels = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                  g0.read(F2 / seq / "evaluator_only_decisions.json")}
        gates = g0.read(F2 / seq / "gates.json")
        for original, old, new in zip((r for r in bank if r["sequence"] == seq),
                                      (r for r in prior if r["sequence"] == seq),
                                      (r for r in corrected if r["sequence"] == seq)):
            pair = original["pair"]
            assert pair == old["pair"] == new["pair"]
            assert all(old[key] == new[key] for key in old if key not in
                       ("true_accepted", "shuffled_accepted"))
            truth_row = labels[pair]
            truth = np.linalg.inv(gt[truth_row["source_i"]]) @ gt[truth_row["source_j"]]
            assert new["true_strict"] == strict(np.asarray(original["pose_true"]), truth)
            assert new["shuffled_strict"] == strict(np.asarray(original["pose_q"]), truth)
            gate = gates[pair]["N"]["0"]
            target_accept = gate["overlap_ratio"] >= .7 and gate["mean_dist"] <= 2.5
            assert gate["accepted"] == target_accept == new["true_accepted"]
            assert new["shuffled_accepted"] == original["accepted"]
            assert new["stratum"] == truth_row["stratum"]
            groups.setdefault(f'{seq}_{new["stratum"]}', []).append(new)
            checks += 8
    ordinary = [r for r in corrected if r["stratum"] == "ordinary"]
    assert len(ordinary) == summary["ordinary_pairs"] == 7
    assert summary["ordinary_raw_responses"] == sum(r["raw_response"] for r in ordinary)
    assert summary["ordinary_pose_responses"] == sum(r["pose_response"] for r in ordinary)
    decision = ("POSE_LEVEL_FEATURE_RELIANCE" if summary["ordinary_pose_responses"] >= 6 else
                "FLOW_ONLY_FEATURE_RELIANCE" if summary["ordinary_raw_responses"] >= 6 else
                "NO_MATERIAL_FEATURE_RELIANCE")
    assert summary["decision"] == decision
    assert summary["amendments"] == ["AMENDMENT_01", "AMENDMENT_02"]
    assert summary["bank_sha256"] == g0.read(BASE / "bank_seal.json")["sha256"]
    for name, reported in summary["groups"].items():
        items = groups[name]
        assert reported["pairs"] == len(items)
        for aggregate, field in (("raw_responses", "raw_response"),
                                 ("pose_responses", "pose_response"),
                                 ("true_strict", "true_strict"),
                                 ("shuffled_strict", "shuffled_strict"),
                                 ("true_accepted", "true_accepted"),
                                 ("shuffled_accepted", "shuffled_accepted")):
            assert reported[aggregate] == sum(item[field] for item in items)
            checks += 1
    g0.save_new(BASE / "validation_v3.json", {"passed": True, "checks": checks,
                                            "decision": decision,
                                            "bank_sha256": summary["bank_sha256"],
                                            "corrected": "generation-0 acceptance binding"})
    print("C2 v3 acceptance validation", checks, decision, flush=True)


if __name__ == "__main__":
    validate()
