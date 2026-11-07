"""[meeting-20260921] Supplementary figure (PPT page 7): front-end convention
alignment effect on KITTI ter, three sequences, neutral wording."""
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

SEQS = ["00", "05", "06"]
BASE = {"00": 0.91, "05": 0.70, "06": 0.67}      # core-baseline-v1 (HC-V1)
KISS = {"00": 0.575, "05": 0.517, "06": 0.325}   # KISS-SLAM same-data run

mm = json.load(open(os.path.join(HERE, "meeting_metrics.json")))
OURS = {s: mm[f"output_meeting/kitti{s}_armB"]["full"]["kitti_ter_pct"]
        for s in SEQS}
OURS_ODOM = {s: mm[f"output_meeting/kitti{s}_armB"]["odometry"]["kitti_ter_pct"]
             for s in SEQS}

x = np.arange(len(SEQS))
w = 0.2
fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)
ax.bar(x - 1.5 * w, [BASE[s] for s in SEQS], w, label="RAP-SLAM（校正前基线）",
       color="#bdbdbd")
ax.bar(x - 0.5 * w, [OURS_ODOM[s] for s in SEQS], w,
       label="RAP-SLAM 里程计（本分支）", color="#9ecae1")
ax.bar(x + 0.5 * w, [OURS[s] for s in SEQS], w,
       label="RAP-SLAM 完整系统（本分支）", color="#2171b5")
ax.bar(x + 1.5 * w, [KISS[s] for s in SEQS], w,
       label="KISS-SLAM（同数据实测）", color="#fb6a4a")
for xi, s in zip(x, SEQS):
    for dx, d in [(-1.5, BASE), (-0.5, OURS_ODOM), (0.5, OURS), (1.5, KISS)]:
        ax.text(xi + dx * w, d[s] + 0.012, f"{d[s]:.3f}", ha="center",
                fontsize=7.5)
ax.set_xticks(x)
ax.set_xticklabels([f"KITTI {s}" for s in SEQS])
ax.set_ylabel("KITTI 官方相对平移漂移 ter (%)")
ax.set_ylim(0, 1.0)
ax.legend(fontsize=9, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
out = os.path.join(HERE, "assets", "fig_frontend_alignment.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("saved", out)
print("ours full ter:", {s: round(OURS[s], 3) for s in SEQS})
