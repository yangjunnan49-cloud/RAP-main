"""Cross-check the byte-verified base, catalogs, current authority and old seals."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A1 = REPO / "docs/maintenance/2026-11-03/migration-audit-01"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def file_record(path, record):
    check(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], "Changed file: " + str(path))


def key(row):
    return row["root"], row["path"]


def run(name, argv):
    result = subprocess.run(argv, cwd=REPO / "docs", env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    folder = PHASE / "validation"
    folder.mkdir(exist_ok=True)
    for stream in ("stdout", "stderr"):
        (folder / (name + "." + stream + ".txt")).write_text(getattr(result, stream), encoding="utf-8")
    check(result.returncode == 0, name + ": " + result.stderr[-1800:])
    return {"name": name, "exit_code": result.returncode,
            "stdout_sha256": sha(folder / (name + ".stdout.txt")), "stderr_sha256": sha(folder / (name + ".stderr.txt"))}


def main():
    baseline = load(PHASE / "BASELINE.json")
    roots = {name: Path(value) for name, value in baseline["source_roots"].items()}
    package = Path(baseline["package_destination"])
    before = {key(r): r for r in baseline["backups"]}
    previous = load(REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json")
    check(len(before) == len(previous["current_files"]) == 63, "Wrong authority scope")
    for r in previous["current_files"]:
        check(before[key(r)]["sha256"] == r["sha256"], "A4 authority chain gap")
        file_record(PHASE / before[key(r)]["backup"], r)
    proof = load(PHASE / "AUTHORITY_PROOF.json")
    authority = {key(r): r for r in proof["current_files"]}
    check(len(authority) == 68 and proof["historical_scientific_claims_superseded"] is False, "Wrong current authority")
    for r in authority.values():
        file_record(roots[r["root"]] / r["path"], r)
    print("63 backups and 68 current authority files passed", flush=True)

    meta = load(package / "PACKAGE.json")
    reference = load(PHASE / "PACKAGE_REFERENCE.json")
    verified = load(PHASE / "ARCHIVE_VERIFY.json")
    delivery = load(package / "DELIVERY_INDEX.json")
    check(meta["complete"] and verified["passed"], "Archive not complete and readback-verified")
    check(sha(package / "PACKAGE.json") == reference["package_manifest_sha256"] == verified["package_manifest_sha256"] == delivery["package_manifest"]["sha256"], "Package binding differs")
    check(sha(package / "DELIVERY_INDEX.json") == reference["delivery_index_sha256"], "Delivery index binding differs")
    for name, digest in meta["control_sha256"].items():
        check(sha(package / name) == sha(PHASE / name) == digest, "Core control changed: " + name)
    for name, field in (("OBJECTS.jsonl", "objects_manifest_sha256"), ("SOURCE_BYTE_CHECKS.jsonl", "source_byte_checks_sha256")):
        check(sha(package / name) == meta[field] == reference[field], "Object/check coverage binding differs")
    for r in delivery["extra_control_files"]:
        file_record(package / r["path"], r)
    tool = REPO / "scripts/migration/content_bundle.py"
    check(sha(tool) == sha(PHASE / "updates/scripts/migration/content_bundle.py") == sha(package / "recovery_tool.py") == reference["packager_source_sha256"] == verified["verification_tool_sha256"], "Tool byte succession differs")
    check(not list(package.glob("*.partial")) and not (package / "BUILD_FAILURE.json").exists(), "Incomplete archive artifacts")
    volumes = {r["name"]: r for r in meta["volumes"]}
    check(len(volumes) == verified["volumes_verified"] == 30, "Volume coverage differs")
    check(meta["volumes"] == reference["volumes"] == rows(package / "COMPLETED_VOLUMES.jsonl"), "Volume digest list differs")
    observed_time = datetime.fromisoformat(verified["observed_utc"]).timestamp()
    for name, r in volumes.items():
        value = (package / name).stat()
        check(value.st_size == r["bytes"] <= 4 * 1024**3 and value.st_mtime <= observed_time, "Volume metadata changed after readback")
    check(sum(r["bytes"] for r in volumes.values()) == reference["archive_volume_bytes"] == 125075722240, "Tar size differs")
    source = {key(r): r for r in rows(PHASE / "SOURCE_FILES.jsonl")}
    checks = rows(package / "SOURCE_BYTE_CHECKS.jsonl")
    fresh = {key(r): r for r in checks}
    objects = {r["sha256"]: r for r in rows(package / "OBJECTS.jsonl")}
    check(len(source) == len(checks) == len(fresh) == meta["source_files_fresh_byte_verified"] == verified["source_files"] == 111629, "Source byte check coverage differs")
    check(set(source) == set(fresh), "Source identity coverage differs")
    for identity, r in source.items():
        c = fresh[identity]
        check(c["sha256"] == r["sha256"] and c["bytes"] == r["bytes"] and c["fresh_raw_byte_match"], "Source raw-byte receipt mismatch")
    check(len(objects) == verified["unique_objects_verified"] == meta["unique_objects"] == 98854, "Object count differs")
    check(set(objects) == {r["sha256"] for r in source.values()}, "Object identity coverage differs")
    check(sum(r["bytes"] for r in source.values()) == meta["logical_bytes"] == 134910234709, "Logical byte count differs")
    check(sum(r["bytes"] for r in objects.values()) == meta["unique_payload_bytes"] == 124999364971, "Payload byte count differs")
    check(sum(r["stored_new_object"] for r in checks) == len(objects), "Stored object deduplication count differs")
    for digest, r in objects.items():
        check(r["member"] == "objects/" + digest and r["volume"] in volumes, "Unexpected object member")
    print("Package core/extra controls and full source/readback receipt chain passed", flush=True)

    units = rows(PHASE / "BUNDLES.jsonl")
    check(len(units) == 517 and sha(PHASE / "BUNDLES.jsonl") == sha(package / "metadata/BUNDLES.jsonl"), "Bundle catalog differs")
    owned = {}
    for unit in units:
        path = PHASE / unit["member_manifest"]
        check(sha(path) == unit["member_manifest_sha256"] == sha(package / "metadata" / unit["member_manifest"]), "Bundle member manifest changed")
        members = rows(path)
        check(len(members) == unit["files"] and sum(r["bytes"] for r in members) == unit["logical_bytes"], "Bundle count differs")
        for r in members:
            identity = tuple(r["asset"].split(":", 1))
            check(identity in source and identity not in owned, "Duplicate or unknown bundle member")
            check(r["sha256"] == source[identity]["sha256"] and r["bytes"] == source[identity]["bytes"], "Member identity differs")
            owned[identity] = unit["id"]
        ids = {r["sha256"] for r in members}
        check(unit["package_volumes"] == sorted({objects[d]["volume"] for d in ids}), "Required bundle volumes differ")
        check(unit["unique_referenced_objects"] == len(ids) and unit["unique_referenced_payload_bytes"] == sum(objects[d]["bytes"] for d in ids), "Unique referenced byte count differs")
    check(set(owned) == set(source), "Unowned source files")
    membership = rows(PHASE / "ASSET_MEMBERSHIP.jsonl")
    check(len(membership) == len(source), "Membership coverage differs")
    for r in membership:
        root, path = r["asset"].split(":", 1)
        check(owned[(root, path)] == r["primary_bundle_id"] and source[(root, path)]["sha256"] == r["sha256"], "Membership join differs")
    opaque_source = {k for k, r in source.items() if r["opaque_experiment"]}
    opaque_units = {u["id"] for u in units if u["opaque_metadata_only"]}
    opaque_owned = {k for k, bundle in owned.items() if bundle in opaque_units}
    check(opaque_source <= opaque_owned, "PGC1 opaque scope lost")
    summary = load(PHASE / "CATALOG_SUMMARY.json")
    check(summary["unowned_files"] == 0 and summary["zero_byte_ordinary_files_retained"] == sum(r["bytes"] == 0 for r in source.values()) == 358, "Empty or unowned file state differs")
    models = load(PHASE / "MODELS.json")["unique_models_or_weight_artifacts"]
    check(len(models) == 3 and sum(len(r["physical_aliases"]) for r in models) == 6, "Model alias coverage differs")
    for r in models:
        check(r["source_url_or_original_release"] is None and not r["metadata_content_inspected_with_pickle_or_torch"] and not r["training_resume_state_certified"], "Model provenance/resume state overstated")
        for identity in r["physical_aliases"]:
            root, path = identity.split(":", 1)
            check(source[(root, path)]["sha256"] == r["sha256"], "Model alias byte identity differs")
    data = load(PHASE / "DATASETS.json")
    sequence = data["odometry_format_collections"]
    check(len(sequence) == 45 and all(r["source_url"] is None and not r["training_validation_test_membership_admitted"] and not r["raw_vs_corrected_coordinate_or_physical_reference_newly_authenticated"] for r in sequence), "Dataset provenance/admission overstated")
    poss = [r for r in sequence if r["id"].startswith("rap-slam:data/poss/")]
    check(len(poss) == 1 and poss[0]["observed_cloud_files"] == 4170 and poss[0]["observed_frame_intervals_inclusive"] == [[3850, 5268], [6750, 9500]], "POSS coverage differs")
    check(data["oxford_spires"]["ordinary_files"] == 5 and data["oxford_spires"]["pcd_files"] == 0 and len(data["datasets_part2"]["files"]) == 4, "Partial/unclassified coverage differs")
    text_reads = load(PHASE / "DATA_TEXT_READS.json")
    check(len(text_reads["reads"]) == 68 and not text_reads["PGC1_partial_results_semantically_read"] and text_reads["model_or_numpy_data_loads"] == 0, "Text read boundary differs")
    claims = load(PHASE / "SOURCE_CLAIMS.json")
    check(not claims["new_downloads_or_source_authentication"] and not claims["PGC1_or_raw_OXTS_route_resumed"], "Provenance/resume boundary differs")
    restore = load(PHASE / "RESTORE_CHECKS.json")
    check(restore["passed"] and sum(r["restored_regular_files"] for r in restore["cases"]) == 18 and sum(r["bytes"] for r in restore["cases"]) == 690123401, "Restore coverage differs")
    check(all(r["all_restored_bytes_sha256_matched"] for r in restore["cases"]) and restore["generated_successful_test_copies_cleaned"] and not restore["original_assets_deleted_or_modified"] and not restore["model_or_result_array_loading_performed"], "Restore boundary differs")
    link_rows = load(PHASE / "SOURCE_LINKS_RAW.json")
    check(len(link_rows) == 27 and all(r["A5_raw_buffer_rechecked"] and r["A5_raw_sha256"] == r["raw_sha256"] and not r["followed"] for r in link_rows), "Native link preservation differs")
    check(len(rows(PHASE / "SOURCE_DIRECTORIES.jsonl")) == 5141 and len(rows(PHASE / "SOURCE_LINKS.jsonl")) == 27, "Directory/link coverage differs")
    print("517 logical bundles, model/data/source holds and real restore receipts passed", flush=True)

    old_code = {key(r): r for r in rows(PHASE / "before/rap-main/docs/code/ENTRYPOINTS.jsonl")}
    code = rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    changed = [key(r) for r in code if key(r) in old_code and r["sha256"] != old_code[key(r)]["sha256"]]
    check(changed == [("rap-main", "scripts/maintenance/index_code_entries.py")] and len(code) == 904, "Unexpected source change")
    check(sum(r["syntax_error"] is not None for r in code) == 1, "New code syntax error")
    index_path = "scripts/maintenance/index_code_entries.py"
    old = (PHASE / "before/rap-main" / index_path).read_text(encoding="utf-8")
    new = (REPO / index_path).read_text(encoding="utf-8")
    addition = '    if root == "rap-main" and path.startswith("scripts/migration/"):\n        return "current_migration_verification", None\n'
    check(new.count(addition) == 1 and ast.dump(ast.parse(new.replace(addition, ""))) == ast.dump(ast.parse(old)), "Unexpected maintenance classifier change")
    for r in code:
        file_record(roots[r["root"]] / r["path"], r)
    unit = run("content-bundle", [sys.executable, "-I", "-B", str(PHASE / "test_content_bundle.py")])
    check("Ran 7 tests" in (PHASE / "validation/content-bundle.stderr.txt").read_text(encoding="utf-8"), "Unexpected unit test count")
    run("code-index", [sys.executable, "-I", "-B", str(REPO / index_path), "--check"])
    state = load(REPO / "docs/CURRENT_STATE.json")
    old_state = load(PHASE / "before/rap-main/docs/CURRENT_STATE.json")
    check(state["research"] == old_state["research"] and state["next_step"]["stage"] == "A6", "Research/stage state changed")
    for name, value in old_state["preservation_holds"].items():
        check(state["preservation_holds"][name] == value, "Prior hold changed: " + name)
    check(state["migration"]["A5"] == "COMPLETE_WINDOWS_BASE_CONTENT_PACKAGE_WITH_PROVENANCE_AND_A7_HOLDS" and not state["migration"]["server_migration_complete"], "Migration status overstated")
    spec = importlib.util.spec_from_file_location("state_renderer", REPO / "scripts/maintenance/render_current_state.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    check(renderer.render(state) == (REPO / "docs/CURRENT_STATE.md").read_text(encoding="utf-8"), "State renderer differs")
    links, deferred = 0, []
    documents = [roots[r["root"]] / r["path"] for r in authority.values() if r["path"].endswith(".md") and "/evidence/" not in r["path"]]
    documents += [PHASE / "REPORT_CN.md", PHASE / "AUTHORITY.md"]
    for document in documents:
        for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", document.read_text(encoding="utf-8")):
            target = unquote(match.group(1).strip().strip("<>").split("#")[0])
            if not target or re.match(r"^[a-z]+://|^mailto:", target):
                continue
            resolved = (document.parent / target).resolve()
            if resolved == PHASE / "CHECKS.json":
                deferred.append(resolved)
            else:
                check(resolved.exists(), "Broken current link: " + str(document) + " -> " + target)
            links += 1
    for root in ("rap-main", "rap-slam", "workspace-root"):
        check((roots[root] / "AGENTS.md").stat().st_size <= (16384 if root == "rap-main" else 8192), "AGENTS too large")
    print("Production source preservation, 7 tests, 904 code roles and current navigation passed", flush=True)

    # Full source bytes and tar payloads were freshly read above in the build/readback
    # receipts. Avoid a third 125GB read; now check post-freeze source metadata and
    # reconcile old seals against exactly those byte-verified source identities.
    allowed_changes = {k for k, r in authority.items() if k in source and r["sha256"] != source[k]["sha256"]}
    post_freeze_changes = []
    for identity, r in source.items():
        path = roots[r["root"]] / r["path"]
        stat = path.lstat()
        check(not (getattr(stat, "st_file_attributes", 0) & 0x400) and path.is_file(), "Source type changed")
        if identity in allowed_changes:
            check(sha(path) == authority[identity]["sha256"], "Unregistered current document bytes")
            post_freeze_changes.append(r["root"] + ":" + r["path"])
        else:
            check(stat.st_size == r["bytes"] and stat.st_mtime_ns == r["mtime_ns"] and getattr(stat, "st_file_attributes", 0) == r["windows_attributes"], "Post-freeze metadata changed: " + str(identity))
    for r in rows(PHASE / "SOURCE_DIRECTORIES.jsonl"):
        check((roots[r["root"]] / r["path"]).is_dir(), "Frozen directory missing")
    prior = {}
    phase_names = [("2026-11-03", "migration-preflight-01"), ("2026-11-03", "migration-audit-01"), ("2026-11-03", "context-index-01"),
                   ("2026-11-04", "code-paths-01"), ("2026-11-04", "environment-readiness-01")]
    scientific_names = ["identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"]
    scientific = 0
    for date, name in phase_names + [("2026-11-03", n) for n in scientific_names]:
        folder = REPO / "docs/maintenance" / date / name
        relative = folder.relative_to(REPO).as_posix()
        seal_path = folder / "DELIVERY_SEAL.json"
        check(sha(seal_path) == source[("rap-main", relative + "/DELIVERY_SEAL.json")]["sha256"], "Prior seal changed")
        entries = load(seal_path)["files"]
        for r in entries:
            identity = ("rap-main", relative + "/" + r["path"])
            check(identity in source and source[identity]["sha256"] == r["sha256"] and source[identity]["bytes"] == r["bytes"], "Prior sealed source differs")
        if name in scientific_names:
            scientific += len(entries)
        else:
            prior[name] = len(entries)
    check(scientific == 2047, "Scientific seal entry coverage differs")
    git = [r for r in source.values() if r["path"].startswith(".git/")]
    original = {key(r): r for r in rows(A1 / "HASHES.jsonl")}
    check(len(git) == 3982 and all(r["sha256"] == original[key(r)]["sha256"] for r in git), "Original Git bytes differ")
    for root in ("rap-main", "rap-slam"):
        git_path = roots[root] / ".git"
        previous_git = load(A1 / "git" / root / "STATE.json")
        ref = (git_path / "HEAD").read_text().strip()
        check(ref == "ref: refs/heads/" + previous_git["branch"] and (git_path / ref[5:]).read_text().strip() == previous_git["head"], "Git HEAD/branch differs")
    failure = load(PHASE / "VALIDATION_FAILURE_01.json")
    check(failure and load(PHASE / "METADATA_ERRATA.json")["actual_user_instruction"] == "继续", "Failure/errata evidence missing")
    result = {"passed": True, "stage": "A5_BASE_PACKAGE_WITH_PROVENANCE_AND_A7_HOLDS", "observed_utc": datetime.now(timezone.utc).isoformat(),
              "before_files_sha256_verified": 63, "current_files_sha256_verified": 68, "code_role_records": 904,
              "other_baseline_code_config_sha256_unchanged": 902, "production_or_training_source_changed": False,
              "physical_source_files_fresh_byte_verified_in_build": 111629, "unique_objects_full_readback_verified": 98854,
              "tar_volumes_full_readback_verified": 30, "archive_verification_receipt_sha256": sha(PHASE / "ARCHIVE_VERIFY.json"),
              "full_tar_hash_read_repeated_in_this_final_cross_check": False, "volume_sizes_and_pre_receipt_write_times_rechecked": True,
              "logical_bytes": meta["logical_bytes"], "unique_payload_bytes": meta["unique_payload_bytes"], "tar_volume_bytes": reference["archive_volume_bytes"],
              "logical_bundles_with_exact_single_membership": 517, "zero_byte_ordinary_files_retained": 358,
              "native_reparse_buffers_verified": 27, "followed_links": 0, "source_directories_retained": 5141,
              "restored_regular_files_sha256_matched": 18, "restored_bytes": 690123401, "unit_tests_passed": 7, "unit_test_receipt": unit,
              "current_navigation_links_checked": links, "post_freeze_source_metadata_checked": len(source), "registered_current_document_changes_after_freeze": post_freeze_changes,
              "post_freeze_metadata_is_not_an_additional_full_source_hash_pass": True, "prior_phase_seals_bound_to_byte_verified_payload": prior,
              "scientific_seal_entries_bound_to_byte_verified_payload": scientific, "original_git_files_bound_to_byte_verified_payload_and_metadata_stable": len(git),
              "unique_model_digests": 3, "model_aliases": 6, "local_sequence_records": 45, "allowed_dataset_text_reads": 68,
              "source_authentication_reestablished": False, "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
              "PGC1_partial_accuracies_interpreted": False, "WSL_GPU_model_training_or_research_operations": 0,
              "software_install_download_deploy_or_external_transfer_performed": False, "original_assets_removed_or_moved": False,
              "full_target_link_permission_or_final_incremental_restore_validated": False, "A4_training_and_target_holds_retained": True,
              "next_stage": "A6", "server_migration_complete": False}
    (PHASE / "CHECKS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check(all(path.exists() for path in deferred), "Receipt link missing")
    display = dict(result)
    display["registered_current_document_changes_after_freeze"] = len(post_freeze_changes)
    print(json.dumps(display, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
