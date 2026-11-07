"""Relocation, preflight, and dispatch tests without numerical dependencies."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from rap_runtime.launch import main, parser, plan, reject_forwarded_paths
from rap_runtime.paths import resolve_paths


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        # All temporary fixtures and cleanup stay inside the authorized workspace.
        self.temporary = tempfile.TemporaryDirectory(prefix="a3-runtime-", dir=REPO / "tests")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.workspace = self.base / "relocated workspace 中文,=x"
        self.rap = self.workspace / "RAP-main"
        self.slam = self.workspace / "RAP-SLAM"
        self.input = self.workspace / "input"
        self.input.mkdir(parents=True)
        for file in ("sample.py", "demo.py", "dataset_process/extract_sample_features.py", "config/RAP_inference.yaml",
                     "weights/rap_model.ckpt", "weights/rap_model_12.ckpt", "weights/mini_spinnet_t.pth"):
            self.touch(self.rap / file)
        self.config = self.base / "paths.json"
        self.config.write_text(json.dumps({"schema_version": 1, "paths": {"workspace": self.workspace.name}}), encoding="utf-8")

    @staticmethod
    def touch(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture only; never load as scientific input", encoding="utf-8")

    def args(self, task, *more):
        return parser().parse_args([task, "--paths", str(self.config), "--run-id", "test-run", *more])

    def test_precedence_and_config_relative_paths(self):
        env = {"RAP_WORKSPACE": str(self.base / "ignored"), "RAP_WEIGHTS_ROOT": str(self.base / "env-weights")}
        values, source = resolve_paths(self.config, {"output_root": "cli-output"}, environ=env, cwd=self.base)
        self.assertEqual(values["workspace"], self.workspace)
        self.assertEqual(values["weights_root"], self.base / "env-weights")
        self.assertEqual(values["output_root"], self.base / "cli-output")
        self.assertEqual(source["workspace"], "json")
        self.assertEqual(source["weights_root"], "environment")
        self.assertEqual(source["output_root"], "cli")

    def test_invalid_config_and_unknown_keys(self):
        for raw in ({"schema_version": 2, "paths": {}}, {"schema_version": 1, "paths": {"typo": "/x"}},
                    {"schema_version": 1, "paths": {"workspace": None}}):
            self.config.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ValueError):
                resolve_paths(self.config, environ={})

    def test_sample_demo_features_use_absolute_paths(self):
        for task in ("sample", "demo", "features"):
            with self.subTest(task=task), patch.dict(os.environ, {}, clear=True):
                result = plan(self.args(task, "--input", str(self.input)), [])
                self.assertEqual(result["errors"], [])
                self.assertEqual(result["cwd"], str(self.rap))
                self.assertEqual(result["output"], str(self.workspace / "RAP-runs" / task / "test-run"))
                if task == "sample":
                    value = next(v for v in result["argv"] if v.startswith("data_root="))
                    self.assertEqual(json.loads(value.split("=", 1)[1]), str(self.input))

    def test_missing_files_and_existing_output_fail_before_dispatch(self):
        (self.rap / "weights/rap_model.ckpt").unlink()
        with patch.dict(os.environ, {}, clear=True):
            result = plan(self.args("sample", "--input", str(self.input)), [])
            self.assertTrue(any("RAP checkpoint" in e for e in result["errors"]))
            output = self.workspace / "RAP-runs/sample/test-run"
            output.mkdir(parents=True)
            result = plan(self.args("sample", "--input", str(self.input)), [])
            self.assertTrue(any("Output already exists" in e for e in result["errors"]))

    def test_overlapping_input_output_rejected(self):
        args = parser().parse_args(["features", "--paths", str(self.config), "--input", str(self.input),
                                    "--output", str(self.input / "child")])
        self.assertTrue(any("separate trees" in e for e in plan(args, [])["errors"]))

    def test_forwarded_path_overrides_rejected(self):
        for task, extra in (("sample", ["+ckpt_path=x"]), ("sample", ["~log_dir"]),
                            ("sample", ["--config-path=/other"]), ("demo", ["-oelsewhere"]),
                            ("features", ["--hdf5_output=/old"]), ("slam", ["--rap-r=/other"])):
            with self.subTest(task=task, extra=extra), self.assertRaises(ValueError):
                reject_forwarded_paths(task, extra)

    def test_evaluation_checks_explicit_references(self):
        self.touch(self.slam / "scripts/eval_external_trajectory.py")
        poses, dataset = self.workspace / "poses", self.workspace / "dataset"
        for file in (poses / "kitti00_poses_kitti.txt", dataset / "poses/00.txt", dataset / "sequences/00/calib.txt"):
            self.touch(file)
        result = plan(self.args("evaluate", "--poses-dir", str(poses), "--dataset-root", str(dataset),
                                "--sequences", "00", "--method-label", "fixture"), [])
        self.assertEqual(result["errors"], [])
        self.assertIn(str(dataset), result["argv"])

    def test_execute_dispatch_is_same_interpreter_without_shell(self):
        with patch.dict(os.environ, {}, clear=True), patch("rap_runtime.launch.subprocess.run") as run:
            run.return_value.returncode = 17
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(["sample", "--paths", str(self.config), "--input", str(self.input), "--run-id", "new", "--execute"])
            self.assertEqual(result, 17)
            argv = run.call_args.args[0]
            self.assertEqual(argv[0], sys.executable)
            self.assertEqual(run.call_args.kwargs["cwd"], str(self.rap))
            self.assertEqual(run.call_args.kwargs["env"]["RAP_ROOT"], str(self.rap))
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertFalse((self.workspace / "RAP-runs/sample/new").exists())

    def test_check_never_dispatches_or_creates_output(self):
        with patch.dict(os.environ, {}, clear=True), patch("rap_runtime.launch.subprocess.run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(["demo", "--paths", str(self.config), "--input", str(self.input), "--run-id", "plan", "--check"])
            self.assertEqual(result, 0)
            run.assert_not_called()
            self.assertFalse((self.workspace / "RAP-runs").exists())

    def test_missing_checkpoint_execute_is_blocked(self):
        (self.rap / "weights/rap_model.ckpt").unlink()
        with patch.dict(os.environ, {}, clear=True), patch("rap_runtime.launch.subprocess.run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(["sample", "--paths", str(self.config), "--input", str(self.input), "--run-id", "bad", "--execute"])
            self.assertEqual(result, 2)
            run.assert_not_called()
            self.assertFalse((self.workspace / "RAP-runs").exists())

    def test_invalid_run_id_rejected(self):
        args = self.args("demo", "--input", str(self.input))
        for value in ("..", "a/b", "../outside", "/absolute"):
            args.run_id = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                plan(args, [])

    def test_real_command_checks_from_other_cwd(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(REPO / "scripts/run.py"), "sample", "--paths", str(self.config),
                                 "--input", str(self.input), "--run-id", "check", "--check"],
                                cwd=REPO / "docs", capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["errors"], [])
        self.assertFalse((self.workspace / "RAP-runs").exists())

    def test_no_numerical_imports(self):
        for name in ("numpy", "torch", "hydra", "lightning", "open3d"):
            self.assertNotIn(name, sys.modules)

    def test_backend_missing_feature_file_only_required_when_enabled(self):
        sys.path.insert(0, str(REPO.parent / "RAP-SLAM"))
        try:
            from rap_slam.runtime_paths import backend_paths
        finally:
            sys.path.pop(0)
        (self.rap / "rectified_point_flow").mkdir()
        spin = self.rap / "weights/mini_spinnet_t.pth"
        spin.unlink()
        with patch.dict(os.environ, {}, clear=True):
            values = backend_paths(str(self.rap), feature_extraction_on=False)
            self.assertEqual(Path(values[1]), self.rap / "weights/rap_model_12.ckpt")
            with self.assertRaisesRegex(FileNotFoundError, "miniSpinNet checkpoint"):
                backend_paths(str(self.rap), feature_extraction_on=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
