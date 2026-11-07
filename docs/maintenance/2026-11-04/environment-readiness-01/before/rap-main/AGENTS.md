# RAP-main：当前核心上下文

更新：2026-11-04，Asia/Shanghai。所有者当前任务为迁移前工程整理；A0–A2 已完成各自范围，**A3 已完成离线入口、代码职责和路径配置整理，并通过标准库测试、参数及数值源码保持检查。下一步 A4：环境依赖与完整训练/恢复链审计。** A3 未运行模型，目标环境数值验收仍待 A4。

## 已确认的目标

完整研究资产纳入迁移：RAP-main、RAP-SLAM、报告、Datasets、外部 Codex 记录和组会。服务器用于继续研究与训练，尚未选定；**全部实验历史随迁并常驻服务器**。先保留两个代码仓库边界。当前维护文档中文为主，代码标识/注释英文，历史原文保留。

阅读顺序：

1. [当前状态](docs/CURRENT_STATE.md) / [机器状态](docs/CURRENT_STATE.json)：迁移阶段、研究边界和未决项。
2. [项目约定](docs/CONVENTIONS.md)：坐标、路径、精度、记录和保全要求。
3. [迁移入口](docs/migration/README.md) / [执行计划](docs/migration/PLAN.md)。
4. [实验索引](docs/experiments/README.md)、[档案目录](docs/experiments/CATALOG.md)和[保全缺口](docs/experiments/GAPS.md)。
5. [代码职责](docs/code/README.md) / [运行说明](docs/code/RUNNING.md) / [A3 记录](docs/maintenance/2026-11-04/code-paths-01/REPORT_CN.md)。
6. [A1 审计](docs/maintenance/2026-11-03/migration-audit-01/REPORT_CN.md)及[A2 整理记录](docs/maintenance/2026-11-03/context-index-01/REPORT_CN.md)。

## 必须保留的研究状态

- 研究 **UNRESOLVED**，论文 **PAUSED**；E0/E0-H1 工程正面记录与比较范围限制保留，不声称新 RAP 方法或普遍优势。
- GCG1 保持 37 正确/8 错误接受，无正确增益。official MAC 数值未准入、未运行；普通实现或 PGC1 不能冒充官方比较。
- PGC1 保持原 64 actions/第八对停止，七份部分准确率未解释读取。索引对 portable_graph_20261031 两处档案仅登记元数据，不重试或扩大原上限。
- SSC1 保持 oldunique00/08=18/3、失败于各至少 5 的固定筛选，评分/训练前停止；不得用阈值、窗口、SIFT、视差或协方差救活。原 46.406s 监督失败、135 个字节复用地图、138 个缺失项续算、原时钟/累计上限及失败峰值限制保留。
- EIA1/SRA1 的来源/字节核对不提供身份独立性、物理基线或科学增益认证。SAC1 的 8 supported/零残差/rank6 仍有 30m 别名歧义；MCV1 的计数和局部满秩不是安全/协方差证书。
- 所有旧失败、停止、预算、原始/校正帧区别及来源/物理参考限制保留。raw/OXTS 包未获新的来源认证；Computer Use 原 URL-enforcement 停止不自动恢复。
- 上轮账户最后拒绝观察是历史，不是本轮查询或 5h 耗尽证明。没有自动重置续跑、排队或后台研究授权。

## 工程边界与保全

- A1 已校验 106,767 个普通文件与 27 个链接，建立 106,794 行处置表，保全两个 Git 原目录和 2,955 条源码路径，恢复 17 个旧版本。五个旧源码哈希、一个旧 AGENTS 中间版本、72 条 Linux 环境引用和外部动态闭包仍有保留项；不能用现代码或索引掩盖缺口。
- A3 新增标准库启动器 scripts/run.py（默认仅命令计划；--check 只验路径，--execute 才执行），支持 sample/demo/features/slam/evaluate。路径优先级 CLI > JSON > 环境 > 布局；新输出拒绝复用。SLAM CLI 独立解析，权重可显式配置；原数值计算与 55 个非路径参数保持。完整训练/恢复链及目标环境仍未验收，归 A4。
- 当前维护工具是 query_experiments.py、index_code_entries.py 和 render_current_state.py；其它历史研究/封存/账户脚本不在默认分派。896 条代码/配置角色索引保留旧路径和一份历史语法错误，未擅自修复封存工具。可选 app.py/ROS2 不在离线入口合同内。
- `RAPBackend.register(a,b)` 为 b→a。保持归一化、RNG、点数/特征条件、坐标/校准、精度作用域、SDPA 与延迟导入；不将文档约定统一误作改动冻结参数。
- 保留现有用户未提交修改和仓库边界；不改变 Git 索引/提交/历史。当前导航页先备份再更新；旧协议、seal/freeze、原始结果、失败和验证程序按字节保留，历史路径由映射解释。
- 本轮不启动 WSL/GPU/模型/训练/研究实验，不安装、下载、部署或对外发送；不自动删除 WSL 镜像、旧备份、数据、失败记录、特殊链接或身份不明文件。缓存/重复项只是后续候选。

## 历史与证明

精简前项目 AGENTS 的完整 452,440 字节见[原件](docs/maintenance/2026-11-03/migration-preflight-01/before/RAP-main.AGENTS.md)。本次替换前入口、父级 AGENTS、两仓库 README 和旧维护首页见 [A2 before](docs/maintenance/2026-11-03/context-index-01/before)。

父级工作区与 RAP-SLAM AGENTS 只补充各层职责；详细当前状态由统一状态页承担。历史 ACTIVE/next 只代表原时点，不是当前自动任务。A2/A3 接续证明保全现行入口的旧版本；A3 修改前源码和文档见 [A3 before](docs/maintenance/2026-11-04/code-paths-01/before)。旧验证器不改写，原科学封存、未恢复版本与完整历史均保持。
