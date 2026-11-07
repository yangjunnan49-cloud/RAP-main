"""Apply the late A8 byte layer after target acceptance, then publish actual state."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import time
import traceback
from zoneinfo import ZoneInfo

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
PACKAGE = Path("/root/autodl-fs/rap-transfer-20261106/A8-20261106")
WORKSPACE = Path("/root/autodl-tmp/rap-workspace-20261106")


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8388608), b""):
            value.update(block)
    return value.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def member(relative):
    name = PurePosixPath(relative)
    if name.is_absolute() or ".." in name.parts or "\\" in relative:
        raise ValueError("Unsafe A8 member")
    target = WORKSPACE.joinpath(*name.parts)
    if not target.resolve().is_relative_to(WORKSPACE.resolve()):
        raise ValueError("A8 member escapes the workspace")
    return target


def main():
    if (ROOT / "CONTROL_STARTED.json").exists():
        raise RuntimeError("Control finalization already started")
    save(ROOT / "CONTROL_STARTED.json", dict(started_utc=utc(), pid=os.getpid()))
    deadline = time.monotonic() + 48 * 3600
    while True:
        if (ROOT / "file-acceptance/FAILURE.json").exists():
            raise RuntimeError("The prerequisite file acceptance failed")
        files_ready = (ROOT / "file-acceptance/ACCEPTANCE.json").exists()
        outcome_ready = (ROOT / "MIGRATION_ACCEPTANCE.json").exists() or (ROOT / "FUNCTIONAL_FAILURE.json").exists()
        if files_ready and outcome_ready:
            break
        if time.monotonic() > deadline:
            raise TimeoutError("Target finalization prerequisites did not finish within 48 hours")
        time.sleep(30)
    binding = json.loads((ROOT / "CONTROL_BINDING.json").read_text())
    assert sha(PACKAGE / "CONTROL.json") == binding["manifest_sha256"]
    manifest = json.loads((PACKAGE / "CONTROL.json").read_text(encoding="utf-8"))
    archive = PACKAGE / manifest["archive"]
    assert archive.stat().st_size == manifest["archive_bytes"] and sha(archive) == manifest["archive_sha256"]
    expected = {row["path"]: row for row in manifest["files"]}
    assert len(expected) == len(manifest["files"])
    changed, added, seen, versions = [], [], set(), []
    with tarfile.open(archive) as stream:
        for info in stream:
            assert info.isfile() and info.name in expected and info.name not in seen
            row = expected[info.name]
            data = stream.extractfile(info).read()
            assert len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"]
            target = member(info.name)
            assert not target.is_symlink()
            if target.exists():
                observed = sha(target)
                if observed == row["sha256"]:
                    seen.add(info.name)
                    continue
                assert row["before_sha256"] is not None and observed == row["before_sha256"], info.name
                old = member("archives/source-versions/A8-control/" + info.name)
                old.parent.mkdir(parents=True, exist_ok=True)
                assert not old.exists()
                shutil.copyfile(target, old)
                assert sha(old) == observed
                os.chmod(old, 0o644)
                versions.append(dict(path=info.name, old_sha256=observed, retained=str(old.relative_to(WORKSPACE))))
                changed.append(info.name)
            else:
                assert row["before_sha256"] is None, info.name
                added.append(info.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".a8-new")
            with temporary.open("xb") as out:
                out.write(data)
            os.chmod(temporary, 0o644)
            temporary.replace(target)
            assert sha(target) == row["sha256"]
            seen.add(info.name)
    assert seen == set(expected)
    save(ROOT / "A8_OVERLAY_APPLIED.json", dict(passed=True, completed_utc=utc(), manifest_sha256=binding["manifest_sha256"],
         files_hash_checked=len(seen), changed=changed, added=added, superseded_bytes_preserved=versions))
    phase = member(manifest["phase_prefix"])
    remote = phase / "remote"
    remote.mkdir()
    for source in sorted(ROOT.glob("*.json")):
        shutil.copyfile(source, remote / source.name)
    for folder in ("file-acceptance", "logs"):
        dest = remote / folder
        dest.mkdir()
        for source in sorted((ROOT / folder).glob("*")):
            if source.is_file():
                shutil.copyfile(source, dest / source.name)
    functional = (ROOT / "MIGRATION_ACCEPTANCE.json").exists() and json.loads((ROOT / "MIGRATION_ACCEPTANCE.json").read_text())["passed"]
    local_date = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    posix = json.loads((ROOT / "file-acceptance/POSIX_CHECK.json").read_text())
    assert posix["passed"] and posix["internal_relative_links"] == 25
    status = "文件、环境与有界模型I/O验收通过；完整训练/恢复链仍有保留项" if functional else "服务器文件恢复/哈希通过；环境或有界功能验收失败，须按收据继续修复"
    rap = WORKSPACE / "RAP-main"
    state_path = rap / "docs/CURRENT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_local_date"] = local_date
    state["current_work"] = "AutoDL迁移验收与后续研究训练准备"
    state["migration"].update(server_selected=True, server_migration_complete=bool(functional),
        server_files_restored_and_hash_verified=True,
        A8="SERVER_FILES_ENVIRONMENT_AND_BOUNDED_MODEL_IO_ACCEPTED_WITH_TRAINING_HOLDS" if functional else "SERVER_FILES_ACCEPTED_WITH_ENVIRONMENT_OR_FUNCTIONAL_FAILURE")
    holds = state["preservation_holds"]
    holds.update(A5_full_target_link_permission_and_final_incremental_restore_validated=True,
        actual_target_relative_links_verified=25, actual_target_regular_mode_policy_verified="0644",
        actual_target_uid_gid_observed=posix["observed_uid_gid"], original_owner_and_ACL_authenticated=False,
        bounded_target_GPU_extension_and_one_pair_model_IO_validated=bool(functional),
        clean_environment_and_target_GPU_model_IO_validated=bool(functional))
    state["next_step"].update(stage="TRAINING_ENTRY_AND_RESUME_PREREQUISITES" if functional else "REPAIR_TARGET_ENVIRONMENT_OR_FUNCTIONAL_FAILURE",
        purpose="完整训练入口/配置、Muon来源、数据资格及断点恢复另行实现/验收；不自动开训" if functional else "阅读A8失败收据，保持原输入/参数，修复迁移依赖或接口；未自动重试科学路线")
    state["maintenance_summary"] = status + "。A5/A7全量589文件及112972文件恢复树已在真实服务器校验；A8接续当日本地" + str(manifest["delta_current_files"]) + "份增量与维护证据，旧版本保留。科学来源/版本缺口和原PyTorch3D构建提交未因迁移关闭。"
    report_relative = manifest["phase_prefix"].removeprefix("RAP-main/") + "/REPORT_CN.md"
    if report_relative not in state["evidence"]:
        state["evidence"].append(report_relative)
    save(state_path, state)
    spec = importlib.util.spec_from_file_location("current_renderer", rap / "scripts/maintenance/render_current_state.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    (rap / "docs/CURRENT_STATE.md").write_text(renderer.render(state), encoding="utf-8")
    agents = rap / "AGENTS.md"
    lines = agents.read_text(encoding="utf-8").splitlines()
    lines[2] = "更新：" + local_date + "，Asia/Shanghai。**A8：" + status + "。** 完整资产及全部历史常驻所租AutoDL，原A5/A7包与本地原件保留；真实收据见[A8报告](" + report_relative + ")及[服务器入口](docs/migration/AUTODL.md)。研究UNRESOLVED、论文PAUSED；不把单对示例I/O写成科学复现或可完整训练。"
    agents.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for path in (WORKSPACE / "AGENTS.md", WORKSPACE / "RAP-SLAM/AGENTS.md"):
        text = path.read_text(encoding="utf-8")
        old = next(line for line in text.splitlines() if line.startswith("更新：") or line.startswith("当前正在执行A8："))
        text = text.replace(old, "更新：" + local_date + "，Asia/Shanghai。A8：" + status + "。实际记录由RAP-main/docs/migration/AUTODL.md和统一状态页承担；原科学停止与历史缺口保持。", 1)
        path.write_text(text, encoding="utf-8")
    for relative, summary in (("README.md", "本仓库保存RAP模型、推理、预处理和完整研究档案；RAP-SLAM保留独立仓库边界。A8：" + status + "。全部历史已随文件层迁至所租AutoDL，入口见[服务器运行说明](docs/migration/AUTODL.md)。"),
                              ("docs/README.md", "A8：" + status + "。当前入口见[服务器运行说明](migration/AUTODL.md)；统一研究状态与完整训练缺口仍由当前状态页承担。"),
                              ("docs/migration/README.md", "A8实际服务器状态：" + status + "。当前证据见[AutoDL运行说明](AUTODL.md)和[A8报告](../" + report_relative.removeprefix("docs/") + ")。下文A0–A7保留原时点范围，不用旧的未选定/未安装声明替代实际收据。")):
        path = rap / relative
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[2] = summary
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    guide = rap / "docs/migration/AUTODL.md"
    text = guide.read_text(encoding="utf-8")
    text = text.replace("A8进行中；尚未声明全量迁移或训练就绪。", "A8：" + status + "。")
    text = text.replace("上传中", "分卷全量校验通过").replace("依赖安装/验收中", "环境验收通过" if functional else "环境/功能失败见收据")
    text += "\n## 实际服务器结果\n\n" + status + "。完成UTC：" + utc() + "。完整文件、POSIX、安装、CPU和GPU各层收据见[A8报告](../" + report_relative.removeprefix("docs/") + ")与同目录remote；原镜像保留指基础Python包集，SSH/Conda注册与临时运行状态不是字节不变声明。\n"
    guide.write_text(text, encoding="utf-8")
    report = phase / "REPORT_CN.md"
    report.write_text(report.read_text(encoding="utf-8") + "\n## 实际服务器最终状态\n\n" + status + "。完成UTC：" + utc() + "。\n\nA7文件层完整恢复及重新读取112,972普通文件/135,168,471,508字节；A8覆盖层" + str(len(seen)) + "文件均核对哈希，替换前" + str(len(versions)) + "份字节另存archives/source-versions/A8-control。CPU/GPU成功仅限本轮有界迁移协议；失败见remote原始收据。完整训练与精确resume未验收；原科学停止/来源/预算限制未改变。\n", encoding="utf-8")
    controls = []
    for row in manifest["current_controls"]:
        path = member("/".join(part for part in (manifest["layout"][row["root"]], row["path"]) if part))
        controls.append(dict(row, bytes=path.stat().st_size, sha256=sha(path)))
    authority = dict(stage="A8_SERVER_ACCEPTED_WITH_TRAINING_HOLDS" if functional else "A8_FILES_ACCEPTED_WITH_FUNCTIONAL_HOLDS",
        created_utc=utc(), current_files=controls, previous_authority="docs/maintenance/2026-11-04/delivery-restore-01/AUTHORITY_PROOF.json",
        A8_control_manifest_sha256=binding["manifest_sha256"], historical_scientific_claims_superseded=False,
        server_file_layer_passed=True, bounded_functional_gate_passed=bool(functional), training_validated=False)
    save(phase / "AUTHORITY_PROOF.json", authority)
    save(ROOT / "SERVER_AUTHORITY.json", authority)
    save(ROOT / "SERVER_FINALIZED.json", dict(completed_utc=utc(), server_file_layer_passed=True,
        bounded_functional_gate_passed=bool(functional), current_authority_files=len(controls),
        authority_sha256=sha(phase / "AUTHORITY_PROOF.json"), phase_prefix=manifest["phase_prefix"],
        training_or_resume_validated=False, original_historical_PyTorch3D_commit_recovered=False))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        save(ROOT / "FINALIZATION_FAILURE.json", dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise
