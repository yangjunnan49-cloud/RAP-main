import json
from pathlib import Path
import numpy as np

ROOT = Path("E:/githouse/RAP-main")
DATASET = ROOT / ".maintenance-archive/2026-09-09-m0/files/Datasets-metadata/data_odometry_velodyne/dataset"
TRAJ = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/trajectory_exports"


def load_kitti(path):
    a = np.loadtxt(path, dtype=np.float64)
    t = np.tile(np.eye(4), (len(a), 1, 1))
    t[:, :3, :] = a.reshape(-1, 3, 4)
    return t


def camera_to_lidar(poses):
    lines = (DATASET / "sequences/05/calib.txt").read_text().splitlines()
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
    return source @ r.T + (ys - r @ xs)


gt = camera_to_lidar(load_kitti(DATASET / "poses/05.txt"))[:, :3, 3]
err = {}
for mode in ["G", "K"]:
    poses = estimate_to_first(load_kitti(TRAJ / f"r1_05_{mode}_lidar.txt"))
    pred = align_positions(poses[:, :3, 3], gt)
    err[mode] = np.linalg.norm(pred - gt, axis=1)

window = 120
candidates = []
for start in range(0, len(gt) - window, 20):
    stop = start + window
    v0 = gt[start + 20, :2] - gt[start, :2]
    v1 = gt[stop - 1, :2] - gt[stop - 21, :2]
    c = np.dot(v0, v1) / (np.linalg.norm(v0) * np.linalg.norm(v1))
    angle = float(np.degrees(np.arccos(np.clip(c, -1, 1))))
    g = float(err["G"][start:stop].mean())
    k = float(err["K"][start:stop].mean())
    span = gt[start:stop, :2].max(axis=0) - gt[start:stop, :2].min(axis=0)
    aspect = float(max(span) / max(min(span), 1.0))
    candidates.append({"start": start, "stop": stop, "turn_deg": angle, "G": g, "K": k,
                       "advantage": k - g, "aspect": aspect})

eligible = [r for r in candidates if r["turn_deg"] >= 25 and r["advantage"] > 0.15 and r["aspect"] <= 5.0]
eligible.sort(key=lambda r: r["advantage"] * (1 + min(r["turn_deg"], 120) / 90), reverse=True)
print(json.dumps(eligible[:20], indent=2))
