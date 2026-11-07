#!/usr/bin/env python3
"""Explicit CPU-only dependency/ABI probe; never instantiate a research model."""
import argparse
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rap-root", type=Path, required=True)
    p.add_argument("--slam-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True, help="New JSON receipt")
    args = p.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        p.error("Explicitly set CUDA_VISIBLE_DEVICES to an empty string")
    if not sys.dont_write_bytecode:
        p.error("Use python -B to avoid bytecode writes")
    if args.output.exists():
        p.error("Output receipt already exists")
    os.environ.update(WANDB_MODE="disabled", WANDB_DISABLED="true", HF_HUB_OFFLINE="1", MPLBACKEND="Agg")
    sys.path[:0] = [str(args.rap_root.resolve()), str(args.slam_root.resolve())]
    started = time.monotonic()
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version, "executable": sys.executable,
              "scope": "CPU_IMPORT_AND_TINY_ABI_FIXTURE_ONLY", "components": [], "model_instances": 0,
              "checkpoint_loads": 0, "dataset_reads": 0, "research_runs": 0, "training_or_backward_calls": 0}

    def probe(name, action, required=True):
        row = {"component": name, "required_for_cpu_inference_import_gate": required}
        try:
            row["details"] = action()
            row["passed"] = True
        except Exception as exc:
            row.update(passed=False, error=repr(exc), traceback=traceback.format_exc())
        result["components"].append(row)

    def module(name):
        value = importlib.import_module(name)
        return {"file": getattr(value, "__file__", None), "version": getattr(value, "__version__", None)}

    probe("torch", lambda: module("torch"))
    torch = sys.modules.get("torch")
    if torch:
        torch.set_num_threads(1)
        result["torch_build_config"] = torch.__config__.show()
        result["torch_cuda_initialized_before"] = torch.cuda.is_initialized()
    for name in ("numpy", "scipy", "hydra", "omegaconf", "lightning", "open3d", "pytorch3d.ops", "kiss_icp.kiss_icp", "gtsam", "evo.core.metrics"):
        probe(name, lambda name=name: module(name))

    def p3d_ops():
        import torch
        from pytorch3d.ops import ball_query, sample_farthest_points, knn_points
        points = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]], device="cpu")
        sampled, index = sample_farthest_points(points, K=2, random_start_point=False)
        ball = ball_query(points, points, K=2, radius=1.1, return_nn=True)
        nearest = knn_points(points, points, K=1)
        assert sampled.shape == (1, 2, 3) and index.shape == (1, 2)
        assert ball.idx.shape == (1, 4, 2)
        assert torch.isfinite(sampled).all() and torch.equal(nearest.dists, torch.zeros((1, 4, 1)))
        return {"fixture_points": 4, "device": "cpu", "ops": ["sample_farthest_points", "ball_query", "knn_points"]}

    probe("pytorch3d_cpu_extension_ops", p3d_ops)
    for name in ("rectified_point_flow.modeling", "rectified_point_flow.data.datamodule", "dataset_process.extract_sample_features", "rap_slam.rap_backend"):
        probe(name, lambda name=name: module(name))

    def hydra_config():
        import hydra
        from omegaconf import OmegaConf
        with hydra.initialize_config_dir(config_dir=str(args.rap_root.resolve() / "config"), version_base="1.3"):
            cfg = hydra.compose(config_name="RAP_inference")
            selected = OmegaConf.to_container(cfg.model, resolve=True)
        return {"config": "RAP_inference", "model_target": selected["_target_"], "model_instantiated": False}

    probe("hydra_inference_model_config_resolution", hydra_config)
    probe("muon_training_dependency", lambda: module("muon"), required=False)
    result["torch_cuda_initialized_after"] = torch.cuda.is_initialized() if torch else None
    result["cpu_import_gate_passed"] = all(row["passed"] for row in result["components"] if row["required_for_cpu_inference_import_gate"])
    result["all_optional_training_dependencies_present"] = all(row["passed"] for row in result["components"])
    result["gpu_model_training_or_clean_environment_validated"] = False
    result["wall_seconds"] = time.monotonic() - started
    assert result["torch_cuda_initialized_after"] in (None, False), "Unexpected CUDA context initialization"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cpu_import_gate_passed": result["cpu_import_gate_passed"],
                      "failed_components": [r["component"] for r in result["components"] if not r["passed"]],
                      "model_instances": 0, "training_calls": 0, "cuda_initialized": result["torch_cuda_initialized_after"]}))
    return 0 if result["cpu_import_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
