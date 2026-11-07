# 制作链与便携准备

维护入口为 [materials.py](../../scripts/meetings/materials.py)，仅使用 Python 3.10+ 标准库。它查询清单、核对原字节、复制到新目录，不启动任何历史生成器、研究计算、Office 或网络操作。RAP 根默认由脚本位置确定；报告根默认工作区的 RAP-SLAM-report，也可用 `--rap-root`、`--reports-root` 或 RAP_REPORTS_ROOT 指定。

```sh
python /workspace/RAP-main/scripts/meetings/materials.py list
python /workspace/RAP-main/scripts/meetings/materials.py check --family meeting-20261018

# 默认只输出准备计划；必须指定新目录。
python /workspace/RAP-main/scripts/meetings/materials.py prepare \
  --family meeting-20261101 --destination /new/meeting-edit

# 显式复制，不执行构建；原始点云/科学结果数组留在保全档案中。
python /workspace/RAP-main/scripts/meetings/materials.py prepare \
  --family meeting-20261101 --destination /new/meeting-edit --execute
```

新工作目录按 root_id/原相对路径保留来源，并附 SOURCE_MANIFEST 和准备收据。拒绝已有输出、路径穿越、原历史目录内部输出、源 reparse point、大小/哈希变化；复制前校验所有选中源文件，复制后再核对字节。它不自动恢复 20 个范围内链接或跳转其目标。

## 11 月 1 日的当前准备流程

A6 已实际准备 [隔离制作副本](../maintenance/2026-11-04/meeting-lineage-01/portable/meeting-20261101)，72 文件、17,121,135 字节。五页 `.pptd`、页面和已保存媒体使用相对引用，未列入页序的两份第 5 页备选保留，不自动加入。准备命令另生成 `authoring/build_notes.mjs`：保留原讲稿正文，只替换模块定位、两幅图片路径和输出覆盖守卫。它使用副本内 `vendor/docx.cjs`，不依赖 node_modules junction、个人缓存或旧 Kimi 桌面入口。

Node 的语法检查与 vendored 模块必需导出导入检查通过；原讲稿从 palette 定义开始的完整正文文本保持。模块来自已在项目中的原文件，原字节哈希记录在收据中；原发行版/许可证来源未重新认证，不把当前安装版本号套到历史 bundle 上。

将来需要生成讲稿时，可在该新副本内显式执行：

```sh
node /new/meeting-edit/authoring/build_notes.mjs /new/meeting-edit/notes-candidate.docx
```

本轮没有执行这条生成命令，也没有输出新的 DOCX/PPTX。新候选必须重新渲染、逐页目检并记录 SHA256，才可标为新交付；不能用语法/导入通过替代版面或终稿验收。五页编辑源的原生导出运行时仍待迁移验证，不猜测工具兼容性，不把现存四页旧导出当其终稿。

## 历史流程的处置

| 材料 | 原制作方式及输入 | 当前处置 |
| --- | --- | --- |
| 7 月阶段报告 | reportlab；本地 figures/data；受旧字体布局影响 | PDF、图表、源码一同保留；不自动重建 |
| 早期/8 月演示 | `.pptd` + `.page` + 相对媒体；Python 图表生成器 | 4 套原生编辑源共 47 个活跃页面引用及媒体已检查；导出器/字体在目标环境另验 |
| 9 月 21 日 | make_ppt.py、assets、指标表、LaTeX 论文 | 按原版本保全；页数差异保留，禁止为对齐说明擅自删页 |
| 9 月 30 日 / 10 月 11 日 | Artifact Tool、Office QA；旧 `.build/node_modules` 为 junction | 保留交付文件、构建源与 QA 收据；不跟随或盲打包 junction；历史生成器不默认执行 |
| 10 月 18 日 | content_sources / meeting_content、Artifact Tool、Word 参考模板与 Office QA | 参考 Word 已定位相同字节的项目内别名；旧脚本仍保留 Downloads 原路径，只作历史源，不能直接当当前命令 |
| 10 月 25 日 / 11 月 1 日 | 旧四页导出、五页编辑源、图表和两代讲稿 | 分别登记；便携准备只替换复制件中的路径/依赖接线，保留原版 |

历史源码内的 E:/、/mnt/e、C:/Users、旧技能版本及 Windows 字体路径是历史记录。静态扫描见 [AUTHORING_SCRIPTS.json](../maintenance/2026-11-04/meeting-lineage-01/AUTHORING_SCRIPTS.json)，不能一键批量改写封存源码或运行带有实验/重算副作用的旧脚本。

## 缓存与证据

`.build` 和 `review_*` 同时保存构建器、QA、参考模板、候选/旧版和实际讲稿输入，不整体归为垃圾。11 月讲稿引用 `review_v3/page-3.png`，因此该文件是制作输入，已随便携副本保留。46 份 Office/PDF 文件的结构/页数、60 个嵌入媒体关系已登记；16 个没有独立文件同哈希别名的媒体仍完整存在原 Office 包中，不解释成“原图已丢失”或“来源已认证”。

A5/A6 不删除这些缓存、旧版、字体、第三方模块或原数据；A7 按清单、特殊链接和最终目标验证后再决定布局，原件清除仍不属于自动步骤。
