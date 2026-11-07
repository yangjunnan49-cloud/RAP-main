"""Render current meeting navigation from inspected, explicitly qualified records."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    target = PHASE / "updates/docs/meetings"
    target.mkdir(parents=True, exist_ok=True)
    catalog = load(PHASE / "CATALOG.json")
    lookup = {r["asset"]: r for r in load(PHASE / "ARTIFACT_STRUCTURE.json")}
    state_names = {
        "RETAINED_PDF_NO_FINAL_RECEIPT": "已保存 PDF；无终稿收据",
        "SOURCE_ONLY_DATE_UNCONFIRMED": "编辑源；日期和最终导出未确认",
        "TWO_EXPORT_VARIANTS_FINAL_OWNER_CHOICE_UNCONFIRMED": "双版导出均保留；唯一终稿未确认",
        "HISTORIC_DELIVERY_WITH_SLIDE_COUNT_DISCREPANCY": "旧交付文件；页数声明不一致",
        "FINAL_IDENTITY_MATCHES_HISTORIC_DELIVERY": "终稿身份匹配原交付收据",
        "RETAINED_EXPORTS_NOT_NOV01_SOURCE_FINAL": "四页旧导出；不标作11月五页源终稿",
        "EDITABLE_SOURCE_AND_NOTES_EXPORT_NOT_BOUND_TO_FINAL_PPTX": "五页编辑源/新讲稿；PPTX终稿对应未确认",
        "HISTORICAL_ONLY_PAPER_CURRENTLY_PAUSED": "历史论文工程；当前写作暂停",
    }
    lines = ["# 按日期与主题查找材料", "", "日期来自原文件/目录/交付记录，不认证实际开会时间。10 月 18 日材料于 10 月 20 日关闭交付；当前科研边界仍由统一状态页承担。", "",
             "| 日期/主题 | 文件数 | 状态 |", "| --- | ---: | --- |"]
    for f in catalog["families"]:
        lines.append(f"| {f['date'] or '未确认日期'} · {f['topic']} | {f['files']} | {state_names[f['state']]} |")
    for f in catalog["families"]:
        lines += ["", "## " + (f["date"] or "未确认日期") + " · " + f["topic"], "", state_names[f["state"]] + "。ID：`" + f["id"] + "`。", ""]
        for asset in f["primary"]:
            root, path = asset.split(":", 1)
            rel = "../../" + path if root == "rap-main" else "../../../RAP-SLAM-report/" + path
            metadata = lookup.get(asset, {})
            count = metadata.get("active_slide_count", metadata.get("pages"))
            annotation = (f"（{count} 页；按实际活跃页序/本地PDF）" if count is not None else "")
            lines.append(f"- [{Path(path).name}]({quote(rel, safe='/')}){annotation}")
        for scope in f["roots"]:
            root, path = scope.split(":", 1)
            rel = "../../" + path if root == "rap-main" else "../../../RAP-SLAM-report/" + path
            lines.append(f"- [原始来源目录：{scope}]({quote(rel, safe='/')})，全部版本/失败/QA 原字节保留。")
    lines += ["", "完整逐文件归属和 SHA256 见 [FILES.jsonl](FILES.jsonl)；讲稿分页、旧视觉检查仅按原记录说明，不把 DOCX app.xml 页数字段当作本轮渲染验收。", "",
              "[返回总入口](README.md) · [制作与便携准备](BUILDING.md) · [版本/来源保留项](GAPS.md)", ""]
    (target / "CATALOG.md").write_bytes("\n".join(lines).encode("utf-8"))
    for name in ("CATALOG.json", "FILES.jsonl"):
        (target / name).write_bytes((PHASE / name).read_bytes())
    chains = {"schema_version": 1, "current_copy_and_preparation_entry": "scripts/meetings/materials.py",
              "current_entry_invokes_historical_scientific_or_builder_scripts": False,
              "prepared_notes_recipe_personal_cache_independent": True,
              "notes_content_body_preserved": True, "new_office_artifact_build_or_visual_export_validated": False,
              "native_pptd_export_runtime_validated": False,
              "portable_preparation": "docs/maintenance/2026-11-04/meeting-lineage-01/PORTABLE_PREPARATION.json",
              "historical_static_scripts": [{"asset": r["asset"], "sha256": r["sha256"], "machine_reference_count": len(r["machine_or_runtime_reference_lines"]), "executed_in_A6": False}
                                            for r in load(PHASE / "AUTHORING_SCRIPTS.json")],
              "editable_decks": load(PHASE / "EDITABLE_DECKS.json"),
              "data_and_figure_recomputation_allowed_by_default": False,
              "link_targets_followed": False, "final_A6_control_plane_and_new_copies_required_in_A7_increment": True}
    (target / "BUILD_CHAINS.json").write_bytes((json.dumps(chains, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"current_families": len(catalog["families"]), "current_docs_and_data": len(list(target.glob('*'))),
                      "current_tool_sha256": hashlib.sha256((PHASE/'updates/scripts/meetings/materials.py').read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
