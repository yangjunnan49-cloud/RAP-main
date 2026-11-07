"""Publish A6 current navigation after catalog and copy-only preparation checks."""
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def edit(root, relative, pairs):
    source = PHASE / "before" / root / relative
    text = source.read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, (relative, old)
        text = text.replace(old, new, 1)
    if root == "rap-main":
        target = REPO / relative
        assert target.read_bytes() == source.read_bytes(), relative
    else:
        target = PHASE / "updates" / root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text.encode("utf-8"))


def main():
    summary = json.loads((PHASE / "SUMMARY.json").read_text(encoding="utf-8"))
    portable = json.loads((PHASE / "PORTABLE_PREPARATION.json").read_text(encoding="utf-8"))
    assert summary["source_files"] == 1975 and portable["node_syntax_check_passed"] and not portable["new_DOCX_or_PPTX_created"]
    for source in (PHASE / "updates/scripts/meetings/materials.py", *sorted((PHASE / "updates/docs/meetings").glob("*"))):
        target = REPO / source.relative_to(PHASE / "updates")
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    edit("rap-main", "AGENTS.md", [
      ("A0–A4 已完成各自审计/整理范围", "A0–A5 已完成各自审计/整理范围"),
      ("**A5 已完成六根可见资产的来源/覆盖清单与本地基础包：111,629 个普通文件逐一新读核对，30 卷、98,854 个唯一内容对象读回验证通过。下一步 A6：组会成品、来源与制作链整理。**", "**A6 已完成组会/报告目录、版本身份、图表字节关联和便携制作准备：10组、1,975文件，6份旧交付哈希匹配。版本差异、1份参考PDF缺口和新导出验收保留。下一步 A7：最终增量、交付布局和恢复验收；服务器未选定。**"),
      ("8. [A1 审计]", "8. [组会/报告](docs/meetings/README.md)、[成品与版本](docs/meetings/CATALOG.md)、[制作说明](docs/meetings/BUILDING.md)和[A6记录](docs/maintenance/2026-11-04/meeting-lineage-01/REPORT_CN.md)。\n9. [A1 审计]"),
      ("904 条代码/配置角色索引", "905 条代码/配置角色索引"),
      ("scripts/environment 的元数据/CPU 工具与 scripts/migration/content_bundle.py 均为显式维护入口", "scripts/environment、scripts/migration/content_bundle.py 和 scripts/meetings/materials.py 均为显式维护入口"),
      ("- `RAPBackend.register(a,b)`", "- A6 不将旧 final/目录日期当作唯一终稿：9月21日实际9页与旧8页声明不同；11月1日5页编辑源与现存4页导出不绑定。历史材料原字节保留，两个node_modules junction不跟随；72文件便携副本只做复制/语法/模块导入验证，未运行旧重算或新Office构建。参考Word已找到精确别名，参考PDF b6c209ac… 原字节未恢复。\n- `RAPBackend.register(a,b)`"),
      ("A2/A3/A4/A5 接续证明", "A2/A3/A4/A5/A6 接续证明")])
    edit("workspace-root", "AGENTS.md", [
      ("A5 完成六根可见资产的本地基础包、全源字节核对和分卷读回；目标环境/训练与完整恢复/链接/最终增量保留，下一阶段为 A6 组会成品及制作链整理", "A6 完成组会/报告目录、版本/图表来源核对与便携制作准备；版本/参考PDF/原生导出、目标环境/训练仍有保留项，下一阶段为 A7 最终增量与恢复验收")])
    edit("rap-slam", "AGENTS.md", [
      ("A5 六根可见资产本地基础包和全源/全卷字节核对已完成；下一步 A6 整理组会成品/制作链，目标重建/GPU 模型 I/O、完整训练及 A7 全量恢复/最终增量仍未验收。", "A6 组会/报告目录、版本核对与便携制作准备已完成；下一步 A7 最终增量/恢复验收。组会版本和参考PDF/原生导出、目标重建/GPU 模型 I/O及完整训练仍有保留项。")])
    edit("rap-main", "README.md", [
      ("下一步 A6 整理组会制作链。", "A6 已交付[组会/报告目录及制作准备](docs/meetings/README.md)，版本和导出限制单列；下一步 A7 汇总最终增量与恢复验收。"),
      ("[组会定位](docs/experiments/MEETINGS.md)：现有成品/工作材料位置，最终整理待 A6。", "[组会/报告总入口](docs/meetings/README.md)：成品、讲稿、编辑源、版本差异、图表和便携制作说明。")])
    edit("rap-slam", "README.md", [
      ("组会与论文材料由[组会定位页](../RAP-main/docs/experiments/MEETINGS.md)进入，成品/源码/缓存组织待 A6，论文仍暂停。", "组会与论文材料由[组会/报告总入口](../RAP-main/docs/meetings/README.md)进入；A6 已核对成品身份、图表字节关联和便携制作准备，版本/参考PDF/新导出保留项另列，论文仍暂停。")])
    edit("rap-main", "docs/README.md", [
      ("| 组会原位置 | [组会材料定位](experiments/MEETINGS.md)，成品/源码/缓存整理待 A6 |", "| 组会、报告与制作链 | [总入口](meetings/README.md)；[日期/版本目录](meetings/CATALOG.md)；[便携制作](meetings/BUILDING.md)；[保留项](meetings/GAPS.md) |")])
    edit("rap-main", "docs/CONVENTIONS.md", [
      ("本轮 A5 为六根可见资产的清单与原字节基础包维护（未启动 WSL/GPU、模型或训练）", "本轮 A6 为组会/报告身份与来源整理、便携制作准备（未启动 WSL/GPU、模型、训练或旧图表重算）"),
      ("后续 A6/A7 及 A4 保留项", "后续 A7 及 A4/A6 保留项")])
    edit("rap-main", "docs/migration/PLAN.md", [
      ("## A6：组会与报告整理", "## A6：组会与报告整理——清单/来源/便携准备完成，版本与新导出验收保留\n\n执行记录：[A6 报告](../maintenance/2026-11-04/meeting-lineage-01/REPORT_CN.md)和[组会总入口](../meetings/README.md)。10组/1,975文件全字节匹配A5；46份Office/PDF结构检查、6份旧交付哈希、4套编辑源活跃页/媒体、60个媒体字节关联和59条历史来源绑定已核对。两处版本差异、未恢复的参考PDF与新Office/原生导出验收保留；72文件便携副本及讲稿路径/模块接线准备通过，不执行旧研究或图表重算。两个junction不跟随，缓存与备选版本按角色保留；A6控制面和新副本在A7最终增量承接。")])
    edit("rap-main", "docs/migration/README.md", [
      ("7. [A5 资产清单/基础分包]", "7. [A6 组会/报告整理](../maintenance/2026-11-04/meeting-lineage-01/REPORT_CN.md)、[成品目录](../meetings/CATALOG.md)与[制作准备](../meetings/BUILDING.md)。\n8. [A5 资产清单/基础分包]"),
      ("8. [A4 环境与训练链审计]", "9. [A4 环境与训练链审计]"),
      ("9. [A3 代码与路径整理]", "10. [A3 代码与路径整理]"),
      ("10. [A2 文档与索引整理]", "11. [A2 文档与索引整理]"),
      ("- 明确保留：", "- A6 组会/报告身份、来源与便携制作准备已完成；未确认终稿变体、参考PDF及新原生导出/版面验收明确保留。\n- 明确保留："),
      ("环境新建验证、组会内容核对、实际数据打包与迁移。", "环境新建验证、组会版本/参考PDF及新导出验收、最终增量与服务器迁移。"),
      ("- 下一步：执行 A6，整理组会成品、来源和制作链；A4 目标/训练及 A5 来源保留项继续跟踪，A7 做完整恢复、链接/权限、服务器与最终增量验收。", "- 下一步：执行 A7，汇总A5/A6控制面和当前入口最终增量，建立交付布局并验证恢复、链接/权限；服务器确定后补目标验收。A4环境/训练、数据来源和A6版本/参考PDF/导出保留项继续跟踪。")])
    edit("rap-main", "docs/maintenance/README.md", [
      ("- [A5 数据/模型/历史资产基础包]", "- [A6 组会/报告与制作链整理](2026-11-04/meeting-lineage-01/REPORT_CN.md)：交付身份、图表字节来源、版本差异与便携制作准备。\n- [A5 数据/模型/历史资产基础包]")])
    edit("rap-main", "docs/experiments/README.md", [
      ("- [组会定位](MEETINGS.md)：只定位现有材料，最终版本与制作依赖待 A6。", "- [组会/报告](../meetings/README.md)：A6已建立成品身份、版本差异、图表字节来源和便携制作入口；历史讲稿不升级当前科学结论。")])
    edit("rap-main", "docs/experiments/GAPS.md", [
      ("| A6 | 最终组会版本、图表来源、制作源码与两个个人 node_modules 目录联接的重建方式 |", "| A6 | [版本与制作链](../meetings/GAPS.md)已审计：三期终稿身份匹配；9月页数/11月源与导出差异、参考PDF缺口、新Office/原生导出仍保留。便携准备不依赖个人junction，原链接元数据待A7恢复 |")])
    edit("rap-main", "docs/experiments/MEETINGS.md", [
      ("本页仅统一入口；成品选择、版本核对、图表来源和制作依赖归 A6。本轮不打开/改写 PPT、Word 或 PDF，不把文件名含 final 当作最终版本认证。", "本页保留原位置导航；A6 的[组会/报告总入口](../meetings/README.md)、[日期/版本目录](../meetings/CATALOG.md)和[制作说明](../meetings/BUILDING.md)已接续成品身份、来源与便携准备。原 PPT/Word/PDF 未改写，版本差异与参考缺口单列，不把文件名 final 当作终稿认证。"),
      ("完整文件归属与哈希见 A1 处置表", "当前组会逐文件归属与哈希见 [A6文件表](../meetings/FILES.jsonl)，完整六根基础包见[A5资产入口](../assets/README.md)")])
    edit("rap-main", "docs/code/README.md", [
      ("A6 处理组会制作链。", "A6组会制作准备见[专门说明](../meetings/BUILDING.md)。"),
      ("完整机器索引见", "[组会目录/哈希/便携准备工具](../../scripts/meetings/materials.py)默认prepare只生成计划，--execute才复制到新目录，不运行旧生成器或研究脚本。\n\n完整机器索引见")])
    index = REPO / "scripts/maintenance/index_code_entries.py"
    original = PHASE / "before/rap-main/scripts/maintenance/index_code_entries.py"
    assert index.read_bytes() == original.read_bytes()
    text = index.read_text(encoding="utf-8")
    needle = '    if root == "rap-main" and path.startswith("scripts/migration/"):\n        return "current_migration_verification", None\n'
    assert text.count(needle) == 1
    index.write_bytes(text.replace(needle, needle + '    if root == "rap-main" and path.startswith("scripts/meetings/"):\n        return "current_meeting_maintenance", None\n', 1).encode("utf-8"))
    state_path = REPO / "docs/CURRENT_STATE.json"
    old_state = PHASE / "before/rap-main/docs/CURRENT_STATE.json"
    assert state_path.read_bytes() == old_state.read_bytes()
    state = json.loads(old_state.read_text(encoding="utf-8"))
    state["migration"]["A6"] = "CATALOG_LINEAGE_AND_PORTABLE_PREPARATION_COMPLETE_WITH_VERSION_REFERENCE_AND_EXPORT_HOLDS"
    state["preservation_holds"]["meeting_final_versions_and_authoring_chain_reviewed"] = True
    state["preservation_holds"]["all_meeting_final_variants_and_new_native_exports_confirmed"] = False
    state["preservation_holds"]["historical_meeting_reference_PDF_exact_bytes_recovered"] = False
    state["next_step"] = {"stage": "A7", "purpose": "汇总最终控制面/增量、交付布局与完整恢复；服务器确定后补目标验收", "executed_in_A6": False}
    state["maintenance_summary"] = "A6已清点10组组会/报告1975文件并匹配A5字节；6份旧交付身份、46份Office/PDF结构、60媒体字节关系、59历史来源绑定已核对；72文件便携副本及讲稿路径/模块准备通过。版本/参考PDF/新导出及A4环境训练与A7最终恢复保留。"
    state["evidence"].append("docs/maintenance/2026-11-04/meeting-lineage-01/REPORT_CN.md")
    state_path.write_bytes((json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("A6 current docs/tool published; external navigation staged")


if __name__ == "__main__":
    main()
