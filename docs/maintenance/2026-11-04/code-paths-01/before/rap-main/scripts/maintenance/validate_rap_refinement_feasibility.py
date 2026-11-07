"""Independent identity, pose, label and decision audit for R0."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np


MAIN = Path(__file__).resolve().parents[2]
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
BASE = MAIN / "docs/maintenance/2026-09-27/rap-refinement-feasibility-01"
GT = {"00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}
sys.path[:0] = [str(MAIN.parent / "RAP-SLAM")]
from rap_slam.measurement import transform_label, rotation_validity  # noqa: E402


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    assert (BASE / "INCOMPLETE").exists()
    frozen = read(BASE / "freeze.json")
    for name, expected in frozen["files"].items():
        assert sha256(Path(name)) == expected, f"frozen file changed: {name}"
    seal = read(BASE / "bank_seal.json")
    assert sha256(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 1800 and seal["peak_rss_gib"] <= 4
    bank = read(BASE / "bank.json")
    outcomes = read(BASE / "outcomes.json")
    summary = read(BASE / "summary.json")
    assert len(bank) == len(outcomes) == 200
    checks = 0
    for seq in ("00", "08"):
        source = read(F2 / seq / "records.json")
        decisions = read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        rows = [r for r in bank if r["sequence"] == seq]
        reported = [r for r in outcomes if r["sequence"] == seq]
        assert len(rows) == len(reported) == len(decisions) == 100
        assert {r["pair"] for r in rows} == {f"{seq}_{r['source_i']}_{r['source_j']}" for r in decisions}
        for record, outcome, decision in zip(rows, reported, decisions):
            pair = f"{seq}_{decision['source_i']}_{decision['source_j']}"
            assert record["pair"] == outcome["pair"] == pair
            choices = [r for r in source if r["pair"] == pair and r["arm"] == "N" and r["valid"]]
            assert len(choices) == 4
            winner = min(choices, key=lambda r: (r["rigidity_rmse_m"], r["generation"]))
            assert winner["generation"] == record["generation"] == decision["methods"]["N"]["generation"]
            np.testing.assert_array_equal(winner["T"], record["initial_T"])
            pose = np.asarray(record["refined_T"], dtype=float)
            assert rotation_validity(pose, 1e-8)["valid"]
            assert np.isfinite(pose).all() and record["iterations"] <= 30
            assert 0 <= record["correspondences"] <= 2000
            truth = np.linalg.inv(gt[decision["source_i"]]) @ gt[decision["source_j"]]
            label = transform_label(pose, truth)
            rte, rre = label["gt_translation_error_m"], label["gt_rotation_error_deg"]
            assert abs(rte - outcome["refined_RTE_m"]) < 1e-8
            assert abs(rre - outcome["refined_RRE_deg"]) < 1e-8
            assert outcome["refined_strict"] == (rte <= 1 and rre <= 5)
            assert abs(outcome["refined_clipped_error"] - min(5, max(rte, rre / 5))) < 1e-8
            assert outcome["native_strict"] == decision["methods"]["N"]["strict"]
            assert outcome["stratum"] == decision["stratum"]
            checks += 1
        positives = [r for r in reported if r["stratum"] != "confuser"]
        assert len(positives) == 75
        stats = summary["sequences"][seq]
        gained = [r["pair"] for r in positives if r["refined_strict"] and not r["native_strict"]]
        lost = [r["pair"] for r in positives if r["native_strict"] and not r["refined_strict"]]
        assert gained == stats["strict_gains"] and lost == stats["strict_losses"]
        assert sum(r["native_strict"] for r in positives) == stats["native_successes"]
        assert sum(r["refined_strict"] for r in positives) == stats["refined_successes"]
        assert abs(float(np.mean([r["refined_clipped_error"] for r in positives])) - stats["refined_clipped_error"]) < 1e-12
        assert abs(float(np.mean([r["native_clipped_error"] for r in positives])) - stats["native_clipped_error"]) < 1e-12
        checks += 6
    a, b = summary["sequences"]["08"], summary["sequences"]["00"]
    signal = (a["refined_successes"] - a["native_successes"] >= 3 and
              a["refined_clipped_error"] <= .95 * a["native_clipped_error"] and
              len(a["strict_losses"]) <= 1 and len(b["strict_losses"]) <= 1)
    expected = "LOCAL_REFINEMENT_FEASIBILITY_SIGNAL" if signal else "NO_LOCAL_REFINEMENT_FEASIBILITY_SIGNAL"
    assert summary["decision"] == expected
    artifact_bytes = sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())
    assert artifact_bytes <= 2 * 1024**3
    result = {"passed": True, "checks": checks + 2, "decision": expected,
              "bank_sha256": seal["sha256"], "wall_s": seal["wall_s"],
              "peak_rss_gib": seal["peak_rss_gib"], "artifact_bytes": artifact_bytes,
              "validator_sha256": sha256(Path(__file__))}
    with (BASE / "validation.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    (BASE / "INCOMPLETE").unlink()
    print(expected, flush=True)


if __name__ == "__main__":
    main()
