"""Read-only, post-hoc partition of the validated F2 evaluator rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
F2 = ROOT / "docs/maintenance/2026-09-27/f2-structured-dev-01"
OUT = ROOT / "docs/maintenance/2026-09-27/f2-postmortem-01"
ARMS = ("N", "S", "P")
STRATA = ("confuser", "ambiguous_positive", "low_overlap", "ordinary")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def key(row: dict) -> str:
    return f"{row['sequence']}_{row['source_i']}_{row['source_j']}"


def partition(row: dict, arm: str) -> str:
    sel = row["methods"][arm]
    oracle = row["methods"][f"{arm}-OR4"]
    if sel["strict"]:
        return "correct_accepted" if sel["accepted"] else "correct_rejected"
    return "selection_miss" if oracle["strict"] else "proposal_unavailable"


def gate_reason(gate: dict) -> str:
    overlap_fails = gate["overlap_ratio"] < 0.7
    distance_fails = gate["mean_dist"] > 2.5
    if overlap_fails and distance_fails:
        return "both"
    if overlap_fails:
        return "overlap_only"
    if distance_fails:
        return "distance_only"
    raise AssertionError("rejected pose passes both common gate conditions")


def analyze_sequence(seq: str) -> dict:
    rows = read(F2 / seq / "evaluator_only_decisions.json")
    gates = read(F2 / seq / "gates.json")
    metrics = read(F2 / seq / "metrics.json")
    assert len(rows) == 100
    assert [r["sequence"] for r in rows] == [seq] * 100
    assert Counter(r["stratum"] for r in rows) == {s: 25 for s in STRATA}
    keys = [key(r) for r in rows]
    assert len(set(keys)) == 100
    assert set(keys) == set(gates)
    positives = [r for r in rows if r["stratum"] != "confuser"]

    result = {"sequence": seq, "arms": {}, "paired": {}}
    for arm in ARMS:
        cats = Counter()
        by_stratum = {}
        gate_failures = Counter()
        incorrect = []
        incorrect_with_candidate = []
        category_pairs = {name: [] for name in (
            "correct_accepted", "correct_rejected", "selection_miss", "proposal_unavailable"
        )}
        for r in rows:
            p = key(r)
            sel = r["methods"][arm]
            oracle = r["methods"][f"{arm}-OR4"]
            assert not sel["failed"] and not oracle["failed"]
            assert not sel["strict"] or oracle["strict"]
            assert sel["incorrect_accepted"] == (sel["accepted"] and not sel["strict"])
            gate = gates[p][arm][str(sel["generation"])]
            assert gate["accepted"] == sel["accepted"]
            assert gate["accepted"] == (gate["overlap_ratio"] >= 0.7 and gate["mean_dist"] <= 2.5)
            if sel["incorrect_accepted"]:
                incorrect.append(p)
                if r["stratum"] != "confuser" and oracle["strict"]:
                    incorrect_with_candidate.append(p)
            if r["stratum"] == "confuser":
                continue
            cat = partition(r, arm)
            cats[cat] += 1
            category_pairs[cat].append(p)
            if cat == "correct_rejected":
                gate_failures[gate_reason(gate)] += 1
        assert sum(cats.values()) == 75
        assert cats["correct_accepted"] + cats["correct_rejected"] == metrics["overall"][arm]["strict_positive_successes"]
        assert cats["correct_accepted"] == metrics["overall"][arm]["correct_positive_accepts"]
        assert len(incorrect) == metrics["overall"][arm]["incorrect_accepted"]
        assert sum(r["methods"][arm]["accepted"] for r in rows if r["stratum"] == "confuser") == metrics["overall"][arm]["accepted_confusers"]
        assert sum(gate_failures.values()) == cats["correct_rejected"]
        for stratum in STRATA[1:]:
            sub = [r for r in positives if r["stratum"] == stratum]
            counts = Counter(partition(r, arm) for r in sub)
            assert sum(counts.values()) == 25
            assert counts["correct_accepted"] + counts["correct_rejected"] == metrics["by_stratum"][stratum][arm]["strict_positive_successes"]
            by_stratum[stratum] = dict(counts)
        result["arms"][arm] = {
            "partition": dict(cats),
            "gate_failures_on_correct_rejections": dict(gate_failures),
            "incorrect_accepts": len(incorrect),
            "incorrect_accepts_with_correct_candidate": len(incorrect_with_candidate),
            "incorrect_accept_pairs": incorrect,
            "incorrect_accepts_with_correct_candidate_pairs": incorrect_with_candidate,
            "by_stratum": by_stratum,
            "category_pairs": category_pairs,
        }

    for arm in ("S", "P"):
        paired = {}
        for name, predicate in (
            ("strict", lambda m: m["strict"]),
            ("correct_accept", lambda m: m["strict"] and m["accepted"]),
            ("incorrect_accept", lambda m: m["incorrect_accepted"]),
        ):
            gained = []
            lost = []
            for r in rows if name == "incorrect_accept" else positives:
                a = bool(predicate(r["methods"]["N"]))
                b = bool(predicate(r["methods"][arm]))
                if b and not a:
                    gained.append(key(r))
                if a and not b:
                    lost.append(key(r))
            paired[name] = {"gained": gained, "lost": lost}
        result["paired"][f"N_to_{arm}"] = paired
    return result


def main() -> None:
    freeze = read(OUT / "freeze.json")
    for rel, expected in freeze["sha256"].items():
        assert sha256(ROOT / rel) == expected, f"hash changed: {rel}"
    assert read(F2 / "decision.json")["decision"] == "NO_DEVELOPMENT_MECHANISM_SIGNAL"
    assert read(F2 / "validation.json")["passed"] is True
    result = {"scope": "post-hoc observed development, no method selection", "sequences": {}}
    for seq in ("00", "08"):
        result["sequences"][seq] = analyze_sequence(seq)
    (OUT / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
