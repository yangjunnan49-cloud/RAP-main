# DELIVERY —— 2026-09-21 组会材料交付说明

生成时间：2026-09-20（截止时间 2026-09-21 15:00 Asia/Shanghai 之前）。

## 1. 完成项清单

| # | 交付物 | 状态 |
|---|--------|------|
| 1 | `rap_slam_meeting.pptx` | ✅ 8 页可编辑 PPT，纯白背景，无封面/目录/致谢；每页备注栏含资产来源与实验配置；已用 PowerPoint 导出逐页预览（`preview_ppt/`）逐页目检 |
| 2 | `paper/` | ✅ 完整 LaTeX 工程：`paper.tex` + `references.bib` + `figures/`；WSL TeX Live xelatex 两遍编译 0 错误，产出 `paper.pdf`（9 页），已逐页渲染目检（`paper/preview/`） |
| 3 | `benchmark_table.md` | ✅ RAP-SLAM × 5 家对比模型 × KITTI 00/05/06 的 ter/rer/aligned ATE 总表；PPT 与论文数字均取自该表 |
| 4 | `assets/` | ✅ 全部图像资产，文件名带来源标注（`seqXX_ours_*` 为自渲染，`papers/pinslam_seq00_frompaper.png` 为论文截取） |
| 5 | `image_prompts.md` | ✅ P1 pipeline 核心图文生图 prompt（必需）+ P2 可选配图 prompt，均注明用途与页码 |
| 6 | `DELIVERY.md` | ✅ 本文件 |

辅助文件（非交付清单项，供复现/追溯）：`make_ppt.py`、`render_maps.py`、`make_innovation_fig.py`、`make_ablation_fig.py`、`meeting_metrics.json`。

## 2. 默认假设回显（任务书中所有【默认】项）

- **分支策略【默认】**：已执行。RAP-main 与 RAP-SLAM 两仓库均在开工前 `git checkout -b meeting_20260921`，main 分支全程零改动、零新 commit。开工前 `git status` 确认的预先存在脏文件（RAP-main 的 `.gitignore`/`AGENTS.md` 修改等；RAP-SLAM 的九个已跟踪文件修改与若干未跟踪脚本）原样保留，未纳入任何提交。
- **PPT 页序【默认】**：按任务 5.2 默认页序执行，未微调（P1 pipeline → P2 创新点总览 → P3 创新点详解：前后端特征统一 → P4 总体对比 → P5 逐序列重建网格 → P6 城市街区重建 → P7 补充实验 → P8 结论与展望）。
- **论文引擎与模板【默认】**：ctexart + xelatex，简洁单栏。本机（WSL Ubuntu-24.04 TeX Live）具备 xelatex 与中文字体，已出 PDF。
- **论文字数【默认】**：正文约 3000 汉字 → 实测约 2900 字（脚本口径：剔除摘要、图注、表格、参考文献后的中文字符计数）。
- **参考文献【默认】**：GB/T 7714 格式，共 17 条（≥15），覆盖第 4 节全部对比论文（LOAM、IMLS-SLAM、SuMa、SuMa++、MULLS、CT-ICP、KISS-ICP、KISS-SLAM、PIN-SLAM、Scan Context、Scan Context++、RPF、RAP、GTSAM、GNC-TLS、KITTI、miniSpinNet）。

## 3. 指标口径声明

RAP-SLAM 是**稀疏 LiDAR SLAM**（点云地图 + 位姿图），非 NeRF/3DGS 稠密重建系统，因此**不采用** PSNR/SSIM/LPIPS。采用口径：

1. **ter / rer**：KITTI 官方评测协议的 100–800 m 分段相对平移/旋转漂移（%，deg/100 m），由 `RAP-SLAM/scripts/eval_paper_metrics.py` 计算；
2. **aligned ATE**：SE(3) Umeyama 对齐后的 APE 平移 RMSE（m），evo 实现，与 PIN-SLAM 论文 Table IV 同口径。

## 4. 序列名单与选取理由

**KITTI odometry 00 / 05 / 06** 三条。理由：(i) 三条均含真回环，是回环系统的核心展示对象；(ii) 已有 KISS-SLAM 官方默认配置在同数据上的本机实测对照（2026-09-19 horizontal-comparison-01 归档），对比公平可复核；(iii) 三条覆盖了长序列多重访（00）、中等（05）、短程少回环（06）三种情形。

## 5. 对比论文名单与选取理由

| 论文 | 年份/出处 | 选取理由 |
|------|-----------|----------|
| PIN-SLAM | T-RO 2024 | 第一梯队 SOTA 锚点（aligned ATE 均值 0.50 m），数字逐字转录自其 Table III/IV |
| KISS-SLAM | IROS 2025 | 2025 年最新横向系统；且为本机同数据实测（官方默认配置，CPU-only），数据最可信 |
| CT-ICP | ICRA 2022 | 公认强基线，ter 均值 0.34% 位于第一梯队区间 |
| MULLS(-SLAM) | ICRA 2021 | 公认强基线，ter 均值 0.37% |
| SuMa / SuMa++ | RSS 2018 / IROS 2019 | 面元地图闭环代表，aligned ATE 文献行来源 |

说明：对比集复用仓库 2026-09-19 HC-V1 横向比较已逐字核验的名单。受本机外网不可达限制，未能补入更多 2025–2026 新作（如 HLBA 仅有 ter 均值 0.47% 单点数字、无逐序列数据，无法进入逐序列表格）；PIN-SLAM（2024）与 KISS-SLAM（2025）作为第一梯队与最新作锚点，经典强基线补齐梯队区间。此限制亦列入"已知缺陷"。

## 6. 指标改动说明（任务第 3 节）

两处改动，全部位于 RAP-SLAM 仓库 `meeting_20260921` 分支，代码中以 `# [meeting-20260921]` 注释标注，集中于两个文件：

1. `scripts/run_pipeline.py`：KITTI HDL-64 内参 **0.205° 垂直角校正默认开启**（`--apply-kitti-205` 默认 True，新增 `--no-apply-kitti-205` 关闭开关；非 KITTI 数据自动禁用而非报错）；前端参数新增/改默认：`--odom-max-range` 80→**100 m**、新增 `--odom-min-range` **0.0 m**（原硬编码 1.5）、新增 `--odom-voxel` **1.0 m**（原 0.8），对齐 KISS 官方 KITTI 配置。
2. `rap_slam/odometry.py`：`run_odometry` 增加 `min_range`/`voxel_size` 透传接线（约 16 行）。

动机：消除与对比文献之间的**数据处理约定不一致**（0.205° 校正是 CT-ICP/MULLS/Traj-LO/KISS 的共同 KITTI 惯例，属传感器固有标定修正；100/0.0/1.0 是 KISS 官方 KITTI 配置），使横向对比公平。算法本身（检索、验证、后端 PGO）未做任何精度导向修改。

影响（完整系统，00/05/06 均值）：ter 0.76% → **0.41%**（00: 0.914→0.557，05: 0.704→0.331，06: 0.667→0.333）；aligned ATE 均值 1.63 m → **1.12 m**（00: 2.8915→1.8141，05: 1.1293→1.2183，06: 0.8690→0.3318）。回环 36/36 全部命中真回环。论文 4.1 节以中性学术措辞如实披露上述改动；PPT 全文（含备注栏）不出现分支/改动操作信息。

复现：WSL `rap-inference` 环境下 `python scripts/run_pipeline.py --real-seq kitti00 ... `（默认参数即新配置），产物在 `RAP-SLAM/output_meeting/kitti{00,05,06}_armB/`，评测 `python scripts/eval_meeting_arms.py`。

## 7. 如何回退（恢复 main）

```bash
cd E:\githouse\RAP-main
git checkout main          # 恢复 RAP-main；交付目录为未跟踪文件，切分支不受影响，需彻底删除可手动移除 docs/meeting_20260921/

cd E:\githouse\RAP-SLAM
git checkout main          # 恢复 RAP-SLAM；会议改动未 commit，切换前如需保留可先 git stash 或 git diff 备份
```

两仓库 main 分支全程零改动。说明：RAP-SLAM 的会议改动**未 commit**——因为工作区中 `run_pipeline.py`/`odometry.py` 等文件混有历史遗留的未提交改动（manifest 导出、`--allow-odom-fallback` 等），按 AGENTS.md"保留原有脏工作"纪律不做混合提交；会议改动可用 `git diff` 按 `# [meeting-20260921]` 注释完整追溯。

## 8. 已知缺陷

1. **P1 pipeline 图为占位框**：按任务要求只交 prompt（`image_prompts.md` P1），待 chatgpt-image-2 生成后替换 PPT 第 1 页与论文图 1 的占位框。
2. **P5 网格多处留空**：KISS-SLAM/CT-ICP/MULLS 的逐序列重建图因本机外网不可达（arXiv/出版社站点 SSL/连接被拒）无法从原论文截取，按任务规则留空"—"不臆造；PIN-SLAM 仅 KITTI-00 一格（截自本地存档 PDF Fig.5(b)）。
3. **aligned ATE 仍有差距**：均值 1.12 m 对比 PIN-SLAM 0.50 m / KISS-SLAM 实测 0.64 m，差距集中于 00 长序列无重访长段；论文中已如实说明，PPT 第 4 页亦保留了该结论。
4. **对比论文年份结构**：见第 5 节说明，受网络限制未能纳入更多 2025–2026 新作。
5. **正文字数为脚本估算口径**（约 2900 字），不同统计口径会有小幅出入。
6. PPT 页字数（含标题）区间 78–280 中文字符，P5 因以网格图为绝对主体，正文接近下限（约 100 字）。
