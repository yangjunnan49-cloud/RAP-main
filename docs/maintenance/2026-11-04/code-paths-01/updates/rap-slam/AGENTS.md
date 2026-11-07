# RAP-SLAM 当前约定

本仓库是 RAP 工作区中的下游系统，独立管理；先读 [RAP-main 核心上下文](../RAP-main/AGENTS.md)、[当前状态](../RAP-main/docs/CURRENT_STATE.md)和[项目约定](../RAP-main/docs/CONVENTIONS.md)。本文件不重复历史指标或建立另一套研究状态。

当前处于迁移前工程维护：A3 离线入口与路径整理已完成，下一步 A4 审计环境和训练/恢复链；目标环境模型 I/O 尚未执行。服务器和训练环境尚未验收；全部实验历史随迁常驻服务器。旧 README 原件及旧结果从当前 README 的历史入口查阅。

- 保留原用户未提交修改、独立仓库边界、算法参数、RNG、精度作用域和输入/输出语义；当前代码改动需按 A3 做行为保持检查。
- `RAPBackend.register(a,b)` 映射 b→a；保持与 pose graph 的约定。原始/校正 LiDAR、KITTI 相机位姿和 POSS LiDAR/world 不混用。
- 数值精度以当前 rap_precision.py 的作用域及已冻结源码为准；不按父级旧历史描述恢复全局 TF32 设置。
- 当前离线入口从 RAP-main/scripts/run.py 生成计划、--check 检查路径、--execute 显式执行；路径优先级 CLI > JSON > 环境 > 布局。scripts/run_pipeline.py 参数已拆到 rap_slam/cli.py，runtime_paths.py 负责布局默认值与预检，新增 --rap-ckpt/--spinnet-ckpt。55 个原非路径参数及数值主体保持；A4 核对依赖、编译扩展和训练/断点恢复链。
- data/、output*/、根运行日志和失败产物均有证据/来源角色，不能因 Git ignored/untracked 或文件名看似临时就删除。新运行使用新目录，保护旧结果与 seal。
- 本阶段不运行模型、训练或研究实验，不启动 WSL/GPU、安装或下载，不改变 Git 历史或对外发送。PGC1 未读部分准确率保持未解释读取；具体停止与来源限制见核心上下文。
- 代码/注释英文，当前维护文档中文，历史原文保留。每阶段更新核心状态及本仓库相关入口，避免累积相互竞争的“当前状态”。
