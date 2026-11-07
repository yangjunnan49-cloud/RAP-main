# A7 执行接续（过程记录，以最终 STATUS/CHECKS/seal 为准）

用户在 A6 封存后要求“执行下一步”，当前执行 A7 本地最终交付/恢复；服务器尚未选定。不部署/购买/外传/安装/下载，不运行模型/GPU/科学数组/训练/旧研究。所有旧研究停止、预算及来源缺口保持。原件不移动删除，原 Git 索引/HEAD/分支不改。

阶段 docs/maintenance/2026-11-04/delivery-restore-01，原 77 当前权威已在 before 保全；A6 seal bafd69136024559a408d48f9af3b127582ea723eda5dbf54d62e371d55cc47fc。

## 已完成

- BASELINE.json，LINK_CAPABILITY 原生 Windows 符号链接权限不足；只读 WSL 查询经 require_escalated 成功，Ubuntu-24.04 为 Stopped。尚未启动本轮 WSL。A7 文件系统链接/模式验收在 PROJECT_RESTORE 完成后，用 run_posix_links.py（需 escalate）单次有界启动，只在新恢复树写25相对链接及/tmp固定小权限夹具，finally terminate恢复Stopped；不碰原链接、模型或GPU。2个人node_modules junction不重建，运行时明确重建依赖。
- 项目冻结为 A5 基础 + 最新到 A6 的增量，排除本 A7 phase 及 .maintenance-archive/migration 全部已知输出。112682普通文件/135095691259bytes，5285目录/27链接；1072增量（1053新+19当前字节变化）186134097逻辑bytes；所有A5源身份保留。108733复用A5字节验证+匹配元数据，3949 freshhash。PROJECT_FILES/DIRECTORIES/LINKS、LINK_PLAN/PERMISSIONS已落盘。Git mode由当前索引精确匹配A1保存索引+对应tracked.stdout获得，两仓库共311项全部100644，不猜扩展名执行位。freeze_project尾部外部Git命令权限失败，finish_freeze已保留并完成，未重做源清单。
- 包目录 E:/githouse/RAP-main/.maintenance-archive/migration/A7-20261104：PROJECT.json SHA711bd1798c01955e9169d950808ebe5e973ca000e058cea2ab618f885da23b1c；delta一卷144814080bytes/833对象/144164228独特内容，完整freshsource1072+独立读回通过，SHA d35a8e56f59d93de2661193298f146bcfd6740dd778de239ef040a8d4333b479。基础包仍原 A5-20261104（30卷/111629源/98854对象）。项目层明确尚不含 A7 当前文档/工具和审计证据，最终将独立控制层纳入，避免自引用。
- 当前维护工具仅暂存 updates/scripts/migration/delivery.py，未发布。恢复核心最初代码在 used/delivery.py（长路径失败原件）、正在运行的修正版 used/delivery-longpath.py。当前staged工具后来只加 evidence/CLI等函数；应比较restore_layer/check_files核心AST一致，勿覆盖used版本。合成9测试通过，含双层恢复/旧版保全、Unicode/空文件、坏卷、长路径、拒绝覆盖/穿越/错误overlay、证据tar尾部损坏拒绝修改控制面。test_delivery.py自建fixture清理用扩展路径并校验范围。

## 正在进行（不要重复启动）

真实基础全恢复 exec session **86973**，driver restore_base.py。目标 **.maintenance-archive/migration/A7-restore-20261104-02/workspace**。正在逐卷恢复所有源身份，卷和唯一内容SHA在同一遍读完整核对，重复源分别物理复制/验证。进度 BASE_RESTORE_PROGRESS.jsonl，成功才写BASE_RESTORE.json。首个恢复目录 A7-restore-20261104 保留（仅建目录时长路径失败，没有进入payload），不复用/删除。长路径修正版使用 native_absolute Windows \\?\ 路径。

上一观察完成第6卷/29779物理文件/34792441632逻辑bytes。基础恢复完后，手动运行 **restore_delta.py**：导入不可变used/delivery-longpath.py，注册overlay1072，19旧版本改存新恢复树archives/source-versions/A5；随后重新按字节读取整个112682文件树135095691259bytes+旧版本19，PROJECT_RESTORE成功才写收据。此后运行有限WSL链接/模式验收，保持停止；再作恢复后CLI --check/标准库测试，无模型。

## 最终收束设计（尚待实现/完成）

1. 项目层先完整恢复/全字节复核，最后 A7 控制层包含所有新当前入口/文档和全部本phase证据。不要把包或恢复输出纳入源枚举。原A5/A6 seals不改。
2. 基础/增量恢复期间，准备 docs/migration/DELIVERY.md、RESTORE.md、HANDOFF.md和最终状态/AGENTS导航，但目前还未发布；项目层冻结时仍为A6，因此A7更新要通过最终控制快照送达。新 current delivery.py 自动归现有scripts/migration角色，无需改旧分类器或生产代码；预计原905不变+1新tool=906代码记录。
3. 全部数据/CLI/链接验收通过后，发布A7当前文档/新tool、父级/SLAM/报告README（外部写需guarded require_escalated）。维护before77 -> authority预计81（77+1工具+3新docs）并快照after；实际按最终文件数。更新当前状态为本地交付完成/目标环境和服务器保留，research对象原样，next为服务器确定后验收；不假称整体迁移完成。记录A4训练/环境/原P3D提交、来源、5source+1AGENTS、A6版本/参考PDF/新导出、未导出Linux环境/wheel与POSIX目标权限保留。
4. 当前改动及晚到Git元数据在最终控制快照装入：CURRENT_DOCUMENT_SNAPSHOTS.json + LATE_GIT_SNAPSHOTS.json（late .git只捕获新增/字节变化，原索引HEAD应保持，记录不归因）。先在恢复树按登记旧SHA做控制更新，旧版留archives/source-versions/A7-control；核对所有当前快照字节与元数据，旧项目层无需再读135GB。项目全读后仅这些已登记小范围改变。
5. A7报告、CHECKS、AUTHORITY_PROOF、current snapshots、STATUS等齐备后封存phase（禁止包含包/恢复树）；seal本身不在files自哈希中。
6. 封存后才把phase完整文件（含seal）做独立PAX evidence.tar，EVIDENCE_MANIFEST逐文件SHA；MASTER DELIVERY.json绑定PROJECT、evidence tar/manifest、seal和最终 workspace 文件表SHA。该封存后步骤的收据放包目录外层，不能再写回已sealphase。维护工具已写 install_evidence：白名单原字节解包、全tarSHA、按current+lateGit快照带旧SHA守卫更新当前入口；本机若已提前应用sameSHA可验证跳过。
7. 调 install_evidence 在本机恢复树补入完整phase证据（当前快照若同SHA跳过）；生成 DELIVERY_FILES.jsonl 全最终映射（项目源+版本存档+phase+当前控制+晚Git），最终收据绑定最后MASTERsha。包仍与原件同盘，本地恢复树保留；非异地或服务器驻留证明。

## 工具和注意

Python C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe，-X utf8 -I -B；PS stdin只用ASCII代码，中文文件用apply_patch。批量独立工具Promise.allSettled，依赖顺序不并行；不要spread工具string或打印巨大JSONL。每60秒左右commentary更新，不要busy polling。当前无子代理（禁止主动委派）、无goal、无skill。

长路径在Windows恢复目标必须用native_absolute；fixtures有一次清理失败已按解析绝对路径和已知测试字节清掉，仅自建fixture，原件不变。VALIDATION_FAILURE_01..03及attempt01/used原件保留。不要把root BASE_RESTORE_FAILURE（首轮历史失败）误当当前86973失败。

## 继续后的最新状态（覆盖前文进行中编号）

- 用户于客户端2026-11-05再次“继续”，继续同一A7。当前文档日期应取客户端2026-11-05；prepare_current已固定该日期，原始收据UTC保持观察值。
- **86973已成功完成**：111629文件/134910234709bytes，98854对象/30卷SHA全通过；BASE_RESTORE.json存在passed，used_tool_sha39873104d5e257be988dfe9f8a9b0d5527a985ee62283c7518bf8c2365334d0f。
- **60951正在运行restore_delta.py**：1072/833/1卷增量已恢复，DELTA_RESTORE.json已保存19旧版；正在真正重新读取112682文件/135095691259bytes，最近输出20000文件/21496075171bytes。进度PROJECT_RESTORE_PROGRESS.jsonl；成功才写PROJECT_RESTORE.json。不要重复启动。
- staged delivery.py 已在used核心基础上增加apply_permissions、apply_control_snapshots、install_evidence、check_delivery_tree和CLI。9项合成测试通过。source core restore_layer/check_files/mapped等应与used-longpath逐函数AST一致；restore_project新增权限和额外控制验证，不能按全文件SHA冒充同版本。
- 3份新文档在updates/docs/migration/{DELIVERY,RESTORE,HANDOFF}.md。**当前source尚未发布A7**，仍A6；prepare_current.py --preflight已通过，实际main有PROJECT_RESTORE/POSIX_LINK/WSL/RELOCATED全部pass守卫。项目层冻结时旧A6上下文正确；A7最终更新经控制快照交付。
- 后续手动顺序：60951成功 -> run_posix_links.py(require_escalated；先确认只有本次WSL文件系统操作，finally恢复Stopped) -> check_relocated.py(5任务--check+19左右stdlibtests+2Git只读) -> prepare_current.py -> 复制A6 guarded install_external.py到本phase，实际外部更新需escalate，ROOTS包括workspace-root/rap-slam/reports；render_current_state.py/index_code_entries.py(预计906)；复制已发布delivery.py到package/tools/delivery.py -> prepare_controls.py(81当前权威after、晚Git新增快照、LOCAL_CONTROL_RESTORE) -> verify_a7.py -> seal_a7.py -> finalize_delivery.py。最后一步写包目录DELIVERY/EVIDENCE_MANIFEST/evidence.tar/DELIVERY_FILES/EVIDENCE_RESTORE/FINAL_ACCEPTANCE，不写已sealphase；会补齐恢复树phase并核对最终普通文件集合+25reparse，最终user答复前必须FINAL_ACCEPTANCE passed。
- verify_a7.py/REPORT_CN.md/seal_a7.py/finalize_delivery.py均已写好但还未执行，可能需依真实结果修正，不可提前标完成。A7封存phase STATUS故意说明证据tar/master finalization follows seal，最终完成以包内FINAL_ACCEPTANCE为准。

## 封存接续

上方为过程记录，已完成项目全量恢复/新读复核、链接/权限小夹具、路径与当前控制接续；原进行中动作不再生效。最终阶段状态见STATUS/CHECKS/seal。封存后还要在包目录生成并验证evidence.tar、最终DELIVERY/文件表和FINAL_ACCEPTANCE，不能回写本phase；最终交付以包内FINAL_ACCEPTANCE为准。真实目标/服务器/训练/来源版本保留项继续有效，无自动研究授权。
