"""G0 fixed KISS-Matcher component comparator; labels only after bank seal."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
BASE = MAIN / "docs/maintenance/2026-09-28/global-proposal-baseline-01"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
GT = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy",
}
WHEEL = BASE / "kiss_matcher-1.0.2-cp310-cp310-manylinux_2_28_x86_64.whl"
WHEEL_SHA = "1a07d57bd23cb0ef4d9803194a74acccfa11f0015c080ab5ecc7302f258fc1f1"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_new(path: Path, obj) -> None:
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def order(seq: str) -> list[str]:
    records = read(F2 / seq / "records.json")
    pairs = list(dict.fromkeys(r["pair"] for r in records if r["arm"] == "N"))
    assert len(pairs) == 100 and all(p.startswith(seq + "_") for p in pairs)
    return pairs


def vendor_files() -> list[Path]:
    return sorted(p for p in (BASE / "vendor").rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def smoke() -> None:
    assert sha(WHEEL) == WHEEL_SHA
    sys.path.insert(0, str(BASE / "vendor"))
    import kiss_matcher as km

    rng = np.random.default_rng(42)
    src = rng.uniform(-5, 5, (5000, 3)).astype(np.float32)
    tgt = src + np.array([1.5, -0.7, 0.4], dtype=np.float32)
    result = km.KISSMatcher(km.KISSMatcherConfig(0.3)).estimate(src, tgt)
    r, t = np.asarray(result.rotation), np.asarray(result.translation).reshape(3)
    assert np.max(np.abs(r - np.eye(3))) < 0.02
    assert np.linalg.norm(t - np.array([1.5, -0.7, 0.4])) < 0.05
    print("G0 synthetic smoke passed", flush=True)


def freeze() -> None:
    assert not (BASE / "freeze.json").exists()
    assert sha(WHEEL) == WHEEL_SHA and WHEEL.stat().st_size <= 20_000_000
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(), MAIN / "scripts/maintenance/validate_global_proposal_baseline.py", WHEEL,
             F2 / "decision.json", F2 / "validation.json"] + vendor_files()
    assert read(F2 / "validation.json")["passed"]
    for seq in ("00", "08"):
        files.extend([F2 / seq / "records.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]])
        files.extend(F2 / seq / pair / "inputs.npz" for pair in order(seq))
    assert len(files) == len(set(files))
    save_new(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
        "numpy": np.__version__, "python": sys.version, "files": {str(p): sha(p) for p in files}})
    print("G0 frozen", len(files), "files", flush=True)


def verify() -> None:
    for name, digest in read(BASE / "freeze.json")["files"].items():
        assert sha(Path(name)) == digest, name


def pose_valid(t: np.ndarray) -> bool:
    return (t.shape == (4, 4) and np.isfinite(t).all() and
            np.max(np.abs(t[3] - [0, 0, 0, 1])) < 1e-8 and
            np.max(np.abs(t[:3, :3].T @ t[:3, :3] - np.eye(3))) < 1e-4 and
            abs(np.linalg.det(t[:3, :3]) - 1) < 1e-4)


def run() -> None:
    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    sys.path.insert(0, str(BASE / "vendor"))
    import kiss_matcher as km
    import resource

    start = time.monotonic()
    (BASE / "INCOMPLETE").write_text("G0 bank started\n", encoding="utf-8")
    bank = []
    for seq in ("00", "08"):
        for idx, pair in enumerate(order(seq)):
            t0 = time.monotonic()
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as data:
                assert data["counts"].tolist() == [2000, 1000, 1000, 2000, 1000, 1000]
                pts = data["points"]
                target = np.ascontiguousarray(pts[:2000], dtype=np.float32)
                source = np.ascontiguousarray(pts[4000:6000], dtype=np.float32)
            assert source.shape == target.shape == (2000, 3)
            assert np.isfinite(source).all() and np.isfinite(target).all()
            try:
                matcher = km.KISSMatcher(km.KISSMatcherConfig(0.3))
                result = matcher.estimate(source, target)
                t = np.eye(4)
                t[:3, :3] = np.asarray(result.rotation, dtype=np.float64)
                t[:3, 3] = np.asarray(result.translation, dtype=np.float64).reshape(3)
                if not pose_valid(t):
                    raise ValueError("nonfinite or non-SE(3) transform")
                entry = {"status": "valid", "T": t.tolist(),
                         "rotation_inliers": int(matcher.get_num_rotation_inliers()),
                         "final_inliers": int(matcher.get_num_final_inliers())}
            except Exception as exc:
                entry = {"status": "failed", "T": None, "error": f"{type(exc).__name__}: {exc}"}
            bank.append({"sequence": seq, "pair": pair, "wall_s": time.monotonic() - t0, **entry})
            if (idx + 1) % 25 == 0:
                print("G0 bank", seq, idx + 1, "elapsed", round(time.monotonic() - start, 1), flush=True)
            assert time.monotonic() - start <= 2700
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2 <= 4
    save_new(BASE / "bank.json", bank)
    save_new(BASE / "bank_seal.json", {"sha256": sha(BASE / "bank.json"),
        "utc": datetime.now(timezone.utc).isoformat(), "wall_s": time.monotonic() - start,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2})
    print("G0 bank sealed", flush=True)


def evaluate() -> None:
    verify()
    assert sha(BASE / "bank.json") == read(BASE / "bank_seal.json")["sha256"]
    sys.path.insert(0, str(MAIN.parent / "RAP-SLAM"))
    from rap_slam.measurement import transform_label

    bank = read(BASE / "bank.json")
    outcomes = []
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        original = read(F2 / seq / "evaluator_only_decisions.json")
        rows = [r for r in bank if r["sequence"] == seq]
        assert len(rows) == len(original) == 100
        for row, old in zip(rows, original):
            assert row["pair"] == f'{seq}_{old["source_i"]}_{old["source_j"]}'
            strict = False
            rte = rre = None
            clipped = 5.0
            if row["status"] == "valid":
                truth = np.linalg.inv(gt[old["source_i"]]) @ gt[old["source_j"]]
                label = transform_label(np.asarray(row["T"]), truth)
                rte, rre = label["gt_translation_error_m"], label["gt_rotation_error_deg"]
                strict = bool(rte <= 1 and rre <= 5)
                clipped = float(min(5, max(rte, rre / 5)))
            outcomes.append({"sequence": seq, "pair": row["pair"], "stratum": old["stratum"],
                "status": row["status"], "strict": strict, "RTE_m": rte, "RRE_deg": rre,
                "clipped_error": clipped, "native_strict": old["methods"]["N"]["strict"],
                "native_clipped_error": old["methods"]["N"]["clipped_error"],
                "native_K4_unavailable": not old["methods"]["N-OR4"]["strict"]})
    save_new(BASE / "outcomes.json", outcomes)
    summary = {"scope": "observed-development matched-2000-point component comparator", "sequences": {}}
    for seq in ("00", "08"):
        rows = [r for r in outcomes if r["sequence"] == seq]
        positives = [r for r in rows if r["stratum"] != "confuser"]
        gains = [r["pair"] for r in positives if r["strict"] and not r["native_strict"]]
        losses = [r["pair"] for r in positives if r["native_strict"] and not r["strict"]]
        recovered = [r["pair"] for r in positives if r["strict"] and r["native_K4_unavailable"]]
        summary["sequences"][seq] = {"valid": sum(r["status"] == "valid" for r in rows),
            "strict": sum(r["strict"] for r in positives), "native_strict": sum(r["native_strict"] for r in positives),
            "gains": gains, "losses": losses, "native_K4_unavailable": sum(r["native_K4_unavailable"] for r in positives),
            "recovered_unavailable": recovered,
            "clipped_error": float(np.mean([r["clipped_error"] for r in positives])),
            "native_clipped_error": float(np.mean([r["native_clipped_error"] for r in positives])),
            "by_stratum": {s: {"strict": sum(r["strict"] for r in positives if r["stratum"] == s),
                              "native": sum(r["native_strict"] for r in positives if r["stratum"] == s)}
                           for s in ("ambiguous_positive", "low_overlap", "ordinary")}}
    a, b = summary["sequences"]["08"], summary["sequences"]["00"]
    signal = (len(a["recovered_unavailable"]) >= 5 and a["strict"] - a["native_strict"] >= 5 and
              a["clipped_error"] <= .95 * a["native_clipped_error"] and
              b["strict"] - b["native_strict"] >= -3)
    summary["decision"] = "GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL" if signal else "NO_GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL"
    save_new(BASE / "summary.json", summary)
    print(summary["decision"], flush=True)


if __name__ == "__main__":
    {"smoke": smoke, "freeze": freeze, "run": run, "evaluate": evaluate}[sys.argv[1]]()
