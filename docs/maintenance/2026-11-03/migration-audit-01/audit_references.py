"""Static path/link audit; read text sources, never experiment result arrays or logs."""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
from pathlib import Path
import posixpath
import re
import time
from urllib.parse import unquote

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[/\\]|/mnt/[a-zA-Z]/|/root/|/home/|/tmp/|/usr/|/opt/|/srv/)[^\s'\"`<>\[\]{}|;,)]+")
QUOTED = re.compile(r"(?P<q>['\"`])(?P<path>(?:[A-Za-z]:[/\\]|/mnt/[a-zA-Z]/|/root/|/home/|/tmp/|/usr/|/opt/|/srv/)[^\r\n'\"`<>]+)(?P=q)")
MARKDOWN = re.compile(r"!?\[[^\]\r\n]*\]\(([^)\r\n]+)\)")
TEXT_EXTS = {".py", ".ps1", ".sh", ".yaml", ".yml", ".toml", ".cfg", ".md", ".cpp", ".h", ".c", ".hpp"}
ACTIVE_CATEGORIES = {"current_code", "current_configuration", "current_maintenance_context", "environment_or_entry_script", "project_metadata", "workspace_context"}


def main():
    started = time.monotonic()
    rows, hashes, by_abs, by_hash = audit.load_state()
    references = []
    skips = []
    agents = []
    per_asset = Counter()
    extracted_cache = {}
    for row in rows:
        path = row["path"]
        low = path.casefold()
        if row["kind"] != "file" or row["reparse_point"]:
            continue
        category = audit.classify(row)[0]
        if Path(path).name == "AGENTS.md" or re.match(r"(?i)AGENTS[._-]", Path(path).name):
            agents.append({"asset": audit.key(row["root"], path), "category": category,
                           "authority_role": "current_project" if row["root"] == "rap-main" and path == "AGENTS.md" else
                                             "current_workspace" if row["root"] == "workspace-root" else "historical_or_copied_authority",
                           "sha256": hashes.get(audit.key(row["root"], path), {}).get("sha256")})
        if audit.opaque(path):
            skips.append({"asset": audit.key(row["root"], path), "reason": "PGC1 opaque preservation; no semantic inspection"})
            continue
        if category in {"git_history", "third_party_dependency", "regenerable_python_cache"}:
            continue
        suffix = Path(path).suffix.casefold()
        if suffix not in TEXT_EXTS and Path(path).name not in {"requirements.txt", "requirements_other.txt", "CMakeLists.txt"}:
            continue
        if row["bytes"] > 8 * 1024 * 1024:
            skips.append({"asset": audit.key(row["root"], path), "reason": "text over 8 MiB; preserved and held for targeted review"})
            continue
        identity = audit.key(row["root"], path)
        sha = hashes.get(identity, {}).get("sha256")
        cache_key = (sha, suffix == ".md")
        if cache_key in extracted_cache:
            extracted = extracted_cache[cache_key]
        else:
            try:
                text = audit.file_path(row).read_text(encoding="utf-8-sig", errors="strict")
            except (UnicodeError, OSError) as exc:
                skips.append({"asset": identity, "reason": type(exc).__name__})
                continue
            extracted = []
            for line_number, line in enumerate(text.splitlines(), 1):
                spans = []
                for match in QUOTED.finditer(line):
                    spans.append(match.span("path"))
                    extracted.append(("absolute", match.group("path"), line_number))
                for match in ABSOLUTE.finditer(line):
                    if any(start <= match.start() < end for start, end in spans):
                        continue
                    extracted.append(("absolute", match.group(), line_number))
                if suffix == ".md":
                    for match in MARKDOWN.finditer(line):
                        target = match.group(1).strip().strip("<>")
                        if target.startswith(("http://", "https://", "mailto:", "data:", "plugin://", "app://", "#")):
                            continue
                        extracted.append(("markdown", target, line_number))
            extracted_cache[cache_key] = extracted
        unique = {}
        for kind, raw, line in extracted:
            raw = raw.strip().rstrip(".").replace("\\\\", "\\")
            if kind == "markdown":
                raw = raw.split("#", 1)[0]
                raw = unquote(raw)
            unique.setdefault((kind, raw), []).append(line)
        for (kind, raw), lines in unique.items():
            local = audit.localize(raw)
            relative = kind == "markdown" and not local and not raw.startswith("/")
            if relative:
                local = str(audit.file_path(row).parent / raw)
            target_row = by_abs.get(audit.norm(local)) if local else None
            target_root = next((root for root, base in audit.ROOTS.items() if local and audit.norm(local) == audit.norm(base)), None)
            dynamic = any(token in raw for token in ("${", "$env:", "$HOME", "{", "*", "<", "your_", "..."))
            status = "dynamic_or_example_path" if dynamic else "linux_runtime_or_unmounted_path" if not local else None
            exists = None
            if local and not dynamic:
                try:
                    exists = Path(local).exists()
                    if target_root:
                        status = "target_is_audited_root"
                    elif target_row:
                        status = "target_in_inventory"
                    elif exists:
                        status = "external_target_exists"
                    elif any(audit.norm(local).startswith(audit.norm(base) + "\\") for base in audit.ROOTS.values()):
                        status = "missing_path_under_audited_root"
                    else:
                        status = "external_target_missing_or_inaccessible"
                except (ValueError, OSError):
                    status = "path_syntax_or_access_error"
            source_role = "current" if category in ACTIVE_CATEGORIES else "optional_or_tool" if category in {"research_or_data_tool", "optional_ros2_component", "research_support_code"} else "historical_or_artifact"
            references.append({"source_asset": identity, "source_role": source_role, "source_category": category,
                               "reference_kind": kind, "recorded_target": raw, "line_numbers": lines,
                               "mapped_local_target": local, "target_status": status, "target_exists": exists,
                               "target_asset": audit.key(target_row["root"], target_row["path"]) if target_row else target_root + ":" if target_root else None,
                               "disposition": "preserve historical spelling and provide mapping" if source_role == "historical_or_artifact"
                                              else "repair in A2 documentation or A3 path configuration; no edits during A1",
                               "target_contents_read": False})
            if target_row:
                per_asset[audit.key(target_row["root"], target_row["path"])] += 1
    claims = audit.load_jsonl(PHASE / "SEAL_CLAIMS.jsonl")
    claim_paths = {}
    for claim in claims:
        pair = (claim["manifest"], claim["recorded_path"])
        claim_paths.setdefault(pair, claim)
    for claim in claim_paths.values():
        references.append({"source_asset": claim["manifest"], "source_role": "historical_manifest", "reference_kind": "hash_manifest_path",
                           "recorded_target": claim["recorded_path"], "target_status": claim["status"],
                           "target_asset": claim["preserved_asset"], "disposition": "preserve manifest and historical path; map exact bytes separately",
                           "target_contents_read": False})
    audit.write_jsonl("REFERENCES.jsonl", references)
    unresolved = [r for r in references if r["target_status"] not in {"target_in_inventory", "target_is_audited_root", "match_at_recorded_resolution"}]
    audit.write_jsonl("REFERENCE_REVIEW.jsonl", unresolved)
    audit.write_jsonl("CURRENT_REFERENCE_REVIEW.jsonl", [r for r in unresolved if r["source_role"] == "current"])
    audit.write_jsonl("TEXT_SCAN_SKIPS.jsonl", skips)
    audit.write_json("AUTHORITY_INDEX.json", agents)
    audit.write_json("REFERENCE_COUNTS_BY_ASSET.json", dict(per_asset))
    outside = {}
    for reference in references:
        if reference.get("target_status") in {"external_target_exists", "linux_runtime_or_unmounted_path", "external_target_missing_or_inaccessible"}:
            raw = reference["recorded_target"]
            record = outside.setdefault(raw, {"recorded_path": raw, "target_status": reference["target_status"], "sources": [],
                                             "disposition": "classify as environment/runtime, historical source, staging location, or additional project asset before migration"})
            if len(record["sources"]) < 6:
                record["sources"].append(reference["source_asset"])
    audit.write_jsonl("EXTERNAL_PATHS.jsonl", outside.values())
    summary = {"finished_utc": audit.utc(), "seconds": time.monotonic() - started,
               "reference_edges": len(references), "target_status": dict(Counter(r["target_status"] for r in references)),
               "source_roles": dict(Counter(r["source_role"] for r in references)),
               "current_review_edges": sum(r["source_role"] == "current" for r in unresolved),
               "authority_files": len(agents), "skips": dict(Counter(r["reason"] for r in skips)),
               "external_unique_paths": len(outside), "project_asset_discovery_closed": False,
               "limit": "Static text/manifest path audit; constructed runtime paths and Linux filesystem internals require A3/A4. No partial PGC1 output interpreted."}
    audit.write_json("REFERENCE_SUMMARY.json", summary)
    print(__import__("json").dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
