"""G1 full-scan KISS-Matcher comparator; evaluator follows a sealed bank."""

from __future__ import annotations

import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
BASE = MAIN / "docs/maintenance/2026-09-28/fullscan-global-baseline-01"
G0 = g0.BASE
RAW = Path("/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset/sequences")


def raw_path(seq: str, frame: int) -> Path:
    return RAW / seq / "velodyne" / f"{frame:06d}.bin"


def pair_scans(seq: str, pair: str) -> tuple[Path, Path]:
    s, i, j = pair.split("_")
    assert s == seq
    return raw_path(seq, int(i)), raw_path(seq, int(j))


def frozen_files() -> list[Path]:
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_fullscan_global_baseline.py",
             MAIN / "scripts/maintenance/global_proposal_baseline.py",
             MAIN / "scripts/maintenance/validate_global_proposal_baseline.py",
             MAIN.parent / "RAP-SLAM/rap_slam/real_dataset.py",
             G0 / "kiss_matcher-1.0.2-cp310-cp310-manylinux_2_28_x86_64.whl",
             F2 / "decision.json", F2 / "validation.json"]
    files += g0.vendor_files()
    for seq in ("00", "08"):
        files += [F2 / seq / "records.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        files += [p for pair in g0.order(seq) for p in pair_scans(seq, pair)]
    return list(dict.fromkeys(files))


def freeze() -> None:
    assert not (BASE / "freeze.json").exists()
    assert g0.sha(G0 / "kiss_matcher-1.0.2-cp310-cp310-manylinux_2_28_x86_64.whl") == g0.WHEEL_SHA
    assert g0.read(F2 / "validation.json")["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {"utc": datetime.now(timezone.utc).isoformat(),
        "numpy": np.__version__, "python": sys.version,
        "files": {str(p): g0.sha(p) for p in files}})
    print("G1 frozen", len(files), "files", flush=True)


def verify() -> None:
    for name, digest in g0.read(BASE / "freeze.json")["files"].items():
        assert g0.sha(Path(name)) == digest, name


def load_scan(path: Path):
    sys.path.insert(0, str(MAIN.parent / "RAP-SLAM"))
    from rap_slam.real_dataset import kitti_vertical_correction
    raw = np.fromfile(path, dtype=np.float32).reshape(-1, 4)[:, :3]
    retained = raw[np.linalg.norm(raw, axis=1) >= 1.5]
    corrected = kitti_vertical_correction(retained)
    out = np.ascontiguousarray(corrected, dtype=np.float32)
    assert out.ndim == 2 and out.shape[1] == 3 and np.isfinite(out).all()
    return out


def run() -> None:
    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    sys.path.insert(0, str(G0 / "vendor"))
    import kiss_matcher as km

    (BASE / "INCOMPLETE").write_text("G1 bank started\n", encoding="utf-8")
    start = time.monotonic()
    bank = []
    for seq in ("00", "08"):
        for index, pair in enumerate(g0.order(seq)):
            t0 = time.monotonic()
            target_path, source_path = pair_scans(seq, pair)
            target, source = load_scan(target_path), load_scan(source_path)
            try:
                matcher = km.KISSMatcher(km.KISSMatcherConfig(0.3))
                result = matcher.estimate(source, target)
                t = np.eye(4)
                t[:3, :3] = np.asarray(result.rotation, dtype=np.float64)
                t[:3, 3] = np.asarray(result.translation, dtype=np.float64).reshape(3)
                if not g0.pose_valid(t):
                    raise ValueError("nonfinite or non-SE(3) transform")
                entry = {"status": "valid", "T": t.tolist(),
                         "rotation_inliers": int(matcher.get_num_rotation_inliers()),
                         "final_inliers": int(matcher.get_num_final_inliers())}
            except Exception as exc:
                entry = {"status": "failed", "T": None, "error": f"{type(exc).__name__}: {exc}"}
            bank.append({"sequence": seq, "pair": pair, "target_points": len(target),
                         "source_points": len(source), "wall_s": time.monotonic() - t0, **entry})
            if (index + 1) % 10 == 0:
                print("G1 bank", seq, index + 1, "elapsed", round(time.monotonic() - start, 1), flush=True)
            assert time.monotonic() - start <= 2700
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2 <= 8
    g0.save_new(BASE / "bank.json", bank)
    g0.save_new(BASE / "bank_seal.json", {"sha256": g0.sha(BASE / "bank.json"),
        "utc": datetime.now(timezone.utc).isoformat(), "wall_s": time.monotonic() - start,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2})
    print("G1 bank sealed", flush=True)


def evaluate() -> None:
    verify()
    assert g0.sha(BASE / "bank.json") == g0.read(BASE / "bank_seal.json")["sha256"]
    sys.path.insert(0, str(MAIN.parent / "RAP-SLAM"))
    from rap_slam.measurement import transform_label

    bank = g0.read(BASE / "bank.json")
    outcomes = []
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        original = g0.read(F2 / seq / "evaluator_only_decisions.json")
        rows = [r for r in bank if r["sequence"] == seq]
        assert len(rows) == len(original) == 100
        for row, old in zip(rows, original):
            assert row["pair"] == f'{seq}_{old["source_i"]}_{old["source_j"]}'
            strict, rte, rre, clipped = False, None, None, 5.0
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
    g0.save_new(BASE / "outcomes.json", outcomes)
    summary = {"scope": "observed-development full corrected raw anchor scans; point budget unequal to RAP",
               "sequences": {}}
    for seq in ("00", "08"):
        rows = [r for r in outcomes if r["sequence"] == seq]
        pos = [r for r in rows if r["stratum"] != "confuser"]
        summary["sequences"][seq] = {
            "valid": sum(r["status"] == "valid" for r in rows),
            "strict": sum(r["strict"] for r in pos),
            "native_strict": sum(r["native_strict"] for r in pos),
            "gains": [r["pair"] for r in pos if r["strict"] and not r["native_strict"]],
            "losses": [r["pair"] for r in pos if r["native_strict"] and not r["strict"]],
            "native_K4_unavailable": sum(r["native_K4_unavailable"] for r in pos),
            "recovered_unavailable": [r["pair"] for r in pos if r["strict"] and r["native_K4_unavailable"]],
            "clipped_error": float(np.mean([r["clipped_error"] for r in pos])),
            "native_clipped_error": float(np.mean([r["native_clipped_error"] for r in pos])),
            "by_stratum": {s: {"strict": sum(r["strict"] for r in pos if r["stratum"] == s),
                              "native": sum(r["native_strict"] for r in pos if r["stratum"] == s)}
                           for s in ("ambiguous_positive", "low_overlap", "ordinary")}}
    a, b = summary["sequences"]["08"], summary["sequences"]["00"]
    signal = (len(a["recovered_unavailable"]) >= 5 and a["strict"] - a["native_strict"] >= 5 and
              a["clipped_error"] <= .95 * a["native_clipped_error"] and
              b["strict"] - b["native_strict"] >= -3)
    summary["decision"] = "GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL" if signal else "NO_GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL"
    g0.save_new(BASE / "summary.json", summary)
    print(summary["decision"], flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "evaluate": evaluate}[sys.argv[1]]()
