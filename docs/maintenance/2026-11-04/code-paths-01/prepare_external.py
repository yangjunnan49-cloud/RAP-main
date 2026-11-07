"""Stage narrowly scoped SLAM changes from the exact A3 before copies."""
import ast
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def main():
    before = PHASE / "before/rap-slam"
    staged = PHASE / "updates/rap-slam"
    original = (before / "scripts/run_pipeline.py").read_text(encoding="utf-8")
    tree = ast.parse(original)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parse_args")
    lines = original.splitlines(keepends=True)
    parse_source = "".join(lines[node.lineno - 1:node.end_lineno])
    cli = replace_once(parse_source, "def parse_args():", "def parse_args(argv=None):")
    cli = replace_once(cli, 'p = argparse.ArgumentParser(description="RAP-SLAM offline SLAM pipeline")',
                       'p = argparse.ArgumentParser(description="RAP-SLAM offline SLAM pipeline")\n    paths = default_paths()')
    for old, key in (("/mnt/e/githouse/RAP-main/demo_example_data/map_kitti/kitti00.ply", "map"),
                     ("/mnt/e/githouse/RAP-main", "rap_root"), ("/mnt/e/githouse/RAP-SLAM/output", "output"),
                     ("/mnt/e/githouse/RAP-SLAM/data/poss", "real_root"), ("/mnt/e/githouse/Datasets/oxford_spires", "spires_root")):
        cli = replace_once(cli, 'default="' + old + '"', 'default=paths["' + key + '"]')
    cli = replace_once(cli, "    return p.parse_args()", '    p.add_argument("--rap-ckpt", default=None, help="RAP checkpoint (default: weights root/rap_model_12.ckpt)")\n    p.add_argument("--spinnet-ckpt", default=None, help="miniSpinNet checkpoint (default: weights root/mini_spinnet_t.pth)")\n    return p.parse_args(argv)')
    (staged / "rap_slam/cli.py").write_text('"""Offline pipeline arguments; numerical defaults are preserved from A3 before."""\nimport argparse\nfrom .runtime_paths import default_paths\n\n\n' + cli + "\n", encoding="utf-8")
    pipeline = original.replace(parse_source, "")
    pipeline = replace_once(pipeline, "Run inside WSL:\n  python scripts/run_pipeline.py --output /mnt/e/githouse/RAP-SLAM/output",
                            "Portable launcher: RAP-main/scripts/run.py slam (plan/check by default).\nDirect entry: python /path/to/RAP-SLAM/scripts/run_pipeline.py --output /new/output")
    pipeline = replace_once(pipeline, "import numpy as np\n\n", "")
    imports = 'from rap_slam import (evaluate, keyframes as kf_mod, loop_closure, odometry,\n                      pose_graph, real_dataset, scan_context as sc_mod,\n                      sequence, spires_dataset)'
    pipeline = replace_once(pipeline, imports, "from rap_slam.cli import parse_args\nfrom rap_slam.runtime_paths import validate_pipeline_paths")
    pipeline = replace_once(pipeline, '    """Load cached sequence, generate a simulated one, or load a real segment."""',
                            '    """Load cached sequence, generate a simulated one, or load a real segment."""\n    import numpy as np\n    from rap_slam import real_dataset, sequence, spires_dataset')
    pipeline = replace_once(pipeline, '    args = parse_args()\n    os.makedirs',
                            '    args = parse_args()\n    errors = validate_pipeline_paths(args)\n    if errors:\n        raise SystemExit("Path preflight failed:\\n" + "\\n".join(errors))\n    import numpy as np\n    from rap_slam import (evaluate, keyframes as kf_mod, loop_closure, odometry,\n                          pose_graph, scan_context as sc_mod, sequence)\n\n    os.makedirs')
    pipeline = replace_once(pipeline, 'rap = RAPBackend(rap_root=args.rap_root,',
                            'rap = RAPBackend(rap_root=args.rap_root,\n                             ckpt_path=args.rap_ckpt,\n                             spinnet_ckpt=args.spinnet_ckpt,')
    (staged / "scripts").mkdir(exist_ok=True)
    (staged / "scripts/run_pipeline.py").write_text(pipeline, encoding="utf-8")
    backend = (before / "rap_slam/rap_backend.py").read_text(encoding="utf-8")
    backend = replace_once(backend, "from .rap_precision import precise_registration", "from .rap_precision import precise_registration\nfrom .runtime_paths import backend_paths")
    backend = replace_once(backend, 'rap_root: str = "/mnt/e/githouse/RAP-main",', 'rap_root: Optional[str] = None,')
    backend = replace_once(backend, '        _setup_rap_imports(rap_root)', '        rap_root, ckpt_path, spinnet_ckpt = backend_paths(\n            rap_root, ckpt_path, spinnet_ckpt, feature_extraction_on)\n        _setup_rap_imports(rap_root)')
    (staged / "rap_slam/rap_backend.py").write_text(backend, encoding="utf-8")
    print("Staged cli.py, runtime_paths.py, pipeline, and backend; no model imported")


if __name__ == "__main__":
    main()
