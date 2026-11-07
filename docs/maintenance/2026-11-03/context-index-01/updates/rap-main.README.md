# RAP-main：模型与研究工作区

本仓库保存 RAP 模型、预处理和推理代码，以及本地研究/维护档案；下游 SLAM 系统在独立的同级 RAP-SLAM 仓库。当前进行迁移前工程整理，服务器尚未选定，未来用于继续研究与训练；全部实验历史随迁并常驻服务器。

从 [AGENTS.md](AGENTS.md)进入核心上下文，再读[当前状态](docs/CURRENT_STATE.md)、[项目约定](docs/CONVENTIONS.md)和[文档导航](docs/README.md)。研究 UNRESOLVED、论文 PAUSED；整理不产生新算法结论或训练资格。

## 代码入口

| 路径 | 作用 |
| --- | --- |
| [rectified_point_flow](rectified_point_flow) | 模型、采样、数据与几何模块 |
| [dataset_process](dataset_process) | 预处理和特征工具 |
| [config/RAP_inference.yaml](config/RAP_inference.yaml) | 现有推理配置；不是已验收的训练配置 |
| [sample.py](sample.py) | Hydra 批量推理入口，现配置名为 RAP_inference |
| [demo.py](demo.py) / [app.py](app.py) | 文件夹处理与可选交互演示入口 |
| [scripts/maintenance](scripts/maintenance) | 研究/维护工具，历史工具不因目录存在而自动执行 |
| [RAP-SLAM](../RAP-SLAM/README.md) | 下游系统的当前说明 |

当前 A2 统一文档入口与索引。A3 处理代码职责、有效脚本和本机路径；A4 核对依赖、编译扩展、训练启动与恢复链。现有安装脚本含旧硬件/个人路径约定，本轮没有执行或证明它们适用于新服务器。

## 研究、迁移和组会资料

- [实验索引](docs/experiments/README.md) / [按类目录](docs/experiments/CATALOG.md)：协议、来源、状态、产物和原始证据。
- [迁移入口](docs/migration/README.md) / [计划](docs/migration/PLAN.md)：阶段、验收及全部历史常驻服务器的要求。
- [维护档案](docs/maintenance/README.md)：历史记录与旧入口原件。
- [版本与环境缺口](docs/experiments/GAPS.md)：五个旧源码哈希、一份上下文版本及 A3–A7 待办。
- [组会定位](docs/experiments/MEETINGS.md)：现有成品/工作材料位置，最终整理待 A6。

## 上游与原始说明

上游文档、论文引用、安装命令和致谢的原文完整保存在[整理前 README](docs/maintenance/2026-11-03/context-index-01/before/rap-main/README.md)，许可证见 [LICENSE](LICENSE)。当前页描述本地工程组织，不改写上游原文，也不将旧结果或未发布计划当作本地已验收功能。
