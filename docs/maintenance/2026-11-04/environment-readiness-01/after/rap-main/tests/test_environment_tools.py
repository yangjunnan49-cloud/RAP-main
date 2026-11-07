"""Metadata isolation and pre-import CPU probe guards using stdlib fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/environment/inspect_metadata.py"
PROBE = REPO / "scripts/environment/cpu_probe.py"
spec = importlib.util.spec_from_file_location("metadata_only_tool", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EnvironmentToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="a4-environment-", dir=REPO / "tests")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.site = self.base / "fixture-site-中文🌱"
        dist = self.site / "a4_fixture-1.0.dist-info"
        dist.mkdir(parents=True)
        (dist / "METADATA").write_text("Metadata-Version: 2.1\nName: a4-fixture\nVersion: 1.0\nRequires-Dist: numpy>=1\n", encoding="utf-8")
        # Metadata collection must never import even a package with a failing initializer.
        package = self.site / "a4_fixture"
        package.mkdir()
        (package / "__init__.py").write_text("raise RuntimeError('must never be imported')", encoding="utf-8")

    def test_metadata_reads_without_import_and_deduplicates_paths(self):
        result = module.inspect([self.site, self.site / "."])
        self.assertEqual(len(result["packages"]), 1)
        self.assertEqual(result["packages"][0]["version"], "1.0")
        self.assertNotIn("a4_fixture", sys.modules)

    def test_metadata_cli_isolated_from_other_cwd(self):
        result = subprocess.run([sys.executable, "-I", "-S", "-B", str(TOOL), "--site-path", str(self.site)],
                                cwd=REPO / "docs", capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["package_imports_performed"])

    def test_existing_receipt_is_not_overwritten(self):
        output = self.base / "existing.json"
        output.write_text("preserve original", encoding="utf-8")
        result = subprocess.run([sys.executable, "-I", "-S", "-B", str(TOOL), "--site-path", str(self.site), "--output", str(output)], capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), "preserve original")

    def test_cpu_probe_guard_fails_before_importing_torch(self):
        env = dict(os.environ)
        env.pop("CUDA_VISIBLE_DEVICES", None)
        result = subprocess.run([sys.executable, "-I", "-S", "-B", str(PROBE), "--rap-root", str(REPO), "--slam-root", str(REPO.parent / "RAP-SLAM"),
                                 "--output", str(self.base / "never.json")], env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertIn("CUDA_VISIBLE_DEVICES", result.stderr)
        self.assertNotIn("No module named", result.stderr)
        self.assertFalse((self.base / "never.json").exists())

    def test_metadata_refuses_site_initialization_mode(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--site-path", str(self.site)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertIn("avoid site initialization", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
