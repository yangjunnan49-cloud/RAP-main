"""Finish mode metadata using byte-identical preserved Git indexes, without Git writes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A1 = REPO / "docs/maintenance/2026-11-03/migration-audit-01"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def main():
    assert not (PHASE / "PROJECT_FREEZE.json").exists()
    baseline = load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["source_roots"].items()}
    tracked, observations = {}, []
    for root in ("rap-main", "rap-slam"):
        index = roots[root] / ".git/index"
        old = A1 / "git" / root
        assert sha(index) == sha(old / "index.snapshot") == load(old / "STATE.json")["index_sha256"], root
        content = (old / "tracked.stdout").read_bytes().rstrip(b"\r\n")
        for record in content.split(b"\0"):
            if not record.strip():
                continue
            header, path = record.split(b"\t", 1)
            mode, obj, stage = header.decode("ascii").split()
            assert stage == "0" and mode in {"100644", "100755", "120000", "160000"}
            tracked[root + ":" + path.decode("utf-8")] = mode
        observations.append({"root": root, "current_index_sha256": sha(index), "A1_index_byte_identical": True,
                             "preserved_ls_files_stage_output_sha256": sha(old / "tracked.stdout"), "Git_index_or_config_modified": False})
    save(PHASE / "PERMISSIONS.json", {"git_tracked_modes": tracked, "mode_counts": dict(Counter(tracked.values())),
         "git_index_read_only_observations": observations, "untracked_file_policy": "0644; no execution inferred from extension",
         "directory_policy": "0755 on POSIX; not an NTFS ACL reconstruction", "original_Linux_mode_or_owner_for_all_untracked_files_known": False,
         "POSIX_target_application_still_requires_target_validation": True})
    files = rows(PHASE / "PROJECT_FILES.jsonl")
    dirs = rows(PHASE / "PROJECT_DIRECTORIES.jsonl")
    links = rows(PHASE / "PROJECT_LINKS.jsonl")
    delta = rows(PHASE / "delta-inventory/SOURCE_FILES.jsonl")
    layout = {"rap-main": "RAP-main", "rap-slam": "RAP-SLAM", "reports": "RAP-SLAM-report", "datasets": "Datasets", "codex-records": "archives/Codex", "workspace-root": ""}
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "ordinary_files": len(files), "logical_bytes": sum(r["bytes"] for r in files),
              "directories": len(dirs), "links": len(links), "delta_files": len(delta), "delta_logical_bytes": sum(r["bytes"] for r in delta),
              "delta_kinds": dict(Counter(r["delta_kind"] for r in delta)), "checksum_basis_counts": dict(Counter(r["checksum_basis"] for r in files)),
              "all_A5_identities_retained": True, "A7_current_and_evidence_overlay_pending": True,
              "source_exclusions": [str(PHASE), str(REPO / ".maintenance-archive/migration")], "layout": layout,
              "WSL_images_unexported_Linux_environment_or_wheel_in_project_layers": False, "model_or_scientific_array_loading": False,
              "git_mode_collection_completed_by_exact_preserved_index_binding": True}
    save(PHASE / "PROJECT_FREEZE.json", result)
    print(json.dumps({**result, "git_mode_counts": dict(Counter(tracked.values()))}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
