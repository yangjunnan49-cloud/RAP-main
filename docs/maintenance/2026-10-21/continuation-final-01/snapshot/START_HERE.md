# 本轮交付入口

首先阅读 [本轮结论与交接](REPORT_CN.md)。当前账户边界记录见 [ACCOUNT_STATE.json](ACCOUNT_STATE.json)，最终停止与成本见 COSTS_AND_STATUS_FINAL.json；各较早报告中的 ACTIVE 或百分比属于当时快照，以本目录最终记录为准。

- [P0 全 72 cells 独立验证报告](../overlap_validation_20261021/REPORT_CN.md)
- [72 条未对齐 LiDAR 轨迹 ZIP](../overlap_validation_20261021/validated_72_trajectories_20261021.zip)
- [速度比较图](../overlap_validation_20261021/runtime_comparison.png)
- [宿主失联保护原型与限制](../guard_hardening_20261021/REPORT_CN.md)
- [冻结源码审查及原因未知边界](../native_stability_review_20261021/REPORT_CN.md)
- [边界记录契约与 21 项合成检查](../boundary_contract_20261021/REPORT_CN.md)
- [下一轮观测工作的准入顺序](NEXT_NATIVE_OBSERVATION.md)
- [281 条封存哈希核对](INTEGRITY_CHECKS.json)

P0 的 G/K 均因原阈值下的等价失败关闭，历史预算失败保留；本轮没有新增 RAP 增益、真实原生重放或默认变更。下一轮方案只作交接，不自动启动。
