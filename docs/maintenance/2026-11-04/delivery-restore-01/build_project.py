"""Build and independently read back the small through-A6 project delta."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def main():
    spec = importlib.util.spec_from_file_location("a7_delta_builder", REPO / "scripts/migration/content_bundle.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    baseline = tool.read_json(PHASE / "BASELINE.json")
    freeze = tool.read_json(PHASE / "PROJECT_FREEZE.json")
    package = Path(baseline["package"])
    assert not package.exists()
    package.mkdir()
    (package / "tools").mkdir()
    (package / "tools/content_bundle.py").write_bytes((REPO / "scripts/migration/content_bundle.py").read_bytes())
    def progress(value):
        with (PHASE / "DELTA_PROGRESS.jsonl").open("ab") as handle:
            handle.write((json.dumps(value) + "\n").encode("utf-8"))
        print(json.dumps(value), flush=True)
    meta = tool.build(PHASE / "delta-inventory", package / "delta", progress=progress)
    verified = tool.verify(package / "delta", progress=progress)
    assert verified["passed"] and meta["source_files_fresh_byte_verified"] == freeze["delta_files"]
    for source, target in [("PROJECT_FILES.jsonl", "FINAL_FILES.jsonl"), ("PROJECT_DIRECTORIES.jsonl", "FINAL_DIRECTORIES.jsonl"),
                           ("LINK_PLAN.json", "LINK_PLAN.json"), ("PERMISSIONS.json", "PERMISSIONS.json")]:
        (package / target).write_bytes((PHASE / source).read_bytes())
    controls = [{"path": name, "bytes": (package / name).stat().st_size, "sha256": tool.sha(package / name)}
                for name in ("FINAL_FILES.jsonl", "FINAL_DIRECTORIES.jsonl", "LINK_PLAN.json", "PERMISSIONS.json")]
    base = REPO / ".maintenance-archive/migration/A5-20261104"
    project = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "A5 base plus latest-through-A6 delta; final A7 authority/evidence is a separate sealed control overlay",
               "layout": freeze["layout"], "control_files": controls,
               "layers": [{"directory": "../A5-20261104", "package_manifest_sha256": tool.sha(base / "PACKAGE.json"),
                           "extra_delivery_index_sha256": tool.sha(base / "DELIVERY_INDEX.json")},
                          {"directory": "delta", "package_manifest_sha256": tool.sha(package / "delta/PACKAGE.json")}],
               "ordinary_files": freeze["ordinary_files"], "logical_bytes": freeze["logical_bytes"], "delta_files": freeze["delta_files"],
               "source_files_deleted_or_moved": False, "scientific_or_model_execution": False, "server_acceptance_validated": False}
    (package / "PROJECT.json").write_bytes((json.dumps(project, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    result = {"passed": True, "source_delta_files_fresh_byte_checked": meta["source_files_fresh_byte_verified"],
              "delta_logical_bytes": meta["logical_bytes"], "delta_unique_objects": meta["unique_objects"], "delta_unique_payload_bytes": meta["unique_payload_bytes"],
              "delta_volumes": meta["volumes"], "independent_readback": verified,
              "project_manifest_sha256": tool.sha(package / "PROJECT.json"), "final_A7_control_overlay_pending": True}
    (PHASE / "PROJECT_PACKAGE.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
