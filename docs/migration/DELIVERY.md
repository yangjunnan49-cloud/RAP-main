# 本地交付入口与最终布局

本地交付由 A5 基础包、A7 项目增量和 A7 最终控制/证据层组成。它保留全部已清点实验历史、失败、源码版本、数据、模型和组会原件；服务器尚未选定，不能把本地恢复完成写成服务器迁移或训练就绪。

| 来源根身份 | 恢复到新 workspace 的位置 |
| --- | --- |
| workspace-root | workspace/AGENTS.md 等原父级普通文件 |
| rap-main | workspace/RAP-main |
| rap-slam | workspace/RAP-SLAM |
| reports | workspace/RAP-SLAM-report |
| datasets | workspace/Datasets |
| codex-records | workspace/archives/Codex |
| 被新入口替换的旧字节 | workspace/archives/source-versions/A5 或 A7-control |

同级仓库和 Datasets 布局与现有路径解析器一致，绝对挂载点可换。旧封存里的 E:/、/mnt/e、C:/Users 路径保留，按来源身份映射解释，不改写历史文件。25 个内部 latest 链接改用相对目标；两个指向个人运行时的 node_modules junction 不重建，由显式依赖/便携准备流程接续。

## 需要携带的包

本机存放在 RAP-main/.maintenance-archive/migration。传输时同时保留两兄弟目录，避免只拿增量：

```text
transfer/
  A5-20261104/       # 原基础包，30卷，保持原字节
  A7-20261104/       # PROJECT、delta、最终证据、工具与DELIVERY总清单
```

A5 覆盖 111,629 份普通文件、98,854 个唯一内容对象；30 卷原字节 tar 共 125,075,722,240 字节。A7 项目增量为 1,072 份源文件，独立读回的 833 对象单卷 144,814,080 字节。二者合成的项目层是最新到 A6 的 112,682 文件、135,095,691,259 字节；19 份被替换的基础版本另存历史，不丢弃。

A7 自身的最终当前入口、工具和审计证据在独立 evidence 层中。先冻结并完整恢复项目数据层，后封存本阶段证据并打包；因此包和恢复树不会被递归装入自身。最终 DELIVERY.json 绑定 PROJECT、各层清单、证据包、控制快照和最终恢复文件表；证据封存后收据放在包目录，不再回写已封存阶段。

最终数量、SHA256 和恢复收据以 A7-20261104/DELIVERY.json、DELIVERY_FILES.jsonl、FINAL_ACCEPTANCE.json 为准。包内工具仅需 Python 3.10+ 标准库，不需要本机个人缓存、模型库或网络。具体操作见[恢复说明](RESTORE.md)。

## 保全与限制

全部历史随迁并常驻服务器，原件和原 Git 索引/分支/提交保留。恢复副本是独立文件，普通文件重复字节去重只发生在包内，不让不同实验原路径共享可写文件身份。替换当前入口时先核对旧 SHA256 并保存旧字节，未知冲突直接停止，不盲覆盖。

本地包和恢复副本仍在同一块 E 盘，没有异地或服务器驻留证明。两个 WSL 镜像、未导出的整套 Linux 环境和仅在 WSL 内登记的 wheel 不在六根项目层中；A4 已导出的环境资料已随迁。目标 Linux 权限/所有者、依赖重建、GPU、模型 I/O、完整训练/续训、数据来源及 A6 版本/参考 PDF 等保留项见[迁移交接](HANDOFF.md)。

[当前状态](../CURRENT_STATE.md) · [环境搭建](../environment/SETUP.md) · [资产清单](../assets/README.md) · [组会索引](../meetings/README.md)
