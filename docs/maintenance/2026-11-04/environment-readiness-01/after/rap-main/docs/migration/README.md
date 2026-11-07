# 迁移准备入口

本次任务：在租用服务器确定前，完成完整研究资产的审计、剪枝、结构整理、环境恢复说明与可校验交付准备。

所有者已确认：服务器用于继续研究与训练；全部实验历史随迁并常驻服务器；先保留仓库边界；当前维护文档以中文为主，历史文档保持原文。

## 阅读顺序

1. [根 AGENTS.md](../../AGENTS.md)：当前任务与必须保留的研究边界。
2. [执行计划](PLAN.md)：阶段、产物与验收条件。
3. [本轮授权](../maintenance/2026-11-03/migration-preflight-01/AUTHORITY.md)：五项已确认约定与维护范围。
4. [初查报告](../maintenance/2026-11-03/migration-preflight-01/REPORT_CN.md)：实测元数据、问题和未覆盖项。
5. [基线](../maintenance/2026-11-03/migration-preflight-01/BASELINE.json)及[清点摘要](../maintenance/2026-11-03/migration-preflight-01/DISCOVERY_SUMMARY.json)。
6. [A1 审计报告](../maintenance/2026-11-03/migration-audit-01/REPORT_CN.md)、[逐文件处置表](../maintenance/2026-11-03/migration-audit-01/DISPOSITION_DRY_RUN.csv)及[保全缺口](../maintenance/2026-11-03/migration-audit-01/PRESERVATION_GAPS.json)。
7. [A4 环境与训练链审计](../maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)、[搭建说明](../environment/SETUP.md)和[训练缺口](../environment/TRAINING.md)。
8. [A3 代码与路径整理](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)、[代码职责](../code/README.md)和[运行说明](../code/RUNNING.md)。
9. [A2 文档与索引整理](../maintenance/2026-11-03/context-index-01/REPORT_CN.md)、[当前状态](../CURRENT_STATE.md)和[实验总索引](../experiments/README.md)。

## 当前进度

- 已完成 A0：约定、基线、前置 AGENTS 原字节备份、执行计划和当前入口精简。
- 已完成 A1 的 Windows 可见范围：106,767 个普通文件全量 SHA256、27 个链接元数据、106,794 行逐文件/链接处置表；两个 Git 原目录及 2,955 条源码路径保全，找回 17 个历史版本。原资产未移动或删除。
- 已完成 A2：父级/两仓库当前约定、README、维护首页和统一状态页接续；实验、维护、旧产物与组会按类建立索引，保留原文、未知字段和停止边界。
- 已完成 A3 离线入口与路径整理：标准库启动器、显式配置、SLAM CLI 拆分及路径/参数/数值源码保持检查；没有运行模型。
- A4 审计/说明与现有环境 CPU 检查已完成；Muon、专用训练入口/完整配置、原 PyTorch3D 构建来源和干净/目标环境保留项明确。
- 明确保留：5 个旧源码哈希和 1 个旧 AGENTS 中间版本暂未恢复，72 条 Linux 环境引用已在 A4 全部精确匹配，原构建提交和目标环境仍待验收；虚拟/负对照夹具保持原样。详见 A1 报告。
- 尚未完成：工作区外动态引用闭包、数据集来源核对、可选交互/ROS2 与外部动态依赖的目标验证、环境新建验证、组会内容核对、实际数据打包与迁移。
- 下一步：执行 A5，整理数据、模型与全部历史的来源、范围及校验清单；A4 目标/训练保留项继续跟踪，A6/A7 分别验收。

本阶段没有选择或购买服务器，没有安装依赖、启动 WSL/GPU、加载模型、训练或恢复已停止的科学路线。可见目录审计和字节校验不代表完整来源认证或整体迁移完成。
