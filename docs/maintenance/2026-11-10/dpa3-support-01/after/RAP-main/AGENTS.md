# 2026-11-10：DPA3支持诊断完成

DPA3原末态支持代数诊断完成：4对、0新NN/原raw/参考数组读取，32组Gram/谱等独立核对通过。低对6129/7592互惠点对，法线中位夹角约10.06/8.58°，互惠y/z谱比.677–.837，未见该投影单方向近零表现，但不认证物理正确。固定02局部诊断收束，下一策略为结构关联歧义的受控可辨识性与弃权验证；不增加旧ICP迭代或调门控。0模型/训练/生产改动，UNRESOLVED/PAUSED及来源/旧停止保持。一次聚焦RAP-main提交，不推送。

[报告](docs/maintenance/2026-11-10/dpa3-support-01/REPORT_CN.md)。DPA4仅草案未执行，旧入口已备份，原封存/失败保持。

---

# 2026-11-07：历史提交与审计

所有者已明确授权提交、同步现有历史，并审计源码、实验结果与创新策略。历史入库范围及原AGENTS见[本次记录](docs/versioning/2026-11-07/README.md)。本轮允许Git新提交与指定目标同步；原科学停止、来源缺口和原始产物保全继续有效。审计与头脑风暴不自动启动新训练或恢复旧实验。

---

# RAP-main：当前核心上下文

更新：2026-11-06，Asia/Shanghai。**A8：文件、环境与有界模型I/O验收通过；完整训练/恢复链仍有保留项。** 完整资产及全部历史常驻所租AutoDL，原A5/A7包与本地原件保留；真实收据见[A8报告](docs/maintenance/2026-11-06/autodl-migration-01/REPORT_CN.md)及[服务器入口](docs/migration/AUTODL.md)。研究UNRESOLVED、论文PAUSED；不把单对示例I/O写成科学复现或可完整训练。

## 已确认的目标

完整研究资产纳入迁移：RAP-main、RAP-SLAM、报告、Datasets、外部 Codex 记录和组会。服务器已选 AutoDL，用于继续研究与训练；**全部实验历史随迁并常驻服务器**。先保留两个代码仓库边界。当前维护文档中文为主，代码标识/注释英文，历史原文保留。

阅读顺序：

1. [当前状态](docs/CURRENT_STATE.md) / [机器状态](docs/CURRENT_STATE.json)：迁移阶段、研究边界和未决项。
2. [项目约定](docs/CONVENTIONS.md)：坐标、路径、精度、记录和保全要求。
3. [迁移入口](docs/migration/README.md) / [执行计划](docs/migration/PLAN.md)。
   当前实际迁移见[AutoDL运行说明](docs/migration/AUTODL.md)和[A8授权](docs/maintenance/2026-11-06/autodl-migration-01/AUTHORITY.md)。
4. [实验索引](docs/experiments/README.md)、[档案目录](docs/experiments/CATALOG.md)和[保全缺口](docs/experiments/GAPS.md)。
5. [代码职责](docs/code/README.md) / [运行说明](docs/code/RUNNING.md) / [A3 记录](docs/maintenance/2026-11-04/code-paths-01/REPORT_CN.md)。
6. [环境入口](docs/environment/README.md)、[搭建顺序](docs/environment/SETUP.md)、[训练缺口](docs/environment/TRAINING.md)和[A4 记录](docs/maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)。
7. [资产入口](docs/assets/README.md)、[数据覆盖](docs/assets/DATASETS.md)、[分包/恢复](docs/assets/PACKAGING.md)和[A5 记录](docs/maintenance/2026-11-04/assets-package-01/REPORT_CN.md)。
8. [组会/报告](docs/meetings/README.md)、[成品与版本](docs/meetings/CATALOG.md)、[制作说明](docs/meetings/BUILDING.md)和[A6记录](docs/maintenance/2026-11-04/meeting-lineage-01/REPORT_CN.md)。
9. [最终交付](docs/migration/DELIVERY.md)、[恢复说明](docs/migration/RESTORE.md)、[迁移交接](docs/migration/HANDOFF.md)和[A7记录](docs/maintenance/2026-11-04/delivery-restore-01/REPORT_CN.md)。
10. [A1 审计](docs/maintenance/2026-11-03/migration-audit-01/REPORT_CN.md)及[A2 整理记录](docs/maintenance/2026-11-03/context-index-01/REPORT_CN.md)。

## 必须保留的研究状态

- 研究 **UNRESOLVED**，论文 **PAUSED**；E0/E0-H1 工程正面记录与比较范围限制保留，不声称新 RAP 方法或普遍优势。
- GCG1 保持 37 正确/8 错误接受，无正确增益。official MAC 数值未准入、未运行；普通实现或 PGC1 不能冒充官方比较。
- PGC1 保持原 64 actions/第八对停止，七份部分准确率未解释读取。索引对 portable_graph_20261031 两处档案仅登记元数据，不重试或扩大原上限。
- SSC1 保持 oldunique00/08=18/3、失败于各至少 5 的固定筛选，评分/训练前停止；不得用阈值、窗口、SIFT、视差或协方差救活。原 46.406s 监督失败、135 个字节复用地图、138 个缺失项续算、原时钟/累计上限及失败峰值限制保留。
- EIA1/SRA1 的来源/字节核对不提供身份独立性、物理基线或科学增益认证。SAC1 的 8 supported/零残差/rank6 仍有 30m 别名歧义；MCV1 的计数和局部满秩不是安全/协方差证书。
- 所有旧失败、停止、预算、原始/校正帧区别及来源/物理参考限制保留。raw/OXTS 包未获新的来源认证；Computer Use 原 URL-enforcement 停止不自动恢复。
- 上轮账户最后拒绝观察是历史，不是本轮查询或 5h 耗尽证明。没有自动重置续跑、排队或后台研究授权。

## 工程边界与保全

- A8 的服务器迁移授权覆盖此前阶段“不安装/不传输/未选定服务器”的限制：允许仅向指定 AutoDL 传输已登记完整资产、恢复独立工作区、安装独立环境并做有限迁移验收。旧阶段未执行事项仍按历史原文保留；科学停止、无新研究/完整训练、保留本地原件与Git历史等边界不变。A7当前81个权威文件已在A8 before备份并逐哈希匹配，凭据不落盘。
- A1 已校验 106,767 个普通文件与 27 个链接，建立 106,794 行处置表，保全两个 Git 原目录和 2,955 条源码路径，恢复 17 个旧版本。五个旧源码哈希、一个旧 AGENTS 中间版本和外部动态闭包仍有保留项；原 72 条 Linux 环境引用已在 A4 逐条精确匹配，PyTorch3D 原构建提交与目标重建仍未闭合；不能用现代码或索引掩盖缺口。
- A3 新增标准库启动器 scripts/run.py（默认仅命令计划；--check 只验路径，--execute 才执行），支持 sample/demo/features/slam/evaluate。路径优先级 CLI > JSON > 环境 > 布局；新输出拒绝复用。SLAM CLI 独立解析，权重可显式配置；原数值计算与 55 个非路径参数保持。A4 已查明缺少受维护训练入口/完整根配置、Muon 及训练/恢复证据；目标环境和独立训练入口实现仍待验收。
- 当前维护工具是 query_experiments.py、index_code_entries.py 和 render_current_state.py；其它历史研究/封存/账户脚本不在默认分派。906 条代码/配置角色索引保留旧路径和一份历史语法错误，未擅自修复封存工具。可选 app.py/ROS2 不在离线入口合同内。scripts/environment、scripts/migration 的分包/交付恢复工具和 scripts/meetings/materials.py 均为显式维护入口，不进入五项推理/SLAM任务默认分派。
- A5基础快照当时排除A5自身和包目录；A7增量已承接A5/A6资料，最终控制层承接A7当前入口及审计。A7项目层完整恢复后逐文件新读复核，19份替换前基础字节另存历史；25内部链接在新恢复树改相对目标并验证，2个人junction不跟随/不重建。原27链接缓冲区保留；四份EPUB单列非研究，原件不删。
- A6 不将旧 final/目录日期当作唯一终稿：9月21日实际9页与旧8页声明不同；11月1日5页编辑源与现存4页导出不绑定。历史材料原字节保留，两个node_modules junction不跟随；72文件便携副本只做复制/语法/模块导入验证，未运行旧重算或新Office构建。参考Word已找到精确别名，参考PDF b6c209ac… 原字节未恢复。
- A7仅一次有界WSL文件系统维护：恢复新副本内相对链接、运行/tmp固定权限夹具，已恢复Stopped。五项离线启动器在新树从其它cwd做--check，未导入数值/模型模块、不创建任务输出；不把路径检查、权限夹具或本地恢复写成Linux服务器/GPU/训练验收。包与恢复副本仍同盘，不提供异地或服务器驻留证明。
- `RAPBackend.register(a,b)` 为 b→a。保持归一化、RNG、点数/特征条件、坐标/校准、精度作用域、SDPA 与延迟导入；不将文档约定统一误作改动冻结参数。
- 保留现有用户未提交修改和仓库边界；不改变 Git 索引/提交/历史。当前导航页先备份再更新；旧协议、seal/freeze、原始结果、失败和验证程序按字节保留，历史路径由映射解释。
- A4 按计划四次短暂启动 WSL（元数据、CPU 检查、构建日志/脚本补查），均已恢复停止；17 项必需 CPU 导入/配置/基础算子检查通过，Muon 训练依赖缺失。未初始化 CUDA、实例化模型、加载 checkpoint/数据或训练。没有安装、软件包下载、部署或对外发送；不自动删除 WSL 镜像、旧备份、数据、失败记录、特殊链接或身份不明文件。缓存/重复项只是后续候选。

## 历史与证明

精简前项目 AGENTS 的完整 452,440 字节见[原件](docs/maintenance/2026-11-03/migration-preflight-01/before/RAP-main.AGENTS.md)。本次替换前入口、父级 AGENTS、两仓库 README 和旧维护首页见 [A2 before](docs/maintenance/2026-11-03/context-index-01/before)。

父级工作区与 RAP-SLAM AGENTS 只补充各层职责；详细当前状态由统一状态页承担。历史 ACTIVE/next 只代表原时点，不是当前自动任务。A2/A3/A4/A5/A6/A7 接续证明保全现行入口的旧版本；A3 修改前源码和文档见 [A3 before](docs/maintenance/2026-11-04/code-paths-01/before)。旧验证器不改写，原科学封存、未恢复版本与完整历史均保持。
