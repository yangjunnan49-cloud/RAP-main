"""Independent GT-free validator for the P0 engineering preflight."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / "RAP-SLAM"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
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


def scan(path):
    from rap_slam.real_dataset import kitti_vertical_correction
    raw = np.fromfile(path, dtype=np.float32).reshape(-1, 4)[:, :3]
    return np.ascontiguousarray(kitti_vertical_correction(
        raw[np.linalg.norm(raw, axis=1) >= 1.5]), dtype=np.float32)


def cloud(raw):
    import open3d as o3d
    p = o3d.geometry.PointCloud()
    p.points = o3d.utility.Vector3dVector(raw.astype(np.float64))
    p = p.voxel_down_sample(.25)
    full = np.asarray(p.points, dtype=np.float32).copy()
    _, indices = p.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.5)
    return full, full[np.asarray(indices, dtype=np.int64)]


def validate():
    import torch
    from pytorch3d.ops import sample_farthest_points
    from dataset_process.extract_sample_features import FeatureExtractor

    frozen = read(BASE / "freeze.json")
    assert frozen["pairs"] == {s: [r["key"] for r in read(F2 / f"inputs_{s}.json")[:2]]
                               for s in ("00", "08")}
    checks = 0
    for name, digest in frozen["files"].items():
        assert sha(Path(name)) == digest, name
        checks += 1
    seal = read(BASE / "bank_seal.json")
    assert sha(BASE / "bank.json") == seal["sha256"]
    assert seal["wall_s"] <= 1200 and seal["peak_allocated_gib"] <= 12
    assert seal["artifact_bytes"] <= 100 * 2**20
    rows = read(BASE / "bank.json")
    assert len(rows) == 4
    saved_order = [(s, r) for s in ("00", "08") for r in read(F2 / f"inputs_{s}.json")[:2]]
    model = FeatureExtractor(model_config={"num_points_per_patch": 512,
                             "is_aligned_to_global_z": True, "des_r": 5.0},
                             des_r=5.0, is_aligned_to_global_z=True,
                             checkpoint_path=None, device="cuda")
    state = torch.load(MAIN / "weights/mini_spinnet_t.pth", map_location="cpu", weights_only=True)
    model.model.load_state_dict({k[5:]: v for k, v in state.items() if k.startswith("Desc.")}, strict=True)
    model.model.eval()
    for index, (saved, (seq, pair)) in enumerate(zip(rows, saved_order)):
        assert saved["sequence"] == seq and saved["pair"] == pair["key"]
        file = Path(saved["file"])
        assert sha(file) == saved["sha256"]
        with np.load(file, allow_pickle=False) as z:
            points, features = z["points"], z["features"]
        assert points.shape == (8000, 3) and features.shape == (8000, 32)
        assert np.isfinite(points).all() and np.isfinite(features).all()
        assert np.all(np.linalg.norm(features, axis=1) > 1e-8)
        supports, candidates = [], []
        offset = 0
        for part, (item, cap, counts) in enumerate(zip(pair["scans"], CAPS, saved["counts"])):
            raw = Path(item["path"])
            assert sha(raw) == item["sha256"]
            full, candidate = cloud(scan(raw))
            assert len(full) == counts["voxel"] and len(candidate) == counts["post_outlier"]
            assert cap <= len(candidate) <= len(full) <= 400000
            selected = points[offset:offset+cap]
            assert np.max(cKDTree(candidate).query(selected, workers=1)[0]) <= 1e-6
            supports.append(full)
            candidates.append(candidate)
            offset += cap
            checks += 6
        assert offset == 8000
        lengths = torch.tensor([len(p) for p in candidates], dtype=torch.int64, device="cuda")
        padded = torch.zeros((6, int(lengths.max()), 3), device="cuda")
        for part, candidate in enumerate(candidates):
            padded[part, :len(candidate)] = torch.from_numpy(candidate).to("cuda")
        with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
            torch.manual_seed(42)
            _, indices = sample_farthest_points(padded, lengths=lengths,
                K=torch.tensor(CAPS, dtype=torch.int64, device="cuda"), random_start_point=True)
        numpy_state = np.random.get_state()
        try:
            np.random.seed(pair["seeds"][0])
            offset = 0
            for part, cap in enumerate(CAPS):
                selected = candidates[part][indices[part, :cap].cpu().numpy()]
                assert np.array_equal(selected, points[offset:offset+cap])
                with torch.inference_mode():
                    derived = model.extract_features(torch.from_numpy(supports[part]).to("cuda"),
                                                     torch.from_numpy(selected).to("cuda"))["features"]
                assert np.array_equal(derived.cpu().numpy(), features[offset:offset+cap])
                offset += cap
                checks += 2
        finally:
            np.random.set_state(numpy_state)
        checks += 5
    assert sum(Path(r["file"]).stat().st_size for r in rows) == seal["artifact_bytes"]
    assert not (BASE / "validation.json").exists()
    with (BASE / "validation.json").open("x", encoding="utf-8") as f:
        json.dump({"passed": True, "checks": checks, "utc": datetime.now(timezone.utc).isoformat(),
                   "bank_sha256": seal["sha256"]}, f, indent=2)
        f.write("\n")
    (BASE / "INCOMPLETE").unlink()
    print("P0 preflight validation passed", checks, "checks", flush=True)


if __name__ == "__main__":
    sys.path[:0] = [str(SLAM), str(MAIN), str(MAIN / "dataset_process")]
    assert os.environ.get("OMP_NUM_THREADS") == "1" and os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert not (BASE / "validation.json").exists()
    validate()

