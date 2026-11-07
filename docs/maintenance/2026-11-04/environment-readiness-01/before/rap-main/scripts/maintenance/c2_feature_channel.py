"""C2 matched-noise feature permutation, with sealed bank before GT."""

from __future__ import annotations

import collections
import hashlib
import importlib
import os
import random
import resource
import sys
import time
import typing
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import fullscan_global_baseline as g1
import v0_ray_visibility as v0
import s1_stepcount_dev_v2 as s1

MAIN, F2, GT = g0.MAIN, g0.F2, g0.GT
RAP = MAIN.parent / "RAP-SLAM"
BASE = MAIN / "docs/maintenance/2026-09-28/c2-feature-channel-01"
C1 = MAIN / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
CAPS = (2000, 1000, 1000, 2000, 1000, 1000)
INDICES = (0, 1, 25, 26, 27, 28, 50, 51, 52, 53, 75, 76, 77, 78)


def selected():
    return {seq: [g0.order(seq)[i] for i in INDICES] for seq in ("00", "08")}


def frozen_files():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_c2_feature_channel.py",
             C1 / "validation.json", C1 / "bank_seal.json",
             F2 / "validation.json", F2 / "freeze.json",
             MAIN / "weights/rap_model_12.ckpt", MAIN / "weights/mini_spinnet_t.pth",
             RAP / "rap_slam/rap_backend.py", RAP / "rap_slam/structured_motion.py",
             RAP / "rap_slam/real_dataset.py", RAP / "rap_slam/rap_precision.py",
             RAP / "scripts/hl0_preflight.py"]
    files += list((MAIN / "rectified_point_flow").rglob("*.py"))
    files += list((MAIN / "dataset_process").rglob("*.py"))
    files += list((MAIN / "config").rglob("*.yaml"))
    for seq, pairs in selected().items():
        files += [F2 / f"inputs_{seq}.json", F2 / seq / "records.json",
                  F2 / seq / "gates.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        rows = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        for pair in pairs:
            files += [F2 / seq / pair / "inputs.npz", F2 / seq / pair / "N0.npz",
                      C1 / seq / f"{pair}.npz"]
            files.extend(Path(e["path"]) for e in rows[pair]["scans"])
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert g0.read(C1 / "validation.json")["passed"]
    assert g0.read(F2 / "validation.json")["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": selected(), "files": {str(p): g0.sha(p) for p in files},
    })
    print("C2 frozen", len(files), "identities", flush=True)


def verify():
    freeze = g0.read(BASE / "freeze.json")
    assert freeze["pairs"] == selected()
    for name, digest in freeze["files"].items():
        assert g0.sha(Path(name)) == digest, name


def safe_model_weights(path):
    import torch
    import omegaconf
    from omegaconf.base import ContainerMetadata, Metadata
    from omegaconf.listconfig import ListConfig
    from omegaconf.nodes import AnyNode

    reconstruct = importlib.import_module("numpy._core.multiarray")._reconstruct
    allowed = [(reconstruct, "numpy._core.multiarray._reconstruct"),
               np.ndarray, np.dtype, np.dtypes.UInt32DType,
               ListConfig, ContainerMetadata, AnyNode, Metadata,
               int, typing.Any, dict, list, collections.defaultdict]
    with torch.serialization.safe_globals(allowed):
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    assert isinstance(checkpoint, dict) and isinstance(checkpoint["state_dict"], dict)
    return checkpoint["state_dict"]


def make_backend():
    import hydra
    import torch
    sys.path[:0] = [str(MAIN), str(RAP), str(RAP / "scripts")]
    from rap_slam.rap_backend import RAPBackend
    from dataset_process.extract_sample_features import FeatureExtractor

    torch.manual_seed(42)
    np.random.seed(42)
    backend = RAPBackend.__new__(RAPBackend)
    backend.device = torch.device("cuda")
    backend.seed = 42
    backend.voxel_size = .4
    backend.remove_outliers = True
    backend.max_points_per_scan = 4000
    with hydra.initialize_config_dir(config_dir=str(MAIN / "config"), version_base="1.3"):
        cfg = hydra.compose(config_name="RAP_inference", overrides=[
            "model=rap_12", "model.inference_sampling_steps=5",
            "model.rigidity_forcing=true", "model.n_generations=1",
            "model.save_results=false"])
    backend.model = hydra.utils.instantiate(cfg.model)
    result = backend.model.load_state_dict(safe_model_weights(MAIN / "weights/rap_model_12.ckpt"),
                                           strict=False)
    assert not result.missing_keys and not result.unexpected_keys, result
    backend.model.to(backend.device).eval()
    backend.feature_extractor = FeatureExtractor(
        model_config={"num_points_per_patch": 512, "is_aligned_to_global_z": True,
                      "des_r": 5.0}, des_r=5.0, is_aligned_to_global_z=True,
        checkpoint_path=None, device="cuda")
    state = torch.load(MAIN / "weights/mini_spinnet_t.pth", map_location="cpu",
                       weights_only=True)
    desc = {k[5:]: v for k, v in state.items() if k.startswith("Desc.")}
    backend.feature_extractor.model.load_state_dict(desc, strict=True)
    backend.feature_extractor.model.eval()
    assert backend.model.inference_sampling_steps == 5
    assert backend.model.inference_sampler == "euler"
    assert backend.model.rigidity_forcing
    return backend


def part_permutation(pair, counts):
    offsets = np.r_[0, np.cumsum(counts)]
    chunks = []
    for part in range(6):
        key = f"C2|{pair}|{part}".encode()
        seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
        local = np.random.default_rng(seed).permutation(int(counts[part]))
        chunks.append(local + int(offsets[part]))
    return np.concatenate(chunks)


def pose_delta(reference, changed):
    e = np.linalg.inv(reference) @ changed
    translation = float(np.linalg.norm(e[:3, 3]))
    rotation = float(np.degrees(np.arccos(np.clip((np.trace(e[:3, :3]) - 1) / 2, -1, 1))))
    return translation, rotation


def bank():
    import torch
    sys.path[:0] = [str(MAIN), str(RAP), str(RAP / "scripts")]
    from rap_slam.rap_precision import ieee_matmul
    from rap_slam.structured_motion import build_batch, decode_parts
    from hl0_preflight import request_rng
    from rap_slam.measurement import rotation_validity

    verify()
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert torch.cuda.is_available()
    (BASE / "INCOMPLETE").write_text("C2 paired bank started\n", encoding="utf-8")
    started = time.monotonic()
    backend = make_backend()
    gate = v0.gate_backend()
    torch.cuda.reset_peak_memory_stats()
    rows = []

    def state():
        return (torch.get_rng_state().clone(), torch.cuda.get_rng_state().clone(),
                random.getstate(), np.random.get_state(), backend.seed,
                torch.get_float32_matmul_precision())

    def same(a, b):
        assert torch.equal(a[0], b[0]) and torch.equal(a[1], b[1]) and a[2] == b[2]
        assert a[3][0] == b[3][0] and np.array_equal(a[3][1], b[3][1]) and a[3][2:] == b[3][2:]
        assert a[4:] == b[4:]

    for seq, pairs in selected().items():
        inputs = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        records = g0.read(F2 / seq / "records.json")
        gates = g0.read(F2 / seq / "gates.json")
        for pair in pairs:
            row = inputs[pair]
            scans = []
            for entry in row["scans"]:
                path = Path(entry["path"])
                assert g0.sha(path) == entry["sha256"]
                scans.append(g1.load_scan(path))
            before = state()
            with request_rng(row["seeds"][0], backend), ieee_matmul(), torch.inference_mode():
                backend.seed = 42
                points, features = [], []
                for scan, cap in zip(scans, CAPS):
                    p, f = backend.preprocess(scan, max_points=cap)
                    assert len(p) == cap and f.shape == (cap, 32)
                    points.append(p)
                    features.append(f)
            same(before, state())
            batch, scale, centers, counts = build_batch(backend, points, features)
            all_features = np.concatenate(features)
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                assert np.array_equal(all_features, z["features"])
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                assert np.array_equal(np.concatenate(points), z["points"])
                assert np.array_equal(counts, z["counts"])
                assert np.array_equal(batch["pointclouds"].cpu().numpy(), z["cond"])
                assert np.array_equal(centers, z["centers"]) and scale == float(z["scale"])
                noise = torch.from_numpy(z["noise"][0]).to(backend.device)
            with np.load(F2 / seq / pair / "N0.npz", allow_pickle=False) as z:
                saved_raw = z["end_point_trajectory"]
                saved_state = z["trajectory"]
            before = state()
            with request_rng(row["seeds"][0], backend), ieee_matmul(), torch.inference_mode(), \
                 torch.autocast(device_type="cuda", dtype=torch.float16):
                true = backend.model.sample_rectified_flow(batch, None, x_1=noise,
                                                            return_tarjectory=True)
            torch.cuda.synchronize()
            same(before, state())
            true_raw = true["end_point_trajectory"].detach().float().cpu().numpy()
            true_state = true["trajectory"].detach().float().cpu().numpy()
            assert true_raw.shape == saved_raw.shape == (5, 8000, 3)
            assert true_state.shape == saved_state.shape == (5, 8000, 3)
            reproduction = max(float(np.max(np.abs(true_raw - saved_raw))),
                               float(np.max(np.abs(true_state - saved_state))))
            assert reproduction <= 1e-5, (pair, reproduction)
            perm = part_permutation(pair, counts)
            shuffled = [all_features[perm[int(a):int(b)]] for a, b in
                        zip(np.r_[0, np.cumsum(counts)][:-1], np.cumsum(counts))]
            batch_q, scale_q, centers_q, counts_q = build_batch(backend, points, shuffled)
            assert scale_q == scale and np.array_equal(centers_q, centers)
            assert np.array_equal(counts_q, counts)
            assert torch.equal(batch_q["pointclouds"], batch["pointclouds"])
            before = state()
            with request_rng(row["seeds"][0], backend), ieee_matmul(), torch.inference_mode(), \
                 torch.autocast(device_type="cuda", dtype=torch.float16):
                changed = backend.model.sample_rectified_flow(batch_q, None, x_1=noise,
                                                               return_tarjectory=True)
            torch.cuda.synchronize()
            same(before, state())
            raw_q = changed["end_point_trajectory"].detach().float().cpu().numpy()
            state_q = changed["trajectory"].detach().float().cpu().numpy()
            assert raw_q.shape == state_q.shape == (5, 8000, 3)
            assert np.isfinite(raw_q).all() and np.isfinite(state_q).all()
            with ieee_matmul(), torch.inference_mode():
                parts_true = decode_parts(batch, true["end_point_trajectory"][-1], centers, scale)
                parts_q = decode_parts(batch_q, changed["end_point_trajectory"][-1], centers, scale)
            pose_true = np.linalg.inv(parts_true[0]) @ parts_true[3]
            pose_q = np.linalg.inv(parts_q[0]) @ parts_q[3]
            assert rotation_validity(pose_q)["valid"]
            parent = next(r for r in records if r["pair"] == pair and r["arm"] == "N" and r["generation"] == 0)
            assert np.max(np.abs(pose_true - np.asarray(parent["T"]))) <= 1e-5
            anchor_t, anchor_s = gate.preprocess(scans[0])[0], gate.preprocess(scans[3])[0]
            old_overlap, old_dist = gate._alignment_metrics(anchor_t, anchor_s, pose_true, thresh=1.)
            old_gate = gates[pair]["N"]["0"]
            assert abs(old_overlap - old_gate["overlap_ratio"]) <= 1e-5
            assert abs(old_dist - old_gate["mean_dist"]) <= 1e-5
            overlap, distance = gate._alignment_metrics(anchor_t, anchor_s, pose_q, thresh=1.)
            trans, rot = pose_delta(pose_true, pose_q)
            rms = float(np.sqrt(np.mean(np.sum((raw_q[-1].astype(np.float64) -
                                                true_raw[-1].astype(np.float64)) ** 2, axis=1))))
            artifact = BASE / seq / f"{pair}.npz"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            assert not artifact.exists()
            np.savez_compressed(artifact, raw_true=true_raw, state_true=true_state,
                                raw_q=raw_q, state_q=state_q,
                                permutation=perm, pose_q=pose_q)
            rows.append({"sequence": seq, "pair": pair, "file": str(artifact),
                         "sha256": g0.sha(artifact), "reproduction_max_delta": reproduction,
                         "pose_true": pose_true.tolist(), "pose_q": pose_q.tolist(),
                         "raw_final_rms": rms, "pose_delta_m": trans,
                         "pose_delta_deg": rot, "overlap": float(overlap),
                         "mean_dist": float(distance),
                         "accepted": bool(overlap >= .7 and distance <= 2.5)})
            print("C2 bank", seq, pair, "elapsed", round(time.monotonic() - started, 1), flush=True)
            assert time.monotonic() - started <= 600
            assert torch.cuda.max_memory_allocated() <= 12 * 2**30
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 512 * 2**20
    g0.save_new(BASE / "bank.json", rows)
    g0.save_new(BASE / "bank_seal.json", {
        "sha256": g0.sha(BASE / "bank.json"), "utc": datetime.now(timezone.utc).isoformat(),
        "wall_s": time.monotonic() - started,
        "peak_allocated_gib": torch.cuda.max_memory_allocated() / 2**30,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz")),
    })
    print("C2 bank sealed", flush=True)


def evaluate():
    verify()
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    bank = g0.read(BASE / "bank.json")
    assert len(bank) == 28
    rows = []
    for seq in ("00", "08"):
        parents = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                   g0.read(F2 / seq / "evaluator_only_decisions.json")}
        gt = np.load(GT[seq], allow_pickle=False)
        for row in (r for r in bank if r["sequence"] == seq):
            assert g0.sha(Path(row["file"])) == row["sha256"]
            parent = parents[row["pair"]]
            truth = np.linalg.inv(gt[parent["source_i"]]) @ gt[parent["source_j"]]
            true = s1.label(np.asarray(row["pose_true"]), truth)
            q = s1.label(np.asarray(row["pose_q"]), truth)
            response = row["raw_final_rms"] >= .005 and (row["pose_delta_m"] >= .25
                                                            or row["pose_delta_deg"] >= .25)
            rows.append({"sequence": seq, "pair": row["pair"], "stratum": parent["stratum"],
                         "native_candidate_available": bool(parent["methods"]["N-OR4"]["strict"]),
                         "raw_response": bool(row["raw_final_rms"] >= .005),
                         "pose_response": bool(response),
                         "true_strict": true["strict"], "shuffled_strict": q["strict"],
                         "true_accepted": bool(parent["methods"]["N"]["accepted"]),
                         "shuffled_accepted": row["accepted"]})
    g0.save_new(BASE / "outcomes.json", rows)
    ordinary = [r for r in rows if r["stratum"] == "ordinary"]
    assert len(ordinary) == 8
    pose_count = sum(r["pose_response"] for r in ordinary)
    raw_count = sum(r["raw_response"] for r in ordinary)
    decision = ("POSE_LEVEL_FEATURE_RELIANCE" if pose_count >= 6 else
                "FLOW_ONLY_FEATURE_RELIANCE" if raw_count >= 6 else
                "NO_MATERIAL_FEATURE_RELIANCE")
    groups = {}
    for seq in ("00", "08"):
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            subset = [r for r in rows if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = {
                "pairs": len(subset), "raw_responses": sum(r["raw_response"] for r in subset),
                "pose_responses": sum(r["pose_response"] for r in subset),
                "true_strict": sum(r["true_strict"] for r in subset),
                "shuffled_strict": sum(r["shuffled_strict"] for r in subset),
                "true_accepted": sum(r["true_accepted"] for r in subset),
                "shuffled_accepted": sum(r["shuffled_accepted"] for r in subset),
            }
    g0.save_new(BASE / "summary.json", {
        "scope": "fixed small observed-development feature-channel intervention",
        "decision": decision, "ordinary_raw_responses": raw_count,
        "ordinary_pose_responses": pose_count, "groups": groups,
        "bank_sha256": seal["sha256"],
    })
    (BASE / "INCOMPLETE").unlink()
    print("C2 decision", decision, "ordinary pose", pose_count,
          "ordinary raw", raw_count, flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
