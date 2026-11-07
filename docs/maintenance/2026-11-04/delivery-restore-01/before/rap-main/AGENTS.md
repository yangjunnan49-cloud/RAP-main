# RAP-main：当前核心上下文

更新：2026-11-04，Asia/Shanghai。所有者当前任务为迁移前工程整理；A0–A5 已完成各自审计/整理范围，**A6 已完成组会/报告目录、版本身份、图表字节关联和便携制作准备：10组、1,975文件，6份旧交付哈希匹配。版本差异、1份参考PDF缺口和新导出验收保留。下一步 A7：最终增量、交付布局和恢复验收；服务器未选定。** A4 的目标环境/训练、A7 的完整恢复/链接/权限与最终增量仍有保留项。 不将审计完成写成训练就绪或服务器迁移完成。

## 已确认的目标

完整研究资产纳入迁移：RAP-main、RAP-SLAM、报告、Datasets、外部 Codex 记录和组会。服务器用于继续研究与训练，尚未选定；**全部实验历史随迁并常驻服务器**。先保留两个代码仓库边界。当前维护文档中文为主，代码标识/注释英文，历史原文保留。

阅读顺序：

1. [当前状态](docs/CURRENT_STATE.md) / [机器状态](docs/CURRENT_STATE.json)：迁移阶段、研究边界和未决项。
2. [项目约定](docs/CONVENTIONS.md)：坐标、路径、精度、记录和保全要求。
3. [迁移入口](docs/migration/README.md) / [执行计划](docs/migration/PLAN.md)。
4. [实验索引](docs/experiments/README.md)、[档案目录](docs/experiments/CATALOG.md)和[保全缺口](docs/experiments/GAPS.md)。
5. [代码职责](docs/code/README.md) / [运行说明](docs/code/RUNNING.md) / [A3 记录](docs/maintenance/2026-11-04/code-paths-01/REPORT_CN.md)。
6. [环境入口](docs/environment/README.md)、[搭建顺序](docs/environment/SETUP.md)、[训练缺口](docs/environment/TRAINING.md)和[A4 记录](docs/maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)。
7. [资产入口](docs/assets/README.md)、[数据覆盖](docs/assets/DATASETS.md)、[分包/恢复](docs/assets/PACKAGING.md)和[A5 记录](docs/maintenance/2026-11-04/assets-package-01/REPORT_CN.md)。
8. [组会/报告](docs/meetings/README.md)、[成品与版本](docs/meetings/CATALOG.md)、[制作说明](docs/meetings/BUILDING.md)和[A6记录](docs/maintenance/2026-11-04/meeting-lineage-01/REPORT_CN.md)。
9. [A1 审计](docs/maintenance/2026-11-03/migration-audit-01/REPORT_CN.md)及[A2 整理记录](docs/maintenance/2026-11-03/context-index-01/REPORT_CN.md)。

## 必须保留的研究状态

- 研究 **UNRESOLVED**，论文 **PAUSED**；E0/E0-H1 工程正面记录与比较范围限制保留，不声称新 RAP 方法或普遍优势。
- GCG1 保持 37 正确/8 错误接受，无正确增益。official MAC 数值未准入、未运行；普通实现或 PGC1 不能冒充官方比较。
- PGC1 保持原 64 actions/第八对停止，七份部分准确率未解释读取。索引对 portable_graph_20261031 两处档案仅登记元数据，不重试或扩大原上限。
- SSC1 保持 oldunique00/08=18/3、失败于各至少 5 的固定筛选，评分/训练前停止；不得用阈值、窗口、SIFT、视差或协方差救活。原 46.406s 监督失败、135 个字节复用地图、138 个缺失项续算、原时钟/累计上限及失败峰值限制保留。
- EIA1/SRA1 的来源/字节核对不提供身份独立性、物理基线或科学增益认证。SAC1 的 8 supported/零残差/rank6 仍有 30m 别名歧义；MCV1 的计数和局部满秩不是安全/协方差证书。
- 所有旧失败、停止、预算、原始/校正帧区别及来源/物理参考限制保留。raw/OXTS 包未获新的来源认证；Computer Use 原 URL-enforcement 停止不自动恢复。
- 上轮账户最后拒绝观察是历史，不是本轮查询或 5h 耗尽证明。没有自动重置续跑、排队或后台研究授权。

## 工程边界与保全

- A1 已校验 106,767 个普通文件与 27 个链接，建立 106,794 行处置表，保全两个 Git 原目录和 2,955 条源码路径，恢复 17 个旧版本。五个旧源码哈希、一个旧 AGENTS 中间版本和外部动态闭包仍有保留项；原 72 条 Linux 环境引用已在 A4 逐条精确匹配，PyTorch3D 原构建提交与目标重建仍未闭合；不能用现代码或索引掩盖缺口。
- A3 新增标准库启动器 scripts/run.py（默认仅命令计划；--check 只验路径，--execute 才执行），支持 sample/demo/features/slam/evaluate。路径优先级 CLI > JSON > 环境 > 布局；新输出拒绝复用。SLAM CLI 独立解析，权重可显式配置；原数值计算与 55 个非路径参数保持。A4 已查明缺少受维护训练入口/完整根配置、Muon 及训练/恢复证据；目标环境和独立训练入口实现仍待验收。
- 当前维护工具是 query_experiments.py、index_code_entries.py 和 render_current_state.py；其它历史研究/封存/账户脚本不在默认分派。905 条代码/配置角色索引保留旧路径和一份历史语法错误，未擅自修复封存工具。可选 app.py/ROS2 不在离线入口合同内。scripts/environment、scripts/migration/content_bundle.py 和 scripts/meetings/materials.py 均为显式维护入口，不进入五项推理/SLAM任务默认分派。
- A5 基础快照排除本次 phase 与包目录自身；A5 控制面、后续 A6 成品和当前入口最终增量由 A7 汇总。27 个链接原缓冲区已 fresh 核对，不跟随 junction；只做过18份真实普通文件恢复抽查，未声称全量目标恢复或数据来源/训练资格认证。四份 EPUB 非研究保留，不删除。
- A6 不将旧 final/目录日期当作唯一终稿：9月21日实际9页与旧8页声明不同；11月1日5页编辑源与现存4页导出不绑定。历史材料原字节保留，两个node_modules junction不跟随；72文件便携副本只做复制/语法/模块导入验证，未运行旧重算或新Office构建。参考Word已找到精确别名，参考PDF b6c209ac… 原字节未恢复。
- `RAPBackend.register(a,b)` 为 b→a。保持归一化、RNG、点数/特征条件、坐标/校准、精度作用域、SDPA 与延迟导入；不将文档约定统一误作改动冻结参数。
- 保留现有用户未提交修改和仓库边界；不改变 Git 索引/提交/历史。当前导航页先备份再更新；旧协议、seal/freeze、原始结果、失败和验证程序按字节保留，历史路径由映射解释。
- A4 按计划四次短暂启动 WSL（元数据、CPU 检查、构建日志/脚本补查），均已恢复停止；17 项必需 CPU 导入/配置/基础算子检查通过，Muon 训练依赖缺失。未初始化 CUDA、实例化模型、加载 checkpoint/数据或训练。没有安装、软件包下载、部署或对外发送；不自动删除 WSL 镜像、旧备份、数据、失败记录、特殊链接或身份不明文件。缓存/重复项只是后续候选。

## 历史与证明

精简前项目 AGENTS 的完整 452,440 字节见[原件](docs/maintenance/2026-11-03/migration-preflight-01/before/RAP-main.AGENTS.md)。本次替换前入口、父级 AGENTS、两仓库 README 和旧维护首页见 [A2 before](docs/maintenance/2026-11-03/context-index-01/before)。

父级工作区与 RAP-SLAM AGENTS 只补充各层职责；详细当前状态由统一状态页承担。历史 ACTIVE/next 只代表原时点，不是当前自动任务。A2/A3/A4/A5/A6 接续证明保全现行入口的旧版本；A3 修改前源码和文档见 [A3 before](docs/maintenance/2026-11-04/code-paths-01/before)。旧验证器不改写，原科学封存、未恢复版本与完整历史均保持。
