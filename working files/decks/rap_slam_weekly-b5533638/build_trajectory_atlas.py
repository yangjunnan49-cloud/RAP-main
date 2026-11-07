import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

DECK = Path(__file__).resolve().parent
ROOT = DECK.parents[2]
TRAJ = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/trajectory_exports"
GT = ROOT / ".maintenance-archive/2026-09-09-m0/files/Datasets-metadata/data_odometry_velodyne/dataset"
RESULTS = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01/results06.json"
MEDIA = DECK / "media"
MEDIA.mkdir(exist_ok=True)
SEQS = ["00", "05", "09", "06", "07", "10"]
ADVANTAGE = {"00", "05", "09"}
GREEN = "#0B6B4F"
GRAY = "#979F9B"
INK = "#17231E"
ORANGE = "#B96238"


def load_kitti(path):
    a = np.loadtxt(path, dtype=np.float64)
    t = np.tile(np.eye(4), (len(a), 1, 1))
    t[:, :3, :] = a.reshape(-1, 3, 4)
    return t


def camera_to_lidar(poses, seq):
    lines = (GT / "sequences" / seq / "calib.txt").read_text().splitlines()
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


def limits(points, margin=0.08):
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    span = np.maximum(hi - lo, 1.0)
    return lo - span * margin, hi + span * margin


def style_axis(ax):
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#DDE4E0")
        spine.set_linewidth(0.6)
    ax.set_facecolor("white")


reported = {
    (r["sequence"], r["mode"]): r["ate"]
    for r in json.loads(RESULTS.read_text(encoding="utf-8"))["rows"]
    if r["repeat"] == 1
}
fig, axes = plt.subplots(2, 6, figsize=(18, 7.4), dpi=220)
details = {}
for col, seq in enumerate(SEQS):
    gt_camera = load_kitti(GT / "poses" / f"{seq}.txt")
    gt_lidar = camera_to_lidar(gt_camera, seq)
    gt = gt_lidar[:, :3, 3]
    pred = {}
    err = {}
    for mode in ["G", "K"]:
        poses = estimate_to_first(load_kitti(TRAJ / f"r1_{seq}_{mode}_lidar.txt"))
        assert len(poses) == len(gt_lidar)
        pred[mode] = align_positions(poses[:, :3, 3], gt)
        err[mode] = np.linalg.norm(pred[mode] - gt, axis=1)
        rmse = float(np.sqrt(np.mean(err[mode] ** 2)))
        assert abs(rmse - reported[(seq, mode)]) < 1e-8, (seq, mode, rmse, reported[(seq, mode)])
    n = len(gt)
    window = max(50, min(140, n // 18))
    score = err["K"] - err["G"] if seq in ADVANTAGE else err["G"] - err["K"]
    smooth = np.convolve(score, np.ones(window) / window, mode="valid")
    start = int(np.argmax(smooth))
    stop = start + window
    full_ax = axes[0 if seq in ADVANTAGE else 1, col]
    # Bottom row is re-indexed below to keep three advantage and three weakness groups together.
    details[seq] = dict(start=start, stop=stop, G_local_mean=float(err["G"][start:stop].mean()), K_local_mean=float(err["K"][start:stop].mean()), G_ATE=reported[(seq, "G")], K_ATE=reported[(seq, "K")])

# Rebuild with explicit group rows: top 00/05/09, bottom 06/07/10.
plt.close(fig)
fig, axes = plt.subplots(2, 6, figsize=(18, 7.4), dpi=220)
for row, group in enumerate([SEQS[:3], SEQS[3:]]):
    for pair_index, seq in enumerate(group):
        gt_camera = load_kitti(GT / "poses" / f"{seq}.txt")
        gt = camera_to_lidar(gt_camera, seq)[:, :3, 3]
        pred, err = {}, {}
        for mode in ["G", "K"]:
            poses = estimate_to_first(load_kitti(TRAJ / f"r1_{seq}_{mode}_lidar.txt"))
            pred[mode] = align_positions(poses[:, :3, 3], gt)
            err[mode] = np.linalg.norm(pred[mode] - gt, axis=1)
        d = details[seq]
        start, stop = d["start"], d["stop"]
        full = axes[row, pair_index * 2]
        zoom = axes[row, pair_index * 2 + 1]
        for ax in [full, zoom]:
            style_axis(ax)
            ax.plot(gt[:, 0], gt[:, 1], color=INK, lw=0.65, alpha=0.72, zorder=1)
            ax.plot(pred["K"][:, 0], pred["K"][:, 1], color=GRAY, lw=0.9, alpha=0.95, zorder=2)
            ax.plot(pred["G"][:, 0], pred["G"][:, 1], color=GREEN, lw=1.0, alpha=0.98, zorder=3)
        selected = np.concatenate([gt[start:stop], pred["G"][start:stop], pred["K"][start:stop]])
        lo, hi = limits(selected, 0.16)
        full.add_patch(Rectangle((lo[0], lo[1]), hi[0]-lo[0], hi[1]-lo[1], fill=False, edgecolor=ORANGE, lw=1.0, zorder=4))
        zoom.set_xlim(lo[0], hi[0])
        zoom.set_ylim(lo[1], hi[1])
        full.set_title(f"{seq}  FULL\nATE  RAP {d['G_ATE']:.3f} | KISS {d['K_ATE']:.3f} m", fontsize=10.2, color=INK, pad=5)
        relation = "RAP closer" if seq in ADVANTAGE else "KISS closer"
        zoom.set_title(f"ZOOM  {start}–{stop-1}\n{relation}: {d['G_local_mean']:.2f} | {d['K_local_mean']:.2f} m", fontsize=9.5, color=GREEN if seq in ADVANTAGE else ORANGE, pad=5)
        for ax in [full, zoom]:
            ax.tick_params(length=0)
fig.text(0.012, 0.74, "ADVANTAGE  ·  00 / 05 / 09", rotation=90, va="center", ha="center", fontsize=11, color=GREEN, weight="bold")
fig.text(0.012, 0.26, "FOCUS  ·  06 / 07 / 10", rotation=90, va="center", ha="center", fontsize=11, color=ORANGE, weight="bold")
legend = [Line2D([0], [0], color=INK, lw=1.2, label="GT"), Line2D([0], [0], color=GREEN, lw=1.8, label="RAP-SLAM"), Line2D([0], [0], color=GRAY, lw=1.5, label="KISS-SLAM"), Line2D([0], [0], color=ORANGE, lw=1.2, label="Zoom region")]
fig.legend(handles=legend, loc="upper center", ncol=4, frameon=False, fontsize=11, bbox_to_anchor=(0.52, 0.995))
fig.subplots_adjust(left=0.035, right=0.995, top=0.88, bottom=0.035, wspace=0.24, hspace=0.52)
fig.savefig(MEDIA / "trajectory_atlas.png", facecolor="white", bbox_inches="tight", pad_inches=0.08)
plt.close(fig)
(MEDIA / "trajectory_atlas_details.json").write_text(json.dumps(details, indent=2), encoding="utf-8")

idx = [0, 5, 6, 7, 9, 10]
ate_source = json.loads((ROOT / "docs/maintenance/2026-09-19/horizontal-comparison-01/data-literature/kitti_ate_pin_slam_tab4.json").read_text(encoding="utf-8"))
ate = {name: float(np.mean(np.array(values["ate"])[idx])) for name, values in ate_source["methods"].items()}
ate.update({"RAP-SLAM": 0.6483341409634862, "KISS-SLAM": 0.6989917123598139})
ter_rows = {
    "LOAM": [0.78, 0.57, 0.65, 0.63, 0.77, 0.79],
    "SuMa": [0.68, 0.43, 0.54, 0.74, 0.62, 0.72],
    "SuMa++": [0.64, 0.40, 0.46, 0.34, 0.47, 0.66],
    "LiTAMIN2": [0.70, 0.45, 0.59, 0.44, 0.69, 0.80],
    "MULLS-SLAM": [0.54, 0.29, 0.29, 0.27, 0.51, 0.61],
    "CT-ICP": [0.49, 0.25, 0.27, 0.31, 0.49, 0.48],
    "RAP-SLAM": [0.573657038, 0.321078493, 0.331791807, 0.407228723, 0.519444038, 0.528519905],
    "KISS-SLAM": [0.574511281, 0.517251809, 0.325492815, 0.386563401, 0.542079976, 0.525042648],
}
ter = {name: float(np.mean(values)) for name, values in ter_rows.items()}
(MEDIA / "horizontal_means.json").write_text(json.dumps({"ATE": ate, "ter": ter}, indent=2), encoding="utf-8")
print(json.dumps({"trajectories": details, "ATE": ate, "ter": ter}, indent=2))
