"""Bounded migration I/O: four-point native ops and one unchanged demo pair."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not sys.dont_write_bytecode:
        parser.error("Use -B and a new output receipt")
    os.environ.update(WANDB_MODE="disabled", WANDB_DISABLED="true", HF_HUB_OFFLINE="1", MPLBACKEND="Agg")
    started = time.monotonic()
    result = dict(started_utc=datetime.now(timezone.utc).isoformat(), scope="MIGRATION_IO_ONLY",
                  registration_pairs=0, scientific_comparison=False, training_or_backward_calls=0)
    try:
        rap, slam = args.workspace / "RAP-main", args.workspace / "RAP-SLAM"
        sys.path[:0] = [str(rap), str(slam)]
        inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
        for row in inputs:
            path = args.workspace / row["path"]
            assert path.is_file() and not path.is_symlink()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], str(path)
        result["input_hashes_verified"] = inputs
        import numpy as np
        import torch
        import open3d as o3d
        from pytorch3d.ops import ball_query, knn_points, sample_farthest_points
        assert torch.cuda.is_available()
        torch.set_num_threads(1)
        torch.cuda.reset_peak_memory_stats()
        result.update(torch=torch.__version__, cuda=torch.version.cuda,
                      gpu=torch.cuda.get_device_name(0), capability=list(torch.cuda.get_device_capability(0)))
        points = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 2., 0.], [0., 0., 3.]]])
        cpu_fps, cpu_index = sample_farthest_points(points, K=2, random_start_point=False)
        cpu_ball = ball_query(points, points, K=2, radius=2.1, return_nn=True)
        device_points = points.cuda()
        gpu_fps, gpu_index = sample_farthest_points(device_points, K=2, random_start_point=False)
        gpu_ball = ball_query(device_points, device_points, K=2, radius=2.1, return_nn=True)
        gpu_knn = knn_points(device_points, device_points, K=1)
        assert torch.equal(cpu_index, gpu_index.cpu()) and torch.equal(cpu_fps, gpu_fps.cpu())
        assert torch.equal(cpu_ball.idx, gpu_ball.idx.cpu())
        assert torch.isfinite(gpu_ball.dists).all() and torch.equal(gpu_knn.dists, torch.zeros_like(gpu_knn.dists))
        torch.cuda.synchronize()
        result["four_point_GPU_extension_gate_passed"] = True
        # Use the established backend defaults, including features and five Euler steps.
        from rap_slam.rap_backend import RAPBackend
        backend = RAPBackend(rap_root=str(rap), ckpt_path=str(rap / "weights/rap_model_12.ckpt"),
                             spinnet_ckpt=str(rap / "weights/mini_spinnet_t.pth"))
        assert backend.feature_extraction_on and backend.feature_extractor is not None
        assert backend.sampling_steps == 5 and backend.max_points_per_scan == 4000
        # The production loaders tolerate missing keys. The acceptance harness also
        # requires an exact state-dict match; it does not change production loaders.
        checkpoint = torch.load(rap / "weights/rap_model_12.ckpt", map_location="cpu", weights_only=False)
        backend.model.load_state_dict(checkpoint["state_dict"], strict=True)
        del checkpoint
        feature_state = torch.load(rap / "weights/mini_spinnet_t.pth", map_location="cpu", weights_only=False)
        filtered = {key[5:]: value for key, value in feature_state.items() if key.startswith("Desc.")}
        assert filtered
        backend.feature_extractor.model.load_state_dict(filtered, strict=True)
        del filtered, feature_state
        result["both_model_state_dicts_strictly_matched"] = True
        clouds = []
        for name in ("scan000.ply", "scan001.ply"):
            cloud = o3d.io.read_point_cloud(str(rap / "demo_example_data/indoor_scan_arena" / name))
            points_array = np.asarray(cloud.points, dtype=np.float32)
            assert len(points_array) >= 200 and np.isfinite(points_array).all()
            clouds.append(points_array)
        before = torch.get_float32_matmul_precision()
        cudnn_before = torch.backends.cudnn.allow_tf32
        transform, diagnostic = backend.register(*clouds)
        result["registration_pairs"] = 1
        torch.cuda.synchronize()
        assert transform.shape == (4, 4) and np.isfinite(transform).all()
        assert np.allclose(transform[3], [0, 0, 0, 1])
        assert torch.get_float32_matmul_precision() == before
        assert torch.backends.cudnn.allow_tf32 == cudnn_before
        result.update(passed=True, transform_shape=list(transform.shape), transform_finite=True,
                      convention="b_to_a", preprocessed_points=[int(diagnostic["n_a"]), int(diagnostic["n_b"])],
                      features_enabled=True, unchanged_backend_defaults=True, model_euler_steps=5,
                      matmul_precision_restored=True, cudnn_policy_retained=True,
                      peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                      peak_reserved_bytes=torch.cuda.max_memory_reserved(), accuracy_evaluated=False)
    except BaseException as exc:
        result.update(passed=False, error=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        result["wall_seconds"] = time.monotonic() - started
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
