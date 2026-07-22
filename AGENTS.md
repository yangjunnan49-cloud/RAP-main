# AGENTS.md — RAP (Register Any Point)

> AI-agent notes for the RAP project. This file is intended for automated agents that need to understand, modify, or run code in this repository. The project uses English for all comments, documentation, and commit messages.

---

## Project Overview

**RAP** (Register Any Point) is a research codebase for 3D point cloud registration. It casts registration as a conditional generation problem: a learned continuous point-wise velocity field (a *rectified flow*) transports noisy points to a registered scene, from which the rigid pose of each input view is recovered. The repository currently provides inference code and pre-trained models; training code and data-curation code are listed as future work in the README.

Key facts:
- Repository: `https://github.com/PRBonn/RAP`
- Paper: "Register Any Point: Scaling 3D Point Cloud Registration by Flow Matching" (arXiv:2512.01850)
- License: MIT
- Main language/framework: Python 3.10, PyTorch 2.5.1, Lightning 2.5.2
- Alternative stack for NVIDIA Blackwell (RTX 50-series): Python 3.10, PyTorch 2.7.0, CUDA 12.8
- Configuration: Hydra 1.3.2 (YAML-based)
- Entry points:
  - `sample.py` — batch/CLI inference
  - `app.py` — Gradio web demo
  - `demo.py` — folder-based preprocessing + inference
  - `test_smoke.py` — dependency-free model smoke test (no checkpoint needed)

**Important packaging note:** there is **no** `pyproject.toml`, `setup.py`, or `setup.cfg` — this repo is **not** a pip-installable package. All scripts rely on running from the repo root (they do `sys.path.insert(0, current_dir)`), and imports like `rectified_point_flow.*` resolve because the repo root is the working directory.

**Important config gotcha:** `sample.py` declares `config_name="RAP_base"` as its Hydra default, but `config/RAP_base.yaml` does **not** exist in this repository — only `config/RAP_inference.yaml` ships. Therefore you **must** always pass `--config-name RAP_inference` (as `scripts/test_script_example.sh` does), otherwise Hydra fails immediately.

---

## RAP-SLAM Sister Project — Handoff State (read this first if continuing SLAM work)

The owner's goal is a **non-realtime SLAM system around RAP as the registration engine**. That work lives in a **sibling directory** `E:\githouse\RAP-SLAM` (WSL: `/mnt/e/githouse/RAP-SLAM`), kept separate from this repo. **Rule: `RAP-main` is read-only for that project** (imported via `sys.path`); all new code goes to `RAP-SLAM`. See `RAP-SLAM/README.md` for full details.

### Status: Phase 1 + real-sequence validation DONE; Scan Context loop retrieval DONE; N-way backend first comparison DONE (2026-07-20)

Pipeline: `preprocess → KISS-ICP odometry → keyframe selection → Scan Context global + proximity loop candidates → RAP 2-way verification (or N-way joint batch registration) → GTSAM PGO → evo APE/RPE + merged map`. Entry point: `RAP-SLAM/scripts/run_pipeline.py`. All six stages verified end-to-end three times.

### Phase 2 STARTED (2026-07-21): ROS 2 Jazzy + RViz — Step 0+1+2 DONE

- **Both repos now on GitHub** (private, owner account): `YCDJ/RAP` (upstream snapshot + Blackwell patches) and `YCDJ/RAP-SLAM` (original pipeline). Local dirs are git repos; `data/` and `output*/` are gitignored.
- **Step 0**: `RAP-SLAM/scripts/install_ros2_jazzy.sh` — idempotent Jazzy installer for WSL2 Ubuntu 24.04; auto-probes apt mirrors (TUNA → Aliyun → official) + rosdistro key sources. Installed & verified in WSL2: ros-base, rviz2, ros2cli, demo nodes, sensor-msgs-py, colcon. Talker/listener DDS check passed. WSLg present (`DISPLAY=:0`).
- **Step 1**: `RAP-SLAM/ros2/` — `pointcloud_player.py` (standalone rclpy node, no colcon: POSS/KITTI `.bin` → `/points_raw` PointCloud2 with xyz+intensity; Reliable QoS to match RViz default), `rviz/rap_slam.rviz`, `run_step1.sh` (one-command player + RViz). Verified headless: 1419 POSS scans publish correctly; effective rate caps at ~10 Hz due to `.tolist()` conversion (= native LiDAR rate, fine). **Owner confirmed GUI working 2026-07-21 (after WSLg restart).**
- **Step 2** (2026-07-21): `ros2/odometry_node.py` — KISS-ICP wrapped as rclpy node reusing `rap_slam.odometry.KissOdometry` with the offline pipeline's exact params (**`max_range=80.0`**, min_range 1.5, voxel 0.8). Subscribes `/points_raw` → publishes `/odom` (nav_msgs/Odometry), `/odom_path` (nav_msgs/Path), TF `odom→base_link` + static `base_link→velodyne`. RViz config now fixed frame `odom` + Path display. `run_step2.sh` = player + odometry + RViz; `verify_step2_headless.sh` = no-GUI regression vs `output_poss/odom_poses.txt`. **Verified: full 1419-frame POSS segment, live trajectory numerically identical to offline (max diff 1e-6 m); KISS-ICP 18–45 ms/scan, real-time at native 10 Hz.** Deps: `kiss-icp==1.3.0` into **system python3** via `pip --break-system-packages --ignore-installed typing_extensions ... 'numpy<2'`. GUI run: `bash /mnt/e/githouse/RAP-SLAM/ros2/run_step2.sh`.
- Gotchas recorded in `RAP-SLAM/ros2/README.md`: never source ROS `setup.bash` under `set -u`; RViz PointCloud2 default Reliable QoS (player matches it deliberately); **WSLg can wedge so that NO GUI window shows at all (even `xeyes` exits silently) — fix is `wsl --shutdown` from PowerShell**; do not hand-write `Window Geometry`/`QMainWindow State` blobs into `.rviz` files (off-screen/zero-size windows); `RVIZ_SOFTWARE=1 bash run_step2.sh` (LIBGL_ALWAYS_SOFTWARE) is the fallback when OGRE windows stay invisible; start odometry node BEFORE the player (wait for "KISS-ICP odometry up" log) or the first scans are missed; WSL `/tmp` can be wiped between `wsl` invocations — keep state in the repo or `/mnt/e`.
- Next: Step 3 — loop-closure + PGO nodes with `map→odom` correction TF + loop-edge markers.

#### Session handoff addendum (2026-07-22, end of session)

**Immediate next action (agreed with owner): Step 3 — loop-closure + PGO nodes.** Subscribe `/points_raw` (or keyframe topic), run Scan Context + proximity loop candidates, verify with RAP, optimize with GTSAM, publish `map→odom` correction TF and loop-edge markers so RViz shows the trajectory snapping into place on loop closure. Runs on local data: POSS segment (`data/poss/...`) and/or KITTI seq 01–04 (now available, see below); does NOT need the rest of the KITTI download.

**Done this session (2026-07-22):**
- **Step 2 complete + verified headless**: full 1419-frame POSS segment through player + `ros2/odometry_node.py`, live trajectory numerically identical to the offline pipeline (max diff 1e-6 m); KISS-ICP 18–45 ms/scan, real-time at native 10 Hz. GUI demo: `bash /mnt/e/githouse/RAP-SLAM/ros2/run_step2.sh`. Deps: `kiss-icp==1.3.0` installed into WSL **system python3** (with rclpy) via `pip --break-system-packages --ignore-installed typing_extensions 'numpy<2'`.
- **KITTI velodyne cleaned & assembled**: owner-provided partial extraction at `E:\githouse\Datasets\data_odometry_velodyne` (WSL: `/mnt/e/githouse/Datasets/...`). Kept complete seq **01, 02, 03, 04** (verified counts + contiguity + sample scans); deleted truncated 00/05; fixed one extraction artifact (`000001(1).bin` → `000001.bin` in seq 04). Copied poses 00–10 + calib/times for 01–04 into the tree → self-contained `--real-root`.
- **Fixed latent KITTI calib bug** (`rap_slam/real_dataset.py`): correct conversion is `Tr⁻¹ @ T_cam @ Tr` (was `Tr @ T @ Tr⁻¹`). KITTI 04 smoke (271 frames, 31.4 s): odometry APE 2.96 m / RPE 0.021 m; was 310.7 m pre-fix. Products in `output_kitti04_smoke/`.

**Owner pending:** completing the KITTI dataset (remaining sequences, esp. seq 06) at the same Datasets path. **Next session: re-check that dir first.** If new sequences appear: (1) sweep for `NNNNNN(1).bin` artifacts and rename, (2) verify per-sequence frame counts + contiguity against the canonical counts, (3) copy `poses/<seq>.txt` + `calib.txt` + `times.txt` from `RAP-SLAM/data/kitti/dataset/` into the tree, (4) smoke-run `run_pipeline.py --source real --real-root /mnt/e/githouse/Datasets/data_odometry_velodyne --real-seq <seq> --real-start 0 --real-end <last> --real-apply-calib`.

**Repo / sync state:**
- GitHub (private, owner account `YCDJ`): `YCDJ/RAP` and `YCDJ/RAP-SLAM`. Local dirs `E:\githouse\RAP-main` and `E:\githouse\RAP-SLAM` are git repos (branch `main`, remote `origin`, git identity `YCDJ <184950371+YCDJ@users.noreply.github.com>`, commit messages in English).
- RAP-SLAM pushed through `f387048` (calib fix); RAP pushed through this wrap-up commit. **On session start, check for unpushed commits in both repos: `git log origin/main..HEAD --oneline` — push if non-empty.** Pushes to github.com can be flaky while big downloads saturate the link; Windows GCM credentials work, retry-with-backoff succeeds. Use `GIT_TERMINAL_PROMPT=0`.

**ROS 2 environment (WSL2 `Ubuntu-24.04`, root):** Jazzy installed via `scripts/install_ros2_jazzy.sh` (ros-base, rviz2, ros2cli, demo-nodes, sensor-msgs-py, colcon, python3-numpy; x11-apps/xdotool/wmctrl added during debugging). Player + odometry node run with **system python3** (`/usr/bin/python3`, where rclpy + kiss-icp live), not the conda env. Offline pipeline runs in conda env `rap-inference`. Viz entry points: `run_step1.sh` (player only), `run_step2.sh` (player + odometry); headless regression: `ros2/verify_step2_headless.sh [n_frames]`; software-GL fallback: prefix `RVIZ_SOFTWARE=1`.

**Agent operational gotchas (Windows host → WSL):**
- When invoking `wsl` from Git Bash, prefix `MSYS_NO_PATHCONV=1` and prefer repo-relative paths (Git Bash mangles `/mnt/...` args into the Git install dir); do **not** pass URLs or `\$VAR`-bearing command lines inline into `wsl bash -c` (quoting gets eaten — write a script file instead).
- Filter WSL's harmless NAT warning with `grep -av 'localhost'` (output can look binary to grep).
- WSL `/tmp` can be wiped between `wsl` invocations — keep verification state in the repo (`output_ros2/`) or `/mnt/e`.


**Verified results (RTX 5070, WSL2):**

| Dataset | Setup | Odometry APE RMSE | After PGO | Notes |
|---|---|---|---|---|
| Simulated loop on real KITTI-00 map | 101 scans, 80 m radius circle | 5.53 m | **3.67 m** | smoke test, `output/` |
| **POSS real LiDAR** (Velodyne-32e campus) | 1419 frames [3850–5268], 413 m path, true loop | 8.26 m | **1.82 m (−78%)** | 4/4 loop candidates true & accepted; **RAP verification error vs GT only 0.15–0.47 m / 0.0°**; 67.9 s total, `output_poss/` |
| POSS, `--loop-method both` (SC + proximity merged) | same as above | 8.26 m | **1.82 m** | reproduces baseline exactly, `output_poss_sc/` |
| POSS, `--loop-dist 5` proximity-only | drift 13.3 m > radius | 8.26 m | **8.26 m (0 loops)** | controlled failure case, `output_poss_prox5/` |
| POSS, `--loop-dist 5` + Scan Context | same drift | 8.26 m | **1.90 m** | SC alone rescued both true loops (RAP GT error 0.15/0.34 m), `output_poss_sc5/` |
| **KITTI odometry 04** (HDL-64E, 271 frames full seq) | first KITTI velodyne smoke, `--real-apply-calib` | 2.96 m (RPE 0.021 m) | 3.26 m (no true loops on 04) | 31.4 s total; RAP verify error 0.02–0.31 m on all 12 candidates; caught & fixed the inverted KITTI calib conversion, `output_kitti04_smoke/` |

**Scan Context retrieval quality (POSS, `scripts/eval_loop_retrieval.py`):** 82 keyframes, true pairs = GT distance < 3 m & separation ≥ 200. True-pair SC distances 0.060 / 0.106 vs lowest false pair 0.347 (>3× margin) → **precision = recall = 1.0 for any threshold in [0.13, 0.30]** (pipeline default `--sc-dist-thresh 0.25`). Proximity retrieval at the default 15 m radius scores precision 0.50 (2 false positives), and recall collapses to 0 at radius ≤ 10 m because loop-closure drift is 13.3 m. Cost: 0.2 s to build 82 descriptors, 0.6 s for 654 pairwise matches — negligible vs RAP verification. SC also yields a per-pair yaw hint (column shift × 6°) that is currently only logged, not yet consumed.

**N-way joint registration backend (POSS, `scripts/eval_nway_backend.py`, products in `output_nway/`):** `RAPBackend.register_multi(scans, max_points_per_scan=...)` registers N keyframes in ONE RAP call → cycle-consistent per-part poses. Three batches compared against odometry APE 8.257 m and pairwise-PGO APE 1.821 m:

| Batch | Parts | Oracle SE(3) layout fit to GT | Loop relatives vs GT | N-way constraints + PGO | Direct anchor (no PGO) |
|---|---|---|---|---|---|
| B1 loop keyframes | 5 × 4000 pts | **0.145 m rmse** | 0.17–0.53 m | **1.736 m (best)** | 8.37 m |
| B2 + temporal neighbors | 7 × 4000 pts | 0.153 m | 0.12–0.50 m | 1.781 m | 8.65 m |
| B3 ALL keyframes | 82 × 1500 pts (123k pts, 38.6 s infer) | **55.0 m rmse (global warp)** | 0.21–0.49 m (local stays good) | 2.313 m | 98.2 m |

Conclusions: (1) small loop-batch N-way registration is near-perfect (batch keyframe poses themselves median 0.35 m from GT); (2) cycle-consistent N-way constraints beat independent pairwise constraints in PGO (−4.7% APE); (3) one-shot joint registration of all 82 keyframes warps the global layout — local geometry stays accurate, so PGO remains necessary for global consistency; (4) direct pose substitution fails for sparse batches (trajectory interior keeps drifting) and for warped dense batches. Sweet spot: **N-way as a batch-consistent loop-constraint factory feeding PGO**, not a PGO replacement. Next iteration: hierarchical N-way (joint registration within loop clusters, PGO stitching across clusters) + multi-seed variance (RAP sampling is stochastic, ±0.05 m run-to-run).

**Extra deps installed into the same WSL2 conda env `rap-inference`:** `kiss-icp==1.3.0`, `gtsam==4.2`, `evo==1.36.5` (all pip, verified working). Scan Context is pure NumPy — no new deps.

**Run commands (WSL2):**
```bash
source /root/miniconda3/bin/activate rap-inference && cd /mnt/e/githouse/RAP-SLAM
python scripts/run_pipeline.py --source real --output ./output_poss --loop-sep 200   # real POSS segment (loop-method=both by default)
python scripts/run_pipeline.py --output ./output                                     # simulated sequence
python scripts/eval_loop_retrieval.py                                                # retrieval P/R vs GT (reuses output_poss/odom_poses.txt)
python scripts/eval_nway_backend.py --batches B1,B2,B3 --load-loops output_nway/accepted_loops.json --reuse-cache   # N-way backend comparison
```

**Data inventory:** `RAP-SLAM/data/poss/dataset/` — POSS seq 00 poses (full 36924), calib, times, and frames 3850–5268 velodyne (1.4 GB, downloaded via `scripts/download_poss_segment.py`, resumable). `RAP-SLAM/data/kitti/dataset/` — KITTI odometry calib + poses for all 22 sequences, **no velodyne scans** (S3 too slow, see below). **`E:\githouse\Datasets\data_odometry_velodyne\dataset/`** (WSL: `/mnt/e/githouse/Datasets/...`) — KITTI odometry **velodyne scans for seq 01, 02, 03, 04 (complete, verified)** + poses 00–10 and calib/times for 01–04 copied in, so it is a self-contained `--real-root` (use `--real-apply-calib`). Owner will complete the remaining sequences (esp. seq 06) later; truncated 00/05 were deleted 2026-07-22.

### Hard-won gotchas (do not relearn these)

1. **POSS poses are already in the LiDAR/world frame** (z-up horizontal trajectory). Do NOT apply the KITTI conversion — it rotates the trajectory upright and corrupts evaluation. Controlled by `real_dataset.load_gt_poses(apply_calib=...)`: **False for POSS, True for KITTI**. **KITTI conversion direction fixed 2026-07-22:** the correct formula is `T_velo = Tr⁻¹ @ T_cam @ Tr`; the code previously used `Tr @ T @ Tr⁻¹`, which leaves the GT in a ~90°-rotated world frame (KITTI 04 "odometry APE" was 310.7 m before the fix, 2.96 m after). This bug was latent because the KITTI path had never run without velodyne data.
2. **Loop-closure acceptance must not gate on odometry consistency.** Requiring RAP's transform to agree with the drifting odometry estimate is self-defeating (true loops under 13.3 m drift were rejected while RAP was 0.15–0.47 m from GT). Current logic: accept on RAP overlap ratio only (`min_overlap`), consistency is logged as diagnostics.
3. **Network (China host):** AWS S3 (`avg-kitti`, etc.) is throttled to ~15 KB/s–0.5 MB/s; HuggingFace unreachable; `www.poss.pku.edu.cn` is fast (~4–5 MB/s). Download big files on the **Windows host** (`curl --ssl-no-revoke`, Git Bash), not in WSL. For partial extraction of huge remote zips use `remotezip` (vendored at `RAP-SLAM/scripts/_vendor`) — it is **not thread-safe**, use one instance per thread. KITTI seq 06 velodyne (~2.15 GB) via S3 remains un-downloaded.
4. **Git Bash path mangling:** passing `E:\githouse\...` as a CLI argument to `python` gets backslash-mangled; use forward slashes `E:/githouse/...`.
5. **WSL warning noise:** every `wsl` invocation prints a harmless `wsl: ... localhost ... NAT` warning line; filter with `grep -v '^wsl'` (use `grep -a`, output can look binary to grep) or ignore.
6. **Scan Context cosine distance is uninformative on structureless scenes** — uniform random clutter yields near-constant columns, so even unrelated scenes score ~0.1. Do not sanity-check SC on synthetic random clouds; judge separability on real scans (POSS: true 0.06–0.11 vs false ≥ 0.35). Rotation shows up as a column shift in the *opposite* direction (+60° yaw → shift 50 of 60 cols).
7. **RAP N-way registration scales non-gracefully in part count** — 5–7 parts: global layout near-perfect (0.15 m); 82 parts in one call: global warp (55 m layout rmse) while local relatives stay 0.2–0.5 m accurate. Global attention is O(total_points²) — 82 × 1500 pts = 123k points took 38.6 s for 5 Euler steps on the RTX 5070; do not attempt ~4000 pts × 82 (OOM/slow). Also: RAP sampling is stochastic even with a fixed seed (RNG is consumed across calls), so single-run APE numbers carry ±0.05 m noise.
8. **Comparing trajectories across frames:** POSS GT poses live in a world frame hundreds of meters from the odometry origin (KISS starts at identity). Always compare in the first-pose frame (`evaluate.align_to_first_pose`) — raw world-frame position diffs between anchored estimates and GT are meaningless.
9. **Interrupted zip extraction leaves `NNNNNN(1).bin` duplicate files** (Windows "file already exists" naming): seq 04 had `000001(1).bin` instead of `000001.bin`, which crashes `load_scans` (`int('000001(1)')`). After any extraction, sweep for `*( )*` files, verify content, and rename; then re-check frame-number contiguity per sequence.

### Roadmap (next tasks, in priority order)

3. ~~Scan Context global place recognition for loop candidates~~ ✅ (2026-07-20: `rap_slam/scan_context.py`, merged with proximity via `--loop-method both`; rescues loops under 13.3 m drift). Remaining: multi-dataset generalization (KITTI seq 06 velodyne still un-downloaded, MCD, Livox) and SC threshold validation off-POSS.
4. ~~RAP N-way joint global registration backend — first comparison~~ ✅ (2026-07-20: `register_multi` in `rap_backend.py` + `scripts/eval_nway_backend.py`; small-batch cycle-consistent constraints beat pairwise-PGO 1.74 vs 1.82 m; 82-part one-shot registration warps globally). Next iteration: **hierarchical N-way** (joint registration within loop clusters + PGO across clusters) and multi-seed variance evaluation.
5. Phase 2: ROS 2 (Jazzy on Ubuntu 24.04) node-ification + RViz. ⏳ STARTED 2026-07-21: Step 0 (Jazzy install in WSL2) + Step 1 (PointCloud2 player + RViz config) done — see "Phase 2 STARTED" section above.

---

## Technology Stack and Runtime Architecture

### Core dependencies
- **PyTorch** 2.5.1 (CUDA 12.4 wheel) — original upstream target, installed by `scripts/install.sh`
- **PyTorch** 2.7.0 (CUDA 12.8 wheel) — required for NVIDIA Blackwell (RTX 50-series, e.g., RTX 5070); used in the WSL2 deployment documented below
- **Lightning** 2.5.2 (`L.LightningModule`, `L.Trainer`, data modules)
- **Hydra** 1.3.2 — configuration composition
- **torchmetrics** 1.6.3, **pytorch3d** 0.7.8 — metrics and ICP/Chamfer utilities
- **FlashAttention** 2.7.4 — attention kernels in the DiT model (original upstream). **Already replaced** in this repo with PyTorch native `scaled_dot_product_attention` — see the WSL2 deployment notes below; `flash_attn` is **not imported anywhere** in the current code.
- **torch-scatter/sparse/cluster/spline-conv** — geometric utilities (PointTransformer V3 support)
- **diffusers** 0.33.0 — transformer building blocks (`FeedForward`)
- **open3d**, **trimesh**, **h5py**, **laspy** — point-cloud I/O
- **wandb** 0.20.1 — experiment logging
- **gradio** ≥6.0.0 — demo UI
- **mitsuba** 3.6.4, **matplotlib**, **rich** — visualization / tables
- **muon** (installed from `git+https://github.com/KellerJordan/Muon`) — optimizer

### Project layout
```text
RAP/
├── app.py                              # Gradio demo entry point (port 7860)
├── demo.py                             # Preprocess + run inference on a PLY folder
├── sample.py                           # Main inference script (Hydra CLI)
├── test_smoke.py                       # Smoke test: PointCloudDiT forward pass on random data
├── build_p3d.sh                        # Helper: build pytorch3d from source (WSL2/Blackwell env)
├── requirements_other.txt              # Pip requirements for non-torch packages
├── config/                             # Hydra YAML configs
│   ├── RAP_inference.yaml              # Default inference config (the only root config)
│   ├── data/data_tmp.yaml              # Data module defaults
│   ├── model/rap_{8,10,12,16}.yaml     # Model size configs (number of DiT layers)
│   ├── model/flow_model/               # PointCloudDiT architecture configs
│   ├── model/optimizer/                # muon / adamw optimizer configs
│   ├── model/lr_scheduler/             # muon / adamw LR scheduler configs
│   ├── trainer/                        # Lightning trainer configs (main/infer)
│   ├── loggers/wandb.yaml              # W&B logger config
│   └── visualizer/flow.yaml            # FlowVisualizationCallback config
├── dataset_process/                    # Training-sample generation & preprocessing
│   ├── extract_sample_features.py      # miniSpinNet feature extraction
│   ├── visualize_registered_pointclouds.py
│   ├── visualize_sample_features.py
│   └── utils/                          # I/O, splits, sampling, spinnet, etc.
├── rectified_point_flow/               # Core library
│   ├── modeling.py                     # RectifiedPointFlow LightningModule
│   ├── sampler.py                      # Flow integration (Euler / RK2 / RK4)
│   ├── procrustes.py                   # Rigid transform fitting / rigidity forcing
│   ├── visualizer.py                   # FlowVisualizationCallback
│   ├── data/                           # PointCloudDataset, PointCloudDataModule
│   ├── eval/                           # Evaluator and metrics
│   ├── flow_model/                     # PointCloudDiT + layers/norm/embedding
│   └── utils/                          # Checkpoints, logging, optimizers, training helpers, point-cloud helpers
├── scripts/                            # Setup and example run scripts
│   ├── install.sh
│   ├── download_weights_and_demo_data.sh
│   └── test_script_example.sh
├── weights/                            # Pre-trained checkpoints (gitignored)
│   ├── rap_model_10.ckpt               # rap_10 weights (~327 MB)
│   ├── rap_model_12.ckpt               # rap_12 weights (~356 MB)
│   └── mini_spinnet_t.pth              # miniSpinNet feature extractor weights
├── demo_example_data/                  # 27 demo datasets (gitignored; downloaded by script)
└── demo_output/                        # Local inference outputs (logs/, results/, visualizations/)
```

Stray non-source artifacts in the repo root (leftovers from the WSL2 deployment, safe to ignore): `cuda-keyring_1.1-1_all.deb`, `wget-log`, `__pycache__/`.

### Model architecture
The registration pipeline is implemented in `rectified_point_flow.modeling.RectifiedPointFlow`:
1. **Input**: multiple unposed point-cloud parts, optionally with 32-D local features extracted by miniSpinNet.
2. **Rectified flow**: `PointCloudDiT` predicts a velocity field that maps Gaussian noise `x_1` toward the registered point cloud `x_0`.
3. **Sampling**: Euler integration (default, `inference_sampler: "euler"`; RK2/RK4 also available in `sampler.py`) produces the registered point cloud.
4. **Rigidity forcing** (optional, on by default in `RAP_inference.yaml`): Procrustes-based rigidification during sampling.
5. **Pose recovery**: per-part rigid transformations are fitted with SVD/Procrustes in `procrustes.py` (`solve_procrustes`, `fit_transformations`, `rigidify_prediction_with_procrustes`).

`PointCloudDiT` is a Diffusion Transformer (DiT) with part-wise attention and global attention (both routed through the PyTorch-native `_flash_attn_varlen` SDPA helper in `flow_model/layer.py`), timestep/scale embeddings, and anchor-part embeddings. Default architecture (`point_cloud_dit_12.yaml`): `embed_dim=512`, `num_heads=8`, `local_feat_dim=32`.

Four model sizes are pre-defined (the number is the DiT layer count):
- `rap_8` — 8 DiT layers
- `rap_10` — 10 DiT layers
- `rap_12` — 12 DiT layers (default inference)
- `rap_16` — 16 DiT layers

---

## Build and Run Commands

### Environment setup (upstream / Linux, CUDA 12.4)
```bash
conda create -n py310-rap python=3.10 -y
conda activate py310-rap
bash ./scripts/install.sh          # installs torch 2.5.1+cu124, geometric libs, pytorch3d, flash-attn, etc.
bash ./scripts/download_weights_and_demo_data.sh
```

`scripts/install.sh` pins specific wheels for CUDA 12.4, PyTorch 2.5.1, FlashAttention 2.7.4.post1, pytorch3d 0.7.8, trimesh 4.6.4, lightning 2.5.2, torchmetrics 1.6.3, diffusers 0.33.0. It also installs the Muon optimizer from GitHub and finally `pip install --ignore-installed -r requirements_other.txt`.

`scripts/download_weights_and_demo_data.sh` downloads `weights.zip` and `demo_example_data.zip` from `https://www.ipb.uni-bonn.de/html/projects/rap/` and unzips them into the repo root.

### Run the Gradio demo
```bash
python app.py
```
Defaults: port `7860` (`--server_port`), checkpoint `./weights/rap_model_12.ckpt` (`--flow_model_checkpoint`), config `RAP_inference`. Launches with `server_name="0.0.0.0"`; the `SHARE_URL` environment variable controls whether a temporary Gradio share link is created (`permanent` disables sharing). Accepts PLY/OBJ/PTS/E57 point clouds and meshes.

### Run batch inference
```bash
python sample.py --config-name "RAP_inference" \
  model=rap_12 \
  data.dataset_names=[threedmatch,kitti] \
  data.data_root=./demo_new/data \
  ckpt_path=./weights/rap_model.ckpt \
  data.max_parts=12 \
  data.min_parts=2
```

An example shell command is in `scripts/test_script_example.sh`. Remember: `--config-name` is **required** (see the gotcha in Project Overview).

### Run inference on a folder of PLY files
```bash
python demo.py --input ./your_data --output ./output \
  --flow_model_checkpoint ./weights/rap_model_12.ckpt \
  --config RAP_inference --model rap_12
```

`demo.py` voxel-downsamples (default `--voxel_size 0.25`), extracts miniSpinNet features (`--feature_extraction_checkpoint ./weights/mini_spinnet_t.pth`, default `--des_r 5.0`), removes outliers (default on, `--no_remove_outliers` to disable), allocates per-part points via `--allocation_method voxel_adaptive`, and runs `sample.py`-style inference through Hydra. Useful flags: `--point_cloud_count/-k`, `--adaptive_parameters/-a`, `--no_rigidity_forcing`, `--apply_coordinate_transform`.

### Feature extraction (training-sample preprocessing)
```bash
python ./dataset_process/extract_sample_features.py \
  --input ./dataset/raw \
  --output ./dataset/processed \
  --des_r 0.5 --voxel_size 0.1 -r 0.5
```

This uses miniSpinNet (`dataset_process/utils/spinnet`) to compute per-point 32-D descriptors and saves sampled PLY + `.npy` feature files (optionally HDF5 via `--save_hdf5`, on by default).

---

## Deployment on Windows + WSL2 + NVIDIA Blackwell (RTX 50-series)

This section documents a validated deployment path for running RAP on a Windows 11 PC with an NVIDIA RTX 5070 (Blackwell architecture, SM 12.0) inside an isolated WSL2 + Conda environment. The upstream `scripts/install.sh` targets PyTorch 2.5.1 + CUDA 12.4, which does **not** support Blackwell. The following steps are required. **All patches described here are already applied in this repository** — do not re-apply them.

### Host prerequisites
- Windows 11 with WSL2 enabled (`wsl --install -d Ubuntu-24.04`)
- NVIDIA GPU driver installed on Windows (WSL inherits it via CUDA-Forward)
- `.wslconfig` with `vmIdleTimeout=-1` to prevent WSL suspension during long builds

### Step 1 — WSL2 environment
```bash
# Inside WSL2 Ubuntu 24.04 (running as root)
apt update && apt install -y build-essential git wget curl unzip

# Install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /root/miniconda3
source /root/miniconda3/bin/activate

# Create environment
conda create -n rap-inference python=3.10 -y
conda activate rap-inference
```

### Step 2 — PyTorch 2.7.0 + CUDA 12.8 (Blackwell)
```bash
pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 \
  --index-url https://download.pytorch.org/whl/cu128
```
Verify GPU:
```python
import torch
print(torch.cuda.get_device_name(0))  # NVIDIA GeForce RTX 5070
print(torch.cuda.is_available())      # True
```

### Step 3 — torch-geometric + PyG libs
```bash
pip install torch-geometric
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv \
  -f https://data.pyg.org/whl/torch-2.7.0+cu128.html
```

### Step 4 — FlashAttention workaround (mandatory for Blackwell; ALREADY APPLIED)
FlashAttention 2.7.4/2.8.3 has **no pre-built wheel** for PyTorch 2.7 + CUDA 12.8 + Blackwell, and source compilation fails due to GitHub release-download timeouts.

**Patch already applied:** `rectified_point_flow/flow_model/layer.py`
- Removed `import flash_attn`
- Added `_flash_attn_varlen()` helper using `torch.nn.functional.scaled_dot_product_attention`
- Replaced both `flash_attn.flash_attn_varlen_qkvpacked_func` calls (in `_part_attention()` and `_global_attention()`) with the native helper
- PyTorch 2.7 automatically routes SDPA through its built-in Flash Attention kernel on CUDA 12.8, so performance is preserved.

### Step 5 — pytorch3d (build from source)
No pre-built wheel exists for PT 2.7 + CU12.8. The repo-root helper script `build_p3d.sh` automates exactly this (activate env, set arch flags, clone, build):
```bash
export TORCH_CUDA_ARCH_LIST=12.0
export CUDA_HOME=/usr/local/cuda-12.8
export FORCE_CUDA=1
export MAX_JOBS=2

git clone --depth 1 https://github.com/facebookresearch/pytorch3d.git /tmp/pytorch3d-build
cd /tmp/pytorch3d-build
pip install -v --no-build-isolation .
```
Result: `pytorch3d-0.7.9` installed successfully.

### Step 6 — Remaining Python dependencies
```bash
pip install diffusers==0.33.0 lightning==2.5.2 torchmetrics==1.6.3 \
  trimesh==4.6.4 ninja
pip install -r requirements_other.txt
```

### Step 7 — Lazy-import patches (optional but recommended; ALREADY APPLIED)
To keep the codebase robust when pytorch3d is temporarily unavailable, the following files were patched for **lazy imports**:

| File | Patch |
|------|-------|
| `rectified_point_flow/utils/render.py` | Added `_ensure_pytorch3d()` guard; imports `pytorch3d.structures` / `pytorch3d.renderer` only inside `visualize_point_clouds_pytorch3d()` |
| `rectified_point_flow/eval/metrics.py` | Wrapped `chamfer_distance` and `iterative_closest_point` in `_chamfer_distance()` / `_iterative_closest_point()` helpers that import on first call |

These are backward-compatible — if pytorch3d is present, behavior is identical.

### Step 8 — Model weights
Weights are hosted at:
- Primary: `https://www.ipb.uni-bonn.de/html/projects/rap/weights.zip` (~640 MB)
- Mirror: HuggingFace `YuePanEdward/RAP` — **unreachable from some WSL2 networks**

If the WSL2 download is slow/unstable, download on Windows and copy into WSL:
```powershell
# Windows PowerShell
wget https://www.ipb.uni-bonn.de/html/projects/rap/weights.zip -O $env:USERPROFILE\Desktop\weights.zip
wsl -d Ubuntu-24.04 -u root cp /mnt/c/Users/$env:USERNAME/Desktop/weights.zip /mnt/e/githouse/RAP-main/
```

Then extract:
```bash
cd /mnt/e/githouse/RAP-main
unzip weights.zip   # creates ./weights/rap_model_10.ckpt, rap_model_12.ckpt, mini_spinnet_t.pth
```

### Step 9 — Smoke test
`test_smoke.py` in the repo root is the canonical smoke test (instantiates a 2-layer `PointCloudDiT`, runs a forward pass on 1000 random points, and exercises the `_flash_attn_varlen` SDPA replacement):
```bash
python test_smoke.py
```

### Step 10 — Run inference
```bash
python sample.py --config-name RAP_inference \
  model=rap_12 \
  data.force_use_ply=true \
  data.data_root=./demo_example_data \
  ckpt_path=./weights/rap_model_12.ckpt \
  visualizer.renderer=none
```

### Performance notes on RTX 5070
- PyTorch 2.7 + CUDA 12.8 routes `scaled_dot_product_attention` through the native Flash Attention kernel automatically on SM 12.0 (Blackwell).
- Micro-benchmark (8 heads, 64 dim, 100 pts): **~0.015 ms** per SDPA call on GPU.
- Full `rap_12` inference latency is diffusion-step-bound; use `model.inference_sampling_steps=5` or `1` for faster results.
- VRAM usage: ~2–4 GB for typical `max_points_per_batch=40000` workloads on 12 GB RTX 5070.

### Patch Details (exact code)

These are the three patches applied to run RAP on PyTorch 2.7 + CUDA 12.8 without FlashAttention and with optional pytorch3d. **They are already present in this repo** — this subsection documents them for reference and for porting to a fresh upstream clone.

#### 1. `rectified_point_flow/flow_model/layer.py` — SDPA replacement

**Before:**
```python
import torch
import torch.nn as nn
from diffusers.models.attention import FeedForward
from flash_attn import flash_attn_varlen_qkvpacked_func

from .norm import AdaptiveLayerNorm, MultiHeadRMSNorm
```

**After:**
```python
import torch
import torch.nn as nn
from diffusers.models.attention import FeedForward

from .norm import AdaptiveLayerNorm, MultiHeadRMSNorm


def _flash_attn_varlen(qkv: torch.Tensor, cu_seqlens: torch.Tensor, max_seqlen: int, softcap: float = 0) -> torch.Tensor:
    """PyTorch-native variable-length attention (replaces flash_attn).

    Args:
        qkv: (total_seq_len, 3, num_heads, head_dim)
        cu_seqlens: (num_seqs + 1,)
        max_seqlen: unused (kept for API compatibility)
        softcap: unused (kept for API compatibility)

    Returns:
        out: (total_seq_len, num_heads, head_dim)
    """
    outputs = []
    for i in range(len(cu_seqlens) - 1):
        start, end = int(cu_seqlens[i]), int(cu_seqlens[i + 1])
        if start == end:
            continue
        seq_qkv = qkv[start:end]                    # (seq_len, 3, num_heads, head_dim)
        q, k, v = seq_qkv.unbind(dim=1)             # each: (seq_len, num_heads, head_dim)

        # scaled_dot_product_attention expects (batch, num_heads, seq_len, head_dim)
        q = q.transpose(0, 1).unsqueeze(0)
        k = k.transpose(0, 1).unsqueeze(0)
        v = v.transpose(0, 1).unsqueeze(0)

        out = torch.nn.functional.scaled_dot_product_attention(q, k, v)
        out = out.squeeze(0).transpose(0, 1)        # (seq_len, num_heads, head_dim)
        outputs.append(out)

    return torch.cat(outputs, dim=0) if outputs else qkv.new_empty(0, qkv.size(2), qkv.size(3))
```

Both `_part_attention()` and `_global_attention()` call `_flash_attn_varlen(...)` instead of `flash_attn_varlen_qkvpacked_func(...)`.

**Rationale:** PyTorch 2.7 on CUDA 12.8 automatically routes `scaled_dot_product_attention` through its built-in Flash Attention kernel (cuDNN/Flash) on Blackwell. The loop-over-sequences approach is correct because each part in the batch is an independent sequence; `cu_seqlens` already marks the boundaries. The overhead is negligible for the sequence lengths typical in point-cloud registration (< 1000 points per part).

#### 2. `rectified_point_flow/utils/render.py` — lazy pytorch3d import

**Before:**
```python
import torch
import numpy as np
from PIL import Image
from pytorch3d.structures import Pointclouds
from pytorch3d.renderer import (
    look_at_view_transform,
    FoVPerspectiveCameras,
    PointsRasterizationSettings,
    PointsRasterizer,
    PointsRenderer,
    AlphaCompositor,
)
```

**After:**
```python
import torch
import numpy as np
from PIL import Image

_pytorch3d_available = None

def _ensure_pytorch3d():
    global _pytorch3d_available
    if _pytorch3d_available is not None:
        return _pytorch3d_available
    try:
        from pytorch3d.structures import Pointclouds
        from pytorch3d.renderer import (
            look_at_view_transform,
            FoVPerspectiveCameras,
            PointsRasterizationSettings,
            PointsRasterizer,
            PointsRenderer,
            AlphaCompositor,
        )
        _pytorch3d_available = True
    except ImportError:
        _pytorch3d_available = False
    return _pytorch3d_available
```

Inside `visualize_point_clouds_pytorch3d()`:
```python
if not _ensure_pytorch3d():
    raise ImportError("pytorch3d is not installed. Install it or use renderer='none'.")
from pytorch3d.structures import Pointclouds
from pytorch3d.renderer import (
    look_at_view_transform,
    FoVPerspectiveCameras,
    PointsRasterizationSettings,
    PointsRasterizer,
    PointsRenderer,
    AlphaCompositor,
)
```

**Rationale:** Makes the renderer robust when pytorch3d is not yet built or is temporarily unavailable. The rest of the codebase (modeling, sampler, procrustes) does not import pytorch3d, so inference can run with `visualizer.renderer=none` while pytorch3d is being compiled.

#### 3. `rectified_point_flow/eval/metrics.py` — lazy pytorch3d ops

**Before:**
```python
from pytorch3d.loss.chamfer import chamfer_distance
from pytorch3d.ops import iterative_closest_point
```

**After:**
```python
def _chamfer_distance(*args, **kwargs):
    from pytorch3d.loss.chamfer import chamfer_distance as _cd
    return _cd(*args, **kwargs)


def _iterative_closest_point(*args, **kwargs):
    from pytorch3d.ops import iterative_closest_point as _icp
    return _icp(*args, **kwargs)
```

All call sites in the same file (`compute_cd`, `compute_part_acc`, `align_anchor`, `compute_transform_errors`) use `_chamfer_distance(...)` and `_iterative_closest_point(...)` instead of the direct imports.

**Rationale:** Same as render.py — allows the evaluator to be imported and used for metrics that do not require pytorch3d (e.g., rotation/translation errors, overlap ratio) while pytorch3d is still building. Once pytorch3d is installed, behavior is identical.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `RuntimeError: FlashAttention only supports Ampere, Hopper or Ada` | FlashAttention 2.7.4 has no Blackwell support | The `layer.py` SDPA patch is already applied in this repo; ensure you did not reintroduce `import flash_attn`. |
| `torch.load(..., weights_only=False)` warning | PyTorch 2.7 default change | Ignored for now; checkpoints are from trusted source (PRBonn). |
| Corrupted `weights.zip` (bad CRC / `unzip` error) | Partial download resumed with `--continue` creates a malformed zip | Delete the file and re-download **without** `--continue`: `wget -O weights.zip <url>` |
| HuggingFace unreachable from WSL2 | Network routing / GFW | Download on Windows host and `wsl cp` into WSL, or use the Bonn mirror. |
| `git clone --filter=blob:none` fails for pytorch3d | Git protocol not supported by WSL2 network | Use `git clone --depth 1 https://github.com/facebookresearch/pytorch3d.git` instead (this is what `build_p3d.sh` does). |
| pytorch3d build killed / OOM | WSL2 default memory limit | Add `.wslconfig` on Windows host: `[wsl2] memory=16GB processors=8`, then `wsl --shutdown`. |
| pytorch3d build fails with `nvcc` SM 12.0 error | Missing `TORCH_CUDA_ARCH_LIST` | Export `TORCH_CUDA_ARCH_LIST=12.0` before building. |
| `sample.py` fails with `ImportError: cannot import name 'chamfer_distance'` | pytorch3d not installed or import failed | Use `visualizer.renderer=none` to skip rendering while building pytorch3d. |
| `cudaErrorNoKernelImageForDevice` at runtime | Binary compiled for wrong CUDA arch | Rebuild pytorch3d with `TORCH_CUDA_ARCH_LIST=12.0` and `FORCE_CUDA=1`. |
| WSL2 suspends during long build | Default idle timeout | Set `vmIdleTimeout=-1` in `.wslconfig`. |
| Hydra error: `Could not find config 'RAP_base'` | `sample.py`'s default `config_name` refers to a config that does not ship | Always pass `--config-name RAP_inference`. |

### Verified Results (RTX 5070, WSL2, rap_12)

| Test | Configuration | Result |
|------|-------------|--------|
| Smoke test | `test_smoke.py` (2-layer `PointCloudDiT`, 1000 random pts) | Pass — `torch.cuda` OK, output shape correct |
| `demo.py` — `object_stanford_bunny` | 2 parts, 174 pts, 5 Euler steps, `rap_12` | **Pass** — Total 2.4 s, inference 1.69 s, output PLY + transforms saved |
| `sample.py` — `object_stanford_bunny` | `visualizer.renderer=none` | **Pass** — Rich metrics table printed, results under `demo_output/logs/results/` |
| VRAM peak | `rap_12`, 5 steps, 174 pts | ~2.1 GB |
| SDPA micro-benchmark | 8 heads, 64 dim, 100 pts | ~0.015 ms/call |

Files produced by a successful inference run (actual on-disk layout, verified under `demo_output/logs/`):
```text
demo_output/logs/
├── results/
│   └── object_stanford_bunny/
│       └── demo_sample/
│           ├── registered/
│           │   ├── source_generation00_registered.ply   # registered part PLYs
│           │   └── target_generation00_registered.ply
│           ├── generation/
│           │   ├── input.pcd                            # merged input point cloud
│           │   ├── endpoint/step_{0..N}.pcd             # merged cloud at each Euler step (endpoints)
│           │   └── midpoint/step_{0..N}.pcd             # merged cloud at each Euler step (midpoints)
│           ├── object_stanford_bunny_sample00000_generation00_source_transform.txt  # 4x4 transform
│           └── object_stanford_bunny_sample00000_generation00_target_transform.txt
└── visualizations/                                      # rendered images (empty when renderer=none)
```

### Full Command Reference (WSL2 + RTX 5070)

```bash
# 1. Enter WSL2
wsl -d Ubuntu-24.04

# 2. Activate environment
conda activate rap-inference

# 3. Verify GPU
python -c "import torch; print(torch.cuda.get_device_name(0))"
# Expected: NVIDIA GeForce RTX 5070

# 4. Quick smoke test (no weights needed)
cd /mnt/e/githouse/RAP-main
python test_smoke.py

# 5. Run inference on demo data (no rendering, fastest)
python sample.py --config-name RAP_inference \
  model=rap_12 \
  model.inference_sampling_steps=5 \
  data.force_use_ply=true \
  data.data_root=./demo_example_data \
  ckpt_path=./weights/rap_model_12.ckpt \
  visualizer.renderer=none

# 6. Run inference with demo.py (includes preprocessing)
python demo.py --input ./demo_example_data/object_stanford_bunny \
  --output ./demo_output \
  --flow_model_checkpoint ./weights/rap_model_12.ckpt \
  --config RAP_inference --model rap_12

# 7. Faster inference (1 step, smaller model)
python sample.py --config-name RAP_inference \
  model=rap_10 \
  model.inference_sampling_steps=1 \
  data.force_use_ply=true \
  data.data_root=./demo_example_data \
  ckpt_path=./weights/rap_model_10.ckpt \
  visualizer.renderer=none
```

---

## Configuration System

- **Hydra** is used for the runnable entry points `sample.py` (and is also used by `demo.py` / `app.py` internally to compose the model).
- Config root: `./config`. The **only** root config that ships is `config/RAP_inference.yaml`.
- `RAP_inference.yaml` composes `model: rap_12`, `data: data_tmp`, `trainer: infer`, `loggers: wandb`, `visualizer: flow`, sets `seed: 42`, and pins the data budget: `batch_size: 1`, `num_workers: 1`, `min_parts: 2`, `max_parts: 512`, `min_points_per_part: 200`, `max_points_per_part: 40000`, `max_points_per_batch: 400000`.
- Model inference defaults in `RAP_inference.yaml`: `inference_sampling_steps: 10` (the `rap_*.yaml` model configs default to 50), `n_generations: 1`, `rigidity_forcing: true`, `return_end_point_trajectory: true`, `save_results: true`, `save_merged_pointcloud_steps: true`.
- The infer trainer (`config/trainer/infer.yaml`) runs single-device with `precision: "16-mixed"`. The main trainer (`config/trainer/main.yaml`) uses `strategy: ddp` for multi-GPU training.
- Important config groups and override examples:
  - Model size: `model=rap_8`, `model=rap_10`, `model=rap_12`, `model=rap_16`
  - Sampling steps: `model.inference_sampling_steps=10`
  - Number of generations: `model.n_generations=3`
  - Rigidity forcing: `model.rigidity_forcing=true`
  - Data root: `data.data_root=./your_data` (interpolated from the top-level `data_root` key)
  - Disable visualization: `visualizer.renderer=none` (choices: `mitsuba`, `pytorch3d`, `none`)
  - Limit visualized samples: `visualizer.max_samples_per_batch=5`
  - Checkpoint: `ckpt_path=./weights/rap_model.ckpt` (or `null` to auto-download from Hugging Face into `./weights`)

Configuration values are referenced with `${...}` interpolation (e.g., `${data_root}`, `${log_dir}`).

### Key data settings
- `data.force_use_ply=true` — skip HDF5 detection and load `.ply` files directly (already the default in `config/data/data_tmp.yaml`).
- `data.use_random_split=true` — prefer `*_random.txt` split files (default `false` = sequence-based split).
- `data.max_points_per_batch` — dynamic batching budget.
- `data.max_parts`, `data.min_parts` — filter samples by number of parts.

---

## Code Organization and Module Divisions

### `rectified_point_flow/`

| File/Dir | Responsibility |
|----------|----------------|
| `modeling.py` (~800 lines) | `RectifiedPointFlow` LightningModule: forward/loss/sampling loops (`training_step`, `validation_step`, `test_step`, `sample_rectified_flow`), multi-generation selection, rigidity selection. |
| `sampler.py` | Flow integration: `flow_sampler`, `euler_step`, `rk2_step`, `rk4_step`, `get_sampler`. |
| `procrustes.py` | Per-part SVD pose fitting (`solve_procrustes`, `fit_transformations`) and rigidity forcing (`rigidify_prediction_with_procrustes`). |
| `visualizer.py` (~1300 lines) | `FlowVisualizationCallback` for rendered point-cloud images and trajectory GIFs. |
| `data/datamodule.py` | `PointCloudDataModule`, dynamic batching (`DynamicBatchSampler`), variable collate, multi-dataset concatenation. |
| `data/dataset.py` | `PointCloudDataset`: loads HDF5 or PLY folders, applies augmentation, splits, padding. |
| `data/transform.py` | Point sampling, centering, rotation, padding helpers. |
| `eval/evaluator.py` | `Evaluator`: computes metrics and saves result point clouds/JSON. |
| `eval/metrics.py` | Chamfer distance, rotation/translation errors, rigidity RMSE, recalls, part accuracy. **Patched:** lazy pytorch3d ops (`_chamfer_distance`, `_iterative_closest_point`). |
| `flow_model/point_cloud_dit.py` | `PointCloudDiT` transformer model. |
| `flow_model/layer.py` | `DiTLayer`: part-wise + global attention layers. **Patched:** uses PyTorch native `_flash_attn_varlen` (SDPA) instead of `flash_attn`. |
| `flow_model/embedding.py` | `PointCloudEncodingManager` (position, scale, local features, timestep). |
| `flow_model/norm.py` | `AdaptiveLayerNorm`, `MultiHeadRMSNorm`. |
| `utils/checkpoint.py` | Checkpoint loading with prefix editing and HuggingFace download (`load_checkpoint_for_module`, `download_rap_checkpoint`). |
| `utils/logging.py` | `MetricsMeter`, Rich evaluation tables (`print_eval_table`), per-step/epoch logging. |
| `utils/optimizers.py` | Muon + AdamW builder (`build_muon_with_aux_adam`). |
| `utils/training.py` | Training helpers: W&B logger setup and run-resume (`setup_loggers`, `setup_wandb_resume`, `find_wandb_run_id`). |
| `utils/point_clouds.py` | `split_parts`, `ppp_to_ids`, `flatten_valid_parts`, etc. |
| `utils/render.py` | Mitsuba / PyTorch3D rendering helpers. **Patched:** lazy pytorch3d import (`_ensure_pytorch3d`). |

### `dataset_process/`

| File/Dir | Responsibility |
|----------|----------------|
| `extract_sample_features.py` | `FeatureExtractor` (miniSpinNet) and `SampleProcessor`; CLI for batch feature extraction. |
| `visualize_registered_pointclouds.py` | Open3D visualization of registration results. |
| `visualize_sample_features.py` | Feature visualization utilities. |
| `utils/io_utils.py` | Loading/saving PLY/HDF5, color maps (`CMAP_DEFAULT`), metadata, `save_processed_sample`. |
| `utils/dataset_utils.py` | Dataset helpers used by `demo.py` (loading PLY folders). |
| `utils/point_sampling_utils.py` | FPS allocation, voxel-adaptive sampling (`calculate_voxel_coverage`, `allocate_fps_points`, `calculate_adaptive_sample_count_per_part`). |
| `utils/split_utils.py` | Train/val split creation (random and sequence-based). |
| `utils/submap_utils.py` | Submap generation from sequences. |
| `utils/processing_utils.py` | Dataset-specific processing and `set_random_seeds`. |
| `utils/feature_extraction_metadata_utils.py` | Metadata sidecar files for extracted features. |
| `utils/validation_utils.py` | Input validation helpers. |
| `utils/preview_utils.py` | Preview/summary helpers. |
| `utils/spinnet/` | miniSpinNet implementation (`patch_embedder.py`, `patchnet.py`) and SE3/common helpers. |

---

## Data Format Conventions

The data module supports two input formats:

1. **HDF5 file** (`.hdf5`) with groups:
   - `data_split/<dataset_name>/<split>` — list of sample names.
   - `num_points/<dataset_name>/<split>` — precomputed point counts (optional but recommended).
   - `<sample_name>/<part_name>/vertices` and optionally `features`.
2. **Folder of PLY files** (one folder per dataset, PLYs grouped per sample, one `.ply` per part — e.g. `demo_example_data/object_stanford_bunny/{source,target}.ply`). Features are loaded from `features_<part_name>.npy` if present.

For folder format, split files must live at `<dataset>/data_split/{train,val}.txt` or `{train_random,val_random}.txt`, and optional point-count files at `<dataset>/num_points/{train,val}.txt`. When `dataset_names` is empty (`[]`), all dataset folders found under `data_root` are used.

The model expects input tensors produced by `variable_collate_fn`:
- `pointclouds` / `pointclouds_gt`: `(TP, 3)` concatenated points
- `features`: `(TP, 32)` local features (optional)
- `points_per_part`: `(B, P)` padded counts
- `cu_seqlens`: `(B + 1,)` batch boundaries
- `scales`: `(B,)` normalization scale
- `anchor_indices`, `anchor_parts`: anchor annotations

`TP` = total points in the dynamic batch, `B` = batch size, `P` = max parts.

---

## Code Style Guidelines

- Python 3.10+ syntax is used; union types are written as `X | Y`.
- Type hints are encouraged but not exhaustive.
- Docstrings follow Google/Numpy style with argument shapes.
- Use `logger = logging.getLogger("ModuleName")` for logging.
- Prefer `pathlib.Path` for new path handling, but `os.path` is widely used.
- GPU timing helpers synchronize with `torch.cuda.synchronize()` when CUDA is available (see `get_time()` in `sample.py` / `demo.py`).
- Variables use abbreviations common in the paper: `x_0` (registered), `x_1` (noise), `x_t` (intermediate), `v_t` (velocity), `cond` (condition).
- Use `torch.inference_mode()` for sampling and `torch.autocast(..., dtype=torch.float32)` around SVD/Procrustes for stability.
- `sample.py` enables TF32 (`torch.backends.cuda.matmul.allow_tf32 = True`, `cudnn.benchmark = True`) at import time — keep this when adding entry points.
- When touching attention code, do **not** reintroduce a hard `import flash_attn` — the SDPA-based `_flash_attn_varlen` in `flow_model/layer.py` is what makes the code portable (Blackwell/ROCm/CPU fallback). Keep new heavy/optional dependencies lazily imported, following the `render.py` / `metrics.py` pattern.

---

## Testing Instructions

There is **no formal unit-test suite** in this repository. Validation is done by running inference and inspecting metrics. There are no CI/GitHub Actions files; local execution is the only test path.

Recommended workflow when making changes:
1. **Fast smoke test (no checkpoint needed):** `python test_smoke.py` — instantiates a small `PointCloudDiT`, runs a forward pass on random CUDA tensors, and checks the `_flash_attn_varlen` SDPA helper. Use this after any change to `flow_model/`.
2. **End-to-end smoke test:** `python sample.py --config-name RAP_inference model=rap_10 data.force_use_ply=true data.data_root=./demo_example_data ckpt_path=./weights/rap_model_10.ckpt visualizer.renderer=none` (adjust `model=`/`ckpt_path=` to the weights you have).
3. **Full example script:** `bash ./scripts/test_script_example.sh` (adjust paths/dataset names first).
4. Verify that metrics print in a Rich table and that outputs appear under `<log_dir>/results` and `<log_dir>/visualizations` (see the output tree in "Verified Results" above).
5. When modifying core modules (`modeling.py`, `sampler.py`, `procrustes.py`, `eval/`), check both single-generation and multi-generation (`n_generations>1`) paths.

---

## Security Considerations

- The install script downloads and executes pre-built wheels from PyTorch, pyg.org, Facebook (pytorch3d), and GitHub releases. Verify checksums/environment if running in a sensitive context.
- Weights and demo data are downloaded over HTTP(S) from `www.ipb.uni-bonn.de` and Hugging Face (`YuePanEdward/RAP`).
- `torch.load(..., weights_only=False)` is used for checkpoint loading; only load checkpoints from trusted sources.
- The Gradio demo (`app.py`) accepts arbitrary uploaded files and binds to `0.0.0.0` by default; it may also create a public share link unless `SHARE_URL=permanent` is set. If exposing publicly, run it with appropriate sandboxing and do not trust uploaded content.
- No secrets, API keys, or credentials are stored in the repository. W&B logging requires the user's own `wandb` login outside the repo.

---

## Common Tasks for Agents

### Add a new dataset
1. Create a folder under the data root: `<data_root>/<dataset_name>/`.
2. Add PLY files per sample, or convert to HDF5 with `dataset_process/utils/io_utils.py` helpers.
3. Create split files in `<dataset_name>/data_split/{train,val}.txt`.
4. Optionally compute `num_points/{train,val}.txt`.
5. Reference it in config: `data.dataset_names=[your_dataset_name]` (or leave `dataset_names: []` to pick up all folders under `data_root`).

### Change model size
Override the model config group: `model=rap_10`. Ensure a matching checkpoint exists (e.g., `weights/rap_model_10.ckpt`).

### Disable visualizations
Pass `visualizer.renderer=none` on the command line.

### Run faster inference
Reduce sampling steps: `model.inference_sampling_steps=5` or `1`, or use a smaller model (`rap_8`, `rap_10`).

### Add a new metric
Implement it in `rectified_point_flow/eval/metrics.py` and wire it into `Evaluator` in `eval/evaluator.py`.

---

## Notes and Caveats

- Training code is **not yet released** (see README TODO list). The current codebase is inference-focused, although the LightningModule contains training/validation scaffolding (`training_step`, optimizer/scheduler configs, `trainer/main.yaml`).
- `encoder_on` is currently `false` in all model configs; the `feature_extractor` branch is dormant and the model relies on pre-computed local features (or zero features).
- Multi-GPU training is configured via `strategy: ddp` in `config/trainer/main.yaml`; inference (`config/trainer/infer.yaml`) is single-device.
- The codebase is developed on Linux; native Windows support is not guaranteed (FlashAttention and pytorch3d wheels are Linux-specific in the install script). Use the WSL2 path documented above on Windows machines.
- `sample.py`'s Hydra default `config_name="RAP_base"` does not exist in this repo — always pass `--config-name RAP_inference` explicitly.
- `config/RAP_inference.yaml` writes outputs to `log_dir: ./demo_new/` by default and uses `data_root: ./demo_new/data`; override both on the CLI for real runs (e.g. `data.data_root=./demo_example_data`, and `log_dir` lives in the config).
- When modifying Hydra configs, keep `_target_` and `_partial_` keys intact; the model, datamodule, trainer, and callbacks are instantiated by `hydra.utils.instantiate()`.
- `demo_example_data/` contains 27 datasets spanning indoor scans, TLS, LiDAR, maps, medical, and object scans (e.g. `object_stanford_bunny` with `source.ply`/`target.ply`); it and `weights/` are gitignored and fetched by `scripts/download_weights_and_demo_data.sh`.
