"""Verify A6 lineage/preparation and preservation; never execute historical builders."""
import ast
from collections import Counter
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
A5 = REPO / "docs/maintenance/2026-11-04/assets-package-01"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for b in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def file_record(path, row):
    check(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], "Changed bytes: " + str(path))


def key(row):
    return row["root"], row["path"]


def run(name, argv):
    r = subprocess.run(argv, cwd=REPO / "docs", env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    folder = PHASE / "validation"
    folder.mkdir(exist_ok=True)
    for stream in ("stdout", "stderr"):
        (folder / (name + "." + stream + ".txt")).write_bytes(getattr(r, stream).encode("utf-8"))
    check(r.returncode == 0, name + " failed: " + r.stderr[-1800:])
    return {"name": name, "exit_code": r.returncode, "stdout_sha256": sha(folder / (name + ".stdout.txt")), "stderr_sha256": sha(folder / (name + ".stderr.txt"))}


def main():
    baseline = load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["roots"].items()}
    before = {key(r): r for r in baseline["backups"]}
    previous = load(A5 / "AUTHORITY_PROOF.json")
    check(len(before) == len(previous["current_files"]) == 68, "Wrong before scope")
    for r in previous["current_files"]:
        check(before[key(r)]["sha256"] == r["sha256"], "A5 authority chain gap")
        file_record(PHASE / before[key(r)]["backup"], r)
    proof = load(PHASE / "AUTHORITY_PROOF.json")
    authority = {key(r): r for r in proof["current_files"]}
    check(len(authority) == 77 and not proof["historical_scientific_claims_superseded"], "Wrong A6 authority scope")
    for r in authority.values():
        file_record(roots[r["root"]] / r["path"], r)
    source = {key(r): r for r in rows(PHASE / "SOURCE_FILES.jsonl")}
    check(len(source) == 1975 and sum(r["bytes"] for r in source.values()) == 2902199121, "Wrong source scope")
    for r in source.values():
        check(r["matches_A5_base"] and r["sha256"] == r["A5_frozen_sha256"], "A6 source not matched to A5")
        file_record(roots[r["root"]] / r["path"], r)
    for r in load(PHASE / "LINKS.json"):
        value = (roots[r["root"]] / r["path"]).lstat()
        check(value.st_mtime_ns == r["mtime_ns"] and getattr(value, "st_file_attributes", 0) == r["windows_attributes"], "Source link metadata changed")
    check(len(load(PHASE / "LINKS.json")) == 20, "Link scope differs")
    print("68 before, 77 current authority and all 1,975 original asset hashes passed", flush=True)

    catalog = load(PHASE / "CATALOG.json")
    files = rows(PHASE / "FILES.jsonl")
    check(len(catalog["families"]) == 10 and len(files) == len({key(r) for r in files}) == 1975, "Catalog identity coverage differs")
    check({key(r) for r in files} == set(source), "Unowned assets")
    families = {r["id"]: r for r in catalog["families"]}
    for r in files:
        check(r["family"] in families and r["sha256"] == source[key(r)]["sha256"], "Catalog member differs")
    for f in families.values():
        members = [r for r in files if r["family"] == f["id"]]
        check(len(members) == f["files"] and sum(r["bytes"] for r in members) == f["bytes"], "Family count differs")
        check(not f["meeting_actually_held_certified"] and not f["new_scientific_or_training_admission"], "Meeting/science certification overstated")
    for name in ("CATALOG.json", "FILES.jsonl"):
        check(sha(PHASE / name) == sha(REPO / "docs/meetings" / name), "Published catalog differs")
    structure = load(PHASE / "ARTIFACT_STRUCTURE.json")
    check(len(structure) == 46 and Counter(r["format"] for r in structure) == {"pptx": 17, "docx": 8, "pdf": 21}, "Office/PDF inspection coverage differs")
    check(all(r.get("zip_CRC_passed", True) and not r["new_native_or_visual_QA_performed"] for r in structure), "Artifact QA claim differs")
    delivered = load(PHASE / "DELIVERY_IDENTITY_CHECKS.json")
    check(len(delivered) == 6 and all(r["matches"] and r["actual_sha256"] == r["expected_sha256"] for r in delivered), "Delivery identity differs")
    for r in delivered:
        root, relative = r["asset"].split(":", 1)
        check(sha(roots[root] / relative) == r["expected_sha256"], "Delivered artifact changed")
    decks = load(PHASE / "EDITABLE_DECKS.json")
    check(len(decks) == 4 and sum(r["active_page_count"] for r in decks) == 47, "Editable source coverage differs")
    check(all(rr["exists"] for r in decks for rr in r["image_references"]), "Missing active source image")
    media = load(PHASE / "FIGURE_BYTE_LINKS.json")
    check(len(media) == 60 and sum(bool(r["source_file_byte_aliases"]) for r in media) == 44 and all(not r["scientific_or_pixel_semantics_certified"] for r in media), "Figure byte-role state differs")
    bindings = load(PHASE / "HISTORICAL_SOURCE_BINDINGS.json")
    check(len(bindings) == 59 and Counter(r["state"] for r in bindings) == {"EXACT_ORIGINAL_PATH": 57, "EXACT_BYTE_ALIAS_AVAILABLE": 1, "UNRECOVERED_EXACT_BYTES": 1}, "Historical source gap lost")
    differences = load(PHASE / "VERSION_DISCREPANCIES.json")
    check(differences[0]["observed_active_pptx_slides"] == 9 and not differences[1]["borrow_prefix_matches"] and differences[1]["current_export_slides"] == 4 and differences[1]["editable_source_active_pages"] == 5, "Version discrepancy hidden")
    check(len(load(PHASE / "AUTHORING_SCRIPTS.json")) == 64 and all(not r["executed_in_A6"] for r in load(PHASE / "AUTHORING_SCRIPTS.json")), "Historical builder unexpectedly executed")
    portable = load(PHASE / "PORTABLE_PREPARATION.json")
    check(portable["files_selected"] == 72 and portable["bytes_selected"] == 17121135 and portable["node_syntax_check_passed"] and portable["vendored_module_import_check_passed"], "Portable preparation differs")
    check(not portable["builder_office_export_or_render_executed"] and not portable["new_DOCX_or_PPTX_created"] and not portable["personal_cache_path_used_by_prepared_notes_recipe"], "Preparation boundary overstated")
    destination = PHASE / "portable/meeting-20261101"
    for r in rows(destination / "SOURCE_MANIFEST.jsonl"):
        check(r["role"] != "scientific_or_data_history_opaque_preserved", "Opaque scientific data in edit copy")
        file_record(destination / r["root"] / r["path"], r)
    normalized = destination / "authoring/build_notes.mjs"
    check(sha(normalized) == portable["normalized_recipe_sha256"], "Normalized recipe changed")
    original = roots["rap-main"] / "working files/weekly_20261101/create_weekly_script.js"
    check(normalized.read_text(encoding="utf-8").split("const palette =", 1)[1] == original.read_text(encoding="utf-8").split("const palette =", 1)[1], "Notes body changed")
    check(sha(destination / "authoring/vendor/docx.cjs") == portable["vendored_module_sha256"], "Vendored module changed")
    print("Catalog ownership, final identities, version/source gaps, figures and portable copies passed", flush=True)

    old_code = {key(r): r for r in rows(PHASE / "before/rap-main/docs/code/ENTRYPOINTS.jsonl")}
    code = rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    changed = [key(r) for r in code if key(r) in old_code and r["sha256"] != old_code[key(r)]["sha256"]]
    added = [key(r) for r in code if key(r) not in old_code]
    check(len(old_code) == 904 and len(code) == 905 and changed == [("rap-main", "scripts/maintenance/index_code_entries.py"), ("rap-main", "scripts/maintenance/render_current_state.py")] and added == [("rap-main", "scripts/meetings/materials.py")], "Unexpected source change")
    check(sum(r["syntax_error"] is not None for r in code) == 1, "New indexed syntax error")
    index_path = "scripts/maintenance/index_code_entries.py"
    old = (PHASE / "before/rap-main" / index_path).read_text(encoding="utf-8")
    new = (REPO / index_path).read_text(encoding="utf-8")
    addition = '    if root == "rap-main" and path.startswith("scripts/meetings/"):\n        return "current_meeting_maintenance", None\n'
    check(new.count(addition) == 1 and ast.dump(ast.parse(new.replace(addition, ""))) == ast.dump(ast.parse(old)), "Unexpected classifier change")
    old_render = (PHASE / "before/rap-main/scripts/maintenance/render_current_state.py").read_text(encoding="utf-8")
    new_render = (REPO / "scripts/maintenance/render_current_state.py").read_text(encoding="utf-8")
    old_line = '"- 工作区外动态引用闭包、raw/OXTS 来源认证、完整训练/恢复链和组会最终版本/制作链仍未完成。",'
    new_block = ('"- 工作区外动态引用闭包、raw/OXTS 来源认证、完整训练/恢复链仍未完成。",\n'
                 '                  ("- 组会/制作链已在 A6 审计；终稿版本差异、参考 PDF 原件和新原生导出验收保留，见组会总入口。"\n'
                 '                   if holds.get("meeting_final_versions_and_authoring_chain_reviewed", False) else "- 组会最终版本与制作链待 A6 核对。"),')
    check(old_render.count(old_line) == 1 and ast.dump(ast.parse(old_render.replace(old_line, new_block))) == ast.dump(ast.parse(new_render)), "Unexpected state renderer change")
    for r in code:
        file_record(roots[r["root"]] / r["path"], r)
    tests = run("materials-tests", [sys.executable, "-X", "utf8", "-I", "-B", str(PHASE / "test_materials.py")])
    check("Ran 6 tests" in (PHASE / "validation/materials-tests.stderr.txt").read_text(encoding="utf-8"), "Unexpected test count")
    run("code-index", [sys.executable, "-X", "utf8", "-I", "-B", str(REPO / index_path), "--check"])
    run("materials-list", [sys.executable, "-X", "utf8", "-I", "-B", str(REPO / "scripts/meetings/materials.py"), "list"])
    run("materials-check", [sys.executable, "-X", "utf8", "-I", "-B", str(REPO / "scripts/meetings/materials.py"), "check", "--family", "meeting-20261018"])
    no_output = PHASE / "validation/plan-only-must-not-exist"
    check(not no_output.exists(), "Plan fixture already exists")
    run("materials-plan", [sys.executable, "-X", "utf8", "-I", "-B", str(REPO / "scripts/meetings/materials.py"), "prepare", "--family", "meeting-20261101", "--destination", str(no_output)])
    check(not no_output.exists(), "Default preparation created output")
    state = load(REPO / "docs/CURRENT_STATE.json")
    old_state = load(PHASE / "before/rap-main/docs/CURRENT_STATE.json")
    check(state["research"] == old_state["research"] and state["next_step"]["stage"] == "A7" and not state["migration"]["server_migration_complete"], "Research/stage state differs")
    for name, value in old_state["preservation_holds"].items():
        check(state["preservation_holds"][name] == (True if name == "meeting_final_versions_and_authoring_chain_reviewed" else value), "Prior hold changed: " + name)
    check(not state["preservation_holds"]["all_meeting_final_variants_and_new_native_exports_confirmed"] and not state["preservation_holds"]["historical_meeting_reference_PDF_exact_bytes_recovered"], "Meeting holds lost")
    spec = importlib.util.spec_from_file_location("a6_state_renderer", REPO / "scripts/maintenance/render_current_state.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    check(renderer.render(state) == (REPO / "docs/CURRENT_STATE.md").read_text(encoding="utf-8"), "State rendering differs")
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
                check(resolved.exists(), "Broken link: " + str(document) + " -> " + target)
            links += 1
    for root in ("rap-main", "rap-slam", "workspace-root"):
        check((roots[root] / "AGENTS.md").stat().st_size <= (16384 if root == "rap-main" else 8192), "AGENTS too large")
    print("905 source roles, 6 tests, CLI contracts, current research state and navigation passed", flush=True)

    check(sha(A5 / "DELIVERY_SEAL.json") == baseline["previous_seal_sha256"], "A5 seal changed")
    previous_seal = load(A5 / "DELIVERY_SEAL.json")
    for r in previous_seal["files"]:
        file_record(A5 / r["path"], r)
    reference = load(A5 / "PACKAGE_REFERENCE.json")
    package = Path(reference["package_directory"])
    check(sha(package / "PACKAGE.json") == reference["package_manifest_sha256"] and sha(package / "DELIVERY_INDEX.json") == reference["delivery_index_sha256"], "A5 package controls changed")
    meta = load(package / "PACKAGE.json")
    for name, digest in meta["control_sha256"].items():
        check(sha(package / name) == digest, "A5 package core control changed")
    for r in load(package / "DELIVERY_INDEX.json")["extra_control_files"]:
        file_record(package / r["path"], r)
    readback = load(A5 / "ARCHIVE_VERIFY.json")
    check(readback["passed"] and readback["unique_objects_verified"] == 98854, "A5 full-readback receipt invalid")
    for r in meta["volumes"]:
        stat = (package / r["name"]).stat()
        check(stat.st_size == r["bytes"] and stat.st_mtime <= datetime.fromisoformat(readback["observed_utc"]).timestamp(), "A5 volume metadata changed")
    a5_roots = {k: Path(v) for k, v in load(A5 / "BASELINE.json")["source_roots"].items()}
    a5_source = {key(r): r for r in rows(A5 / "SOURCE_FILES.jsonl")}
    git_observation = {key(r): r for r in load(PHASE / "GIT_METADATA_TIMESTAMP_OBSERVATION.json")["observed_differences"]}
    git_metadata_byte_checks = []
    for identity, r in a5_source.items():
        path = a5_roots[r["root"]] / r["path"]
        stat = path.lstat()
        check(not (getattr(stat, "st_file_attributes", 0) & 0x400) and path.is_file(), "A5 original file missing/type changed")
        if identity not in authority:
            same = stat.st_size == r["bytes"] and stat.st_mtime_ns == r["mtime_ns"] and getattr(stat, "st_file_attributes", 0) == r["windows_attributes"]
            if not same and r["path"].startswith(".git/"):
                observed = git_observation.get(identity)
                if observed and stat.st_mtime_ns == observed["after_mtime_ns"] and getattr(stat, "st_file_attributes", 0) == observed["after_attributes"] and stat.st_size == observed["bytes"]:
                    digest = observed["sha256"]
                else:
                    digest = sha(path)
                check(stat.st_size == r["bytes"] and digest == r["sha256"], "Frozen Git byte change: " + str(identity))
                git_metadata_byte_checks.append({"root": r["root"], "path": r["path"], "bytes": r["bytes"], "sha256": digest,
                                                "mtime_ns": stat.st_mtime_ns, "attributes": getattr(stat, "st_file_attributes", 0),
                                                "matched_original_byte_hash_despite_metadata_difference": True})
            else:
                check(same, "A5 original metadata changed: " + str(identity))
    (PHASE / "GIT_METADATA_FINAL_BYTE_CHECKS.json").write_bytes((json.dumps(git_metadata_byte_checks, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    scientific_count = 0
    for name in ("identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"):
        folder = REPO / "docs/maintenance/2026-11-03" / name
        relative = folder.relative_to(REPO).as_posix()
        check(sha(folder / "DELIVERY_SEAL.json") == a5_source[("rap-main", relative + "/DELIVERY_SEAL.json")]["sha256"], "Scientific seal changed")
        for r in load(folder / "DELIVERY_SEAL.json")["files"]:
            old = a5_source[("rap-main", relative + "/" + r["path"])]
            check(old["sha256"] == r["sha256"] and old["bytes"] == r["bytes"], "Scientific sealed byte chain mismatch")
            scientific_count += 1
    check(scientific_count == 2047, "Scientific seal scope differs")
    original_git = [r for r in a5_source.values() if r["path"].startswith(".git/")]
    check(len(original_git) == 4029, "Frozen Git coverage differs")
    for root in ("rap-main", "rap-slam"):
        for relative in (".git/HEAD", ".git/index"):
            check(sha(a5_roots[root] / relative) == a5_source[(root, relative)]["sha256"], "Git head/index changed")
        git_state = load(REPO / "docs/maintenance/2026-11-03/migration-audit-01/git" / root / "STATE.json")
        ref = (a5_roots[root] / ".git/HEAD").read_text().strip()
        check(ref == "ref: refs/heads/" + git_state["branch"] and (a5_roots[root] / ".git" / ref[5:]).read_text().strip() == git_state["head"], "Git branch/commit changed")
    additions = []
    for root in ("rap-main", "rap-slam"):
        for path in (a5_roots[root] / ".git").rglob("*"):
            if path.is_file():
                relative = path.relative_to(a5_roots[root]).as_posix()
                if (root, relative) not in a5_source:
                    additions.append({"root": root, "path": relative, "bytes": path.stat().st_size, "sha256": sha(path)})
    (PHASE / "GIT_METADATA_DELTA.json").write_bytes((json.dumps({"A5_frozen_git_files_preserved": 4029, "additional_current_files": additions, "origin_attributed": False,
          "git_commit_index_or_branch_mutated_by_A6": False, "final_current_metadata_to_be_included_in_A7": True}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    result = {"passed": True, "stage": "A6_LINEAGE_AND_PORTABLE_PREPARATION_WITH_VERSION_REFERENCE_AND_EXPORT_HOLDS",
              "observed_utc": datetime.now(timezone.utc).isoformat(), "before_files_sha256_verified": 68, "current_files_sha256_verified": 77,
              "meeting_report_source_files_fresh_sha256_verified": 1975, "source_bytes": 2902199121, "all_sources_match_A5_base": True,
              "source_links_metadata_checked_without_following": 20, "families": 10, "Office_PDF_files_inspected_read_only": 46,
              "historical_deliverable_hashes_matched": 6, "editable_decks": 4, "active_editable_pages": 47,
              "embedded_media_byte_relationships": 60, "relationships_with_exact_file_byte_alias": 44,
              "historical_source_bindings": 59, "original_path_matches": 57, "exact_byte_aliases": 1, "unrecovered_exact_reference_PDF": 1,
              "portable_files_sha256_verified": 72, "portable_bytes": 17121135, "native_document_or_pptd_build_export_visual_QA_validated": False,
              "portable_notes_syntax_and_module_import_passed": True, "historical_authoring_or_research_scripts_executed": 0,
              "code_role_records": 905, "old_code_config_unchanged_except_two_maintenance_sources": 902, "production_or_training_source_changed": False,
              "unit_tests_passed": 6, "unit_receipt": tests, "current_navigation_links_checked": links,
              "A5_seal_files_fresh_sha256_verified": len(previous_seal["files"]), "A5_package_manifest_and_extra_control_hashes_matched": True,
              "A5_full_tar_readback_receipt_bound_without_repeating_125GB_read": True, "A5_original_file_post_freeze_metadata_checked": len(a5_source),
              "scientific_seal_entries_bound_to_A5_byte_verified_payload_and_stable_metadata": scientific_count,
              "A5_git_files_bound_to_original_byte_hashes_and_metadata_rechecked": 4029,
              "git_metadata_differences_fresh_byte_verified_without_origin_attribution": len(git_metadata_byte_checks),
              "additional_current_git_metadata_files_observed_without_attribution": len(additions),
              "git_heads_branches_commits_and_indexes_unchanged": True, "research_state_unchanged": True,
              "PGC1_partial_results_semantically_read": False, "WSL_GPU_model_training_or_new_research_runs": 0,
              "install_download_deploy_or_external_transfer_performed": False, "original_assets_deleted_or_moved": False,
              "all_meeting_final_variants_confirmed": False, "historical_source_digest_gaps_retained": 5,
              "historical_AGENTS_version_gaps_retained": 1, "A4_training_target_and_A7_final_restore_holds_retained": True,
              "next_stage": "A7", "server_migration_complete": False}
    (PHASE / "CHECKS.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    check(all(p.exists() for p in deferred), "Receipt link missing")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
