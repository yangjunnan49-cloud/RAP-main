"""Preserve intermediate navigation and include recovered build logs/scripts."""
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def update(path, pairs):
    value = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert value.count(old) == 1, (str(path), old)
        value = value.replace(old, new, 1)
    relative = path.relative_to(REPO)
    backup = PHASE / "before-build-supplement" / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    assert not backup.exists()
    backup.write_bytes(path.read_bytes())
    path.write_text(value, encoding="utf-8")


def main():
    update(REPO / "AGENTS.md", [("A4 按计划只读采集两次短暂启动 WSL", "A4 按计划四次短暂启动 WSL（元数据、CPU 检查、构建日志/脚本补查）")])
    update(REPO / "docs/environment/OBSERVED.md", [
        ("原提交、原构建日志和完整编译命令尚未恢复。安装版本号 0.7.9 不能代替 Git 提交证明。", "两份构建日志和原脚本已补查保全，包含编译命令与 compute_120/sm_120；原脚本使用未固定的 @stable。失败克隆日志出现的 Git object ID 不能冒充成功安装的提交，安装版本号 0.7.9 也不能代替提交证明。见 [构建复核](../maintenance/2026-11-04/environment-readiness-01/BUILD_REVIEW.json)。"),
        ("本轮两次短暂启动，分别采集元数据/源码/哈希和保全关键扩展/CPU 验证，两次均在 finally 中恢复停止状态。", "本轮四次短暂启动，分别采集元数据/源码/哈希、保全扩展/CPU 验证，以及两次限定构建日志/脚本补查，均在 finally 中恢复停止状态。"),
        ("[CPU_SESSION.json](../maintenance/2026-11-04/environment-readiness-01/CPU_SESSION.json)；", "[CPU_SESSION.json](../maintenance/2026-11-04/environment-readiness-01/CPU_SESSION.json)、[BUILD_SESSION.json](../maintenance/2026-11-04/environment-readiness-01/BUILD_SESSION.json)、[BUILD_SCRIPT_SESSION.json](../maintenance/2026-11-04/environment-readiness-01/BUILD_SCRIPT_SESSION.json)；")])
    update(REPO / "docs/environment/VALIDATION.md", [("两次 WSL 维护会话已停止", "四次 WSL 维护会话均已恢复停止")])
    update(REPO / "docs/migration/PLAN.md", [("两次 WSL 维护启动均恢复停止", "四次 WSL 维护启动（含构建来源补查）均恢复停止")])
    update(PHASE / "AUTHORITY.md", [("两次短暂 WSL 会话", "四次短暂 WSL 会话（含构建日志/脚本补查）")])
    update(PHASE / "REPORT_CN.md", [
        ("原构建提交/补丁和完整编译记录未恢复。", "两份原构建日志和原脚本已补查保全，包含编译命令与架构设置，但没有恢复精确原构建提交/完整源码输入。"),
        ("381 份环境来源/安装文件，共 **332,391,193 字节**", "384 份环境来源/安装/构建记录文件，共 **332,636,737 字节**"),
        ("本轮两次 WSL 维护会话先确认 Stopped", "本轮四次 WSL 维护会话先确认 Stopped"),
        ("[CPU 会话](CPU_SESSION.json)及[最终宿主观察](HOST_final.json)", "[CPU 会话](CPU_SESSION.json)、[构建日志会话](BUILD_SESSION.json)、[原脚本补查](BUILD_SCRIPT_SESSION.json)及[最终宿主观察](HOST_after_build.json)"),
        ("## 验证与接续", "补查先发现并保全旧失败克隆日志和成功构建日志，又读取了原脚本；失败 Git object ID、未固定 @stable 和成功本地构建没有提交绑定，详见 [BUILD_REVIEW.json](BUILD_REVIEW.json)。原扫描对 .sh 路径的存在性标签错误由独立字节证据纠正，未改写第一次扫描。补查驱动有一次隔离 Python 辅助导入失败，发生在启动 WSL 前，原驱动及修正见 [VALIDATION_FAILURE_01.json](VALIDATION_FAILURE_01.json)。\n\n## 验证与接续")])
    source = PHASE / "AUTHORITY_PROOF.json"
    (PHASE / "AUTHORITY_PROOF_BEFORE_BUILD_SUPPLEMENT.json").write_bytes(source.read_bytes())
    print("Build evidence included; intermediate navigation and successful checks retained")


if __name__ == "__main__":
    main()
