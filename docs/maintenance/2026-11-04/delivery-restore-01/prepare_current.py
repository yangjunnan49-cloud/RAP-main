"""Publish final A7 authority only after full local project/link/path acceptance."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
PREFLIGHT = "--preflight" in sys.argv


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
        if not PREFLIGHT:
            target.parent.mkdir(parents=True, exist_ok=True)
    if PREFLIGHT:
        return
    target.write_bytes(text.encode("utf-8"))


def main():
    if not PREFLIGHT:
        project = json.loads((PHASE / "PROJECT_RESTORE.json").read_text(encoding="utf-8"))
        links = json.loads((PHASE / "POSIX_LINK_CHECKS.json").read_text(encoding="utf-8"))
        session = json.loads((PHASE / "WSL_LINK_SESSION.json").read_text(encoding="utf-8"))
        relocated = json.loads((PHASE / "RELOCATED_CHECKS.json").read_text(encoding="utf-8"))
        assert project["passed"] and links["passed"] and session["restored_initial_stopped_state"] and relocated["passed"]
        assert project["fresh_restored_tree_check"]["ordinary_files_freshly_rehashed"] == 112682
    date = "2026-11-05"  # Client date supplied for this continuation, Asia/Shanghai.
    for source in (PHASE / "updates/scripts/migration/delivery.py", *sorted((PHASE / "updates/docs/migration").glob("*.md"))):
        target = REPO / source.relative_to(PHASE / "updates")
        assert not target.exists()
        if PREFLIGHT:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    edit("rap-main", "AGENTS.md", [
      ("更新：2026-11-04，Asia/Shanghai。", "更新：" + date + "，Asia/Shanghai。"),
      ("A0–A5 已完成各自审计/整理范围", "A0–A6 已完成各自审计/整理范围"),
      ("**A6 已完成组会/报告目录、版本身份、图表字节关联和便携制作准备：10组、1,975文件，6份旧交付哈希匹配。版本差异、1份参考PDF缺口和新导出验收保留。下一步 A7：最终增量、交付布局和恢复验收；服务器未选定。**", "**A7 项目层本地完整恢复与字节复核通过：112,682文件、135,095,691,259字节；25内部相对链接及POSIX小夹具通过，WSL已恢复停止。最终当前控制与A7证据作为独立封存层交付，最终收据见包内DELIVERY/FINAL_ACCEPTANCE。服务器尚未选定，下一步为选定目标后的环境/权限/功能验收。**"),
      ("A4 的目标环境/训练、A7 的完整恢复/链接/权限与最终增量仍有保留项。", "A4目标环境/训练、A5/A6来源/版本、两个外部junction重建、真实Linux权限/所有者与服务器验收仍有保留项。"),
      ("9. [A1 审计]", "9. [最终交付](docs/migration/DELIVERY.md)、[恢复说明](docs/migration/RESTORE.md)、[迁移交接](docs/migration/HANDOFF.md)和[A7记录](docs/maintenance/2026-11-04/delivery-restore-01/REPORT_CN.md)。\n10. [A1 审计]"),
      ("905 条代码/配置角色索引", "906 条代码/配置角色索引"),
      ("scripts/environment、scripts/migration/content_bundle.py 和 scripts/meetings/materials.py", "scripts/environment、scripts/migration 的分包/交付恢复工具和 scripts/meetings/materials.py"),
      ("- A5 基础快照排除本次 phase 与包目录自身；A5 控制面、后续 A6 成品和当前入口最终增量由 A7 汇总。27 个链接原缓冲区已 fresh 核对，不跟随 junction；只做过18份真实普通文件恢复抽查，未声称全量目标恢复或数据来源/训练资格认证。四份 EPUB 非研究保留，不删除。", "- A5基础快照当时排除A5自身和包目录；A7增量已承接A5/A6资料，最终控制层承接A7当前入口及审计。A7项目层完整恢复后逐文件新读复核，19份替换前基础字节另存历史；25内部链接在新恢复树改相对目标并验证，2个人junction不跟随/不重建。原27链接缓冲区保留；四份EPUB单列非研究，原件不删。"),
      ("- `RAPBackend.register(a,b)`", "- A7仅一次有界WSL文件系统维护：恢复新副本内相对链接、运行/tmp固定权限夹具，已恢复Stopped。五项离线启动器在新树从其它cwd做--check，未导入数值/模型模块、不创建任务输出；不把路径检查、权限夹具或本地恢复写成Linux服务器/GPU/训练验收。包与恢复副本仍同盘，不提供异地或服务器驻留证明。\n- `RAPBackend.register(a,b)`"),
      ("A2/A3/A4/A5/A6 接续证明", "A2/A3/A4/A5/A6/A7 接续证明")])
    edit("workspace-root", "AGENTS.md", [
      ("更新：2026-11-04，Asia/Shanghai。", "更新：" + date + "，Asia/Shanghai。"),
      ("A6 完成组会/报告目录、版本/图表来源核对与便携制作准备；版本/参考PDF/原生导出、目标环境/训练仍有保留项，下一阶段为 A7 最终增量与恢复验收", "A7项目层本地完整恢复/字节复核、内部相对链接和便携路径预检已通过，最终控制/证据独立封存交付；服务器未选定，环境/训练、Linux目标权限及来源/组会版本仍有保留项，下一步为目标选定后的验收")])
    edit("rap-slam", "AGENTS.md", [
      ("A6 组会/报告目录、版本核对与便携制作准备已完成；下一步 A7 最终增量/恢复验收。", "A7本地项目层完整恢复/字节核对及25内部相对链接验证已通过，最终当前入口与证据层独立交付；下一步为服务器选定后的目标环境/权限/功能验收。")])
    edit("rap-main", "README.md", [
      ("下一步 A7 汇总最终增量与恢复验收。", "A7已形成[本地交付与恢复入口](docs/migration/DELIVERY.md)，完整项目字节复核及相对链接检查通过；服务器确定后继续目标验收。")])
    edit("rap-slam", "README.md", [
      ("完整目标恢复、链接/权限与最终增量待 A7。", "[A7本地交付](../RAP-main/docs/migration/DELIVERY.md)已完成项目层全量恢复/字节与相对链接检查；真实目标权限/环境及服务器验收仍待闭合。")])
    edit("reports", "README.md", [
      ("本 README 为 A6 新导航，纳入 A7 最终增量。", "本 README 为 A6 新导航，已由[A7交付层](../RAP-main/docs/migration/DELIVERY.md)承接；目标服务器与新导出验收仍未完成。")])
    edit("rap-main", "docs/README.md", [
      ("| 当前任务、限制和下一步 |", "| 最终交付、恢复与服务器保留项 | [交付入口](migration/DELIVERY.md)；[恢复](migration/RESTORE.md)；[交接](migration/HANDOFF.md) |\n| 当前任务、限制和下一步 |")])
    edit("rap-main", "docs/CONVENTIONS.md", [
      ("本轮 A6 为组会/报告身份与来源整理、便携制作准备（未启动 WSL/GPU、模型、训练或旧图表重算）", "本轮 A7 为本地交付、完整恢复和路径/链接/权限处理（仅一次有界WSL文件系统维护并恢复Stopped，未启动GPU/模型/训练或旧图表重算）"),
      ("后续 A7 及 A4/A6 保留项按迁移计划分别验收", "A7真实目标/服务器及A4/A6保留项按迁移交接继续验收")])
    edit("rap-main", "docs/migration/PLAN.md", [
      ("## A7：交付包与恢复验收", "## A7：交付包与恢复验收——本地项目/控制交付完成，真实目标与服务器保留\n\n执行记录：[A7报告](../maintenance/2026-11-04/delivery-restore-01/REPORT_CN.md)、[交付入口](DELIVERY.md)、[恢复说明](RESTORE.md)和[剩余验收](HANDOFF.md)。A5基础+1,072增量合成112,682文件/135,095,691,259字节，已完整恢复并重新读取核对；19份基础旧字节另存。25内部相对链接在新树验证，2个人junction不重建；一次WSL文件系统维护已恢复Stopped，POSIX小夹具不替代真实目标权限。当前A7文档/工具和本阶段完整证据单独封存交付，避免自包含递归；服务器尚未选定，环境/GPU/训练及真实目标验收不提前标完成。")])
    edit("rap-main", "docs/migration/README.md", [
      ("7. [A6 组会/报告整理]", "7. [A7最终交付](DELIVERY.md)、[恢复说明](RESTORE.md)、[迁移交接](HANDOFF.md)与[A7记录](../maintenance/2026-11-04/delivery-restore-01/REPORT_CN.md)。\n8. [A6 组会/报告整理]"),
      ("8. [A5 资产清单/基础分包]", "9. [A5 资产清单/基础分包]"),
      ("9. [A4 环境与训练链审计]", "10. [A4 环境与训练链审计]"),
      ("10. [A3 代码与路径整理]", "11. [A3 代码与路径整理]"),
      ("11. [A2 文档与索引整理]", "12. [A2 文档与索引整理]"),
      ("- 明确保留：", "- A7本地项目层全量恢复/字节、25内部相对链接与五项离线路径预检已通过，最终当前控制与证据独立封存交付，服务器尚未选定。\n- 明确保留："),
      ("最终增量与服务器迁移。", "真实Linux权限/所有者、服务器迁移与驻留验收。"),
      ("- 下一步：执行 A7，汇总A5/A6控制面和当前入口最终增量，建立交付布局并验证恢复、链接/权限；服务器确定后补目标验收。A4环境/训练、数据来源和A6版本/参考PDF/导出保留项继续跟踪。", "- 下一步：服务器选定后按迁移交接验收真实文件系统/权限、完整包/驻留、环境和最小功能。A4训练/GPU/构建来源、数据来源及A6版本/参考PDF/导出保留项继续跟踪，不自动开训或部署。"),
      ("本阶段没有选择或购买服务器，没有安装依赖、启动 WSL/GPU、加载模型、训练或恢复已停止的科学路线。", "本阶段没有选择/购买/部署服务器，没有安装依赖、启动GPU、加载模型、训练或恢复已停止的科学路线；一次WSL仅用于新恢复副本的链接与小权限夹具，已恢复原停止状态。")])
    edit("rap-main", "docs/maintenance/README.md", [
      ("- [A6 组会/报告与制作链整理]", "- [A7本地交付与完整恢复](2026-11-04/delivery-restore-01/REPORT_CN.md)：项目层全字节恢复、相对链接/路径预检、当前控制与证据封存，真实服务器保留。\n- [A6 组会/报告与制作链整理]")])
    edit("rap-main", "docs/assets/PACKAGING.md", [
      ("该工具只承诺普通文件字节；本轮还没有完整恢复全部 125GB、还原 POSIX 权限或在服务器验收。A7 将源身份映射到最终布局并验证恢复/增量。", "A5工具只承诺普通文件字节；[A7交付工具](../migration/RESTORE.md)已将基础和增量完整恢复并逐文件复核，25内部相对链接另验。真实Linux权限/所有者、环境和服务器验收仍未完成。"),
      ("A6/A7 分别处理重建与实际链接恢复，普通文件恢复脚本不会自动创建这些链接或下载依赖。", "A7已在新恢复树通过一次WSL文件系统维护恢复/验证25个相对内部链接并恢复Stopped；2个人junction不创建。A5普通文件脚本不创建链接，A7显式链接选项也不下载依赖。"),
      ("旧快照字节仍保存在内容包。", "旧快照字节仍保存在内容包。最终项目增量及A7封存控制层见[交付入口](../migration/DELIVERY.md)。")])
    edit("rap-main", "docs/experiments/PATHS.md", [
      ("| codex-records | 外部 Codex 记录根 |", "| codex-records | archives/Codex（A7恢复布局） |"),
      ("这份映射是来源记录，目标服务器路径未冻结；", "这份A1映射保持原建议；A7已采用[同级仓库/Datasets和独立档案根布局](../migration/DELIVERY.md)，服务器绝对挂载点仍未定；")])
    edit("rap-main", "docs/code/RUNNING.md", [
      ("## 直接入口和兼容性", "A7已在新恢复树从其它cwd对全部五项任务做--check，确认所需路径全部落在新树、未导入数值/模型模块、不创建任务输出；这不验证数据格式、依赖或模型I/O。见[本地交付](../migration/DELIVERY.md)。\n\n## 直接入口和兼容性")])
    edit("rap-main", "docs/experiments/GAPS.md", [
      ("## 后续阶段承接", "A7本地项目恢复和当前控制接续见[交付/交接](../migration/DELIVERY.md)；真实目标权限、环境、训练与来源/版本保留项继续有效。\n\n## 后续阶段承接")])
    state_path = REPO / "docs/CURRENT_STATE.json"
    old = PHASE / "before/rap-main/docs/CURRENT_STATE.json"
    assert state_path.read_bytes() == old.read_bytes()
    state = json.loads(old.read_text(encoding="utf-8"))
    state["updated_local_date"] = date
    state["migration"]["A7"] = "LOCAL_LAYERED_PROJECT_AND_CONTROL_DELIVERY_COMPLETE_WITH_LINUX_TARGET_AND_SERVER_HOLDS"
    state["preservation_holds"]["A7_local_project_restore_and_full_byte_recheck_passed"] = True
    state["preservation_holds"]["A7_local_relative_internal_links_verified"] = 25
    state["preservation_holds"]["external_personal_runtime_junctions_recreated"] = False
    state["preservation_holds"]["actual_target_Linux_modes_owners_ACLs_environment_or_GPU_validated"] = False
    state["next_step"] = {"stage": "TARGET_SELECTION_AND_REMAINING_ACCEPTANCE", "purpose": "服务器确定后验收文件/权限/驻留、环境和最小功能；A4训练及来源/版本保留项另行闭合", "automatic_deploy_training_or_research_authorized": False}
    state["maintenance_summary"] = "A7基础+项目增量112682文件/135095691259字节已完整恢复及新读复核，19份基础旧字节另存；25内部相对链接与五项迁移路径检查通过，WSL已停止。最终当前控制和A7证据独立封存交付；真实Linux目标/服务器、环境训练和来源版本仍保留。"
    state["evidence"].append("docs/maintenance/2026-11-04/delivery-restore-01/REPORT_CN.md")
    if not PREFLIGHT:
        state_path.write_bytes((json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("A7 publication preflight passed" if PREFLIGHT else "A7 final current authority published internally; external guarded updates staged")


if __name__ == "__main__":
    main()
