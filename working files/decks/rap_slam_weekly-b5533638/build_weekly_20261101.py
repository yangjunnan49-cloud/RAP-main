import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

DECK = Path(__file__).resolve().parent
ROOT = DECK.parents[2]
WORK = ROOT / "working files/weekly_20261101"
CLOUD_SOURCE = Path("E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences/05/velodyne")
CLOUD_LOCAL = WORK / "pointcloud_src/05"
DATASET = ROOT / ".maintenance-archive/2026-09-09-m0/files/Datasets-metadata/data_odometry_velodyne/dataset"
TRAJ = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/trajectory_exports"
RESULTS = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/results06.json"
MEDIA = DECK / "media"
MEDIA.mkdir(exist_ok=True)
CLOUD_LOCAL.mkdir(parents=True, exist_ok=True)

GREEN = "#0B6B4F"
GREEN_DARK = "#084C39"
GREEN_LIGHT = "#DCEBE4"
GRAY = "#A4ADA8"
LIGHT_GRAY = "#DDE4E0"
INK = "#17231E"
MUTED = "#65736C"
ORANGE = "#B96238"
ORANGE_LIGHT = "#E8CDBF"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_kitti(path):
    a = np.loadtxt(path, dtype=np.float64)
    t = np.tile(np.eye(4), (len(a), 1, 1))
    t[:, :3, :] = a.reshape(-1, 3, 4)
    return t


def camera_to_lidar(poses, seq):
    lines = (DATASET / "sequences" / seq / "calib.txt").read_text().splitlines()
    row = next(x for x in lines if x.startswith("Tr:"))
    tr = np.array([float(x) for x in row.split()[1:]], dtype=np.float64).reshape(3, 4)
    t = np.eye(4)
    t[:3] = tr
    t_inv = np.linalg.inv(t)
    converted = np.stack([t_inv @ pose @ t for pose in poses])
    return np.stack([np.linalg.inv(converted[0]) @ pose for pose in converted])


def estimate_to_first(poses):
    return np.stack([np.linalg.inv(poses[0]) @ pose for pose in poses])


def align_positions(source, target):
    xs = source.mean(axis=0)
    ys = target.mean(axis=0)
    h = (source - xs).T @ (target - ys) / len(source)
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    t = ys - r @ xs
    return source @ r.T + t


def style_axis(ax):
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#FBFCFB")
    for spine in ax.spines.values():
        spine.set_color("#D9E2DD")
        spine.set_linewidth(0.7)


def limits(points, margin=0.08):
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    span = np.maximum(hi - lo, 1.0)
    return lo - span * margin, hi + span * margin


def load_cloud(frame, max_range, sample, rng):
    # External scans are copied into the workspace first; only the copies are decoded.
    local = CLOUD_LOCAL / f"{frame:06d}.bin"
    a = np.fromfile(local, dtype=np.float32).reshape(-1, 4)
    xyz = a[:, :3].astype(np.float64)
    r = np.linalg.norm(xyz, axis=1)
    keep = (r > 3.0) & (r < max_range) & (xyz[:, 2] > -2.2) & (xyz[:, 2] < 3.5)
    xyz = xyz[keep]
    if len(xyz) > sample:
        xyz = xyz[rng.choice(len(xyz), sample, replace=False)]
    world = xyz @ gt_lidar[frame, :3, :3].T + gt_lidar[frame, :3, 3]
    return world


# ----- Verified trajectory geometry and source point-cloud copies -----
seq = "05"
gt_lidar = camera_to_lidar(load_kitti(DATASET / "poses" / f"{seq}.txt"), seq)
gt = gt_lidar[:, :3, 3]
reported = {
    (r["sequence"], r["mode"]): r["ate"]
    for r in json.loads(RESULTS.read_text(encoding="utf-8"))["rows"]
    if r["repeat"] == 1
}
pred, err = {}, {}
for mode in ["G", "K"]:
    poses = estimate_to_first(load_kitti(TRAJ / f"r1_{seq}_{mode}_lidar.txt"))
    assert len(poses) == len(gt_lidar)
    pred[mode] = align_positions(poses[:, :3, 3], gt)
    err[mode] = np.linalg.norm(pred[mode] - gt, axis=1)
    rmse = float(np.sqrt(np.mean(err[mode] ** 2)))
    assert abs(rmse - reported[(seq, mode)]) < 1e-8

start, stop = 1140, 1260
full_frames = sorted(set(range(0, len(gt), 50)) | {len(gt) - 1})
zoom_frames = list(range(max(0, start - 30), min(len(gt), stop + 31), 4))
needed = sorted(set(full_frames) | set(zoom_frames))
for frame in needed:
    dst = CLOUD_LOCAL / f"{frame:06d}.bin"
    if not dst.exists():
        shutil.copyfile(CLOUD_SOURCE / f"{frame:06d}.bin", dst)

rng = np.random.default_rng(20261101)
full_cloud = np.concatenate([load_cloud(f, 65.0, 1300, rng) for f in full_frames], axis=0)
zoom_cloud = np.concatenate([load_cloud(f, 45.0, 2600, rng) for f in zoom_frames], axis=0)
zoom_points = np.concatenate([gt[start:stop], pred["G"][start:stop], pred["K"][start:stop]])
zlo_full, zhi_full = limits(zoom_points, 0.16)
# Rotate only the zoom presentation so the road uses the wide panel; geometry is unchanged.
zoom_center = gt[start:stop].mean(axis=0)
_, _, zoom_vt = np.linalg.svd(gt[start:stop, :2] - zoom_center[:2], full_matrices=False)
zoom_direction = zoom_vt[0]
theta = np.arctan2(zoom_direction[1], zoom_direction[0])
zoom_rot = np.array([[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]])


def rotate_zoom(points):
    out = points.copy()
    out[:, :2] = (points[:, :2] - zoom_center[:2]) @ zoom_rot.T
    return out


zoom_cloud = rotate_zoom(zoom_cloud)
gt_zoom = rotate_zoom(gt)
pred_zoom = {mode: rotate_zoom(points) for mode, points in pred.items()}
zlo, zhi = limits(rotate_zoom(zoom_points), 0.16)

fig = plt.figure(figsize=(18, 7.4), dpi=220)
axes = np.array([
    [fig.add_axes([0.02, 0.56, 0.17, 0.32]), fig.add_axes([0.23, 0.56, 0.75, 0.32])],
    [fig.add_axes([0.02, 0.14, 0.17, 0.32]), fig.add_axes([0.23, 0.14, 0.75, 0.32])],
])
panel_info = [
    (axes[0, 0], "G", "全局 · RAP-SLAM", f"ATE  {reported[(seq, 'G')]:.3f} m", False),
    (axes[0, 1], "G", f"局部 {start}–{stop - 1} · RAP-SLAM", f"平均误差  {err['G'][start:stop].mean():.3f} m", True),
    (axes[1, 0], "K", "全局 · KISS-SLAM", f"ATE  {reported[(seq, 'K')]:.3f} m", False),
    (axes[1, 1], "K", f"局部 {start}–{stop - 1} · KISS-SLAM", f"平均误差  {err['K'][start:stop].mean():.3f} m", True),
]
for ax, mode, title, metric, is_zoom in panel_info:
    style_axis(ax)
    cloud = zoom_cloud if is_zoom else full_cloud
    ax.scatter(cloud[:, 0], cloud[:, 1], s=0.50 if is_zoom else 0.30,
               c="#B6C2BB" if is_zoom else "#AFBDB5", alpha=0.66 if is_zoom else 0.52, linewidths=0, rasterized=True)
    color = GREEN if mode == "G" else ORANGE
    if is_zoom:
        sl = slice(start, stop)
        ax.plot(gt_zoom[sl, 0], gt_zoom[sl, 1], color=INK, lw=1.25, alpha=0.88, zorder=3)
        ax.plot(pred_zoom[mode][sl, 0], pred_zoom[mode][sl, 1], color=color, lw=1.75, alpha=0.98, zorder=4)
        ax.set_xlim(zlo[0], zhi[0])
        ax.set_ylim(zlo[1], zhi[1])
    else:
        ax.plot(gt[:, 0], gt[:, 1], color=INK, lw=0.85, alpha=0.82, zorder=3)
        ax.plot(pred[mode][:, 0], pred[mode][:, 1], color=color, lw=1.15, alpha=0.97, zorder=4)
        ax.add_patch(Rectangle((zlo_full[0], zlo_full[1]), zhi_full[0] - zlo_full[0], zhi_full[1] - zlo_full[1],
                               fill=False, edgecolor=ORANGE, lw=1.0, zorder=5))
        all_points = np.concatenate([gt, pred["G"], pred["K"]])
        lo, hi = limits(all_points, 0.05)
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
    ax.set_title(title, fontsize=12.5, color=INK, weight="bold", pad=18)
    ax.text(0.5, 1.015, metric, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=10.5, color=color, weight="bold")

fig.text(0.5, 0.97, "真实点云 + 分栏轨迹对照 · 局部统一旋转至水平视角", ha="center", fontsize=11, color=MUTED)
legend = [
    Line2D([0], [0], color=INK, lw=1.4, label="GT"),
    Line2D([0], [0], color=GREEN, lw=1.8, label="RAP-SLAM"),
    Line2D([0], [0], color=ORANGE, lw=1.8, label="KISS-SLAM"),
    Line2D([0], [0], marker="s", color="none", markerfacecolor="#BFCAC4", markersize=7, label="真实点云"),
]
fig.legend(handles=legend, loc="lower center", ncol=4, frameon=False, fontsize=10.5, bbox_to_anchor=(0.5, 0.005))
fig.savefig(MEDIA / "trajectory_pointcloud_05.png", facecolor="white", bbox_inches="tight", pad_inches=0.08)
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
for panel_name, (ax, *_rest) in zip(["rap_global", "rap_zoom", "kiss_global", "kiss_zoom"], panel_info):
    bbox = ax.get_tightbbox(renderer).transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(MEDIA / f"trajectory_05_{panel_name}.png", facecolor="white",
                bbox_inches=bbox.expanded(1.04, 1.14), pad_inches=0.04)
plt.close(fig)

# ----- Overview benchmark bars -----
means = json.loads((MEDIA / "horizontal_means.json").read_text(encoding="utf-8"))
ate_names = ["SC-KISS-ICP", "PIN-SLAM", "RAP-SLAM", "HLBA", "KISS-SLAM", "MULLS", "SuMa"]
ter_names = ["CT-ICP", "MULLS-SLAM", "RAP-SLAM", "KISS-SLAM", "SuMa++", "LiTAMIN2", "LOAM"]
fig, axes = plt.subplots(1, 2, figsize=(16, 3.6), dpi=220)
for ax, names, key, title, unit in [
    (axes[0], ate_names, "ATE", "ATE / m · 同六序列均值 ↓", "m"),
    (axes[1], ter_names, "ter", "ter / % · 同六序列均值 ↓", "%"),
]:
    values = [means[key][n] for n in names]
    y = np.arange(len(names))[::-1]
    colors = [GREEN if n == "RAP-SLAM" else (GRAY if n == "KISS-SLAM" else "#DCE4E0") for n in names]
    ax.barh(y, values, height=0.62, color=colors, edgecolor="none")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5, color=INK)
    for tick, name in zip(ax.get_yticklabels(), names):
        if name == "RAP-SLAM":
            tick.set_color(GREEN_DARK)
            tick.set_weight("bold")
    for yy, value, name in zip(y, values, names):
        ax.text(value + max(values) * 0.015, yy, f"{value:.4f}" if key == "ATE" else f"{value:.3f}",
                va="center", ha="left", fontsize=9.2, color=GREEN_DARK if name == "RAP-SLAM" else MUTED,
                weight="bold" if name == "RAP-SLAM" else "normal")
    ax.set_title(title, loc="left", fontsize=12.2, color=INK, weight="bold", pad=8)
    ax.set_xlim(0, max(values) * 1.20)
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_facecolor("white")
fig.subplots_adjust(left=0.105, right=0.985, top=0.84, bottom=0.04, wspace=0.28)
fig.savefig(MEDIA / "overview_benchmarks.png", facecolor="white", bbox_inches="tight", pad_inches=0.04)
plt.close(fig)

# ----- MCV1 mechanism figure, restyled for this deck -----
fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), dpi=220, gridspec_kw={"width_ratios": [1.08, 1]})
ax = axes[0]
ax.set_title("重复结构：局部满秩仍可能对应错误身份", loc="left", fontsize=11.5, color=INK, weight="bold", pad=10)
for x, color, label in [(0.0, GREEN, "结构 A"), (4.0, ORANGE, "结构 B")]:
    ax.scatter([x, x + 1.4, x, x + 1.4], [1.3, 1.3, 0.0, 0.0], s=72, color=color, zorder=3)
    ax.plot([x, x + 1.4], [1.3, 1.3], ls="--", lw=1.0, color="#B8C3BD")
    ax.plot([x, x + 1.4], [0.0, 0.0], ls="--", lw=1.0, color="#B8C3BD")
    ax.text(x + 0.7, 1.65, label, ha="center", fontsize=10, color=color, weight="bold")
ax.annotate("两个不一致变换\n均可零残差、局部满秩", xy=(2.7, 0.65), ha="center", va="center",
            fontsize=10.2, color=MUTED, linespacing=1.4)
ax.set_xlim(-0.7, 6.1)
ax.set_ylim(-0.65, 2.1)
ax.axis("off")

ax = axes[1]
ax.set_title("PCS1 A：所有可用输出均满足局部满秩", loc="left", fontsize=11.5, color=INK, weight="bold", pad=10)
names = ["正确回环", "错误回环", "非回环"]
values = [70, 65, 20]
colors = [GREEN, ORANGE, GRAY]
bars = ax.bar(names, values, color=colors, width=0.58)
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 2, str(value), ha="center", fontsize=12, color=INK, weight="bold")
ax.set_ylim(0, 82)
ax.set_yticks([0, 20, 40, 60, 80])
ax.tick_params(axis="x", labelsize=9.5, length=0, colors=INK)
ax.tick_params(axis="y", labelsize=8, length=0, colors=MUTED)
ax.grid(axis="y", color="#E5EBE8", lw=0.7)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_visible(False)
fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.12, wspace=0.18)
fig.savefig(MEDIA / "mcv1_mechanism.png", facecolor="white", bbox_inches="tight", pad_inches=0.05)
plt.close(fig)

summary = {
    "sequence": seq,
    "ATE": {"RAP-SLAM": reported[(seq, "G")], "KISS-SLAM": reported[(seq, "K")]},
    "zoom": {
        "start": start,
        "stop": stop,
        "RAP-SLAM_mean_error": float(err["G"][start:stop].mean()),
        "KISS-SLAM_mean_error": float(err["K"][start:stop].mean()),
    },
    "cloud_frames": {"full": full_frames, "zoom": zoom_frames},
    "cloud_points": {"full": int(len(full_cloud)), "zoom": int(len(zoom_cloud))},
    "MCV1_PCS1_A_full_rank": {"correct": 70, "wrong": 65, "nonloop": 20},
}
(MEDIA / "weekly_visual_data.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
