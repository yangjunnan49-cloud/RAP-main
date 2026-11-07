"""[meeting-20260921] Build the innovation-detail figure (PPT page 3):
front/back-end unified representation + RAP generative loop verification.

Panels (all real data, KITTI-06 loop pair frames 150/978, meeting arm B):
  A: unified scan representation - preprocessed scan + its Scan Context
     descriptor (the shared front/back-end representation)
  B: loop candidate pair under the odometry prior (visible misalignment)
  C: same pair after RAP verification transform (aligned)
"""
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))
from daimon_runtime import setup_plot  # noqa: E402
setup_plot()
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SLAM = "E:/githouse/RAP-SLAM"
SEQ = "00"
FI, FJ = 597, 3552


def load_bin(seq, frame):
    p = f"E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences/{seq}/velodyne/{frame:06d}.bin"
    return np.fromfile(p, dtype=np.float32).reshape(-1, 4)[:, :3].astype(np.float64)


def kitti205(points, angle_deg=0.205):
    t = np.deg2rad(angle_deg)
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    rho = np.hypot(x, y)
    safe = rho > 1e-6
    c, s = np.cos(t), np.sin(t)
    out = points.copy()
    sxz = np.where(safe, x * z / np.maximum(rho, 1e-6), 0.0)
    syz = np.where(safe, y * z / np.maximum(rho, 1e-6), 0.0)
    out[:, 0] = np.where(safe, x * c - sxz * s, x)
    out[:, 1] = np.where(safe, y * c - syz * s, y)
    out[:, 2] = np.where(safe, z * c + np.where(safe, rho, 0.0) * s, z)
    return out


def voxel_down(pts, v=0.4):
    key = np.floor(pts / v).astype(np.int64)
    _, idx = np.unique(key, axis=0, return_index=True)
    return pts[np.sort(idx)]


def load_poses(path):
    rows = [list(map(float, l.split())) for l in open(path)]
    return np.array([np.vstack([np.array(r).reshape(3, 4), [0, 0, 0, 1]])
                     for r in rows])


def scan_context(pts, rings=20, sectors=60, max_r=80.0):
    rho = np.hypot(pts[:, 0], pts[:, 1])
    theta = np.arctan2(pts[:, 1], pts[:, 0])
    r_bin = np.clip((rho / max_r * rings).astype(int), 0, rings - 1)
    s_bin = np.clip(((theta + np.pi) / (2 * np.pi) * sectors).astype(int),
                    0, sectors - 1)
    sc = np.zeros((rings, sectors))
    np.maximum.at(sc, (r_bin, s_bin), pts[:, 2] + 2.0)  # shift above ground
    return sc


def main():
    si = voxel_down(kitti205(load_bin(SEQ, FI)))
    sj = voxel_down(kitti205(load_bin(SEQ, FJ)))
    odom = load_poses(f"{SLAM}/output_meeting/kitti{SEQ}_armB/odom_poses.txt")
    loops = json.load(open(f"{SLAM}/output_meeting/kitti{SEQ}_armB/accepted_loops.json"))
    loop = [l for l in loops if l["i"] == FI and l["j"] == FJ][0]
    T_rel = np.array(loop["T_rel"])

    wi = odom[FI] @ np.vstack([si.T, np.ones(len(si))])
    wj_prior = odom[FJ] @ np.vstack([sj.T, np.ones(len(sj))])
    wj_corr = (odom[FI] @ T_rel) @ np.vstack([sj.T, np.ones(len(sj))])

    cx, cy = odom[FI][0, 3], odom[FI][1, 3]
    R = 60.0
    PS = 0.6

    def crop(w):
        m = (np.abs(w[0] - cx) < R) & (np.abs(w[1] - cy) < R)
        return w[:, m]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), dpi=200)

    # A: unified representation
    ax = axes[0]
    m = np.hypot(si[:, 0], si[:, 1]) < 80
    ax.scatter(si[m, 0], si[m, 1], c=si[m, 2], s=0.3, cmap="viridis",
               linewidths=0)
    ax.set_title("统一预处理后的扫描表示\n(体素 0.4 m + 统计滤波 + 归一化)", fontsize=11)
    ax.set_aspect("equal")
    inset = ax.inset_axes([0.55, 0.02, 0.43, 0.30])
    inset.imshow(scan_context(si), cmap="magma", origin="lower",
                 aspect="auto")
    inset.set_title("Scan Context 描述子", fontsize=8)
    inset.set_xticks([]); inset.set_yticks([])

    # B: odometry prior
    ax = axes[1]
    a, b = crop(wi), crop(wj_prior)
    ax.scatter(a[0], a[1], s=PS, c="#1f77b4", linewidths=0,
               label=f"帧 {FI}（历史关键帧）")
    ax.scatter(b[0], b[1], s=PS, c="#d62728", linewidths=0,
               label=f"帧 {FJ}（重访帧）")
    ax.set_title(f"里程计先验下的回环候选\n先验误差 "
                 f"{loop['odom_trans_err']:.2f} m / "
                 f"{loop['odom_rot_err_deg']:.2f}°",
                 fontsize=11)
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper right", markerscale=6)

    # C: after RAP
    ax = axes[2]
    a, b = crop(wi), crop(wj_corr)
    ax.scatter(a[0], a[1], s=PS, c="#1f77b4", linewidths=0)
    ax.scatter(b[0], b[1], s=PS, c="#d62728", linewidths=0)
    ax.set_title(f"RAP 生成式验证后（对真值误差 "
                 f"{loop['gt_trans_err']:.2f} m / "
                 f"{loop['gt_rot_err_deg']:.2f}°）\n"
                 f"重叠率 {loop['overlap']:.2f}，平均对应距离 "
                 f"{loop['mean_dist']:.2f} m → 验收通过",
                 fontsize=11)
    ax.set_aspect("equal")

    for ax in axes:
        ax.set_facecolor("white")
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    out = os.path.join(HERE, "assets", "fig_innovation_unified.png")
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    print("saved", out)


if __name__ == "__main__":
    main()
