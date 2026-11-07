"""M1 GT-free support pose bank and evaluator-only availability screen."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / "RAP-SLAM"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
BASE = MAIN / "docs/maintenance/2026-09-29/m1-support-pose-hypotheses-01"
GT = {"00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}


def rd(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def inputs():
    return {s: rd(F2 / f"inputs_{s}.json") for s in ("00", "08")}


def rigid(T):
    assert T.shape == (4, 4) and np.isfinite(T).all()
    assert np.max(np.abs(T[3]-[0, 0, 0, 1])) < 1e-8
    R = T[:3, :3]
    assert np.max(np.abs(R.T @ R-np.eye(3))) < 1e-4
    assert abs(np.linalg.det(R)-1) < 1e-4


def hypotheses(poses, motions):
    assert poses.shape == motions.shape == (6, 4, 4)
    for T in list(poses)+list(motions):
        rigid(T)
    assert np.array_equal(motions[0], np.eye(4)) and np.array_equal(motions[3], np.eye(4))
    anchor_est = np.asarray([poses[k] @ np.linalg.inv(motions[k]) for k in range(6)])
    proposals = np.asarray([[np.linalg.inv(anchor_est[a]) @ anchor_est[3+b]
                             for b in range(3)] for a in range(3)])
    assert proposals.shape == (3, 3, 4, 4)
    for T in proposals.reshape(-1, 4, 4):
        rigid(T)
    assert np.max(np.abs(proposals[0, 0]-(np.linalg.inv(poses[0]) @ poses[3]))) < 1e-10
    return proposals


def synthetic():
    def make(angle, t):
        c, s = np.cos(angle), np.sin(angle)
        T = np.eye(4)
        T[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
        T[:3, 3] = t
        return T
    visits = [make(.3, [1, 2, 3]), make(-.2, [8, -1, 2])]
    local = np.asarray([np.eye(4), make(.08, [2, 0, 0]), make(-.04, [4, 1, 0]),
                        np.eye(4), make(.05, [1, 2, 0]), make(-.03, [3, -1, 0])])
    poses = np.asarray([visits[0] @ local[k] if k < 3 else visits[1] @ local[k]
                        for k in range(6)])
    expected = np.linalg.inv(visits[0]) @ visits[1]
    assert np.max(np.abs(hypotheses(poses, local)-expected)) < 1e-12
    common = make(.27, [3, -2, 1])
    assert np.max(np.abs(hypotheses(common @ poses, local)-expected)) < 1e-12
    print("M1 synthetic passed", flush=True)


def frozen_files():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_m1_support_pose_hypotheses.py",
             SLAM / "rap_slam/structured_motion.py",
             SLAM / "scripts/structured_motion_dev.py",
             F2 / "validation.json", F2 / "freeze.json"]
    for seq, rows in inputs().items():
        files += [F2 / f"inputs_{seq}.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        for row in rows:
            files += [F2 / seq / row["key"] / f"N{k}.npz" for k in range(4)]
    return list(dict.fromkeys(files))


def freeze():
    synthetic()
    assert not (BASE / "freeze.json").exists()
    assert rd(F2 / "validation.json")["passed"]
    cohort = inputs()
    assert all(len(rows) == 100 for rows in cohort.values())
    files = frozen_files()
    assert all(p.is_file() for p in files)
    save(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": {s: [r["key"] for r in rows] for s, rows in cohort.items()},
        "files": {str(p): sha(p) for p in files},
        "caps": {"bank_wall_s": 300, "artifacts_bytes": 100*2**20},
    })
    print("M1 frozen", len(files), "identities", flush=True)


def verify():
    frozen = rd(BASE / "freeze.json")
    assert frozen["pairs"] == {s: [r["key"] for r in rows] for s, rows in inputs().items()}
    for name, digest in frozen["files"].items():
        assert sha(Path(name)) == digest, name


def bank():
    verify()
    assert not (BASE / "bank.json").exists()
    (BASE / "INCOMPLETE").write_text("M1 bank started\n", encoding="utf-8")
    start = time.monotonic()
    rows = []
    for seq, pairs in inputs().items():
        for ix, row in enumerate(pairs):
            pair = row["key"]
            motions = np.asarray(row["motions"], dtype=np.float64)
            candidates = []
            for k in range(4):
                with np.load(F2 / seq / pair / f"N{k}.npz", allow_pickle=False) as z:
                    poses, original = z["raw_poses"], z["T"]
                candidate = hypotheses(poses, motions)
                assert np.max(np.abs(candidate[0, 0]-original)) < 1e-10
                candidates.append(candidate)
            dest = BASE / seq / f"{pair}.npz"
            dest.parent.mkdir(parents=True, exist_ok=True)
            assert not dest.exists()
            np.savez_compressed(dest, candidates=np.asarray(candidates))
            rows.append({"sequence": seq, "pair": pair, "file": str(dest), "sha256": sha(dest)})
            if (ix+1) % 25 == 0:
                print("M1 bank", seq, ix+1, "elapsed", round(time.monotonic()-start, 1), flush=True)
            assert time.monotonic()-start <= 300
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 100*2**20
    save(BASE / "bank.json", rows)
    save(BASE / "bank_seal.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "sha256": sha(BASE / "bank.json"),
        "wall_s": time.monotonic()-start,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz")),
    })
    print("M1 bank sealed", flush=True)


def pose_error(T, truth):
    delta = np.linalg.inv(truth) @ T
    rte = float(np.linalg.norm(delta[:3, 3]))
    angle = np.arccos(np.clip((np.trace(delta[:3, :3])-1)/2, -1, 1))
    return rte, float(np.degrees(angle))


def evaluate():
    verify()
    seal = rd(BASE / "bank_seal.json")
    assert sha(BASE / "bank.json") == seal["sha256"]
    rows = rd(BASE / "bank.json")
    assert len(rows) == 200
    outcomes = []
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        labels = rd(F2 / seq / "evaluator_only_decisions.json")
        selected = [r for r in rows if r["sequence"] == seq]
        assert len(selected) == len(labels) == 100
        for saved, label in zip(selected, labels):
            pair = f'{seq}_{label["source_i"]}_{label["source_j"]}'
            assert saved["pair"] == pair and sha(Path(saved["file"])) == saved["sha256"]
            with np.load(saved["file"], allow_pickle=False) as z:
                candidates = z["candidates"]
            assert candidates.shape == (4, 3, 3, 4, 4)
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            errors = np.asarray([[pose_error(T, truth) for T in gen.reshape(-1, 4, 4)]
                                 for gen in candidates])
            assert errors.shape == (4, 9, 2)
            strict = (errors[:, :, 0] <= 1) & (errors[:, :, 1] <= 5)
            interior = (errors[:, :, 0] <= .8) & (errors[:, :, 1] <= 4)
            native = bool(strict[:, 0].any())
            assert native == bool(label["methods"]["N-OR4"]["strict"]), pair
            outcomes.append({"sequence": seq, "pair": pair, "stratum": label["stratum"],
                             "native_available": native,
                             "any_support_strict": bool(strict[:, 1:].any()),
                             "any_support_interior": bool(interior[:, 1:].any()),
                             "all_oracle_strict": bool(strict.any()),
                             "strict_candidates": int(strict.sum()),
                             "best_translation_m": float(errors[:, :, 0].min()),
                             "best_rotation_deg": float(errors[:, :, 1].min())})
    save(BASE / "outcomes.json", outcomes)
    groups = {}
    for seq in ("00", "08"):
        for available in (False, True):
            subset = [r for r in outcomes if r["sequence"] == seq and r["stratum"] != "confuser"
                      and r["native_available"] == available]
            groups[f"{seq}_{'available' if available else 'unavailable'}"] = {
                "pairs": len(subset), "support_strict": sum(r["any_support_strict"] for r in subset),
                "support_interior": sum(r["any_support_interior"] for r in subset),
                "all_oracle_strict": sum(r["all_oracle_strict"] for r in subset)}
        for stratum in ("ordinary", "confuser", "low_overlap", "ambiguous_positive"):
            subset = [r for r in outcomes if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = {"pairs": len(subset),
                "native_oracle_strict": sum(r["native_available"] for r in subset),
                "all_oracle_strict": sum(r["all_oracle_strict"] for r in subset)}
    primary = [r for r in outcomes if r["sequence"] == "08" and r["stratum"] != "confuser"
               and not r["native_available"]]
    assert len(primary) == 41
    new = sum(r["any_support_strict"] for r in primary)
    interior = sum(r["any_support_interior"] for r in primary)
    decision = "SUPPORT_HYPOTHESIS_HEADROOM" if new >= 5 and interior >= 3 else "NO_SUPPORT_HYPOTHESIS_HEADROOM"
    save(BASE / "summary.json", {"decision": decision, "primary_pairs": len(primary),
                                  "primary_new_strict": new, "primary_new_interior": interior,
                                  "groups": groups, "bank_sha256": seal["sha256"]})
    print("M1 decision", decision, "strict", new, "interior", interior, flush=True)


if __name__ == "__main__":
    {"synthetic": synthetic, "freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
