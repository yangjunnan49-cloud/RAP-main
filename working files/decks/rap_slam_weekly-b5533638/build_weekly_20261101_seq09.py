import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

DECK = Path(__file__).resolve().parent
ROOT = DECK.parents[2]
WORK = ROOT / "working files/weekly_20261101"
SEQ = "09"
START, STOP = 210, 330  # Representative 73-degree turn; both methods are shown separately.
CLOUD_SOURCE = Path(f"E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences/{SEQ}/velodyne")
CLOUD_LOCAL = WORK / f"pointcloud_src/{SEQ}"
DATASET = ROOT / ".maintenance-archive/2026-09-09-m0/files/Datasets-metadata/data_odometry_velodyne/dataset"
TRAJ = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/trajectory_exports"
RESULTS = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/results06.json"
MEDIA = DECK / "media"
CLOUD_LOCAL.mkdir(parents=True, exist_ok=True)

GREEN, ORANGE, INK = "#0B6B4F", "#B96238", "#17231E"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_kitti(path):
    a = np.loadtxt(path, dtype=np.float64)
    t = np.tile(np.eye(4), (len(a), 1, 1))
    t[:, :3, :] = a.reshape(-1, 3, 4)
    return t


def camera_to_lidar(poses):
    lines = (DATASET / "sequences" / SEQ / "calib.txt").read_text().splitlines()
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
    return source @ r.T + ys - xs @ r.T


def limits(points, margin=0.08):
    lo, hi = points.min(axis=0), points.max(axis=0)
    span = np.maximum(hi - lo, 1.0)
    return lo - span * margin, hi + span * margin


def style_axis(ax):
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#FBFCFB")
    for spine in ax.spines.values():
        spine.set_color("#D9E2DD")
        spine.set_linewidth(0.7)


gt_lidar = camera_to_lidar(load_kitti(DATASET / "poses" / f"{SEQ}.txt"))
gt = gt_lidar[:, :3, 3]
reported = {(r["sequence"], r["mode"]): r["ate"] for r in json.loads(RESULTS.read_text())["rows"] if r["repeat"] == 1}
pred, err = {}, {}
for mode in ["G", "K"]:
    poses = estimate_to_first(load_kitti(TRAJ / f"r1_{SEQ}_{mode}_lidar.txt"))
    assert len(poses) == len(gt_lidar)
    pred[mode] = align_positions(poses[:, :3, 3], gt)
    err[mode] = np.linalg.norm(pred[mode] - gt, axis=1)
    rmse = float(np.sqrt(np.mean(err[mode] ** 2)))
    assert abs(rmse - reported[(SEQ, mode)]) < 1e-8


def load_cloud(frame, max_range, sample, rng):
    local = CLOUD_LOCAL / f"{frame:06d}.bin"
    a = np.fromfile(local, dtype=np.float32).reshape(-1, 4)
    xyz = a[:, :3].astype(np.float64)
    r = np.linalg.norm(xyz, axis=1)
    keep = (r > 3.0) & (r < max_range) & (xyz[:, 2] > -2.2) & (xyz[:, 2] < 3.5)
    xyz = xyz[keep]
    if len(xyz) > sample:
        xyz = xyz[rng.choice(len(xyz), sample, replace=False)]
    return xyz @ gt_lidar[frame, :3, :3].T + gt_lidar[frame, :3, 3]


full_frames = sorted(set(range(0, len(gt), 50)) | {len(gt) - 1})
zoom_frames = list(range(max(0, START - 30), min(len(gt), STOP + 31), 4))
for frame in sorted(set(full_frames) | set(zoom_frames)):
    dst = CLOUD_LOCAL / f"{frame:06d}.bin"
    if not dst.exists():
        shutil.copyfile(CLOUD_SOURCE / f"{frame:06d}.bin", dst)

rng = np.random.default_rng(20261101)
full_cloud = np.concatenate([load_cloud(f, 65.0, 1300, rng) for f in full_frames], axis=0)
zoom_cloud = np.concatenate([load_cloud(f, 45.0, 2600, rng) for f in zoom_frames], axis=0)
zoom_points = np.concatenate([gt[START:STOP], pred["G"][START:STOP], pred["K"][START:STOP]])
zlo_full, zhi_full = limits(zoom_points, 0.16)
zoom_center = gt[START:STOP].mean(axis=0)
_, _, zoom_vt = np.linalg.svd(gt[START:STOP, :2] - zoom_center[:2], full_matrices=False)
theta = np.arctan2(zoom_vt[0][1], zoom_vt[0][0])
zoom_rot = np.array([[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]])


def rotate_zoom(points):
    out = points.copy()
    out[:, :2] = (points[:, :2] - zoom_center[:2]) @ zoom_rot.T
    return out


zoom_cloud = rotate_zoom(zoom_cloud)
gt_zoom = rotate_zoom(gt)
pred_zoom = {mode: rotate_zoom(points) for mode, points in pred.items()}
zlo, zhi = limits(rotate_zoom(zoom_points), 0.16)
all_points = np.concatenate([gt, pred["G"], pred["K"]])
lo, hi = limits(all_points, 0.05)


def render_panel(mode, is_zoom):
    method = "RAP-SLAM" if mode == "G" else "KISS-SLAM"
    color = GREEN if mode == "G" else ORANGE
    fig = plt.figure(figsize=(10.0, 5.4) if is_zoom else (5.0, 6.4), dpi=220)
    ax = fig.add_axes([0.03, 0.03, 0.94, 0.83])
    style_axis(ax)
    cloud = zoom_cloud if is_zoom else full_cloud
    ax.scatter(cloud[:, 0], cloud[:, 1], s=0.50 if is_zoom else 0.30,
               c="#B6C2BB" if is_zoom else "#AFBDB5", alpha=0.66 if is_zoom else 0.52,
               linewidths=0, rasterized=True)
    if is_zoom:
        sl = slice(START, STOP)
        ax.plot(gt_zoom[sl, 0], gt_zoom[sl, 1], color=INK, lw=1.25, alpha=0.88, zorder=3)
        ax.plot(pred_zoom[mode][sl, 0], pred_zoom[mode][sl, 1], color=color, lw=1.75, alpha=0.98, zorder=4)
        ax.set_xlim(zlo[0], zhi[0])
        ax.set_ylim(zlo[1], zhi[1])
        title = f"局部 {START}–{STOP - 1} · {method}"
        metric = f"平均误差  {err[mode][START:STOP].mean():.3f} m"
        panel_name = "rap_zoom" if mode == "G" else "kiss_zoom"
    else:
        ax.plot(gt[:, 0], gt[:, 1], color=INK, lw=0.85, alpha=0.82, zorder=3)
        ax.plot(pred[mode][:, 0], pred[mode][:, 1], color=color, lw=1.15, alpha=0.97, zorder=4)
        ax.add_patch(Rectangle((zlo_full[0], zlo_full[1]), zhi_full[0] - zlo_full[0], zhi_full[1] - zlo_full[1],
                               fill=False, edgecolor=ORANGE, lw=1.0, zorder=5))
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        title = f"全局 · {method}"
        metric = f"ATE  {reported[(SEQ, mode)]:.3f} m"
        panel_name = "rap_global" if mode == "G" else "kiss_global"
    ax.set_title(title, fontsize=12.5, color=INK, weight="bold", pad=18)
    ax.text(0.5, 1.015, metric, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=10.5, color=color, weight="bold")
    fig.savefig(MEDIA / f"trajectory_{SEQ}_{panel_name}.png", facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


for panel_mode, panel_zoom in [("G", False), ("G", True), ("K", False), ("K", True)]:
    render_panel(panel_mode, panel_zoom)

summary = {
    "sequence": SEQ,
    "ATE": {"RAP-SLAM": reported[(SEQ, "G")], "KISS-SLAM": reported[(SEQ, "K")]},
    "ATE_reduction_percent": 100 * (1 - reported[(SEQ, "G")] / reported[(SEQ, "K")]),
    "zoom": {
        "start": START,
        "stop": STOP,
        "RAP-SLAM_mean_error": float(err["G"][START:STOP].mean()),
        "KISS-SLAM_mean_error": float(err["K"][START:STOP].mean()),
        "mean_error_reduction_percent": float(100 * (1 - err["G"][START:STOP].mean() / err["K"][START:STOP].mean())),
    },
    "cloud_frames": {"full": full_frames, "zoom": zoom_frames},
    "cloud_points": {"full": len(full_cloud), "zoom": len(zoom_cloud)},
}
(MEDIA / f"weekly_visual_data_{SEQ}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
