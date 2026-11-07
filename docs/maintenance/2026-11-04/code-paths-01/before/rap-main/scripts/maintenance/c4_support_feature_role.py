"""C4 paired anchor-only/support-only feature intervention with GT-free bank."""

from __future__ import annotations

import os
import random
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c2_feature_channel as c2
import global_proposal_baseline as g0

MAIN, F2, GT, C1, RAP = c2.MAIN, c2.F2, c2.GT, c2.C1, c2.RAP
C2 = c2.BASE
BASE = MAIN / "docs/maintenance/2026-09-29/c4-support-feature-role-01"


def frozen_files():
    files = [BASE / "PROTOCOL.md", Path(__file__).resolve(),
             MAIN / "scripts/maintenance/validate_c4_support_feature_role.py",
             MAIN / "scripts/maintenance/c2_feature_channel.py",
             MAIN / "scripts/maintenance/global_proposal_baseline.py",
             MAIN / "scripts/maintenance/s1_stepcount_dev_v2.py",
             C1 / "bank_seal.json", C1 / "validation.json",
             C2 / "bank.json", C2 / "bank_seal.json", C2 / "validation_v2.json",
             C2 / "validation_v3.json", C2 / "summary_v3.json",
             F2 / "freeze.json", F2 / "validation.json",
             MAIN / "weights/rap_model_12.ckpt", MAIN / "weights/mini_spinnet_t.pth",
             RAP / "rap_slam/rap_backend.py", RAP / "rap_slam/structured_motion.py",
             RAP / "rap_slam/rap_precision.py", RAP / "scripts/hl0_preflight.py"]
    files += list((MAIN / "rectified_point_flow").rglob("*.py"))
    files += list((MAIN / "dataset_process").rglob("*.py"))
    files += list((MAIN / "config").rglob("*.yaml"))
    for seq, pairs in c2.selected().items():
        files += [F2 / f"inputs_{seq}.json", F2 / seq / "records.json",
                  F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        for pair in pairs:
            files += [F2 / seq / pair / "inputs.npz", F2 / seq / pair / "N0.npz",
                      C1 / seq / f"{pair}.npz", C2 / seq / f"{pair}.npz"]
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE / "freeze.json").exists()
    assert g0.read(C1 / "validation.json")["passed"]
    assert g0.read(C2 / "validation_v2.json")["passed"]
    assert g0.read(C2 / "validation_v3.json")["passed"]
    files = frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pairs": c2.selected(), "files": {str(p): g0.sha(p) for p in files}})
    print("C4 frozen", len(files), "identities", flush=True)


def verify():
    frozen = g0.read(BASE / "freeze.json")
    assert frozen["pairs"] == c2.selected()
    for path, digest in frozen["files"].items():
        assert g0.sha(Path(path)) == digest, path


def permute_mask(pair, counts, selected_parts):
    full = c2.part_permutation(pair, counts)
    perm = np.arange(sum(counts), dtype=np.int64)
    offsets = np.r_[0, np.cumsum(counts)]
    for part in selected_parts:
        a, b = int(offsets[part]), int(offsets[part+1])
        perm[a:b] = full[a:b]
    return perm


def response(raw_t, raw_changed, pose_t, pose_changed):
    rms = float(np.sqrt(np.mean(np.sum((raw_changed[-1].astype(np.float64)-
                                        raw_t[-1].astype(np.float64))**2, axis=1))))
    trans, angle = c2.pose_delta(pose_t, pose_changed)
    return rms, trans, angle


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
    assert not (BASE / "INCOMPLETE").exists() and not (BASE / "bank.json").exists()
    (BASE / "INCOMPLETE").write_text("C4 paired bank in progress\n", encoding="utf-8")
    started = time.monotonic()
    backend = c2.make_backend()
    torch.cuda.reset_peak_memory_stats()
    c2_bank = {r["pair"]: r for r in g0.read(C2 / "bank.json")}
    rows = []

    def state():
        return (torch.get_rng_state().clone(), torch.cuda.get_rng_state().clone(),
                random.getstate(), np.random.get_state(), backend.seed,
                torch.get_float32_matmul_precision())

    def same(a, b):
        assert torch.equal(a[0], b[0]) and torch.equal(a[1], b[1]) and a[2] == b[2]
        assert a[3][0] == b[3][0] and np.array_equal(a[3][1], b[3][1]) and a[3][2:] == b[3][2:]
        assert a[4:] == b[4:]

    for seq, pairs in c2.selected().items():
        inputs = {r["key"]: r for r in g0.read(F2 / f"inputs_{seq}.json")}
        native = g0.read(F2 / seq / "records.json")
        for pair in pairs:
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                all_points = z["points"]
                cond, counts, centers, scale = z["cond"], z["counts"], z["centers"], float(z["scale"])
                noise = torch.from_numpy(z["noise"][0]).to(backend.device)
            assert all_points.shape == (8000, 3) and counts.tolist() == list(c2.CAPS)
            with np.load(C1 / seq / f"{pair}.npz", allow_pickle=False) as z:
                all_features = z["features"]
            assert all_features.shape == (8000, 32) and np.isfinite(all_features).all()
            offsets = np.r_[0, np.cumsum(counts)]
            points = [all_points[int(a):int(b)] for a, b in zip(offsets[:-1], offsets[1:])]
            features = [all_features[int(a):int(b)] for a, b in zip(offsets[:-1], offsets[1:])]
            batch_t, found_scale, found_centers, found_counts = build_batch(backend, points, features)
            assert np.array_equal(batch_t["pointclouds"].cpu().numpy(), cond)
            assert found_scale == scale and np.array_equal(found_centers, centers)
            assert np.array_equal(found_counts, counts)
            perm_a = permute_mask(pair, counts, (0, 3))
            perm_s = permute_mask(pair, counts, (1, 2, 4, 5))
            with np.load(C2 / seq / f"{pair}.npz", allow_pickle=False) as z:
                full = z["permutation"]
                assert np.array_equal(full, c2.part_permutation(pair, counts))
                assert np.array_equal(all_features[full], all_features[perm_a][perm_s])
            batches = {"T": batch_t}
            for arm, perm in (("A", perm_a), ("S", perm_s)):
                changed = [all_features[perm[int(a):int(b)]] for a, b in zip(offsets[:-1], offsets[1:])]
                batch, s, centers_new, counts_new = build_batch(backend, points, changed)
                assert s == scale and np.array_equal(centers_new, centers)
                assert np.array_equal(counts_new, counts)
                for key in ("pointclouds", "anchor_indices", "points_per_part", "scales", "cu_seqlens"):
                    assert torch.equal(batch[key], batch_t[key])
                batches[arm] = batch
            raw, state_trajectory, poses = {}, {}, {}
            for arm in ("T", "A", "S"):
                before = state()
                with request_rng(inputs[pair]["seeds"][0], backend), ieee_matmul(), torch.inference_mode(), \
                     torch.autocast(device_type="cuda", dtype=torch.float16):
                    output = backend.model.sample_rectified_flow(
                        batches[arm], None, x_1=noise, return_tarjectory=True)
                torch.cuda.synchronize()
                same(before, state())
                raw[arm] = output["end_point_trajectory"].detach().float().cpu().numpy()
                state_trajectory[arm] = output["trajectory"].detach().float().cpu().numpy()
                assert raw[arm].shape == state_trajectory[arm].shape == (5, 8000, 3)
                assert np.isfinite(raw[arm]).all() and np.isfinite(state_trajectory[arm]).all()
                with ieee_matmul(), torch.inference_mode():
                    parts = decode_parts(batches[arm], output["end_point_trajectory"][-1], centers, scale)
                poses[arm] = np.linalg.inv(parts[0]) @ parts[3]
                assert rotation_validity(poses[arm])["valid"]
            with np.load(F2 / seq / pair / "N0.npz", allow_pickle=False) as z:
                reproduction = max(float(np.max(np.abs(raw["T"]-z["end_point_trajectory"]))),
                                   float(np.max(np.abs(state_trajectory["T"]-z["trajectory"]))))
            assert reproduction <= 1e-5, (pair, reproduction)
            parent = next(r for r in native if r["pair"] == pair and r["arm"] == "N" and r["generation"] == 0)
            assert np.max(np.abs(poses["T"]-np.asarray(parent["T"]))) <= 1e-5
            metrics = {arm: response(raw["T"], raw[arm], poses["T"], poses[arm]) for arm in ("A", "S")}
            artifact = BASE / seq / f"{pair}.npz"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            assert not artifact.exists()
            np.savez_compressed(artifact, raw_t=raw["T"], state_t=state_trajectory["T"],
                                raw_a=raw["A"], state_a=state_trajectory["A"],
                                raw_s=raw["S"], state_s=state_trajectory["S"],
                                perm_a=perm_a, perm_s=perm_s,
                                pose_t=poses["T"], pose_a=poses["A"], pose_s=poses["S"])
            rows.append({"sequence": seq, "pair": pair, "file": str(artifact),
                         "sha256": g0.sha(artifact), "reproduction_max_delta": reproduction,
                         "pose_t": poses["T"].tolist(), "pose_a": poses["A"].tolist(),
                         "pose_s": poses["S"].tolist(),
                         "a_raw_final_rms": metrics["A"][0], "a_pose_delta_m": metrics["A"][1],
                         "a_pose_delta_deg": metrics["A"][2],
                         "s_raw_final_rms": metrics["S"][0], "s_pose_delta_m": metrics["S"][1],
                         "s_pose_delta_deg": metrics["S"][2]})
            print("C4 bank", seq, pair, "elapsed", round(time.monotonic()-started, 1), flush=True)
            assert time.monotonic()-started <= 600
            assert torch.cuda.max_memory_allocated() <= 12*2**30
            assert sum(p.stat().st_size for p in BASE.rglob("*.npz")) <= 512*2**20
    g0.save_new(BASE / "bank.json", rows)
    g0.save_new(BASE / "bank_seal.json", {
        "sha256": g0.sha(BASE / "bank.json"),
        "utc": datetime.now(timezone.utc).isoformat(),
        "wall_s": time.monotonic()-started,
        "peak_allocated_gib": torch.cuda.max_memory_allocated()/2**30,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        "artifact_bytes": sum(p.stat().st_size for p in BASE.rglob("*.npz"))})
    print("C4 bank sealed", flush=True)


def evaluate():
    import s1_stepcount_dev_v2 as s1

    verify()
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    bank = g0.read(BASE / "bank.json")
    assert len(bank) == 28
    rows = []
    for seq in ("00", "08"):
        labels = {f'{seq}_{r["source_i"]}_{r["source_j"]}': r for r in
                  g0.read(F2 / seq / "evaluator_only_decisions.json")}
        gt = np.load(GT[seq], allow_pickle=False)
        for item in (r for r in bank if r["sequence"] == seq):
            assert g0.sha(Path(item["file"])) == item["sha256"]
            label = labels[item["pair"]]
            truth = np.linalg.inv(gt[label["source_i"]]) @ gt[label["source_j"]]
            strict = {arm: bool(s1.label(np.asarray(item[f"pose_{arm}"]), truth)["strict"])
                      for arm in ("t", "a", "s")}
            response_a = (item["a_raw_final_rms"] >= .005 and
                          (item["a_pose_delta_m"] >= .25 or item["a_pose_delta_deg"] >= .25))
            response_s = (item["s_raw_final_rms"] >= .005 and
                          (item["s_pose_delta_m"] >= .25 or item["s_pose_delta_deg"] >= .25))
            rows.append({"sequence": seq, "pair": item["pair"], "stratum": label["stratum"],
                         "native_candidate_available": bool(label["methods"]["N-OR4"]["strict"]),
                         "true_strict": strict["t"], "anchor_strict": strict["a"],
                         "support_strict": strict["s"],
                         "anchor_pose_response": bool(response_a),
                         "support_pose_response": bool(response_s)})
    g0.save_new(BASE / "outcomes.json", rows)
    ordinary = [r for r in rows if r["stratum"] == "ordinary"]
    positives = [r for r in rows if r["stratum"] != "confuser"]
    assert len(ordinary) == 7 and len(positives) == 22
    anchor_count = sum(r["anchor_pose_response"] for r in ordinary)
    support_count = sum(r["support_pose_response"] for r in ordinary)
    support_flips = sum(r["support_strict"] != r["true_strict"] for r in positives)
    decision = ("INCONCLUSIVE_ANCHOR_CONTROL" if anchor_count < 5 else
                "SUPPORT_FEATURE_CANDIDATE_RELIANCE" if support_count >= 6 and support_flips >= 3 else
                "SUPPORT_FEATURE_POSE_RELIANCE_ONLY" if support_count >= 6 else
                "NO_MATERIAL_SUPPORT_FEATURE_RELIANCE")
    groups = {}
    for seq in ("00", "08"):
        for stratum in ("confuser", "ambiguous_positive", "low_overlap", "ordinary"):
            subset = [r for r in rows if r["sequence"] == seq and r["stratum"] == stratum]
            groups[f"{seq}_{stratum}"] = {
                "pairs": len(subset),
                "anchor_pose_responses": sum(r["anchor_pose_response"] for r in subset),
                "support_pose_responses": sum(r["support_pose_response"] for r in subset),
                "true_strict": sum(r["true_strict"] for r in subset),
                "anchor_strict": sum(r["anchor_strict"] for r in subset),
                "support_strict": sum(r["support_strict"] for r in subset),
                "support_strict_gains": sum(r["support_strict"] and not r["true_strict"] for r in subset),
                "support_strict_losses": sum(r["true_strict"] and not r["support_strict"] for r in subset),
            }
    g0.save_new(BASE / "summary.json", {
        "scope": "observed-development six-part feature role intervention",
        "decision": decision, "ordinary_pairs": 7, "positive_pairs": 22,
        "ordinary_anchor_pose_responses": anchor_count,
        "ordinary_support_pose_responses": support_count,
        "positive_support_strict_flips": support_flips,
        "groups": groups, "bank_sha256": seal["sha256"]})
    (BASE / "INCOMPLETE").unlink()
    print("C4 decision", decision, "anchor", anchor_count,
          "support", support_count, "strict flips", support_flips, flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "bank": bank, "evaluate": evaluate}[sys.argv[1]]()
