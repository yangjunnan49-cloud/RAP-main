"""Recheck the 27 current native link buffers without following targets."""
import ast
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path

phase = Path(__file__).resolve().parent
repo = phase.parents[3]
roots = {key: Path(value) for key, value in json.loads((phase / "CURRENT_AUDIT.json").read_text(encoding="utf-8"))["source_roots"].items()}
reader = repo / "docs/maintenance/2026-11-03/migration-audit-01/audit_assets.py"
tree = ast.parse(reader.read_text(encoding="utf-8"))
node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "reparse_data")
namespace = dict(ctypes=ctypes, wintypes=wintypes, Path=Path, base64=base64, hashlib=hashlib)
exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "sealed_A1_link_metadata_reader_only", "exec"), namespace)
original = {(row["root"], row["path"]): row for row in json.loads((repo / "docs/maintenance/2026-11-04/assets-package-01/SOURCE_LINKS_RAW.json").read_text(encoding="utf-8"))}
current = json.loads((phase / "CURRENT_LINKS.json").read_text(encoding="utf-8"))
result = []
for row in current:
    key = row["root"], row["path"]
    observed = namespace["reparse_data"](roots[row["root"]] / row["path"])
    assert key in original and observed["raw_sha256"] == original[key]["raw_sha256"], key
    result.append(dict(root=key[0], path=key[1], A8_raw_sha256=observed["raw_sha256"],
                       A5_raw_sha256=original[key]["raw_sha256"], raw_buffer_matches=True, followed=False))
assert len(result) == len(original) == 27
(phase / "CURRENT_LINK_BYTE_CHECKS.json").write_text(json.dumps(dict(passed=True, links=result, links_followed=False), indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(current_raw_link_buffers_verified=len(result), followed=False)))
