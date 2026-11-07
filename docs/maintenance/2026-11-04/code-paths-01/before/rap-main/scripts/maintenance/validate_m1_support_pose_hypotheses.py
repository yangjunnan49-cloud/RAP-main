"""Independent validator for the M1 transported multiview pose bank."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
BASE = MAIN / "docs/maintenance/2026-09-29/m1-support-pose-hypotheses-01"
GT = {"00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def metric(candidate, truth):
    relative = np.linalg.solve(truth, candidate)
    t = float(np.linalg.norm(relative[:3, 3]))
    r = float(np.degrees(np.arccos(np.clip((np.trace(relative[:3, :3])-1)/2, -1, 1))))
    return t, r


def validate():
    frozen = read(BASE / "freeze.json")
    checks = 0
    for name, digest in frozen["files"].items():
        assert sha(Path(name)) == digest, name
        checks += 1
    seal = read(BASE / "bank_seal.json")
    assert sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 300 and seal["artifact_bytes"] <= 100*2**20
    bank, outcomes, summary = [read(BASE / f) for f in ("bank.json", "outcomes.json", "summary.json")]
    assert len(bank) == len(outcomes) == 200 and summary["bank_sha256"] == seal["sha256"]
    assert frozen["pairs"] == {s: [r["key"] for r in read(F2 / f"inputs_{s}.json")]
                                for s in ("00", "08")}
    gts = {s: np.load(GT[s], allow_pickle=False) for s in ("00", "08")}
    labels = {s: read(F2 / s / "evaluator_only_decisions.json") for s in ("00", "08")}
    cohort = [(s, row) for s in ("00", "08") for row in read(F2 / f"inputs_{s}.json")]
    assert len(cohort) == 200
    for index, ((seq, row), entry, outcome) in enumerate(zip(cohort, bank, outcomes)):
        pair = row["key"]
        assert entry["sequence"] == outcome["sequence"] == seq
        assert entry["pair"] == outcome["pair"] == pair
        assert sha(Path(entry["file"])) == entry["sha256"]
        with np.load(entry["file"], allow_pickle=False) as z:
            saved = z["candidates"]
        assert saved.shape == (4, 3, 3, 4, 4) and np.isfinite(saved).all()
        motions = np.asarray(row["motions"], dtype=np.float64)
        for k in range(4):
            with np.load(F2 / seq / pair / f"N{k}.npz", allow_pickle=False) as z:
                poses, native = z["raw_poses"], z["T"]
            assert poses.shape == motions.shape == (6, 4, 4)
            target = [poses[a] @ np.linalg.solve(motions[a], np.eye(4)) for a in range(3)]
            source = [poses[3+b] @ np.linalg.solve(motions[3+b], np.eye(4)) for b in range(3)]
            for a in range(3):
                for b in range(3):
                    derived = np.linalg.solve(target[a], source[b])
                    assert np.max(np.abs(derived-saved[k, a, b])) <= 1e-10
                    assert np.max(np.abs(saved[k, a, b, 3]-[0, 0, 0, 1])) <= 1e-8
                    checks += 2
            assert np.max(np.abs(saved[k, 0, 0]-native)) <= 1e-10
            checks += 1
        label = labels[seq][index % 100]
        assert pair == f'{seq}_{label["source_i"]}_{label["source_j"]}'
        truth = np.linalg.solve(gts[seq][label["source_i"]], gts[seq][label["source_j"]])
        errors = np.asarray([[metric(saved[k, a, b], truth) for a in range(3) for b in range(3)]
                             for k in range(4)])
        strict = (errors[:, :, 0] <= 1) & (errors[:, :, 1] <= 5)
        interior = (errors[:, :, 0] <= .8) & (errors[:, :, 1] <= 4)
        native = bool(strict[:, 0].any())
        assert native == bool(label["methods"]["N-OR4"]["strict"])
        assert outcome["stratum"] == label["stratum"] and outcome["native_available"] == native
        assert outcome["any_support_strict"] == bool(strict[:, 1:].any())
        assert outcome["any_support_interior"] == bool(interior[:, 1:].any())
        assert outcome["all_oracle_strict"] == bool(strict.any())
        assert outcome["strict_candidates"] == int(strict.sum())
        assert abs(outcome["best_translation_m"]-float(errors[:, :, 0].min())) <= 1e-10
        assert abs(outcome["best_rotation_deg"]-float(errors[:, :, 1].min())) <= 1e-5
        checks += 10
    assert sum(Path(r["file"]).stat().st_size for r in bank) == seal["artifact_bytes"]
    groups = {}
    for seq in ("00", "08"):
        for available in (False, True):
            items = [r for r in outcomes if r["sequence"] == seq and r["stratum"] != "confuser"
                     and r["native_available"] == available]
            groups[f"{seq}_{'available' if available else 'unavailable'}"] = {
                "pairs": len(items), "support_strict": sum(r["any_support_strict"] for r in items),
                "support_interior": sum(r["any_support_interior"] for r in items),
                "all_oracle_strict": sum(r["all_oracle_strict"] for r in items)}
        for stratum in ("ordinary", "confuser", "low_overlap", "ambiguous_positive"):
            items = [r for r in outcomes if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = {"pairs": len(items),
                "native_oracle_strict": sum(r["native_available"] for r in items),
                "all_oracle_strict": sum(r["all_oracle_strict"] for r in items)}
    assert groups == summary["groups"]
    primary = [r for r in outcomes if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_available"]]
    n = sum(r["any_support_strict"] for r in primary)
    m = sum(r["any_support_interior"] for r in primary)
    assert len(primary) == summary["primary_pairs"] == 41
    assert n == summary["primary_new_strict"] and m == summary["primary_new_interior"]
    decision = "SUPPORT_HYPOTHESIS_HEADROOM" if n >= 5 and m >= 3 else "NO_SUPPORT_HYPOTHESIS_HEADROOM"
    assert decision == summary["decision"]
    checks += 15
    with (BASE / "validation.json").open("x", encoding="utf-8") as f:
        json.dump({"passed": True, "checks": checks, "decision": decision,
                   "bank_sha256": seal["sha256"]}, f, indent=2)
        f.write("\n")
    (BASE / "INCOMPLETE").unlink()
    print("M1 validation passed", checks, "checks", flush=True)


if __name__ == "__main__":
    validate()
