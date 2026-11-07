"""Check the known legacy build logs and bounded source-directory candidates."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a4_readonly_helpers", PHASE / "collect_linux.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "files": [], "log_checks": [], "directory_candidates": [], "commit_candidates": []}
    paths = {Path("/root/pytorch3d_build.log"), Path("/root/pytorch3d_build2.log"), Path("/root/pytorch3d_build3.log")}
    for parent in (Path("/root"), Path("/tmp")):
        if parent.is_dir():
            paths.update(p for p in parent.iterdir() if re.search(r"pytorch3d|muon", p.name, re.I))
    for source in sorted(paths):
        if source.is_file() and source.suffix == ".log":
            row = {"path": str(source), "bytes": source.stat().st_size}
            if source.stat().st_size <= 64 * 1024 * 1024:
                record = helper.preserve(source, "build-evidence")
                result["files"].append(record)
                text = (PHASE / record["copy"]).read_text(encoding="utf-8", errors="replace")
                row["commit_candidates"] = sorted(set(re.findall(r"(?i)(?:resolved.{0,100}commit|commit[ :]+|checkout[ :]+|HEAD is now at)[^\n]{0,60}?\b([a-f0-9]{7,40})\b", text)))
                row["cuda_arch_flags"] = sorted(set(re.findall(r"(?:compute|sm)_[0-9]+", text)))
                row["torch_cuda_mentions"] = sorted(set(re.findall(r"(?:torch-|cuda[- /])\d+(?:\.\d+){0,2}", text, re.I)))
                result["commit_candidates"] += row["commit_candidates"]
            else:
                row["not_copied"] = "exceeds bounded build log limit"
            result["log_checks"].append(row)
        elif source.is_dir():
            row = {"path": str(source), "resolved": str(source.resolve()), "git": [], "source_files_preserved": 0}
            if (source / ".git").exists():
                for args in (["rev-parse", "HEAD"], ["status", "--porcelain=v1", "--untracked-files=all"], ["diff", "--no-ext-diff", "--binary", "HEAD"]):
                    row["git"].append(helper.command(["git", "--no-optional-locks", "-C", str(source), *args]))
                total = 0
                for file in sorted(source.rglob("*")):
                    if not file.is_file() or file.is_symlink() or any(p in {".git", "build", "__pycache__", "dist"} for p in file.relative_to(source).parts):
                        continue
                    if file.suffix not in {".py", ".cu", ".cuh", ".h", ".hpp", ".cpp", ".toml", ".txt", ".md", ".cfg"}:
                        continue
                    if file.stat().st_size > 4 * 1024 * 1024 or total + file.stat().st_size > 64 * 1024 * 1024:
                        continue
                    result["files"].append(helper.preserve(file, "build-evidence"))
                    total += file.stat().st_size
                    row["source_files_preserved"] += 1
            result["directory_candidates"].append(row)
        else:
            result["log_checks"].append({"path": str(source), "state": "NOT_PRESENT"})
    result["commit_candidates"] = sorted(set(result["commit_candidates"]))
    (PHASE / "BUILD_EVIDENCE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"log_checks": result["log_checks"], "directory_candidates": result["directory_candidates"], "preserved_files": len(result["files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
