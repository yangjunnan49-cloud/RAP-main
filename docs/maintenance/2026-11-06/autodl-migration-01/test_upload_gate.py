"""Exercise corrupted/partial upload rejection using tiny temporary fixtures."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
import uuid

spec = importlib.util.spec_from_file_location("upload_gate", Path(__file__).with_name("receive_and_restore.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class UploadGateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / "validation" / ("upload-gate-" + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.transfer = self.root / "transfer"
        self.receipts = self.root / "receipts"
        self.transfer.mkdir()
        self.receipts.mkdir()
        self.original_sleep = gate.time.sleep
        gate.time.sleep = lambda seconds: None

    def tearDown(self):
        gate.time.sleep = self.original_sleep
        # Tiny fixtures remain as validation evidence; no recursive deletion.

    def expected(self, data=b"abc"):
        return dict(files=[dict(path="A5/file.bin", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())],
                    bytes=len(data), delivery_sha256="fixture-only")

    def upload(self, data):
        path = self.transfer / "A5/file.bin"
        path.parent.mkdir()
        path.write_bytes(data)
        return path

    def test_complete_upload_passes_and_preserves_bytes(self):
        path = self.upload(b"abc")
        result = gate.wait_upload(self.expected(), self.transfer, self.receipts, 10)
        self.assertTrue(result["passed"])
        self.assertEqual(path.read_bytes(), b"abc")
        self.assertTrue((self.receipts / "UPLOAD_VERIFIED.json").exists())

    def test_partial_file_is_never_accepted(self):
        path = self.upload(b"ab")
        with self.assertRaises(TimeoutError):
            gate.wait_upload(self.expected(), self.transfer, self.receipts, 0)
        self.assertEqual(path.read_bytes(), b"ab")
        self.assertFalse((self.receipts / "UPLOAD_VERIFIED.json").exists())

    def test_complete_size_with_corrupt_bytes_is_rejected(self):
        path = self.upload(b"bad")
        with self.assertRaisesRegex(ValueError, "SHA256 differs"):
            gate.wait_upload(self.expected(), self.transfer, self.receipts, 10)
        self.assertEqual(path.read_bytes(), b"bad")
        self.assertFalse((self.receipts / "UPLOAD_VERIFIED.json").exists())

    def test_manifest_path_cannot_escape_transfer_root(self):
        value = self.expected()
        value["files"][0]["path"] = "../outside"
        with self.assertRaisesRegex(ValueError, "Unsafe expected path"):
            gate.wait_upload(value, self.transfer, self.receipts, 10)


if __name__ == "__main__":
    unittest.main()
