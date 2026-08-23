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

**CORE GOAL (declared 2026-08-01): RAP-CORE SLAM.** The owner's goal is a **non-realtime SLAM system with RAP as the core, not as a plug-in verifier**. Every pipeline stage should either be performed by RAP or explicitly shaped around RAP's capabilities and outputs: retrieval feeds RAP the candidates it can verify, the acceptance gate trusts RAP's intrinsic geometry (overlap / mean_dist), the backend consumes RAP's per-edge diagnostics as information weighting, and RAP's native N-way joint registration produces cycle-consistent submap constraints. The design test for any change is: *does this use more of what RAP knows, or does it route around RAP?* See the "RAP-CORE roadmap" section below for the staged plan.

That work lives in a **sibling directory** `E:\githouse\RAP-SLAM` (WSL: `/mnt/e/githouse/RAP-SLAM`), kept separate from this repo. **Rule: `RAP-main` is read-only for that project** (imported via `sys.path`); all new code goes to `RAP-SLAM`. See `RAP-SLAM/README.md` for full details.

### Status: Phase 1 + real-sequence validation DONE; Scan Context loop retrieval DONE; N-way backend first comparison DONE (2026-07-20)

Pipeline: `preprocess → KISS-ICP odometry → keyframe selection → Scan Context global + proximity loop candidates → RAP 2-way verification (or N-way joint batch registration) → GTSAM PGO → evo APE/RPE + merged map`. Entry point: `RAP-SLAM/scripts/run_pipeline.py`. All six stages verified end-to-end three times.

### Phase 2 STARTED (2026-07-21): ROS 2 Jazzy + RViz — Step 0+1+2+3 DONE

- **Both repos now on GitHub** (private, owner account): `YCDJ/RAP` (upstream snapshot + Blackwell patches) and `YCDJ/RAP-SLAM` (original pipeline). Local dirs are git repos; `data/` and `output*/` are gitignored.
- **Step 0**: `RAP-SLAM/scripts/install_ros2_jazzy.sh` — idempotent Jazzy installer for WSL2 Ubuntu 24.04; auto-probes apt mirrors (TUNA → Aliyun → official) + rosdistro key sources. Installed & verified in WSL2: ros-base, rviz2, ros2cli, demo nodes, sensor-msgs-py, colcon. Talker/listener DDS check passed. WSLg present (`DISPLAY=:0`).
- **Step 1**: `RAP-SLAM/ros2/` — `pointcloud_player.py` (standalone rclpy node, no colcon: POSS/KITTI `.bin` → `/points_raw` PointCloud2 with xyz+intensity; Reliable QoS to match RViz default), `rviz/rap_slam.rviz`, `run_step1.sh` (one-command player + RViz). Verified headless: 1419 POSS scans publish correctly; effective rate caps at ~10 Hz due to `.tolist()` conversion (= native LiDAR rate, fine). **Owner confirmed GUI working 2026-07-21 (after WSLg restart).**
- **Step 2** (2026-07-21): `ros2/odometry_node.py` — KISS-ICP wrapped as rclpy node reusing `rap_slam.odometry.KissOdometry` with the offline pipeline's exact params (**`max_range=80.0`**, min_range 1.5, voxel 0.8). Subscribes `/points_raw` → publishes `/odom` (nav_msgs/Odometry), `/odom_path` (nav_msgs/Path), TF `odom→base_link` + static `base_link→velodyne`. RViz config now fixed frame `odom` + Path display. `run_step2.sh` = player + odometry + RViz; `verify_step2_headless.sh` = no-GUI regression vs `output_poss/odom_poses.txt`. **Verified: full 1419-frame POSS segment, live trajectory numerically identical to offline (max diff 1e-6 m); KISS-ICP 18–45 ms/scan, real-time at native 10 Hz.** Deps: `kiss-icp==1.3.0` into **system python3** via `pip --break-system-packages --ignore-installed typing_extensions ... 'numpy<2'`. GUI run: `bash /mnt/e/githouse/RAP-SLAM/ros2/run_step2.sh`.
- Gotchas recorded in `RAP-SLAM/ros2/README.md`: never source ROS `setup.bash` under `set -u`; RViz PointCloud2 default Reliable QoS (player matches it deliberately); **WSLg can wedge so that NO GUI window shows at all (even `xeyes` exits silently) — fix is `wsl --shutdown` from PowerShell**; do not hand-write `Window Geometry`/`QMainWindow State` blobs into `.rviz` files (off-screen/zero-size windows); `RVIZ_SOFTWARE=1 bash run_step2.sh` (LIBGL_ALWAYS_SOFTWARE) is the fallback when OGRE windows stay invisible; start odometry node BEFORE the player (wait for "KISS-ICP odometry up" log) or the first scans are missed; WSL `/tmp` can be wiped between `wsl` invocations — keep state in the repo or `/mnt/e`.
- Next: Step 4 — merged-map publication (or rosbag/KITTI-06 live runs); Step 3 done below.

**Step 3 (2026-07-22, DONE + headless-verified): live loop closure + PGO + accumulated map.** `ros2/rap_server.py` (runs in conda env, NOT a ROS node: loads `RAPBackend` once, serves `register` + `pgo` requests over TCP 127.0.0.1:5557, length-prefixed pickle) + `ros2/loop_closure_node.py` (system python3 rclpy node: pairs `/points_raw`+`/odom` by stamp, streaming keyframes (6 m/12°), Scan Context + proximity candidates (sep 200, 15 m, SC<0.25), RAP verification in a worker thread (accept on overlap≥0.25 only), GTSAM PGO per accepted loop). Publishes TF `map→odom` (10 Hz, identity until first loop), `/map_path` (corrected trajectory, map frame), `/loop_edges` (cyan LINE_LIST markers), and `/map_cloud` (accumulated map: stride-5 scans pre-downsampled at 0.3 m voxels, rebuilt at latest corrected poses after each PGO and every 200 scans, capped at 500k points, ~0.17 s/rebuild; saved on shutdown as binary PLY). Path/marker/map QoS TRANSIENT_LOCAL so RViz late-starts see state. `run_step3.sh` (server→odom→loop→player→RViz, each waited on its readiness log line), `rviz/rap_slam_step3.rviz` (fixed frame `map`), `verify_step3_headless.sh [n] [rate]` (eval via conda python + evo vs POSS GT; also checks /map_cloud publish + PLY). **Verified twice: full 1419-frame POSS segment @12 Hz, 1419/1419 frames, loops (0,1394) overlap 0.76 + (0,1415) overlap 0.86 accepted, live odometry APE 8.257 m (= offline), live PGO APE 1.757 m (offline batch 1.821 m with 4 loops — the j=1418 pairs need the batch-only "last scan is keyframe" rule, unreachable in streaming), merged map 500k pts.** Products: `output_ros2/step3/`. GUI demo: `bash /mnt/e/githouse/RAP-SLAM/ros2/run_step3.sh` (**owner has NOT yet confirmed the Step-3 GUI — do that next session**).

#### Session handoff addendum (2026-07-22, end of session)

**Immediate next action (next session):** (1) owner confirms the Step-3 GUI demo (`bash /mnt/e/githouse/RAP-SLAM/ros2/run_step3.sh` — map cloud grows, trajectory snaps on loop closure); (2) push any unpushed commits (`git log origin/main..HEAD --oneline` in both repos); (3) then pick from: live runs on KITTI seq 01–04 (player `--data_dir` + `--real-apply-calib` equivalents), rosbag recording, SC yaw-hint consumption, hierarchical N-way backend, owner completing the KITTI seq 06 download.

**Done this session (2026-07-22):**
- **Step 2 complete + verified headless**: full 1419-frame POSS segment through player + `ros2/odometry_node.py`, live trajectory numerically identical to the offline pipeline (max diff 1e-6 m); KISS-ICP 18–45 ms/scan, real-time at native 10 Hz. GUI demo: `bash /mnt/e/githouse/RAP-SLAM/ros2/run_step2.sh`. Deps: `kiss-icp==1.3.0` installed into WSL **system python3** (with rclpy) via `pip --break-system-packages --ignore-installed typing_extensions 'numpy<2'`.
- **KITTI velodyne cleaned & assembled**: owner-provided partial extraction at `E:\githouse\Datasets\data_odometry_velodyne` (WSL: `/mnt/e/githouse/Datasets/...`). Kept complete seq **01, 02, 03, 04** (verified counts + contiguity + sample scans); deleted truncated 00/05; fixed one extraction artifact (`000001(1).bin` → `000001.bin` in seq 04). Copied poses 00–10 + calib/times for 01–04 into the tree → self-contained `--real-root`.
- **Fixed latent KITTI calib bug** (`rap_slam/real_dataset.py`): correct conversion is `Tr⁻¹ @ T_cam @ Tr` (was `Tr @ T @ Tr⁻¹`). KITTI 04 smoke (271 frames, 31.4 s): odometry APE 2.96 m / RPE 0.021 m; was 310.7 m pre-fix. Products in `output_kitti04_smoke/`.

**Owner pending:** completing the KITTI dataset (remaining sequences, esp. seq 06) at the same Datasets path. **Next session: re-check that dir first.** If new sequences appear: (1) sweep for `NNNNNN(1).bin` artifacts and rename, (2) verify per-sequence frame counts + contiguity against the canonical counts, (3) copy `poses/<seq>.txt` + `calib.txt` + `times.txt` from `RAP-SLAM/data/kitti/dataset/` into the tree, (4) smoke-run `run_pipeline.py --source real --real-root /mnt/e/githouse/Datasets/data_odometry_velodyne --real-seq <seq> --real-start 0 --real-end <last> --real-apply-calib`.

#### Session handoff addendum (2026-07-23)

**Done this session: KITTI live ROS 2 runs (full Step-3 stack) headless-verified on seq 04 / 03 / 01.** New scripts: `ros2/verify_step3_kitti.sh <seq> [n] [rate]` (headless; GT loaded from the Datasets tree with `apply_calib=True`; products in `output_ros2/step3_kitti<seq>/`, logs `output_ros2/*_kitti<seq>.log` — POSS artifacts untouched) and `ros2/run_step3_kitti.sh <seq> [rate]` (GUI demo variant, not yet run). The existing four nodes needed ZERO changes — already dataset-agnostic; player just gets `-p data_dir:=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset/sequences/<seq>/velodyne`. Results @12 Hz, full sequences: **04: 271/271 frames, odom APE 2.957 m (= offline 2.96 m), 0 loops (none exist on 04), PASS; 03: 801/801, odom APE 4.428 m (RPE 0.023), 0 loops, PASS; 01: 1101/1101, odom APE 117.8 m over a 2453 m highway path (~4.8% drift) — classic KISS-ICP behavior on KITTI 01 (fast, structureless highway, no place revisits → no loop candidates → PGO has nothing to correct), NOT a pipeline bug** (first-100-frame APE 0.42 m rules out a calib/frame bug; per-step RPE healthy at 0.037 m). **Seq 02 (4661 fr urban, same session):** 4661/4661 frames, 812 keyframes, odom APE 31.64 m = **0.62% of the 5.07 km path** (RPE 0.033, healthy KISS-ICP); the verify script's absolute 10 m threshold simply does not scale to 5 km. All 17 default-budget candidates were false (GT dist 177–386 m) and RAP correctly rejected every one (overlap 0.03–0.11 < 0.25). **Two important findings** (details in `RAP-SLAM/ros2/README.md`, products `output_ros2/step3_kitti02*/`): (1) **Retrieval misses seq-02's true loops in streaming** — GT shows 27 true revisit pairs (SC dist 0.087–0.172, well under 0.25) at scans ~930–1030↔~4200–4270 and ~1800–1820↔~4400–4410, but the POSS-tuned `max_total=16` budget was exhausted by false SC hits by scan ~1832, and even with `max_total=120, sc_shortlist=25` (121 proposals) true pairs never survive the ring-key top-N prefilter — repetitive urban geometry outranks them. (2) **~~HAZARD: overlap-only acceptance is NOT safe on KITTI urban streets~~ → FIXED 2026-07-23** — the big-budget re-run let RAP accept 11 FALSE loops (overlap 0.29–0.50, odom-consistency deceptively matched GT) → PGO APE blew up to 500 m. **Fix (commit `f59686f`): two-metric gate `overlap ≥ 0.7 AND mean_dist ≤ 2.5 m`** (mean_dist = mean symmetric NN distance after RAP alignment, added to `rap_backend.register` diagnostics; wired through `rap_server.py`, live `loop_closure_node.py` params, offline `loop_closure.verify_candidates` + `run_pipeline.py --max-mean-dist`; odometry-consistency stays diagnostic-only). Empirical basis (`scripts/eval_acceptance_gate.py`, 21 pairs): KITTI-02 TRUE loops overlap **0.853–0.959** (RAP transforms 1.2–4.3 m / ≤1.3° from GT) vs false loops 0.028–0.255 in batch re-score — but **live false overlaps reached 0.64** (opposite-direction urban streets genuinely align), so the separator is overlap with a clean gap 0.64 < 0.7 < 0.76; mean_dist only guards catastrophic failures (its distribution overlaps: false 1.26 m < true 1.45 m). Regressions: POSS live PASS (2/2 loops, PGO APE 1.757 m = baseline), offline POSS PASS (4/4 loops, 1.821 m), KITTI-02 gatecheck 121 verifications → **0 false accepts, PGO stable at 31.64 m**. Committed `cbc92f7` + `580d2d9` + `f59686f` on RAP-SLAM main. `verify_step3_kitti.sh` now has `LOOP_ARGS` / `SAVE_SUFFIX` env knobs for tuned re-runs without touching shared code. **Remaining open item:** KITTI-02's true loops are still never PROPOSED live (ring-key shortlist filters them out — retrieval recall), though the new gate would accept them (0.85–0.96).

**Immediate next actions (next session):** (1) owner STILL has not confirmed the Step-3 GUI demo — `bash /mnt/e/githouse/RAP-SLAM/ros2/run_step3.sh` (WSL: POSS map grows, trajectory snaps on loop closure); optional KITTI GUI variant `run_step3_kitti.sh 04`; (2) ~~fix the loop-acceptance gate~~ ✅ DONE 2026-07-23 (`f59686f`, overlap ≥ 0.7 AND mean_dist ≤ 2.5 m); (3) ~~improve streaming retrieval recall~~ ✅ DONE 2026-08-01 (`b39d116`, full-scan SC + cluster-persistence gate — see addendum below); (4) **PGO robustness** — 182 noisy RAP edges (median 2 m, worst 15 m) only bought 31.6→27.4 m on KITTI-02; try a robust kernel (Huber/DCS) on loop edges in `rap_slam/pose_graph.py` + offline noise sweep on the saved products (`output_ros2/step3_kitti02/accepted_loops.json` + `live_poses_kitti02.txt`, indices == frame indices, no GPU needed); (5) then: rosbag recording, SC yaw-hint consumption, hierarchical N-way backend, owner completing the KITTI seq 06 download (re-check `E:\githouse\Datasets\data_odometry_velodyne` first).

#### Session handoff addendum (2026-08-01, streaming retrieval rework)

**Done this session: fixed streaming retrieval recall — KITTI-02 went from 0 proposed loops to 182 accepted edges; POSS golden regression preserved bit-exact.** Commit `b39d116` (RAP-SLAM main).

- **Root cause (quantified by a new offline simulator `scripts/eval_streaming_retrieval.py`, no GPU/ROS needed):** the old policy (ring-key shortlist 10 + FIFO + `max_total=16`) proposed **0/37** true keyframe loop pairs on KITTI-02 — false SC hits (down to d=0.05 on repetitive urban streets, overlapping the true range 0.03–0.10) exhausted the budget by scan ~1832. What separates true from false is **persistence**: true revisits form dense clusters in (i,j) index space (27+ pairs per revisit site), while 38/77 false clusters are singletons.
- **New policy:** (a) `scan_context.sc_distances_batch` — vectorized shift-invariant SC matching against ALL earlier keyframes, no ring-key prefilter (matches `sc_distance` to 1e-6; ~10 ms/keyframe at 800 keyframes, fine in the spin thread); (b) `rap_slam/cluster_gate.ClusterGate` — strong SC hits (`sc_strong` 0.12) and proximity hits queue **immediately and uncapped**; weaker SC hits queue only when their (i,j) Chebyshev cluster (window 50 scans) reaches `min_cluster`=2 members, capped at 2 persistence promotions/cluster with 25-scan spacing NMS; (c) best-first `PriorityQueue` (SC by distance, then proximity), `max_total` default 0 (no permanent budget), `pgo_max_wait`=30 s so a busy queue can't starve PGO.
- **Two gate bugs found by simulation, fixed before live:** (1) capping *immediate* queueing let 2 false proximity hits fill a cluster's slots and block 27 true SC pairs — immediate queueing is now never capped; (2) persistence promotion lived in an `elif` so a prox arrival never triggered it — killed the POSS SC loop when `sc_strong`(0.10) < POSS's 0.106; now a separate `if`, and `sc_strong`=0.12 covers POSS's 0.106 immediately.
- **Live results:** POSS PASS — 1419/1419 frames, 2/2 loops (prox (0,1394) 0.76 + SC (0,1415) 0.86), odom APE 8.257 m, PGO APE **1.757 m = pre-rework baseline exactly**. KITTI-02 (clean run @10 Hz, 4661/4661, dropped=0): 256 verifications, **182 accepted / 84 rejected**; accepted = 125 edges GT ≤10 m (T_rel err median 2.05 m) + 57 edges GT 10–37 m (same-street constraints, T_rel err median 2.65 m, worst 15 m — mild street aliasing); all false candidates rejected by the 0.7/2.5 m gate (incl. the 0.64-overlap urban traps). Odometry APE 31.640 m (= reference, 0.62% of 5.07 km) → **PGO APE 27.387 m (−13%)**; residual error is in the long unconstrained one-way stretches (frames 0–900, 2000–3400 have no revisits). Script still prints FAIL only because of the absolute 10 m odometry threshold (known non-scaling criterion). Products: `output_ros2/step3_kitti02/` (182-loop `accepted_loops.json` is a clean PGO dataset for offline experiments — indices == frame indices).
- **Gotchas:** (a) **odometry node drops frames under CPU contention** (`queue_depth=1` by design) — 2 of 3 runs today lost 23–26 frames; dropped frames shift GT correspondence and make the eval's APE meaningless (60 m artifact); re-run at 10 Hz (`verify_step3_kitti.sh 02 4661 10.0`) for a clean run; `scripts/eval_live_dropped.py` attempts timestamp-based correspondence recovery (works only for coarse checks — publish jitter defeats exact recovery). (b) **The verify scripts DELETE the previous run's products at startup** (`rm -f` in `output_ros2/step3*/`) — copy anything you need BEFORE re-running (lost the first 185-loop run's `accepted_loops.json` this way). (c) The drain wait now counts `Loop worker idle` lines (mid-playback idle must not end the wait); `DRAIN_SECS` env knob (default 180/240) — KITTI-02's priority-queue backlog drains in ~4 min post-playback. (d) `eval_streaming_retrieval.py --preset {kitti02,poss} [--keyframes-json auto]` reuses live products (keyframes.json, live_poses) — `--keyframes-json auto` recomputes keyframes from odom poses with the node's exact streaming rule.
- **Also:** owner confirmed the Step-3 GUI demo works (2026-07-31) before the rework.

**Repo / sync state:**
- GitHub (private, owner account `YCDJ`): `YCDJ/RAP` and `YCDJ/RAP-SLAM`. Local dirs `E:\githouse\RAP-main` and `E:\githouse\RAP-SLAM` are git repos (branch `main`, remote `origin`, git identity `YCDJ <184950371+YCDJ@users.noreply.github.com>`, commit messages in English).
- RAP-SLAM pushed through `2075f5e` (P4 probe: Spires loader + wiring, 2026-08-23 10:5x; chain: P1 `a7072f0` → P2 `fdbbb56` → P3a `5933699` → P3b `1b4c871` → README `2f0d4d9` → P3c `833f71b` → README `b80b5e4` → P4-probe `2075f5e`); RAP pushed through `e2df6a3` + addenda through 2026-08-23 (P4-probe handoff below). **On session start, check for unpushed commits in both repos: `git log origin/main..HEAD --oneline` — push if non-empty.** Pushes to github.com can be flaky while big downloads saturate the link; retry-with-backoff succeeds. Use `GIT_TERMINAL_PROMPT=0`. **Push from WINDOWS Git Bash, NOT WSL: the WSL-side git has no GitHub credentials (`git push` fails with "could not read Username for 'https://github.com': terminal prompts disabled"), while Windows GCM credentials work. In WSL, root needs `git config --global --add safe.directory /mnt/e/githouse/<repo>` for status/commit (dubious-ownership error otherwise).**

**ROS 2 environment (WSL2 `Ubuntu-24.04`, root):** Jazzy installed via `scripts/install_ros2_jazzy.sh` (ros-base, rviz2, ros2cli, demo-nodes, sensor-msgs-py, colcon, python3-numpy; x11-apps/xdotool/wmctrl added during debugging). Player + odometry node run with **system python3** (`/usr/bin/python3`, where rclpy + kiss-icp live), not the conda env. Offline pipeline runs in conda env `rap-inference`. Viz entry points: `run_step1.sh` (player only), `run_step2.sh` (player + odometry); headless regression: `ros2/verify_step2_headless.sh [n_frames]`; software-GL fallback: prefix `RVIZ_SOFTWARE=1`.

**Agent operational gotchas (Windows host → WSL):**
- When invoking `wsl` from Git Bash, prefix `MSYS_NO_PATHCONV=1` and prefer repo-relative paths (Git Bash mangles `/mnt/...` args into the Git install dir); do **not** pass URLs or `\$VAR`-bearing command lines inline into `wsl bash -c` (quoting gets eaten — write a script file instead).
- Filter WSL's harmless NAT warning with `grep -av 'localhost'` (output can look binary to grep).
- WSL `/tmp` can be wiped between `wsl` invocations — keep verification state in the repo (`output_ros2/`) or `/mnt/e`.
- `pkill -f 'foo_node.py'` inside `wsl bash -c "... pkill ..."` kills the invoking shell itself (the pattern matches its own command line) and silently aborts the rest of the command — use the bracket trick `'foo_[n]ode.py'` or a separate call. Same for `pgrep -af` self-matches.
- Long verification runs exceed the 300 s tool cap: launch detached (`setsid bash script.sh > log 2>&1 < /dev/null &`) and poll the log in later calls; the verify scripts self-terminate all children. A full Step-3 POSS run at 12 Hz takes ~4 min.
- rclpy parameter typing is strict: a double-declared param rejects an integer literal (`-p rate:=15` → InvalidParameterTypeException); pass `-p rate:=15.0`.
- `wsl` from Git Bash may default to a NON-root user (`aaa`) even though the whole ROS/conda setup was done as root — conda envs live under `/root/miniconda3`, so permission errors mean you landed in the wrong user; always invoke pipeline work as `wsl -u root bash ...`.
- A detached `setsid bash script.sh > log 2>&1 < /dev/null &` launched inside `wsl bash -c '...'` gets killed when the outer command exits immediately; append `sleep 3` after the background launch inside the same command so the setsid child fully detaches.
- **`RAP-SLAM/scripts/_vendor/` can show every file as modified** after Windows-side touches — pure CRLF/LF churn (identical content, equal insertions/deletions). Restore with `git checkout -- scripts/_vendor` before staging; never commit that noise (hit 2026-08-09).
- In `wsl bash -c "... sed 's/x$/y/' ..."`, the `$` is eaten by Git Bash even inside double quotes — prefer `awk '/START/,0'` over `sed -n '/START/,$p'` (hit 2026-08-09).


**Verified results (RTX 5070, WSL2):**

| Dataset | Setup | Odometry APE RMSE | After PGO | Notes |
|---|---|---|---|---|
| Simulated loop on real KITTI-00 map | 101 scans, 80 m radius circle | 5.53 m | **3.67 m** | smoke test, `output/` |
| **POSS real LiDAR** (Velodyne-32e campus) | 1419 frames [3850–5268], 413 m path, true loop | 8.26 m | **1.82 m (−78%)** | 4/4 loop candidates true & accepted; **RAP verification error vs GT only 0.15–0.47 m / 0.0°**; 67.9 s total, `output_poss/` |
| POSS, `--loop-method both` (SC + proximity merged) | same as above | 8.26 m | **1.82 m** | reproduces baseline exactly, `output_poss_sc/` |
| POSS, `--loop-dist 5` proximity-only | drift 13.3 m > radius | 8.26 m | **8.26 m (0 loops)** | controlled failure case, `output_poss_prox5/` |
| POSS, `--loop-dist 5` + Scan Context | same drift | 8.26 m | **1.90 m** | SC alone rescued both true loops (RAP GT error 0.15/0.34 m), `output_poss_sc5/` |
| **KITTI odometry 04** (HDL-64E, 271 frames full seq) | first KITTI velodyne smoke, `--real-apply-calib` | 2.96 m (RPE 0.021 m) | 3.26 m (no true loops on 04) | 31.4 s total; RAP verify error 0.02–0.31 m on all 12 candidates; caught & fixed the inverted KITTI calib conversion, `output_kitti04_smoke/` |
| **KITTI 04 live** (ROS 2 Step-3 stack) | 271 fr @12 Hz, full seq, `verify_step3_kitti.sh` | 2.957 m (= offline) | 2.957 m (0 loops, none exist) | headless PASS; zero node changes needed, `output_ros2/step3_kitti04/` |
| **KITTI 03 live** | 801 fr @12 Hz, full seq | 4.428 m (RPE 0.023) | 4.428 m (0 loops) | headless PASS, `output_ros2/step3_kitti03/` |
| **KITTI 01 live** (highway, 2453 m path) | 1101 fr @12 Hz, full seq | 117.8 m (~4.8% drift) | 117.8 m (no revisits → 0 loops) | expected KISS-ICP highway drift, NOT a bug (first-100-fr APE 0.42 m, RPE 0.037 m), `output_ros2/step3_kitti01/` |
| **KITTI 02 live** (urban, 5070 m path) | 4661 fr @12 Hz, full seq, 812 keyframes | 31.64 m (**0.62%** of path, RPE 0.033 — healthy) | 31.64 m (0 loops accepted) | 17 SC/proximity candidates all false (GT dist 177–386 m) & RAP correctly rejected all (overlap 0.03–0.11); "FAIL" only vs the absolute 10 m script threshold, `output_ros2/step3_kitti02/` |
| **KITTI 02 live, retrieval rework** (`b39d116`) | 4661 fr @10 Hz, full seq, clean (0 drops) | 31.640 m (= reference) | **27.387 m (−13%)** | 182 loop edges accepted (125 GT ≤10 m + 57 same-street 10–37 m), 84/84 false rejected; old policy proposed 0/37 true pairs, `output_ros2/step3_kitti02/` |
| **KITTI 06 offline smoke** (loop-closure benchmark seq) | 1101 fr full seq, `--real-apply-calib --loop-sep 200`, 70 s total | 2.777 m (RPE 0.020) | **2.441 m** | 12/12 candidates accepted, ALL true — RAP verify GT err only 0.02–0.11 m / ≤1.9°; overlap 0.85–0.92, mean_dist 0.52–0.66 m, `output_kitti06_smoke/` |
| **KITTI 06 live** (ROS 2 Step-3 stack) | 1101 fr @10 Hz, full seq | 2.777 m (= offline exactly) | 3.221 m ⚠ dense-edge over-weighting (see 2026-08-08 addendum) | 114/114 proposals accepted, 0 false proposals, all at the true revisit site; headless PASS, map 500k, `output_ros2/step3_kitti06/` |
| **KITTI 06 live + loop-edge NMS w=10** | same, NMS live default | 2.777 m | **2.581 m (fixed, < odometry)** | NMS 114→25 edges at final PGO; matches the offline sweep prediction 2.573 m; PASS, `output_ros2/step3_kitti06/` |
| **KITTI 00 offline smoke** | 4541 fr full seq, `--real-apply-calib --loop-sep 200`, 294 s | 12.267 m (RPE 0.032) | **11.423 m (−6.9%)** | 12/12 candidates accepted, ALL true (RAP GT err 0.22–1.18 m, overlap 0.88–0.96); recall capped by `--max-candidates 12` default, `output_kitti00_smoke/` |
| **KITTI 05 offline smoke** | 2761 fr full seq, same flags, 187 s | 5.194 m (RPE 0.020) | **3.417 m (−34%)** | 12/12 accepted ALL true (GT err 0.018–0.525 m / ≤2.2°, overlap 0.86–0.97), `output_kitti05_smoke/` |
| **KITTI 00 offline, budget sweep** | 4541 fr, `--loop-sep 200 --max-candidates 40`, 289–345 s | 12.267 m (RPE 0.032) | **10.920 m**; +`--loop-nms-width 10` → **10.640 m (−13%)** | 40/40 accepted, ALL true — 4 revisit sites covered vs 1 at the default `--max-candidates 12` (11.423 m); offline NMS helps once the budget admits dense clusters, `output_kitti00_bigbudget*/` |
| **POSS-B offline smoke** (frames 6750–9500) | 2751 fr, `--loop-sep 200`, 282 s | 16.258 m (RPE 0.194) | **14.064 m (−13.5%)** | 12/12 accepted, ALL true (overlap 0.77–0.84, mean_dist 0.67–0.80 m; RAP GT err 1.45–2.06 m / 3.7–4.5°), `output_possb_smoke/` |
| **RC-4 hierarchical N-way** (offline, saved live products) | KITTI-02 182 edges → 12 clusters, joint registration per cluster + PGO | 31.640 m (= reference) | 26.87 m vs pairwise **26.423 m** (no gain) | per-edge N-way slightly better (2.33 vs 2.45 m med) but APE dominated by unconstrained stretches; POSS arm 1.763/1.808 vs 1.757 (seed noise); seed spread 0.126 m, `output_hier_nway*/` |

**Scan Context retrieval quality (POSS, `scripts/eval_loop_retrieval.py`):** 82 keyframes, true pairs = GT distance < 3 m & separation ≥ 200. True-pair SC distances 0.060 / 0.106 vs lowest false pair 0.347 (>3× margin) → **precision = recall = 1.0 for any threshold in [0.13, 0.30]** (pipeline default `--sc-dist-thresh 0.25`). Proximity retrieval at the default 15 m radius scores precision 0.50 (2 false positives), and recall collapses to 0 at radius ≤ 10 m because loop-closure drift is 13.3 m. Cost: 0.2 s to build 82 descriptors, 0.6 s for 654 pairwise matches — negligible vs RAP verification. SC also yields a per-pair yaw hint (column shift × 6°); evaluated 2026-08-01 as an RAP pre-rotation (RC-2) with zero benefit — RAP is yaw-invariant in practice — so it stays log-only diagnostics.

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

**Data inventory:** `RAP-SLAM/data/poss/dataset/` — POSS seq 00 poses (full 36924), calib, times, and frames 3850–5268 + 6750–9500 velodyne (4170 frames, ~4.2 GB total, downloaded via `scripts/download_poss_segment.py`, resumable; segB verified contiguous + artifact-free 2026-08-09). `RAP-SLAM/data/kitti/dataset/` — KITTI odometry calib + poses for all 22 sequences, **no velodyne scans**. **`E:\githouse\Datasets\data_odometry_velodyne\dataset/`** (WSL: `/mnt/e/githouse/Datasets/...`) — **COMPLETE KITTI odometry velodyne: all 22 sequences, verified 2026-08-01** (counts + contiguity + zip cross-check; 00–10 = 23201 scans, 11–21 = 20351 scans, matching the official totals; spot-checked frames valid) + poses 00–10 + calib/times for all 22 sequences — self-contained `--real-root` (use `--real-apply-calib`). Merged from the owner's full-archive download (`Datasets\part2\data_odometry_velodyne.zip`, 84.8 GB, extraction verified = zip; **zip DELETED 2026-08-16, owner-approved**). Note: test-seq frame counts differ from some online lists (13: 3281, 16: 1731, 17: 491, 18: 1801, 19: 4981, 20: 831, 21: 2721) but the 11–21 sum 20351 matches LO-Net exactly — these are the authentic counts.

#### Session handoff addendum (2026-08-01, RAP-CORE declaration + RC-1 PGO robustness DONE)

**Core goal restated: RAP-CORE SLAM** — RAP is the core of the system, not a plug-in verifier; see the declaration at the top of this section and the restructured "RAP-CORE roadmap" (RC-1…RC-5) below. **RC-1 done this session.**

- **Experiment (GPU-free, reuses saved live products):** `scripts/eval_pgo_robust.py` loads `output_ros2/live_poses_kitti02.txt` + `output_ros2/step3_kitti02/{keyframes,accepted_loops}.json` (indices == frame indices) and compares 27 PGO loop-edge noise models against evo APE on GT; `--dataset poss` reruns the same grid on the POSS live products (`live_poses_step3.txt` + `step3/`). Summaries: `output_ros2/eval_pgo_robust_summary.json`, `output_ros2/eval_pgo_robust_poss.json`.
- **Findings:** (1) RAP diagnostics correlate with true edge error but weakly (mean_dist r=+0.245, overlap r=−0.201) → use them for floor-relative loosening, not tight absolute sigmas. (2) Absolute adaptive sigmas (σ_t = mean_dist) are the best on KITTI-02 (+Huber: 25.688 m) but inflate covariance on near-perfect edges and regress POSS 1.757→1.961 m. (3) **Winner (new default): `relfloor` (σ scale = clip(mean_dist/1.0 m, 1, 3)) + Huber(k=1)** — KITTI-02 27.387→**26.423 m**, POSS bit-identical **1.757 m** (POSS edges' mean_dist 0.62–0.997 < 1.0 m ref ⇒ identical noise model by construction). (4) Robust kernels are cheap insurance: under 50% edge corruption @5 m σ, fixed weighting explodes to 86–107 m while kernelled variants hold ~25 m. DCS is NOT safe at small edge counts (dcs_p1 destroyed POSS: 8.19 m).
- **Integrated:** `rap_slam/pose_graph.py` (`loop_weighting` fixed|adaptive|relfloor + `robust_kernel` None|huber|dcs, defaults relfloor+huber; loop dicts now read `mean_dist`), wired through `ros2/rap_server.py` `_pgo` (req fields), live `loop_closure_node.py` (params `pgo_loop_weighting`/`pgo_robust_kernel`/`pgo_huber_k`/`pgo_dcs_phi`/`pgo_relfloor_*`; `_run_pgo` now sends mean_dist — it used to strip loop dicts to i/j/T_rel), and offline `run_pipeline.py` (`--loop-weighting/--robust-kernel/--huber-k/--dcs-phi/--relfloor-ref/--relfloor-cap`). End-to-end check through the integrated defaults: KITTI-02 26.423 m, POSS 1.757 m (`scripts/_check_pgo_integration.py`).
- **Live POSS golden regression with the new defaults: PASS** (`output_ros2/verify_poss_rapcore.log`, 2026-08-01) — 1419/1419 frames, loops (0,1394) 0.76 + (0,1415) 0.86, live odom APE 8.257 m, live PGO APE **1.757 m = baseline exactly**, map 500k pts. Products regenerated in `output_ros2/step3/`. Commits: RAP-SLAM `cb5dce0`, RAP-main `a1267ba`, both pushed.

#### Session handoff addendum (2026-08-01, dataset consolidation + KITTI-06 smoke + RC-2 FALSIFIED)

- **Dataset consolidation:** owner delivered the full KITTI odometry velodyne archive at `Datasets\part2\data_odometry_velodyne.zip` (84.8 GB) + extraction. Verified: extraction == zip exactly, zero `NNNNNN(1).bin` artifacts, all 22 sequences at canonical counts (00–10 = 23201 scans, 11–21 = 20351 scans — matches LO-Net's published totals; individual test-seq counts differ from some online lists — see Data inventory). Merged into the single self-contained tree `E:\githouse\Datasets\data_odometry_velodyne\dataset\` (sequences 00–21 velodyne + calib/times for ALL 22 + poses 00–10); duplicate 01–04 copies were verified identical (names/sizes/sample-md5) then removed from part2. Full-tree re-verification: ALL OK. **The 84.8 GB zip was deleted 2026-08-16 (owner-approved).** POSS segment unchanged (still frames 3850–5268).
- **KITTI 06 offline smoke** (first run on the new data, 70 s total): odometry APE 2.777 m (RPE 0.020) → PGO APE **2.441 m**; 12/12 loop candidates accepted, ALL true, RAP verification GT error only 0.02–0.11 m / ≤1.9° (products `output_kitti06_smoke/`). Seq 06 is now the cheapest full-pipeline regression with true loops.
- **RC-2 (SC yaw-hint → RAP pre-rotation): FALSIFIED — do not integrate.** `scripts/eval_yaw_prehint.py` re-scored 10 TRUE + 11 FALSE KITTI-02 pairs with vs without SC-yaw pre-rotation (`T1 = register(a, Rz(ψ)·b) @ Rz(ψ)`, ψ = shift×6°): the hint is accurate (median err 0.8° vs GT yaw) but pre-rotation changes nothing — TRUE dT err med 3.21→3.21 m, gate accepts 10→10/10, FALSE 0→0/11 (and no trap inflation). RAP is a genuinely global registration method — there is no yaw local minimum to escape. Caveat: KITTI-02's true revisits are all same-direction (max GT yaw 22°), so `scripts/eval_yaw_prehint_synth.py` re-tested with scan j synthetically rotated +90°/+180° (GT adjusted): **vanilla RAP is yaw-invariant** — dT/dR/overlap identical to the unrotated baseline even at 180° (the hint tracks the synthetic rotation to ≤4.1° but is unneeded; even a 91°-wrong hint did not hurt). Products: `output_ros2/eval_yaw_prehint.{json,log}`, `eval_yaw_prehint_synth.log`. Keep SC hint logging for diagnostics only.

#### Session handoff addendum (2026-08-01, RC-4 hierarchical N-way EVALUATED — no gain)

- **RC-4 (hierarchical N-way backend) evaluated on live products: no APE gain, keep pairwise.** `scripts/eval_hier_nway.py` (new): mines loop clusters via union-find over accepted edges (KITTI-02: 182 edges → 12 clusters; the 2 biggest are 41/34-member same-street CHAINS with 104–109 m bbox, not single places — chain-aware batch composition matters), jointly registers each ≥3-member cluster (`register_multi`, degree-trim to `--max-parts` 16, `--points-budget` 30k default), replaces each edge's `T_rel` with the cluster-consistent relative, re-runs PGO (defaults relfloor+huber), and repeats per seed. **KITTI-02: hier 26.872/26.930/26.803 m (seeds 42/43/44) vs pairwise 26.423 m; POSS: 1.763/1.808 vs 1.757 (within seed noise).** A 64k-point arm (4000 pts/scan = pairwise parity) confirms it's not point dilution: per-edge intrinsics even tilt N-way (med 2.33 vs 2.45 m) yet APE stays 26.894 — **the residual error lives in the unconstrained no-revisit stretches (frames 0–900, 2000–3400), which loop-side engineering cannot touch** (that is RC-5's target). Cluster layouts do NOT warp at ≤16 parts × ≤4000 pts (rmse 0.40–3.47 m; one 6.12 m outlier at 64k pts total — stay below). **Multi-seed variance now quantified: 0.126 m (KITTI-02) / 0.045 m (POSS) spread on final APE.** Products: `output_hier_nway/` + `output_hier_nway_64k/` (summaries + per-cluster npz cache). Gotcha fixed mid-run: POSS live products use SEGMENT-RELATIVE scan indices (file = idx + 3850). NB: the previous checklist called this item "RC-3"; the roadmap section's RC-3 is multi-generation confidence — roadmap numbering wins.

#### Session handoff addendum (2026-08-08, RC-3 multi-generation confidence EVALUATED + integrated as optional gate)

- **RC-3 evaluated (`scripts/eval_multigen_confidence.py`, 195 pairs × 4 generations, 19.4 min GPU): the value is GATE HARDENING, not PGO σ.** (a) Q1 σ-weighting: inter-generation dispersion correlates with true edge error only weakly (disp_t Spearman ρ=+0.165 vs mean_dist's +0.245 from RC-1); dispersion-scaled PGO variants all land within ±0.1 m of the 26.423 m default — NOT adopted. (b) Q2 gate separation — the big finding: **min overlap across k=4 generations cleanly separates TRUE (0.661–0.979) from FALSE (0.031–0.156)** loops, whereas single-generation overlap false positives reached 0.64 (margin to the 0.7 threshold: 0.06). False loops also show 90° bistable yaw flips (disp_r 89–90°). Multi-gen turns the acceptance margin from 0.06 into >0.5. (c) best-of-k estimate: KITTI-02 APE −0.45 m (25.976) but POSS golden regresses 1.757→1.827 — NOT default. Cost: 0.97 s/gen → k extra generations are cheap enough for borderline escalation, wasteful as default.
- **Integrated as an OPTIONAL consistency gate (default OFF, k=1 keeps legacy behavior):** `RAPBackend.register_consistent(points_a, points_b, k)` returns best-of-k T_rel + `overlap_min/overlap_all/disp_t/disp_r` diagnostics; offline `run_pipeline.py --multigen-k 3 [--min-overlap-min 0.4 --max-disp-r 30]`; live `ros2/loop_closure_node.py` params `multigen_k`/`min_overlap_min`/`max_disp_r` wired through `ros2/rap_server.py` (`register` request field `k`). Multigen gate rule: accept iff overlap_min ≥ min_overlap_min (0.4 — huge two-sided margin by design, true min 0.661 / false max 0.156) AND mean_dist ≤ 2.5 AND disp_r ≤ 30°.
- **Golden regressions (all PASS):** multigen k=3 offline POSS 4/4 loops accepted (PGO APE 1.856 vs 1.821 — best-of-k seed noise, within the quantified 0.126 m spread); multigen k=3 KITTI-06 smoke 12/12 accepted (odom 2.777 = baseline, PGO 2.516 vs 2.441, seed noise); **default k=1 offline POSS reproduces baseline bit-exactly (4/4, odom 8.257, PGO 1.821 m)**. Products: `output_multigen/` (samples cache + analysis json/log), `output_poss_mg/`, `output_kitti06_mg/`, `output_poss_default_check/`.
- **Recommended use:** enable `multigen_k=3` when running new/urban datasets where single-gen overlap traps are a risk, or as borderline escalation (re-verify candidates near the 0.7 threshold); leave k=1 for known-good regression runs.

#### Session handoff addendum (2026-08-08, RC-5 sparse odometry refinement EVALUATED — FALSIFIED, do not integrate)

- **Session opened with a repo-pollution audit** (owner reported hallucination/garbled text in the previous turn's chat reply). Verdict: **repos clean** — no uncommitted tracked changes, no unpushed commits, no mojibake/invalid-UTF-8 in any tracked source file (the only scan flags were legitimate vendored binaries under `RAP-SLAM/scripts/_vendor/`); RAP-SLAM `README.md` is intentionally Chinese; the previous turn's untracked RC-5 scripts were read in full and verified sane (every referenced API exists). The garbling touched only the chat reply, never any artifact. Note: `RAP-main/advisor_report/` and `RAP-main/ppt/` (untracked report PDF/PPT deliverables, see Project Overview) sat inside the nominally read-only repo at the time — **relocated to `E:\githouse\RAP-SLAM-report\` 2026-08-16**.
- **RC-5 evaluated (`scripts/eval_sparse_odom_refine.py`, new; products `output_odom_refine/`): FALSIFIED — replacing keyframe between-edges with RAP edges degrades PGO.** Sample phase (GPU 7.5 min): 434 consecutive-keyframe pairs — 412 in the no-revisit stretches (frames 0–900 / 2000–3400) + 22 control pairs from the loop-covered region (every 8th). Analyze phase (CPU):
  - **Q1: RAP between-edges are LESS accurate than KISS-ICP between-edges at keyframe baselines** (vs GT relative poses). Stretch: RAP med 0.105 m / 0.44° (p90 0.211) vs odom med 0.072 m / 0.09° (p90 0.165). Control: RAP med 0.097 m / 0.31° vs odom 0.076 m / 0.10°. The RC-5 premise (trade correlated drift for independent noise) fails on magnitude: short-baseline KISS-ICP relatives already beat RAP's ~0.1 m per-edge noise floor.
  - **Q2/Q3: PGO APE degrades monotonically with the number of replaced edges** (loops-only baseline 26.423 m; odom-only 31.640 m): stride=1 (412 refined) **72.984 m**, stride=2 51.054 m, stride=4 40.200 m; control-arm refinement 26.836 m ≈ baseline (specificity holds). Compounding cause: RAP edges are noisier AND were given the tighter loop-style relfloor noise model (0.03/0.20 base vs odom 0.05/0.30).
  - **Conclusion:** keep KISS-ICP between-edges untouched; RAP's role stays loop/submap constraints. The unconstrained-stretch residual (KITTI-02 ~26 m) is NOT fixable by edge replacement — remaining levers are front-end upgrade (deskew/LIO) or denser revisits. The 434 cached RAP edges (`odom_edge_samples.json`) remain reusable for future edge-level studies.

#### Session handoff addendum (2026-08-08, multi-dataset generalization: KITTI 06 live + 00/05 offline smokes)

- **KITTI-06 LIVE through the full ROS 2 Step-3 stack: PASS** (`ros2/verify_step3_kitti.sh 06 1101 10.0`; the script's seq case list gained 00/05/06 this session). 1101/1101 frames (no drops), live odometry APE **2.777 m = offline reference exactly**, merged map 500k pts. Retrieval + gate: **114/114 proposed candidates accepted, 0 false proposals** — all edges cluster at the single true revisit site (i∈[0,290] × j∈[826,1099], overlap 0.73–0.91). **But live PGO APE 3.221 m > odometry 2.777 m** (script WARNING, not a failure) — see the dense-edge finding below. Products: `output_ros2/step3_kitti06/`.
- **KITTI-00 offline smoke** (4541 fr full seq, `--real-apply-calib --loop-sep 200`, 294 s): odometry APE 12.267 m (RPE 0.032) → PGO **11.423 m (−6.9%)**; 12/12 candidates accepted, ALL TRUE (RAP GT err 0.22–1.18 m / ≤1.8°, overlap 0.88–0.96). Gain is capped by the offline `--max-candidates 12` default budget — seq 00 has several revisit sites, only one received verified edges. Products: `output_kitti00_smoke/`.
- **KITTI-05 offline smoke** (2761 fr full seq, same flags, 187 s): odometry APE 5.194 m (RPE 0.020) → PGO **3.417 m (−34%)**; 12/12 accepted, ALL TRUE (GT err 0.018–0.525 m / ≤2.2°, overlap 0.86–0.97). Products: `output_kitti05_smoke/`.
- **Generalization verdicts:** (a) **the acceptance gate generalizes** — across every dataset tried to date there are ZERO confirmed false accepts (POSS 4/4 true; KITTI-06 offline 12/12 + live 114/114; KITTI-00 12/12; KITTI-05 12/12; KITTI-02 84/84 false rejected). (b) **SC retrieval generalizes** at the default 0.25 threshold — true loops found on all new sequences without retuning; on 00/05 the recall limiter is the offline candidate budget, not separability. (c) **NEW ISSUE — dense redundant loop edges:** cluster-persistence retrieval can accept 100+ near-duplicate edges at one revisit site (KITTI-06: five edges from keyframe 0 alone); PGO treats them as independent and over-weights that site's ~0.7 m mean_dist noise, so when odometry is already excellent (RPE 0.02) PGO ends up slightly WORSE than odometry (2.777→3.221 m). On drift-dominated sequences (POSS, KITTI-02/00/05) the same edges still help. **Fix candidates: accepted-edge NMS/dedup (keep the best-overlap edge per (i,j) cell) before PGO, or correlation-aware covariance inflation for same-site edges — offline-first on saved products `output_ros2/step3_kitti06/` (GPU-free, same pattern as RC-1).**
- **Script bugs fixed this session:** `verify_step3_kitti.sh` (1) seq case list only knew 01–04 → added 00/05/06 (canonical counts 4541/2761/1101); (2) drain-wait `IDLE=$(grep -c ... || echo 0)` emitted "0\n0" when no idle lines existed ("integer expression expected" spam + early-break disabled, costing the full DRAIN_SECS every run) → changed to `|| true`.

#### Session handoff addendum (2026-08-08, loop-edge NMS integrated — KITTI-06 dense-edge pathology FIXED)

- **Finding (from the generalization runs above):** dense same-site loop clusters (KITTI-06 live: 114 accepted edges at one revisit site, endpoint degree ≤4) enter PGO as independent constraints → live PGO 3.221 m was WORSE than odometry 2.777 m.
- **Fix: greedy (i,j)-space NMS on accepted loop edges before PGO** (`nms_loop_edges` in `rap_slam/pose_graph.py`, keep the highest-overlap edge per Chebyshev-w cell). Offline sweep on saved live products (`scripts/eval_loop_edge_nms.py`, GPU-free): **w=10 is the sweet spot** — KITTI-06 3.221→**2.573 m** (below odometry), KITTI-02 182→38 edges 26.423→**26.018 m**, POSS 1.757 m bit-identical (its 2 edges are dj=21 apart). w=25 rejected (KITTI-02 30.274; POSS drops an edge → 1.787). Summary: `output_ros2/eval_loop_edge_nms.json`.
- **Integration asymmetry (deliberate): live default ON (w=10), offline default OFF.** The live streaming retrieval is deliberately uncapped (cluster-persistence) → dense clusters are its normal mode; the offline pipeline is budget-capped (`--max-candidates 12`) and its goldens stay bit-exact with NMS off. Wiring: `optimize_pose_graph(loop_nms_width=0)` library default; `rap_server._pgo` req field `loop_nms_width` (default 10.0); live node param `pgo_loop_nms_width` (default 10.0; the PGO wire dict now also carries `overlap`); offline `run_pipeline.py --loop-nms-width` (default 0).
- **Regressions:** (a) **POSS offline golden bit-exact 1.821 m** (`output_poss_nms_check/`). (b) **KITTI-06 live PASS: PGO 2.581 m < odometry 2.777 m** (3.221 pre-fix; WARNING gone; server log: NMS 114→25 edges at the final PGO; 1101/1101 frames), products `output_ros2/step3_kitti06/`. (c) POSS live: three runs tonight all hit the PRE-EXISTING odometry-drop flake (3/1/7 dropped frames; documented 2026-07-31, unrelated to NMS — the change adds ~µs of server-side work) so the eval FAILed on frame count and its APEs are not GT-comparable; loop-level behavior was correct on all three (2–3 true loops accepted; NMS a no-op on the sparse POSS edge set by construction, dj=21 > 10; PGO 1.698–2.052, in family with 1.757 ± seed noise + drop artifacts). **Re-run `ros2/verify_step3_headless.sh` when the host is idle for the clean PASS.**

**Immediate next actions (next session):** (1) push any unpushed commits in both repos (`git log origin/main..HEAD --oneline`); (2) clean POSS live golden re-run (`ros2/verify_step3_headless.sh 1419 10.0`, host idle — three runs on 2026-08-08 evening hit the odometry-drop flake); (3) owner GUI demo `ros2/run_step3_kitti.sh 06`; (4) rosbag recording; (5) POSS segment B if the owner downloaded it (checklist item 3); (6) optional: relocate `advisor_report/` + `ppt/` out of RAP-main; (7) optional: KITTI-00 with a raised `--max-candidates` (multiple revisit sites, only one got edges at the default 12) and/or `--loop-nms-width 10` arm.

#### Session handoff addendum (2026-08-09, odometry-drop flake ROOT-CAUSED + fixed; POSS-B validated; KITTI-00 budget sweep)

- **POSS live golden: clean PASS again** — 1419/1419 frames, 0 drops, loops (0,1394) 0.76 + (0,1415) 0.86, live odom APE 8.257 m = offline, live PGO APE **1.757 m = baseline exactly** (products `output_ros2/step3/`, log `output_ros2/verify_poss_rerun.log`).
- **Drop flake root cause — the "idle host" theory was WRONG:** odometry-node register times under the full Step-3 stack spike well past the 100 ms frame period (every-50-frame samples: 149/145/260/135/103/112 ms — sibling-node CPU + KISS-ICP local-map growth, not external load; load average was 0.05 and the flake reproduced 4/4). With the subscriber's `queue_depth=1` (real-time-freshness design), any >100 ms spike drops a frame (1–26 drops/run). **Fix: the verify scripts now pass `-p queue_depth:=20`** (`verify_step3_headless.sh`, `verify_step3_kitti.sh`; commit RAP-SLAM `daaf3d4`) — verification needs every scan for GT-comparable eval, and average register time (30–90 ms) is far below the period so spikes drain between frames. GUI run scripts unchanged (freshness policy for demos) but already accept `ODOM_ARGS="--ros-args -p queue_depth:=20"` if a demo must not skip scans.
- **Drain-wait fix (same commit):** `loop_closure_node.py` now emits `Loop worker idle` as a throttled 5 s heartbeat instead of a one-shot busy→idle transition log — the headless drain wait counts NEW idle lines after its sampling point, and a single transition line could precede the sample and cost the full DRAIN_SECS (240 s) on quick-drain datasets (POSS).
- **POSS segment B downloaded + validated:** frames 6750–9500 (2751 files, 2.8 GB), zero missing, zero `NNNNNN(1).bin` artifacts, sample scans ~63–65k pts @ ≤104 m. Offline smoke (`--loop-sep 200`, 282 s, `output_possb_smoke/`): 12/12 candidates accepted, ALL true (proximity+SC agree; overlap 0.77–0.84, mean_dist 0.67–0.80 m; RAP GT err 1.45–2.06 m / 3.7–4.5° — notably larger than segA's 0.15–0.47 m, keep in mind for future gate tuning), odometry APE 16.258 m → PGO **14.064 m (−13.5%)**.
- **KITTI-00 candidate-budget sweep (offline, `--loop-sep 200`):** default `--max-candidates 12` (PGO 11.423 m, one revisit site) → 40 candidates: 40/40 accepted, all true, four revisit sites (APE 12.267 → **10.920 m**); 40 + `--loop-nms-width 10`: **10.640 m (−13%)**. Retrieval recall headroom on multi-revisit sequences is real; offline NMS helps once the budget admits dense clusters. Products `output_kitti00_bigbudget*/`.
- **Owner decisions (all RESOLVED):** (1) ~~delete `Datasets\part2\data_odometry_velodyne.zip` (84.8 GB)~~ DONE 2026-08-16; (2) ~~relocate `advisor_report/` + `ppt/` out of RAP-main~~ DONE 2026-08-16 → `E:\githouse\RAP-SLAM-report\`; (3) ~~GUI demo `ros2/run_step3_kitti.sh 06`~~ confirmed 2026-08-09. Next technical items: rosbag recording, MCD/Livox generalization, front-end upgrade (deskew/LIO — the only lever for KITTI-02's unconstrained-stretch residual, per RC-5).

#### Session handoff addendum (2026-08-09, owner decisions: post-RC research directions + front-end upgrade APPROVED)

- **Owner confirmed the KITTI-06 GUI demo works** (RViz via WSLg, `ros2/run_step3_kitti.sh 06`, run from a WSL root shell; `wsl --shutdown` fixes a wedged WSLg, `RVIZ_SOFTWARE=1` is the software-GL fallback) — the last pending demo item is closed.
- **DECISION (owner, 2026-08-09): post-RC research directions, ranked:**
  - **Direction A — PRIMARY (paper headline candidate): submap-level N-way SLAM.** Keyframes → local submaps (5–16 scans) → RAP N-way joint registration within revisit clusters → cycle-consistent constraints → PGO over the submap graph. Uses RAP's headline capability (multi-view joint registration) instead of pairwise-only. Metric axes: APE on loop-rich datasets (POSS, KITTI-05/06/00 — RC-4 showed KITTI-02's residual lives in unconstrained stretches) + **map-consistency metrics as a second axis** (cycle consistency improves map quality even where trajectory APE doesn't move). Evidence base: POSS 5-part joint batch PGO 1.736 vs pairwise 1.821 (−4.7%); cluster per-edge intrinsics 2.33 vs 2.45 m med. First step: offline evaluation on existing products extending the `scripts/eval_hier_nway.py` framework (union-find clusters → submap composition → register_multi → submap-graph PGO), no new data needed.
  - **Direction B — SECONDARY (probe-first, kill fast if falsified): place recognition from RAP's encoder features.** Pool RAP point-encoder features into per-keyframe global descriptors; evaluate retrieval P/R vs Scan Context (POSS 82 keyframes + KITTI-02 keyframes separability probe, ~1–2 days). Inference-only probing — the repo has no training code; that constraint stands. Story if it works: one network both recognizes and registers (unified representation); targets urban repetitive-scene recall (KITTI-02's remaining retrieval gap).
  - **Direction C — paper section, not headline:** multi-generation uncertainty calibration (RC-3's dispersion→error correlation too weak for σ weighting, ρ=0.165).
  - **Direction D — ablation material (do NOT build):** RC-2 (yaw pre-hint), RC-5 (odometry edge replacement), one-shot full-graph N-way (82 parts, 55 m warp) — valuable falsified results for the paper's ablation section.
- **DECISION (owner, 2026-08-09): front-end upgrade APPROVED — deskew first, LIO deferred.** Rationale: KITTI-02's ~26 m residual lives in zero-revisit stretches (frames 0–900, 2000–3400) and KITTI-01's 117.8 m / 4.8% is pure odometry drift — loop-side methods cannot reach them (RC-5), the front-end is the only lever. Plan: (1) `.bin` scans carry xyzi only, no per-point time → synthesize LOAM-style timestamps from azimuth; (2) wire kiss-icp 1.3.0's built-in deskew (`config.deskew: bool = True`, verified present in the installed package) through `rap_slam/odometry.py`; (3) re-run offline goldens (POSS, KITTI-02/06/00/05) and compare. Expected (estimate, not measured): KITTI-01 4.8% → ~1–2% class, KITTI-02 odometry 0.62% → 0.4–0.5%; loop-rich datasets (POSS 1.757 m) barely move — itself a clean result. LIO only if the paper needs the last points: KITTI OXTS IMU lives only in the RAW dataset (throttled S3 download), POSS IMU availability unknown — check before committing.

#### Session handoff addendum (2026-08-09, Direction A EVALUATED — positive signal + hazard re-gate; Direction B probe DONE)

- **Pipeline products dump (new infrastructure):** `scripts/run_pipeline.py` STAGE 4 now writes `keyframes.json` + `accepted_loops.json` (T_rel/overlap/mean_dist — same schema as the ROS 2 live products) into the output dir, so every offline run is a reusable PGO/N-way dataset. Four goldens re-run into `output_prods/{poss,kitti06,kitti05,kitti00_bb}` (`scripts/_rerun_prods.sh`; KITTI via `--real-root /mnt/e/githouse/Datasets/data_odometry_velodyne --real-apply-calib --loop-sep 200`, 00 with `--max-candidates 40`) and **reproduce the references EXACTLY**: POSS 8.257→1.821, 06 2.777→2.441, 05 5.194→3.417, 00-bb 12.267→10.920.
- **Direction A evaluated** (`scripts/eval_submap_nway.py`; products `output_submap_nway/`, log `output_submap_nway_final.log`; `kitti06_live` added to the registry with TUM live poses `output_ros2/live_poses_kitti06.txt` + `loop_nms_width=10`; the script gained `load_tum` + per-dataset NMS config). Arms: pairwise / nway_raw / submap (consecutive-keyframe submaps as one `register_multi` part) / submap_clique (+ all intra-cluster submap-pair relatives in PGO); 5 datasets × seeds 42/43; metrics = evo APE + map consistency (Chamfer/recall@0.5 m/MME/loop-site alignment) + per-cluster layout-warp check. **Final gated SUMMARY (APE rmse, m; seeds 42/43, med):**

  | dataset | odometry | pairwise | nway_raw | submap | submap_clique |
  |---|---|---|---|---|---|
  | poss | 8.257 | 1.821 | 1.763/1.699 (1.731) | **1.705/1.688 (1.696)** | 1.724/1.691 (1.707) |
  | kitti06 | 2.777 | 2.441 | 2.441 (=) | 2.441 (=) | 2.441 (=) |
  | kitti05 | 5.194 | 3.417 | **3.234/3.146 (3.190)** | 3.398/3.448 (3.423) | 3.398/3.448 (3.423) |
  | kitti00_bb | 12.267 | 10.920 | 10.609/10.709 (10.659) | 10.508/10.524 (10.516) | **10.480/10.514 (10.497)** |
  | kitti06_live | 2.777 | 2.581 | 2.581 (=) | 2.581 (=) | 2.581 (=, re-gated 7) |

- **Direction A conclusions:** (1) on datasets with REAL multi-member clusters, submap batching consistently beats raw N-way AND pairwise (POSS med 1.696 best vs 1.821; KITTI-00_bb submap_clique med 10.497 best vs 10.920, its +30 clique edges all good); (2) near-perfect-edge datasets gain nothing from batching — KITTI-05 nway_raw best (med 3.190; its pairwise edges are already ~0.02 m accurate; submap neutral 3.423); (3) offline KITTI-06 has no ≥3-member clusters (12 edges → disjoint 2-member clusters) → all arms degenerate to baseline, no signal; (4) map-consistency metrics are a valid second axis (strongly separate odometry from PGO: POSS chamfer 1.344 → 0.6-class) but inter-arm separation is weak. Follow-up: chain-aware batch composition (street-chain clusters need chain-preserving part selection, not degree trim).
- **HAZARD found + fixed — warped edges from degree-capped street-chain clusters:** `kitti06_live` (114 live edges → ONE 97-member street-chain cluster) exposed two failure modes: (F1) degree-trim 97→16 parts shatters the chain → replacement edges get ZERO coverage (`edges replaced 0`) and the joint registration warps (layout rmse 40–75 m, seed-dependent); (F2) ungated clique edges injected the warp into PGO → **APE 135.7 m** vs baseline 2.581 (original record: `output_submap_nway_k06live.log`). Fix: replacement/clique edges pass a unified intrinsic RE-GATE. Threshold basis (`scripts/eval_submap_regate.py`, GPU-free dump of 48 candidate edges with GT error): good edges ov ≥ 0.588 / md ≤ 1.75; warped edges ov ≤ 0.486 / md ≥ 2.14 (GT error 184–280 m) → **re-gate = overlap ≥ 0.5 AND mean_dist ≤ 2.0** — a disaster detector, NOT a retrieval gate; deliberately looser than the 0.7/2.5 acceptance gate (the strict gate false-killed POSS: 1.705→1.838). With it: kitti06_live 7/7 garbage edges rejected → APE back to baseline 2.581 both seeds; KITTI-00 30/30 good clique edges pass; zero POSS false kills.
- **Direction B probe DONE** (`RAPBackend.extract_features()` — single t=0 DiT forward at x=cond → (M,512) tokens, mean/max/meanmax pooled — + `scripts/eval_rap_retrieval.py`; products `output_rap_retrieval/`, descriptor caches `*_descs.npz`; 0.31 s/frame; POSS 82 + KITTI-02 812 keyframes). **DiT features are WEAKER than Scan Context** (KITTI-02 AUC 0.755–0.819 vs SC 0.807, lower F1) → the unified recognize+register hypothesis is essentially FALSIFIED for DiT tokens. **Unexpected finding: miniSpinNet 32-D mean-pooled features — a FREE byproduct already computed inside every RAP `register` preprocess — strongly beat SC** (AUC 0.987/0.994 vs 0.807/0.954; F1 0.562 vs 0.407 @<10 m on KITTI-02). POSS arms all near-perfect (n=2 true pairs — weak statistics). Follow-up: per-query top-K streaming recall eval of spinnet_mean via `scripts/eval_streaming_retrieval.py`.
- **Commits:** RAP-SLAM `7ab2f06` (products dump + Direction A eval + re-gate + Direction B probe); RAP-main this addendum.

#### Session handoff addendum (2026-08-16, chain-aware N-way batch composition DONE — warp hazard eliminated, modest APE)

- **Fix (RAP-SLAM `19ea550`, `--compose {degree,chain}`, default degree for back-compat):** `chain_order()` sorts cluster members by the PCA-1 projection of their odometry positions (interleaves the revisited passes in spatial order along the street); `compose_batches()` cuts overlapping sliding windows (size `--max-parts`=16, stride 8) over that order — any pair within 8 in chain order (loop endpoints are chain-adjacent by construction) shares a window. Replacement edges use the first batch covering both endpoints; clique edges are intra-batch only, deduped across window overlaps (the old clique loop never updated `have` — fine for one batch, wrong for many). Single-batch clusters keep the legacy cache filename → POSS regression bit-exact (1.763/1.705/1.724 seed 42).
- **kitti06_live (seeds 42/43, baseline pairwise 2.581):** 12 windows, per-window layout rmse **0.09–0.10 m** (degree-trim: 67–69 m — warp ELIMINATED); replacement coverage **114/114** (was 0), 0 re-gated (submap seed 43 re-gated 2, net still healthy). APE: nway_raw 2.737/2.810 (med 2.773 — slightly worse; raw-scan chain edges noisier, intrinsic 0.08→0.12 m), **submap 2.575/2.512 (med 2.543, best, −1.5%)**, submap_clique 2.861/2.952 (med 2.906 — WORSE: ~233 clique edges at ONE dense site over-weight the within-window correlated bias; the 2026-08-08 dense-edge pathology in correlated form — NMS w=10 does not fix correlated errors).
- **kitti00_bb regression** (all clusters ≤ 16 → single batch, fresh RNG path): 10.422–10.700 across arms/seeds vs recorded 10.480–10.524 — within the documented ±0.05–0.1 m seed-path noise (RNG consumption order differs when datasets are run in a different subset/order).
- **Conclusions:** chain composition converts a catastrophic failure mode into a working one (coverage 0→114/114, warp 67 m→0.1 m) with neutral-to-slightly-positive APE on an already-excellent edge set — consistent with Direction A lesson 2 (near-perfect edges gain nothing from batching). Paper takeaways: (1) batch composition must be chain-aware; (2) dense same-site clique constraints need DOWN-WEIGHTING (within-window correlated errors), not just NMS. Products: `output_submap_nway_chain/` (+ `output_submap_nway_chain.log`).

#### Session handoff addendum (2026-08-16, Direction B follow-up DONE — spinnet_mean streaming recall eval)

- **`eval_streaming_retrieval.py` extended (RAP-SLAM `e020783`):** `--descriptor {sc,spinnet}` — cached miniSpinNet-32D mean descriptors (`output_rap_retrieval/<preset>_descs.npz`, aligned by frame index; POSS cache 82 kfs vs streaming 81 — by-index mapping absorbs it) as a drop-in matching signal for the new policy (cosine distance, own `--spinnet-thresh`/`--spinnet-strong`, per-descriptor `--sweep`). True-pair diagnostics now print SC and spinnet distance+rank side by side plus a streaming recall@K table. `descriptor=sc` behavior unchanged (regression: same 577/256/32tp numbers as the 2026-08-01 rework).
- **KITTI-02 streaming results (37 true pairs <3 m, sep≥200):**
  - Per-pair ranks at arrival: first revisit cluster (1803–1995↔4400–4565, 27 pairs) — spinnet ranks 1–3 at d 0.0005–0.0049 (**~50× sharper than SC's** 0.032–0.215); second cluster (3351–3410↔4580–4615, 10 pairs) — BOTH descriptors weak: spinnet ranks 8–60 (d 0.0075–0.0147), SC ranks 2–178 (d 0.18–0.44, several above the 0.25 threshold → never proposed).
  - Streaming recall@K (n=37): spinnet @1 **0.62** vs SC 0.54; SC saturates 0.86 @3; spinnet 0.89 @20.
  - Policy sim (new policy, t_verify=3 s): SC verified recall 0.86 (32/37) with 224 false verifications (12.8 GPU-min); spinnet at the 0.005 default was worse through the gate (0.76, strong=0.002 too tight → 6 first-cluster pairs cluster-gated), but the sweep found **thresh 0.002 → recall 0.89 (33/37) with 196 false (11.4 GPU-min) — beats SC on recall AND verification cost**.
- **POSS (weak statistics, n=1 true pair):** both descriptors rank 1; spinnet@0.005 is too loose there (11 false verifications vs SC's 1) — **spinnet thresholds are per-dataset** (POSS true-pair spin_d 0.0007 vs KITTI-02's 0.0005–0.0147).
- **Conclusions:** (1) spinnet_mean is a strictly sharper retrieval signal than SC on urban repetitive scenes — higher top-1, higher recall at tighter threshold, ~50× distance separation on the easy cluster; (2) it does NOT solve the hard second cluster (both descriptors fail there — that site's gap is viewpoint/direction, not descriptor sharpness; candidates: expose the SC yaw hint to a rotation-augmented spinnet match, or multi-view submap descriptors); (3) a hybrid OR of SC+spinnet through the same cluster gate is the natural integration (union recall 0.89+ with dedup) but needs a per-dataset calibration story — Direction B's "one network recognizes AND registers" story survives as "the registration preprocess's free feature byproduct doubles as the retrieval descriptor".
- Products: `output_rap_retrieval/stream_eval.log` (full tables), `stream_props_{sc,spinnet}.jsonl` (per-proposal dumps).

#### Session handoff addendum (2026-08-16, front-end deskew EVALUATED — POSS-only gain, KITTI falsified)

- **Wiring (RAP-SLAM `5f22b3a`):** `KissOdometry(deskew=)` synthesizes per-point timestamps from azimuth (`yaw = -atan2(y,x)`, normalized [0,1] — same convention as `kiss_icp.datasets.kitti_raw`, which is what KISS-ICP's C++ deskew preprocessor expects) and sets `cfg.data.deskew`; threaded through `run_odometry()`, `run_pipeline.py --deskew`, and the ROS 2 node (`-p deskew:=true`). Default OFF everywhere → pre-deskew goldens stay bit-exact (zeros timestamps = old code path; verified: POSS off re-run reproduces odom APE 8.257 exactly).
- **Sign probe (`scripts/eval_deskew_sign.py`, modes off/neg/pos, CPU-only):** KITTI-06 (fr 0–200): off RPE 0.0157 vs neg 0.0662 / pos 0.0450 — BOTH signs hurt 2–4×; KITTI-02 (fr 1000–1200): off 0.0387 vs neg 0.0709 / pos 0.0498 — same. POSS head (3850–4050): pos best (0.1553 vs 0.1932); **POSS full segment: neg best** (APE 8.257→6.989, RPE 0.2068→0.1738; pos 8.025/0.1857). Interpretation: KITTI odometry `.bin` scans behave as already motion-compensated (or per-point azimuth is a poor firing-time proxy for the HDL-64E) — any synthesized deskew only injects distortion; POSS (raw Velodyne-32e) genuinely benefits, with the KISS-ICP convention (neg) winning on the full segment that matters. Note the POSS head-segment/full-segment sign disagreement — the azimuth model is a coarse proxy for POSS too; the gain is real but modest.
- **Batch results (`scripts/_rerun_deskew.sh`, products `output_deskew/` — all runs dump keyframes/accepted_loops, so they are reusable PGO/N-way datasets):**

  | dataset | baseline odom → PGO | deskew odom → PGO | verdict |
  |---|---|---|---|
  | POSS | 8.257 → 1.821 | **7.040 → 1.602** | ✅ −15% odom / −12% PGO; 3/3 loops true (GT err 0.15–0.47 m) |
  | KITTI-06 | 2.777 → 2.441 | 10.334 → 3.031 | ❌ odom 3.7× worse |
  | KITTI-05 | 5.194 → 3.417 | 13.892 → 5.835 | ❌ odom 2.7× worse |
  | KITTI-00 bb | 12.267 → 10.920 | 23.213 → 12.173 | ❌ odom 1.9× worse |
  | KITTI-02 | 31.640 → 27.972 (offline baseline, NEW) | 70.927 → 60.636 | ❌ odom 2.2× worse |

- **Decision: deskew is a per-dataset opt-in — recommended for POSS-class raw spinning data, never for the KITTI odometry benchmark.** The 2026-08-09 expectation (KITTI-01 4.8% → ~1–2% class via deskew) is FALSIFIED for KITTI; the only remaining front-end lever for KITTI odometry residuals is LIO (still deferred — IMU lives in the throttled raw dataset) or accepting the status quo. Side observation: KITTI PGO still recovers most of the wrecked deskew odometry (10.334→3.031 on 06) — a back-end robustness data point, not a usable front-end.
- **Bonus: KITTI-02 offline no-deskew baseline established** (`output_deskew/kitti02_off/`): odom APE **31.640 m — matches the live reference exactly**, PGO 27.972 m (live 27.387 with its different edge set). Live/offline odometry equivalence re-confirmed.
- **Live deskew verification (2026-08-16, same day): PASS.** `SAVE_SUFFIX=_deskew ODOM_ARGS='-p deskew:=true' DRAIN_SECS=240 bash ros2/verify_step3_headless.sh 1419 10.0` (the POSS script gained the kitti-style `SAVE_SUFFIX`/`ODOM_ARGS` knobs, `2c18d30`; golden `step3/` untouched). Full 1419/1419 frames, 0 drops: live odometry APE **6.984 m** (golden 8.257 — matches the offline deskew probe's 6.989 almost exactly), live PGO APE **1.497 m** (golden 1.757, offline deskew 1.602), loops (0,1393) ov 0.76 + (21,1414) ov 0.74 (keyframe indices shift slightly with the changed odometry; both true-class). The offline deskew gain transfers fully to the live stack. Products: `output_ros2/step3_deskew/`, logs `output_ros2/*_deskew.log`.
- **Follow-ups:** the POSS pos-sign arm was not taken through PGO (its odom was already worse than neg — skipped).
- **Also committed:** `ac570f7` — `ros2/capture_rviz.sh`, a leftover headless RViz screenshot helper (Xvfb, shots to `output_ros2/rviz_shots/`), previously untracked.

#### Session handoff addendum (2026-08-22, advisor feedback → paper-phase plan DECIDED)

**Context:** Advisor feedback to the owner: (1) the SLAM paradigm needs a HORIZONTAL COMPARISON against established systems (with reasonable expected metrics); (2) the innovation story must move beyond "building-block assembly" (KISS-ICP + SC + RAP + GTSAM). This session ran a literature sweep and decided the post-RC plan; no experiments run.

**Literature findings (2026-08-22 sweep):**
- KITTI system-level reference (avg relative transl. drift %, seq 00–10; sources: KISS-ICP paper Tab. II, Hi-LOAM arXiv:2604.01720 comparison table): CT-ICP 0.50–0.53 (with loop closing), KISS-ICP 0.50 (OPEN-LOOP), MULLS/IMLS-SLAM 0.52, SuMa/SuMa++ 0.70–0.75, F-LOAM 0.84, LeGO-LOAM 2.49. ATE-RMSE table template to enter: SG-SLAM (arXiv:2503.11145) — KITTI ATE RMSE vs MULLS/CT-ICP/BALM2/SLIM/HBA/SuMa++/SA-LOAM/SELVO + an offline PGO combo; their avg ≈ 0.99 m on loop sequences (aligned ATE; semantic inputs — flag modality differences).
- **Protocol trap (critical):** literature "ATE RMSE" is almost always evo `--align` (SE(3) Umeyama); our pipeline reports first-pose-anchored UNALIGNED APE (`rap_slam/evaluate.py compute_ape_rpe(align=False)`). Never compare our unaligned numbers (2.44/3.42/10.9 m) against aligned literature numbers. P0 recomputes both protocols from saved trajectories (CPU-only).
- **Module-level reference:** LCDNet (KITTI-TRAINED) loop-pair TE 0.74–1.36 m / RE 6.4–7.5° at only 4–16% recall (reproduced in arXiv:2512.24384 Tab. III); that paper's own trained method reaches 0.09–0.54 m @ ~100% recall. Our saved RAP verifications are ZERO-SHOT at 0.02–1.18 m / ≤1.9° on true loops (KITTI-06 0.02–0.11 m) — already competitive with KITTI-trained SOTA loop closers. RAP's own pairwise KITTI benchmark is saturated (RAP & KISS-Matcher 100%, GeoTransformer 99.82% success on curated pairs) → the module comparison must be IN-PIPELINE (retrieval-proposed candidates incl. false urban traps → gate separation → end-to-end APE), not benchmark pairwise RR.
- **Novelty landscape:** FLOCC-SLAM (arXiv:2602.02430, RAL 2025) claims "3D foundation model-based loop closing" but is VISION (MASt3R on monocular image pairs) + decentralized multi-robot + needs scale-resolving PGO — cite & differentiate. RAP paper v2 appendix D.4 demos offline SLAM on FusionPortablev2/Newer College (2–10 s batch registration, NO loop closure, NO PGO) — cite & differentiate. Uncertainty→PGO prior art is classical (ICP covariance à la Censi; Hessian-inverse (H+I)⁻¹ loop-factor covariance, e.g. Sensors 26(10):3275, 2026) or learned for ICP — nobody calibrates a frozen GENERATIVE registration model's intrinsic outputs (overlap / mean_dist / multi-generation dispersion) into PGO noise models with cross-dataset transfer: niche confirmed OPEN.

**DECIDED plan (priority order P0→P5):**
- **P0 — Evaluation-protocol unification + comparison-numbers draft (CPU-only, START HERE):** new `scripts/eval_paper_metrics.py` — reload saved trajectories (`output_prods/*`, `output_ros2/live_poses_*`), compute (a) evo aligned APE (SE3), (b) KITTI official relative drift % (100–800 m segments) for all GT datasets; emit the horizontal table skeleton (ours vs SuMa++/CT-ICP/MULLS/KISS-ICP-open-loop/SG-SLAM-class). Decide per-sequence win/lose framing BEFORE writing claims.
- **P1 — Module-level verifier swap (same front-end/retrieval/back-end; the direct answer to "RAP core vs replaceable part"):** arms = ICP-from-odometry-init / ICP-from-SC-yaw-init / no-verification / RAP (saved). Reuse saved candidate sets (KITTI-02, POSS, KITTI-06 live products) → re-run PGO → APE + gate-separation stats. Learned-registration baselines: cite the RAP paper's cross-domain benchmark instead of re-running (GeoTransformer-class repos pin pre-2022 torch → Blackwell sm_120 env hazard; time-box a 2-day attempt, else fallback to citation).
- **P2 — Paper contribution 1: calibrated generative uncertainty.** Fit a conditional error model p(edge err | overlap, mean_dist, multigen dispersion) on KITTI-02's 182 saved edges (+ POSS), validate ZERO-ADJUSTMENT transfer on KITTI 00/05/06 + POSS; integrate as `loop_weighting=calibrated` in `rap_slam/pose_graph.py` (relfloor stays default until calibrated matches/beats it on ALL goldens; POSS golden must stay bit-exact or be justified).
- **P3 — Paper contribution 2: set-level loop closure.** Formalize chain-aware N-way composition + re-gate + NEW clique down-weighting (correlated within-window same-site edges — the 2026-08-16 lesson); complete the 5-dataset × multi-seed matrix with the map-consistency second axis; failure taxonomy (part-count/point-budget warp horizon, clique correlation).
- **P4 — Supporting: cross-sensor zero-shot + Properties & Limits section.** Download-feasibility probe FIRST from the China host: Newer College (Ouster OS1-64) preferred over MCD if faster; new loader + run the pipeline with IDENTICAL parameters (the zero-shot claim requires zero tuning). Properties section = compile RC-2/RC-3/RC-4/RC-5 falsifications + multi-seed variance + the odometry-consistency-free gate philosophy.
- **P5 — Paper writing** on top of the existing `paper/main.tex` outline (IEEEtran + ctex).
- **De-prioritized (kept):** rosbag recording (demo engineering), live N-way in ROS 2 (demo), LIO (KITTI front-end residuals; needs throttled raw-dataset IMU), MCD if download infeasible.

**Paper narrative (one sentence):** not "RAP plugged into SLAM" but "a frozen generative registration foundation model as the SLAM sensor model: (1) its intrinsic statistics calibrate into transferable PGO noise models; (2) its native N-way generation lifts loop closing from pairwise edges to cycle-consistent set-level constraints; (3) all zero-training, zero-shot across sensor embodiments". The headline is the PARADIGM + properties — NOT overall KITTI SOTA (CT-ICP-class front-ends out-tune us there; we win on loop-rich sequences, the isolated module comparison, and cross-sensor zero-shot).

**Housekeeping (RESOLVED same day, owner-approved "use your default"):** `paper/` relocated to `E:\githouse\RAP-SLAM-report\paper\` (alongside advisor_report/ + ppt/); forced rebuild PASS in WSL (`latexmk -xelatex -g`, fresh main.pdf). RAP-main tree 100% clean again.

#### Session handoff addendum (2026-08-22, P0 DONE — all saved trajectories recomputed on both APE protocols + KITTI official drift)

- **P0 DONE:** `RAP-SLAM/scripts/eval_paper_metrics.py` (CPU-only, conda env) recomputes ALL saved trajectory products on three metric families: unaligned APE (our convention), evo aligned APE (SE3 Umeyama — the literature "ATE RMSE" convention), and KITTI official drift ter%/rer (100–800 m subsegments, start-step 10, per-length mean then averaged). GT is derived automatically from each offline run's summary.json config (`real_root` + the `dataset/` subdir convention) or from the live-run registry (KITTI apply_calib=True, POSS False, segA offset 3850). Products: `RAP-SLAM/output_paper_metrics/paper_metrics.{json,md}` (12 offline + 7 live entries × {odometry, pgo}). Live↔offline equivalence re-confirmed (step3_poss odometry row == prods_poss odometry row, bit-exact).
- **Headline numbers (odometry → PGO; aligned APE rmse [m] / unaligned [m] / KITTI ter [%]):**

  | dataset | path [m] | aligned APE | unaligned APE | ter % |
  |---|---|---|---|---|
  | POSS segA | 420 | 2.565 → **0.665** (live 0.651; deskew live 0.629) | 8.257 → 1.821 | 3.589 → 1.315 |
  | POSS segB | 844 | 1.921 → **1.040** | 16.258 → 14.064 | 2.161 → 1.764 |
  | KITTI 06 | 1233 | 0.893 → **0.869** | 2.777 → 2.441 | 0.583 → 0.606 |
  | KITTI 05 | 2205 | 1.869 → **1.129** | 5.194 → 3.417 | 0.764 → 0.688 |
  | KITTI 00 (bb) | 3723 | 3.938 → **2.264** | 12.267 → 10.920 | 0.902 → 0.909 |
  | KITTI 02 (offline / live) | 5067 | 7.953 → **4.410 / 6.930** | 31.64 → 27.97 / 27.39 | 1.234 → 1.196 / 1.612 |
  | KITTI 01 (no loops) | 2453 | 19.874 (= odom) | 117.8 | 2.256 |

- **Three findings that shape the experiment section:**
  1. **Alignment flips our optics:** POSS-B 16.3 m unaligned → 1.9 m aligned; every loop-rich dataset lands at **0.63–2.26 m aligned APE after PGO** — the same ballpark as SG-SLAM's semantic-aided ~0.99 m loop-sequence average, achieved zero-shot, LiDAR-only, no training.
  2. **The KITTI official metric is odometry-dominated:** PGO barely moves ter (06: 0.583→0.606; 00: 0.902→0.909; 02: 1.234→1.196) while unaligned APE improves 12–78%. Loop-closure value must be argued via APE + map consistency, NOT the official metric (the same effect is reported by the GICP matching-cost-factor paper, arXiv:2109.07073 — cite it).
  3. **Our ter is ~2× CT-ICP per-seq** (06: 0.58 vs 0.27; 05: 0.69 vs 0.25; 00: 0.90 vs 0.49) — the front-end runs untuned KISS-ICP (max_range 80 / voxel 0.8 / no motion compensation; the KISS-ICP paper's 0.50 avg used tuned params). System-table framing: competitive on loop-rich sequences, not leaderboard SOTA. Optional P0.5: a tuned-front-end arm (max_range 100, smaller voxel) for the system table ONLY — it would break golden bit-exactness, so default-param goldens stay the canonical regression; report tuning separately.

#### Session handoff addendum (2026-08-22, P0 CLOSED — horizontal comparison table emitted; labeling note)

- **DONE (RAP-SLAM `2f158b2`, `18f50e8`, `f0599f2` — pushed):** `data/literature/kitti_baselines.json` (**now versioned** — .gitignore changed `/data` → `/data/*` + `!/data/literature/`; per-seq ter/rer for 15 methods transcribed from MULLS arXiv:2102.03771 Tab. II, CT-ICP arXiv:2109.12979 Tab. I, PSF-LO arXiv:2010.13355 Tab. II, KISS-ICP arXiv:2209.15397 Tab. II; convention notes embedded: MULLS/CT-ICP apply 0.2°/0.205° intrinsic correction, we do NOT; CT-ICP AVG = all-segment average, not per-seq mean; KISS-ICP paper reports split means only) + `scripts/make_comparison_table.py` (CPU-only merge → `output_paper_metrics/comparison_table.{md,json}`: ter/rer per-seq with a 00–06 mean column + aligned-ATE table with loop-count annotations; found & fixed a POSS-B loop-count label bug: `'poss' in 'possb_smoke'` matched seg-A's 4/4 — use exact key equality) + `scripts/rerun_pgo_saved.py` (re-run PGO from saved live products with the CURRENT backend). **KITTI-02 current-backend authoritative: unaligned 26.018 m / aligned 4.035 m** (old backend 27.387 m — exactly matches the `eval_loop_edge_nms` prediction); POSS / KITTI-06 re-runs bit-exact vs stored (1.757 / 2.581 m).
- **Labeling note:** the commit messages say "P1" but per the 2026-08-22 decided plan this work IS P0's "horizontal table skeleton" deliverable — **P0 is now CLOSED**. The plan's P1 (module-level verifier swap: ICP-from-odom-init / ICP-from-SC-yaw-init / no-verification / RAP arms on the saved KITTI-02 + POSS + KITTI-06 candidate sets → PGO → APE + gate-separation stats) is UNTOUCHED and is the next session's first item.
- **Table headline (ours full, aligned ATE rmse):** 00: 3.94→**2.26 m** (40/40 true loops), 02: 7.95→**4.04 m** (182 edges), 05: 1.87→**1.13 m**, 06: 0.89→**0.87 m**, POSS-A 2.56→**0.67 m**, POSS-B 1.92→**1.04 m**; 00–06 mean ter 1.13 % (odom) / 1.13 % (full) — weaker than CT-ICP/MULLS per-seq (front-end is POSS-tuned KISS-ICP; seq-01 highway inflates the mean) → narrative per the plan: ter argued as odometry-dominated, loop value via ATE + map consistency.
- **Failed/unused literature sources (do not retry):** arXiv IDs 2103.01116 / 1906.04632 / 2207.07661 / 1806.01722 are WRONG papers (blockchain/malware/cond-mat/Kähler); correct: LCDNet = arXiv:2103.05056, CT-ICP = 2109.12979, KISS-ICP = 2209.15397, MULLS = 2102.03771; roboticsproceedings.org/rss14/p07.pdf is NOT SuMa. LCDNet's SLAM ATE table + SuMa paper's own table were never fetched (arXiv HTML/PDF fetches truncate at 50k chars, tables sit at the end) — the table is sufficient without them; fill only if P5 wants more ATE-side rows (needs ranged fetches or a mirror).

#### Session handoff addendum (2026-08-22, P1 DONE — module-level verifier swap; the direct answer to "RAP core vs replaceable part")

- **DONE (RAP-SLAM `a7072f0`):** `scripts/eval_verifier_swap.py` (CPU-only, WSL conda env, open3d point-to-point) replays the live system's ACTUAL proposed candidate sets through four verifier arms with identical front-end (KISS-ICP), retrieval (the parsed candidate lists), acceptance gate (overlap ≥ 0.7 & mean_dist ≤ 2.5 on the exact clouds RAP saw, via `RAPBackend.preprocess`/`_alignment_metrics` with a SimpleNamespace stand-in — no model load), and back-end (relfloor+Huber, NMS w=10). Candidate sources: KITTI-02 = parsed `loop_node_kitti02.log` (256 pairs, 154 sc + 102 prox, with live-logged yaw hints); KITTI-06 = `accepted_loops.json` (114 pairs — canonical log was overwritten by a later partial run; 0 false proposals existed); POSS = `loop_node.log` (2 pairs).
- **Arms:** `noverif` = accept all at IDENTITY T_rel (**the odom-prediction variant is information-free — it duplicates the odometry factors and PGO cannot move; first implementation fell into this trap**); `icp_odom` = two-scale ICP 5.0→1.0 m from odom init; `icp_scyaw` = ICP from odom ∘ SC-yaw; `rap` = saved.
- **Results** (`output_verifier_swap/swap_table.{md,json}` + per-candidate diagnostics + per-arm TUM; gitignored, regenerable in ~90 s):
  - **KITTI-02** (candidate pool 32 ≤3 m / 93 3–10 / 70 10–30 / 61 >30 m truly-false): noverif → **APE 31.6→265 m, ter 59 %** (map destroyed). icp_odom and rap both reject (nearly) all truly-false (**0 vs 1** >30 m accepts) — **the two-metric gate transfers across verifier engines**. Where both accept, RAP's edges are ~2× more accurate (median **2.03 vs 3.58 m**); aligned APE **4.035 vs 5.005**, ter **1.237 vs 1.342**. RAP additionally recovers 11 same-street constraints (11–37 m GT) ICP cannot align from the odom init — ICP's accepted set is a STRICT SUBSET of RAP's. ICP's unaligned APE 24.423 < RAP 26.018 ONLY because its leaner edge set skips those noisy same-street edges (fewer edges, not better edges).
  - **KITTI-06** (114 true, short-init easy loops): ICP refines marginally tighter (0.07 vs 0.08 m; APE 2.513 vs 2.581) — honest limit: on easy loops ICP-from-good-init is competitive. Recomputed SC yaw hints (318–342° from SC shift aliasing on repetitive structure) made ICP LOSE 4 true loops — corroborates RC-2 (hint useless for RAP) with evidence it is even harmful for ICP.
  - **POSS** (2 true loops, 13 m drift): rap 1.757 m best, icp_odom 1.774 m (converged — revisit rotation error was only 2.5–3.8°), noverif 2.270 m (Huber+relfloor absorbed part of the identity-edge damage; POSS has no false candidates so nothing catastrophic).
  - **Regression:** all three rap arms reproduce the `rerun_pgo_saved.py` references bit-exact (26.018 / 2.581 / 1.757 m).
- **Paper framing:** the swap answers "is RAP a replaceable plugin?" with nuance — (1) verification itself is indispensable (265 m); (2) the gate is verifier-agnostic (a contribution independent of RAP); (3) RAP's value = 2× edge accuracy + a wider convergence basin (+11 hard constraints) + robustness where ICP needs good init — the margin grows with drift/rotation, and 02's ICP "win" on unaligned APE is an artifact of accepting fewer noisy edges.
- **Implementation gotchas recorded:** POSS log pads indices (`pair (  0, 1394)`) — regex needs `\s*`; RAP-arm overlap/mean_dist must come from `accepted_loops.json` full precision, NOT the log's 2-decimal printout (26.158 vs 26.018 artifact); SC-yaw sign calibration on accepted SC pairs TIED at 2.8/2.8° (hints ≈ 0 on accepted pairs — odometry rotation drift at revisits is small, translation dominates).
- **Push status:** `a7072f0` pushed 2026-08-23 08:2x after the outage cleared. Host network is INTERMITTENT (dropped again 08:40) — always verify with `git log origin/main..HEAD --oneline` on session start.

#### Session handoff addendum (2026-08-23, P2 DONE — calibrated generative uncertainty; honest mixed outcome)

- **DONE (RAP-SLAM `fdbbb56`, local; push pending — network intermittent):** `scripts/eval_calibrated_weighting.py` (CPU) assembles **378 saved edges with GT errors** (fit: KITTI-02's 182 live edges + POSS 18 (4 off + 2 live + 12 possb-from-summary, the latter analysis-only: possb summary stores gt errs but no T_rel); transfer: KITTI-00_bb 40 / 05 12 / 06 off 12 / 06 live 114) + RC-3 multigen dispersion features (184 edges), fits σ(mean_dist) by log-log LSQ rescaled to 68.3 % coverage, and `pose_graph.py` gains `loop_weighting="calibrated"` + `calib_params` (**default relfloor UNCHANGED**). Products `output_calibrated/` (edge_dataset.json + fit_report.{md,json}; gitignored).
- **Findings (the paper-relevant part):**
  1. Post-gate RAP edge error is ~INDEPENDENT of its own geometry diagnostics on accepted edges — Pearson r vs ln(gt trans err): **mean_dist 0.022, overlap 0.044** (n=188); multi-generation dispersion is the ONLY feature with signal (**r=0.377**, n=184; sharper in-sample calibration 76 % vs 85 % 1σ-coverage) but needs extra sampling passes and RC-3 showed no PGO gain → the transferable calibrated model is **near-constant: σ_t = 2.835·md^0.032 m, σ_r = 1.174·md^0.305 deg**.
  2. Stock PGO noise models are catastrophically overconfident in translation: fixed/relfloor 1σ trans coverage **2 %** on the fit set (target 68 %), adaptive 28 %, calibrated 86 %. Rotation is over-conservative instead (98–100 %).
  3. Zero-adjustment transfer: 100 % trans coverage on 00/05/06 — safe but over-conservative; **the error LEVEL is set by candidate difficulty, not the sensor; the flat SHAPE transfers**.
  4. Golden PGO regression (7 goldens, calibrated vs relfloor): all within ±5 %; aligned APE better on 00/02/06live/posslive (02: 3.78 vs 4.04 m; poss_live 1.674 vs 1.757 m). Per the predeclared criterion (match/beat ALL goldens) **relfloor stays default**; calibrated remains available via `loop_weighting="calibrated"` + `calib_params`.
- **Implementation gotchas:** offline `odom_poses.txt` is **KITTI 3×4 (12 cols), NOT TUM** — `load_poses_auto` (rerun_pgo_saved's `load_tum` silently garbage-parses 12-col files: offline goldens showed 253–399 m APE until caught; the three live goldens stayed bit-exact which is how the bug was isolated); clamp gt errors ≥1e-3 before log fits (near-perfect 05/06 edges have 0.00 deg rot err); keep calib rotation params in radians end-to-end (gtsam convention) — a deg/rad mixup between the analysis script and pose_graph produced plausible-but-wrong intermediate results.
- **Next per plan: P3 set-level loop closure + clique down-weighting** (formalize chain-aware N-way composition + re-gate; complete the 5-dataset × multi-seed matrix with the map-consistency second axis; failure taxonomy). Then P4 cross-sensor (Newer College feasibility probe first) and P5 writing.

#### Session handoff addendum (2026-08-23, P3a + P3b DONE — clique down-weighting + map-consistency axis)

- **P3a DONE (RAP-SLAM `5933699`, pushed):** `pose_graph.py` gains `clique_downweight={"component","degree"}` + `loop_clique_*` params (**default OFF — NMS stays default**); `scripts/eval_clique_weighting.py` compares raw / NMS(w=10) / clique-component σ·√k / clique-degree σ·√(1+deg) on all 7 goldens. Products `output_clique_weighting/clique_report.{md,json}`. Findings: NMS keeps the crown on 06-unaligned (2.581 m); **clique-comp is best on 06-aligned (0.872 m) and 00_bb-unaligned (10.795 m); clique-deg best on 02-unaligned (25.996 m)** — a principled no-edge-dropped alternative to NMS, aligned-protocol even better; component mode over-merges KITTI-02's long chain into one giant component (27.845 m degradation) → **degree mode preferred** in the paper discussion. Sparse goldens are near-no-ops as required (POSS live 1.757 bit-exact).
- **P3b DONE (RAP-SLAM `1b4c871`, pushed):** `scripts/eval_map_consistency.py` — second evaluation axis in MAP space next to trajectory APE. Merges keyframe scans at odometry / PGO (canonical current-backend products) / GT poses (**first-pose anchored, same gauge as the unaligned-APE convention — POSS GT lives in a global frame; without anchoring you get a 454 m Chamfer artifact**), per-scan voxel 0.4 m → global 0.3 m → 500k cap; reports symmetric **Chamfer mean/p95 vs the GT map** + **leave-one-scan-out crispness** (GT-free double-vision measure, 1 m cap). Products `output_map_consistency/map_report.{md,json}`.
- **P3b findings: PGO improves Chamfer on 7/7 goldens**, magnitude tracking the trajectory-APE gains (POSS off 3.065→0.687 = −78 % matching APE −78 %; 05 −36 %; 00bb −11 %; 02live −12 %; 06 ±6–10 %). POSS live with 2 loops (0.660) ≈ POSS offline with 4 loops (0.687) in map space. Crispness co-monotone but low dynamic range (0.24–0.52 m) → usable as a GT-free deployment monitor. Chamfer p95 stays large (02: 41.7 m) — residuals live in the unrevisited stretches, corroborating RC-4/RC-5: loop-side engineering is at its ceiling, front-end upgrade is the only lever left.
- **README.md P3a/P3b sections written** (committed with this addendum's sibling commit on RAP-SLAM `main`).
- **Next per plan: P3c — the 5-dataset × multi-seed N-way matrix** (GPU `register_multi` re-runs, ~30–40 s/batch on the RTX 5070; formalize chain-aware batch composition + the post-N-way re-gate ov≥0.5/md≤2.0 from the 2026-08-09 submap eval; failure taxonomy: ≤16 parts × ≤4000 pts no warp / 82-frame one-shot 55 m global warp / clique correlation). Then P4 (Newer College feasibility probe) → P5 writing.

#### Session handoff addendum (2026-08-23, P3c DONE — N-way matrix closed; edge-cover trim is the methods-section takeaway)
- **DONE (RAP-SLAM `833f71b`, pushed):** `scripts/eval_nway_matrix.py` (GPU, 534 s total) — hierarchical N-way over **all 7 goldens × seeds 42/43/44 × 3 arms** (canonical pairwise baseline with built-in regression check **7/7 PASS** / hier / hier + md≤2.0 re-gate). Products `output_nway_matrix/matrix_report.{md,json}` + per-cluster npz caches (`--reuse-cache`).
- **Chain-aware batch composition — the real methods contribution:** RC-4's degree-top-N cluster trimming has a **bipartite trap**: at a two-pass revisit site (all edges cross-pass) the highest-degree nodes can all be on the SAME pass → kitti06_live's 97-member cluster got 0/114 coverable edges and the one-sided 16-part batch **warped 61.9 m**. NEW `edge_cover_trim` (greedy: repeatedly pick the member that completes the most new both-endpoints-kept edges, degree tie-break) → 18/114 coverable, **warp 0.10 m**, and hier s42 2.487 m < baseline 2.581 m. Batch connectivity is decisive for joint-registration stability.
- **Matrix outcome (unaligned/aligned APE, hier across seeds):** kitti00_bb 10.920/2.264 → **10.42–10.89 / 2.18–2.23 (consistent small gain, all seeds)**; kitti05 3.417 → 3.19–3.42; poss_off 1.821 → 1.66–1.88 (seed noise); kitti02_live 26.018 → 26.18–26.42 (slightly worse; per-edge N-way median 3.18 vs pairwise 2.60 m — N-way NOT better here, reversing RC-4's edge-level note under edge-cover with 115 replaced edges vs 91); kitti06_live 2.581 → 2.487–2.781 (mixed); poss_live 1.757 → 1.763–1.837 (seed noise; s42/s43 **bit-match RC-4** 1.763/1.808 ✅). kitti06_off: 12 edges = 12 singleton clusters → N-way vacuous. **Overall verdict unchanged: pairwise stays default; N-way = methods-section discussion + taxonomy, no accuracy claim.**
- **Re-gate honest negative:** hier == hier_gate on EVERY row — the md≤2.0 gate never fired. **Layout warp is a low-frequency global bend invisible to pairwise NN metrics** (KITTI-02 clusters warped 6–7 m still show md med 0.6–0.9 m, gate PASS). The md gate only catches catastrophic misalignment (the 61.9 m one-sided batch). GT-free warp detection needs cycle-consistency residuals (triangle-closure disagreement inside the cluster) — future work.
- **Failure taxonomy (revised):** the "≤16 parts × ≤4000 pts = safe" regime does NOT hold on KITTI-02's self-similar urban geometry — even 3–16-part batches warp 1.3–7.3 m there; POSS/05/00/06 clusters never warp (0.01–0.5 m). **Warp is governed by geometric self-similarity, not batch size**; batch size only sets the warp's spatial frequency (82-frame one-shot = 55 m global bend). Two-pass of the same street = highest warp risk; degree-trimmed one-sided batches = catastrophic.
- **Implementation note:** per seed the script makes TWO passes (all `register_multi` first, gate preprocessing after) so the per-seed RNG stream is identical across arms and cache reruns; `rap.preprocess` between inferences would otherwise shift subsequent sampling draws (harmless but breaks comparability with RC-4's stream).

#### Session handoff addendum (2026-08-23, P4 PROBE DONE — target pivoted to Oxford Spires; downloads STARTED, pipeline wired, smoke NOT yet run)

- **Feasibility verdict:** Newer College is **infeasible from this host** — its download page is an embedded **Google Form** and the data sits on **Google Drive; both docs/drive.google.com time out (HTTP 000)** here. Pivot per the predeclared gate: **Oxford Spires Dataset (IJRR 2025)** — Hesai **QT64** (64 ch, **104° VFoV**, 60 m range, 10 Hz, rolling-shutter) on a **backpack** rig, 24 sequences / 6 Oxford sites, TLS-registered GT (**1–2 cm**) as `processed/trajectory/gt-tum.txt` (TUM). Hosted on Hugging Face `ori-drs/oxford_spires_dataset`: huggingface.co blocked, but **hf-mirror.com API + resolve works, LFS redirects to us.aws.cdn.hf.co (AWS CloudFront, reachable), measured ~3 MB/s sustained with Range support** → a 2.2 GB `lidar-clouds.zip` ≈ 13 min. Sensor is genuinely different from Velodyne/Ouster arms → a real cross-sensor zero-shot test.
- **Per-sequence layout:** `sequences/<seq>/raw/lidar-clouds.zip` (~2.2 GB, `<epoch>.pcd` binary, sweep-start timestamp), `raw/images.zip` (5.8 GB, not needed), `raw/imu.csv` (16 MB, for a future LIO axis), `processed/trajectory/{gt,vilens-slam,hba,colmap}-tum.txt` (benchmark baselines free for the comparison table). **keble-college-01 and christ-church-01 have NO gt-tum.txt** (not core sequences).
- **GT harvest (IN PROGRESS at session end):** `E:\githouse\Datasets\oxford_spires\gt\<seq>.txt` — valid so far: keble-02 (294 m/301 s, 15 revisit sites @3 m), keble-04 (783 m/681 s, 69 sites), christ-church-02 (642 m/561 s, 39 sites); the rest were mid-download when the session closed. **Resume with `bash scripts/download_spires.sh gt` (integrity-checked, resumable, retries; then `python scripts/select_spires_sequence.py` to rank all).** Watch out: hf-mirror serves these small non-LFS git blobs SLOWLY (~10–100 KB/s) and the host network flakes (HTTP 000 bursts) — the script retries; files failing the 8-field first/last-line check are auto-deleted. Truncated files from a killed run previously masqueraded as done (the 300 s tool cap killed pass 1 mid-file).
- **Code landed (RAP-SLAM `2075f5e`):** `rap_slam/spires_dataset.py` (binary-PCD xyz parser + TUM GT + nearest-timestamp matching, |dt|<0.05 s asserted; GT is rig-BASE frame vs our LiDAR frame — first-pose anchoring absorbs the small constant extrinsic, documented); `run_pipeline.py --source spires --spires-root/-seq/-start/-end`; `scripts/select_spires_sequence.py`; `scripts/download_spires.sh` (`gt` / `clouds <seq>`).
- **NEXT SESSION — P4 smoke:** (1) finish GT harvest; (2) pick sequence (leading candidate **keble-02**: 294 m, 15 sites, POSS-A-like scale; christ-church-02 as the bigger arm); (3) `bash scripts/download_spires.sh clouds 2024-03-12-keble-college-02` (~13 min); (4) zero-shot run with CANONICAL params, no retuning: `python scripts/run_pipeline.py --source spires --spires-seq 2024-03-12-keble-college-02 --output ./output_spires_keble02 --loop-sep 200` (KISS-ICP max_range 80 > QT64's 60 m — harmless; min_range 1.5 drops rig self-hits); (5) eval with eval_paper_metrics conventions + record aligned ATE / ter / loop stats for the cross-sensor table row. If KISS-ICP diverges on walking motion, that itself is the finding (front-end is the known ceiling — RC-5); consider `--deskew` only as a documented second arm (QT64 is rolling-shutter, walking rotation is fast).


#### Next-session startup checklist (2026-08-22, eleventh update)

1. `git log origin/main..HEAD --oneline` in both repos — should be empty; pull if the owner edited elsewhere.
2. **Paper-phase plan DECIDED 2026-08-22** (advisor feedback: horizontal comparison + innovation beyond assembly) — full plan + literature findings in the 2026-08-22 decision addendum. **P0 + P1 + P2 + P3 CLOSED** (P0: metrics + horizontal table; P1: verifier swap — gate transfers, RAP 2× edge accuracy + wider basin; P2: calibrated generative uncertainty — post-gate errors near-independent of mean_dist/overlap, dispersion the only signal axis, near-constant σ_t≈2.8 m; relfloor stays default; P3a: clique √k down-weighting = principled no-edge-dropped NMS alternative, degree mode preferred, NMS stays default; P3b: map-consistency axis — Chamfer vs GT map improves on 7/7 goldens tracking APE, crispness as GT-free monitor; P3c: N-way matrix + edge-cover trim — pairwise stays default, warp governed by geometric self-similarity not batch size, md re-gate cannot see low-frequency warp). **P4 probe DONE 2026-08-23: target = Oxford Spires (Hesai QT64 backpack, TLS GT) via hf-mirror (~3 MB/s, Range OK); Newer College infeasible (Google-gated). Loader + `--source spires` wired; GT harvest in progress at `E:\githouse\Datasets\oxford_spires\gt\`; smoke run NOT yet done — see the P4-probe addendum for the exact 5-step resume recipe.** Then P5 writing (`RAP-SLAM-report\paper\main.tex` outline exists).
3. Old next-work list re-prioritized: (d) rosbag recording — optional demo; (e) MCD/Livox generalization — folded into P4 as a download-feasibility-gated probe (Newer College preferred); (f) LIO — still deferred (deskew falsified for KITTI 2026-08-16; needs throttled raw-dataset IMU).
4. POSS segments A+B local (4170 frames, both smoke-validated). Further GT-revisit segments from the 2026-08-01 analysis: 0–1750, 16000–17250, 21750–22750, 25250–27250, 31000–35000 — download only if P4 wants more POSS coverage.
5. Cleanup items DONE 2026-08-16 (84.8 GB zip deleted; advisor_report/ + ppt/ → `RAP-SLAM-report\`). `paper/` stray RESOLVED 2026-08-22 (relocated to `RAP-SLAM-report\paper\`, rebuild verified); RAP-main tree 100% clean.

#### Dataset request sent to owner (2026-08-01)

- ~~**KITTI odometry seq 06 velodyne**~~ ✅ FULFILLED 2026-08-01 — owner delivered the FULL 22-sequence archive (see consolidation addendum above). Nice-to-haves 00/05 included.
- **POSS segment B: frames 6750–9500** (~2800 frames, est. ~2.8 GB, fast PKU server): `python scripts/download_poss_segment.py --start 6750 --end 9500 --threads 4`. Frame ranges chosen by GT revisit analysis of the full 36924-pose seq 00 (path 11.39 km; segments with a <5 m revisit approach ≥300 frames apart): 0–1750, 3250–5250 (current segment lives here), **6750–9500**, 16000–17250, 21750–22750, 25250–27250, **31000–35000** (largest; ~4 GB if a third segment is wanted).
- **Optional, needs a new loader (do only if multi-platform generalization becomes the goal):** Newer College Dataset (Ouster OS1-64 handheld, campus loops, GT provided) or MCD (Livox+spinning, multi-campus). Not required for RC-2…RC-4.

### Hard-won gotchas (do not relearn these)

1. **POSS poses are already in the LiDAR/world frame** (z-up horizontal trajectory). Do NOT apply the KITTI conversion — it rotates the trajectory upright and corrupts evaluation. Controlled by `real_dataset.load_gt_poses(apply_calib=...)`: **False for POSS, True for KITTI**. **KITTI conversion direction fixed 2026-07-22:** the correct formula is `T_velo = Tr⁻¹ @ T_cam @ Tr`; the code previously used `Tr @ T @ Tr⁻¹`, which leaves the GT in a ~90°-rotated world frame (KITTI 04 "odometry APE" was 310.7 m before the fix, 2.96 m after). This bug was latent because the KITTI path had never run without velodyne data.
2. **Loop-closure acceptance must not gate on odometry consistency.** Requiring RAP's transform to agree with the drifting odometry estimate is self-defeating (true loops under 13.3 m drift were rejected while RAP was 0.15–0.47 m from GT). Current logic (since `f59686f`): two-metric gate on RAP's intrinsic geometry — **overlap ≥ 0.7 AND mean_dist ≤ 2.5 m** — odometry consistency is logged as diagnostics only. And since 2026-08-01 the same diagnostics are consumed a second time in PGO information weighting (`relfloor` sigmas, RC-1).
3. **Network (China host):** AWS S3 (`avg-kitti`, etc.) is throttled to ~15 KB/s–0.5 MB/s; HuggingFace unreachable; `www.poss.pku.edu.cn` is fast (~4–5 MB/s). Download big files on the **Windows host** (`curl --ssl-no-revoke`, Git Bash), not in WSL. For partial extraction of huge remote zips use `remotezip` (vendored at `RAP-SLAM/scripts/_vendor`) — it is **not thread-safe**, use one instance per thread. KITTI seq 06 velodyne (~2.15 GB) via S3 remains un-downloaded.
4. **Git Bash path mangling:** passing `E:\githouse\...` as a CLI argument to `python` gets backslash-mangled; use forward slashes `E:/githouse/...`.
5. **WSL warning noise:** every `wsl` invocation prints a harmless `wsl: ... localhost ... NAT` warning line; filter with `grep -v '^wsl'` (use `grep -a`, output can look binary to grep) or ignore.
6. **Scan Context cosine distance is uninformative on structureless scenes** — uniform random clutter yields near-constant columns, so even unrelated scenes score ~0.1. Do not sanity-check SC on synthetic random clouds; judge separability on real scans (POSS: true 0.06–0.11 vs false ≥ 0.35). Rotation shows up as a column shift in the *opposite* direction (+60° yaw → shift 50 of 60 cols).
7. **RAP N-way registration scales non-gracefully in part count** — 5–7 parts: global layout near-perfect (0.15 m); 82 parts in one call: global warp (55 m layout rmse) while local relatives stay 0.2–0.5 m accurate. Global attention is O(total_points²) — 82 × 1500 pts = 123k points took 38.6 s for 5 Euler steps on the RTX 5070; do not attempt ~4000 pts × 82 (OOM/slow). Also: RAP sampling is stochastic even with a fixed seed (RNG is consumed across calls), so single-run APE numbers carry ±0.05 m noise.
8. **Comparing trajectories across frames:** POSS GT poses live in a world frame hundreds of meters from the odometry origin (KISS starts at identity). Always compare in the first-pose frame (`evaluate.align_to_first_pose`) — raw world-frame position diffs between anchored estimates and GT are meaningless.
9. **Interrupted zip extraction leaves `NNNNNN(1).bin` duplicate files** (Windows "file already exists" naming): seq 04 had `000001(1).bin` instead of `000001.bin`, which crashes `load_scans` (`int('000001(1)')`). After any extraction, sweep for `*( )*` files, verify content, and rename; then re-check frame-number contiguity per sequence.

### RAP-CORE roadmap (restructured 2026-08-01, supersedes the old numbered list)

**Core goal: SLAM with RAP as the core** — every stage either performed by RAP or shaped around its outputs. Staged plan, in priority order:

- **RC-1 ✅ DONE 2026-08-01 — Consume RAP's per-edge diagnostics in the backend.** RAP `overlap`/`mean_dist` now drive PGO information weighting: floor-relative adaptive sigmas (`relfloor`, scale = clip(mean_dist/1.0 m, 1, 3)) + Huber(k=1) robust kernel on loop edges in `rap_slam/pose_graph.py` (defaults; wired through `ros2/rap_server.py`, live `loop_closure_node.py` params `pgo_*`, offline `run_pipeline.py --loop-weighting/--robust-kernel`). Empirical basis: `scripts/eval_pgo_robust.py` on 182 KITTI-02 + 2 POSS saved edges — KITTI-02 APE 27.387 → **26.423 m**, POSS bit-identical **1.757 m**; robust kernels hold ~25 m under 50% edge corruption @5 m σ where fixed weighting explodes past 80 m. Diagnostics→error correlation is real but weak (mean_dist vs trans err r=+0.245; overlap r=−0.201) — enough for floor-relative loosening, not for tight absolute sigmas (absolute "adaptive" wins on KITTI at 25.688 m but regresses POSS 1.757→1.961 m; available via `--loop-weighting adaptive`).
- **RC-2 ✅ DONE 2026-08-01 — FALSIFIED: SC yaw-hint → RAP pre-rotation.** Offline re-score of 10 TRUE + 11 FALSE KITTI-02 pairs with/without pre-rotation (`scripts/eval_yaw_prehint.py`): hint accurate (med 0.8° vs GT yaw) but changes nothing (dT med 3.21→3.21 m, gate 10→10 / 0→0). Synthetic large-yaw arm (`eval_yaw_prehint_synth.py`, scan j rotated +90°/+180° with adjusted GT): vanilla RAP is yaw-invariant — identical dT/dR/overlap at 180°, robust even to a 91°-wrong hint. RAP is a genuinely global registration method; there is no yaw basin to widen. Hint stays log-only.
- **RC-3 ✅ DONE 2026-08-08 — Multi-generation confidence: value is GATE HARDENING, not PGO σ.** `scripts/eval_multigen_confidence.py` (195 pairs × 4 generations): **min overlap across k=4 generations cleanly separates TRUE (0.661–0.979) from FALSE (0.031–0.156) loops** — acceptance margin 0.06 → >0.5 — and exposes 90° bistable yaw flips on false loops; dispersion→error correlation too weak for σ-weighting (Spearman ρ=+0.165 vs mean_dist's +0.245); best-of-k helps KITTI-02 (−0.45 m) but regresses the POSS golden, so not default. Integrated as an OPTIONAL consistency gate (default OFF, k=1 = legacy, POSS golden bit-exact): `RAPBackend.register_consistent(points_a, points_b, k)` + offline `--multigen-k 3 [--min-overlap-min 0.4 --max-disp-r 30]` + live params `multigen_k`/`min_overlap_min`/`max_disp_r` via `rap_server.py` field `k`. Use k=3 on new/urban datasets or as borderline escalation near the 0.7 overlap threshold. Products: `output_multigen/`.
- **RC-4 ✅ DONE 2026-08-01 — EVALUATED, no gain: hierarchical N-way backend.** `scripts/eval_hier_nway.py` mines loop clusters (union-find over accepted edges; KITTI-02: 182 edges → 12 clusters, biggest 41/34 members = street chains ~104–109 m bbox), jointly registers each ≥3-member cluster with `register_multi` (degree-trim to 16 parts, 30k/64k point budgets), swaps each edge's `T_rel` for the cluster-consistent `inv(T_i)@T_j`, and re-runs PGO. Results (defaults relfloor+huber): KITTI-02 hier-PGO **26.80–26.93 m vs pairwise 26.423 m** (3 seeds, spread 0.126 m); POSS 1.763/1.808 vs 1.757 (2 seeds, spread 0.045 m — within noise). Per-edge intrinsics at equal 4000 pts/scan: N-way slightly better (med 2.33 vs 2.45 m, rot 0.5° vs 0.7°) but APE doesn't move — **KITTI-02's residual error lives in the long UNCONSTRAINED stretches (frames 0–900, 2000–3400, no revisits), which no loop-constraint engineering can fix**. Cluster layouts don't warp at ≤16 parts × ≤4000 pts (layout rmse 0.4–3.5 m; one 6.12 m instability at 64k pts total). Multi-seed variance quantified: ±0.05–0.13 m on final APE. Conclusion: keep pairwise edges; N-way adds nothing the robust weighting doesn't already capture at the data's constraint coverage. Products: `output_hier_nway*/summary_*.json`.
- **RC-5 ✅ DONE 2026-08-08 — FALSIFIED: sparse RAP odometry refinement.** `scripts/eval_sparse_odom_refine.py` (434 consecutive-keyframe pairs: 412 in KITTI-02 stretches 0–900/2000–3400 + 22 control): RAP between-edges are noisier than KISS-ICP between-edges at keyframe baselines (stretch med 0.105 m / 0.44° vs 0.072 m / 0.09°), and PGO degrades monotonically with replaced-edge count (stride 1/2/4 = 72.98 / 51.05 / 40.20 m vs 26.423 m baseline; control arm 26.84 m ≈ baseline). The independent-noise-for-correlated-drift trade fails on magnitude. Keep KISS-ICP between-edges untouched; the unconstrained-stretch residual is only addressable via front-end upgrade (deskew/LIO) or denser revisits. Products: `output_odom_refine/` (434 cached RAP edges reusable).
- **Standing/done items (kept for context):** 3. ~~Scan Context global retrieval~~ ✅ 2026-07-20 (+ streaming recall rework 2026-08-01, `b39d116`); SC threshold validation off-POSS ✅ 2026-08-08 (0.25 default held on KITTI 00/05/06, zero false accepts); remaining: MCD/Livox generalization. 4. ~~N-way first comparison~~ ✅ 2026-07-20 → superseded by RC-4. 5. Phase 2 ROS 2 ⏳ Step 0–3 done (2026-07-22); remaining: rosbag recording. **GUI demos all owner-confirmed** (Step-3 POSS 2026-07-31, KITTI-06 2026-08-09).
- **Post-RC directions (owner-approved 2026-08-09 — full detail in the 2026-08-09 decisions addendum + ninth-update checklist):** Direction A submap-level N-way SLAM = PRIMARY (paper-headline candidate) — **EVALUATED 2026-08-09, positive signal** (submap arms best on POSS/KITTI-00; hazard re-gate ov≥0.5/md≤2.0; chain-aware batch composition next); Direction B RAP-encoder-feature retrieval — **probe DONE 2026-08-09: DiT features FALSIFIED vs SC (AUC 0.76–0.82 vs 0.81); surprise winner miniSpinNet-32D mean-pooled (AUC 0.99, free RAP-preprocess byproduct)**; Direction C/D = paper sections / ablations; front-end deskew APPROVED, not started (LIO deferred pending IMU-data availability).

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

**Report-artifact dirs** (RAP-SLAM progress-report deliverables; NOT part of the RAP codebase): **RELOCATED 2026-08-16 (owner-approved) to `E:\githouse\RAP-SLAM-report\`** (`advisor_report/` + `ppt/`), out of this read-only repo. Contents:
- `advisor_report/` — Chinese progress-report PDF (`RAP-SLAM进展汇报_202607.pdf`) + `build_pdf.py` / `make_figures.py` + figure scripts (`fig01_*`…`fig15_*`) that plot from RAP-SLAM pipeline products.
- `ppt/` (2026-08-09) — the slide-deck source: `rap_slam_report/` holds a `.pptd` project manifest + 18 `.page` files + `media/` copies; `screenshots/pages/*.jpg` are the rendered 18 slides. Figure generators:
  - `ppt/gen_figures.py` + `gen_figures2.py` — matplotlib figures from real RAP-SLAM products (POSS `output_poss/`, KITTI-02 live `output_ros2/step3_kitti02/`, KITTI GT in `E:\githouse\Datasets\data_odometry_velodyne`). Hardcode `SLAM = Path(r"E:\githouse\RAP-SLAM")` and assert the exact APEs (POSS 8.257 / 1.821) — re-running doubles as a product-consistency check. Depend on `daimon_runtime` (external plotting-style helper in the running env's site-packages, NOT in this repo or RAP-SLAM).
  - `ppt/rap_flow_viz_gpu.py` — the only GPU part: runs in WSL with the `rap-inference` conda env, does one real RAP registration (POSS pair 3850↔5268, 20 Euler steps, 1500 pts/scan) via `RAPBackend` (read-only import from RAP-SLAM) and dumps the sampling trajectory to `ppt/media/flow_traj.npz` for offline plotting.

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
