"""Build, check, or execute explicit commands for current RAP entry points."""
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .paths import ENV_NAMES, absolute, resolve_paths

TASKS = ("sample", "demo", "features", "slam", "evaluate")
# Runtime-controlled arguments cannot be bypassed by forwarding a second path.
RESERVED = {
    "sample": {"data_root", "data.data_root", "log_dir", "ckpt_path", "hydra.run.dir", "hydra.job.chdir"},
    "demo": {"--input", "-i", "--output", "-o", "--log_dir", "--feature_extraction_checkpoint", "--flow_model_checkpoint", "--config"},
    "features": {"--input", "-i", "--output", "-o", "--checkpoint", "--hdf5_output"},
    "slam": {"--rap-root", "--output", "--map", "--real-root", "--spires-root", "--rap-ckpt", "--spinnet-ckpt"},
    "evaluate": set(),
}


def parser():
    p = argparse.ArgumentParser(description="RAP portable launcher (default: plan only; no model imports)", allow_abbrev=False)
    p.add_argument("task", choices=TASKS)
    p.add_argument("--paths", help="Local JSON path config; relative values use its directory")
    for key in ENV_NAMES:
        p.add_argument("--" + key.replace("_", "-"), dest=key)
    p.add_argument("--input", help="Sample data directory, PLY directory, or feature input")
    out = p.add_mutually_exclusive_group(required=True)
    out.add_argument("--run-id", help="New output_root/task/run-id directory")
    out.add_argument("--output", help="Explicit new output directory")
    p.add_argument("--map", help="Simulation map (SLAM)")
    p.add_argument("--real-root", help="Root containing dataset/ (SLAM real loader)")
    p.add_argument("--spires-root", help="Oxford Spires root (SLAM)")
    p.add_argument("--poses-dir", help="External KITTI trajectories (evaluate)")
    p.add_argument("--dataset-root", help="Root containing poses/ and sequences/ (evaluate)")
    p.add_argument("--sequences", default="00,05,06", help="Existing external-evaluation contract")
    p.add_argument("--method-label", help="Explicit external method label (evaluate)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Return failure for missing paths; still no imports or execution")
    mode.add_argument("--execute", action="store_true", help="Execute the checked command in this Python environment")
    return p


def split_arguments(argv):
    if "--" in argv:
        pos = argv.index("--")
        return argv[:pos], argv[pos + 1:]
    return argv, []


def reject_forwarded_paths(task, extra):
    if task == "evaluate" and extra:
        raise ValueError("evaluate accepts named launcher options only")
    for token in extra:
        key = token.split("=", 1)[0]
        if task == "sample":
            key = key.lstrip("+~")
            if token.startswith("--") or key in RESERVED[task] or key in {"data", "hydra"} or key.startswith(("hydra.", "data.data_root.")):
                raise ValueError("Pass input/output/checkpoint paths through launcher options: " + token)
        elif token.startswith("-"):
            # Reject argparse abbreviations and concatenated short path aliases.
            if any(key == item or (key.startswith("--") and item.startswith(key)) or
                   (len(item) == 2 and token.startswith(item)) for item in RESERVED[task]):
                raise ValueError("Pass paths through launcher options: " + token)


def hydra_string(value):
    # Hydra quoted values must survive spaces, commas, brackets, and '='.
    return json.dumps(str(value), ensure_ascii=False)


def plan(args, extra):
    paths, sources = resolve_paths(args.paths, {key: getattr(args, key) for key in ENV_NAMES})
    reject_forwarded_paths(args.task, extra)
    if args.run_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.run_id):
        raise ValueError("run-id must be one safe path component")
    output = absolute(args.output, Path.cwd()) if args.output else paths["output_root"] / args.task / args.run_id
    input_path = absolute(args.input, Path.cwd()) if args.input else None
    errors, required = [], []

    def need(path, kind, role):
        path = Path(path)
        required.append({"role": role, "path": str(path), "kind": kind})
        valid = path.is_dir() if kind == "directory" else path.is_file() if kind == "file" else path.exists()
        if not valid:
            errors.append(f"Missing {role} ({kind}): {path}")

    if output.exists() or output.is_symlink():
        errors.append("Output already exists; choose a new output: " + str(output))
    ancestor = output.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        errors.append("Output parent is not a directory: " + str(ancestor))
    if input_path and (output == input_path or input_path in output.parents or output in input_path.parents):
        errors.append("Input and output must be separate trees")
    root = paths["slam_root"] if args.task in {"slam", "evaluate"} else paths["rap_root"]
    entry = {"sample": "sample.py", "demo": "demo.py", "features": "dataset_process/extract_sample_features.py",
             "slam": "scripts/run_pipeline.py", "evaluate": "scripts/eval_external_trajectory.py"}[args.task]
    need(root / entry, "file", "entry point")
    argv = [sys.executable, "-B", str(root / entry)]
    if args.task in {"sample", "demo", "features"}:
        if input_path is None:
            raise ValueError("--input is required for " + args.task)
        need(input_path, "path" if args.task == "features" else "directory", "input")
    if args.task in {"sample", "demo"}:
        need(paths["rap_root"] / "config/RAP_inference.yaml", "file", "inference config")
        checkpoint = paths[args.task + "_checkpoint"]
        need(checkpoint, "file", "RAP checkpoint")
        if args.task == "sample":
            argv += ["--config-name", "RAP_inference", "data_root=" + hydra_string(input_path),
                     "log_dir=" + hydra_string(output), "ckpt_path=" + hydra_string(checkpoint), "hydra.job.chdir=false"]
        else:
            need(paths["spinnet_checkpoint"], "file", "miniSpinNet checkpoint")
            argv += ["--input", str(input_path), "--output", str(output), "--log_dir", str(output / "logs"),
                     "--flow_model_checkpoint", str(checkpoint), "--feature_extraction_checkpoint", str(paths["spinnet_checkpoint"]),
                     "--config", "RAP_inference"]
    elif args.task == "features":
        if "--hdf5_only" not in extra and "--dry_run" not in extra:
            need(paths["spinnet_checkpoint"], "file", "miniSpinNet checkpoint")
        argv += ["--input", str(input_path), "--output", str(output), "--checkpoint", str(paths["spinnet_checkpoint"])]
    elif args.task == "slam":
        argv += ["--rap-root", str(paths["rap_root"]), "--output", str(output),
                 "--rap-ckpt", str(paths["backend_checkpoint"]), "--spinnet-ckpt", str(paths["spinnet_checkpoint"])]
        defaults = {"map": paths["rap_root"] / "demo_example_data/map_kitti/kitti00.ply",
                    "real_root": paths["slam_root"] / "data/poss",
                    "spires_root": paths["datasets_root"] / "oxford_spires"}
        for flag, default in defaults.items():
            value = absolute(getattr(args, flag), Path.cwd()) if getattr(args, flag) else default
            argv += ["--" + flag.replace("_", "-"), str(value)]
        # Import only the dependency-free SLAM argument/path modules, never the pipeline.
        need(paths["slam_root"] / "rap_slam/cli.py", "file", "SLAM CLI module")
        if not errors:
            sys.path.insert(0, str(paths["slam_root"]))
            try:
                cli = importlib.import_module("rap_slam.cli")
                runtime = importlib.import_module("rap_slam.runtime_paths")
                parsed = cli.parse_args(argv[3:] + extra)
                errors.extend(runtime.validate_pipeline_paths(parsed))
            finally:
                sys.path.pop(0)
    else:
        if not args.poses_dir or not args.dataset_root or not args.method_label:
            raise ValueError("evaluate requires --poses-dir, --dataset-root, and --method-label")
        poses = absolute(args.poses_dir, Path.cwd())
        dataset = absolute(args.dataset_root, Path.cwd())
        seqs = [s.strip() for s in args.sequences.split(",")]
        if not seqs or any(s not in {"00", "05", "06"} for s in seqs):
            raise ValueError("External evaluation supports sequences 00,05,06 only")
        for seq in seqs:
            need(poses / f"kitti{seq}_poses_kitti.txt", "file", "external trajectory")
            need(dataset / f"poses/{seq}.txt", "file", "reference trajectory")
            need(dataset / f"sequences/{seq}/calib.txt", "file", "calibration")
        argv += ["--poses-dir", str(poses), "--dataset-root", str(dataset), "--method-label", args.method_label,
                 "--sequences", args.sequences, "--out", str(output)]
    argv += extra
    return {"task": args.task, "mode": "execute" if args.execute else "check" if args.check else "plan",
            "cwd": str(root), "argv": argv, "output": str(output),
            "paths": {k: str(v) for k, v in paths.items()}, "path_sources": sources,
            "required_paths": required, "errors": errors,
            "validation_scope": "Path/CLI checks only; no data provenance, model, dependency, or numerical validation"}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    own, extra = split_arguments(sys.argv[1:] if argv is None else argv)
    p = parser()
    args = p.parse_args(own)
    try:
        result = plan(args, extra)
    except (OSError, ValueError) as exc:
        p.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if result["errors"]:
        return 2 if args.execute or args.check else 0
    if not args.execute:
        return 0
    env = dict(os.environ)
    env.update({ENV_NAMES[k]: v for k, v in result["paths"].items()})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("HF_HOME", str(Path(result["paths"]["cache_root"]) / "huggingface"))
    Path(result["output"]).parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(result["argv"], cwd=result["cwd"], env=env, check=False).returncode
