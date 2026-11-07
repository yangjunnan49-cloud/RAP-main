# 路径与原始资料解析

索引文件中的 `asset`、`source`、`id` 使用 `root_id:relative/path`。它们表示本地来源身份，不作为可以直接执行的系统路径。

| 根 ID | 当前相对工作区位置 | 迁移要求 |
| --- | --- | --- |
| rap-main | RAP-main | 独立模型/研究仓库 |
| rap-slam | RAP-SLAM | 与 RAP-main 保持仓库边界 |
| reports | RAP-SLAM-report | 报告和论文材料，论文仍暂停 |
| datasets | Datasets | 全部数据及来源/校验说明随迁 |
| codex-records | archives/Codex（A7恢复布局） | 全部项目实验历史随迁并常驻服务器 |
| workspace-root | 工作区父级 | 当前共通约定与旧原件保全 |

本机 Windows、`/mnt/<drive>/...` 别名和暂存根建议见 A1 [ROOT_MAPPING.json](../maintenance/2026-11-03/migration-audit-01/ROOT_MAPPING.json)。这份A1映射保持原建议；A7已采用[同级仓库/Datasets和独立档案根布局](../migration/DELIVERY.md)，服务器绝对挂载点仍未定；A3 已提供[离线运行路径配置](../code/RUNNING.md)，允许分别指定代码、数据、权重、输出和缓存根；历史来源映射不变。

目录中的可读链接优先指向仓库内相同 SHA256 的历史文档。没有仓库副本的外部报告/协议，按原字节存入 evidence/，来源和校验见 [evidence_manifest.json](evidence_manifest.json)。镜像是历史资料，内部旧相对链接保持原文；当前导航由 CATALOG.md 和来源 ID 承担，不把镜像内部路径当成已修复的运行入口。

旧清单的首选路径不再匹配、另一处仍有相同字节、从 Git/原文切片恢复、未检查的 Linux 文件和未恢复版本分别登记，不能互相代替。详细对照在 A1 的 SEAL_CLAIMS.jsonl、REVIEWED_SEAL_EXCEPTIONS.jsonl 和 RECOVERED_SOURCES.json；从[缺口页](GAPS.md)进入。

当前目录不移动、重命名或重新解释原始实验数据；缺少原件的哈希仅作文字证据，不生成指向不存在文件的链接。
