# 环境、依赖与训练就绪入口

更新：2026-11-04，Asia/Shanghai。A4 已完成环境与训练链审计、参考搭建说明和现有环境 CPU 依赖检查。**目标服务器尚未选定，干净环境、GPU 模型 I/O 和完整训练/恢复链尚未验收。** 本次没有安装、下载软件包、加载模型权重或运行训练。

| 要做什么 | 入口 |
| --- | --- |
| 按顺序搭建与定位缺失依赖 | [SETUP.md](SETUP.md) |
| 查看实际环境、来源、补丁及二进制限制 | [OBSERVED.md](OBSERVED.md) |
| 检查完整训练/断点恢复链的具体缺口 | [TRAINING.md](TRAINING.md) |
| 区分元数据、CPU、GPU、训练和恢复验收 | [VALIDATION.md](VALIDATION.md) |
| 追踪源码中的依赖位置 | [DEPENDENCIES.json](DEPENDENCIES.json)：72 份当前运行相关源码、552 条静态导入边，不是完整动态闭包 |
| 追踪公开安装依据 | [SOURCES.md](SOURCES.md) |
| 查看原始收据与保全材料 | [A4 报告](../maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md) |

[参考依赖配置](../../environment/requirements)按核心、SLAM、可选渲染/UI 分层；184 项 observed constraints 只来自现有环境，不作为经过干净重建或逐包来源认证的锁文件。旧 requirements_other.txt、install.sh、build_p3d.sh 原字节保留，不能与新说明混用后宣称环境已统一。

可使用[标准库元数据工具](../../scripts/environment/inspect_metadata.py)和[显式 CPU 探针](../../scripts/environment/cpu_probe.py)。模型数据、推理命令和历史限制分别见[代码入口](../code/README.md)、[运行说明](../code/RUNNING.md)和[当前状态](../CURRENT_STATE.md)。
