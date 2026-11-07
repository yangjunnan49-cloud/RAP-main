"""[meeting-20260921] Render merged SLAM maps (PLY) to presentation figures.

Pure numpy PLY (binary_little_endian, xyz double) parser + matplotlib
projection. No Open3D needed on Windows.

Outputs (into docs/meeting_20260921/assets/):
  seqXX_ours_render_topdown.png  -- orthographic top view, height-colored
  seq00_ours_render_aerial.png   -- oblique aerial view (new viewpoint,
                                    never shown in past meetings)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SLAM = "E:/githouse/RAP-SLAM/output_meeting"


def load_ply_xyz(path):
    with open(path, "rb") as f:
        header = b""
        while not header.endswith(b"end_header\n"):
            header += f.read(1)
        text = header.decode("latin1")
        n = int([l.split()[2] for l in text.splitlines()
                 if l.startswith("element vertex")][0])
        data = np.frombuffer(f.read(n * 24), dtype="<f8").reshape(n, 3)
    return data


def style_ax(ax):
    ax.set_facecolor("white")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def render_topdown(pts, path, max_pts=400000, s=0.25):
    if len(pts) > max_pts:
        idx = np.random.default_rng(0).choice(len(pts), max_pts, replace=False)
        pts = pts[idx]
    z = pts[:, 2]
    zlo, zhi = np.percentile(z, [2, 98])
    fig, ax = plt.subplots(figsize=(8, 8), dpi=200)
    ax.scatter(pts[:, 0], pts[:, 1], c=np.clip(z, zlo, zhi), s=s,
               cmap="viridis", linewidths=0, rasterized=True)
    ax.set_aspect("equal"); style_ax(ax)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02,
                facecolor="white")
    plt.close(fig)
    print("saved", path)


def render_aerial(pts, path, yaw_deg=25.0, tilt_deg=55.0, max_pts=500000,
                  s=0.3):
    """Oblique aerial view: rotate about z, then tilt the ground plane."""
    if len(pts) > max_pts:
        idx = np.random.default_rng(1).choice(len(pts), max_pts, replace=False)
        pts = pts[idx]
    yaw = np.deg2rad(yaw_deg)
    c, sn = np.cos(yaw), np.sin(yaw)
    x = c * pts[:, 0] - sn * pts[:, 1]
    y = sn * pts[:, 0] + c * pts[:, 1]
    z = pts[:, 2]
    tilt = np.deg2rad(tilt_deg)
    sy = y * np.cos(tilt) + (z - z.mean()) * np.sin(tilt)
    depth = y * np.sin(tilt) - (z - z.mean()) * np.cos(tilt)
    order = np.argsort(depth)  # far first (painter's algorithm)
    zc = np.clip(z, *np.percentile(z, [2, 98]))
    fig, ax = plt.subplots(figsize=(10, 7), dpi=200)
    ax.scatter(x[order], sy[order], c=zc[order], s=s, cmap="viridis",
               linewidths=0, rasterized=True)
    ax.set_aspect("equal"); style_ax(ax)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02,
                facecolor="white")
    plt.close(fig)
    print("saved", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("kitti06_armB", "seq06_ours_render_topdown.png", render_topdown),
        ("kitti05_armB", "seq05_ours_render_topdown.png", render_topdown),
        ("kitti00_armB", "seq00_ours_render_topdown.png", render_topdown),
        ("kitti00_armB", "seq00_ours_render_aerial.png", render_aerial),
    ]
    for run, name, fn in jobs:
        ply = os.path.join(SLAM, run, "merged_map_optimized.ply")
        if not os.path.exists(ply):
            print("missing", ply); continue
        pts = load_ply_xyz(ply)
        print(run, pts.shape)
        fn(pts, os.path.join(OUT, name))


if __name__ == "__main__":
    sys.exit(main())
