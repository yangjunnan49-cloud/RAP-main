"""Classify audit holds and connect dry-run actions to concrete preservation evidence."""
from __future__ import annotations

from collections import Counter
import csv
import importlib.util
import json
import os
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def normalize_label(filename):
    source = PHASE / filename
    target = PHASE / (filename + ".new")
    with source.open(encoding="utf-8") as incoming, target.open("w", encoding="utf-8", newline="\n") as outgoing:
        for line in incoming:
            outgoing.write(line.replace('"exact_historical_bytes_recovered_from_git"', '"exact_historical_bytes_recovered"'))
    os.replace(target, source)


def main():
    for filename in ("SEAL_CLAIMS.jsonl", "SEAL_EXCEPTIONS.jsonl", "SEAL_SUMMARY.json", "ANALYSIS_SUMMARY.json",
                     "REFERENCES.jsonl", "REFERENCE_REVIEW.jsonl", "REFERENCE_SUMMARY.json"):
        normalize_label(filename)
    rows = audit.metadata()
    by_asset = {audit.key(r["root"], r["path"]): r for r in rows}
    reference_counts = audit.read_json(PHASE / "REFERENCE_COUNTS_BY_ASSET.json")
    snapshots = {r["asset"]: r for r in audit.load_jsonl(PHASE / "SOURCE_PRESERVATION.jsonl")}
    rules = []
    exceptions = audit.load_jsonl(PHASE / "SEAL_EXCEPTIONS.jsonl")
    for claim in exceptions:
        status, path, manifest = claim["status"], claim["recorded_path"], claim["manifest"]
        if status == "expected_negative_control_digest_mismatch":
            category, next_step = "expected_negative_control", "保留 WLC1 原始负对照和错误哈希，不修正测试夹具。"
            evidence = "docs/maintenance/2026-11-03/windows-lease-01/source_mismatch/SOURCE_FREEZE.json"
        elif "/overlap_validation_20261021/synthetic_fixture/freeze.json" in manifest and re.search(r"synthetic_\d{6}\.bin$", path):
            category, next_step = "virtual_synthetic_source_declaration", "保留虚拟输入声明；这些名称由测试源码构造，不作为真实数据文件缺失。"
            evidence = "codex-records:2026-10-21/y/work/overlap_validation_01/synthetic_validation.py:16-18"
        elif "/overlap_validation_20261021/synthetic_fixture/bank_seal02.json" in manifest and path == "exact/poses.npy":
            category, next_step = "intentionally_corrupted_synthetic_fixture", "保留已污染的合成测试原件和污染前 seal，维持原失败检测证据。"
            evidence = "codex-records:2026-10-21/y/work/overlap_validation_01/synthetic_validation.py:40-45"
        elif path.startswith(("/root/", "/usr/", "/home/", "/opt/")) and "no_exact_copy" in status:
            category, next_step = "linux_environment_not_inspected", "A4 在明确环境采集范围内核对 Linux 文件、版本和本地补丁；当前不声明文件已丢失。"
            evidence = "WSL image internals excluded from A1; ENVIRONMENT_IMAGES.json in A0"
        elif status == "historical_external_runtime_changed":
            category, next_step = "historical_windows_runtime_changed", "记录历史工具二进制与当前工具不同；不得用当前版本冒充旧版本，A4 建立版本来源说明。"
            evidence = "RECOVERED_SOURCES.json:external_observations"
        elif "no_exact_copy" in status and Path(path.replace("\\", "/")).name in {"AGENTS.md", "PHASE_RECORD.md"}:
            category, next_step = "unrecovered_historical_mutable_context", "A2 在历史上下文索引中保留旧哈希和版本缺口；当前入口校验由新证明承担，不重写旧 seal。"
            evidence = "RECOVERED_SOURCES.json; existing context full texts and Git byte search"
        elif "no_exact_copy" in status:
            category, next_step = "unrecovered_historical_source_or_asset", "保留原路径、旧哈希和当前字节；在实验索引明列复现缺口，不能将现代码替换成旧源码证明。"
            evidence = "RECOVERED_SOURCES.json; ARCHIVE_SOURCE_SEARCH.json"
        elif status == "exact_historical_bytes_recovered":
            category, next_step = "exact_historical_bytes_recovered", "使用本轮 recovered-sources 中的原字节作为迁移解析映射；不改写旧路径和原件。"
            evidence = "RECOVERED_SOURCES.json"
        elif status == "referenced_external_runtime_matches":
            category, next_step = "external_runtime_digest_verified", "保留验证收据；按 A4 区分 Windows 维护工具与 Linux 研究运行时。"
            evidence = "RECOVERED_SOURCES.json:external_observations"
        else:
            category, next_step = "exact_bytes_preserved_at_other_path", "迁移解析器按保存位置和校验值映射；原始清单不改写。"
            evidence = "SEAL_CLAIMS.jsonl:preserved_asset"
        rules.append({"manifest": manifest, "json_location": claim["json_location"], "recorded_path": path,
                      "sha256": claim["sha256"], "raw_status": status, "review_category": category,
                      "next_step": next_step, "evidence": evidence, "original_modified": False})
    audit.write_jsonl("REVIEWED_SEAL_EXCEPTIONS.jsonl", rules)
    counts = Counter(r["review_category"] for r in rules)
    genuine = [r for r in rules if r["review_category"] in {"unrecovered_historical_source_or_asset", "unrecovered_historical_mutable_context"}]
    unique = {}
    for row in genuine:
        unique.setdefault((row["recorded_path"], row["sha256"]), row)
    audit.write_json("PRESERVATION_GAPS.json", {"review_categories": dict(counts), "unrecovered_entries": list(unique.values()),
                     "unique_missing_source_digests": len({r["sha256"] for r in genuine if r["review_category"] == "unrecovered_historical_source_or_asset"}),
                     "note": "Pre-existing provenance gaps, not files deleted by this audit. Linux environment is uninspected rather than declared missing; virtual and negative fixtures retained."})
    ledger = audit.load_jsonl(PHASE / "ASSET_LEDGER.jsonl")
    cache_rows = []
    for row in ledger:
        row["direct_static_reference_count"] = reference_counts.get(row["asset"], 0)
        row["preservation_copy"] = snapshots.get(row["asset"], {}).get("backup")
        if row["proposed_action"] != "cache_removal_candidate_after_reference_review":
            continue
        filename = Path(row["path"])
        stem = re.sub(r"\.(?:cpython|pypy)-\d+(?:\.opt-\d+)?$", "", filename.stem)
        source = filename.parent.parent / (stem + ".py") if filename.parent.name == "__pycache__" else filename.with_suffix(".py")
        source_id = audit.key(row["root"], source.as_posix())
        paired = by_asset.get(source_id)
        row["cache_source_asset"] = source_id
        row["cache_source_present"] = paired is not None
        if not paired:
            row["proposed_action"] = "hold_orphan_bytecode"
            row["cache_review"] = "对应源码不存在；字节码可能具有独有保全价值，保留。"
        elif row["direct_static_reference_count"]:
            row["proposed_action"] = "hold_referenced_cache"
            row["cache_review"] = "存在静态引用，保留并在 A3 核对。"
        else:
            row["proposed_action"] = "cache_removal_candidate_after_A4_recipe"
            row["cache_review"] = "对应源码存在且已备份、无显式静态引用、未被 seal 保护；待环境重建约定验证后处理。"
        cache_rows.append(row)
    audit.write_jsonl("ASSET_LEDGER.jsonl", ledger)
    audit.write_jsonl("CACHE_CANDIDATES.jsonl", cache_rows)
    fields = ("asset", "category", "git_status", "bytes", "sha256", "reparse_metadata_sha256", "hash_status", "protected",
              "seal_claim_count", "direct_static_reference_count", "proposed_action", "action_executed", "proposed_target",
              "rollback_location", "preservation_copy", "ownership_basis")
    with (PHASE / "DISPOSITION_DRY_RUN.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ledger)
    classification = audit.read_json(PHASE / "CLASSIFICATION_SUMMARY.json")
    classification["proposed_actions"] = dict(Counter(r["proposed_action"] for r in ledger))
    classification["cache_review"] = dict(Counter(r["proposed_action"] for r in cache_rows))
    classification["source_backup_paths_in_ledger"] = sum(bool(r["preservation_copy"]) for r in ledger)
    audit.write_json("CLASSIFICATION_SUMMARY.json", classification)
    external = audit.load_jsonl(PHASE / "EXTERNAL_PATHS.jsonl")
    for row in external:
        path = row["recorded_path"].lower().replace("\\", "/")
        if path.endswith(".vhdx") or "/wsl/" in path or "/wsl-backup/" in path:
            group, stage = "environment_image", "A4"
        elif "/node/" in path or "node_modules" in path:
            group, stage = "meeting_authoring_runtime", "A6"
        elif path.startswith(("/root/", "/usr/", "/home/", "/opt/")) or "codex-runtimes" in path:
            group, stage = "linux_or_windows_runtime_dependency", "A4"
        elif path.startswith("/tmp/"):
            group, stage = "historical_temporary_staging", "A2/A4"
        else:
            group, stage = "historical_external_or_dynamic_path", "A2/A3"
        row.update(asset_class=group, next_stage=stage, preserve_original=True, automatically_followed=False)
    audit.write_jsonl("EXTERNAL_PATHS.jsonl", external)
    summary = {"finished_utc": audit.utc(), "reviewed_seal_exception_categories": dict(counts),
               "unique_unrecovered_scientific_source_digests": audit.read_json(PHASE / "PRESERVATION_GAPS.json")["unique_missing_source_digests"],
               "cache_actions": classification["cache_review"], "source_preservation_paths": classification["source_backup_paths_in_ledger"],
               "external_path_next_stages": dict(Counter(r["next_stage"] for r in external)),
               "all_106794_file_or_link_rows_have_disposition": len(ledger) == 106794,
               "actual_original_asset_moves_or_deletions": 0,
               "A1_status": "COMPLETE_FOR_ENUMERATED_WINDOWS_ROOTS_WITH_EXPLICIT_HOLDS",
               "project_wide_external_closure": False, "next_stage": "A2 context and experiment index; A3/A4/A6 holds remain explicit"}
    audit.write_json("A1_SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
