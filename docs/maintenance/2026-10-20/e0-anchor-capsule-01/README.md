# Coarse-anchor preserving fine graph: experimental component

`anchor_fine.py` is a reusable extraction of the already-tested G fine correction. It has no repository path, dataset name, GT reader, learned model or package installation. The library function accepts odometry, initial trajectory, sorted anchor source-frame IDs, prescribed coarse poses and an explicit native pose-graph configuration. The CLI reads NumPy/JSON files and writes a fresh NumPy trajectory. Run in the existing Linux KISS-SLAM environment; this is not a Windows-native binary.

Validated environment: Python3.12, kiss-slam0.0.2, kiss-icp1.3.0, map-closures2.1.0, numpy2.2.6, open3d0.20.0. These describe the installed test environment, not permission or instructions to install/update packages. `pose_graph_config.json` is the exact tested `max_iterations:10`; no parameter tuning was performed. Existing selected source/native identities are bound in the parent LMB freeze; transitive native builds are not fully authenticated.

Example inside this directory, only after an explicit execution scope and the original host resource/cumulative-budget checks:

```sh
/root/venvs/kiss-slam-hc1/bin/python -B anchor_fine.py \
  --odometry cases/07/odometry.npy --initial cases/07/initial.npy \
  --anchors cases/07/anchors.json --config pose_graph_config.json \
  --output cases/07/G_new.npy
```

The example creates a new output; existing files are refused. It does not launch automatically. A single CLI has a60s ceiling and4GiB per-process check, but these do not replace the original cumulative LMB1800s account or Windows12GiB launch guard. This package does not grant permission to replay stopped experiments or reset their caps. Source poses are unaligned with GT; all frames are retained. Anchor IDs must include0, be sorted/unique/in range and match prescribed coarse poses. Input arrays must be finite homogeneous rigid transforms. No GT alignment, interpolation, pose selection or altered solver objective occurs.

The fine function is AST-identical to the original frozen `coarse_anchor_fine_control.py` after only adding the explicit configuration argument and replacing the repository config lookup. Six complete CLI runs reproduce every matrix of the already-sealed G00/05/06/07/09/10 output exactly: maximum difference0. EQUIVALENCE and FREEZE retain the proof and source identities. This verifies portability, not independent optimizer correctness or an accuracy improvement. The AST proof includes the numerical function, not the CLI/parser.

The case directory contains complete source O/initial/anchor inputs and returned G arrays for repeatable independent review. They are development trajectories, not independent scenes or reference truth. All G performance statements remain those of the original six-sequence comparison: mean owner target passes, extra07-ter/10-rer protection fails,06/10 ATE is >5% worse than KISS. Default B and installed packages remain unchanged. No new efficacy result or RAP increment follows from packaging. Original negative trials and all old stops remain.
