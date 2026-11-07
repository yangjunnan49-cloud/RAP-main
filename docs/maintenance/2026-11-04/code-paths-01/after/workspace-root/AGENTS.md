# RAP 工作区：共通约定

更新：2026-11-04，Asia/Shanghai。当前为所有者明确授权的迁移前工程整理。A3 完成离线代码入口与路径整理，未运行模型；下一阶段为 A4 环境与训练/恢复链审计，具体记录由 RAP-main 当前入口承担。

## 入口与范围

- [RAP-main 当前约定](RAP-main/AGENTS.md)：核心上下文和必须保留的研究边界。
- [当前状态](RAP-main/docs/CURRENT_STATE.md)、[项目约定](RAP-main/docs/CONVENTIONS.md)、[迁移计划](RAP-main/docs/migration/PLAN.md)。
- [实验索引](RAP-main/docs/experiments/README.md)、[保全缺口](RAP-main/docs/experiments/GAPS.md)。
- RAP-SLAM 的本仓库规则见 [RAP-SLAM/AGENTS.md](RAP-SLAM/AGENTS.md)。

范围包括两个独立代码仓库、RAP-SLAM-report、Datasets、外部 Codex 实验档案和组会材料。服务器用于继续研究与训练，尚未选定；全部实验历史随迁并常驻服务器。当前维护说明中文为主，代码标识/注释英文，历史材料保持原文。

## 共通边界

研究 UNRESOLVED，论文 PAUSED。E0 工程正面结果、全部历史失败/中断/上限/来源限制保留；GCG1 保持 37/8；SSC1 保持评分/训练前停止；PGC1 保持原 64 actions/第八对停止及七份部分准确率未解释读取；official MAC 未运行。

工程维护不恢复已停止路线、不放宽阈值、不启动新研究或训练，不自动跨额度窗口/重置续跑，不自动购买/部署/发送材料或改写 Git 历史。环境、数据、组会和目标服务器分别按迁移计划验收。

保留两个仓库边界和现有用户修改。旧协议、原始输入/结果、失败、seal/freeze 和验证程序原字节保留；当前入口先备份再更新。历史原路径通过映射解释，不批量改写封存文件。五个旧源码哈希、一份旧上下文与环境待办仍有效。

本文件旧 24,622 字节全文保存在 [A2 原件](RAP-main/docs/maintenance/2026-11-03/context-index-01/before/workspace/AGENTS.md)。其中旧“当前状态”和安装命令作为历史材料，不替代上述当前入口。
