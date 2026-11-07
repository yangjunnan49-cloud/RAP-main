"""Check source equivalence outside the explicitly allowed A3 path changes."""
import argparse
import ast
import copy
import json
from pathlib import Path
import sys

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
SLAM = REPO.parent / "RAP-SLAM"


def tree(text):
    return ast.dump(ast.parse(text), include_attributes=False)


def text(root, path, before=False):
    base = PHASE / "before" / root if before else REPO if root == "rap-main" else SLAM
    return (base / path).read_text(encoding="utf-8")


def function(source, name):
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def dump(node):
    return ast.dump(node, include_attributes=False)


def main():
    results = {}
    old = text("rap-main", "sample.py", True)
    new = text("rap-main", "sample.py").replace('config_name="RAP_inference"', 'config_name="RAP_base"')
    assert tree(old) == tree(new)
    results["sample_only_default_config_name_corrected"] = True
    old = text("rap-main", "demo.py", True)
    new = text("rap-main", "demo.py").replace("import json\n", "")
    for value in ("data_root", "log_dir", "dataset_name", "args.flow_model_checkpoint"):
        new = new.replace("json.dumps(str(" + value + "), ensure_ascii=False)", value)
    assert tree(old) == tree(new)
    results["demo_only_four_hydra_string_values_quoted"] = True
    old = text("rap-slam", "rap_slam/rap_backend.py", True)
    new = text("rap-slam", "rap_slam/rap_backend.py")
    new = new.replace("from .runtime_paths import backend_paths\n", "")
    new = new.replace("rap_root: Optional[str] = None,", 'rap_root: str = "/mnt/e/githouse/RAP-main",')
    new = new.replace("        rap_root, ckpt_path, spinnet_ckpt = backend_paths(\n            rap_root, ckpt_path, spinnet_ckpt, feature_extraction_on)\n", "")
    assert tree(old) == tree(new)
    results["backend_all_numeric_methods_rng_precision_and_normalization_ast_unchanged"] = True

    old = text("rap-slam", "scripts/run_pipeline.py", True)
    new = text("rap-slam", "scripts/run_pipeline.py")
    before_sequence, after_sequence = function(old, "get_sequence"), function(new, "get_sequence")
    after_sequence.body = [n for n in after_sequence.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    assert dump(before_sequence) == dump(after_sequence)
    before_main, after_main = function(old, "main"), function(new, "main")
    # Remove the path preflight and moved imports before the original first I/O.
    pos = next(i for i, n in enumerate(after_main.body) if isinstance(n, ast.Expr) and
               isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "makedirs")
    after_main.body = [after_main.body[0]] + after_main.body[pos:]
    for node in ast.walk(after_main):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "RAPBackend":
            node.keywords = [k for k in node.keywords if k.arg not in {"ckpt_path", "spinnet_ckpt"}]
    assert dump(before_main) == dump(after_main)
    results["pipeline_data_frame_calibration_and_compute_body_ast_unchanged"] = True
    # Execute only the original isolated argument function, not historical imports.
    original_parse = function(old, "parse_args")
    module = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(original_parse)], type_ignores=[]))
    namespace = {"argparse": argparse}
    exec(compile(module, "original_argument_function_only", "exec"), namespace)
    sys.path.insert(0, str(SLAM))
    from rap_slam.cli import parse_args
    from rap_slam.runtime_paths import backend_paths, validate_pipeline_paths
    cases = [[], ["--no-apply-kitti-205"], ["--real-apply-calib", "--deskew"],
             ["--source", "real", "--real-start", "0", "--real-end", "1", "--real-stride", "2"],
             ["--source", "spires", "--spires-start", "2"], ["--seed", "17", "--rap-steps", "10"],
             ["--no-rap-features", "--skip-loop-closure"], ["--gate-mode", "conformal", "--multigen-k", "3"]]
    path_keys = {"map", "rap_root", "output", "real_root", "spires_root"}
    for args in cases:
        saved = sys.argv
        sys.argv = ["original", *args]
        try:
            before = vars(namespace["parse_args"]())
        finally:
            sys.argv = saved
        after = vars(parse_args(args))
        assert {k: v for k, v in before.items() if k not in path_keys} == {
            k: v for k, v in after.items() if k not in path_keys | {"rap_ckpt", "spinnet_ckpt"}}
    results["argument_cases_compared"] = len(cases)
    results["original_non_path_arguments_per_case"] = len(before) - len(path_keys)
    # Actual current paths: checks only; no files read as arrays or checkpoints.
    current = parse_args(["--skip-loop-closure"])
    assert validate_pipeline_paths(current) == []
    resolved = backend_paths()
    assert Path(resolved[1]).name == "rap_model_12.ckpt"
    results["actual_default_map_and_backend_files_preflight"] = True
    for name in ("numpy", "torch", "hydra", "lightning", "open3d"):
        assert name not in sys.modules, name
    results["numerical_dependencies_imported"] = False
    results["numerical_execution_performed"] = False
    results["passed"] = True
    (PHASE / "BEHAVIOR_CHECKS.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results))


if __name__ == "__main__":
    main()
