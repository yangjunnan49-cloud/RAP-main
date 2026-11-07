#!/usr/bin/env python3
"""Index code roles statically; never import or execute research scripts."""
import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]
ACTIVE = {("rap-main", "scripts/run.py"): "portable_launcher",
          ("rap-main", "sample.py"): "sample", ("rap-main", "demo.py"): "demo",
          ("rap-main", "dataset_process/extract_sample_features.py"): "features",
          ("rap-slam", "scripts/run_pipeline.py"): "slam",
          ("rap-slam", "scripts/eval_external_trajectory.py"): "evaluate"}
MAINTENANCE = {"scripts/maintenance/query_experiments.py", "scripts/maintenance/index_code_entries.py",
               "scripts/maintenance/render_current_state.py"}


def classify(root, path):
    if (root, path) in ACTIVE:
        return "current_entry", ACTIVE[(root, path)]
    if root == "rap-main" and path in MAINTENANCE:
        return "current_maintenance", None
    if path.startswith(("tests/", "test_")):
        return "verification_tool", None
    if path.startswith("scripts/maintenance/"):
        return "historical_research_tool", None
    if root == "rap-slam" and path == "scripts/eval_paper_metrics.py":
        return "metric_library_and_historical_registry", None
    if root == "rap-slam" and path.startswith("scripts/"):
        return "historical_research_or_operations_tool", None
    if path == "app.py" or "visualize_" in path:
        return "optional_interactive_tool", None
    if path.endswith((".sh", ".ps1")):
        return "legacy_environment_or_operations_recipe_A4", None
    if path.startswith("ros2/"):
        return "optional_ros2_component_A4", None
    if path.startswith("config/") or "requirements" in path:
        return "configuration_or_dependency_input_A4", None
    return "library_or_module_diagnostic", None


def build(slam):
    roots = {"rap-main": REPO, "rap-slam": slam}
    groups = {"rap-main": ("rectified_point_flow", "dataset_process", "config", "scripts", "rap_runtime", "tests"),
              "rap-slam": ("rap_slam", "scripts", "ros2")}
    suffixes = {".py", ".sh", ".ps1", ".yaml", ".yml", ".toml", ".xml", ".cfg", ".txt"}
    rows = []
    for root, folders in groups.items():
        paths = list(roots[root].glob("*"))
        for folder in folders:
            paths.extend((roots[root] / folder).rglob("*"))
        for source in sorted(set(paths)):
            if not source.is_file() or source.suffix.lower() not in suffixes or "__pycache__" in source.parts:
                continue
            path = source.relative_to(roots[root]).as_posix()
            raw = source.read_bytes()
            content = raw.decode("utf-8-sig", errors="replace")
            role, dispatch = classify(root, path)
            doc, imports, main_guard, syntax_error = None, [], False, None
            if source.suffix == ".py":
                try:
                    tree = ast.parse(content)
                    doc = ast.get_docstring(tree)
                    doc = doc.splitlines()[0] if doc else None
                    imports = sorted({n.module or "." for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} |
                                     {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
                    main_guard = any(isinstance(n, ast.If) and "__name__" in ast.dump(n.test) and
                                     "__main__" in ast.dump(n.test) for n in tree.body)
                except SyntaxError as exc:
                    syntax_error = {"line": exc.lineno, "message": exc.msg}
            refs = [{"line": i, "text": line.strip()[:320]} for i, line in enumerate(content.splitlines(), 1)
                    if re.search(r"/mnt/[a-z]/|/root/|[A-Z]:[/\\]|C:/Users/", line)]
            rows.append({"id": root + ":" + path, "root": root, "path": path, "role": role,
                         "dispatch": dispatch, "default_dispatch_allowed": dispatch is not None,
                         "purpose": doc, "has_main_guard": main_guard, "imports_static": imports,
                         "absolute_machine_reference_lines": refs, "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest(), "syntax_error": syntax_error,
                         "execution_or_research_admission": False})
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--slam-root", type=Path, default=Path(os.environ.get("RAP_SLAM_ROOT", str(REPO.parent / "RAP-SLAM"))))
    p.add_argument("--output", type=Path, default=REPO / "docs/code/ENTRYPOINTS.jsonl")
    p.add_argument("--check", action="store_true", help="Compare without rewriting the current index")
    args = p.parse_args()
    rows = build(args.slam_root.resolve())
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    if args.check:
        if args.output.read_text(encoding="utf-8") != content:
            raise SystemExit("Code index differs; review changes before refreshing it")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(json.dumps({"records": len(rows), "roles": dict(Counter(r["role"] for r in rows)),
                      "syntax_errors": sum(r["syntax_error"] is not None for r in rows),
                      "machine_references": sum(bool(r["absolute_machine_reference_lines"]) for r in rows),
                      "default_dispatch_entries": [r["id"] for r in rows if r["default_dispatch_allowed"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
