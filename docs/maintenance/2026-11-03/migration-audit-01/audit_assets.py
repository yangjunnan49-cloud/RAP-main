"""Finite, stdlib-only asset audit. Never execute project or experimental code."""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import csv
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import posixpath
import re
import shutil
import time
from urllib.parse import unquote

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": Path("E:/githouse/RAP-SLAM"),
         "reports": Path("E:/githouse/RAP-SLAM-report"), "datasets": Path("E:/githouse/Datasets"),
         "codex-records": Path("C:/Users/AAA/Documents/Codex"), "workspace-root": Path("E:/githouse")}
PREFIXES = {"rap-main": "repositories/RAP-main", "rap-slam": "repositories/RAP-SLAM",
            "reports": "reports/RAP-SLAM-report", "datasets": "data/Datasets",
            "codex-records": "history/codex-records", "workspace-root": "workspace"}
SOURCE_EXTS = {".py", ".ps1", ".sh", ".yaml", ".yml", ".toml", ".cfg", ".cpp", ".h", ".c", ".hpp"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(name, value):
    (PHASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(name, rows):
    with (PHASE / name).open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_jsonl(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def key(root, path):
    return root + ":" + path.replace("\\", "/")


def norm(path):
    return ntpath.normpath(str(path).replace("/", "\\")).casefold()


def localize(path):
    """Only translate recorded /mnt/<drive> paths. Never mount a Linux filesystem."""
    path = str(path).strip().replace("\\\\", "\\")
    if re.match(r"^/mnt/[a-zA-Z]/", path):
        return path[5].upper() + ":/" + path[7:]
    if re.match(r"^[A-Za-z]:[/\\]", path):
        return path
    return None


def opaque(path):
    return "portable_graph_20261031" in str(path).casefold()


def metadata():
    return load_jsonl(PHASE / "inventory/entries.jsonl")


def file_path(row):
    return ROOTS[row["root"]] / row["path"]


def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def reparse_data(path):
    """Read Windows reparse metadata with OPEN_REPARSE_POINT, without dereferencing."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    create.restype = wintypes.HANDLE
    ioctl = kernel.DeviceIoControl
    ioctl.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                      wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID)
    ioctl.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    filename = str(Path(path).absolute())
    if not filename.startswith("\\\\?\\"):
        filename = "\\\\?\\" + filename
    handle = create(filename, 0, 7, None, 3, 0x02200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        buffer = ctypes.create_string_buffer(16384)
        received = wintypes.DWORD()
        if not ioctl(handle, 0x000900A8, None, 0, buffer, len(buffer), ctypes.byref(received), None):
            raise ctypes.WinError(ctypes.get_last_error())
        raw = buffer.raw[:received.value]
    finally:
        close(handle)
    tag = int.from_bytes(raw[:4], "little")
    target = None
    version = None
    if tag == 0xA000001D:  # IO_REPARSE_TAG_LX_SYMLINK
        version = int.from_bytes(raw[8:12], "little")
        target = raw[12:].decode("utf-8").rstrip("\0")
        kind = "linux_symlink"
    elif tag in (0xA0000003, 0xA000000C):
        offset = int.from_bytes(raw[8:10], "little")
        length = int.from_bytes(raw[10:12], "little")
        start = 16 if tag == 0xA0000003 else 20
        target = raw[start + offset:start + offset + length].decode("utf-16-le").rstrip("\0")
        if target.startswith("\\??\\"):
            target = target[4:]
        kind = "junction" if tag == 0xA0000003 else "windows_symlink"
    else:
        kind = "unknown_reparse_tag"
    return {"tag": hex(tag), "kind": kind, "lx_version": version, "target": target,
            "raw_base64": base64.b64encode(raw).decode("ascii"),
            "raw_sha256": hashlib.sha256(raw).hexdigest(), "metadata_bytes": len(raw)}


def hash_one(row):
    result = {"root": row["root"], "path": row["path"], "bytes": row["bytes"]}
    path = file_path(row)
    try:
        before = path.lstat()
        result.update(mtime_ns=before.st_mtime_ns, file_id=str(before.st_ino), device=str(before.st_dev))
        if row["reparse_point"]:
            result.update(status="reparse_metadata", sha256=None, reparse=reparse_data(path))
        else:
            if before.st_size != row["bytes"]:
                raise RuntimeError("Size differs from metadata inventory")
            result.update(status="sha256", sha256=sha_file(path))
        after = path.lstat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise RuntimeError("File changed during hashing")
    except Exception as exc:
        result.update(status="error", sha256=None, error=f"{type(exc).__name__}: {exc}")
    return result


def hash_all():
    output = PHASE / "HASHES.jsonl"
    if output.exists():
        raise RuntimeError("Hash observation exists; refusing overwrite")
    rows = [r for r in metadata() if r["kind"] == "file" or r["reparse_point"]]
    started = time.monotonic()
    counts = Counter()
    hashed_bytes = 0
    last_print = started
    with output.open("x", encoding="utf-8", newline="\n") as stream, ThreadPoolExecutor(max_workers=4) as pool:
        source = iter(rows)
        pending = set()
        for _ in range(min(64, len(rows))):
            pending.add(pool.submit(hash_one, next(source)))
        while pending:
            finished, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                result = future.result()
                stream.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
                counts[result["status"]] += 1
                if result["status"] == "sha256":
                    hashed_bytes += result["bytes"]
                try:
                    pending.add(pool.submit(hash_one, next(source)))
                except StopIteration:
                    pass
            now = time.monotonic()
            if now - last_print >= 5:
                stream.flush()
                print(json.dumps({"done": sum(counts.values()), "total": len(rows), "sha256_GiB": round(hashed_bytes / 2**30, 3),
                                  "errors": counts["error"], "seconds": round(now - started, 1)}), flush=True)
                last_print = now
    summary = {"finished_utc": utc(), "counts": dict(counts), "hash_bytes": hashed_bytes,
               "wall_seconds": time.monotonic() - started, "workers": 4,
               "source_changed_by_audit": False, "opaque_PGC1_files_semantically_read": False,
               "coherent_filesystem_snapshot_claimed": False}
    write_json("HASH_SUMMARY.json", summary)
    print(json.dumps(summary), flush=True)


def classify(row):
    root, path = row["root"], row["path"]
    low = path.casefold()
    suffix = Path(path).suffix.casefold()
    parts = low.split("/")
    if row["reparse_point"]:
        return "filesystem_link", "filesystem metadata; preserve target and original reparse bytes"
    if ".git" in parts:
        return "git_history", "repository identity, local refs and Git objects"
    if opaque(path):
        return "opaque_stopped_experiment", "PGC1 stopped outputs; hash and preserve bytes only"
    if root == "workspace-root":
        return "workspace_context", "parent workspace authority"
    if "node_modules" in parts or "_vendor" in parts or "official-source" in parts:
        return "third_party_dependency", "dependency or pinned third-party source; no automatic deletion"
    if "__pycache__" in parts or suffix in (".pyc", ".pyo"):
        return "regenerable_python_cache", "Python bytecode; deletion depends on seal and reference review"
    if root == "datasets":
        return "dataset_source", "dataset root; byte preservation does not authenticate provenance or completeness"
    if suffix in (".ckpt", ".pth", ".pt", ".safetensors"):
        return "model_weight", "checkpoint or feature-model weight; preserve source association"
    if root == "reports":
        return "report_artifact", "independent report and manuscript source tree"
    if root == "codex-records":
        return "external_experiment_record", "owner-included external research/work/outputs archive"
    if root == "rap-main":
        if parts[0] == ".maintenance-archive":
            return "preservation_archive", "previous maintenance preservation copy"
        if low.startswith("docs/maintenance/") or low.startswith("docs/meeting_") and "/benchmark/" in low:
            return "experiment_record", "dated protocol, source, receipts, input or output evidence"
        if low.startswith(("docs/meeting_", "working files/")):
            return "meeting_artifact", "meeting delivery, source, review or build material"
        if low.startswith("docs/migration/") or path == "AGENTS.md":
            return "current_maintenance_context", "current migration entry and task conventions"
        if parts[0] == "docs":
            return "project_documentation", "repository documentation outside dated experiment records"
        if parts[0] == "config":
            return "current_configuration", "model/inference Hydra configuration"
        if path == "kiss_slam.yaml":
            return "comparator_configuration", "existing KISS-SLAM odometry/loop/mapper configuration; preserve parameters"
        if path == "build_p3d.sh":
            return "environment_or_entry_script", "inspected historical PyTorch3D build helper; absolute root/CUDA paths require A4 replacement"
        if low.startswith("scripts/maintenance/"):
            return "research_support_code", "research maintenance tool; active/retired role requires A3 review"
        if parts[0] in ("rectified_point_flow", "dataset_process") or path in ("app.py", "demo.py", "sample.py", "test_smoke.py"):
            return "current_code", "current model, preprocessing or documented entry point"
        if parts[0] == "demo_example_data":
            return "example_input", "existing demo source/input"
        if parts[0] == "demo_output":
            return "saved_output", "saved inference evidence; preserve before deciding value"
        if parts[0] == "weights":
            return "model_asset", "model weights and associated payload"
        if parts[0] == "scripts" and suffix in SOURCE_EXTS:
            return "environment_or_entry_script", "installation/download/entry script; require portability review"
    if root == "rap-slam":
        if parts[0] == "rap_slam" or path in ("scripts/run_pipeline.py", "scripts/test_rap_backend.py"):
            return "current_code", "SLAM library or documented pipeline entry"
        if parts[0] == "scripts":
            return "research_or_data_tool", "analysis/data/download script; retain until entrypoint review"
        if parts[0] == "ros2":
            return "optional_ros2_component", "optional live visualization/integration component"
        if parts[0] == "data":
            return "research_input", "SLAM source, derived or calibration input; subtype requires provenance review"
        if parts[0].startswith("output"):
            return "saved_experiment_output", "historical SLAM output or execution log"
    if path in ("README.md", "LICENSE", ".gitignore", "requirements_other.txt", "requirements.txt"):
        return "project_metadata", "repository documentation, license, ignore or dependency definition"
    if suffix in (".deb", ".log") or path == "wget-log" or parts[0] == "nvidia corporation":
        return "installation_or_machine_artifact_review", "possible local installation/download artifact; preserve and inspect references"
    if suffix in (".yaml", ".yml", ".json"):
        return "configuration_or_metadata_review", "configuration/metadata candidate; lifecycle requires review"
    return "unclassified_review", "no reliable automatic ownership rule; retain for manual review"


def load_state():
    rows = metadata()
    hashes = {key(r["root"], r["path"]): r for r in load_jsonl(PHASE / "HASHES.jsonl")}
    by_abs = {norm(file_path(r)): r for r in rows}
    by_hash = defaultdict(list)
    for row in rows:
        h = hashes.get(key(row["root"], row["path"]))
        if h and h.get("sha256"):
            by_hash[h["sha256"]].append(row)
    return rows, hashes, by_abs, by_hash


def audit_links(rows, hashes, by_abs):
    results = []
    for row in rows:
        if not row["reparse_point"]:
            continue
        h = hashes[key(row["root"], row["path"])]
        record = {"root": row["root"], "path": row["path"], "hash_status": h["status"], **h.get("reparse", {})}
        target = record.get("target")
        target_local = localize(target) if target else None
        if target and not target_local and not target.startswith("/"):
            target_local = str(file_path(row).parent / target)
        record["target_local"] = target_local
        match = by_abs.get(norm(target_local)) if target_local else None
        record["target_in_inventory"] = match is not None
        record["target_exists"] = Path(target_local).exists() if target_local else None
        if match:
            source_target = posixpath.join(PREFIXES[row["root"]], row["path"])
            destination_target = posixpath.join(PREFIXES[match["root"]], match["path"])
            record["proposed_relative_target"] = posixpath.relpath(destination_target, posixpath.dirname(source_target))
            record["disposition"] = "preserve original raw metadata; recreate a relative link in migration staging after validation"
        elif record.get("kind") == "junction" and "node_modules" in row["path"]:
            record["disposition"] = "personal runtime dependency; retain manifest, recreate from verified dependency recipe during A6"
        else:
            record["disposition"] = "hold external or unresolved link; preserve raw metadata; no automatic dereference or deletion"
        results.append(record)
    write_json("LINKS_RESOLVED.json", results)
    return results


def manifest_candidates(rows):
    pattern = re.compile(r"seal|manifest|freeze|proof|registry", re.I)
    return [r for r in rows if r["kind"] == "file" and not r["reparse_point"]
            and Path(r["path"]).suffix.lower() == ".json" and pattern.search(Path(r["path"]).name)
            and ".git/" not in r["path"] and "/node_modules/" not in r["path"]
            and "/_vendor/" not in r["path"] and not opaque(r["path"])]


def hash_claims(value, location="$", ancestors=None, path_hint=None):
    ancestors = ancestors or []
    if isinstance(value, dict):
        digest = value.get("sha256")
        if isinstance(digest, str) and re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            path = next((value.get(k) for k in ("path", "archived_path", "file", "source", "source_path", "relative_path")
                         if isinstance(value.get(k), str)), path_hint)
            if path:
                size = next((value[k] for k in ("bytes", "size", "size_bytes") if isinstance(value.get(k), int)), None)
                yield {"json_location": location, "recorded_path": path, "sha256": digest.lower(), "bytes": size,
                       "archived_path": value.get("archived_path"), "source": value.get("source"),
                       "ancestor_roots": [a[k] for a in ancestors + [value] for k in ("root", "base", "archive_root", "source_root", "repo", "repository")
                                          if isinstance(a.get(k), str)]}
        for name, child in value.items():
            name_is_path = isinstance(name, str) and ("/" in name or "\\" in name or Path(name).suffix.lower() in SOURCE_EXTS | {".json", ".jsonl", ".txt", ".npz", ".npy", ".bin", ".png", ".ply", ".md", ".exe", ".csv", ".zip"})
            if name_is_path and isinstance(child, str) and re.fullmatch(r"[a-fA-F0-9]{64}", child):
                yield {"json_location": location + "." + name, "recorded_path": name, "sha256": child.lower(), "bytes": None,
                       "archived_path": None, "source": None, "ancestor_roots": []}
            if isinstance(child, (dict, list)):
                yield from hash_claims(child, location + "." + str(name), ancestors + [value], name if name_is_path else None)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            if isinstance(child, (dict, list)):
                yield from hash_claims(child, f"{location}[{i}]", ancestors)


def claim_paths(manifest_row, claim):
    base = file_path(manifest_row).parent
    path = claim["recorded_path"]
    absolute = localize(path)
    if absolute:
        return [Path(absolute)]
    if path.startswith("/"):
        return []
    paths = [base / path]
    if Path(manifest_row["path"]).name == "bank_seal02.json":
        paths.insert(0, base / "bank02" / path)
    for root in claim["ancestor_roots"]:
        translated = localize(root)
        if translated:
            paths.append(Path(translated) / path)
        elif root in ("RAP-SLAM", "RAP-main"):
            paths.append(Path("E:/githouse") / root / path)
    if path.replace("\\", "/").startswith(("rap_slam/", "scripts/")):
        paths.append(ROOTS["rap-slam"] / path)
    paths.extend([ROOTS[manifest_row["root"]] / path, REPO / path, Path("E:/githouse") / path])
    if claim.get("archived_path"):
        for archive in (REPO / ".maintenance-archive").iterdir():
            if archive.is_dir():
                paths.append(archive / claim["archived_path"])
    unique = {}
    for candidate in paths:
        unique.setdefault(norm(candidate), candidate)
    return list(unique.values())


def audit_seals(rows, hashes, by_abs, by_hash):
    candidates = manifest_candidates(rows)
    documents, claims, protected = [], [], defaultdict(set)
    recovered_path = PHASE / "RECOVERED_SOURCES.json"
    recovered = read_json(recovered_path) if recovered_path.exists() else {"recovered": [], "external_observations": []}
    recovered_map = {r["sha256"]: r for r in recovered["recovered"]}
    external_map = {norm(r["path"]): r for r in recovered["external_observations"]}
    for manifest in candidates:
        mid = key(manifest["root"], manifest["path"])
        try:
            content = read_json(file_path(manifest))
            extracted = list(hash_claims(content))
            documents.append({"manifest": mid, "bytes": manifest["bytes"], "hash_claims": len(extracted),
                              "status": "hash_claims_found" if extracted else "no_supported_file_hash_claims"})
        except Exception as exc:
            documents.append({"manifest": mid, "status": "parse_error", "error": str(exc)})
            continue
        for claim in extracted:
            paths = claim_paths(manifest, claim)
            examined = []
            matched = None
            for candidate in paths:
                row = by_abs.get(norm(candidate))
                if row is None:
                    continue
                h = hashes.get(key(row["root"], row["path"]))
                if h is None:
                    continue
                identity = key(row["root"], row["path"])
                protected[identity].add(mid)
                same = h.get("sha256") == claim["sha256"] and (claim["bytes"] is None or row["bytes"] == claim["bytes"])
                examined.append({"asset": identity, "match": same, "observed_sha256": h.get("sha256"), "bytes": row["bytes"]})
                if same and matched is None:
                    matched = row
            copies = [r for r in by_hash.get(claim["sha256"], []) if claim["bytes"] is None or r["bytes"] == claim["bytes"]]
            if matched:
                status = "match_at_recorded_resolution" if examined[0]["match"] else "match_at_alternate_resolution"
                preserved = matched
            elif copies:
                status = "recorded_path_differs_but_exact_bytes_preserved" if examined else "recorded_path_unresolved_but_exact_bytes_preserved"
                preserved = copies[0]
            elif examined:
                status = "recorded_current_bytes_differ_no_exact_copy_in_scope"
                preserved = None
            else:
                status = "recorded_path_unresolved_no_exact_copy_in_scope"
                preserved = None
            special_preserved = None
            recovered_entry = recovered_map.get(claim["sha256"])
            if preserved is None and recovered_entry and (claim["bytes"] is None or claim["bytes"] == recovered_entry["bytes"]):
                status = "exact_historical_bytes_recovered"
                special_preserved = "recovered-source:" + claim["sha256"]
            external = external_map.get(norm(paths[0])) if paths else None
            if preserved is None and not special_preserved and external:
                status = "referenced_external_runtime_matches" if external.get("sha256") == claim["sha256"] else "historical_external_runtime_changed"
            negative_control = ("/windows-lease-01/source_mismatch/" in mid and claim["sha256"] == "0" * 64)
            if negative_control:
                status = "expected_negative_control_digest_mismatch"
            if preserved:
                protected[key(preserved["root"], preserved["path"])].add(mid)
            claims.append({"manifest": mid, **{k: v for k, v in claim.items() if k != "ancestor_roots"},
                           "status": status, "examined": examined,
                           "exact_copy_count_in_scope": len(copies),
                           "preserved_asset": key(preserved["root"], preserved["path"]) if preserved else special_preserved,
                           "first_resolution": str(paths[0]) if paths else None,
                           "expected_digest_is_historical_not_new_acceptance": True})
    write_jsonl("SEAL_DOCUMENTS.jsonl", documents)
    write_jsonl("SEAL_CLAIMS.jsonl", claims)
    exceptions = [c for c in claims if c["status"] != "match_at_recorded_resolution"]
    write_jsonl("SEAL_EXCEPTIONS.jsonl", exceptions)
    result = {"manifest_documents": len(documents), "document_status": dict(Counter(d["status"] for d in documents)),
              "file_hash_claims": len(claims), "claim_status": dict(Counter(c["status"] for c in claims)),
              "protected_assets_from_claims": len(protected),
              "scope_limit": "Supported path+sha256 records in selected manifest/seal/freeze/proof/registry JSON; arbitrary dynamic validators not executed; PGC1 opaque tree excluded from semantic parsing."}
    write_json("SEAL_SUMMARY.json", result)
    return claims, protected, result


def duplicates(rows, hashes, by_hash):
    groups = []
    for digest, members in by_hash.items():
        if len(members) < 2:
            continue
        size = members[0]["bytes"]
        files = [{"asset": key(r["root"], r["path"]), "category": classify(r)[0],
                  "device": hashes[key(r["root"], r["path"])].get("device"),
                  "file_id": hashes[key(r["root"], r["path"])].get("file_id")} for r in members]
        ids = {(f["device"], f["file_id"]) for f in files}
        groups.append({"sha256": digest, "bytes_each": size, "copies": len(members),
                       "repeated_logical_bytes": size * (len(members) - 1),
                       "distinct_file_ids": len(ids), "members": files,
                       "disposition": "preserve all path identities; future deduplicating archive may restore every name; no deletion authorized by equality alone"})
    groups.sort(key=lambda g: (-g["repeated_logical_bytes"], g["sha256"]))
    write_jsonl("DUPLICATE_GROUPS.jsonl", groups)
    result = {"groups": len(groups), "duplicate_member_files": sum(g["copies"] for g in groups),
              "repeated_logical_bytes": sum(g["repeated_logical_bytes"] for g in groups),
              "physical_reclaimable_bytes": None, "files_removed": 0,
              "zero_byte_files": sum(r["bytes"] == 0 for r in rows if r["kind"] == "file" and not r["reparse_point"])}
    write_json("DUPLICATE_SUMMARY.json", result)
    return groups, result


def git_maps():
    result = {}
    behind_links = []
    for root in ("rap-main", "rap-slam"):
        state = read_json(PHASE / "git" / root / "STATE.json")
        values = {r["path"]: "tracked" for r in state["tracked"]}
        values.update({p: "untracked" for p in state["untracked"]})
        values.update({p: "ignored" for p in state["ignored"]})
        for path in state["dirty"]:
            values[path] = "tracked_dirty"
        result[root] = values
    return result


def ledger(rows, hashes, protected, duplicate_groups):
    flags = git_maps()
    duplicate_ids = {m["asset"]: g["sha256"] for g in duplicate_groups for m in g["members"]}
    categories, actions, git_flags, unknown, cache_candidates = Counter(), Counter(), Counter(), [], []
    file_rows = []
    directory_rows = []
    for row in rows:
        identity = key(row["root"], row["path"])
        category, basis = classify(row)
        h = hashes.get(identity, {})
        seal_ids = sorted(protected.get(identity, set()))
        boundary = (row["root"] == "codex-records" or row["path"].startswith(("docs/maintenance/", ".maintenance-archive/"))
                    or row["path"].startswith("docs/meeting_") and "/benchmark/" in row["path"])
        is_protected = bool(seal_ids) or boundary or opaque(row["path"])
        action = "retain_in_place"
        if row["reparse_point"]:
            action = "preserve_link_metadata_for_staging"
        elif category == "git_history":
            action = "preserve_git_history"
        elif category == "regenerable_python_cache" and not is_protected:
            action = "cache_removal_candidate_after_reference_review"
        elif category in ("unclassified_review", "configuration_or_metadata_review", "installation_or_machine_artifact_review"):
            action = "hold_for_review"
        git_status = "git_metadata" if category == "git_history" else flags.get(row["root"], {}).get(row["path"], "not_in_captured_git_lists")
        if row["root"] not in flags:
            git_status = "independent_file_asset"
        record = {"asset": identity, "root": row["root"], "path": row["path"], "source_path": str(file_path(row)),
                  "kind": row["kind"], "bytes": row["bytes"], "mtime_utc": row["mtime_utc"],
                  "category": category, "ownership_basis": basis, "git_status": git_status,
                  "sha256": h.get("sha256"), "hash_status": h.get("status", "directory"),
                  "reparse_metadata_sha256": h.get("reparse", {}).get("raw_sha256"),
                  "checksum_basis": "raw reparse metadata in LINKS_RESOLVED.json" if row["reparse_point"] else "file bytes" if row["kind"] == "file" else "directory metadata",
                  "protected": is_protected, "seal_claim_count": len(seal_ids), "seal_manifests": seal_ids,
                  "proposed_action": action, "action_executed": False,
                  "proposed_target": posixpath.join(PREFIXES[row["root"]], row["path"]),
                  "target_status": "root-preserving staging proposal; final A2/A3 layout not applied",
                  "rollback_location": str(file_path(row)),
                  "backup_policy": "original retained; content-addressed source snapshot where listed; data copied/verified before later mutation",
                  "duplicate_group_sha256": duplicate_ids.get(identity),
                  "reference_repair": "resolve through ROOT_MAPPING.json and REFERENCES.jsonl before current-path edits",
                  "opaque_experiment": opaque(row["path"])}
        if row["kind"] == "directory" and not row["reparse_point"]:
            directory_rows.append(record)
            continue
        file_rows.append(record)
        categories[category] += 1
        actions[action] += 1
        git_flags[git_status] += 1
        if category == "unclassified_review":
            unknown.append(record)
        if action == "cache_removal_candidate_after_reference_review":
            cache_candidates.append(record)
    write_jsonl("ASSET_LEDGER.jsonl", file_rows)
    write_jsonl("DIRECTORY_LEDGER.jsonl", directory_rows)
    write_jsonl("UNCLASSIFIED_REVIEW.jsonl", unknown)
    write_jsonl("CACHE_CANDIDATES.jsonl", cache_candidates)
    fields = ("asset", "category", "git_status", "bytes", "sha256", "hash_status", "protected", "seal_claim_count",
              "proposed_action", "action_executed", "proposed_target", "rollback_location", "ownership_basis")
    with (PHASE / "DISPOSITION_DRY_RUN.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(file_rows)
    inventory_keys = {key(r["root"], r["path"]) for r in rows}
    git_only = []
    link_prefixes = [(r["root"], r["path"].rstrip("/") + "/") for r in rows if r["reparse_point"]]
    for root, paths in flags.items():
        for path, status in paths.items():
            if key(root, path) in inventory_keys or path.startswith("docs/maintenance/2026-11-03/migration-audit-01/"):
                continue
            link = next((prefix for r, prefix in link_prefixes if r == root and path.startswith(prefix)), None)
            git_only.append({"root": root, "path": path, "git_status": status,
                             "reason": "behind_unfollowed_reparse_directory" if link else "git_path_not_in_nonrecursive_link_inventory",
                             "link_prefix": link})
    write_jsonl("GIT_ONLY_PATHS.jsonl", git_only)
    result = {"file_and_link_ledger_rows": len(file_rows), "directory_ledger_rows": len(directory_rows),
              "categories": dict(categories), "proposed_actions": dict(actions), "git_status": dict(git_flags),
              "protected_file_or_link_rows": sum(r["protected"] for r in file_rows),
              "unclassified_file_rows": len(unknown), "git_only_path_reasons": dict(Counter(r["reason"] for r in git_only)),
              "cache_candidate_count": len(cache_candidates), "cache_candidate_logical_bytes": sum(r["bytes"] for r in cache_candidates),
              "asset_moves": 0, "asset_deletions": 0}
    write_json("CLASSIFICATION_SUMMARY.json", result)
    write_json("ROOT_MAPPING.json", {"proposal_only": True, "mapping": [
        {"id": root, "local": str(base), "wsl_alias": "/mnt/" + str(base)[0].lower() + "/" + str(base)[3:].replace("\\", "/")
         if str(base)[1:3] == ":\\" else None, "staging_prefix": PREFIXES[root]} for root, base in ROOTS.items()]})
    return file_rows, result


def analyze():
    started = time.monotonic()
    rows, hashes, by_abs, by_hash = load_state()
    links = audit_links(rows, hashes, by_abs)
    claims, protected, seal_summary = audit_seals(rows, hashes, by_abs, by_hash)
    groups, duplicate_summary = duplicates(rows, hashes, by_hash)
    records, classification = ledger(rows, hashes, protected, groups)
    write_json("ANALYSIS_SUMMARY.json", {"finished_utc": utc(), "seconds": time.monotonic() - started,
        "link_count": len(links), "links_with_target": sum(bool(r.get("target")) for r in links),
        "seal_summary": seal_summary, "duplicate_summary": duplicate_summary, "classification": classification})
    print(json.dumps({"links": len(links), "seals": seal_summary, "duplicates": duplicate_summary,
                      "classification": classification}, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("hash", "analyze"))
    args = parser.parse_args()
    if args.command == "hash":
        hash_all()
    else:
        analyze()


if __name__ == "__main__":
    main()
