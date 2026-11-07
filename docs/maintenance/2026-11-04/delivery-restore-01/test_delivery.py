"""Exercise layered byte restoration, collision guards and superseded versions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import tarfile
import unittest

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


delivery = module("tested_delivery", PHASE / "updates/scripts/migration/delivery.py")
bundle = module("tested_content_bundle", REPO / "scripts/migration/content_bundle.py")


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delivery-test-", dir=PHASE)
        self.base = Path(self.temp.name).resolve()
        assert self.base.is_relative_to(PHASE)
        self.addCleanup(self.cleanup_fixture)
        self.roots = {"rap-main": self.base / "source-main", "reports": self.base / "source-report"}
        for root in self.roots.values():
            root.mkdir()
        self.layout = {"rap-main": "RAP-main", "reports": "RAP-SLAM-report"}
        self.records = []
        for root, path, raw in [("rap-main", "notes 中文.txt", b"original notes"), ("reports", "same.txt", b"original notes"),
                                ("rap-main", "empty", b""), ("rap-main", "payload.bin", b"x" * 20000)]:
            target = self.roots[root] / path
            target.write_bytes(raw)
            self.records.append({"root": root, "path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "mtime_ns": target.stat().st_mtime_ns})
        self.inventory = self.base / "inventory"
        self.inventory.mkdir()
        self.write_inventory(self.inventory, self.records)
        self.package = self.base / "base-layer"
        bundle.build(self.inventory, self.package, max_volume_bytes=32768)
        self.destination = self.base / "restored"

    def cleanup_fixture(self):
        target = self.base.resolve()
        assert target.is_relative_to(PHASE.resolve()) and target.name.startswith("delivery-test-")
        if target.exists():
            shutil.rmtree(delivery.native_absolute(target))
        self.temp.cleanup()

    def write_inventory(self, folder, records):
        (folder / "SOURCE_FILES.jsonl").write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records).encode("utf-8"))
        for name in ("SOURCE_DIRECTORIES.jsonl", "SOURCE_LINKS.jsonl"):
            (folder / name).write_bytes(b"")
        (folder / "SOURCE_LINKS_RAW.json").write_bytes(b"[]\n")
        (folder / "BASELINE.json").write_text(json.dumps({"source_roots": {k: str(v) for k, v in self.roots.items()}}), encoding="utf-8")

    def test_complete_restore_dedup_unicode_and_empty(self):
        r = delivery.restore_layer(self.package, self.destination, self.layout)
        self.assertEqual(r["ordinary_files_restored"], 4)
        self.assertEqual(r["unique_objects_and_volume_hashes_verified"], 3)
        self.assertTrue(delivery.check_files(self.records, self.destination, self.layout)["passed"])
        self.assertEqual((self.destination / "RAP-main/empty").read_bytes(), b"")

    def test_overlay_preserves_old_bytes_in_version_archive(self):
        delivery.restore_layer(self.package, self.destination, self.layout)
        path = self.roots["rap-main"] / "notes 中文.txt"
        path.write_bytes(b"new reviewed notes")
        delta_row = {**self.records[0], "bytes": path.stat().st_size, "sha256": delivery.sha(path), "mtime_ns": path.stat().st_mtime_ns}
        inv = self.base / "delta-inventory"
        inv.mkdir()
        self.write_inventory(inv, [delta_row])
        delta = self.base / "delta"
        bundle.build(inv, delta, max_volume_bytes=32768)
        result = delivery.restore_layer(delta, self.destination, self.layout, overlay=True, expected_before=self.records)
        self.assertEqual(len(result["superseded_base_versions_preserved"]), 1)
        self.assertEqual((self.destination / "RAP-main/notes 中文.txt").read_bytes(), b"new reviewed notes")
        self.assertEqual((self.destination / result["superseded_base_versions_preserved"][0]["path"]).read_bytes(), b"original notes")
        self.assertEqual((self.destination / "RAP-SLAM-report/same.txt").read_bytes(), b"original notes")

    def test_corrupt_volume_is_rejected(self):
        archive = next(self.package.glob("payload-*.tar"))
        with archive.open("r+b") as handle:
            handle.seek(512)
            old = handle.read(1)
            handle.seek(512)
            handle.write(bytes([old[0] ^ 1]))
        with self.assertRaises(ValueError):
            delivery.restore_layer(self.package, self.destination, self.layout)

    def test_existing_destination_is_rejected(self):
        self.destination.mkdir()
        with self.assertRaises(FileExistsError):
            delivery.restore_layer(self.package, self.destination, self.layout)

    def test_traversal_or_mapping_collisions_are_rejected(self):
        for bad in ("../escape", "E:/outside", "a\\b"):
            with self.assertRaises(ValueError):
                delivery.validate_rows([{**self.records[0], "path": bad}], self.layout)
        with self.assertRaises(ValueError):
            delivery.validate_rows([self.records[0], {**self.records[0], "root": "reports"}], {"rap-main": "shared", "reports": "shared"})

    def test_wrong_overlay_baseline_is_rejected_without_replacing_file(self):
        delivery.restore_layer(self.package, self.destination, self.layout)
        wrong = [{**r, "sha256": "0" * 64} for r in self.records]
        with self.assertRaises(ValueError):
            delivery.restore_layer(self.package, self.destination, self.layout, overlay=True, expected_before=wrong)
        self.assertEqual((self.destination / "RAP-main/notes 中文.txt").read_bytes(), b"original notes")

    def test_deeper_workspace_preserves_long_relative_names(self):
        row = {**self.records[0], "path": "a" * 110 + "/" + "b" * 110 + "/name.txt"}
        target = delivery.mapped(self.destination, self.layout, row)
        target.parent.mkdir(parents=True)
        target.write_bytes(b"long-path preserved")
        self.assertEqual(target.read_bytes(), b"long-path preserved")

    def evidence_fixture(self):
        package = self.base / "release"
        package.mkdir()
        tree = self.base / "evidence-source"
        (tree / "after/rap-main").mkdir(parents=True)
        new = tree / "after/rap-main" / self.records[0]["path"]
        new.write_bytes(b"final reviewed control")
        snapshot = {**self.records[0], "sha256": delivery.sha(new), "bytes": new.stat().st_size,
                    "snapshot": "after/rap-main/" + self.records[0]["path"]}
        (tree / "CURRENT_DOCUMENT_SNAPSHOTS.json").write_text(json.dumps([snapshot], ensure_ascii=False), encoding="utf-8")
        (tree / "LATE_GIT_SNAPSHOTS.json").write_text("[]", encoding="utf-8")
        expected = []
        with tarfile.open(package / "evidence.tar", "w", format=tarfile.PAX_FORMAT) as out:
            for f in sorted(tree.rglob("*")):
                if f.is_file():
                    name = f.relative_to(tree).as_posix()
                    out.add(f, arcname=name, recursive=False)
                    expected.append({"path": name, "bytes": f.stat().st_size, "sha256": delivery.sha(f)})
        (package / "EVIDENCE_MANIFEST.json").write_text(json.dumps({"files": expected}), encoding="utf-8")
        (package / "FINAL_FILES.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.records), encoding="utf-8")
        (package / "PROJECT.json").write_text(json.dumps({"layout": self.layout}), encoding="utf-8")
        master = {"evidence": {"manifest": "EVIDENCE_MANIFEST.json", "manifest_sha256": delivery.sha(package / "EVIDENCE_MANIFEST.json"),
                               "workspace_prefix": "RAP-main/docs/audit", "archive": "evidence.tar", "archive_bytes": (package / "evidence.tar").stat().st_size,
                               "archive_sha256": delivery.sha(package / "evidence.tar")},
                  "project_manifest": "PROJECT.json", "project_manifest_sha256": delivery.sha(package / "PROJECT.json")}
        (package / "DELIVERY.json").write_text(json.dumps(master), encoding="utf-8")
        return package

    def test_final_control_overlay_keeps_prior_version(self):
        delivery.restore_layer(self.package, self.destination, self.layout)
        release = self.evidence_fixture()
        result = delivery.install_evidence(release / "DELIVERY.json", self.destination)
        self.assertTrue(result["passed"])
        self.assertEqual((self.destination / "RAP-main" / self.records[0]["path"]).read_bytes(), b"final reviewed control")
        self.assertEqual((self.destination / "archives/source-versions/A7-control/rap-main" / self.records[0]["path"]).read_bytes(), b"original notes")

    def test_evidence_padding_corruption_blocks_control_overwrite(self):
        delivery.restore_layer(self.package, self.destination, self.layout)
        release = self.evidence_fixture()
        with (release / "evidence.tar").open("r+b") as handle:
            handle.seek(-1, 2)
            handle.write(b"X")
        with self.assertRaises(ValueError):
            delivery.install_evidence(release / "DELIVERY.json", self.destination)
        self.assertEqual((self.destination / "RAP-main" / self.records[0]["path"]).read_bytes(), b"original notes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
