import json
from pathlib import Path
import numpy as np

ROOT = Path(r"E:/githouse/RAP-main")
DATASET = ROOT / ".maintenance-archive/2026-09-09-m0/files/Datasets-metadata/data_odometry_velodyne/dataset"
TRAJ = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/trajectory_exports"
RESULTS = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/results06.json"


def load_kitti(path):
    a = np.loadtxt(path, dtype=np.float64)
    t = np.tile(np.eye(4), (len(a), 1, 1))
    t[:, :3, :] = a.reshape(-1, 3, 4)
    return t


def camera_to_lidar(poses):
    lines = (DATASET / "sequences/09/calib.txt").read_text().splitlines()
    row = next(x for x in lines if x.startswith("Tr:"))
    tr = np.array([float(x) for x in row.split()[1:]], dtype=np.float64).reshape(3, 4)
    t = np.eye(4)
    t[:3] = tr
    converted = np.stack([np.linalg.inv(t) @ pose @ t for pose in poses])
    return np.stack([np.linalg.inv(converted[0]) @ pose for pose in converted])


def estimate_to_first(poses):
    return np.stack([np.linalg.inv(poses[0]) @ pose for pose in poses])


def align_positions(source, target):
    xs, ys = source.mean(axis=0), target.mean(axis=0)
    u, _, vt = np.linalg.svd((source - xs).T @ (target - ys) / len(source))
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    return source @ r.T + target.mean(axis=0) - xs @ r.T


gt_lidar = camera_to_lidar(load_kitti(DATASET / "poses/09.txt"))
gt = gt_lidar[:, :3, 3]
reported = {(r["sequence"], r["mode"]): r["ate"] for r in json.loads(RESULTS.read_text())["rows"] if r["repeat"] == 1}
pred, err = {}, {}
for mode in ["G", "K"]:
    poses = estimate_to_first(load_kitti(TRAJ / f"r1_09_{mode}_lidar.txt"))
    assert len(poses) == len(gt_lidar)
    pred[mode] = align_positions(poses[:, :3, 3], gt)
    err[mode] = np.linalg.norm(pred[mode] - gt, axis=1)
    rmse = float(np.sqrt(np.mean(err[mode] ** 2)))
    assert abs(rmse - reported[("09", mode)]) < 1e-8
    print("global", mode, "ATE", rmse)

window = 120
rows = []
for start in range(0, len(gt) - window + 1, 10):
    stop = start + window
    a = gt[start:start + 12, :2].mean(axis=0)
    b = gt[start + 44:start + 56, :2].mean(axis=0)
    c = gt[stop - 56:stop - 44, :2].mean(axis=0)
    d = gt[stop - 12:stop, :2].mean(axis=0)
    v1, v2 = b - a, d - c
    if np.linalg.norm(v1) < 5 or np.linalg.norm(v2) < 5:
        continue
    cosine = np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
    turn = float(np.degrees(np.arccos(cosine)))
    length = float(np.linalg.norm(np.diff(gt[start:stop, :2], axis=0), axis=1).sum())
    rows.append((start, stop, turn, length, float(err["G"][start:stop].mean()), float(err["K"][start:stop].mean())))

print("top turn windows: start stop turn_deg length RAP_mean KISS_mean")
for row in sorted(rows, key=lambda r: r[2], reverse=True)[:20]:
    print("%4d %4d %7.2f %8.2f %.4f %.4f" % row)
print("turn >= 25 deg, ordered by KISS local error")
for row in sorted((r for r in rows if r[2] >= 25), key=lambda r: r[5], reverse=True)[:20]:
    print("%4d %4d %7.2f %8.2f %.4f %.4f" % row)
