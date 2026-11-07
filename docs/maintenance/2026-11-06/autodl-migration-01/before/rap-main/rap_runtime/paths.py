"""Resolve relocatable runtime paths without importing numerical dependencies."""
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_NAMES = {
    "workspace": "RAP_WORKSPACE", "rap_root": "RAP_ROOT", "slam_root": "RAP_SLAM_ROOT",
    "datasets_root": "RAP_DATASETS_ROOT", "weights_root": "RAP_WEIGHTS_ROOT",
    "output_root": "RAP_OUTPUT_ROOT", "cache_root": "RAP_CACHE_ROOT",
    "sample_checkpoint": "RAP_SAMPLE_CHECKPOINT", "demo_checkpoint": "RAP_DEMO_CHECKPOINT",
    "backend_checkpoint": "RAP_BACKEND_CHECKPOINT", "spinnet_checkpoint": "RAP_SPINNET_CHECKPOINT",
}


def absolute(value, base):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Path must be a nonempty string")
    path = Path(value).expanduser()
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


def resolve_paths(config_file=None, overrides=None, environ=None, cwd=None):
    """CLI > JSON > environment > layout; relative JSON paths use its directory."""
    environ = os.environ if environ is None else environ
    cwd = Path.cwd() if cwd is None else Path(cwd)
    overrides = {} if overrides is None else overrides
    config_file = config_file or environ.get("RAP_PATHS_FILE")
    config, config_base = {}, cwd
    if config_file:
        filename = absolute(str(config_file), cwd)
        raw = json.loads(filename.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict) or set(raw) != {"schema_version", "paths"} or raw["schema_version"] != 1:
            raise ValueError("Path config requires schema_version=1 and paths")
        config = raw["paths"]
        if not isinstance(config, dict) or set(config) - set(ENV_NAMES):
            raise ValueError("Unknown path config keys or invalid paths object")
        config_base = filename.parent
    if set(overrides) - set(ENV_NAMES):
        raise ValueError("Unknown path override")
    values, sources = {}, {}

    def select(key, default):
        if overrides.get(key) is not None:
            value, base, source = overrides[key], cwd, "cli"
        elif key in config:
            value, base, source = config[key], config_base, "json"
        elif environ.get(ENV_NAMES[key]):
            value, base, source = environ[ENV_NAMES[key]], cwd, "environment"
        else:
            value, base, source = str(default), cwd, "layout"
        values[key] = absolute(value, base)
        sources[key] = source

    select("workspace", REPO_ROOT.parent)
    select("rap_root", values["workspace"] / "RAP-main")
    select("slam_root", values["workspace"] / "RAP-SLAM")
    select("datasets_root", values["workspace"] / "Datasets")
    select("weights_root", values["rap_root"] / "weights")
    select("output_root", values["workspace"] / "RAP-runs")
    select("cache_root", values["workspace"] / ".cache/rap")
    select("sample_checkpoint", values["weights_root"] / "rap_model.ckpt")
    select("demo_checkpoint", values["weights_root"] / "rap_model.ckpt")
    select("backend_checkpoint", values["weights_root"] / "rap_model_12.ckpt")
    select("spinnet_checkpoint", values["weights_root"] / "mini_spinnet_t.pth")
    return values, sources
