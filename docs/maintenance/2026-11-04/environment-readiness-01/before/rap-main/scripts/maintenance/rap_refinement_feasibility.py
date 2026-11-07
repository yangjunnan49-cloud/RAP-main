"""Fixed point-to-point ICP preflight from F2 native selected proposals."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


MAIN = Path(__file__).resolve().parents[2]
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
BASE = MAIN / "docs/maintenance/2026-09-27/rap-refinement-feasibility-01"
GT = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy",
}
SEQ = ("00", "08")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_new(path: Path, obj) -> None:
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pair_order(seq: str, records: list[dict]) -> list[str]:
    order = []
    seen = set()
    for record in records:
        if record["arm"] == "N" and record["pair"] not in seen:
            order.append(record["pair"])
            seen.add(record["pair"])
    assert len(order) == 100 and all(p.startswith(seq + "_") for p in order)
    return order


def selected_native(records: list[dict], pair: str) -> dict:
    choices = [r for r in records if r["pair"] == pair and r["arm"] == "N"]
    assert len(choices) == 4 and sorted(r["generation"] for r in choices) == list(range(4))
    assert all(r["valid"] for r in choices)
    return min(choices, key=lambda r: (r["rigidity_rmse_m"], r["generation"]))


def fit_rigid(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    x = source.mean(axis=0)
    y = target.mean(axis=0)
    u, _, vh = np.linalg.svd((source - x).T @ (target - y))
    d = np.diag([1.0, 1.0, np.linalg.det(vh.T @ u.T)])
    r = vh.T @ d @ u.T
    t = y - r @ x
    out = np.eye(4)
    out[:3, :3] = r
    out[:3, 3] = t
    return out


def icp(source: np.ndarray, target: np.ndarray, init: np.ndarray) -> tuple[np.ndarray, dict]:
    tree = cKDTree(target)
    pose = init.copy()
    status = "max_iterations"
    iterations = 0
    for iteration in range(30):
        transformed = source @ pose[:3, :3].T + pose[:3, 3]
        distances, indices = tree.query(transformed, k=1, workers=1)
        mask = distances < 1.0
        if int(mask.sum()) < 50:
            status = "insufficient_correspondences"
            break
        update = fit_rigid(source[mask], target[indices[mask]])
        delta = float(np.max(np.abs(update - pose)))
        pose = update
        iterations = iteration + 1
        if delta < 1e-6:
            status = "converged"
            break
    transformed = source @ pose[:3, :3].T + pose[:3, 3]
    distances, _ = tree.query(transformed, k=1, workers=1)
    mask = distances < 1.0
    return pose, {
        "status": status,
        "iterations": iterations,
        "correspondences": int(mask.sum()),
        "rmse_m": float(np.sqrt(np.mean(distances[mask] ** 2))) if mask.any() else None,
    }


def freeze() -> None:
    assert not (BASE / "freeze.json").exists()
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(), MAIN / "scripts/maintenance/validate_rap_refinement_feasibility.py",
             F2 / "decision.json", F2 / "validation.json"]
    for seq in SEQ:
        files += [F2 / seq / "records.json", F2 / seq / "evaluator_only_decisions.json", F2 / seq / "metrics.json", GT[seq]]
        records = read(F2 / seq / "records.json")
        for pair in pair_order(seq, records):
            files.append(F2 / seq / pair / "inputs.npz")
    assert read(F2 / "validation.json")["passed"]
    save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "numpy": np.__version__,
        "scipy": __import__("scipy").__version__,
        "files": {str(p): sha256(p) for p in files},
        "scope": "observed-development ICP feasibility; GT and evaluator rows excluded from runner stage",
    })
    print("R0 frozen", len(files), "files", flush=True)


def verify_freeze() -> None:
    frozen = read(BASE / "freeze.json")
    for name, expected in frozen["files"].items():
        assert sha256(Path(name)) == expected, f"frozen input changed: {name}"


def run() -> None:
    verify_freeze()
    (BASE / "INCOMPLETE").write_text("R0 runner started\n", encoding="utf-8")
    start = time.monotonic()
    bank = []
    for seq in SEQ:
        records = read(F2 / seq / "records.json")
        for pair in pair_order(seq, records):
            native = selected_native(records, pair)
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as data:
                assert data["counts"].tolist() == [2000, 1000, 1000, 2000, 1000, 1000]
                points = data["points"]
                target = np.asarray(points[:2000], dtype=np.float64)
                source = np.asarray(points[4000:6000], dtype=np.float64)
            assert np.isfinite(source).all() and np.isfinite(target).all()
            init = np.asarray(native["T"], dtype=np.float64)
            assert init.shape == (4, 4) and np.isfinite(init).all()
            refined, diagnostic = icp(source, target, init)
            assert np.isfinite(refined).all() and abs(np.linalg.det(refined[:3, :3]) - 1) < 1e-8
            bank.append({"sequence": seq, "pair": pair, "generation": native["generation"],
                         "initial_T": init.tolist(), "refined_T": refined.tolist(), **diagnostic})
        print("R0 bank", seq, "complete", flush=True)
    assert time.monotonic() - start <= 1800
    save_new(BASE / "bank.json", bank)
    import resource
    save_new(BASE / "bank_seal.json", {"sha256": sha256(BASE / "bank.json"),
                                      "utc": datetime.now(timezone.utc).isoformat(),
                                      "wall_s": time.monotonic() - start,
                                      "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2})
    print("R0 bank sealed; evaluator may run", flush=True)


def evaluate() -> None:
    verify_freeze()
    assert sha256(BASE / "bank.json") == read(BASE / "bank_seal.json")["sha256"]
    sys.path[:0] = [str(MAIN.parent / "RAP-SLAM")]
    from rap_slam.measurement import transform_label
    bank = read(BASE / "bank.json")
    outcomes = []
    for seq in SEQ:
        gt = np.load(GT[seq], allow_pickle=False)
        original = read(F2 / seq / "evaluator_only_decisions.json")
        rows = [r for r in bank if r["sequence"] == seq]
        assert len(rows) == len(original) == 100
        for row, old in zip(rows, original):
            i, j = old["source_i"], old["source_j"]
            assert row["pair"] == f"{seq}_{i}_{j}"
            assert row["generation"] == old["methods"]["N"]["generation"]
            truth = np.linalg.inv(gt[i]) @ gt[j]
            original_label = transform_label(np.asarray(row["initial_T"]), truth)
            assert abs(original_label["gt_translation_error_m"] - old["methods"]["N"]["RTE_m"]) < 1e-6
            assert abs(original_label["gt_rotation_error_deg"] - old["methods"]["N"]["RRE_deg"]) < 1e-5
            label = transform_label(np.asarray(row["refined_T"]), truth)
            rte = label["gt_translation_error_m"]
            rre = label["gt_rotation_error_deg"]
            outcomes.append({"sequence": seq, "pair": row["pair"], "stratum": old["stratum"],
                             "native_strict": old["methods"]["N"]["strict"],
                             "refined_strict": bool(rte <= 1 and rre <= 5),
                             "native_clipped_error": old["methods"]["N"]["clipped_error"],
                             "refined_clipped_error": float(min(5, max(rte, rre / 5))),
                             "refined_RTE_m": float(rte), "refined_RRE_deg": float(rre)})
    save_new(BASE / "outcomes.json", outcomes)
    summary = {"scope": "post-hoc observed-development ICP baseline, no gate or graph claim", "sequences": {}}
    for seq in SEQ:
        pos = [r for r in outcomes if r["sequence"] == seq and r["stratum"] != "confuser"]
        gains = [r["pair"] for r in pos if r["refined_strict"] and not r["native_strict"]]
        losses = [r["pair"] for r in pos if r["native_strict"] and not r["refined_strict"]]
        native_clip = float(np.mean([r["native_clipped_error"] for r in pos]))
        refined_clip = float(np.mean([r["refined_clipped_error"] for r in pos]))
        summary["sequences"][seq] = {"native_successes": sum(r["native_strict"] for r in pos),
                                     "refined_successes": sum(r["refined_strict"] for r in pos),
                                     "strict_gains": gains, "strict_losses": losses,
                                     "native_clipped_error": native_clip,
                                     "refined_clipped_error": refined_clip,
                                     "by_stratum": {s: {"native": sum(r["native_strict"] for r in pos if r["stratum"] == s),
                                                         "refined": sum(r["refined_strict"] for r in pos if r["stratum"] == s)}
                                                    for s in ("ambiguous_positive", "low_overlap", "ordinary")}}
    a = summary["sequences"]["08"]
    b = summary["sequences"]["00"]
    signal = (a["refined_successes"] - a["native_successes"] >= 3 and
              a["refined_clipped_error"] <= 0.95 * a["native_clipped_error"] and
              len(a["strict_losses"]) <= 1 and len(b["strict_losses"]) <= 1)
    summary["decision"] = "LOCAL_REFINEMENT_FEASIBILITY_SIGNAL" if signal else "NO_LOCAL_REFINEMENT_FEASIBILITY_SIGNAL"
    save_new(BASE / "summary.json", summary)
    print(summary["decision"], flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "evaluate": evaluate}[sys.argv[1]]()
