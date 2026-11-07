"""Publish A5 navigation only after complete archive and real restore verification."""
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
    target.write_text(text, encoding="utf-8")


def main():
    assert json.loads((PHASE / "ARCHIVE_VERIFY.json").read_text(encoding="utf-8"))["passed"]
    assert json.loads((PHASE / "RESTORE_CHECKS.json").read_text(encoding="utf-8"))["passed"]
    receipt = json.loads((PHASE / "PACKAGE_REFERENCE.json").read_text(encoding="utf-8"))
    assert len(receipt["volumes"]) == 30 and receipt["ordinary_files_fresh_byte_verified"] == 111629
    for source in (PHASE / "updates/scripts/migration/content_bundle.py", *sorted((PHASE / "updates/docs/assets").glob("*.md"))):
        relative = source.relative_to(PHASE / "updates").as_posix()
        target = REPO / relative
        assert not target.exists(), target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    edit("rap-main", "AGENTS.md", [
        ("**A4 已完成环境/依赖/训练链审计与搭建说明，现有环境 CPU 依赖检查通过；干净重建、GPU 模型 I/O 和完整训练/恢复仍未验收。下一步 A5：数据、模型与全部实验历史清单和打包整理。**", "**A5 已完成六根可见资产的来源/覆盖清单与本地基础包：111,629 个普通文件逐一新读核对，30 卷、98,854 个唯一内容对象读回验证通过。下一步 A6：组会成品、来源与制作链整理。** A4 的目标环境/训练、A7 的完整恢复/链接/权限与最终增量仍有保留项。"),
        ("A0–A3 已完成各自范围", "A0–A4 已完成各自审计/整理范围"),
        ("7. [A1 审计]", "7. [资产入口](docs/assets/README.md)、[数据覆盖](docs/assets/DATASETS.md)、[分包/恢复](docs/assets/PACKAGING.md)和[A5 记录](docs/maintenance/2026-11-04/assets-package-01/REPORT_CN.md)。\n8. [A1 审计]"),
        ("903 条代码/配置角色索引", "904 条代码/配置角色索引"),
        ("新增 scripts/environment 的隔离元数据工具与显式 CPU 探针，不进入五项任务默认分派。", "scripts/environment 的元数据/CPU 工具与 scripts/migration/content_bundle.py 均为显式维护入口，不进入五项推理/SLAM任务默认分派。"),
        ("- `RAPBackend.register(a,b)`", "- A5 基础快照排除本次 phase 与包目录自身；A5 控制面、后续 A6 成品和当前入口最终增量由 A7 汇总。27 个链接原缓冲区已 fresh 核对，不跟随 junction；只做过18份真实普通文件恢复抽查，未声称全量目标恢复或数据来源/训练资格认证。四份 EPUB 非研究保留，不删除。\n- `RAPBackend.register(a,b)`"),
        ("A2/A3/A4 接续证明", "A2/A3/A4/A5 接续证明")])
    edit("workspace-root", "AGENTS.md", [
        ("A4 完成环境/训练链审计和搭建说明，CPU 依赖检查通过、WSL 已恢复停止；目标重建/GPU/完整训练仍待验收，下一阶段为 A5 数据、模型与历史清单整理", "A5 完成六根可见资产的本地基础包、全源字节核对和分卷读回；目标环境/训练与完整恢复/链接/最终增量保留，下一阶段为 A6 组会成品及制作链整理")])
    edit("rap-slam", "AGENTS.md", [
        ("A4 环境与训练链审计/说明已完成，现有 CPU 依赖检查通过；下一步 A5 整理数据、模型与历史清单，目标重建/GPU 模型 I/O 及完整训练仍未验收。", "A5 六根可见资产本地基础包和全源/全卷字节核对已完成；下一步 A6 整理组会成品/制作链，目标重建/GPU 模型 I/O、完整训练及 A7 全量恢复/最终增量仍未验收。"),
        ("- data/、output*/", "- 数据、模型和历史原件未移动/删除；本地包与原路径清单见 [A5 资产入口](../RAP-main/docs/assets/README.md)。\n- data/、output*/")])
    edit("rap-main", "README.md", [
        ("下一步 A5 整理数据、模型及全部历史清单。", "A5 已交付[资产清单与本地基础包](docs/assets/README.md)，原件保留，源文件和分卷字节核对通过；下一步 A6 整理组会制作链。")])
    edit("rap-slam", "README.md", [
        ("data/、output*/ 和根运行日志保留原路径。", "[A5 数据/模型/历史资产](../RAP-main/docs/assets/README.md)登记本地覆盖与原字节基础包；完整目标恢复、链接/权限与最终增量待 A7。data/、output*/ 和根运行日志保留原路径。")])
    edit("rap-main", "docs/README.md", [
        ("| 实验、维护和历史产物 |", "| 数据、权重和本地分包/恢复 | [资产入口](assets/README.md)；[数据覆盖](assets/DATASETS.md)；[分包说明](assets/PACKAGING.md) |\n| 实验、维护和历史产物 |")])
    edit("rap-main", "docs/CONVENTIONS.md", [
        ("本轮 A4 为环境与训练链审计及 CPU 依赖验证（WSL 已恢复停止，未运行模型）", "本轮 A5 为六根可见资产的清单与原字节基础包维护（未启动 WSL/GPU、模型或训练）"),
        ("后续 A4/A5/A6/A7 按迁移计划分别验收", "后续 A6/A7 及 A4 保留项按迁移计划分别验收")])
    edit("rap-main", "docs/migration/PLAN.md", [
        ("## A5：数据、模型与全部实验历史整理", "## A5：数据、模型与全部实验历史整理——六根可见基础包完成，来源与目标恢复保留\n\n执行记录：[A5 报告](../maintenance/2026-11-04/assets-package-01/REPORT_CN.md)及[资产入口](../assets/README.md)。111,629 个普通源文件（含重复副本）全部重新核对字节；30 卷、98,854 个唯一内容读回通过，517 份逻辑包有成员清单与必需卷。27 个链接原缓冲区匹配 A1，不跟随 junction；真实权重/参考/外部历史18文件恢复抽查通过。原件保留，未知来源、raw/OXTS、A4环境/训练和 A7完整链接/权限/服务器恢复继续明列。基础包排除 A5自身与包目录，A5/A6控制面及入口最终增量在 A7 汇总。")])
    edit("rap-main", "docs/migration/README.md", [
        ("7. [A4 环境与训练链审计]", "7. [A5 资产清单/基础分包](../maintenance/2026-11-04/assets-package-01/REPORT_CN.md)、[数据覆盖](../assets/DATASETS.md)与[恢复说明](../assets/PACKAGING.md)。\n8. [A4 环境与训练链审计]"),
        ("8. [A3 代码与路径整理]", "9. [A3 代码与路径整理]"),
        ("9. [A2 文档与索引整理]", "10. [A2 文档与索引整理]"),
        ("- 明确保留：", "- A5 六根可见资产本地基础包已完成并读回核对，原件保留；517逻辑包、数据覆盖和三份唯一权重另列索引。来源/完整目标恢复仍有保留项。\n- 明确保留："),
        ("- 下一步：执行 A5，整理数据、模型与全部历史的来源、范围及校验清单；A4 目标/训练保留项继续跟踪，A6/A7 分别验收。", "- 下一步：执行 A6，整理组会成品、来源和制作链；A4 目标/训练及 A5 来源保留项继续跟踪，A7 做完整恢复、链接/权限、服务器与最终增量验收。")])
    edit("rap-main", "docs/maintenance/README.md", [
        ("- [11 月 3 日研究关闭交接]", "- [A5 数据/模型/历史资产基础包](2026-11-04/assets-package-01/REPORT_CN.md)：全源字节核对、分卷读回、逻辑包和普通文件恢复抽查。\n- [11 月 3 日研究关闭交接]")])
    edit("rap-main", "docs/experiments/README.md", [
        ("- [A4 维护记录]", "- [A5 维护记录](../maintenance/2026-11-04/assets-package-01/REPORT_CN.md)：全部六根可见历史随基础包保全；517逻辑包不等于独立实验数。\n- [A4 维护记录]")])
    edit("rap-main", "docs/experiments/GAPS.md", [
        ("| A5 | 数据集来源、版本、校准/时间/位姿角色与完整性；raw/OXTS 包不因目录存在被标齐 |", "| A5 | [本地基础包/覆盖清单](../assets/README.md)已完成；数据提供方来源、raw/OXTS、物理参考与训练资格未新认证，完整链接/权限/服务器及最终增量恢复待 A7 |")])
    edit("rap-main", "docs/code/README.md", [
        ("完整机器索引见", "[内容分卷/普通文件恢复工具](../../scripts/migration/content_bundle.py)为显式维护命令，默认推理/SLAM分派不调用它；范围和限制见[资产入口](../assets/README.md)。\n\n完整机器索引见")])
    index = REPO / "scripts/maintenance/index_code_entries.py"
    original = PHASE / "before/rap-main/scripts/maintenance/index_code_entries.py"
    assert index.read_bytes() == original.read_bytes()
    text = index.read_text(encoding="utf-8")
    needle = '    if root == "rap-main" and path.startswith("scripts/environment/"):\n        return "current_environment_verification", None\n'
    assert text.count(needle) == 1
    text = text.replace(needle, needle + '    if root == "rap-main" and path.startswith("scripts/migration/"):\n        return "current_migration_verification", None\n')
    index.write_text(text, encoding="utf-8")
    state_path = REPO / "docs/CURRENT_STATE.json"
    old_state = PHASE / "before/rap-main/docs/CURRENT_STATE.json"
    assert state_path.read_bytes() == old_state.read_bytes()
    state = json.loads(old_state.read_text(encoding="utf-8"))
    state["migration"]["A5"] = "COMPLETE_WINDOWS_BASE_CONTENT_PACKAGE_WITH_PROVENANCE_AND_A7_HOLDS"
    state["preservation_holds"]["A5_full_target_link_permission_and_final_incremental_restore_validated"] = False
    state["preservation_holds"]["unexported_Linux_environment_and_wheel_in_A5_base"] = False
    state["next_step"] = {"stage": "A6", "purpose": "整理组会成品、图表来源与制作链", "executed_in_A5": False}
    state["maintenance_summary"] = "A5 六根可见资产111,629个普通文件全部新读核对，30卷/98,854个唯一内容读回通过，517逻辑包和18份真实恢复抽查完成。27链接只保留原元数据；来源、A4目标/训练及A7完整恢复/最终增量保留，原件未删。"
    state["evidence"].append("docs/maintenance/2026-11-04/assets-package-01/REPORT_CN.md")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("A5 current assets and internal navigation published; sibling updates staged")


if __name__ == "__main__":
    main()
