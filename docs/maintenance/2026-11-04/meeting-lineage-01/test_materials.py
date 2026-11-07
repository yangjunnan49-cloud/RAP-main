"""Check safe, explicit preparation of meeting authoring copies."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("materials", PHASE / "updates/scripts/meetings/materials.py")
materials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materials)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="materials-test-", dir=PHASE)
        self.base = Path(self.temp.name).resolve()
        assert self.base.is_relative_to(PHASE)
        self.addCleanup(self.temp.cleanup)
        self.root = self.base / "source"
        self.root.mkdir()
        self.file = self.root / "中文 notes.txt"
        self.file.write_bytes(b"preserve original")
        self.record = {"root": "rap-main", "path": self.file.name, "family": "test", "role": "editable_source",
                       "bytes": self.file.stat().st_size, "sha256": hashlib.sha256(self.file.read_bytes()).hexdigest()}
        self.roots = {"rap-main": self.root}
        self.target = self.base / "prepared"

    def test_default_is_plan_only(self):
        result = materials.prepare([self.record], "test", self.roots, self.target)
        self.assertFalse(result["executed"])
        self.assertFalse(self.target.exists())

    def test_new_copy_matches_and_opaque_arrays_stay_out(self):
        opaque = {**self.record, "path": "not-present.npy", "role": "scientific_or_data_history_opaque_preserved"}
        result = materials.prepare([self.record, opaque], "test", self.roots, self.target, True)
        self.assertEqual(result["files_selected"], 1)
        self.assertEqual((self.target / "rap-main" / self.file.name).read_bytes(), self.file.read_bytes())
        self.assertFalse((self.target / "rap-main/not-present.npy").exists())

    def test_overwrite_is_rejected(self):
        self.target.mkdir()
        with self.assertRaises(FileExistsError):
            materials.prepare([self.record], "test", self.roots, self.target, True)

    def test_changed_same_size_source_rejected_before_output(self):
        self.file.write_bytes(b"X" * self.record["bytes"])
        with self.assertRaises(ValueError):
            materials.prepare([self.record], "test", self.roots, self.target, True)
        self.assertFalse(self.target.exists())

    def test_traversal_and_historical_overlap_rejected(self):
        for name in ("../escape", "E:/outside", "a\\b"):
            with self.assertRaises(ValueError):
                materials.prepare([{**self.record, "path": name}], "test", self.roots, self.target, True)
        with self.assertRaises(ValueError):
            materials.prepare([self.record], "test", self.roots, self.root / "copies", True)

    def test_normalization_keeps_template_tag_used_by_questions(self):
        original = (PHASE.parents[3] / "working files/weekly_20261101/create_weekly_script.js").read_text(encoding="utf-8")
        normalized = materials.normalized_notes_script(original)
        self.assertIn("const T = String.raw;", normalized)
        self.assertIn("T`问：${q}`", normalized)
        self.assertEqual(normalized.split("const palette =", 1)[1], original.split("const palette =", 1)[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
