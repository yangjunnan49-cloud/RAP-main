"""Advance current authority after A4 auditing; never rewrite archived records."""
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def edit(root, relative, pairs):
    source = PHASE / "before" / root / relative
    value = source.read_text(encoding="utf-8")
    for old, new in pairs:
        assert value.count(old) == 1, (relative, old)
        value = value.replace(old, new, 1)
    if root == "rap-main":
        target = REPO / relative
        assert target.read_bytes() == source.read_bytes(), relative
    else:
        target = PHASE / "updates" / root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def main():
    edit("rap-main", "AGENTS.md", [
        ("更新：2026-11-04，Asia/Shanghai。所有者当前任务为迁移前工程整理；A0–A2 已完成各自范围，**A3 已完成离线入口、代码职责和路径配置整理，并通过标准库测试、参数及数值源码保持检查。下一步 A4：环境依赖与完整训练/恢复链审计。** A3 未运行模型，目标环境数值验收仍待 A4。",
         "更新：2026-11-04，Asia/Shanghai。所有者当前任务为迁移前工程整理；A0–A3 已完成各自范围，**A4 已完成环境/依赖/训练链审计与搭建说明，现有环境 CPU 依赖检查通过；干净重建、GPU 模型 I/O 和完整训练/恢复仍未验收。下一步 A5：数据、模型与全部实验历史清单和打包整理。** 不将审计完成写成训练就绪或服务器迁移完成。"),
        ("6. [A1 审计]", "6. [环境入口](docs/environment/README.md)、[搭建顺序](docs/environment/SETUP.md)、[训练缺口](docs/environment/TRAINING.md)和[A4 记录](docs/maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)。\n7. [A1 审计]"),
        ("五个旧源码哈希、一个旧 AGENTS 中间版本、72 条 Linux 环境引用和外部动态闭包仍有保留项", "五个旧源码哈希、一个旧 AGENTS 中间版本和外部动态闭包仍有保留项；原 72 条 Linux 环境引用已在 A4 逐条精确匹配，PyTorch3D 原构建提交与目标重建仍未闭合"),
        ("896 条代码/配置角色索引", "903 条代码/配置角色索引"),
        ("可选 app.py/ROS2 不在离线入口合同内。", "可选 app.py/ROS2 不在离线入口合同内。新增 scripts/environment 的隔离元数据工具与显式 CPU 探针，不进入五项任务默认分派。"),
        ("完整训练/恢复链及目标环境仍未验收，归 A4。", "A4 已查明缺少受维护训练入口/完整根配置、Muon 及训练/恢复证据；目标环境和独立训练入口实现仍待验收。"),
        ("- 本轮不启动 WSL/GPU/模型/训练/研究实验，不安装、下载、部署或对外发送；", "- A4 按计划只读采集两次短暂启动 WSL，均已恢复停止；17 项必需 CPU 导入/配置/基础算子检查通过，Muon 训练依赖缺失。未初始化 CUDA、实例化模型、加载 checkpoint/数据或训练。没有安装、软件包下载、部署或对外发送；"),
        ("A2/A3 接续证明", "A2/A3/A4 接续证明")])
    edit("workspace-root", "AGENTS.md", [
        ("A3 完成离线代码入口与路径整理，未运行模型；下一阶段为 A4 环境与训练/恢复链审计", "A4 完成环境/训练链审计和搭建说明，CPU 依赖检查通过、WSL 已恢复停止；目标重建/GPU/完整训练仍待验收，下一阶段为 A5 数据、模型与历史清单整理"),
        ("五个旧源码哈希、一份旧上下文与环境待办仍有效。", "五个旧源码哈希、一份旧上下文与构建/目标环境待办仍有效；原 72 条 Linux 引用已在 A4 精确匹配，具体由统一状态页说明。")])
    edit("rap-slam", "AGENTS.md", [
        ("A3 离线入口与路径整理已完成，下一步 A4 审计环境和训练/恢复链；目标环境模型 I/O 尚未执行。", "A4 环境与训练链审计/说明已完成，现有 CPU 依赖检查通过；下一步 A5 整理数据、模型与历史清单，目标重建/GPU 模型 I/O 及完整训练仍未验收。"),
        ("A4 核对依赖、编译扩展和训练/断点恢复链。", "[A4 环境说明](../RAP-main/docs/environment/README.md)登记依赖/编译来源与训练缺口；没有宣称可完整训练或目标环境可用。"),
        ("本阶段不运行模型、训练或研究实验，不启动 WSL/GPU、安装或下载，不改变 Git 历史或对外发送。", "A4 仅短暂启动 WSL 做元数据采集与显式 CPU 依赖/小型算子验证，已恢复停止；没有初始化 CUDA、构造模型、加载数据/权重、训练、安装/软件包下载、Git 历史修改或对外发送。")])
    edit("rap-main", "README.md", [
        ("A4 核对依赖、编译扩展、训练启动与恢复链。", "A4 已形成[环境搭建说明](docs/environment/README.md)和[训练缺口审计](docs/environment/TRAINING.md)；现有 CPU 依赖检查通过，目标重建/GPU 模型与完整训练恢复仍待验收。下一步 A5 整理数据、模型及全部历史清单。")])
    edit("rap-slam", "README.md", [
        ("完整系统/模型/编译扩展和训练链由 A4 建立受测搭建说明；本页不把旧机器安装成功等同于目标服务器已可训练。", "[A4 环境入口](../RAP-main/docs/environment/README.md)提供分层依赖、搭建顺序、CPU 检查与训练缺口。现有环境的 CPU 依赖检查通过；目标重建/GPU/完整训练恢复尚未验收，不把当前包清单当作已验证锁文件。")])
    edit("rap-main", "docs/CONVENTIONS.md", [
        ("训练相关模块存在，但完整训练启动、数据划分和断点恢复尚未验收，归 A4。", "训练组件存在；A4 已明确没有受维护完整训练入口/根配置、Muon 缺失，数据划分和完整恢复尚未验收，见[训练审计](environment/TRAINING.md)。"),
        ("A4 按实际硬件、系统依赖、版本、编译扩展和本地补丁形成搭建文档。", "A4 已形成[环境说明](environment/README.md)，区分当前 CPU 受查结果、参考版本与目标重建/训练保留项；不能把新说明称为经过干净重建的环境锁。"),
        ("本轮 A3 为离线入口、职责和路径维护（未运行模型）", "本轮 A4 为环境与训练链审计及 CPU 依赖验证（WSL 已恢复停止，未运行模型）")])
    edit("rap-main", "docs/README.md", [
        ("| 实验、维护和历史产物 |", "| 环境搭建、依赖分层与训练缺口 | [环境入口](environment/README.md)；[训练审计](environment/TRAINING.md) |\n| 实验、维护和历史产物 |")])
    edit("rap-main", "docs/migration/PLAN.md", [
        ("## A4：环境与研究训练就绪说明", "## A4：环境与研究训练就绪说明——审计/说明完成，目标与训练验收保留\n\n执行记录：[A4 报告](../maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)、[环境入口](../environment/README.md)和[训练审计](../environment/TRAINING.md)。四个环境已采集，72 条旧 Linux 哈希全部匹配，17 项必需 CPU 依赖/基础算子/配置检查通过，Muon 缺失；两次 WSL 维护启动均恢复停止。没有安装或模型/训练运行。当前缺少受维护训练入口和完整根配置，PyTorch3D 原构建提交未恢复；干净重建、目标 GPU/模型 I/O 及训练/恢复未验收。后续 A5 可继续资产清单，相关 A4 保留项仍须在目标验收前闭合。")])
    edit("rap-main", "docs/migration/README.md", [
        ("7. [A3 代码与路径整理]", "7. [A4 环境与训练链审计](../maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)、[搭建说明](../environment/SETUP.md)和[训练缺口](../environment/TRAINING.md)。\n8. [A3 代码与路径整理]"),
        ("8. [A2 文档与索引整理]", "9. [A2 文档与索引整理]"),
        ("72 条 Linux 环境引用待 A4", "72 条 Linux 环境引用已在 A4 全部精确匹配，原构建提交和目标环境仍待验收"),
        ("- 明确保留：", "- A4 审计/说明与现有环境 CPU 检查已完成；Muon、专用训练入口/完整配置、原 PyTorch3D 构建来源和干净/目标环境保留项明确。\n- 明确保留："),
        ("- 下一步：执行 A4，审计依赖、现有环境、训练启动与恢复链，按受测范围建立搭建文档；A5–A7 继续分别验收。", "- 下一步：执行 A5，整理数据、模型与全部历史的来源、范围及校验清单；A4 目标/训练保留项继续跟踪，A6/A7 分别验收。")])
    edit("rap-main", "docs/maintenance/README.md", [
        ("- [11 月 3 日研究关闭交接]", "- [A4 环境与训练链审计](2026-11-04/environment-readiness-01/REPORT_CN.md)：实际 Linux 元数据、依赖/搭建说明、CPU 验证和训练缺口。\n- [11 月 3 日研究关闭交接]")])
    edit("rap-main", "docs/experiments/GAPS.md", [
        ("| A4 | 72 条 Linux 环境哈希声明的实际核对、旧 Windows 工具版本差异、依赖与完整训练/恢复链 |", "| A4 | 原 72 条 Linux 哈希已全部精确匹配；[新审计](../environment/README.md)保留 PyTorch3D 原提交、Muon/专用训练入口与完整恢复、干净重建/GPU 目标验收及旧 Windows 工具版本差异 |")])
    edit("rap-main", "docs/experiments/README.md", [
        ("- [A3 维护记录]", "- [A4 维护记录](../maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md)：环境/训练链审计和现有 CPU 依赖验证，未运行研究或训练。\n- [A3 维护记录]")])
    edit("rap-main", "docs/code/README.md", [
        ("完整机器索引见", "新增[环境检查工具](../environment/VALIDATION.md)只做隔离元数据采集或显式 CPU 检查，不进入五项任务默认分派。环境、训练和目标验证范围见 [A4 环境入口](../environment/README.md)。\n\n完整机器索引见")])
    edit("rap-main", "docs/code/RUNNING.md", [
        ("依赖。**本轮只做路径/CLI 和源码保持验证，没有加载模型、运行配准或训练。**", "依赖。[A4 环境说明](../environment/README.md)已提供搭建与 CPU 验证结果；目标环境及完整训练仍未验收。**A3 只做路径/CLI 和源码保持验证，没有加载模型、运行配准或训练。**")])
    old = PHASE / "before/rap-main/docs/CURRENT_STATE.json"
    state = json.loads(old.read_text(encoding="utf-8"))
    assert (REPO / "docs/CURRENT_STATE.json").read_bytes() == old.read_bytes()
    state["migration"]["A4"] = "AUDIT_AND_GUIDE_COMPLETE_WITH_TRAINING_AND_TARGET_HOLDS"
    state["preservation_holds"]["linux_environment_hash_claim_occurrences_pending_A4"] = 0
    state["preservation_holds"]["linux_environment_hash_claim_occurrences_exact_matched_in_A4"] = 72
    state["preservation_holds"]["pytorch3d_original_build_commit_recovered"] = False
    state["preservation_holds"]["clean_environment_and_target_GPU_model_IO_validated"] = False
    state["next_step"] = {"stage": "A5", "purpose": "整理数据、模型和全部历史的来源、范围、校验与分包清单", "executed_in_A4": False}
    state["maintenance_summary"] = "A4 环境/依赖/训练链审计和搭建说明已完成；72 条 Linux 哈希精确匹配，17 项必需 CPU 检查通过，WSL 恢复停止。Muon/专用训练入口、原构建提交、干净重建/GPU 模型及完整恢复仍未验收。"
    state["evidence"].append("docs/maintenance/2026-11-04/environment-readiness-01/REPORT_CN.md")
    (REPO / "docs/CURRENT_STATE.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    renderer = REPO / "scripts/maintenance/render_current_state.py"
    value = renderer.read_text(encoding="utf-8")
    old_line = 'f"- {holds[\'linux_environment_hash_claim_occurrences_pending_A4\']} 条 Linux 环境哈希声明待 A4 核对，不能称为文件已丢失。",'
    assert old_line in value
    value = value.replace(old_line, 'f"- 原 {holds.get(\'linux_environment_hash_claim_occurrences_exact_matched_in_A4\', 0)} 条 Linux 环境哈希声明已在 A4 精确匹配；仍待核对 {holds[\'linux_environment_hash_claim_occurrences_pending_A4\']} 条。原构建提交与目标重建另行验收。",')
    renderer.write_text(value, encoding="utf-8")
    print("A4 current navigation updated internally; sibling navigation staged")


if __name__ == "__main__":
    main()
