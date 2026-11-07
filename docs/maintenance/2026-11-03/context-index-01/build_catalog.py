"""Documentary catalog from the immutable A1 inventory; never evaluate experiment data."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A1 = REPO / "docs/maintenance/2026-11-03/migration-audit-01"
OUT = REPO / "docs/experiments"
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "reports": REPO.parent / "RAP-SLAM-report",
         "datasets": REPO.parent / "Datasets", "codex-records": Path("C:/Users/AAA/Documents/Codex"), "workspace-root": REPO.parent}
PROTECTED = "portable_graph_20261031"
CANONICAL = re.compile(r"^(?:REPORT(?:_CN|_FINAL)?|FINAL_REPORT|RESEARCH_REPORT|AUDIT_REPORT|PROTOCOL(?:_[A-Z0-9_]+)?|PHASE_RECORD|CURRENT_HANDOFF(?:_FINAL)?|HANDOFF|ASSESSMENT|DECISION|RESEARCH_MEMO|POSTMORTEM|OWNER_SCOPE|AUTHORITY|CONTEXT_CN|当前上下文|入口|最终核验说明|CLOSED_SCOPES)\.md$", re.I)
EXCLUDED = re.compile(r"(?:^|/)(?:before[^/]*|after|authority_before|source_snapshot|source_snapshots|source-snapshot|snapshot|snapshots|handoff_snapshot|source-store|git|node_modules|official-source|\.build|backup|backups)(?:/|$)", re.I)
ROLES = {"protocol": r"protocol|contract|合同|方案", "report": r"report|assessment|decision|memo|postmortem|报告",
         "context": r"handoff|context|当前上下文|入口|owner_scope|authority|phase_record"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_lines(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identity(root, path):
    return root + ":" + path


def local(row):
    return ROOTS[row["root"]] / row["path"]


def link_to(path, base=OUT):
    return quote(os.path.relpath(path, base).replace("\\", "/"), safe="/._-~")


def discover(rows):
    scopes = {}

    def add(root, path, kind):
        scopes.setdefault(identity(root, path), {"root": root, "path": path, "kind": kind})

    for row in rows:
        path, root = row["path"], row["root"]
        parts = path.split("/")
        if root == "rap-main" and path.startswith("docs/maintenance/"):
            if len(parts) >= 3 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[2]):
                add(root, "/".join(parts[:3]), "date_record")
                if len(parts) >= 4 and row["kind"] == "directory" or len(parts) >= 5:
                    add(root, "/".join(parts[:4]), "research_or_maintenance_scope")
                if row["kind"] == "file" and CANONICAL.match(parts[-1]) and len(parts) > 5 and not EXCLUDED.search(path):
                    parent = "/".join(parts[:-1])
                    if not re.search(r"/(?:controls?|packet|audit|discovery|confirmation|preflight)$", parent, re.I):
                        add(root, parent, "nested_documented_scope")
            elif len(parts) >= 3 and parts[2].startswith("audit-"):
                add(root, "/".join(parts[:3]), "audit_record")
        elif root == "codex-records":
            if "outputs" in parts:
                slot = parts.index("outputs")
                if len(parts) > slot + 1:
                    add(root, "/".join(parts[:slot + 2]), "external_documented_scope")
                    if row["kind"] == "file" and CANONICAL.match(parts[-1]) and len(parts) > slot + 3 and not EXCLUDED.search(path):
                        parent = "/".join(parts[:-1])
                        if not re.search(r"/(?:controls?|packet|audit|discovery|confirmation|preflight)$", parent, re.I):
                            add(root, parent, "nested_external_scope")
            elif "work" in parts:
                add(root, "/".join(parts[:parts.index("work") + 1]), "support_work_collection")
        elif root == "rap-slam" and parts[0].startswith("output"):
            if len(parts) > 1 or row["kind"] == "directory":
                add(root, parts[0], "legacy_saved_output")
            else:
                add(root, "", "legacy_root_log_collection")
        elif root == "rap-main" and path.startswith(".maintenance-archive/") and len(parts) >= 2:
            add(root, "/".join(parts[:2]), "preservation_snapshot")
        elif root == "rap-main" and (path.startswith("docs/meeting_") or path.startswith("working files/")):
            if len(parts) >= 2:
                add(root, "/".join(parts[:2]), "meeting_or_authoring_collection")
        elif root == "reports" and parts:
            add(root, parts[0], "report_or_manuscript_collection")
    add("rap-main", "docs/maintenance/2026-11-03/migration-audit-01", "migration_maintenance")
    add("rap-main", "docs/maintenance/2026-11-03/context-index-01", "migration_maintenance")
    add("rap-main", "scripts/maintenance", "research_tool_collection")
    for slug in ("migration-preflight-01", "migration-audit-01", "context-index-01"):
        scopes[identity("rap-main", "docs/maintenance/2026-11-03/" + slug)]["kind"] = "migration_maintenance"
    return scopes


def role(name):
    for candidate, pattern in ROLES.items():
        if re.search(pattern, name, re.I):
            return candidate
    return "documentation"


def summarize_document(path, asset):
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    title = next((line.lstrip("# ").strip() for line in lines if line.startswith("# ")), path.stem)
    excerpts = []
    in_code = False
    for n, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
        clean = line.strip()
        if in_code or not clean or clean.startswith(("#", "|", "---", "```", "![")):
            continue
        if len(excerpts) < 2:
            excerpts.append({"text": clean[:360], "truncated": len(clean) > 360, "source": asset, "line": n, "verbatim": True})
    status_lines, limitation_lines = [], []
    for n, line in enumerate(lines, 1):
        clean = line.strip()
        if not clean or len(clean) > 1400 or clean.startswith("|"):
            continue
        if len(status_lines) < 3 and re.search(r"\b(?:Status|State|Decision)\s*:|INCOMPLETE_STOPPED|STOP_THIS_|COMPLETE|门槛|已完成|未完成|未准入|保持停止", clean, re.I):
            status_lines.append({"text": clean[:420], "truncated": len(clean) > 420, "source": asset, "line": n, "scope": "document_excerpt_not_global_verdict"})
        if len(limitation_lines) < 3 and re.search(r"\bFAIL\b|\bSTOP\b|failed|failure|INCOMPLETE|budget|cap\b|timeout|unread|失败|中断|预算|上限|停止|未读|未验证", clean, re.I):
            limitation_lines.append({"text": clean[:420], "truncated": len(clean) > 420, "source": asset, "line": n, "scope": "document_excerpt_may_describe_control_or_attempt"})
    return {"title": title, "purpose_excerpts": excerpts, "declared_status_excerpts": status_lines, "failure_stop_budget_excerpts": limitation_lines}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_lines(A1 / "inventory/entries.jsonl")
    hashes = {identity(r["root"], r["path"]): r for r in read_lines(A1 / "HASHES.jsonl")}
    # A1 excluded itself; append its sealed metadata without opening any data member.
    a1_seal = load(A1 / "DELIVERY_SEAL.json")
    for record in a1_seal["files"]:
        path = A1.relative_to(REPO).as_posix() + "/" + record["path"]
        row = {"root": "rap-main", "path": path, "kind": "file", "bytes": record["bytes"], "reparse_point": False}
        rows.append(row)
        hashes[identity("rap-main", path)] = {**row, "sha256": record["sha256"]}
    for filename in ("AUTHORITY.md", "REPORT_CN.md", "STATUS.json"):
        path = PHASE / filename
        if path.exists():
            relative = path.relative_to(REPO).as_posix()
            row = {"root": "rap-main", "path": relative, "kind": "file", "bytes": path.stat().st_size, "reparse_point": False}
            rows.append(row)
            hashes[identity("rap-main", relative)] = {**row, "sha256": sha(path)}
    scopes = discover(rows)
    ordered_prefixes = sorted(scopes, key=lambda k: (-len(scopes[k]["path"]), k))
    by_root = defaultdict(list)
    for scope_id in ordered_prefixes:
        by_root[scopes[scope_id]["root"]].append(scope_id)
    assets = defaultdict(list)
    coverage = []
    for row in rows:
        if row["kind"] != "file" and not row["reparse_point"]:
            continue
        for scope_id in by_root[row["root"]]:
            prefix = scopes[scope_id]["path"]
            if not prefix and not ("/" not in row["path"] and row["path"].startswith("output")):
                continue
            if (not prefix or row["path"] == prefix or row["path"].startswith(prefix + "/")):
                assets[scope_id].append(row)
                coverage.append({"asset": identity(row["root"], row["path"]), "owner": scope_id})
                break
    owner_by_asset = {r["asset"]: r["owner"] for r in coverage}
    row_by_asset = {identity(r["root"], r["path"]): r for r in rows}
    claims_by_scope = defaultdict(Counter)
    source_claims = defaultdict(dict)
    linked_protocols = defaultdict(set)
    source_suffixes = {".py", ".ps1", ".sh", ".cpp", ".h", ".hpp", ".c", ".yaml", ".yml", ".toml"}
    with (A1 / "SEAL_CLAIMS.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            claim = json.loads(line)
            owner = owner_by_asset.get(claim["manifest"])
            if owner is None:
                continue
            claims_by_scope[owner][claim["status"]] += 1
            recorded = claim["recorded_path"].replace("\\", "/")
            if Path(recorded).suffix.lower() in source_suffixes:
                source_claims[owner][(recorded, claim["sha256"])] = {
                    "recorded_path": claim["recorded_path"], "expected_sha256": claim["sha256"],
                    "status_observed_in_A1": claim["status"], "manifest": claim["manifest"],
                    "preserved_asset": claim["preserved_asset"]}
            preserved = claim.get("preserved_asset")
            if preserved in row_by_asset and re.search(r"protocol|contract", Path(recorded).name, re.I) and recorded.lower().endswith(".md"):
                linked_protocols[owner].add(preserved)
    hash_aliases = defaultdict(list)
    for row in rows:
        h = hashes.get(identity(row["root"], row["path"]), {})
        if h.get("sha256") and row["root"] == "rap-main" and row["kind"] == "file":
            hash_aliases[h["sha256"]].append(row)
    mirrors = {}
    read_receipts = []

    def docref(row):
        asset = identity(row["root"], row["path"])
        expected = hashes.get(asset, {}).get("sha256")
        source = local(row)
        if PROTECTED in row["path"].lower():
            return {"asset": asset, "role": role(source.name), "sha256": expected, "link": None, "opaque_metadata_only": True}
        observed = sha(source)
        if expected and observed != expected:
            raise RuntimeError("Document changed since source inventory: " + asset)
        read_receipts.append({"asset": asset, "sha256": observed, "purpose": "documentary_summary_only"})
        display = source
        alias = None
        if row["root"] == "codex-records":
            choices = [r for r in hash_aliases[observed] if PROTECTED not in r["path"].lower() and Path(r["path"]).suffix.lower() == ".md"]
            if choices:
                choice = min(choices, key=lambda r: (EXCLUDED.search(r["path"]) is not None, len(r["path"]), r["path"]))
                display = local(choice)
                alias = identity(choice["root"], choice["path"])
            else:
                display = OUT / "evidence" / (observed + ".md")
                display.parent.mkdir(exist_ok=True)
                content = source.read_bytes()
                if hashlib.sha256(content).hexdigest() != observed:
                    raise RuntimeError("Source changed while copying documentary mirror")
                display.write_bytes(content)
                mirrors[observed] = {"sha256": observed, "bytes": len(content), "copy": display.relative_to(REPO).as_posix(),
                                     "source_asset": asset, "verbatim_historical_document": True, "internal_original_links_not_rewritten": True}
        summary = summarize_document(source, asset)
        return {"asset": asset, "role": role(source.name), "sha256": observed, "link": link_to(display),
                "same_bytes_repository_asset": alias, "historical_verbatim_document": True,
                "title": summary["title"], **{k: v for k, v in summary.items() if k != "title"}}

    curated = load(PHASE / "CURATED_STUDIES.json")
    overrides = {entry["scope"]: entry for entry in curated}
    missing_curated = sorted(set(overrides) - set(scopes))
    if missing_curated:
        raise RuntimeError("Curated dossier not discovered: " + repr(missing_curated))
    records = []
    shared_reports = defaultdict(list)
    for scope_id in sorted(scopes):
        scope = scopes[scope_id]
        members = assets[scope_id]
        documents = [r for r in members if Path(r["path"]).suffix.lower() == ".md" and not EXCLUDED.search(r["path"])
                     and CANONICAL.match(Path(r["path"]).name)]
        # A nested dossier owns its own documents; avoid reading an entire implementation/fixture tree.
        documents.sort(key=lambda r: (len(r["path"].split("/")), 0 if re.match(r"REPORT", Path(r["path"]).name, re.I) else 1, r["path"]))
        docs = [docref(row) for row in documents[:8]]
        primary_docs = list(docs)
        existing_docs = {d["asset"] for d in docs}
        for protocol_id in sorted(linked_protocols[scope_id]):
            if protocol_id not in existing_docs:
                docs.append(docref(row_by_asset[protocol_id]))
                existing_docs.add(protocol_id)
        summary_doc = next((d for d in primary_docs if d["role"] == "report" and not d.get("opaque_metadata_only")),
                           next((d for d in primary_docs if not d.get("opaque_metadata_only")), None))
        declared = overrides.get(scope_id)
        explicit_status = []
        if PROTECTED not in scope["path"].lower():
            for row in members:
                if Path(row["path"]).name.upper() != "STATUS.JSON" or len(Path(row["path"]).parts) > len(Path(scope["path"]).parts) + 2:
                    continue
                value = load(local(row))
                if isinstance(value, dict):
                    for field in ("status", "state", "execution_status", "decision"):
                        if isinstance(value.get(field), str):
                            explicit_status.append({"field": field, "value": value[field], "source": identity(row["root"], row["path"]),
                                                    "interpretation": "top-level declared value; no pass/fail inference"})
        purpose = declared.get("purpose") if declared else None
        if not purpose and summary_doc and summary_doc["purpose_excerpts"]:
            purpose = summary_doc["purpose_excerpts"][0]["text"]
        metadata_for = lambda pattern: [{"asset": identity(r["root"], r["path"]), "sha256": hashes.get(identity(r["root"], r["path"]), {}).get("sha256")}
                                       for r in members if re.search(pattern, Path(r["path"]).name, re.I) and r["kind"] == "file"]
        source_records = metadata_for(r"source.*(?:freeze|manifest|snapshot)|(?:freeze|manifest).*source")
        input_records = metadata_for(r"input.*(?:freeze|manifest)|cohort.*(?:freeze|manifest)|(?:input|cohort)_.*\.json$")
        seals = metadata_for(r"(?:delivery_)?seal.*\.json$")
        protocols = [d for d in docs if d["role"] == "protocol"]
        date = re.search(r"\d{4}-\d{2}-\d{2}", scope["path"])
        record = {"id": scope_id, **scope, "folder_date": date.group() if date else None,
                  "aliases": declared.get("aliases", []) if declared else [],
                  "title": summary_doc["title"] if summary_doc else scope["path"].split("/")[-1] or scope["root"],
                  "purpose": purpose, "purpose_basis": "curated_source_backed" if declared else "verbatim_document_excerpt" if purpose else "not_normalized",
                  "record_state": "METADATA_ONLY_UNREAD_PARTIALS" if PROTECTED in scope["path"].lower() else "DOCUMENTS_INDEXED" if docs else "ARTIFACTS_INDEXED_NO_PRIMARY_REPORT",
                  "execution_state": declared.get("execution_state") if declared else None,
                  "scientific_outcome": declared.get("scientific_outcome") if declared else None,
                  "declared_status_values": explicit_status, "unknown_status_is_not_success": True,
                  "documents": docs, "protocol_documents": [d["asset"] for d in protocols],
                  "code_version_evidence": source_records, "input_version_evidence": input_records,
                  "frozen_source_claims_preview": list(source_claims[scope_id].values())[:64],
                  "frozen_source_claims_total": len(source_claims[scope_id]),
                  "historical_asset_hash_claim_status_counts": dict(claims_by_scope[scope_id]),
                  "full_hash_claim_index": "rap-main:docs/maintenance/2026-11-03/migration-audit-01/SEAL_CLAIMS.jsonl",
                  "seal_evidence": seals, "artifact_count": len(members), "artifact_logical_bytes": sum(r["bytes"] for r in members),
                  "artifacts_basis": "A1 immutable inventory; A1 phase seal; current A2 documentary records only",
                  "failure_stop_budget_evidence": [e for d in docs if not d.get("opaque_metadata_only") for e in d["failure_stop_budget_excerpts"]],
                  "declared_status_excerpts": [e for d in docs if not d.get("opaque_metadata_only") for e in d["declared_status_excerpts"]],
                  "curated_evidence": declared.get("evidence", []) if declared else [],
                  "constraints": declared.get("constraints", []) if declared else [],
                  "rerun_admitted_by_catalog": False}
        if summary_doc:
            shared_reports[summary_doc["sha256"]].append(scope_id)
        records.append(record)
    for record in records:
        docs = [d for d in record["documents"] if d.get("sha256")]
        record["same_primary_document_other_scopes"] = sorted({other for d in docs for other in shared_reports[d["sha256"]] if other != record["id"]})
    with (OUT / "catalog.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    fields = ("id", "kind", "folder_date", "aliases", "title", "purpose", "record_state", "execution_state", "scientific_outcome", "artifact_count", "protocol_documents", "code_version_evidence", "input_version_evidence", "seal_evidence", "frozen_source_claims_total", "historical_asset_hash_claim_status_counts")
    with (OUT / "catalog.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({k: json.dumps(record[k], ensure_ascii=False) if isinstance(record[k], (list, dict)) else record[k] for k in fields})
    lines = ["# 实验与维护档案目录", "", "本目录登记研究、维护、旧产物和组会材料；条目数不是独立实验数。执行状态为空表示未统一解释，不能当作成功。原文的 ACTIVE/next 等文字只代表原记录时点，不构成当前任务。", "", "[阅读说明](README.md) · [当前研究状态](../CURRENT_STATE.md) · [机器索引](catalog.jsonl) · [版本缺口](GAPS.md)", ""]
    for kind in sorted({r["kind"] for r in records}):
        subset = sorted([r for r in records if r["kind"] == kind], key=lambda r: (r["folder_date"] or "", r["id"]), reverse=True)
        lines.extend(["## " + kind, "", "| 日期 | 档案 | 已明确执行状态 | 入口 |", "| --- | --- | --- | --- |"])
        for record in subset:
            doc = next((d for d in record["documents"] if d.get("link") and d["role"] == "report"), next((d for d in record["documents"] if d.get("link")), None))
            entry = f"[原始文档]({doc['link']})" if doc else "元数据登记"
            title = record["title"].replace("|", "\\|").replace("\n", " ")[:120]
            title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title).replace("<", "&lt;").replace(">", "&gt;")
            state = record["execution_state"] or "未统一解释"
            lines.append(f"| {record['folder_date'] or '未统一日期'} | `{record['id']}`<br>{title} | {state} | {entry} |")
        lines.append("")
    (OUT / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    coverage_ids = {r["asset"] for r in coverage}
    expected = [r for r in rows if (r["kind"] == "file" or r["reparse_point"]) and
                (r["root"] == "codex-records" or r["root"] == "reports" or r["root"] == "rap-main" and r["path"].startswith(("docs/maintenance/", "docs/meeting_", "working files/", ".maintenance-archive/", "scripts/maintenance/"))
                 or r["root"] == "rap-slam" and r["path"].split("/")[0].startswith("output"))]
    uncovered = [identity(r["root"], r["path"]) for r in expected if identity(r["root"], r["path"]) not in coverage_ids
                 and r["path"] not in {"docs/maintenance/README.md", "docs/maintenance/history/AGENTS.pre-maintenance-2026-09-09.md"}]
    write_json(PHASE / "INDEX_COVERAGE.json", {"expected_asset_rows": len(expected), "mapped_asset_rows": len(coverage), "uncovered": uncovered,
               "known_navigation_exclusions": ["docs/maintenance/README.md", "docs/maintenance/history/AGENTS.pre-maintenance-2026-09-09.md"]})
    with (PHASE / "ASSET_SCOPE_MAP.jsonl").open("w", encoding="utf-8") as stream:
        for row in coverage:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_json(OUT / "evidence_manifest.json", {"copies": list(mirrors.values()), "originals_modified": False,
               "historical_internal_links_are_source_text_not_current_navigation": True})
    write_json(PHASE / "DOCUMENT_READS.json", {"documents": read_receipts, "PGC1_tree_semantically_read": False})
    summary = {"scopes": len(records), "kinds": dict(Counter(r["kind"] for r in records)),
               "curated_status_records": sum(r["execution_state"] is not None for r in records),
               "documents_indexed": sum(len(r["documents"]) for r in records), "verbatim_external_mirrors": len(mirrors),
               "unique_document_assets": len({d["asset"] for r in records for d in r["documents"]}),
               "protocol_references": sum(len(r["protocol_documents"]) for r in records),
               "opaque_PGC1_records": sum(r["record_state"] == "METADATA_ONLY_UNREAD_PARTIALS" for r in records),
               "uncovered_historical_assets": len(uncovered), "scientific_evaluations_run": 0,
               "source_inventory": "migration-audit-01/inventory + its immutable seal; current A2 documents"}
    write_json(PHASE / "CATALOG_SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
