# A6：组会/报告、版本来源与便携制作准备

2026-11-04，Asia/Shanghai。所有者指令“继续执行A6”，执行中再次指令“继续”。本阶段完成 10 组组会/报告材料的文件归属、旧交付身份、Office/PDF 结构、图表字节关联、历史来源与制作链整理，并建立不依赖个人缓存的当前准备入口。终稿版本差异、一份参考 PDF 原字节缺口及新构建/原生导出验收明确保留；原件不移动、不删改。

## 结果与入口

| 项目 | 结果 |
| --- | ---: |
| 来源目录范围 / 主题组 | 11 / 10 |
| 普通文件全字节核对 / 字节 | 1,975 / 2,902,199,121 |
| 与 A5 冻结清单精确匹配 | 全部 1,975 |
| 范围内链接，不跟随目标 | 20（18 个 LX，2 个 junction） |
| Office/PDF 只读结构检查 | 46（17 PPTX、8 DOCX、21 PDF） |
| 旧交付文件哈希匹配 | 6（3 期 PPTX/Word 配对） |
| 原生编辑源 / 活跃页面 | 4 / 47 |
| 嵌入媒体关系 / 有独立文件同字节别名 | 60 / 44 |
| 历史来源声明核对 | 59（57 原路径、1 字节别名、1 未恢复） |
| 静态制作/报告脚本检查 | 64；均未运行 |
| 真实便携制作副本 | 72 文件 / 17,121,135 字节 |
| 安全准备合成测试 | 6 项 |

新入口是[组会/报告](../../../meetings/README.md)、[按日期/版本目录](../../../meetings/CATALOG.md)、[制作说明](../../../meetings/BUILDING.md)和[保留项](../../../meetings/GAPS.md)。机器记录见 [CATALOG.json](CATALOG.json)、[FILES.jsonl](FILES.jsonl)、[结构](ARTIFACT_STRUCTURE.json)、[图表字节关系](FIGURE_BYTE_LINKS.json)、[静态脚本](AUTHORING_SCRIPTS.json)、[编辑源](EDITABLE_DECKS.json)与[历史来源](HISTORICAL_SOURCE_BINDINGS.json)。报告根新 README 提供统一入口，两个代码仓库边界保持。

原 A5 基础包已包含这些 1,975 份原件和全部历史，包括 benchmark、数据/派生数组、失败、旧版和 QA。A6 新控制面、便携副本与当前入口改动不在该基础快照内，必须在 A7 最终增量汇总；没有改写 A5 包或旧 seal。

## 成品身份与版本事实

9 月 30 日、10 月 11 日、10 月 18 日的 PPTX/Word 实际 SHA256 与各自 delivery_manifest、DELIVERY、DELIVERY_CHECKS 一致，分别为 6、5、12 个活跃幻灯片。Word 的历史页数/原生视觉验收仅引用原收据，本轮不拿 app.xml 页数字段替代实际分页检查。10 月 18 日报告于 10 月 20 日关闭交付，不认证实际开会时间。

9 月 21 日旧说明及生成器文案写 8 页，现有 PPTX 的 presentation.xml 活跃页序实际 9 页。保留文件和旧说法，不通过删页或改写历史来对齐。8 月两版演示各 12 页，小抄两页；缺少可信唯一终稿选择依据，均保留。早期无日期编辑源不补造日期。

11 月 1 日 `.pptd` 列出 5 个活跃页面，7 份 page 文件中的 `5_adapter`、`5_gaps` 未列入页序。`.borrow.json` 的旧 PPTX 摘要前缀 e25e2a14e76a 与当前四页 PPTX 的 e037dc4e6b79 不符，现存 PDF 也为四页；五页编辑源、新讲稿和旧导出分别登记，不给它们补造终稿对应。[VERSION_DISCREPANCIES.json](VERSION_DISCREPANCIES.json)记录差异。

## 图表与来源

只读解包并校验 ZIP CRC，按 presentation 关系解析活跃页序、备注、原生表/图关系和图片字节；PDF 检查页数及首页少量定位文字。没有更改任何成品或重算科学数值。60 条媒体关系中 44 条找到 A5 六根内同 SHA256 文件别名；其余 16 条媒体本身仍保存在 Office 包内，不能直接推断原图丢失，也不能认证图表的科学来源链完整。

59 条旧来源声明中，57 条原路径字节匹配。10 月 18 日旧脚本所指 Downloads Word 已不存在，但项目内 10 月 11 日 Word 的完整 SHA256 精确相同，登记为可用字节别名；不提供身份独立性。另一份旧参考 PDF 的完整期望哈希 b6c209ac65964ccd3235e64cb6853b6c07ae059382adf31b4bfa51d6b91f4147 未在 A5 可见六根发现，继续保留，不能以别的 Word QA PDF 或索引替代。

静态来源、图片哈希和标题不把历史研究结论升级为当前科学结论；图表数据/原始和校正坐标角色仍由各次原协议解释。没有解析点云、NumPy/模型/科学结果数组，未读取 PGC1 七份部分准确率，未重跑模型、配准、指标、绘图或训练。

## 可维护的当前准备流程

[materials.py](../../../../scripts/meetings/materials.py) 为显式标准库维护入口，支持 list、check、prepare。prepare 默认仅计划，--execute 仅在新目录生成已核验副本；拒绝覆盖、穿越、源 reparse、原历史目录内输出和哈希变化，不调用旧生成器或网络。全部科学数组/点云/benchmark 继续保全在原目录和 A5 包，不复制到轻量制作副本中。

本次已实际准备 [portable/meeting-20261101](portable/meeting-20261101)。新 `authoring/build_notes.mjs` 仅替换复制件的模块定位、两张图片路径和输出覆盖守卫，正文从 palette 定义开始完整保持；模块随副本按原字节保存，图片位于相对可定位路径，Node 语法和必需模块导出导入通过。[PORTABLE_PREPARATION.json](PORTABLE_PREPARATION.json)绑定源、配方和模块哈希。历史 vendored 模块原发行版/许可证来源未新认证，不能用当前安装的版本号认证旧 bundle。

没有执行该讲稿生成器、新 DOCX/PPTX 构建、Office/目标平台渲染或原生 `.pptd` 导出。当前准备流程已消除个人缓存/junction 路径依赖；候选构建、版面与原生导出仍需独立验收。所有旧构建器保留，不直接作为当前命令。

`.build`、review 等目录中混有源码、候选、旧终稿、参考、实际输入和失败证据，不能整体删除。讲稿实际引用 review_v3/page-3.png，该图片已作为制作输入保留并在本轮只读查看；这不是对全套材料的新视觉验收。两个 `.build/node_modules` junction 不跟随，18 个范围内 LX 链接也只保留元数据；全工作区原 27 个链接仍由 A5/A7 保全和恢复。

## 上下文、验证与保留项

A5 的 68 份当前权威在 [before](before) 按哈希备份，当前三层 AGENTS、README、组会/迁移导航、状态和新增报告入口同步，权威清单扩展到 77 文件。代码索引为 905；原 904 条仅维护分类器加组会工具角色、状态渲染器接续“A6已审计但终稿/参考/导出保留”，另外 902 源码/配置完整字节保持；仅新增一个维护工具，不改生产/训练、算法参数、RNG、精度、坐标或五项默认分派。见 [AUTHORITY_PROOF.json](AUTHORITY_PROOF.json)与[SOURCE_SUCCESSION.json](SOURCE_SUCCESSION.json)。

最终 [CHECKS.json](CHECKS.json)核对全部 1,975 原文件、来源/成品/媒体与副本、当前权威/导航、6 项测试、旧封存和 A5 包控制清单绑定。未重复读取 125GB payload；原 A5 全卷读回收据、包摘要与卷元数据接续，旧历史与原 Git 文件继续核对元数据/字节证明链，不将元数据检查声称为另一遍完整原文件哈希。

全项目保全检查观测到 2,877 个原 Git 文件的时间/属性元数据差异，已另行新读 721,934,575 字节，全部 SHA256 匹配 A5；来源不归因、不重置时间或重写对象，HEAD/分支/索引直接核对。初版将这些差异直接作为失败的范围过严，[VALIDATION_FAILURE_02.json](VALIDATION_FAILURE_02.json)、[原观察](GIT_METADATA_TIMESTAMP_OBSERVATION.json)及最终字节核对表保留；后续新增 Git 元数据也只登记为 A7 增量，不删改。

便携配方的封存前静态复核发现问答助手仍使用 String.raw 的 T 标签；初稿路径接线曾删除定义，语法检查无法捕获该运行期问题。已保留 T、修正复制件并加入第 6 项回归检查，原正文保持；初稿从未被运行以生成 Word。原配方和工具在 attempt02 保留，详见 [RECIPE_CORRECTION_01.json](RECIPE_CORRECTION_01.json)。

初版只读检查器未处理 OOXML 包根绝对关系 `/ppt/...`，触发 KeyError；原检查器和 [VALIDATION_FAILURE_01.json](VALIDATION_FAILURE_01.json)保留，修正关系定位后通过，没有改动 Office 文件。

研究 UNRESOLVED、论文 PAUSED，E0 工程正面记录及比较范围保持。GCG1 的 37/8、official MAC 未准入/未运行、PGC1 原 64 actions/第八对停止及七份未解释部分、SSC1 的 18/3 失败/评分训练前停止及原预算均保持。EIA/SRA、SAC/MCV 的身份/物理参考/别名/安全限制不变；5 源码哈希、1 旧上下文、raw/OXTS 及外部动态闭包、A4 Muon/训练入口/完整恢复/PyTorch3D 原提交/目标环境保留项继续有效。

本轮没有启动 WSL/GPU、模型、训练或旧研究/绘图脚本，没有安装、下载、提交、Git 历史改写或对外传输，原件未删除或移动。下一步 A7 整理最终布局与增量，验证恢复、链接和权限；服务器未选定时只能完成本地交付准备，不能标记正式迁移完成。
