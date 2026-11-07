"""Verify Linux asset copies and native RECORD entries using stdlib only."""
import base64
import csv
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    raw = json.loads((PHASE / "LINUX_OBSERVATION.json").read_text(encoding="utf-8"))
    extra = json.loads((PHASE / "LINUX_SUPPLEMENT.json").read_text(encoding="utf-8"))
    unique = {}
    build = json.loads((PHASE / "BUILD_EVIDENCE.json").read_text(encoding="utf-8"))
    script = json.loads((PHASE / "BUILD_SCRIPT_EVIDENCE.json").read_text(encoding="utf-8"))
    for row in raw["preserved_files"] + extra["installed_artifacts"] + build["files"] + script["files"]:
        target = PHASE / row["copy"]
        assert target.is_relative_to(PHASE) and target.stat().st_size == row["bytes"] and sha(target) == row["sha256"], target
        if row["copy"] in unique:
            assert unique[row["copy"]]["sha256"] == row["sha256"]
        unique[row["copy"]] = row
    expected_claims = {r["recorded_path"]: r["observed_sha256"] for r in raw["claims"]}
    for source, digest in expected_claims.items():
        candidates = [r for r in unique.values() if r["source"] == source and "/historical-claims/" in "/" + r["copy"]]
        assert len(candidates) == 1 and candidates[0]["sha256"] == digest, source
    record_by_source = {}
    site = "/root/miniconda3/envs/rap-inference/lib/python3.10/site-packages/"
    for name in ("pytorch3d-0.7.9.dist-info", "torch_cluster-1.6.3+pt27cu128.dist-info"):
        path = PHASE / "linux-preservation/distribution-metadata" / site.lstrip("/") / name / "RECORD"
        assert path.is_file(), path
        for filename, value, size in csv.reader(path.read_text(encoding="utf-8").splitlines()):
            if value.startswith("sha256="):
                encoded = value[7:]
                record_by_source[site + filename] = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()
    artifacts = []
    for row in extra["installed_artifacts"]:
        expected = record_by_source.get(row["source"])
        assert expected == row["sha256"], row["source"]
        artifacts.append({"source": row["source"], "sha256": row["sha256"], "RECORD_match": True, "native_binary": row["source"].endswith(".so")})
    result = {"files": list(unique.values()), "unique_files": len(unique), "total_bytes": sum(r["bytes"] for r in unique.values()),
              "historical_claim_paths_preserved": len(expected_claims), "installed_artifacts_RECORD_verified": artifacts,
              "upstream_source_or_full_environment_provenance_certified": False, "full_environment_package_created": False,
              "torch_wheel_in_WSL_only": extra["wheel_inventory"]}
    (PHASE / "LINUX_PRESERVATION_MANIFEST.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files_verified": len(unique), "bytes": result["total_bytes"], "installed_artifacts_RECORD_verified": len(artifacts),
                      "native_binaries_RECORD_verified": sum(r["native_binary"] for r in artifacts)}))


if __name__ == "__main__":
    main()
