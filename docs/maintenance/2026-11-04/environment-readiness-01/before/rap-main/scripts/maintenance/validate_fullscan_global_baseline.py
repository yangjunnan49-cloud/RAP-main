"""Independent G1 full-scan identity, geometry, label and decision audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
BASE = MAIN / "docs/maintenance/2026-09-28/fullscan-global-baseline-01"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
GT = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy",
}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def close(a, b, tol=1e-8):
    assert abs(float(a) - float(b)) <= tol, (a, b)


def metric(pose, truth):
    err = np.linalg.inv(truth) @ pose
    r = err[:3, :3]
    sine = np.linalg.norm([r[2, 1] - r[1, 2], r[0, 2] - r[2, 0], r[1, 0] - r[0, 1]]) / 2
    angle = float(np.degrees(np.arctan2(sine, np.clip((np.trace(r) - 1) / 2, -1, 1))))
    return float(np.linalg.norm(err[:3, 3])), angle


def main():
    assert not (BASE / "validation.json").exists()
    checks = 0
    frozen = read(BASE / "freeze.json")
    for name, digest in frozen["files"].items():
        assert sha(Path(name)) == digest, name
        checks += 1
    assert sha(BASE / "bank.json") == read(BASE / "bank_seal.json")["sha256"]
    checks += 1
    assert not (BASE / "INCOMPLETE").exists()
    bank, outcomes, summary = (read(BASE / name) for name in ("bank.json", "outcomes.json", "summary.json"))
    assert len(bank) == len(outcomes) == 200
    checks += 1
    for seq in ("00", "08"):
        records = read(F2 / seq / "records.json")
        pair_order = list(dict.fromkeys(r["pair"] for r in records if r["arm"] == "N"))
        old = read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        rows = [r for r in bank if r["sequence"] == seq]
        labels = [r for r in outcomes if r["sequence"] == seq]
        assert len(pair_order) == len(old) == len(rows) == len(labels) == 100
        assert [r["pair"] for r in rows] == pair_order
        for row, lab, parent in zip(rows, labels, old):
            assert row["pair"] == lab["pair"] == f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            assert lab["stratum"] == parent["stratum"] and row["status"] == lab["status"]
            assert lab["native_strict"] == parent["methods"]["N"]["strict"]
            assert lab["native_K4_unavailable"] == (not parent["methods"]["N-OR4"]["strict"])
            close(lab["native_clipped_error"], parent["methods"]["N"]["clipped_error"])
            assert row["wall_s"] >= 0
            assert row["target_points"] > 2000 and row["source_points"] > 2000
            if row["status"] == "valid":
                t = np.asarray(row["T"])
                assert t.shape == (4, 4) and np.isfinite(t).all()
                assert np.max(np.abs(t[3] - [0, 0, 0, 1])) < 1e-8
                assert np.max(np.abs(t[:3, :3].T @ t[:3, :3] - np.eye(3))) < 1e-4
                assert abs(np.linalg.det(t[:3, :3]) - 1) < 1e-4
                truth = np.linalg.inv(gt[parent["source_i"]]) @ gt[parent["source_j"]]
                rte, rre = metric(t, truth)
                close(lab["RTE_m"], rte, 1e-6)
                close(lab["RRE_deg"], rre, 1e-5)
                assert lab["strict"] == (rte <= 1 and rre <= 5)
                close(lab["clipped_error"], min(5, max(rte, rre / 5)), 1e-6)
                assert row["rotation_inliers"] >= 0 and row["final_inliers"] >= 0
            else:
                assert row["status"] == "failed" and row["T"] is None
                assert not lab["strict"] and lab["RTE_m"] is None and lab["RRE_deg"] is None
                close(lab["clipped_error"], 5)
            checks += 1
        positives = [r for r in labels if r["stratum"] != "confuser"]
        assert len(positives) == 75 and len(labels) - len(positives) == 25
        result = summary["sequences"][seq]
        assert result["valid"] == sum(r["status"] == "valid" for r in rows)
        assert result["strict"] == sum(r["strict"] for r in positives)
        assert result["native_strict"] == sum(r["native_strict"] for r in positives)
        assert result["gains"] == [r["pair"] for r in positives if r["strict"] and not r["native_strict"]]
        assert result["losses"] == [r["pair"] for r in positives if r["native_strict"] and not r["strict"]]
        assert result["native_K4_unavailable"] == sum(r["native_K4_unavailable"] for r in positives)
        assert result["recovered_unavailable"] == [r["pair"] for r in positives if r["strict"] and r["native_K4_unavailable"]]
        close(result["clipped_error"], np.mean([r["clipped_error"] for r in positives]))
        close(result["native_clipped_error"], np.mean([r["native_clipped_error"] for r in positives]))
        for stratum in ("ambiguous_positive", "low_overlap", "ordinary"):
            assert result["by_stratum"][stratum] == {
                "strict": sum(r["strict"] for r in positives if r["stratum"] == stratum),
                "native": sum(r["native_strict"] for r in positives if r["stratum"] == stratum)}
        checks += 1
    a, b = summary["sequences"]["08"], summary["sequences"]["00"]
    signal = (len(a["recovered_unavailable"]) >= 5 and a["strict"] - a["native_strict"] >= 5 and
              a["clipped_error"] <= .95 * a["native_clipped_error"] and b["strict"] - b["native_strict"] >= -3)
    assert summary["decision"] == ("GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL" if signal else "NO_GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL")
    seal = read(BASE / "bank_seal.json")
    assert seal["wall_s"] <= 2700 and seal["peak_rss_gib"] <= 8
    artifact_bytes = sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())
    assert artifact_bytes <= 2 * 1024**3
    checks += 3
    output = {"passed": True, "checks": checks, "decision": summary["decision"],
              "bank_sha256": seal["sha256"], "artifact_bytes": artifact_bytes}
    with (BASE / "validation.json").open("x", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
    print("G1 validation passed", checks, "checks")


if __name__ == "__main__":
    main()
