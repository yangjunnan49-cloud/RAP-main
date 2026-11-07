"""Find exact historical source SHA256 in local Git blobs. Never evaluate blob contents."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import shutil

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    destination = PHASE / "recovered-sources"
    destination.mkdir(exist_ok=True)
    previous_file = PHASE / "RECOVERED_SOURCES.json"
    previous = audit.read_json(previous_file) if previous_file.exists() else {}
    if previous:
        shutil.copyfile(previous_file, destination / "BEFORE_ADDITIONAL_GIT_SEARCH.json")
    claims = [r for r in audit.load_jsonl(PHASE / "SEAL_EXCEPTIONS.jsonl") if "no_exact_copy" in r["status"] and r["sha256"] != "0" * 64]
    wanted = defaultdict(list)
    external = []
    for claim in claims:
        wanted[claim["sha256"]].append({"manifest": claim["manifest"], "recorded_path": claim["recorded_path"]})
        local = audit.localize(claim["recorded_path"])
        if local and Path(local).is_file() and not any(audit.norm(local).startswith(audit.norm(base) + "\\") for base in audit.ROOTS.values()):
            observed = audit.sha_file(local)
            external.append({"path": local, "bytes": Path(local).stat().st_size, "sha256": observed,
                             "historical_expected_sha256": claim["sha256"], "matches": observed == claim["sha256"],
                             "purpose": "referenced external runtime; byte inspection only"})
    recovered = {r["sha256"]: r for r in previous.get("recovered", [])}
    receipts = []
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    for root_name in ("rap-main", "rap-slam"):
        started = time.monotonic()
        prefix = ["git", "--no-optional-locks", "--no-pager", "-C", str(audit.ROOTS[root_name])]
        result = subprocess.run(prefix + ["cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
                                capture_output=True, env=env, timeout=90, check=True)
        (destination / (root_name + ".object-list.stdout")).write_bytes(result.stdout)
        (destination / (root_name + ".object-list.stderr")).write_bytes(result.stderr)
        objects = [line.split() for line in result.stdout.decode().splitlines()]
        objects = [(oid, int(size)) for oid, kind, size in objects if kind == "blob" and int(size) <= 2 * 1024 * 1024]
        total_bytes = 0
        with (destination / (root_name + ".cat-file.stderr")).open("wb") as errors:
            process = subprocess.Popen(prefix + ["cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=errors, env=env)
            try:
                for oid, expected_size in objects:
                    process.stdin.write((oid + "\n").encode())
                    process.stdin.flush()
                    header = process.stdout.readline().decode().strip().split()
                    if len(header) != 3 or header[1] != "blob" or int(header[2]) != expected_size:
                        raise RuntimeError("Unexpected Git blob response header")
                    remaining, pieces = expected_size, []
                    while remaining:
                        block = process.stdout.read(min(remaining, 1024 * 1024))
                        if not block:
                            raise RuntimeError("Unexpected end of Git blob")
                        pieces.append(block)
                        remaining -= len(block)
                    if process.stdout.read(1) != b"\n":
                        raise RuntimeError("Unexpected Git batch framing")
                    content = b"".join(pieces)
                    sha = hashlib.sha256(content).hexdigest()
                    total_bytes += len(content)
                    if sha in wanted and sha not in recovered:
                        target = destination / (sha + ".source")
                        target.write_bytes(content)
                        recovered[sha] = {"sha256": sha, "bytes": len(content), "backup": target.relative_to(PHASE).as_posix(),
                                          "git_repository": root_name, "git_blob": oid, "claims": wanted[sha],
                                          "source_or_repository_rewritten": False, "blob_semantically_evaluated": False}
                process.stdin.close()
                code = process.wait(timeout=30)
                if code:
                    raise RuntimeError(f"Git cat-file exit {code}")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
        receipt = {"root": root_name, "blob_size_limit": 2 * 1024 * 1024, "blobs_byte_hashed": len(objects),
                   "blob_bytes_hashed": total_bytes, "seconds": time.monotonic() - started,
                   "search_includes_dangling_objects": True, "git_mutated": False, "child_reaped": True}
        receipts.append(receipt)
        print(json.dumps(receipt), flush=True)
    external_by_path = {r["path"]: r for r in previous.get("external_observations", []) + external}
    summary = {**previous, "finished_utc": audit.utc(), "recovered": list(recovered.values()), "external_observations": list(external_by_path.values()),
               "unrecovered_sha256": sorted(set(wanted) - set(recovered)), "git_reads": previous.get("git_reads", []) + receipts,
               "note": "Exact original bytes recovered into this audit only. No historical source, manifest, experiment result or current code rewritten."}
    audit.write_json("RECOVERED_SOURCES.json", summary)
    print(json.dumps({"recovered_unique_sources": len(recovered), "remaining_unique_digests": len(summary["unrecovered_sha256"]),
                      "external_runtime_observations": len(external)}), flush=True)


if __name__ == "__main__":
    main()
