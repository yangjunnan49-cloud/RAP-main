# 迁移准备初查报告

本报告属于前置清点与计划阶段，不是全面审计或整体整理完成声明。依据：当前对话所有者五项确认，见 AUTHORITY.md；执行顺序见 ../../../migration/PLAN.md。

## 已完成的前置工作

- 原项目 AGENTS 452,440 字节和父级 AGENTS 24,622 字节均原字节备份，哈希记入 BASELINE.json。
- RAP-main：HEAD `4055d929c594b0033aafc6eed339c910369eef55`，分支 `codex/meeting-20260930`，原 tracked dirty 为 `.gitignore` 和 `AGENTS.md`。
- RAP-SLAM：HEAD `6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6`，分支 `codex/e0-f1-20260926`，原九个 tracked dirty 路径见 BASELINE.json。首次受限 Git chdir 失败，升级后的只读访问成功，保留原修改。
- RAP-SLAM-report 未发现 Git 仓库。未查询远端状态，未修改索引、分支、提交或历史。
- 初次清点将格式化目录输出中的两个 working files 子目录误认作同级候选根；两个不存在的候选与首次观察完整保存在 inventory/。核对实际路径后，将脚本及输出修正为 inventory02/；实际文件已由 RAP-main 根覆盖，没有遗漏这两处内容。

## 元数据清点

主观察：inventory02/SUMMARY.json 和 entries.jsonl。枚举不跟随 reparse point，不读取文件内容，不包括本维护阶段自身。

| 根 | 文件数 | 逻辑大小 GiB |
| --- | ---: | ---: |
| RAP-main | 42,535 | 34.237 |
| RAP-SLAM | 6,044 | 7.726 |
| RAP-SLAM-report | 311 | 0.178 |
| Datasets | 43,616 | 78.970 |
| 外部 Codex 记录 | 14,247 | 0.687 |
| 工作区根文件 | 1 | <0.001 |
| 合计 | 106,754 | 121.798 |

六根枚举均返回完成、零枚举错误；该“完成”仅指指定根的非递归链接枚举。27 个 reparse point 未跟随。逻辑总字节 130,779,517,380，可重复计入硬链接或重复副本，不是物理独占空间或最终压缩包大小。未做全量内容哈希，也未证明任一数据集完整或全部资产已被引用链覆盖。

通过既有 WSL 迁移记录另定位到当前镜像和旧备份，各 44,881,149,952 字节，见 ENVIRONMENT_IMAGES.json。这两个镜像未计入上表，内部未检查，也未宣称相同内容。是否存在尚未外置的项目源码、数据或实验需后续环境审计确认；不自动清除或迁移整个操作系统镜像。

## 初步问题及处置方向

1. **上下文膨胀、入口陈旧。** 原 AGENTS 约 442 KiB，历史全文持续叠加；维护 README 仍标 10 月 5 日为最新。本阶段将根 AGENTS 精简为当前入口并保留原件，后续统一其余入口与实验索引。
2. **实验材料跨根。** RAP-main/docs 约 25.665 GiB，另有外部 Codex 记录、维护快照和 RAP-SLAM 输出；目录名不足以判定归属与可删性。
3. **特殊链接依赖。** 27 项中，两个 node_modules junction 可解析到个人 Codex 缓存；另 25 个 latest 项带 reparse 属性，但 Windows API 未给出目标。详见 LINK_AUDIT.json。后者尚不能直接认定为损坏或可删。
4. **本机绝对路径。** 有限静态扫描在 RAP-main 指定当前源码/脚本范围命中 1 文件/2 行；RAP-SLAM 的 rap_slam/scripts/ros2 范围命中 59 文件/109 行。后者包含尚未分类的开发脚本；命中数不是缺陷数，也不是全部路径依赖数。原始命中见 ACTIVE_PATHS_*.jsonl。
5. **环境约定分叉。** 安装脚本目标 PyTorch 2.5.1/CUDA12.4；父级记录存在 PyTorch2.7.0/CUDA12.8 的实际环境路径；build_p3d.sh 固定 root、CUDA、架构并包含清理/联网动作。这里只读取脚本，不执行，也不据此推荐目标服务器版本。
6. **训练链尚未验证。** 发现 modeling.py 的 training_step/configure_optimizers 及 datamodule.py 的 train_dataloader；当前可见根配置为推理配置，有限入口扫描未发现独立训练启动脚本。模块接口存在不能证明完整训练入口、数据和断点恢复可用，需 A4 专项核对。
7. **组会材料分散。** docs/meeting_*、working files 及 RAP-SLAM-report 均有相关资产，需要按交付版本和来源建立总索引。当前仅清点名称与路径，未核对幻灯片/文档内容。

## 保全及验证口径

根 AGENTS 是维护中的当前入口；本阶段其精简版本取代旧的“当前文件哈希”断言。旧关闭记录和验证程序保持原样，旧程序若直接断言现行 AGENTS 等于旧哈希，已不再适合作为当前入口验证。本阶段以 before/RAP-main.AGENTS.md 对接旧 AUTHORITY_PROOF.json 的哈希，另检查历史封存文件和 source freeze，并记录新的当前入口证明；不声称旧验证程序在变更后原样通过。

verify_preflight.ps1 的首次只读检查通过：2,047 个科学封存文件 / 297,738,079 字节、39 项 source freeze、28 项关闭记录封存条目、原 AGENTS 备份与当前入口证明、清点内部计数及 14 个当前 Markdown 链接均通过。根 AGENTS 精简后为 6,167 字节。此检查不执行旧实验程序、不读取解释 PGC1 部分准确率，也不替代其它日期尚未审计的全部历史封存检查。

研究 UNRESOLVED、论文 PAUSED。GCG1 37/8、PGC1 原停止位置和未读部分准确率、official MAC 未运行、SSC1 停止门槛、既有来源限制及 E0 工程正面结果均保留。未启动研究实验、WSL、GPU、模型、训练、安装、数据下载、服务器操作或对外发送；未移动或删除现有资产。

## 下一步

执行 A1，补齐归属、封存边界、外部引用与链接处理，形成可校验、可回退的逐文件处置表。尚不能宣称迁移包、依赖锁、训练环境或数据完整性已验收。
