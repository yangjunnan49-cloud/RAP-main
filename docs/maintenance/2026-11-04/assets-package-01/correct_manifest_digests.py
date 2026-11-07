"""Correct Windows text-newline digest declarations without changing payload bytes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    package = Path(load(PHASE / "BASELINE.json")["package_destination"])
    reference = load(PHASE / "PACKAGE_REFERENCE.json")
    delivery = load(package / "DELIVERY_INDEX.json")
    check_before = {"package_manifest_sha256": sha(package / "PACKAGE.json"),
                    "delivery_index_sha256": sha(package / "DELIVERY_INDEX.json")}
    assert reference["delivery_index_sha256"] == check_before["delivery_index_sha256"]
    folder = PHASE / "attempt02"
    for name in ("BUNDLES.jsonl", "DELIVERY_INDEX.json"):
        target = folder / ("package-" + name)
        assert not target.exists()
        shutil.copyfile(package / ("metadata/" + name if name == "BUNDLES.jsonl" else name), target)
    units = [json.loads(line) for line in (PHASE / "BUNDLES.jsonl").read_text(encoding="utf-8").splitlines()]
    corrected = []
    for unit in units:
        member = PHASE / unit["member_manifest"]
        raw = member.read_bytes()
        assert sha(member) == sha(package / "metadata" / unit["member_manifest"])
        declared = unit["member_manifest_sha256"]
        assert declared == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        actual = hashlib.sha256(raw).hexdigest()
        if declared != actual:
            corrected.append({"id": unit["id"], "path": unit["member_manifest"], "before_declared_sha256": declared, "actual_sha256": actual})
        unit["member_manifest_sha256"] = actual
    assert len(corrected) == 517
    target = PHASE / "BUNDLES.jsonl"
    target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in units), encoding="utf-8")
    (package / "metadata/BUNDLES.jsonl").write_bytes(target.read_bytes())
    for item in delivery["extra_control_files"]:
        if item["path"] == "metadata/BUNDLES.jsonl":
            item["bytes"] = target.stat().st_size
            item["sha256"] = sha(target)
        else:
            assert sha(package / item["path"]) == item["sha256"]
    delivery["finalized_after_windows_member_digest_correction_utc"] = datetime.now(timezone.utc).isoformat()
    (package / "DELIVERY_INDEX.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reference["delivery_index_sha256"] = sha(package / "DELIVERY_INDEX.json")
    reference["member_manifest_digest_corrections"] = 517
    (PHASE / "PACKAGE_REFERENCE.json").write_text(json.dumps(reference, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert sha(package / "PACKAGE.json") == check_before["package_manifest_sha256"] == reference["package_manifest_sha256"]
    receipt = {"observed_utc": datetime.now(timezone.utc).isoformat(), "failed_check": "Bundle member manifest changed",
               "cause": "Digest used pre-write LF text while Windows write_text stored CRLF bytes",
               "failed_verifier_exit_code": 1, "corrected_member_manifest_digest_declarations": corrected,
               "member_manifest_and_source_or_tar_payload_bytes_changed": False,
               "package_manifest_and_full_payload_readback_receipt_remain_valid": True,
               "before": check_before, "after_delivery_index_sha256": reference["delivery_index_sha256"],
               "original_evidence": "attempt02", "generator_corrected_without_rerunning_inventory": True}
    (PHASE / "VALIDATION_FAILURE_02.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"corrected_declarations": len(corrected), "core_package_unchanged": True,
                      "delivery_index_sha256": reference["delivery_index_sha256"]}))


if __name__ == "__main__":
    main()
