"""Run a path/help check while rejecting imports of numerical/model libraries."""
import builtins
import runpy
import sys

BANNED = {"numpy", "torch", "hydra", "lightning", "open3d", "gtsam", "kiss_icp"}
original_import = builtins.__import__


def guarded_import(name, *args, **kwargs):
    if name.split(".", 1)[0] in BANNED:
        raise RuntimeError("A3 path check attempted numerical import: " + name)
    return original_import(name, *args, **kwargs)


if __name__ == "__main__":
    entry = sys.argv[1]
    sys.argv = sys.argv[1:]
    builtins.__import__ = guarded_import
    try:
        runpy.run_path(entry, run_name="__main__")
    finally:
        assert not (BANNED & set(sys.modules))
        print("A3_NUMERICAL_IMPORT_GUARD_PASS", file=sys.stderr)
