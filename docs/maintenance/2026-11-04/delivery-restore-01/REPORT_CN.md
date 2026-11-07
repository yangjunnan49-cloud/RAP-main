# A7：本地分层交付与完整恢复验收

所有者在 A6 封存后要求“执行下一步”，并于 2026-11-05 再次指令“继续”。本阶段从 2026-11-04 的审计目录接续，当前维护日期按客户端 Asia/Shanghai 的 2026-11-05 记账，原始运行 UTC 时间另存收据。

本地交付采用不改写 A5 的基础层、承接最新 A6 的项目增量，以及本阶段最终当前入口/审计证据的独立控制层。完成范围是本地可恢复交付；服务器尚未选定，真实 Linux 权限/所有者、目标环境/GPU/训练、资料来源及组会版本保留项不提前关闭。

## 项目层结果

| 项目 | 实际范围 |
| --- | ---: |
| A5 基础物理文件 / 唯一内容对象 | 111,629 / 98,854 |
| 基础卷，完整读回并恢复 | 30 / 125,075,722,240 卷字节 |
| A7 项目增量 | 1,072 文件（1,053 新身份、19 当前字节更新） |
| 增量对象 / 唯一内容字节 | 833 / 144,164,228 |
| 增量卷，独立读回通过 | 1 / 144,814,080 字节 |
| 项目合成普通文件 / 目录 / 链接元数据 | 112,682 / 5,285 / 27 |
| 项目恢复后逐文件重新读 SHA256 | 112,682 文件 / 135,095,691,259 字节 |
| 被替换的基础版本，另存并重新核对 | 19 |
| 新恢复树的内部相对链接 | 25，目标解析/范围检查通过 |
| 不重建的个人运行时 junction | 2 |
| 隔离 cwd 的任务路径合同检查 | 5，无数值/模型导入，无任务输出 |
| 新交付工具的合成测试 | 9 |

本机包位于 RAP-main/.maintenance-archive/migration/A5-20261104 和 A7-20261104；两者必须一同携带。成功恢复位置为 `.maintenance-archive/migration/A7-restore-20261104-02/workspace`，新副本保留供验收，原件不移动或删除。包与恢复副本仍在同一块 E 盘，不提供异地或服务器驻留证明。

最终布局保持 workspace 下 RAP-main、RAP-SLAM、RAP-SLAM-report 和 Datasets 同级；外部 Codex 档案进入 archives/Codex，来源身份保持。替换前字节进入 archives/source-versions/A5 或 A7-control，不以重跑替代历史。旧绝对路径原文不批量重写，按映射解释。入口见[交付说明](../../../migration/DELIVERY.md)、[恢复步骤](../../../migration/RESTORE.md)和[交接/保留项](../../../migration/HANDOFF.md)。

## 字节验证及冻结范围

[PROJECT_FREEZE.json](PROJECT_FREEZE.json)和[PROJECT_FILES.jsonl](PROJECT_FILES.jsonl)冻结六根最新到 A6 的项目视图，排除本 A7 phase 及全部迁移包/恢复输出。A5 全部源身份保留。108,733 项以 A5 完整字节验证和本次匹配元数据作为预期哈希；3,949 项重新读源字节。1,072 项新增/改字节文件在实际增量打包时再逐物理文件新读并核对，没有把元数据复用声称为另一遍源全量读取。

真实恢复按每个卷完整流式读取，检查所有 tar 成员/对象身份、内容大小/SHA256和整卷 SHA256，再写出每个源路径；重复字节分别恢复成独立文件。[BASE_RESTORE.json](BASE_RESTORE.json)覆盖基础全量，[PROJECT_PACKAGE.json](PROJECT_PACKAGE.json)记录增量独立读回，[DELTA_RESTORE.json](DELTA_RESTORE.json)记录注册覆盖及 19 份旧版保留。

随后真正重新读取恢复后的整棵项目普通文件树和旧版副本，逐文件核对原期望字节；[PROJECT_RESTORE.json](PROJECT_RESTORE.json)不是抽样、仅 tar 校验或目录计数。之后只对明确登记的当前控制/晚到 Git 元数据做替换并逐一核对，不再无条件重复读取同一份 135GB。[LOCAL_CONTROL_RESTORE.json](LOCAL_CONTROL_RESTORE.json)和[快照](CURRENT_DOCUMENT_SNAPSHOTS.json)记录这部分小范围变更。

## 链接、权限和运行路径

Windows 原生 symlink 探针因缺少权限失败，未修改原链接；[LINK_CAPABILITY.json](LINK_CAPABILITY.json)保留结果。按 A7 文件系统验收范围，一次有界 WSL 维护仅在新恢复树创建 25 个相对内部链接，逐一 readlink/resolve 并确认目标仍在新树内。两个 node_modules junction 只登记、不跟随、不重建。原 27 个 reparse buffer 继续按 A5 原字节保全，终验再不跟随目标读取核对；相对化只发生在新恢复副本。

Linux /tmp 的新建小夹具实际调用交付工具的权限函数，验证 0755 脚本、0644 普通文件、0755 目录及固定文字脚本可执行，成功后只清理该新夹具。它与 NTFS 恢复树是不同文件系统，不把夹具当作整树或真实服务器 POSIX 权限/ACL 证书。[POSIX_LINK_CHECKS.json](POSIX_LINK_CHECKS.json)和[WSL_LINK_SESSION.json](WSL_LINK_SESSION.json)记录范围及恢复原 Stopped 状态。

[PERMISSIONS.json](PERMISSIONS.json)绑定当前两仓库 Git index 与 A1 精确保全索引/对应 tracked-mode 输出；311 项均为 100644。未跟踪文件不靠扩展名推断执行位，采用明确普通文件/目录策略；原所有者、ACL、所有未跟踪文件的原 Linux 模式没有完整来源，真实目标继续验收。没有更改原 Git 配置/索引。

[RELOCATED_CHECKS.json](RELOCATED_CHECKS.json)覆盖 sample、demo、features、slam、evaluate：在新恢复树从其它 cwd 做 --check，所需路径都位于新树、输出未创建，审计 sys.modules 未导入 torch/numpy/open3d/lightning 等数值/模型模块。两份恢复后的标准库测试文件再次通过；两仓库只读 rev-parse 的 HEAD/仓库根正确，索引字节保持。路径存在不是数据格式、来源、模型 I/O 或训练通过。

## 最终控制与封存后的证据层

项目层冻结时仍保留 A6 的当前入口。A7 完整数据/链接/路径检查通过后才发布最终文档/工具并形成 [AUTHORITY_PROOF.json](AUTHORITY_PROOF.json)、[SOURCE_SUCCESSION.json](SOURCE_SUCCESSION.json)与 81 份 after 快照；原 77 份权威事先在 [before](before) 按字节备份。原 905 份代码/配置全部不改字节，只新增 scripts/migration/delivery.py，当前职责索引为 906，默认推理/SLAM 分派不变。

最终控制更新先核对项目旧 SHA256，再保留旧字节、复制新字节并复核；未知冲突、已有目标或路径穿越停止。项目冻结后晚到的 Git 普通文件按有限终止时点另拍快照，不归因、不清理、不当成新研究/提交，也不承诺无限动态后台闭包。见 [LATE_GIT_OBSERVATION.json](LATE_GIT_OBSERVATION.json)和[快照表](LATE_GIT_SNAPSHOTS.json)。

[CHECKS.json](CHECKS.json)覆盖项目完整重读、当前控制、链接/路径、原件元数据、原索引/分支、A0–A6 和 2,047 条科学封存字节链。然后封存本 phase；封存后才把包括 seal 的整份证据做独立 PAX evidence.tar，逐文件清单绑定。离线恢复工具白名单解包、校验整 tar 与每个证据文件，再接续当前入口；该最后步骤的收据、最终 workspace 文件表和 DELIVERY 总清单放在包目录，避免回写已经封存的 phase 或递归把输出装入自身。

最终交付验收以 A7-20261104/FINAL_ACCEPTANCE.json 为准，它绑定最终 DELIVERY.json/文件表、phase seal 与证据包，并记录证据层在本地恢复树的字节校验。此报告的阶段 CHECKS 与封存后收据覆盖范围不同，不能以封存前项目验收冒充最后证据层已验证。

## 失败与修正均保留

1. 首次恢复在建目录时遇到 WinError 206：新根更深导致原 Git checkpoint 路径超过普通 Windows 路径上限，尚未进入 payload。首个目录树保留，不复用；改用扩展绝对路径和第二个新目标，补长路径回归。[VALIDATION_FAILURE_01.json](VALIDATION_FAILURE_01.json)、[最初工具](used/delivery.py)及 attempt01 保留。
2. 长路径回归的实际写/读成功，但 TemporaryDirectory 的普通路径清理失败；核对自建目录范围及固定生成字节后，仅清理该测试副本，并让测试清理也使用扩展路径。[VALIDATION_FAILURE_02.json](VALIDATION_FAILURE_02.json)保留。
3. 项目冻结末尾读取兄弟 Git tracked modes 的命令被沙箱权限拒绝；原索引未改。改为先核对当前 index 与 A1 保存的 index.snapshot/STATE 全 SHA256 精确相同，再使用对应已保全 mode 输出，未修改 Git safe.directory 或重新冻结已写出的清单。[VALIDATION_FAILURE_03.json](VALIDATION_FAILURE_03.json)和 [finish_freeze.py](finish_freeze.py)保留。

真实恢复使用的 `used/delivery-longpath.py` 按哈希绑定；最终发布工具中实际用到的恢复/检查核心逐函数 AST 一致。后加的控制/证据/CLI 与权限策略另外检查，9 项合成测试覆盖坏卷、尾部损坏证据阻止控制覆盖、双层/旧版保留、空文件/Unicode/长路径、穿越/碰撞/错误覆盖/已有输出。

## 继续保留的边界

研究 UNRESOLVED，论文 PAUSED。GCG1 37/8，official MAC 未准入/未运行；PGC1 原64 actions/第八对停止、七份部分准确率未解释；SSC1 18/3失败/评分训练前停止和原预算不变。EIA/SRA、SAC/MCV 的身份/物理参考/别名/安全限制保持。未加载模型、checkpoint、科学数组，未运行 GPU、训练、旧研究、图表重算或指标重算。

5 个旧源码哈希、1 个旧 AGENTS、外部动态闭包、raw/OXTS/数据/权重来源、A4 Muon/专用训练入口/完整恢复/原 PyTorch3D 成功提交/干净目标环境，以及 A6 终稿差异、参考 PDF、原生新导出继续保留。两个 WSL 镜像、未导出的整套 Linux 环境/wheel 留在原主机，不冒充已进入六根包。没有安装、下载、购买/部署/传输或对外发送，没有删改原件、旧 seal、Git HEAD/分支/索引/提交。

下一步为服务器确定后的完整包/驻留、实际权限/所有者、环境与获准最小功能验收。训练链和科学来源保留项另行闭合；本地交付完成不产生自动部署、开训、跨窗口续跑或新研究授权。
