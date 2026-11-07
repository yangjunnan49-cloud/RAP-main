"""Validate current navigation, catalog provenance and preserved originals. No experiments."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A1 = REPO / "docs/maintenance/2026-11-03/migration-audit-01"
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent,
         "reports": REPO.parent / "RAP-SLAM-report", "datasets": REPO.parent / "Datasets",
         "codex-records": Path("C:/Users/AAA/Documents/Codex")}


def check(value, message):
    if not value:
        raise AssertionError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def lines(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_file(path, item):
    check(Path(path).stat().st_size == item["bytes"], "Length mismatch: " + str(path))
    check(sha(path) == item["sha256"], "Hash mismatch: " + str(path))


def resolve(asset):
    root, relative = asset.split(":", 1)
    check(root in ROOTS, "Unknown asset root")
    check(not Path(relative).is_absolute() and ".." not in relative.replace("\\", "/").split("/"), "Invalid source identity")
    return ROOTS[root] / relative


def main():
    baseline = load(PHASE / "BASELINE.json")
    before_by_source = {str(Path(r["source"])).casefold(): r for r in baseline["backups"]}
    for item in baseline["backups"]:
        verify_file(PHASE / item["backup"], item)
    proof = load(PHASE / "AUTHORITY_PROOF.json")
    for item in proof["current_files"]:
        verify_file(ROOTS[item["root"]] / item["path"], item)
    previous = load(A1 / "AUTHORITY_PROOF.json")
    for old in previous["current_files"]:
        backup = before_by_source[str(REPO / old["path"]).casefold()]
        check(old["sha256"] == backup["sha256"] and old["bytes"] == backup["bytes"], "A1 authority chain gap")
    for scope in ("internal", "external"):
        for item in load(PHASE / ("INSTALL_" + scope.upper() + ".json")):
            check(sha(item["target"]) == item["new_sha256"], "Installed document changed")
    state = load(REPO / "docs/CURRENT_STATE.json")
    check(state["migration"]["A2"] == "COMPLETE_DOCUMENTATION_AND_CATALOG" and state["next_step"]["stage"] == "A3", "Current stage inconsistent")
    check(state["research"]["status"] == "UNRESOLVED" and state["research"]["manuscript"] == "PAUSED", "Research state changed")
    check(state["research"]["GCG1_correct_accepted"] == 37 and state["research"]["GCG1_wrong_accepted"] == 8, "GCG1 changed")
    check(state["research"]["PGC1_partial_accuracies_interpreted"] is False and state["research"]["PGC1_original_actions"] == 64, "PGC1 boundary changed")
    check(state["preservation_holds"]["historical_source_digest_gaps"] == 5 and state["preservation_holds"]["historical_AGENTS_version_gaps"] == 1, "Gaps lost")
    spec = importlib.util.spec_from_file_location("current_state_renderer", PHASE / "render_state.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    check(renderer.render(state) == (REPO / "docs/CURRENT_STATE.md").read_text(encoding="utf-8"), "Human state differs from machine state")

    catalog = lines(REPO / "docs/experiments/catalog.jsonl")
    check(len(catalog) == len({r["id"] for r in catalog}) == 482, "Catalog identity coverage mismatch")
    check(sum(r["execution_state"] is not None for r in catalog) == 25, "Curated status count changed")
    check(all(r["rerun_admitted_by_catalog"] is False for r in catalog), "Catalog authorizes a rerun")
    curated = {r["scope"]: r for r in load(PHASE / "CURATED_STUDIES.json")}
    document_checks = {}
    evidence_checks = {}
    for row in catalog:
        check(row["id"] == row["root"] + ":" + row["path"], "Invalid dossier key")
        check((ROOTS[row["root"]] / row["path"]).exists(), "Dossier path does not exist")
        if row["execution_state"] is not None:
            check(row["id"] in curated and row["execution_state"] == curated[row["id"]]["execution_state"], "Unbacked normalized state")
        else:
            check(row["scientific_outcome"] is None, "Unknown state inferred as outcome")
        for asset in row["curated_evidence"]:
            check(resolve(asset).is_file(), "Curated evidence missing: " + asset)
        opaque = "portable_graph_20261031" in row["path"].lower()
        if opaque:
            check(row["record_state"] == "METADATA_ONLY_UNREAD_PARTIALS", "PGC1 not opaque")
            check(row["failure_stop_budget_evidence"] == [] and row["declared_status_excerpts"] == [], "PGC1 partial content extracted")
        for doc in row["documents"]:
            check(resolve(doc["asset"]).is_file(), "Document pointer missing")
            if doc.get("opaque_metadata_only"):
                check("portable_graph_20261031" in doc["asset"].lower() and doc["link"] is None, "Invalid opaque document")
                continue
            document_checks[doc["asset"]] = doc["sha256"]
            display = REPO / "docs/experiments" / unquote(doc["link"])
            check(display.is_file() and sha(display) == doc["sha256"], "Display document does not preserve source bytes")
            for excerpt in doc["purpose_excerpts"] + doc["declared_status_excerpts"] + doc["failure_stop_budget_excerpts"]:
                check(excerpt["source"] == doc["asset"] and excerpt["line"] >= 1, "Excerpt citation missing")
        for field in ("code_version_evidence", "input_version_evidence", "seal_evidence"):
            for item in row[field]:
                check(resolve(item["asset"]).is_file(), "Version/input/seal pointer missing")
                if item["sha256"]:
                    evidence_checks[item["asset"]] = item["sha256"]
    for asset, digest in document_checks.items():
        check(sha(resolve(asset)) == digest, "Original documentary source changed")
    for asset, digest in evidence_checks.items():
        check(sha(resolve(asset)) == digest, "Version/input/seal metadata changed")
    reads = load(PHASE / "DOCUMENT_READS.json")
    check(not any("portable_graph_20261031" in r["asset"].lower() for r in reads["documents"]), "PGC1 tree semantically read")
    check(reads["PGC1_tree_semantically_read"] is False, "PGC1 read guard missing")
    mirrors = load(REPO / "docs/experiments/evidence_manifest.json")["copies"]
    check(len(mirrors) == 11, "Unexpected mirror count")
    for item in mirrors:
        verify_file(REPO / item["copy"], item)
        check(sha(resolve(item["source_asset"])) == item["sha256"], "External source differs from mirror")
    coverage = load(PHASE / "INDEX_COVERAGE.json")
    check(coverage["uncovered"] == [], "Historical asset missing from catalog")
    mapping = lines(PHASE / "ASSET_SCOPE_MAP.jsonl")
    check(len(mapping) == len({r["asset"] for r in mapping}), "Asset has multiple catalog owners")
    valid_ids = {r["id"] for r in catalog}
    check(all(r["owner"] in valid_ids for r in mapping), "Invalid catalog owner")
    query_script = REPO / "scripts/maintenance/query_experiments.py"
    query_results = []
    for args, expected in ((["--alias", "PGC1"], 2), (["--alias", "SSC1"], 1), (["--kind", "legacy_saved_output"], 41)):
        result = subprocess.run([sys.executable, "-I", "-B", str(query_script), *args, "--json"],
                                cwd=REPO / "docs", capture_output=True, text=True, encoding="utf-8", timeout=30,
                                env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        check(result.returncode == 0, "Catalog query failed")
        values = json.loads(result.stdout)
        check(len(values) == expected, "Catalog query result count mismatch")
        if args == ["--alias", "PGC1"]:
            check(all(r["execution_state"] == "INCOMPLETE_STOPPED_UNREAD_PARTIALS" for r in values), "Stopped state lost in query")
        query_results.append({"args": args, "matched_records": len(values), "from_different_working_directory": True})

    markdown = [ROOTS[r["root"]] / r["path"] for r in proof["current_files"] if r["path"].lower().endswith(".md") and "/evidence/" not in r["path"]]
    markdown.append(PHASE / "REPORT_CN.md")
    link_count = 0
    for document in markdown:
        text = document.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = unquote(target.split("#")[0])
            if not target or re.match(r"^[a-z]+://|^mailto:", target):
                continue
            check((document.parent / target).exists(), "Missing current navigation link: " + str(document) + " -> " + target)
            link_count += 1
    for path, bound in ((REPO / "AGENTS.md", 16384), (REPO.parent / "AGENTS.md", 8192), (REPO.parent / "RAP-SLAM/AGENTS.md", 8192)):
        check(path.stat().st_size <= bound, "Current AGENTS too large")

    original = lines(A1 / "inventory/entries.jsonl")
    hash_records = {r["root"] + ":" + r["path"]: r for r in lines(A1 / "HASHES.jsonl")}
    allowed = set()
    for item in baseline["backups"]:
        for root in ("rap-main", "rap-slam", "workspace-root"):
            try:
                relative = Path(item["source"]).relative_to(ROOTS[root]).as_posix()
            except ValueError:
                continue
            allowed.add(root + ":" + relative)
            break
    source_count = 0
    metadata_count = 0
    code_suffixes = {".py", ".ps1", ".sh", ".yaml", ".yml", ".toml", ".cpp", ".h", ".hpp", ".c"}
    for row in original:
        path = ROOTS[row["root"]] / row["path"]
        # lstat checks the entry itself; exists() would dereference unsupported LX links.
        path.lstat()
        if row["kind"] != "file" or row["reparse_point"]:
            continue
        asset = row["root"] + ":" + row["path"]
        stat = path.stat()
        h = hash_records[asset]
        if asset not in allowed:
            check(stat.st_size == row["bytes"] and stat.st_mtime_ns == h["mtime_ns"], "Unexpected original change: " + asset)
            if Path(row["path"]).suffix.lower() in code_suffixes:
                check(sha(path) == h["sha256"], "Existing source/config changed: " + asset)
                source_count += 1
        metadata_count += 1
    prior_seal_counts = {}
    for folder in (REPO / "docs/maintenance/2026-11-03/migration-preflight-01", A1):
        entries = load(folder / "DELIVERY_SEAL.json")["files"]
        for item in entries:
            verify_file(folder / item["path"], item)
        prior_seal_counts[folder.name] = len(entries)
    scientific = 0
    for scope in ("identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"):
        folder = REPO / "docs/maintenance/2026-11-03" / scope
        for item in load(folder / "DELIVERY_SEAL.json")["files"]:
            verify_file(folder / item["path"], item)
            scientific += 1
    check(scientific == 2047, "Scientific seal count mismatch")
    result = {"passed": True, "stage": "A2_COMPLETE_DOCUMENTATION_AND_CATALOG", "catalog_records": len(catalog),
              "curated_records": 25, "unique_source_documents_sha256_verified": len(document_checks),
              "unique_version_input_seal_metadata_sha256_verified": len(evidence_checks),
              "current_navigation_links_verified": link_count, "verbatim_external_mirrors_verified": len(mirrors),
              "historical_asset_owner_rows_verified": len(mapping), "uncovered_historical_assets": 0,
              "query_acceptance_checks": query_results, "existing_regular_file_metadata_verified": metadata_count,
              "existing_source_config_files_sha256_unchanged": source_count, "prior_phase_seal_entries_verified": prior_seal_counts,
              "old_scientific_seal_entries_verified": scientific, "original_document_backups_verified": len(baseline["backups"]),
              "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
              "PGC1_partial_accuracies_interpreted": False, "WSL_GPU_model_training_or_research_started": False,
              "historical_internal_links_rewritten": False, "next_stage": "A3", "server_migration_complete": False}
    (PHASE / "CHECKS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
