# October31 renewed continuation COMPLETE: PTA1/GCP2/GCG1

Explicit owner renewal targets closeout with1-5% current5h quota remaining; actual final receipt is independent at C:/Users/AAA/Documents/Codex/2026-10-31/agetns-md/outputs/continuation_close_20261031/ACCOUNT_STATUS.json. Read CONTEXT_CN.md and NEXT_STEPS_CN.md there. PTA1 all200/273raw/8612time rows source/index chain PASS, physical timing/upstream-deskew/per-pair reference error bounds UNVERIFIED. GCP2 full200/17140clique fits/148native outputs, Horn17140 and16947579scalar projections PASS; F pool61->F+graph69, expandedR/L96, R/L stillunique27(00/08=21/6), nativecorrect59 belowcachedL82. Existing NetworkX3.4.2 API controls84graphs first; independent ordinary kernel, NOT officialMAC or equal-wall comparison/PGC1 completion. GCG1 same old gate correctaccepted37/wrong8 vsF/J37/9, no correct gains/losses/newwrong; removedwrong only00_80_1532; >=5correctgain screenFAIL. Full1184000NN and592scalar queries PASS. MCV1 count+rank insufficiency retained. PGC1 original64action/eighth-pair stop and7partial accuracy unread, officialMAC unrun/missingigraph, all old failures/caps/source limits andE0 engineering positive retained. Nine unique Linux numeric workers+nine external watchers exited;18original identities absent; WSLUbuntu24 restoredinitialStopped. Coldcodec failure and zeroexit-wrapper metadata discrepancy separately retained; no successful numerical stage rerun. NoGPU/install/training/production/default/Git-history change, outreach or queued/reset continuation. Next: independently justified identity evidence covering targets and coherent aliases; no new confidence head/threshold sweep. ResearchUNRESOLVED/manuscriptPAUSED. Phase E:/githouse/RAP-main/docs/maintenance/2026-10-31/continuation-source-graph-01/PHASE_RECORD.md. Preceding AGENTS bytes backed up and preserved verbatim below; current verifier supersedes old mutable-current hash checks while old seals remain historical.

---

# October31 afternoon MCV1 COMPLETE; research unresolved

New explicit owner instruction authorizes this finite current-window continuation and closeout. Canonical current context: C:/Users/AAA/Documents/Codex/2026-10-31/agetns-md/outputs/measurement_contract_20261031/CONTEXT_CN.md; full report REPORT_CN.md; contract MEASUREMENT_CONTRACT_V1.md; next recommendations NEXT_STEPS_CN.md. MCV1 all200/1813 candidates/273 exact supports and13 synthetic mechanisms complete. Independent scalar audit1264773 projections/40212 H entries PASS. PCS1 A's70 correct and65 incorrect usable positive outputs, plus20 usable nonloops, ALL have full conditional point-to-point rank: count+rank is not an identity/safety certificate and adds no discrimination on these outputs. Local H is not calibrated covariance/information for PGO. No new accept rule, safe-system gain, training, feature extraction or pose solver. Inputs/math/old rankings unchanged. One preadmission path error and one pre-array zipfile cold import failure retained; import-only integration02 retains original06:55UTC/5400s clock and successful control bytes. Six unique Windows children exited/reaped, including failure; failure peak only host-polled. Original12GiB/2s external nonce/RSS/wall receipts retained. No WSL/GPU/install/production/default/Git-history change. Current Git heads4055d92/6d3f2d2 on codex/meeting-20260930 and codex/e0-f1-20260926, existing dirty worktrees preserved. PGC1 remains INCOMPLETE_STOPPED64actions/eighth pair,7partial accuracy unread; officialMAC not run; all old failures/caps/source limits and E0 engineering positive preserved. Next proposed source/time/calibration/reference applicability audit needs NEW evidence beyond already checked CR1 matrix arithmetic, then independently justified identity evidence; no automatic next numerical study or quota/reset continuation. Actual account receipt in ACCOUNT_STATUS.json, no exhaustion inferred. Research UNRESOLVED/manuscript PAUSED. Phase record: E:/githouse/RAP-main/docs/maintenance/2026-10-31/measurement-contract-01/PHASE_RECORD.md. Exact previous AGENTS bytes backed up under canonical authority_before and preserved verbatim below.

---

# AGENTS.md — RAP Workspace

> AI-agent notes for the workspace at `E:/githouse` (WSL path: `/mnt/e/githouse`). This file is intended for automated agents that need to understand, modify, or run code here. The workspace contains two sibling projects: **RAP-main** (the upstream RAP registration model) and **RAP-SLAM** (an offline SLAM pipeline built on top of RAP). All Python code, docstrings, and comments are written in English; the RAP-SLAM README is written in Chinese for local collaborators.

---

## Project Overview

This workspace is a research development environment around **RAP (Register Any Point)**, a 3D point-cloud registration method that formulates registration as conditional flow matching. The workspace is organized as two separate directories that are managed independently:

| Directory | Role | Status |
|-----------|------|--------|
| `RAP-main/` | Upstream RAP repository: inference code, model weights, Hydra configs, preprocessing scripts, and a Gradio demo. | Used **read-only** by RAP-SLAM. Direct changes are discouraged unless a patch is required. |
| `RAP-SLAM/` | Offline SLAM pipeline that uses RAP as a pairwise registration engine inside a loop-closure + PGO architecture. | Active development project. |

**RAP-SLAM pipeline summary:**

```text
sensor data → [sequence] simulate or load KITTI-format scans
            → [odometry] KISS-ICP (Open3D ICP fallback)
            → [keyframes] displacement-based selection
            → [loop closure] proximity candidates + RAP geometric verification
            → [pose graph] GTSAM PGO
            → [evaluate] evo APE/RPE, trajectory plot, merged map
```

Key validated results (from `RAP-SLAM/output_poss/summary.json`):

- **POSS real sequence** (frames 3850–5268, 1419 scans, Velodyne-32e): odometry APE RMSE 8.26 m → GTSAM PGO 1.82 m (78% reduction). RAP loop-verification accuracy against GT: 0.15–0.47 m / 0.0°.
- **KITTI-00 simulated sequence** (101 scans): odometry APE RMSE 5.53 m → PGO 3.67 m (33.7% reduction).

**Papers / upstream links:**

- RAP paper: *Register Any Point: Scaling 3D Point Cloud Registration by Flow Matching* (arXiv:2512.01850)
- Upstream repo: `https://github.com/PRBonn/RAP`
- RAP license: MIT (see `RAP-main/LICENSE`)

---

## Workspace Layout

```text
E:/githouse/
├── AGENTS.md               # This file (workspace-level guidance)
├── RAP-main/               # Upstream RAP (read-only for RAP-SLAM)
│   ├── AGENTS.md           # Detailed RAP-main-specific notes (read this first for RAP internals)
│   ├── README.md
│   ├── app.py              # Gradio demo
│   ├── demo.py             # Folder-based preprocessing + inference
│   ├── sample.py           # Batch/CLI inference (Hydra)
│   ├── test_smoke.py       # Dependency-free model smoke test
│   ├── config/             # Hydra YAML configs
│   ├── rectified_point_flow/   # Core library
│   ├── dataset_process/    # Training-sample preprocessing
│   ├── scripts/            # install.sh, download_weights_and_demo_data.sh, test_script_example.sh
│   ├── weights/            # Pre-trained checkpoints (gitignored)
│   ├── demo_example_data/  # Demo datasets (gitignored)
│   └── demo_output/        # Local inference outputs
└── RAP-SLAM/               # SLAM pipeline (active development)
    ├── README.md           # Chinese-language project readme
    ├── requirements.txt    # kiss-icp / gtsam / evo
    ├── rap_slam/           # Python modules
    ├── scripts/            # Entry points and dev scripts
    ├── data/               # KITTI/POSS datasets (not in repo)
    ├── output/             # Simulated-sequence results
    └── output_poss/        # Real-sequence results
```

There is **no** root-level `pyproject.toml`, `setup.py`, `package.json`, or `Cargo.toml`. Both subprojects are run as scripts from their respective directories, not as installable packages.

---

## Technology Stack

### RAP-main (upstream registration model)

- **Language:** Python 3.10
- **Primary frameworks:**
  - PyTorch 2.5.1 (CUDA 12.4) — original upstream target
  - PyTorch 2.7.0 (CUDA 12.8) — required for NVIDIA Blackwell / RTX 50-series (validated on RTX 5070)
  - Lightning 2.5.2 (`L.LightningModule`, `L.Trainer`)
  - Hydra 1.3.2 — YAML configuration composition
- **Key libraries:** torchmetrics 1.6.3, pytorch3d 0.7.8/0.7.9 (source build on Blackwell), trimesh 4.6.4, diffusers 0.33.0, open3d, h5py, laspy, mitsuba 3.6.4, gradio ≥6.0.0, wandb 0.20.1, rich 14.0.0, matplotlib
- **Geometric libs:** torch-scatter, torch-sparse, torch-cluster, torch-spline-conv (PyG)
- **Optimizer:** Muon (installed from `git+https://github.com/KellerJordan/Muon`)
- **Attention backend:** The repo has been patched to replace the upstream `flash-attn` dependency with a PyTorch-native `scaled_dot_product_attention` helper (`rectified_point_flow/flow_model/layer.py`). This is required for Blackwell/RTX 50-series and is already applied.

### RAP-SLAM (downstream SLAM pipeline)

- **Language:** Python 3.10 (runs inside the `rap-inference` conda environment created for RAP-main)
- **Core dependencies:**
  - `kiss-icp==1.3.0` — frame-to-frame LiDAR odometry
  - `gtsam==4.2` — pose-graph optimization
  - `evo==1.36.5` — trajectory evaluation (APE/RPE)
  - `open3d 0.19.0`, `numpy`, `scipy`, `matplotlib` — already present in the RAP environment
- **RAP integration:** RAP-SLAM imports `RAP-main` at runtime via `sys.path.insert(0, rap_root)` and uses `RAP-main/demo.py` / `sample.py` style preprocessing plus `RectifiedPointFlow.sample_rectified_flow()`. See `rap_slam/rap_backend.py`.

---

## Build and Run Commands

All commands assume a WSL2 Ubuntu environment with the `rap-inference` conda environment activated, as documented in `RAP-main/AGENTS.md` and validated on an RTX 5070.

### 1. Environment setup (WSL2 + Blackwell / RTX 50-series)

```bash
wsl -d Ubuntu-24.04
source /root/miniconda3/bin/activate rap-inference
cd /mnt/e/githouse
```

The RAP environment is built by following the *Deployment on Windows + WSL2 + NVIDIA Blackwell* section of `RAP-main/AGENTS.md`. In short:

```bash
conda create -n rap-inference python=3.10 -y
conda activate rap-inference
pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu128
pip install torch-geometric
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.7.0+cu128.html
pip install diffusers==0.33.0 lightning==2.5.2 torchmetrics==1.6.3 trimesh==4.6.4 ninja
pip install -r /mnt/e/githouse/RAP-main/requirements_other.txt
# Build pytorch3d from source for PT 2.7 + CUDA 12.8:
bash /mnt/e/githouse/RAP-main/build_p3d.sh
# RAP-SLAM extra deps:
pip install -r /mnt/e/githouse/RAP-SLAM/requirements.txt
```

> **Note:** Upstream `RAP-main/scripts/install.sh` targets PyTorch 2.5.1 + CUDA 12.4, which does **not** support Blackwell. The commands above are the validated path for RTX 50-series GPUs.

### 2. Download RAP weights and demo data

```bash
cd /mnt/e/githouse/RAP-main
bash ./scripts/download_weights_and_demo_data.sh
```

This creates `./weights/` and `./demo_example_data/` under `RAP-main/`. If the download is unstable, download `weights.zip` on the Windows host and copy it into WSL.

### 3. Run RAP inference (upstream)

```bash
cd /mnt/e/githouse/RAP-main
python sample.py --config-name RAP_inference \
  model=rap_12 \
  data.force_use_ply=true \
  data.data_root=./demo_example_data \
  ckpt_path=./weights/rap_model_12.ckpt \
  visualizer.renderer=none
```

> **Important:** `sample.py` declares `config_name="RAP_base"` as its default, but `config/RAP_base.yaml` does **not** exist. You must always pass `--config-name RAP_inference`.

Other RAP entry points:

```bash
python demo.py --input ./demo_example_data/object_stanford_bunny \
  --output ./demo_output \
  --flow_model_checkpoint ./weights/rap_model_12.ckpt \
  --config RAP_inference --model rap_12

python app.py               # Gradio demo on port 7860
python test_smoke.py        # No checkpoint needed
```

See `RAP-main/AGENTS.md` for the full command reference and Blackwell-specific troubleshooting.

### 4. Run RAP-SLAM pipeline

**Simulated KITTI-00 sequence (smoke test):**

```bash
cd /mnt/e/githouse/RAP-SLAM
python scripts/run_pipeline.py --output ./output
```

**Real POSS sequence (requires data download first):**

```bash
cd /mnt/e/githouse/RAP-SLAM
# Download the velodyne segment (~1.4 GB) via HTTP range requests
python scripts/download_poss_segment.py --start 3850 --end 5268 --threads 4
# Download poses + calibration separately if not present
#   http://www.poss.pku.edu.cn/OpenDataResource/poss_odomotry/data_odometry_poses.zip
#   http://www.poss.pku.edu.cn/OpenDataResource/poss_odomotry/data_odometry_calib.zip
python scripts/run_pipeline.py --source real --output ./output_poss --loop-sep 200
```

Useful flags:

```text
--force-regenerate          # regenerate the simulated sequence and rerun the full pipeline
--skip-loop-closure         # run odometry + evaluation baseline only
--rap-steps N               # RAP sampling steps (default 5)
--rap-voxel V               # voxel size for RAP preprocessing (default 0.4 m)
--rap-max-points N          # point cap per scan for RAP (default 4000)
--no-rap-features           # skip miniSpinNet feature extraction
--loop-dist D               # proximity candidate distance (default 15 m)
--loop-sep N                # min scan separation for loop candidates
--max-candidates N          # cap loop candidates
--source real               # run on a KITTI-format real dataset segment
--real-apply-calib          # apply Tr velo↔cam conversion (KITTI convention; leave off for POSS)
```

Pipeline outputs (per run under `--output`):

```text
output/
├── gt_poses.txt
├── odom_poses.txt
├── optimized_poses.txt
├── trajectory_plot.png
├── merged_map_odometry.ply
├── merged_map_optimized.ply
├── sequence/
│   ├── meta.json
│   ├── gt_poses.txt
│   └── scans/scan_*.ply
└── summary.json
```

### 5. Test the RAP backend in isolation

```bash
cd /mnt/e/githouse/RAP-SLAM
python scripts/test_rap_backend.py
```

This instantiates `RAPBackend` and registers known pairs from a simulated sequence, printing translation/rotation error vs. ground truth.

---

## Code Organization and Module Divisions

### RAP-main

See `RAP-main/AGENTS.md` for the exhaustive module table. The core library lives in `RAP-main/rectified_point_flow/`:

| File/Dir | Responsibility |
|----------|----------------|
| `modeling.py` | `RectifiedPointFlow` LightningModule |
| `sampler.py` | Flow integration (Euler / RK2 / RK4) |
| `procrustes.py` | Rigid transform fitting and rigidity forcing |
| `flow_model/` | `PointCloudDiT` transformer, attention layers, embeddings, norms |
| `data/` | `PointCloudDataset`, `PointCloudDataModule`, transforms |
| `eval/` | Evaluator and metrics (lazy pytorch3d imports) |
| `utils/` | Checkpoint loading, logging, optimizers, rendering |
| `dataset_process/` | miniSpinNet feature extraction and training-sample preprocessing |
| `config/` | Hydra YAML configuration |

### RAP-SLAM

```text
RAP-SLAM/
├── rap_slam/
│   ├── __init__.py           # version 0.1.0
│   ├── sequence.py           # simulate scans from an aggregated map; KITTI pose I/O
│   ├── real_dataset.py       # load KITTI-format real sequences (KITTI/POSS)
│   ├── odometry.py           # KISS-ICP wrapper + Open3D ICP fallback
│   ├── keyframes.py          # displacement-based keyframe selection
│   ├── rap_backend.py        # in-process RAP pairwise registration wrapper
│   ├── loop_closure.py       # proximity candidate detection + RAP verification
│   ├── pose_graph.py         # GTSAM pose-graph optimization
│   └── evaluate.py           # evo APE/RPE, trajectory plot, map merging
├── scripts/
│   ├── run_pipeline.py       # main entry point (6-stage pipeline)
│   ├── download_poss_segment.py  # POSS data downloader (HTTP range requests)
│   ├── test_rap_backend.py   # RAP backend unit test
│   └── _*.py / sweep_*.py    # ad-hoc development/debug scripts (not official)
└── scripts/_vendor/          # vendored libraries for the downloader (remotezip, requests, urllib3, idna, charset_normalizer, certifi)
```

---

## Development Conventions

### Code style

- **Python 3.10+** syntax; union types written as `X \| Y`.
- **Type hints** are encouraged but not exhaustive.
- **Docstrings** follow Google/Numpy style with argument shapes.
- **Logging:** use `logger = logging.getLogger(__name__)`.
- **Paths:** scripts often use absolute WSL paths (`/mnt/e/githouse/...`) because the pipeline is cross-platform between Windows and WSL. Prefer `pathlib.Path` for new path handling, but `os.path` is widely used.
- **GPU timing:** synchronize with `torch.cuda.synchronize()` when CUDA is available.
- **RAP internal naming:** `x_0` = registered cloud, `x_1` = noise, `x_t` = intermediate, `v_t` = velocity, `cond` = condition.
- **TF32/cuDNN:** `sample.py` and `rap_backend.py` set `torch.backends.cuda.matmul.allow_tf32 = True` and `torch.backends.cudnn.allow_tf32 = True`; preserve this for consistency.
- **Attention code:** do **not** reintroduce `import flash_attn`. The repo uses the PyTorch-native `_flash_attn_varlen` helper in `rectified_point_flow/flow_model/layer.py`.
- **Lazy imports:** keep heavy/optional dependencies (pytorch3d in `eval/metrics.py` and `utils/render.py`) lazily imported, following the existing pattern.

### RAP-SLAM ↔ RAP-main coupling

- RAP-SLAM imports `RAP-main` **read-only** via `sys.path.insert(0, rap_root)` and `sys.path.insert(0, os.path.join(rap_root, "dataset_process"))`.
- The default `rap_root` in `rap_backend.py` is `/mnt/e/githouse/RAP-main`.
- RAP-SLAM replicates RAP preprocessing exactly: voxel downsampling → statistical outlier removal → point cap → miniSpinNet 32-D features → `PointCloudDataset._transform()` normalization.
- `RAPBackend.register(points_a, points_b)` returns `T_rel = T_a^{-1} @ T_b`, the pose of scan `b` expressed in scan `a`’s frame. This matches the GTSAM `BetweenFactor` convention.

### Configuration

- **RAP-main:** Hydra-based. The only root config that ships is `config/RAP_inference.yaml`. Always use `--config-name RAP_inference`. Model sizes: `model=rap_8`, `rap_10`, `rap_12`, `rap_16`.
- **RAP-SLAM:** No Hydra/config files; behavior is controlled entirely via `argparse` in `run_pipeline.py`.

---

## Testing Instructions

There is **no formal unit-test suite** (no `pytest`, no CI/GitHub Actions) in either subproject. Validation is done by running the entry points and inspecting the outputs.

### Recommended RAP-main workflow

1. `python test_smoke.py` — fast, no checkpoint needed; tests `PointCloudDiT` and the SDPA attention helper.
2. `python sample.py --config-name RAP_inference model=rap_10 data.force_use_ply=true data.data_root=./demo_example_data ckpt_path=./weights/rap_model_10.ckpt visualizer.renderer=none` — end-to-end smoke test.
3. Check that metrics print in a Rich table and that outputs appear under `<log_dir>/results` and `<log_dir>/visualizations`.

See `RAP-main/AGENTS.md` for the full RAP testing notes.

### Recommended RAP-SLAM workflow

1. `python scripts/test_rap_backend.py` — validates RAP registration on a small simulated sequence with known GT.
2. `python scripts/run_pipeline.py --output ./output` — simulated KITTI-00 smoke test (≈ 10 s on RTX 5070).
3. `python scripts/run_pipeline.py --source real --output ./output_poss --loop-sep 200` — real POSS sequence (requires downloaded data, ≈ 68 s on RTX 5070).
4. Inspect `summary.json` for `odometry` vs `optimized` APE/RPE metrics and accepted loop closures.
5. When changing `loop_closure.py`, `rap_backend.py`, or `pose_graph.py`, verify both the simulated and real sequences (if data is available).

### Golden output files (can be used for regression checks)

- `RAP-SLAM/output/summary.json` — simulated KITTI-00 run with 2 accepted loops and APE RMSE 5.53 → 3.67 m.
- `RAP-SLAM/output_poss/summary.json` — real POSS run with 4 accepted loops and APE RMSE 8.26 → 1.82 m.

---

## Security Considerations

- **Checkpoint loading:** `RAP-main` uses `torch.load(..., weights_only=False)` for checkpoint loading. Only load checkpoints from trusted sources (PRBonn official weights or the HuggingFace `YuePanEdward/RAP` model).
- **Downloads:** `RAP-main/scripts/install.sh`, `download_weights_and_demo_data.sh`, and `RAP-SLAM/scripts/download_poss_segment.py` download executable code, wheels, and data from PyTorch, pyg.org, Facebook (pytorch3d), GitHub releases, Bonn University, and Peking University. Verify the environment if running in a sensitive context.
- **Gradio demo:** `RAP-main/app.py` accepts arbitrary uploaded files and binds to `0.0.0.0:7860` by default; it may create a public share link unless `SHARE_URL=permanent` is set. Do not expose it publicly without sandboxing.
- **Vendored libraries:** `RAP-SLAM/scripts/_vendor/` contains vendored copies of `requests`, `urllib3`, `idna`, `charset_normalizer`, `certifi`, and `remotezip`. These are used by the POSS downloader to avoid external dependency issues. Keep them isolated; do not import them from production code outside the downloader.
- **No secrets:** no API keys, credentials, or W&B tokens are stored in the repository. W&B logging requires the user to run `wandb login` outside the repo.
- **Working-directory isolation:** both projects run from their own roots. Avoid writing files outside `RAP-main/` and `RAP-SLAM/` unless the pipeline explicitly requires it.

---

## Common Tasks for Agents

### Add a new RAP-SLAM evaluation metric

1. Implement the metric in `RAP-SLAM/rap_slam/evaluate.py`.
2. Wire it into `compute_ape_rpe()` or add a new helper called from `run_pipeline.py`.
3. Add the metric to `summary.json` in `run_pipeline.py`.

### Change the RAP model used by RAP-SLAM

1. Edit `RAPBackend` defaults in `RAP-SLAM/rap_slam/rap_backend.py` (e.g., `ckpt_path`, `sampling_steps`, `voxel_size`, `max_points_per_scan`).
2. Ensure the corresponding checkpoint exists under `RAP-main/weights/`.
3. Run `python scripts/test_rap_backend.py` to verify registration quality.

### Add a new real dataset to RAP-SLAM

1. Create a KITTI-format directory: `RAP-SLAM/data/<name>/dataset/poses/<seq>.txt` and `RAP-SLAM/data/<name>/dataset/sequences/<seq>/{calib.txt,velodyne/}`.
2. Determine whether poses are in the LiDAR/world frame (`--real-apply-calib` off, like POSS) or camera frame (`--real-apply-calib` on, like KITTI).
3. Call `run_pipeline.py --source real --real-root ./data/<name> ...`.

### Update RAP-main

- RAP-main is treated as upstream. If you must patch it (e.g., a new attention backend fix), keep the change minimal and document it in both `RAP-main/AGENTS.md` and this file. Prefer subclassing or wrapping in RAP-SLAM instead.

---

## Notes and Caveats

- `RAP-main` is **not** a pip-installable package. Scripts rely on running from the repo root and using `sys.path` to resolve imports like `rectified_point_flow.*`.
- `RAP-SLAM` is also not a package; it is run as scripts from `RAP-SLAM/`.
- The `RAP-SLAM` README is written in Chinese; all code and this workspace-level AGENTS file are in English.
- RAP-SLAM’s current loop-closure detection is proximity-based. If odometry drift exceeds the search radius, candidates will be missed. A future improvement is Scan Context global retrieval.
- KISS-ICP is run with `deskew=false` because the current POSS `.bin` files do not provide point-level timestamps.
- The RAP N-way joint global registration backend is **not** yet integrated into RAP-SLAM; only pairwise RAP registration is used for loop-closure verification.
- `RAP-SLAM` has no `.gitignore` of its own; generated outputs in `output/` and `output_poss/` are currently tracked as local artifacts. If you add persistent generated data, consider creating a `.gitignore`.
- There is no root-level git repository; `RAP-main` appears to be its own git checkout. Coordinate version control carefully when changing files in both directories.
