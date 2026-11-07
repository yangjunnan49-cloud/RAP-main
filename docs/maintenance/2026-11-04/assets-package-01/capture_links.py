"""Recheck original reparse buffers without following their targets."""
import ast
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A1 = REPO / "docs/maintenance/2026-11-03/migration-audit-01"


def main():
    baseline = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    roots = {key: Path(value) for key, value in baseline["source_roots"].items()}
    source = (A1 / "audit_assets.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "reparse_data")
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    namespace = {"ctypes": ctypes, "wintypes": wintypes, "Path": Path, "base64": base64, "hashlib": hashlib}
    # Execute only the previously sealed native metadata reader, never the audit driver.
    exec(compile(module, "A1_reparse_metadata_reader_only", "exec"), namespace)
    old = {(r["root"], r["path"]): r for r in json.loads((A1 / "LINKS_RESOLVED.json").read_text(encoding="utf-8"))}
    current = [json.loads(line) for line in (PHASE / "SOURCE_LINKS.jsonl").read_text(encoding="utf-8").splitlines()]
    result = []
    for row in current:
        key = (row["root"], row["path"])
        observed = namespace["reparse_data"](roots[row["root"]] / row["path"])
        assert key in old and observed["raw_sha256"] == old[key]["raw_sha256"], key
        result.append({**old[key], "A5_raw_buffer_rechecked": True, "A5_raw_sha256": observed["raw_sha256"], "followed": False})
    assert len(result) == len(old) == 27
    (PHASE / "SOURCE_LINKS_RAW.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw_reparse_buffers_verified": len(result), "links_followed": False}))


if __name__ == "__main__":
    main()
