"""P0 GT-free bank, then separately sealed-bank information evaluator."""
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
import p0_point_selection_preflight_v2 as pre
from c1_descriptor_information import score

MAIN, F2, C1 = pre.MAIN, pre.F2, pre.C1
BASE = MAIN / "docs/maintenance/2026-09-29/p0-point-selection-information-01"
P2 = pre.BASE
GT = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy",
}


def cohort():
    return {s: pre.read(F2 / f"inputs_{s}.json") for s in ("00", "08")}


def frozen_files():
    paths = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_p0_point_selection_information.py",
             MAIN / "scripts/maintenance/p0_point_selection_preflight_v2.py",
             MAIN / "scripts/maintenance/validate_p0_point_selection_preflight_v2.py",
             MAIN / "scripts/maintenance/c1_descriptor_information.py",
             MAIN / "dataset_process/extract_sample_features.py",
             MAIN / "dataset_process/utils/point_sampling_utils.py",
             MAIN / "dataset_process/utils/spinnet/patch_embedder.py",
             MAIN / "dataset_process/utils/spinnet/utils/common.py",
             MAIN / "weights/mini_spinnet_t.pth",
             pre.SLAM / "rap_slam/real_dataset.py",
             P2 / "PROTOCOL.md", P2 / "REPORT.md", P2 / "freeze.json",
             P2 / "bank.json", P2 / "bank_seal.json", P2 / "validation.json",
             C1 / "bank_seal.json", C1 / "pairs.json", C1 / "validation.json",
             F2 / "validation.json"]
    for seq, pairs in cohort().items():
        paths += [F2 / f"inputs_{seq}.json", GT[seq],
                  F2 / seq / "evaluator_only_decisions.json"]
        for row in pairs:
            pair = row["key"]
            paths += [F2 / seq / pair / "inputs.npz", C1 / seq / f"{pair}.npz"]
            for scan in row["scans"]:
                paths.append(Path(scan["path"]))
    paths += [Path(r["file"]) for r in pre.read(P2 / "bank.json")]
    return list(dict.fromkeys(paths))


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert pre.read(P2 / "validation.json")["passed"]
    assert pre.read(C1 / "validation.json")["passed"]
    assert pre.read(F2 / "validation.json")["passed"]
    pairs = cohort()
    assert all(len(v) == 100 for v in pairs.values())
    raw = {Path(scan["path"]) for rows in pairs.values() for row in rows for scan in row["scans"]}
    assert len(raw) == 796, len(raw)
    for rows in pairs.values():
        for row in rows:
            for scan in row["scans"]:
                p = Path(scan["path"])
                assert p.stat().st_size == scan["bytes"] and pre.sha(p) == scan["sha256"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    pre.save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": {s: [r["key"] for r in rows] for s, rows in pairs.items()},
        "unique_raw_scans": len(raw),
        "files": {str(p): pre.sha(p) for p in files},
        "caps": {"wall_s": 1800, "gpu_allocated_gib": 12, "artifacts_bytes": 2**30},
    })
    print("P0 full frozen", len(files), "identities", flush=True)


def verify():
    frozen = pre.read(BASE / "freeze.json")
    assert frozen["pairs"] == {s: [r["key"] for r in rows] for s, rows in cohort().items()}
    for name, digest in frozen["files"].items():
        assert pre.sha(Path(name)) == digest, name


def bank():
    import torch
    sys.path[:0] = [str(pre.SLAM), str(MAIN), str(MAIN / "dataset_process")]
    verify()  # Hash identities; do not parse evaluator GT or labels.
    assert torch.cuda.is_available()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    (BASE / "INCOMPLETE").write_text("P0 full bank started\n", encoding="utf-8")
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    model = pre.extractor()
    rows = []
    for seq, pairs in cohort().items():
        for ix, row in enumerate(pairs):
            pair = row["key"]
            scans = [pre.load_scan(Path(s["path"])) for s in row["scans"]]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                assert tuple(z["counts"].tolist()) == pre.CAPS and z["points"].shape == (8000, 3)
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                control = z["features"]
                assert control.shape == (8000, 32) and np.isfinite(control).all()
                assert np.all(np.linalg.norm(control, axis=1) > 1e-8)
            voxel, selection, counts = pre.prepare(scans)
            points = pre.fps(selection)
            numpy_state = np.random.get_state()
            try:
                np.random.seed(row["seeds"][0])
                feat = pre.features(model, voxel, points)
            finally:
                np.random.set_state(numpy_state)
            dest = BASE / seq / f"{pair}.npz"
            dest.parent.mkdir(parents=True, exist_ok=True)
            assert not dest.exists()
            np.savez_compressed(dest, points=np.concatenate(points), features=np.concatenate(feat))
            rows.append({"sequence": seq, "pair": pair, "file": str(dest),
                         "sha256": pre.sha(dest), "counts": counts,
                         "min_feature_norm": float(min(np.linalg.norm(f, axis=1).min() for f in feat))})
            if (ix + 1) % 10 == 0:
                print("P0 bank", seq, ix + 1, "elapsed", round(time.monotonic()-start, 1), flush=True)
            assert time.monotonic()-start <= 1800
            assert torch.cuda.max_memory_allocated() <= 12 * 2**30
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 2**30
    pre.save_new(BASE / "bank.json", rows)
    pre.save_new(BASE / "bank_seal.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "sha256": pre.sha(BASE / "bank.json"),
        "wall_s": time.monotonic()-start,
        "peak_allocated_gib": torch.cuda.max_memory_allocated()/2**30,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz")),
    })
    print("P0 full bank sealed", flush=True)


def summary(rows):
    def med(values):
        return float(np.median(values)) if values else None
    valid = [r for r in rows if r["f2"]["paired_difference"] is not None
             and r["p0"]["paired_difference"] is not None]
    return {"pairs": len(rows), "common_nonzero": len(valid),
            "f2_adequate": sum(r["f2"]["eligible_fraction"] >= .1 for r in rows),
            "p0_adequate": sum(r["p0"]["eligible_fraction"] >= .1 for r in rows),
            "common_adequate": sum(r["f2"]["eligible_fraction"] >= .1 and
                                   r["p0"]["eligible_fraction"] >= .1 for r in rows),
            "f2_eligible_median": med([r["f2"]["eligible_fraction"] for r in rows]),
            "p0_eligible_median": med([r["p0"]["eligible_fraction"] for r in rows]),
            "f2_recall_median": med([r["f2"]["true_recall"] for r in valid]),
            "p0_recall_median": med([r["p0"]["true_recall"] for r in valid]),
            "f2_control_median": med([r["f2"]["control_mean_recall"] for r in valid]),
            "p0_control_median": med([r["p0"]["control_mean_recall"] for r in valid]),
            "f2_information_median": med([r["f2"]["paired_difference"] for r in valid]),
            "p0_information_median": med([r["p0"]["paired_difference"] for r in valid]),
            "paired_information_gain_median": med([r["information_gain"] for r in valid]),
            "paired_coverage_gain_median": med([r["coverage_gain"] for r in rows])}


def evaluate():
    verify()
    seal = pre.read(BASE / "bank_seal.json")
    assert pre.sha(BASE / "bank.json") == seal["sha256"]
    bank_rows = pre.read(BASE / "bank.json")
    assert len(bank_rows) == 200
    old = {r["pair"]: r for r in pre.read(C1 / "pairs.json")}
    rows = []
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        labels = pre.read(F2 / seq / "evaluator_only_decisions.json")
        selected = [r for r in bank_rows if r["sequence"] == seq]
        assert len(labels) == len(selected) == 100
        for bank_row, label in zip(selected, labels):
            pair = f'{seq}_{label["source_i"]}_{label["source_j"]}'
            assert bank_row["pair"] == pair and pre.sha(Path(bank_row["file"])) == bank_row["sha256"]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                f2_points = z["points"]
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                f2_features = z["features"]
            with np.load(bank_row["file"], allow_pickle=False) as z:
                p0_points, p0_features = z["points"], z["features"]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            f2 = score(f2_points, f2_features, truth, pair)
            p0 = score(p0_points, p0_features, truth, pair)
            for key, value in f2.items():
                previous = old[pair][key]
                if isinstance(value, list):
                    assert all((a is None and b is None) or abs(a-b) <= 1e-12
                               for a, b in zip(value, previous))
                elif value is None:
                    assert previous is None
                else:
                    assert abs(value-previous) <= 1e-12, (pair, key)
            gain = (p0["paired_difference"]-f2["paired_difference"]
                    if p0["paired_difference"] is not None and f2["paired_difference"] is not None
                    else None)
            rows.append({"sequence": seq, "pair": pair, "stratum": label["stratum"],
                         "native_candidate_available": bool(label["methods"]["N-OR4"]["strict"]),
                         "f2": f2, "p0": p0, "information_gain": gain,
                         "coverage_gain": p0["eligible_fraction"]-f2["eligible_fraction"]})
    pre.save_new(BASE / "pairs.json", rows)
    groups = {}
    for seq in ("00", "08"):
        for available in (False, True):
            selected = [r for r in rows if r["sequence"] == seq and r["stratum"] != "confuser"
                        and r["native_candidate_available"] == available]
            groups[f"{seq}_{'available' if available else 'unavailable'}"] = summary(selected)
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            groups[f"{seq}_{stratum}"] = summary([r for r in rows if r["sequence"] == seq
                                                  and r["stratum"] == stratum])
    hard = [r for r in rows if r["sequence"] == "08" and r["stratum"] != "confuser"
            and not r["native_candidate_available"]]
    assert len(hard) == 41
    common = [r for r in hard if r["f2"]["eligible_fraction"] >= .1
              and r["p0"]["eligible_fraction"] >= .1]
    signs = sum(r["information_gain"] > 0 for r in common)
    guards = {}
    for seq in ("00", "08"):
        ordinary = [r for r in rows if r["sequence"] == seq and r["stratum"] == "ordinary"]
        assert len(ordinary) == 25
        both = [r for r in ordinary if r["information_gain"] is not None]
        guards[seq] = {"common_nonzero": len(both),
                       "median_gain": float(np.median([r["information_gain"] for r in both])) if both else None}
    if len(common) < 20 or any(v["common_nonzero"] < 20 for v in guards.values()):
        decision = "INCONCLUSIVE_COMMON_SUPPORT"
    elif (np.median([r["information_gain"] for r in common]) >= .10
          and 3*signs >= 2*len(common)
          and all(v["median_gain"] >= -.05 for v in guards.values())):
        decision = "MATERIAL_INFORMATION_SIGNAL"
    else:
        decision = "NO_MATERIAL_INFORMATION_SIGNAL"
    pre.save_new(BASE / "summary.json", {
        "decision": decision, "scope": "observed-development input-information audit",
        "hard08_pairs": len(hard), "primary_common_adequate": len(common),
        "primary_median_information_gain": float(np.median([r["information_gain"] for r in common])) if common else None,
        "primary_positive_signs": signs, "ordinary_guards": guards,
        "groups": groups, "bank_sha256": seal["sha256"]})
    print("P0 decision", decision, "common", len(common), "signs", signs, flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
