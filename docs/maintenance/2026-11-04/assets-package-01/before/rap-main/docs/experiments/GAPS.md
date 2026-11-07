# 保全缺口与后续依赖

本页接续 A1 的[原始缺口清单](../maintenance/2026-11-03/migration-audit-01/PRESERVATION_GAPS.json)和[审计报告](../maintenance/2026-11-03/migration-audit-01/REPORT_CN.md)。以下差异在本轮整理之前已被观察到；当前代码、旧声明和已找回原件均保留，不以现在的文件冒充旧版本。

## 五个旧源码哈希

| 原路径/版本 | 旧 SHA256 | 来源 |
| --- | --- | --- |
| RAP-SLAM scripts/run_pipeline.py，M2 | `482d9b285384abb3489211ff621acb9fcf5646227a12151aca1b3c8d8a3e4c41` | [M2 源码清单](../maintenance/2026-09-10/m2-evaluation/final_source_manifest.json) |
| RAP-SLAM rap_slam/rap_backend.py，M2 | `fbf27bafd36dadcf02167f53b8320e70fb7f82e1e66ee0118c01cfbec67d98be` | [M2 源码清单](../maintenance/2026-09-10/m2-evaluation/final_source_manifest.json) |
| RAP-SLAM rap_slam/odometry.py，早期多处引用 | `677ec6d410358ba30cfc3a1e3c022753b5f955d214a5d7888439070d17f547c1` | [M2 源码清单](../maintenance/2026-09-10/m2-evaluation/final_source_manifest.json) |
| RAP-SLAM scripts/run_pipeline.py，M3 logging | `afdf15de7ff3779207d04795e8fe3d03c5adb7b8f419f2fd4c121d5426bc27be` | [M3 源码清单](../maintenance/2026-09-11/m3-logging/final_source_manifest.json) |
| RAP-main scripts/maintenance/diagnose_rejection.py，早期版本 | `b523e3608c7abb42065b2550fb4d6207ad357c2e5f6c8c98fc0e5e668b9baca0` | [原输入冻结](../maintenance/2026-09-15/rejection-diagnostic-01/input_freeze.json) |

A1 在六个已清点根、本地 Git 小型 blob、42 个压缩包的源码成员及历史上下文中进行定界搜索。未找回完全相同字节不等于证明整机永久丢失；此处也不把未恢复源码写成实验结果丢失。

## 旧上下文中间版本

10 月 20 日 AGENTS 中间版本 SHA256 为 `1044715deb7ec959ecec68810450f0245907755913c97c7884d6cd0b071c5261`，见[原停止 seal](../maintenance/2026-10-20/weekly-system-handoff-01/ACCOUNT_STOP_SEAL.json)。该版本的精确字节仍未恢复，完整前后原文及已找回版本继续保留。新入口证明不用于掩盖这个旧版本缺口。

## 后续阶段承接

| 阶段 | 保留项 |
| --- | --- |
| A3 | 离线入口、路径和静态保持检查已完成，见 [A3 报告](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)；可选组件/目标模型执行与工作区外动态引用闭包仍待后续验收 |
| A4 | 原 72 条 Linux 哈希已全部精确匹配；[新审计](../environment/README.md)保留 PyTorch3D 原提交、Muon/专用训练入口与完整恢复、干净重建/GPU 目标验收及旧 Windows 工具版本差异 |
| A5 | 数据集来源、版本、校准/时间/位姿角色与完整性；raw/OXTS 包不因目录存在被标齐 |
| A6 | 最终组会版本、图表来源、制作源码与两个个人 node_modules 目录联接的重建方式 |
| A7 | 全部资料在目标服务器的恢复、完整校验与受测环境验收 |

1,001 条虚拟 synthetic 文件声明、WLC 错误哈希负对照和主动污染的合成夹具已经按原源码解释；不列为真实数据遗失，也不“修复”这些测试证据。已恢复的 17 个旧版本见 A1 [RECOVERED_SOURCES.json](../maintenance/2026-11-03/migration-audit-01/RECOVERED_SOURCES.json)。
