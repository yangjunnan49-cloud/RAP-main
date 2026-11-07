"""Advance current navigation from the backed A2 state; leave historical records intact."""
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
        ("更新：2026-11-03，Asia/Shanghai。所有者当前任务为迁移前工程整理；A0、A1 已完成各自范围，**A2 已完成当前约定、入口与实验索引整理。下一步为 A3：整理有效代码入口、职责和本机运行路径，保持数值行为。** 本轮未执行 A3、环境安装或新研究。",
         "更新：2026-11-04，Asia/Shanghai。所有者当前任务为迁移前工程整理；A0–A2 已完成各自范围，**A3 已完成离线入口、代码职责和路径配置整理，并通过标准库测试、参数及数值源码保持检查。下一步 A4：环境依赖与完整训练/恢复链审计。** A3 未运行模型，目标环境数值验收仍待 A4。"),
        ("5. [A1 审计]", "5. [代码职责](docs/code/README.md) / [运行说明](docs/code/RUNNING.md) / [A3 记录](docs/maintenance/2026-11-04/code-paths-01/REPORT_CN.md)。\n6. [A1 审计]"),
        ("此次 A2 修改当前文档与新增索引，不改生产代码、算法参数、输入/输出或历史结果。当前代码仍有本机默认路径，A3 才改造；完整训练/恢复链与目标环境尚未验收，归 A4。",
         "A3 新增标准库启动器 scripts/run.py（默认仅命令计划；--check 只验路径，--execute 才执行），支持 sample/demo/features/slam/evaluate。路径优先级 CLI > JSON > 环境 > 布局；新输出拒绝复用。SLAM CLI 独立解析，权重可显式配置；原数值计算与 55 个非路径参数保持。完整训练/恢复链及目标环境仍未验收，归 A4。"),
        ("- `RAPBackend.register(a,b)`", "- 当前维护工具是 query_experiments.py、index_code_entries.py 和 render_current_state.py；其它历史研究/封存/账户脚本不在默认分派。895 条代码/配置角色索引保留旧路径和一份历史语法错误，未擅自修复封存工具。可选 app.py/ROS2 不在离线入口合同内。\n- `RAPBackend.register(a,b)`"),
        ("A2 新证明仅接续旧验证器对现行入口的旧哈希断言，原科学封存、未恢复版本与完整历史均保持。",
         "A2/A3 接续证明保全现行入口的旧版本；A3 修改前源码和文档见 [A3 before](docs/maintenance/2026-11-04/code-paths-01/before)。旧验证器不改写，原科学封存、未恢复版本与完整历史均保持。")])
    edit("workspace-root", "AGENTS.md", [
        ("更新：2026-11-03", "更新：2026-11-04"),
        ("A2 完成当前入口和实验索引整理；下一阶段为 A3 代码入口与路径重构", "A3 完成离线代码入口与路径整理，未运行模型；下一阶段为 A4 环境与训练/恢复链审计")])
    edit("rap-slam", "AGENTS.md", [
        ("A2 文档与索引已完成，下一步 A3 处理代码入口和本机路径。", "A3 离线入口与路径整理已完成，下一步 A4 审计环境和训练/恢复链；目标环境模型 I/O 尚未执行。"),
        ("当前 scripts/run_pipeline.py 仍有本机绝对默认路径，README 不声称已可无配置迁移。A3 才改造路径；A4 才核对依赖、编译扩展和训练/断点恢复链。",
         "当前离线入口从 RAP-main/scripts/run.py 生成计划、--check 检查路径、--execute 显式执行；路径优先级 CLI > JSON > 环境 > 布局。scripts/run_pipeline.py 参数已拆到 rap_slam/cli.py，runtime_paths.py 负责布局默认值与预检，新增 --rap-ckpt/--spinnet-ckpt。55 个原非路径参数及数值主体保持；A4 核对依赖、编译扩展和训练/断点恢复链。")])
    edit("rap-main", "README.md", [
        ("| [rectified_point_flow]", "| [scripts/run.py](scripts/run.py) / [运行说明](docs/code/RUNNING.md) | 统一离线启动器：默认生成计划，支持路径检查与显式执行 |\n| [rectified_point_flow]"),
        ("当前 A2 统一文档入口与索引。A3 处理代码职责、有效脚本和本机路径；A4 核对依赖、编译扩展、训练启动与恢复链。", "A3 已整理[代码职责与入口索引](docs/code/README.md)，集中配置运行路径；路径/CLI 和数值源码保持检查通过，尚未执行模型。A4 核对依赖、编译扩展、训练启动与恢复链。")])
    edit("rap-slam", "README.md", [
        ("| [scripts/run_pipeline.py](scripts/run_pipeline.py) | 离线管线参数与入口 |", "| [scripts/run_pipeline.py](scripts/run_pipeline.py) | 离线管线执行入口 |\n| [rap_slam/cli.py](rap_slam/cli.py) / [runtime_paths.py](rap_slam/runtime_paths.py) | 标准库参数解析、布局默认值和路径预检 |"),
        ("现有入口通过 argparse 接收 --rap-root、--output、--real-root、--real-seq、--real-start/--real-end 等参数；源码仍有本机绝对默认值，A3 才实施路径改造。", "[统一启动器与路径配置](../RAP-main/docs/code/RUNNING.md)支持 plan/check/execute；从任意目录传入明确配置，默认输出到新 RAP-runs 树。直接入口保留 argparse 参数并新增 --rap-ckpt/--spinnet-ckpt；默认根按源码布局或环境解析，--help 和路径预检无需数值依赖。"),
        ("坐标校准、0.205° 修正、帧范围与算法参数按原数据合同/协议解释，整理文档不改变默认值。", "坐标校准、0.205° 修正、帧范围与 55 个非路径参数及数值主体保持原合同。A3 只完成静态保持和标准库测试，模型/目标环境的实际 I/O 待 A4。")])
    edit("rap-main", "docs/CONVENTIONS.md", [
        ("当前运行代码仍含本机绝对默认路径，A3 才实施配置与入口改造；本页不把目标约定写成已实现。", "五项当前离线任务通过[统一启动器](code/RUNNING.md)配置根、数据、权重、输出与缓存；优先级 CLI > JSON > 环境 > 布局，JSON 相对路径基于其文件目录。历史/可选脚本内的本机路径保留原文并在代码索引登记，不作为默认分派。"),
        ("本轮 A2 为文档和索引维护", "本轮 A3 为离线入口、职责和路径维护（未运行模型）")])
    edit("rap-main", "docs/README.md", [
        ("| 实验、维护和历史产物 |", "| 代码职责、有效入口和运行路径 | [代码导航](code/README.md)；[运行说明](code/RUNNING.md) |\n| 实验、维护和历史产物 |")])
    edit("rap-main", "docs/migration/PLAN.md", [
        ("## A3：代码与运行路径整理", "## A3：代码与运行路径整理——已完成入口与静态保持验收\n\n执行记录：[A3 报告](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)、[代码职责](../code/README.md)和[运行说明](../code/RUNNING.md)。五项离线任务已接入显式路径启动器；历史/可选工具分类保留，不进入默认分派。标准库测试、8 组共 55 个非路径参数对照、数值主体 AST 与原字节保全检查完成；模型数值执行与依赖/训练链验收待 A4，未提前声明目标环境可用。")])
    edit("rap-main", "docs/migration/README.md", [
        ("7. [A2 文档与索引整理]", "7. [A3 代码与路径整理](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)、[代码职责](../code/README.md)和[运行说明](../code/RUNNING.md)。\n8. [A2 文档与索引整理]"),
        ("- 明确保留：", "- 已完成 A3 离线入口与路径整理：标准库启动器、显式配置、SLAM CLI 拆分及路径/参数/数值源码保持检查；没有运行模型。\n- 明确保留："),
        ("历史脚本退役、生产代码重构、环境新建验证", "可选交互/ROS2 与外部动态依赖的目标验证、环境新建验证"),
        ("- 下一步：执行 A3，整理有效代码入口、职责和本机路径，保持现有数值行为及历史协议。A4–A7 继续按计划分别验收。", "- 下一步：执行 A4，审计依赖、现有环境、训练启动与恢复链，按受测范围建立搭建文档；A5–A7 继续分别验收。")])
    edit("rap-main", "docs/maintenance/README.md", [
        ("- [11 月 3 日研究关闭交接]", "- [A3 代码入口与路径整理](2026-11-04/code-paths-01/REPORT_CN.md)：修改前源码、路径配置、职责索引及行为保持检查。\n- [11 月 3 日研究关闭交接]")])
    edit("rap-main", "docs/experiments/GAPS.md", [
        ("| A3 | 运行路径、动态引用、有效/历史脚本边界和行为保持验证 |", "| A3 | 离线入口、路径和静态保持检查已完成，见 [A3 报告](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)；可选组件/目标模型执行与工作区外动态引用闭包仍待后续验收 |")])
    edit("rap-main", "docs/experiments/PATHS.md", [
        ("A3 才实施运行配置改造。", "A3 已提供[离线运行路径配置](../code/RUNNING.md)，允许分别指定代码、数据、权重、输出和缓存根；历史来源映射不变。")])
    edit("rap-main", "docs/experiments/README.md", [
        ("- [组会定位]", "- [A3 维护记录](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)：首版 482 条目快照之后的代码/路径维护；首版索引原字节保留。\n- [组会定位]")])
    source = PHASE / "before/rap-main/docs/CURRENT_STATE.json"
    state = json.loads(source.read_text(encoding="utf-8"))
    assert (REPO / "docs/CURRENT_STATE.json").read_bytes() == source.read_bytes()
    state["updated_local_date"] = "2026-11-04"
    state["migration"]["A3"] = "COMPLETE_ENTRY_PATH_REFACTOR_WITH_STATIC_BEHAVIOR_CHECKS"
    state["next_step"] = {"stage": "A4", "purpose": "审计环境依赖与完整训练/恢复链，建立受测搭建说明", "executed_in_A3": False}
    state["maintenance_summary"] = "A3 已整理五项离线入口、职责与路径配置，标准库/参数及数值源码保持检查通过；没有加载模型。目标环境模型 I/O、依赖和训练/恢复链待 A4。"
    state["evidence"].append("docs/maintenance/2026-11-04/code-paths-01/REPORT_CN.md")
    (REPO / "docs/CURRENT_STATE.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    renderer = (REPO / "docs/maintenance/2026-11-03/context-index-01/render_state.py").read_text(encoding="utf-8")
    renderer = renderer.replace("parents[4]", "parents[2]")
    renderer = renderer.replace('"服务器尚未选定，正式迁移未完成。A2 为文档/索引整理；生产代码、本机路径和训练环境尚未由本轮验证。"',
                                '"服务器尚未选定，正式迁移未完成。" + state["maintenance_summary"]')
    (REPO / "scripts/maintenance/render_current_state.py").write_text(renderer, encoding="utf-8")
    print("Current internal navigation updated; sibling navigation staged")


if __name__ == "__main__":
    main()
