"""Stage the two outer context pointers without writing outside RAP-main."""
from pathlib import Path

phase = Path(__file__).resolve().parent
folder = phase / "staged-external"
folder.mkdir(exist_ok=True)
parent = (phase / "before/workspace-root/AGENTS.md").read_text(encoding="utf-8")
lines = parent.splitlines()
lines[2] = "更新：2026-11-06，Asia/Shanghai。所有者已租用AutoDL并明确授权连接、传输和实际迁移。A8的SSH/目标预检通过，全量封存包上传和独立环境安装进行中；服务器恢复、环境与功能验收尚未完成。当前收据和下一步由[RAP-main的A8入口](RAP-main/docs/migration/AUTODL.md)与统一状态页承担，A7原封存及本地证明保留。"
parent = "\n".join(lines) + "\n"
parent = parent.replace("服务器用于继续研究与训练，尚未选定；", "服务器已选AutoDL，用于继续研究与训练；")
parent = parent.replace("不自动购买/部署/发送材料或改写 Git 历史。", "不自动购买、向其它目的地发送材料或改写Git历史；本次明确授权向指定AutoDL传输/恢复、独立安装及有限迁移验收，详见A8授权。")
(folder / "workspace-root.AGENTS.md").write_text(parent, encoding="utf-8")
slam = (phase / "before/rap-slam/AGENTS.md").read_text(encoding="utf-8")
old = next(line for line in slam.splitlines() if line.startswith("当前处于迁移前工程维护："))
new = "当前正在执行A8：服务器已租用AutoDL，SSH与目标预检通过，全量资产上传和独立环境安装进行中；后续完整恢复/哈希、五项路径、CPU/GPU及单对示例模型I/O按[RAP-main的A8入口](../RAP-main/docs/migration/AUTODL.md)与有界协议验收。尚未声明迁移完成或训练就绪；全部实验历史常驻服务器。A7原交付和以下A4执行范围均为历史事实，原封存保留。组会版本/参考PDF/原生导出、来源/原构建提交和完整训练链等缺口继续跟踪。"
(folder / "rap-slam.AGENTS.md").write_text(slam.replace(old, new), encoding="utf-8")
print("Staged two context pointers; originals unchanged")
