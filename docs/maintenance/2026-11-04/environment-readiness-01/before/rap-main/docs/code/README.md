# 代码职责与有效入口

更新：2026-11-04，Asia/Shanghai。A3 只整理入口、路径和职责，算法、历史协议与研究停止边界仍由[核心上下文](../../AGENTS.md)和[当前状态](../CURRENT_STATE.md)约束。

## 默认运行链

[scripts/run.py](../../scripts/run.py) 是统一启动器，默认输出 JSON 命令计划，不导入模型。五项任务及参数见[运行说明](RUNNING.md)。它不会扫描或自动分派历史实验脚本。

| 任务 | 实际入口 | 职责 |
| --- | --- | --- |
| sample | [sample.py](../../sample.py) | 对已准备的样本执行 Lightning test 推理；有效配置 RAP_inference |
| demo | [demo.py](../../demo.py) | PLY 文件夹 → 下采样/特征 → 推理；原参数保留 |
| features | [extract_sample_features.py](../../dataset_process/extract_sample_features.py) | 已有样本的 miniSpinNet 特征与格式处理；不等同完整数据集构建或训练就绪 |
| slam | [run_pipeline.py](../../../RAP-SLAM/scripts/run_pipeline.py) | 离线数据 → 里程计 → 关键帧/回环 → 位姿图 → 输出 |
| evaluate | [eval_external_trajectory.py](../../../RAP-SLAM/scripts/eval_external_trajectory.py) | 显式外部 KITTI 轨迹与参考的原有评测合同，限 00/05/06；没有泛化成任意数据集评测器 |

## 模块边界

| 模块 | 职责与保留的接口 |
| --- | --- |
| [rap_runtime](../../rap_runtime) | 仅 Python 标准库：根目录、权重、输出、缓存配置及子进程命令；不依赖模型包，不设置数值策略 |
| [rectified_point_flow/modeling.py](../../rectified_point_flow/modeling.py)、[sampler.py](../../rectified_point_flow/sampler.py) | 模型、损失与采样，A3 不修改 |
| [flow_model](../../rectified_point_flow/flow_model)、[procrustes.py](../../rectified_point_flow/procrustes.py) | 网络/SDPA 与几何求解，A3 不修改 |
| [data](../../rectified_point_flow/data)、[dataset_process/utils](../../dataset_process/utils) | 样本读取、归一化、采样和特征工具，A3 不合并不同研究分支的实现 |
| [RAPBackend](../../../RAP-SLAM/rap_slam/rap_backend.py) | 模型适配、预处理、归一化及 b→a 配准；只新增权重/仓库路径解析与缺失检查 |
| [SLAM cli.py](../../../RAP-SLAM/rap_slam/cli.py)、[runtime_paths.py](../../../RAP-SLAM/rap_slam/runtime_paths.py) | 独立参数解析及路径预检；--help 不需要 numpy/torch/模型依赖 |
| [rap_precision.py](../../../RAP-SLAM/rap_slam/rap_precision.py) | 当前作用域精度政策，原字节保留 |
| [real_dataset.py](../../../RAP-SLAM/rap_slam/real_dataset.py)、[spires_dataset.py](../../../RAP-SLAM/rap_slam/spires_dataset.py) | 原帧选择、校准、时间及坐标合同，A3 不修改 |
| [eval_paper_metrics.py](../../../RAP-SLAM/scripts/eval_paper_metrics.py) | 外部评测复用其指标函数；顶层批量历史产物注册表仍是旧复现工具，含旧路径，不纳入默认分派 |

保留两个仓库边界，不新增 editable install 或打包元数据：当前入口均通过文件位置定位源码，目标 Python/编译扩展的安装与训练/恢复入口由 A4 决定。库内诊断性 `__main__` 不因此成为受维护的训练命令。

## 历史、可选与安装脚本

- [scripts/maintenance](../../scripts/maintenance) 中，当前维护工具为 query_experiments.py、index_code_entries.py 与 render_current_state.py；其余按原协议使用的研究、封存、恢复、账户、下载或一次性工具退出默认运行链。原文件保留，既有 import 关系不移动、不改名，不能按文件名自动运行。
- RAP-SLAM scripts 中除上述两个有效入口外，其余研究/评测、安装、下载和巡检脚本保留来源，不能通过新启动器自动重跑。部分指标库仍被有效入口导入，这与执行其旧顶层批量实验不同。
- [app.py](../../app.py)、可视化工具和 [ROS2](../../../RAP-SLAM/ros2) 属于可选交互/系统组件，未纳入这次离线启动合同。app.py 仍使用其原相对目录与 UI 模型映射；A4 核对额外依赖，A6 处理组会制作链。
- install.sh、build_p3d.sh、下载脚本与旧 test_script_example.sh 是环境/操作来源材料，含旧机器假设；不作为迁移安装步骤。没有删除缓存、备份、权重、数据、日志或失败记录。

完整机器索引见 [ENTRYPOINTS.jsonl](ENTRYPOINTS.jsonl)：每份当前代码/配置记录职责、入口关系、静态导入、个人绝对路径行与 SHA256。分类是维护规则，不认证科学正确性；历史脚本内的本机路径逐项保留，迁移历史路径由[路径映射](../experiments/PATHS.md)解释。

```sh
python /path/to/RAP-main/scripts/maintenance/index_code_entries.py --check
```

索引限定两仓库的代码/配置目录，不遍历数据、输出、封存副本、组会构建缓存或 PGC1 部分结果。详细改动、原版本和验收边界见 [A3 报告](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)。
