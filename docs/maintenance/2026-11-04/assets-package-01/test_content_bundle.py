"""Verify byte deduplication, split archives, corruption detection and safe restore."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bundle_under_test", PHASE / "updates/scripts/migration/content_bundle.py")
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bundle-fixture-", dir=PHASE)
        self.base = Path(self.temp.name).resolve()
        assert self.base.is_relative_to(PHASE.resolve())
        self.addCleanup(self.temp.cleanup)
        self.inventory = self.base / "inventory"
        self.inventory.mkdir()
        self.package = self.base / "package"
        self.roots = {name: self.base / name for name in ("one", "two")}
        for path in self.roots.values():
            path.mkdir()
        self.records = []
        for root, name, payload in (("one", "a.bin", b"a" * 16000), ("one", "name 中文🌱.bin", b"b" * 16000),
                                    ("one", "empty", b""), ("two", "duplicate.bin", b"a" * 16000)):
            path = self.roots[root] / name
            path.write_bytes(payload)
            self.records.append({"root": root, "path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "mtime_ns": path.stat().st_mtime_ns})
        self.write_inventory()

    def write_inventory(self):
        (self.inventory / "SOURCE_FILES.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.records), encoding="utf-8")
        for name in ("SOURCE_DIRECTORIES.jsonl", "SOURCE_LINKS.jsonl"):
            (self.inventory / name).write_text("", encoding="utf-8")
        (self.inventory / "SOURCE_LINKS_RAW.json").write_text("[]\n", encoding="utf-8")
        (self.inventory / "BASELINE.json").write_text(json.dumps({"source_roots": {k: str(v) for k, v in self.roots.items()}}), encoding="utf-8")

    def build(self):
        return bundle.build(self.inventory, self.package, max_volume_bytes=32768)

    def test_build_verify_and_volume_bound(self):
        result = self.build()
        self.assertEqual(result["source_files_fresh_byte_verified"], 4)
        self.assertEqual(result["unique_objects"], 3)
        self.assertGreater(len(result["volumes"]), 1)
        self.assertTrue(all(v["bytes"] <= 32768 for v in result["volumes"]))
        self.assertTrue(bundle.verify(self.package)["passed"])

    def test_restore_duplicates_unicode_and_zero_bytes(self):
        self.build()
        destination = self.base / "restore"
        result = bundle.restore_files(self.package, destination)
        self.assertEqual(result["restored_regular_files"], 4)
        for row in self.records:
            self.assertEqual((destination / row["root"] / row["path"]).read_bytes(), (self.roots[row["root"]] / row["path"]).read_bytes())

    def test_corrupted_archive_payload_is_rejected(self):
        result = self.build()
        archive = self.package / result["volumes"][0]["name"]
        with archive.open("r+b") as handle:
            handle.seek(1024)
            old = handle.read(1)
            handle.seek(1024)
            handle.write(bytes([old[0] ^ 1]))
        with self.assertRaises((ValueError, tarfile.TarError)):
            bundle.verify(self.package)

    def test_traversal_is_rejected_before_package_creation(self):
        self.records[0]["path"] = "../../escape"
        self.write_inventory()
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.package.exists())

    def test_duplicate_content_change_with_unchanged_size_mtime_fails(self):
        row = self.records[-1]
        path = self.roots[row["root"]] / row["path"]
        path.write_bytes(b"z" * row["bytes"])
        os.utime(path, ns=(row["mtime_ns"], row["mtime_ns"]))
        with self.assertRaisesRegex(ValueError, "content does not match"):
            self.build()
        self.assertFalse((self.package / "PACKAGE.json").exists())
        self.assertFalse(json.loads((self.package / "BUILD_FAILURE.json").read_text())["complete"])

    def test_existing_restore_destination_is_preserved(self):
        self.build()
        target = self.base / "existing"
        target.mkdir()
        marker = target / "keep"
        marker.write_text("original")
        with self.assertRaises(FileExistsError):
            bundle.restore_files(self.package, target)
        self.assertEqual(marker.read_text(), "original")

    def test_link_control_metadata_tampering_is_rejected(self):
        self.build()
        (self.package / "SOURCE_LINKS_RAW.json").write_text("[1]\n")
        with self.assertRaisesRegex(ValueError, "Control manifest"):
            bundle.verify(self.package)


if __name__ == "__main__":
    unittest.main(verbosity=2)
