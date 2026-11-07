# 文生图占位 prompt 清单（image_prompts.md）

> 用途：凡 PPT 中判断"真实制作代价过大"或按任务规定只交 prompt 的图，在此给出文生图 prompt（供 chatgpt-image-2 生成）。每条注明用途与对应 PPT 页码。生成后替换 PPT 中同名占位框即可。

## P1 —— PPT 第 1 页：整体方法 pipeline 核心图（任务规定只交 prompt）

**用途**：RAP-SLAM 系统全流程示意图，PPT 第 1 页主视觉。

**Prompt（英文，供 chatgpt-image-2）**：

```
A clean, minimalist academic system-pipeline diagram for a LiDAR SLAM paper,
flat vector style, pure white background, thin dark-gray lines, no gradients,
no shadows, wide 16:9 composition. Left to right flow of five stages connected
by thin arrows:
(1) an icon of a spinning LiDAR sensor emitting a sparse 3D point cloud of a
    city street with small houses and trees drawn as dots;
(2) "front-end odometry" shown as a chain of small coordinate-frame triads
    following a dotted trajectory;
(3) "place recognition" shown as a circular radar-like polar grid descriptor
    (scan context) with two matching highlighted sectors;
(4) "generative registration verification" shown as two overlapping point
    clouds (one blue, one orange) snapping into alignment, with three faint
    ghost hypotheses converging into one solid alignment;
(5) "pose-graph optimization" shown as a small graph of nodes and edges
    relaxing into a smooth loop-closed trajectory.
Below the five stages, one long rounded rectangle labeled as a shared feature
backbone feeding upward into stages 2, 3 and 4 with three thin vertical
arrows, indicating a unified point-cloud feature representation shared by
front end and back end.
Small sans-serif labels under each stage, English text, subtle blue and orange
accent colors only, IEEE-paper figure aesthetic, high resolution.
```

**备注**：图中的"共享特征骨干"视觉元素对应创新点 1（前后端特征统一），与第 3 页呼应。生成图放入 `assets/pipeline_generated.png` 后替换第 1 页占位框。

## P2 —— PPT 第 4 页（可选）：对比方法 logo 行

**用途**：若需要，在实验对比页角落放对比方法小图标行。非必需，可跳过。

```
A horizontal row of five minimal flat icon badges on pure white background,
thin outline style, representing five LiDAR SLAM systems as abstract
geometric marks: a hexagon, a triangle mesh, a compass ring, a waveform, and
a point-cloud cube; dark gray strokes, one small blue accent each, no text,
IEEE-paper aesthetic, 5:1 wide composition.
```

## 说明

- 第 3 页创新点图、第 5 页重建对比网格、第 6 页城市街区重建图、第 7 页消融图均为**真实实验数据渲染/截取**，无需文生图。
- 第 5 页网格中 KISS-SLAM / CT-ICP / MULLS 的重建图因本机网络无法获取原论文 PDF 而留空（任务允许"原论文没有的留空"）；PIN-SLAM 的 KITTI-00 图已从本地存档的 T-RO v2 PDF 截取（`assets/papers/pinslam_seq00_frompaper.png`）。
