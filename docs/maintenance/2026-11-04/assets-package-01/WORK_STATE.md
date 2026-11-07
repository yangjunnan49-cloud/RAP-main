# A5 工作接续（进行中）

- 用户在 A4 封存后说“继续”，当前正在执行 A5，尚未完成或封存。
- A4 交付：docs/maintenance/2026-11-04/environment-readiness-01；seal 1443 files / 370128762 bytes，SHA256 9768cbd7445b12f6df84a525cbc0c586cb2dd3d2bd5b66096c5f9cca8ef1ccc3。当前权威 63 文件；903 代码/配置条目。72 Linux 旧哈希全部匹配；17 CPU 必需检查通过；Muon 缺失。四次 WSL 维护均恢复停止，无模型/训练/GPU context、无安装/包下载。原 P3D Git 提交未恢复，已保全两份构建日志及原脚本；失败 fetch object 不充当成功构建提交。A4 目标/训练保留项继续有效。
- A5 范围见 AUTHORITY.md：六个 Windows 可见根，全部历史常驻服务器；不删除/移动，不运行 WSL/GPU/模型/训练。PGC1 只元数据/原字节打包，不解释部分结果。保留 5 源码哈希和 1 旧上下文缺口、全部旧研究停止/预算/来源限制。
- capture_assets.py 正在生成 SOURCE_FILES/DIRECTORIES/LINKS 与 BASELINE；tool exec session 7653，首个调用尚未完成。先等结果，不并发重跑。不将包目录与本 A5 phase 纳入自身。
- 计划包目的地：.maintenance-archive/migration/A5-20261104（原先不存在，已被 Git 现有规则 ignored，不改 .gitignore）。E 盘可用约 520GB，原六根 A1 普通文件约 130.8GB；唯一内容约再减 9.8GB重复量，另含 A1-A4 新资产。包拟为标准库 tar 分卷，文件内容 SHA256 去重，不改变原路径身份；每源文件在打包阶段按字节再次核对，全部 tar payload 与卷校验独立验证。A7 再做完整目标恢复/特殊链接和最终增量。
- A1 HASHES/ASSET_LEDGER 可复用元数据匹配的旧 hash，随后每个物理文件（含重复副本）都要在包构建中重新读字节核对；每个唯一对象只存一份。缓存旧 hash 不冒充本轮全部新读。32GiB? 当前拟 4GiB 卷，最大新文件约 A1 Git tar 2.9GB，小于卷限；实际以 inventory 为准。
- A1 六根已审计 106767 普通文件+27 reparse，2 junction 不跟随、25 LX 链接原元数据保留。ROOT_MAPPING 中 workspace-root 只非递归根文件，避免重扫其它根。
- 已见数据：Datasets/data_odometry_velodyne/dataset 约 84.78GB/43607文件；Oxford Spires 只有 gt 5文件（扫描完整性不可标齐）；Datasets/part2 4份EPUB 非研究待判定保留（不读内容、不删除）；RAP-SLAM/data 约4.22GB；weights 当前仅 mini_spinnet_t.pth / rap_model_10.ckpt / rap_model_12.ckpt。raw/OXTS 无新认证。
- A5 还未实现分卷工具/恢复工具、数据/模型/历史清单和完整校验；不要把计划记成完成。包输出不进源枚举，A5 控制面和后续 A6 当前文档由 A7 最终增量承接，明确 freeze 语义。
- 没有子代理（当前禁止主动委派），没有 goal tool。Python 为 C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe；工具用 -I -B。PowerShell，读外部根可用；写父级/RAP-SLAM 文档需 require_escalated（A3/A4 已授权，自动审批均成功）。所有源码/导航先备份，保全旧 seal，不改 Git 索引/历史。

## 当前进度接续

- capture session 7653 已失败并保留：A1 HASHES 包含 reparse 行，首次只比较普通文件身份；已修正为 file/link 并集。修正 capture session 44613 已完成。BASELINE 和 SOURCE_FILES/DIRECTORIES/LINKS 都已落盘，111629普通文件/5141目录/27链接；逻辑134910234709 bytes，98854唯一内容/124999364971 bytes。当前权威63 before已保全。
- capture_links.py 已 fresh FSCTL 重读27原buffer，匹配A1，SOURCE_LINKS_RAW.json。没有启动WSL。
- 打包引擎在 updates/scripts/migration/content_bundle.py（尚未安装到当前scripts）。7项合成测试已通过（分卷边界、去重、Unicode/空文件恢复、坏卷、路径穿越、重复物理源被改且mtime不变、拒绝覆盖/控制清单篡改）。真实 build job session 21322 正在运行，目的地既定 ignored package folder。不得启动第二个 build或改其原源文件。新控制面只写本phase。构建逐一新读所有物理源字节（含重复），去重存98k SHA对象，卷上限4GiB；接着必须独立verify完整卷与对象哈希。
- build_asset_catalog.py 已生成517逻辑包、逐包成员manifest及111629行唯一主归属；DATASETS.json有45序列记录（Datasets22、下游Kitti22参考、POSS1），68个允许文本元数据读取；MODELS.json为3唯一weights、每份当前与旧快照两物理别名。无numpy/torch加载、无PGC1语义读取。POSS有4170bin两段3850..5268、6750..9500，pose/time各36924；Oxford5GT、0PCD；Datasets/part2 4EPUB隔离标签保留。
- SOURCE_CLAIMS.json记录3现有下载脚本的URL文本线索与POSS download_b.log历史2751/DONE，未联网或新认证。新README/PACKAGING草稿、render_asset_docs.py产出的DATASETS/MODELS在updates/docs/assets，还未发布。
- 剩余：等build，独立全卷verify并保存receipt，给517逻辑包关联对象/必需卷；对真实weights(3模型+2cache)/KITTI poses/外部历史小范围恢复验证，成功的自建scratch可以安全核对后清除(只清生成测试副本，不能删原件或失败证据)。安装pack工具、更新代码角色与当前AGENTS/状态/导航（必须在build读取原源结束之后修改被冻文件），维护before/接续证明；报告、总校验、seal A5，再提示下一步A6。A7完整目标恢复/链接/权限/最终A5-A6增量仍保留，A4训练/GPU/source commit缺口仍保留。

## 最终交付接续

A5 终验已通过；本文件上方为历史过程记录，其进行中/下一动作不再生效。最终状态以 STATUS.json、CHECKS.json 和 DELIVERY_SEAL.json 为准。111629 源文件新读、98854 对象/30卷全读回、517 逻辑包、18份真实恢复与7项合成测试通过；517处 Windows 换行摘要声明已纠正并留证。当前68权威文件与904代码索引已同步，下一步A6。A4训练/目标环境、来源缺口和A7全量链接/权限/最终增量继续保留；未启动WSL/GPU/研究或对外传输，无原件删除。
