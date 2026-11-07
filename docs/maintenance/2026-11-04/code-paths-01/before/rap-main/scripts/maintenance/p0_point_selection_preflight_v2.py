"""Frozen GT-free P0 point-selection preflight."""
from __future__ import annotations

import hashlib
import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / "RAP-SLAM"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
C1 = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
BASE = MAIN / "docs/maintenance/2026-09-29/p0-point-selection-preflight-02"
CAPS = (2000, 1000, 1000, 2000, 1000, 1000)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save_new(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def cohort():
    return {s: read(F2 / f"inputs_{s}.json")[:2] for s in ("00", "08")}


def frozen_files():
    paths = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_p0_point_selection_preflight_v2.py",
             MAIN / "docs/maintenance/2026-09-29/p0-point-selection-preflight-01/PROTOCOL.md",
             MAIN / "docs/maintenance/2026-09-29/p0-point-selection-preflight-01/REPORT.md",
             MAIN / "docs/maintenance/2026-09-29/p0-point-selection-preflight-01/freeze.json",
             MAIN / "docs/maintenance/2026-09-29/p0-point-selection-preflight-01/bank_seal.json",
             MAIN / "dataset_process/extract_sample_features.py",
             MAIN / "dataset_process/utils/point_sampling_utils.py",
             MAIN / "dataset_process/utils/spinnet/patch_embedder.py",
             MAIN / "dataset_process/utils/spinnet/utils/common.py",
             MAIN / "weights/mini_spinnet_t.pth",
             SLAM / "rap_slam/real_dataset.py",
             F2 / "validation.json", C1 / "validation.json"]
    for seq, pairs in cohort().items():
        paths.append(F2 / f"inputs_{seq}.json")
        for row in pairs:
            pair = row["key"]
            paths += [F2 / seq / pair / "inputs.npz", C1 / seq / f"{pair}.npz"]
            for scan in row["scans"]:
                p = Path(scan["path"])
                assert p.is_file() and p.stat().st_size == scan["bytes"]
                assert sha(p) == scan["sha256"]
                paths.append(p)
    return list(dict.fromkeys(paths))


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert read(F2 / "validation.json")["passed"]
    assert read(C1 / "validation.json")["passed"]
    paths = frozen_files()
    assert all(p.is_file() for p in paths)
    save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": {s: [r["key"] for r in rows] for s, rows in cohort().items()},
        "files": {str(p): sha(p) for p in paths},
        "caps": {"wall_s": 1200, "gpu_allocated_gib": 12, "artifacts_bytes": 100 * 2**20},
    })
    print("P0 frozen", len(paths), "identities", flush=True)


def verify():
    frozen = read(BASE / "freeze.json")
    assert frozen["pairs"] == {s: [r["key"] for r in rows] for s, rows in cohort().items()}
    for name, digest in frozen["files"].items():
        assert sha(Path(name)) == digest, name


def load_scan(path):
    from rap_slam.real_dataset import kitti_vertical_correction
    raw = np.fromfile(path, dtype=np.float32).reshape(-1, 4)[:, :3]
    raw = raw[np.linalg.norm(raw, axis=1) >= 1.5]
    return np.ascontiguousarray(kitti_vertical_correction(raw), dtype=np.float32)


def prepare(scans):
    import open3d as o3d
    voxel, selection, counts = [], [], []
    for scan, cap in zip(scans, CAPS):
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(scan.astype(np.float64))
        cloud = cloud.voxel_down_sample(.25)
        full = np.asarray(cloud.points, dtype=np.float32).copy()
        assert cap <= len(full) <= 400000 and np.isfinite(full).all()
        _, indices = cloud.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.5)
        candidate = full[np.asarray(indices, dtype=np.int64)]
        assert len(candidate) >= cap and np.isfinite(candidate).all()
        voxel.append(full)
        selection.append(candidate)
        counts.append({"voxel": len(full), "post_outlier": len(candidate)})
    return voxel, selection, counts


def fps(selection):
    import torch
    from utils.point_sampling_utils import apply_batched_fps
    device = torch.device("cuda")
    lengths = torch.tensor([len(p) for p in selection], dtype=torch.int64, device=device)
    padded = torch.zeros((6, int(lengths.max()), 3), dtype=torch.float32, device=device)
    for i, points in enumerate(selection):
        padded[i, :len(points)] = torch.from_numpy(points).to(device)
    k = torch.tensor(CAPS, dtype=torch.int64, device=device)
    with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
        sampled, indices = apply_batched_fps(padded, lengths, k, 42, device)
    out = []
    for i, cap in enumerate(CAPS):
        idx = indices[i, :cap].cpu().numpy()
        assert np.all((idx >= 0) & (idx < len(selection[i])))
        points = sampled[i].cpu().numpy()
        assert points.shape == (cap, 3) and np.array_equal(points, selection[i][idx])
        out.append(points)
    return out


def extractor():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    model = FeatureExtractor(model_config={"num_points_per_patch": 512,
                                   "is_aligned_to_global_z": True, "des_r": 5.0},
                             des_r=5.0, is_aligned_to_global_z=True,
                             checkpoint_path=None, device="cuda")
    saved = torch.load(MAIN / "weights/mini_spinnet_t.pth", map_location="cpu", weights_only=True)
    state = {key[5:]: value for key, value in saved.items() if key.startswith("Desc.")}
    model.model.load_state_dict(state, strict=True)
    model.model.eval()
    return model


def features(model, voxel, points):
    import torch
    out = []
    with torch.inference_mode():
        for full, selected in zip(voxel, points):
            result = model.extract_features(torch.from_numpy(full).to("cuda"),
                                            torch.from_numpy(selected).to("cuda"))
            feat = result["features"].cpu().numpy().astype(np.float32, copy=False)
            assert feat.shape == (len(selected), 32) and np.isfinite(feat).all()
            assert np.all(np.linalg.norm(feat, axis=1) > 1e-8)
            out.append(feat)
    return out


def run():
    import torch
    sys.path[:0] = [str(SLAM), str(MAIN), str(MAIN / "dataset_process")]
    verify()
    assert torch.cuda.is_available()
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    (BASE / "INCOMPLETE").write_text("P0 preflight started\n", encoding="utf-8")
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    model = extractor()
    rows = []
    for seq, pairs in cohort().items():
        for row in pairs:
            pair = row["key"]
            scans = [load_scan(Path(s["path"])) for s in row["scans"]]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                assert tuple(z["counts"].tolist()) == CAPS and z["points"].shape == (8000, 3)
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                control = z["features"]
                assert control.shape == (8000, 32) and np.isfinite(control).all()
                assert np.all(np.linalg.norm(control, axis=1) > 1e-8)
            voxel, selection, counts = prepare(scans)
            points = fps(selection)
            numpy_state = np.random.get_state()
            try:
                np.random.seed(row["seeds"][0])
                feat = features(model, voxel, points)
            finally:
                np.random.set_state(numpy_state)
            dest = BASE / seq / f"{pair}.npz"
            dest.parent.mkdir(parents=True, exist_ok=True)
            assert not dest.exists()
            np.savez_compressed(dest, points=np.concatenate(points), features=np.concatenate(feat))
            rows.append({"sequence": seq, "pair": pair, "file": str(dest),
                         "sha256": sha(dest), "counts": counts,
                         "min_feature_norm": float(min(np.linalg.norm(f, axis=1).min() for f in feat))})
            print("P0 preflight", pair, "elapsed", round(time.monotonic()-start, 1), flush=True)
            assert time.monotonic()-start <= 1200
            assert torch.cuda.max_memory_allocated() <= 12 * 2**30
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 100 * 2**20
    save_new(BASE / "bank.json", rows)
    save_new(BASE / "bank_seal.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "sha256": sha(BASE / "bank.json"),
        "wall_s": time.monotonic()-start,
        "peak_allocated_gib": torch.cuda.max_memory_allocated()/2**30,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz")),
    })
    print("P0 preflight bank sealed", flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()

