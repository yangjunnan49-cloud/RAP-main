# RAP-main：模型与研究工作区

本仓库保存 RAP 模型、预处理和推理代码，以及本地研究/维护档案；下游 SLAM 系统在独立的同级 RAP-SLAM 仓库。当前进行迁移前工程整理，服务器尚未选定，未来用于继续研究与训练；全部实验历史随迁并常驻服务器。

从 [AGENTS.md](AGENTS.md)进入核心上下文，再读[当前状态](docs/CURRENT_STATE.md)、[项目约定](docs/CONVENTIONS.md)和[文档导航](docs/README.md)。研究 UNRESOLVED、论文 PAUSED；整理不产生新算法结论或训练资格。

## 代码入口

| 路径 | 作用 |
| --- | --- |
| [scripts/run.py](scripts/run.py) / [运行说明](docs/code/RUNNING.md) | 统一离线启动器：默认生成计划，支持路径检查与显式执行 |
| [rectified_point_flow](rectified_point_flow) | 模型、采样、数据与几何模块 |
| [dataset_process](dataset_process) | 预处理和特征工具 |
| [config/RAP_inference.yaml](config/RAP_inference.yaml) | 现有推理配置；不是已验收的训练配置 |
| [sample.py](sample.py) | Hydra 批量推理入口，现配置名为 RAP_inference |
| [demo.py](demo.py) / [app.py](app.py) | 文件夹处理与可选交互演示入口 |
| [scripts/maintenance](scripts/maintenance) | 研究/维护工具，历史工具不因目录存在而自动执行 |
| [RAP-SLAM](../RAP-SLAM/README.md) | 下游系统的当前说明 |

A3 已整理[代码职责与入口索引](docs/code/README.md)，集中配置运行路径；路径/CLI 和数值源码保持检查通过，尚未执行模型。A4 已形成[环境搭建说明](docs/environment/README.md)和[训练缺口审计](docs/environment/TRAINING.md)；现有 CPU 依赖检查通过，目标重建/GPU 模型与完整训练恢复仍待验收。A5 已交付[资产清单与本地基础包](docs/assets/README.md)，原件保留，源文件和分卷字节核对通过；A6 已交付[组会/报告目录及制作准备](docs/meetings/README.md)，版本和导出限制单列；A7已形成[本地交付与恢复入口](docs/migration/DELIVERY.md)，完整项目字节复核及相对链接检查通过；服务器确定后继续目标验收。现有安装脚本含旧硬件/个人路径约定，本轮没有执行或证明它们适用于新服务器。

## 研究、迁移和组会资料

- [实验索引](docs/experiments/README.md) / [按类目录](docs/experiments/CATALOG.md)：协议、来源、状态、产物和原始证据。
- [迁移入口](docs/migration/README.md) / [计划](docs/migration/PLAN.md)：阶段、验收及全部历史常驻服务器的要求。
- [维护档案](docs/maintenance/README.md)：历史记录与旧入口原件。
- [版本与环境缺口](docs/experiments/GAPS.md)：五个旧源码哈希、一份上下文版本及 A3–A7 待办。
- [组会/报告总入口](docs/meetings/README.md)：成品、讲稿、编辑源、版本差异、图表和便携制作说明。

## 上游与原始说明

上游文档、论文引用、安装命令和致谢的原文完整保存在[整理前 README](docs/maintenance/2026-11-03/context-index-01/before/rap-main/README.md)，许可证见 [LICENSE](LICENSE)。当前页描述本地工程组织，不改写上游原文，也不将旧结果或未发布计划当作本地已验收功能。
