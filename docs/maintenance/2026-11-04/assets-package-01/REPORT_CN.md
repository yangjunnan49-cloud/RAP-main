# A5：数据、权重与全部历史基础包

日期：2026-11-04，Asia/Shanghai。按所有者“继续”的指令接续 A4，完成六个 Windows 可见根的本地来源/覆盖清单、原字节分卷、全卷读回与普通文件恢复抽查。服务器尚未选择；这是可校验的本地基础包，完整目标恢复、链接/权限、A5/A6 最终增量和环境/训练仍分别待 A7 与 A4 保留项验收。

## 交付与范围

| 项目 | 实际结果 |
| --- | ---: |
| 普通源文件，逐物理副本重新读字节核对 | 111,629 |
| 原目录 / 不跟随目标的链接 | 5,141 / 27 |
| 原路径逻辑字节 | 134,910,234,709 |
| 唯一文件内容对象 / 字节 | 98,854 / 124,999,364,971 |
| USTAR 原字节分卷，单卷最多 4GiB | 30 |
| tar 卷总字节，含头及填充 | 125,075,722,240 |
| 单一主归属的逻辑包 / 未归属源文件 | 517 / 0 |
| 保留的零字节普通文件 | 358 |
| 真实恢复抽查文件 / 字节 | 18 / 690,123,401 |

六根分别为 RAP-main 47,407、RAP-SLAM 6,047、报告 311、Datasets 43,616、外部 Codex 记录 14,247、父级 AGENTS 1 个普通文件。两个 Git 仓库和全部实验历史保持原路径身份，原件未移动或删除。[SOURCE_FILES.jsonl](SOURCE_FILES.jsonl)、[目录](SOURCE_DIRECTORIES.jsonl)、[链接](SOURCE_LINKS_RAW.json)、[逻辑包](BUNDLES.jsonl)和[逐包成员](bundles)支持文件级追溯。517 是资产归属数，不是实验次数；A2 的 482 条档案索引保持原字节，A3/A4 新记录另行登记。

本机包位于 `.maintenance-archive/migration/A5-20261104`，在已有 ignored 目录内；没有改 .gitignore、Git 索引、提交、分支或历史。[PACKAGE_REFERENCE.json](PACKAGE_REFERENCE.json)绑定核心清单、30 卷及附加交付索引。包内含独立可运行的 recovery_tool.py、核心清单、517 份成员清单、覆盖/模型/来源表和使用说明；恢复仅需 Python 3.10+ 标准库。使用合同见[资产入口](../../../assets/README.md)和[分卷/恢复](../../../assets/PACKAGING.md)。

## 字节验证与恢复

首次枚举可复用 A1/旧 seal 中匹配元数据的哈希作为预期值；随后真正构建时，每个物理文件（包括重复副本）都重新读取并计算 SHA256，且读取前后检查大小/时间/普通文件状态。相同内容只存一个对象。[ARCHIVE_VERIFY.json](ARCHIVE_VERIFY.json)记录另一遍完整读回：全部 30 卷及 98,854 个成员的内容哈希、覆盖与核心控制清单通过。构建与读回使用同一已测试实现的不同遍历，不声称独立实现认证。

[RESTORE_CHECKS.json](RESTORE_CHECKS.json)记录三类真实恢复：当前 weights 的 5 文件（3 权重及 2 缓存元数据）、11 份 KITTI 本地 pose 参考、2 份外部历史文件。恢复字节逐一匹配冻结清单；没有加载 checkpoint、pickle、NumPy 或科学结果数组。仅清除了本阶段新建且成功验证的恢复测试副本，原件和失败证据保留。7 项标准库合成测试覆盖分卷边界、去重、Unicode/空文件恢复、坏卷、穿越路径、同大小/时间的重复源篡改、拒绝覆盖和控制清单篡改。

27 个原 reparse buffer 经不跟随目标的原生读取，全部匹配 A1。25 个 LX 链接与 2 个 node_modules junction 仅保留原始缓冲区和目标说明；没有将个人运行时目标递归打包，也没有自动重建链接。普通文件恢复为 destination/root_id/relative/path，不代表最终服务器布局、POSIX 权限或完整全量恢复已验收。Windows 枚举中的 file_id/device 为 0，不能据此声称 inode 身份独立性；冻结后的保全检查使用已验证字节与后续大小/时间/属性稳定性，未改写目录时间。

## 数据与模型覆盖

- [数据表](DATASETS.json)含 45 条本地序列/参考记录；68 次允许的 pose/time 文本行列检查逐次记录在 [DATA_TEXT_READS.json](DATA_TEXT_READS.json)。未读取点云数组、运行校准变换或认证原提供方。
- Datasets 的 KITTI 命名目录有 22 序列；各观测编号段连续且时间计数匹配，00–10 本地 pose 行数匹配，11–21 未见本地 pose。这不认证发行版完整性、坐标参考、原始/校正状态或训练划分。
- 下游 KITTI 目录只有 55 份 calibration/time/pose 参考，没有点云 bin。POSS 有 4,170 份 bin，区间 3850–5268 与 6750–9500，pose/time 各 36,924 行；按观测片段保全，不补下载或插值。
- Oxford Spires 只有 5 份 GT、0 PCD，显式标为部分参考。Datasets/part2 的 4 份 EPUB 单列非研究/待判定保留资料，未读内容、未删除。
- [模型表](MODELS.json)登记 3 个唯一内容、6 个当前/历史物理别名。权重来源 URL/原发行版未恢复，架构只按文件名登记；未检查参数或 optimizer/RNG/sampler 状态，不提供完整续训认证。
- [来源线索](SOURCE_CLAIMS.json)只引用 3 个既有下载脚本和历史下载日志的文本；未联网、下载或新增来源认证。raw/OXTS 及 Computer Use 旧 URL-enforcement 停止保持，不因目录或 URL 存在自动恢复。

## 当前文档与保全接续

A4 的 63 份当前权威均已备份在 [before](before)，更新后三层 AGENTS、状态和导航统一指向 A6，并新增 4 份资产说明和 1 个显式打包/恢复工具。904 条代码/配置索引中，原 903 条仅维护索引分类器增加迁移工具角色；902 条其它源码/配置保持字节一致，没有改生产、训练、算法参数或五项默认运行分派。见 [AUTHORITY_PROOF.json](AUTHORITY_PROOF.json)和[SOURCE_SUCCESSION.json](SOURCE_SUCCESSION.json)。

源冻结排除了本 A5 phase 和包目录自身；冻结时仍是 A4 当前文档，其字节也在基础包中。A5 新控制面、替换后的当前入口、后续 A6 成品及可能的新增量由 A7 最终汇总；不能直接把基础包当最终项目快照。包仍在同一块本地 E 盘，没有异地或服务器驻留证明。WSL 镜像及未导出的整套 Linux 环境/wheel 不在六根基础包中；A4 已导出的环境文件已包含，不因此代表环境可干净重建。

A0–A4 与 2,047 条科学封存条目通过原字节清单、源新读校验及包读回链继续保全；最终检查另核对旧 seal 自身与封存源的元数据稳定性。[CHECKS.json](CHECKS.json)记录本次交叉验证范围与方法。5 个旧源码哈希、1 个旧 AGENTS 中间版本及外部动态闭包缺口仍保留；A4 的 Muon、专用训练入口/完整恢复、PyTorch3D 成功构建原提交和目标 GPU/干净环境均未闭合。

Git 原 3,982 路径字节全部匹配 A1；A5 冻结还观测到 RAP-main 内额外 47 个 loose objects（2,869,646 字节），共 4,029 个 Git 文件均已入包。这些对象在本次冻结前已存在，来源不归因，不删改、不当成 A5 新提交；HEAD、分支和索引原字节保持。最初终验误将 A1 原路径数作为 A5 总数断言，[VALIDATION_FAILURE_03.json](VALIDATION_FAILURE_03.json)保留该范围错误，现按原件与额外对象分别核对，详见 [GIT_ADDITIONS_OBSERVATION.json](GIT_ADDITIONS_OBSERVATION.json)。

补充观察的生成曾晚于报告链接检查，产生一次悬空链接校验失败；先生成观察后终验通过。该顺序错误保留在 [VALIDATION_FAILURE_04.json](VALIDATION_FAILURE_04.json)，未改变源文件或 payload。

首次 capture 曾把 A1 HASHES 的链接行与普通文件集合直接比较，触发断言；原尝试和 [VALIDATION_FAILURE_01.json](VALIDATION_FAILURE_01.json)保留，修正为 file/link 并集后完整枚举通过，没有丢失资产。BASELINE 的中文 owner_request 摘要因主机编码损坏保留原字节，准确授权另见 [METADATA_ERRATA.json](METADATA_ERRATA.json)和[范围](AUTHORITY.md)，不改写已绑定包控制清单。

封存前交叉检查另发现 517 份成员清单的声明摘要原先对写入前 LF 字符串计算，Windows 实际写入为 CRLF。清单本身与包内副本原字节一致，源文件和 payload 未受影响；已按实际文件字节修正 BUNDLES 中摘要并重新绑定附加 DELIVERY_INDEX，核心 PACKAGE 和完整 payload 读回收据保持。修正前版本、校验器与 [VALIDATION_FAILURE_02.json](VALIDATION_FAILURE_02.json)保留；生成器也已纠正，未重建或覆盖源资产。

## 不变的研究边界与下一步

研究 UNRESOLVED、论文 PAUSED。GCG1 的 37/8、official MAC 未准入/未运行、PGC1 原 64 actions/第八对停止及七份未解释部分准确率、SSC1 的 18/3 筛选失败/评分训练前停止与原预算均保留。EIA1/SRA1 字节证据不升级身份或物理参考认证；SAC1 别名歧义和 MCV1 非安全/协方差证书限制保持。

本次没有启动 WSL/GPU、模型、训练或研究，没有安装、下载、部署或对外传输。下一步 A6 整理组会成品、图表来源和制作链；A7 再纳入最终控制面/组会增量、恢复链接/权限并对最终目标验收。
