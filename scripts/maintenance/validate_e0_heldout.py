"""Separate post-run metric and identity validation for E0-H1."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np


MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / "RAP-SLAM"
DATA = MAIN.parent / "Datasets/data_odometry_velodyne/dataset"
BASE = MAIN / "docs/maintenance/2026-09-27/e0-heldout-01"
COUNTS = {"07": 1101, "09": 1591, "10": 1201}
sys.path[:0] = [str(SLAM), str(SLAM / "scripts")]
import eval_paper_metrics as epm  # noqa: E402
from rap_slam import real_dataset  # noqa: E402
from rap_slam.evaluate import align_to_first_pose  # noqa: E402
from rap_slam.measurement import rotation_validity, transform_label  # noqa: E402


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_new(path: Path, obj) -> None:
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def independent_ate(gt, est) -> float:
    g = np.asarray(align_to_first_pose(list(gt)))[:, :3, 3]
    e = np.asarray(align_to_first_pose(list(est)))[:, :3, 3]
    a = e - e.mean(axis=0)
    b = g - g.mean(axis=0)
    u, _, vh = np.linalg.svd(a.T @ b)
    d = np.diag([1.0, 1.0, np.linalg.det(vh.T @ u.T)])
    r = vh.T @ d @ u.T
    return float(np.sqrt(np.mean(np.sum((a @ r.T - b) ** 2, axis=1))))


def verify_pose(poses: np.ndarray, n: int) -> None:
    assert poses.shape == (n, 4, 4) and np.isfinite(poses).all()
    for pose in poses:
        assert rotation_validity(pose, 1e-4)["valid"]


def main() -> None:
    freeze = read(BASE / "freeze.json")
    assert freeze["e0_source_identity_equal"] and freeze["kiss_environment_equal_hc"]
    for name, expected in freeze["sources"].items():
        assert sha256(Path(name)) == expected, f"source changed: {name}"
    for name, expected in freeze["inputs"].items():
        assert sha256(Path(name)) == expected, f"input changed: {name}"
    assert (BASE / "INCOMPLETE").exists()
    execution = read(BASE / "execution.json")
    assert execution["wall_s"] <= 7200
    checks = []
    results = {"sequences": {}, "means": {}}
    for seq, n in COUNTS.items():
        gt_file = DATA / "poses" / f"{seq}.txt"
        calib = DATA / "sequences" / seq / "calib.txt"
        gt_lidar = np.asarray(real_dataset.load_gt_poses(str(gt_file), str(calib), apply_calib=True))
        gt_cam = np.asarray(real_dataset.load_gt_poses(str(gt_file), str(calib), apply_calib=False))
        assert len(gt_lidar) == len(gt_cam) == n
        tr = real_dataset._read_calib_transform(str(calib))
        tr_inv = np.linalg.inv(tr)
        results["sequences"][seq] = {}
        for arm in ("O", "A"):
            dest = BASE / f"full-{seq}-{arm}"
            assert not (dest / "INCOMPLETE").exists()
            summary = read(dest / "summary.json")
            cfg = summary["config"]
            frames = read(dest / "source_frames.json")
            assert summary["n_scans"] == n and summary["odometry_backend"] == "kiss-icp"
            assert frames["source_frame_ids"] == list(range(n))
            assert frames["scan_files"] == [str(DATA / "sequences" / seq / "velodyne" / f"{i:06d}.bin") for i in range(n)]
            assert cfg["apply_kitti_205"] == (arm == "A")
            assert cfg["odom_max_range"] == 80 and cfg["odom_min_range"] == 1.5 and cfg["odom_voxel"] == 0.8
            assert cfg["rap_steps"] == 5 and cfg["multigen_k"] == 1 and cfg["max_candidates"] == 12
            assert cfg["loop_nms_width"] == 0 and not cfg["deskew"] and not cfg["allow_odom_fallback"]
            odom = np.asarray(epm.load_kitti_format(str(dest / "odom_poses.txt")))
            pgo = np.asarray(epm.load_kitti_format(str(dest / "optimized_poses.txt")))
            verify_pose(odom, n)
            verify_pose(pgo, n)
            fresh = epm.eval_offline(str(dest))
            assert fresh["frame_binding"] == "persisted_source_frame_ids"
            assert abs(independent_ate(gt_lidar, pgo) - fresh["pgo"]["ape_aligned_rmse"]) < 1e-8
            assert abs(independent_ate(gt_lidar, odom) - fresh["odometry"]["ape_aligned_rmse"]) < 1e-8
            events = [json.loads(line) for line in (dest / "verification_measurements.jsonl").read_text().splitlines()]
            starts = {e["attempt_id"]: e for e in events if e["event"] == "candidate_started"}
            ends = {e["attempt_id"]: e for e in events if e["event"] == "candidate_finished"}
            generations = {e["measurement"]["measurement_id"]: e["measurement"] for e in events if e["event"] == "generation"}
            assert starts.keys() == ends.keys() and len(starts) == summary["n_loop_candidates"]
            assert all(e["status"] in ("accepted", "rejected") for e in ends.values())
            edges = read(dest / "accepted_loops.json")
            assert {e["measurement_id"] for e in edges} == {e["selected_measurement_id"] for e in ends.values() if e["status"] == "accepted"}
            labels = {"strict_correct": 0, "strict_incorrect": 0}
            for edge in edges:
                m = generations[edge["measurement_id"]]
                np.testing.assert_array_equal(m["T_rel"], edge["T_rel"])
                assert m["source_frame_ids"] == [edge["i"], edge["j"]]
                assert "evaluator_gt" not in m and "gt_pose" not in m
                gt_relative = np.linalg.inv(gt_lidar[edge["i"]]) @ gt_lidar[edge["j"]]
                label = transform_label(m["T_rel"], gt_relative)
                assert label["validity"]["valid"] and label["label"] == m["labels"]["label"]
                field = "strict_correct" if label["gt_translation_error_m"] <= 1 and label["gt_rotation_error_deg"] <= 5 else "strict_incorrect"
                labels[field] += 1
            results["sequences"][seq][arm] = {
                "ter": fresh["pgo"]["camera_kitti"]["kitti_ter_pct"],
                "rer": fresh["pgo"]["camera_kitti"]["kitti_rer_deg100m"],
                "ate": fresh["pgo"]["ape_aligned_rmse"],
                "unaligned_ape": fresh["pgo"]["ape_unaligned_rmse"],
                "odom_ter": fresh["odometry"]["camera_kitti"]["kitti_ter_pct"],
                "odom_ate": fresh["odometry"]["ape_aligned_rmse"],
                "attempted_loops": len(starts),
                "accepted_loops": len(edges),
                **labels,
            }
            checks.append(f"{seq}-{arm}: exact frames/config, poses, metrics, edge binding and labels")
        pose_info = read(BASE / f"kiss-{seq}-pose.json")
        pose_path = Path(pose_info["path"])
        assert sha256(pose_path) == pose_info["sha256"]
        kiss_cam = np.asarray(epm.load_kitti_format(str(pose_path)))
        verify_pose(kiss_cam, n)
        kiss_lidar = np.asarray([tr_inv @ p @ tr for p in kiss_cam])
        camera = epm.evaluate_pair(list(gt_cam), list(kiss_cam), list(range(n)))
        lidar = epm.evaluate_pair(list(gt_lidar), list(kiss_lidar), list(range(n)))
        assert abs(independent_ate(gt_lidar, kiss_lidar) - lidar["ape_aligned_rmse"]) < 1e-8
        results["sequences"][seq]["KISS"] = {
            "ter": camera["kitti_ter_pct"],
            "rer": camera["kitti_rer_deg100m"],
            "ate": lidar["ape_aligned_rmse"],
            "unaligned_ape": lidar["ape_unaligned_rmse"],
        }
        checks.append(f"{seq}-KISS: exact frames, pose hash, common metrics, independent ATE")
    for arm in ("O", "A", "KISS"):
        results["means"][arm] = {
            metric: float(np.mean([results["sequences"][seq][arm][metric] for seq in COUNTS]))
            for metric in ("ter", "rer", "ate")
        }
    o, a = results["means"]["O"], results["means"]["A"]
    transfer = (a["ter"] <= o["ter"] - 0.02 and a["ate"] < o["ate"] and
                all(results["sequences"][seq]["A"]["ter"] <= results["sequences"][seq]["O"]["ter"] + 0.05 for seq in COUNTS))
    results["decision"] = "HELDOUT_TRANSFER" if transfer else "NO_HELDOUT_TRANSFER"
    results["scope"] = "07/09/10 held out from E0 arm selection, earlier data/odometry exposure declared; not novelty or training-domain confirmation"
    artifact_bytes = sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())
    assert artifact_bytes <= 20 * 1024**3
    save_new(BASE / "results.json", results)
    save_new(BASE / "validation.json", {
        "passed": True,
        "checks": checks,
        "artifact_bytes": artifact_bytes,
        "wall_s": execution["wall_s"],
        "decision": results["decision"],
        "validator_sha256": sha256(Path(__file__)),
    })
    (BASE / "INCOMPLETE").unlink()
    print(results["decision"], results["means"], flush=True)


if __name__ == "__main__":
    main()
