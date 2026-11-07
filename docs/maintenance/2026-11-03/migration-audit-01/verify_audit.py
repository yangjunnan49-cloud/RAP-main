"""Independent consistency and preservation checks. No project or experiment execution."""
from __future__ import annotations

from collections import Counter
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
import unicodedata

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_file(path, record):
    path = Path(path)
    check(path.stat().st_size == record["bytes"], "Length mismatch: " + str(path))
    check(audit.sha_file(path) == record["sha256"], "SHA256 mismatch: " + str(path))


def current_inventory():
    found = {}
    for root, base in audit.ROOTS.items():
        pending = [base]
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    if audit.norm(entry.path) == audit.norm(PHASE):
                        continue
                    stat = entry.stat(follow_symlinks=False)
                    relative = Path(entry.path).relative_to(base).as_posix()
                    link = bool(stat.st_file_attributes & 0x400)
                    is_directory = bool(stat.st_file_attributes & 0x10)
                    found[audit.key(root, relative)] = {"bytes": 0 if is_directory else stat.st_size,
                        "mtime_ns": stat.st_mtime_ns, "reparse_point": link, "directory": is_directory}
                    if root != "workspace-root" and is_directory and not link:
                        pending.append(Path(entry.path))
    return found


def main():
    metadata = audit.metadata()
    hashes_list = audit.load_jsonl(PHASE / "HASHES.jsonl")
    hashes = {audit.key(r["root"], r["path"]): r for r in hashes_list}
    ledger = audit.load_jsonl(PHASE / "ASSET_LEDGER.jsonl")
    directories = audit.load_jsonl(PHASE / "DIRECTORY_LEDGER.jsonl")
    keys = {audit.key(r["root"], r["path"]) for r in metadata}
    check(len(keys) == len(metadata), "Duplicate metadata identity")
    check(len(hashes) == len(hashes_list) == 106794, "Hash/metadata coverage mismatch")
    check(len(ledger) == 106794 and len(directories) == 4487, "Disposition count mismatch")
    check({r["asset"] for r in ledger + directories} == keys, "Disposition coverage mismatch")
    regular = [r for r in metadata if r["kind"] == "file" and not r["reparse_point"]]
    check(len(regular) == 106767, "Unexpected regular file count")
    check(sum(r["bytes"] for r in regular) == 130829441174, "Regular file byte tally mismatch")
    check(Counter(r["status"] for r in hashes_list) == {"sha256": 106767, "reparse_metadata": 27}, "Hash errors or missing link metadata")
    targets = set()
    for row in ledger:
        h = hashes[row["asset"]]
        check(row["action_executed"] is False, "Unexpected executed action")
        check(row["sha256"] == h.get("sha256"), "Ledger hash mismatch")
        check(row["hash_status"] == h["status"], "Ledger hash status mismatch")
        check(row["category"] != "unclassified_review", "Unclassified asset")
        target = unicodedata.normalize("NFC", row["proposed_target"]).casefold()
        check(target not in targets, "Target collision")
        check(not target.startswith("/") and ".." not in target.split("/"), "Unsafe proposed target")
        targets.add(target)
    now = current_inventory()
    check(set(now) == keys, "Asset names added or lost outside maintenance phase")
    mutable = {"rap-main:AGENTS.md", "rap-main:docs/migration/README.md", "rap-main:docs/migration/PLAN.md"}
    changes = []
    for identity, h in hashes.items():
        item = now[identity]
        before = h.get("mtime_ns")
        same = item["bytes"] == h["bytes"] and item["mtime_ns"] == before
        if not same:
            check(identity in mutable, "Unexpected original asset change: " + identity)
            changes.append(identity)
    proof = audit.read_json(PHASE / "AUTHORITY_PROOF.json")
    for record in proof["current_files"]:
        verify_file(audit.REPO / record["path"], record)
    for record in proof["before_files"]:
        verify_file(PHASE / record["path"], record)
    previous = audit.read_json(audit.REPO / "docs/maintenance/2026-11-03/migration-preflight-01/AUTHORITY_PROOF.json")
    for entry in previous["files"]:
        backup = PHASE / "before" / entry["path"]
        verify_file(backup, entry)
    for root in ("rap-main", "rap-slam"):
        state = audit.read_json(PHASE / "git" / root / "STATE.json")
        head = (audit.ROOTS[root] / ".git/HEAD").read_text().strip()
        check(head == "ref: refs/heads/" + state["branch"], "Branch changed")
        tip = (audit.ROOTS[root] / ".git" / head[5:]).read_text().strip()
        check(tip == state["head"], "HEAD changed")
    preserve = audit.load_jsonl(PHASE / "SOURCE_PRESERVATION.jsonl")
    unique = {}
    for row in preserve:
        check(hashes[row["asset"]]["sha256"] == row["sha256"], "Source alias mismatch")
        unique.setdefault(row["sha256"], row)
    for row in unique.values():
        verify_file(PHASE / row["backup"], row)
    recovered = audit.read_json(PHASE / "RECOVERED_SOURCES.json")["recovered"]
    check(len(recovered) == 17, "Unexpected recovered source count")
    for row in recovered:
        verify_file(PHASE / row["backup"], row)
    links = audit.read_json(PHASE / "LINKS_RESOLVED.json")
    check(len(links) == 27 and Counter(r["kind"] for r in links) == {"linux_symlink": 25, "junction": 2}, "Link count/type mismatch")
    for row in links:
        raw = base64.b64decode(row["raw_base64"])
        check(hashlib.sha256(raw).hexdigest() == row["raw_sha256"], "Preserved reparse bytes mismatch")
        check(audit.reparse_data(audit.ROOTS[row["root"]] / row["path"])["raw_sha256"] == row["raw_sha256"], "Original link changed")
        if row["kind"] == "linux_symlink":
            check(row["target_exists"] and row["target_in_inventory"], "Linux link target absent")
    sample = random.Random(20261103).sample(regular, 64)
    for row in sample:
        # Independent chunked SHA256, distinct from the original file_digest call.
        sha = hashlib.sha256()
        with audit.file_path(row).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1048576), b""):
                sha.update(chunk)
        check(sha.hexdigest() == hashes[audit.key(row["root"], row["path"])]["sha256"], "Independent file hash sample mismatch")
    seal_claims = audit.load_jsonl(PHASE / "SEAL_CLAIMS.jsonl")
    check(len(seal_claims) == 225390, "Historical hash claim count mismatch")
    reviewed = audit.load_jsonl(PHASE / "REVIEWED_SEAL_EXCEPTIONS.jsonl")
    raw_exceptions = audit.load_jsonl(PHASE / "SEAL_EXCEPTIONS.jsonl")
    check(len(reviewed) == len(raw_exceptions), "Unreviewed hash exception")
    check({(r["manifest"], r["json_location"]) for r in reviewed} == {(r["manifest"], r["json_location"]) for r in raw_exceptions}, "Exception review coverage mismatch")
    gaps = audit.read_json(PHASE / "PRESERVATION_GAPS.json")
    check(gaps["unique_missing_source_digests"] == 5, "Unrecorded historical source gap")
    check(Counter(r["review_category"] for r in reviewed)["unrecovered_historical_mutable_context"] == 1, "Unexpected context gap")
    check(not any(audit.opaque(r["manifest"]) for r in seal_claims), "PGC1 metadata parsed unexpectedly")
    old_root = audit.REPO / "docs/maintenance/2026-11-03"
    science_count = 0
    for scope in ("identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"):
        folder = old_root / scope
        for entry in audit.read_json(folder / "DELIVERY_SEAL.json")["files"]:
            verify_file(folder / entry["path"], entry)
            science_count += 1
    check(science_count == 2047, "November science seal coverage mismatch")
    source_freezes = 0
    for scope in ("stereo-source-01", "stereo-support-01", "stereo-support-01/integration02", "stereo-alias-01", "windows-lease-01"):
        for entry in audit.read_json(old_root / scope / "SOURCE_FREEZE.json")["files"]:
            verify_file(entry["path"], entry)
            source_freezes += 1
    old_phase = old_root / "migration-preflight-01"
    a0_count = 0
    for entry in audit.read_json(old_phase / "DELIVERY_SEAL.json")["files"]:
        verify_file(old_phase / entry["path"], entry)
        a0_count += 1
    link_checks = 0
    for relative in ("AGENTS.md", "docs/migration/README.md", "docs/migration/PLAN.md"):
        document = audit.REPO / relative
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            target = match.group(1).split("#")[0]
            if target and not re.match(r"^[a-z]+://", target):
                check((document.parent / target).exists(), "Missing current document link: " + target)
                link_checks += 1
    check((audit.REPO / "AGENTS.md").stat().st_size <= 16384, "Current context grew beyond compact bound")
    result = {"passed": True, "stage": "A1_WINDOWS_VISIBLE_ASSETS_COMPLETE_WITH_HOLDS",
              "metadata_identities_verified": len(keys), "file_and_link_dispositions_verified": len(ledger),
              "regular_file_sha256_records": len(regular), "reparse_metadata_verified": len(links),
              "independent_sha256_samples_verified": len(sample), "source_snapshot_aliases_verified": len(preserve),
              "source_unique_contents_verified": len(unique), "historical_versions_recovered_verified": len(recovered),
              "old_scientific_files_verified": science_count, "old_source_freeze_entries_verified": source_freezes,
              "A0_immutable_seal_files_verified": a0_count, "historical_claims_indexed": len(seal_claims),
              "hash_exception_reviews_verified": len(reviewed), "current_markdown_links_verified": link_checks,
              "allowed_current_document_changes": sorted(changes), "all_other_original_asset_names_sizes_mtimes_unchanged": True,
              "historical_source_digest_gaps_retained": 5, "historical_context_version_gaps_retained": 1,
              "asset_moves_or_deletions": 0, "PGC1_partial_accuracy_interpreted": False,
              "WSL_started": False, "GPU_or_model_or_training_or_research_run": False,
              "whole_project_external_closure_claimed": False, "server_migration_complete": False}
    audit.write_json("CHECKS.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
