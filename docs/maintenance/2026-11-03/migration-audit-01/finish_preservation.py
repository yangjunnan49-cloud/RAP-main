"""Preserve current source bytes and recover exact historical context slices."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import time

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    started = time.monotonic()
    rows, hashes, by_abs, by_hash = audit.load_state()
    state = audit.read_json(PHASE / "RECOVERED_SOURCES.json")
    shutil.copyfile(PHASE / "RECOVERED_SOURCES.json", PHASE / "recovered-sources/BEFORE_CONTEXT_SLICE_RECOVERY.json")
    missing = [r for r in audit.load_jsonl(PHASE / "SEAL_EXCEPTIONS.jsonl")
               if "no_exact_copy" in r["status"] and Path(r["recorded_path"].replace("\\", "/")).name in {"AGENTS.md", "PHASE_RECORD.md"}]
    wanted = {r["sha256"] for r in missing}
    origins = defaultdict(list)
    for row in missing:
        origins[row["sha256"]].append({"manifest": row["manifest"], "recorded_path": row["recorded_path"]})
    seen, matches = set(), []
    for row in sorted(rows, key=lambda r: -r["bytes"]):
        basename = Path(row["path"]).name.casefold()
        if row["kind"] != "file" or row["reparse_point"] or audit.opaque(row["path"]):
            continue
        if not ("agents" in basename or "phase_record" in basename) or not row["path"].lower().endswith(".md"):
            continue
        h = hashes[audit.key(row["root"], row["path"])]
        if h.get("sha256") in seen:
            continue
        seen.add(h.get("sha256"))
        data = audit.file_path(row).read_bytes()
        boundaries = {0, len(data)}
        for match in re.finditer(rb"(?m)^(?:#{1,6} |---\r?$)", data):
            for adjustment in (-4, -3, -2, -1, 0):
                offset = match.start() + adjustment
                if offset >= 0 and (adjustment == 0 or data[offset:match.start()].strip(b"\r\n") == b""):
                    boundaries.add(offset)
        for boundary in sorted(boundaries):
            for start, end in ((0, boundary), (boundary, len(data))):
                if end <= start:
                    continue
                content = data[start:end]
                sha = hashlib.sha256(content).hexdigest()
                if sha not in wanted:
                    continue
                target = PHASE / "recovered-sources" / (sha + ".source")
                target.write_bytes(content)
                record = {"sha256": sha, "bytes": len(content), "backup": target.relative_to(PHASE).as_posix(),
                          "slice_source_asset": audit.key(row["root"], row["path"]), "slice_source_sha256": h["sha256"],
                          "slice_start": start, "slice_end": end, "claims": origins[sha],
                          "exact_bytes_sliced_without_rewriting": True, "source_or_repository_rewritten": False}
                state["recovered"].append(record)
                matches.append(record)
                wanted.remove(sha)
        if not wanted:
            break
    state["context_slice_search"] = {"unique_context_files_checked": len(seen), "exact_slices_recovered": len(matches),
                                     "remaining_context_sha256": sorted(wanted)}
    state["unrecovered_sha256"] = sorted(set(state["unrecovered_sha256"]) - {r["sha256"] for r in state["recovered"]})
    audit.write_json("RECOVERED_SOURCES.json", state)

    store = PHASE / "source-store"
    store.mkdir(exist_ok=False)
    sources = []
    unique_sources = {}
    for row in rows:
        if row["kind"] != "file" or row["reparse_point"] or audit.opaque(row["path"]):
            continue
        category = audit.classify(row)[0]
        if category in {"git_history", "third_party_dependency", "regenerable_python_cache"}:
            continue
        if Path(row["path"]).suffix.lower() not in audit.SOURCE_EXTS and Path(row["path"]).name not in {"AGENTS.md", ".gitignore", "requirements.txt", "requirements_other.txt", "LICENSE"}:
            continue
        h = hashes[audit.key(row["root"], row["path"])]
        if h["status"] != "sha256":
            raise RuntimeError("Source hash unavailable")
        sha = h["sha256"]
        source = audit.file_path(row)
        current = source.stat()
        if (current.st_size, current.st_mtime_ns) != (row["bytes"], h["mtime_ns"]):
            raise RuntimeError(f"Source changed before preservation: {source}")
        target = store / sha[:2] / sha
        if sha not in unique_sources:
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
            if audit.sha_file(target) != sha:
                raise RuntimeError("Source-store copy mismatch")
            unique_sources[sha] = row["bytes"]
        sources.append({"asset": audit.key(row["root"], row["path"]), "sha256": sha, "bytes": row["bytes"],
                        "backup": target.relative_to(PHASE).as_posix(), "source_not_changed": True})
    audit.write_jsonl("SOURCE_PRESERVATION.jsonl", sources)
    git_temp = [r for r in rows if r["kind"] == "file" and r["path"].startswith(".git/")
                and (Path(r["path"]).name.startswith(("tmp_", "tmp_pack_")) or r["path"].endswith(".lock"))]
    audit.write_jsonl("GIT_TEMP_REVIEW.jsonl", [{"asset": audit.key(r["root"], r["path"]), "bytes": r["bytes"],
                      "sha256": hashes[audit.key(r["root"], r["path"])]["sha256"],
                      "disposition": "included in verified raw Git backup; no deletion during A1"} for r in git_temp])
    healthy = []
    for root in ("rap-main", "rap-slam"):
        lines = (PHASE / "git" / root / "fsck.stdout.txt").read_text(encoding="utf-8-sig").splitlines()
        healthy.append({"root": root, "observed_fsck_exit": 0, "command": "git --no-optional-locks fsck --full",
                        "dangling_lines": sum(line.startswith("dangling ") for line in lines),
                        "error_lines": sum(line.startswith(("error:", "fatal:")) for line in lines),
                        "source_mutation": False})
    audit.write_json("GIT_HEALTH.json", healthy)
    result = {"finished_utc": audit.utc(), "seconds": time.monotonic() - started,
              "source_asset_paths_preserved": len(sources), "source_unique_content_files": len(unique_sources),
              "source_store_bytes": sum(unique_sources.values()), "context_slices_recovered": len(matches),
              "all_recovered_sources": len(state["recovered"]), "git_temporary_candidate_files": len(git_temp),
              "git_temporary_candidate_bytes": sum(r["bytes"] for r in git_temp),
              "original_asset_moves": 0, "original_asset_deletions": 0}
    audit.write_json("PRESERVATION_SUMMARY.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
