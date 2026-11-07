"""Render the single machine-readable current state into the human navigation page."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def render(state):
    migration, research, holds = state["migration"], state["research"], state["preservation_holds"]
    lines = ["# 当前状态", "", f"更新：{state['updated_local_date']}，{state['timezone']}。本页由 CURRENT_STATE.json 生成。", "",
             f"当前工作：**{state['current_work']}**。研究 **{research['status']}**，论文 **{research['manuscript']}**。", "",
             state["owner_scope"] + "。", "", "## 迁移进度", "", "| 阶段 | 当前状态 |", "| --- | --- |"]
    for stage in sorted((key for key in migration if key.startswith("A") and key[1:].isdigit()), key=lambda key: int(key[1:])):
        lines.append(f"| {stage} | {migration[stage]} |")
    server_status = ("服务器已选定，文件迁移已验收。" if migration.get("server_migration_complete") else
                     "服务器已选定，实际迁移/验收进行中。" if migration.get("server_selected") else
                     "服务器尚未选定，正式迁移未完成。")
    lines.extend(["", server_status + state["maintenance_summary"], "",
                  f"**下一步：{state['next_step']['stage']}，{state['next_step']['purpose']}。**", "",
                  "## 科学结论边界", "",
                  f"- GCG1 保持 {research['GCG1_correct_accepted']} 正确/{research['GCG1_wrong_accepted']} 错误接受，无正确接受增益。",
                  f"- PGC1：{research['PGC1']}；原 {research['PGC1_original_actions']} actions/第 {research['PGC1_stop_pair']} 对停止，七份部分准确率未解释读取。",
                  f"- SSC1：{research['SSC1']}；oldunique00/08={research['SSC1_oldunique00_08'][0]}/{research['SSC1_oldunique00_08'][1]}，未过各至少 {research['SSC1_frozen_target_minimum_each']} 的固定门槛。原监督失败、复用/续算和资源上限保留，不救活该路线。",
                  "- EIA1/SRA1 为来源/字节准入，不证明身份独立性或物理基线；SAC1 的相干别名与 MCV1 的计数/秩不足结论保留。",
                  "- official MAC 数值未准入、未运行；E0 工程正面结果和混合比较范围限制均保留。没有新的安全增益或训练资格。", "",
                  "完整分母、参数、失败、中断、原始/校正帧区别及来源限制见原协议/报告。最后研究轮次的关闭和账户观察是历史记录，不是本轮可用性查询或新续跑授权。", "",
                  "## 未决项", "",
                  f"- {holds['historical_source_digest_gaps']} 个旧源码哈希和 {holds['historical_AGENTS_version_gaps']} 个旧 AGENTS 中间版本未恢复；原声明及已找到的版本保留。",
                  f"- 原 {holds.get('linux_environment_hash_claim_occurrences_exact_matched_in_A4', 0)} 条 Linux 环境哈希声明已在 A4 精确匹配；仍待核对 {holds['linux_environment_hash_claim_occurrences_pending_A4']} 条。原构建提交与目标重建另行验收。",
                  "- 工作区外动态引用闭包、raw/OXTS 来源认证、完整训练/恢复链仍未完成。",
                  ("- 组会/制作链已在 A6 审计；终稿版本差异、参考 PDF 原件和新原生导出验收保留，见组会总入口。"
                   if holds.get("meeting_final_versions_and_authoring_chain_reviewed", False) else "- 组会最终版本与制作链待 A6 核对。"),
                  "- 全部历史需常驻服务器；缓存、重复副本和 Git tmp 对象仍只是已登记的后续候选。", "",
                  "## 权威来源与导航", "",
                  "[项目约定](CONVENTIONS.md) · [实验索引](experiments/README.md) · [缺口表](experiments/GAPS.md) · [迁移入口](migration/README.md)", ""])
    for source in state["evidence"]:
        relative = Path(source).relative_to("docs").as_posix()
        lines.append(f"- [{Path(source).name}]({relative})")
    return "\n".join(lines) + "\n"


def main():
    state = json.loads((REPO / "docs/CURRENT_STATE.json").read_text(encoding="utf-8"))
    (REPO / "docs/CURRENT_STATE.md").write_text(render(state), encoding="utf-8")


if __name__ == "__main__":
    main()
