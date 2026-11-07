"""Read local Git state and preserve diffs, indexes and source files. No network."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

PHASE = Path(__file__).resolve().parent
REPOS = {"rap-main": Path("E:/githouse/RAP-main"), "rap-slam": Path("E:/githouse/RAP-SLAM")}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    destination = PHASE / "git"
    destination.mkdir(exist_ok=False)
    summary = {"captured_utc": datetime.now(timezone.utc).isoformat(), "network_queried": False, "repositories": []}
    for name, root in REPOS.items():
        folder = destination / name
        folder.mkdir()
        commands = []

        def run(label, args, required=True, timeout=90):
            env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
            command = ["git", "--no-optional-locks", "--no-pager", "-c", "core.quotePath=false", "-C", str(root), *args]
            result = subprocess.run(command, capture_output=True, env=env, timeout=timeout)
            (folder / (label + ".stdout")).write_bytes(result.stdout)
            (folder / (label + ".stderr")).write_bytes(result.stderr)
            commands.append({"label": label, "args": args, "exit_code": result.returncode})
            if required and result.returncode:
                raise RuntimeError(f"{name}: {label} failed ({result.returncode}); receipts retained")
            return result.stdout

        head = run("head", ["rev-parse", "HEAD"]).decode().strip()
        branch = run("branch", ["symbolic-ref", "--short", "HEAD"], required=False).decode().strip()
        run("worktrees", ["worktree", "list", "--porcelain"])
        run("refs", ["for-each-ref", "--format=%(objectname) %(refname)"])
        run("reflog-identities", ["reflog", "show", "--all", "--format=%H %gD"], required=False)
        run("object-count", ["count-objects", "-v"])
        status = run("status", ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
        tracked_raw = run("tracked", ["ls-files", "--stage", "-z"])
        untracked_raw = run("untracked", ["ls-files", "--others", "--exclude-standard", "-z"])
        ignored_raw = run("ignored", ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"])
        run("unstaged.patch", ["diff", "--binary", "--no-ext-diff", "--no-textconv"])
        run("staged.patch", ["diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv"])
        dirty_raw = run("dirty-names", ["diff", "HEAD", "--name-only", "-z", "--no-ext-diff", "--no-textconv"])
        run("lfs-local", ["lfs", "ls-files", "--long"], required=False)
        tracked = []
        for record in tracked_raw.split(b"\0"):
            if not record:
                continue
            prefix, path = record.split(b"\t", 1)
            mode, oid, stage = prefix.decode().split()
            tracked.append({"path": path.decode("utf-8", "surrogateescape"), "mode": mode, "object": oid, "stage": int(stage)})
        split_paths = lambda raw: [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]
        dirty = split_paths(dirty_raw)
        snapshots = []
        sources = {row["path"] for row in tracked if row["mode"] != "160000"}
        sources.update(dirty)
        for relative in sorted(sources):
            source = root / relative
            if not source.is_file() or source.is_symlink():
                continue
            # Preserve all versioned source/text inputs; large data belongs to the full asset ledger.
            if source.stat().st_size > 8 * 1024 * 1024:
                continue
            target = folder / "working-sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            sha = digest(target)
            if sha != digest(source):
                raise RuntimeError(f"Source changed during snapshot: {source}")
            snapshots.append({"path": relative, "backup": target.relative_to(PHASE).as_posix(), "bytes": target.stat().st_size, "sha256": sha})
        git_index_raw = run("index-path", ["rev-parse", "--git-path", "index"]).decode().strip()
        index = Path(git_index_raw)
        if not index.is_absolute():
            index = root / index
        shutil.copyfile(index, folder / "index.snapshot")
        for filename in (".gitmodules", ".gitattributes"):
            path = root / filename
            if path.is_file():
                shutil.copyfile(path, folder / filename.lstrip("."))
        record = {"root": str(root), "head": head, "branch": branch,
                  "tracked": tracked, "untracked": split_paths(untracked_raw), "ignored": split_paths(ignored_raw),
                  "dirty": dirty, "source_snapshots": snapshots,
                  "gitlinks": [r for r in tracked if r["mode"] == "160000"], "commands": commands,
                  "index_sha256": digest(folder / "index.snapshot"),
                  "reflog_objects_copied": False, "bundle_created": False,
                  "preservation_note": "Local refs/reflog identities, binary diffs, index and versioned small-file bytes copied; Git objects remain original and are included in full hashing. No history deletion is proposed."}
        (folder / "STATE.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["repositories"].append({"id": name, "head": head, "branch": branch, "tracked": len(tracked),
                                         "untracked": len(record["untracked"]), "ignored": len(record["ignored"]),
                                         "dirty": len(dirty), "source_snapshots": len(snapshots), "gitlinks": len(record["gitlinks"])})
        print(json.dumps(summary["repositories"][-1], ensure_ascii=False), flush=True)
    (destination / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
