"""Verify local project/control acceptance; final sealed-evidence checks follow sealing."""
import ast
from datetime import datetime, timezone
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


def main():
    spec = importlib.util.spec_from_file_location("a7_verified_delivery", REPO / "scripts/migration/delivery.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    def check(condition, message):
        if not condition:
            raise AssertionError(message)
    def file_record(path, row):
        path = tool.native_absolute(path)
        check(path.stat().st_size == row["bytes"] and tool.sha(path) == row["sha256"], "Changed file: " + str(path))
    baseline = tool.load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["source_roots"].items()}
    previous = tool.load(REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json")
    backups = {(r["root"], r["path"]): r for r in baseline["backups"]}
    check(len(previous["current_files"]) == len(backups) == 77, "Before authority scope differs")
    for row in previous["current_files"]:
        old = backups[(row["root"], row["path"])]
        check(old["sha256"] == row["sha256"], "A6 authority chain differs")
        file_record(PHASE / old["backup"], row)
    authority = tool.load(PHASE / "AUTHORITY_PROOF.json")["current_files"]
    check(len(authority) == 81, "Final authority scope differs")
    for row in authority:
        file_record(roots[row["root"]] / row["path"], row)
    snapshots = tool.load(PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json")
    check(len(snapshots) == 81 and {(r["root"], r["path"]): r["sha256"] for r in snapshots} == {(r["root"], r["path"]): r["sha256"] for r in authority}, "Snapshot authority binding differs")
    for row in snapshots:
        file_record(PHASE / row["snapshot"], row)
    package = Path(baseline["package"])
    project = tool.load(package / "PROJECT.json")
    project_restore = tool.load(PHASE / "PROJECT_RESTORE.json")
    base = tool.load(PHASE / "BASE_RESTORE.json")
    delta = tool.load(PHASE / "DELTA_RESTORE.json")
    check(base["passed"] and base["ordinary_files_restored"] == 111629 and base["unique_objects_and_volume_hashes_verified"] == 98854 and base["volumes_full_hash_verified"] == 30, "Base restore incomplete")
    check(delta["passed"] and delta["ordinary_files_restored"] == 1072 and delta["unique_objects_and_volume_hashes_verified"] == 833 and delta["volumes_full_hash_verified"] == 1, "Delta restore incomplete")
    fresh = project_restore["fresh_restored_tree_check"]
    check(project_restore["passed"] and fresh["passed"] and fresh["ordinary_files_freshly_rehashed"] == 112682 and fresh["bytes_freshly_rehashed"] == 135095691259, "Full restored-tree byte read missing")
    check(fresh["superseded_versions_freshly_rehashed"] == len(delta["superseded_base_versions_preserved"]) == 19, "Superseded base versions missing")
    check(tool.sha(package / "PROJECT.json") == project_restore["project_manifest_sha256"] == tool.load(PHASE / "PROJECT_PACKAGE.json")["project_manifest_sha256"], "Project manifest binding differs")
    tool.project_controls(package / "PROJECT.json")
    for layer in project["layers"]:
        directory = (package / layer["directory"]).resolve()
        check(tool.sha(directory / "PACKAGE.json") == layer["package_manifest_sha256"], "Layer changed after restore")
        meta = tool.load(directory / "PACKAGE.json")
        for row in meta["volumes"]:
            check((directory / row["name"]).stat().st_size == row["bytes"], "Layer volume size changed")
    workspace = Path(tool.load(PHASE / "RESTORE_DESTINATION.json")["directory"]) / "workspace"
    controls = tool.load(PHASE / "LOCAL_CONTROL_RESTORE.json")
    check(controls["passed"] and controls["current_control_count"] == 81, "Local control overlay incomplete")
    late_git = tool.load(PHASE / "LATE_GIT_SNAPSHOTS.json")
    for row in snapshots + late_git:
        file_record(tool.mapped(workspace, project["layout"], row), row)
    for row in delta["superseded_base_versions_preserved"] + controls["applied"]["superseded_versions_preserved"]:
        file_record(tool.native_absolute(workspace) / tool.safe_relative(row["path"]), row)
    print("77 before, 81 current controls; full base/delta restore and 135GB fresh tree check passed", flush=True)

    links = tool.load(PHASE / "POSIX_LINK_CHECKS.json")
    session = tool.load(PHASE / "WSL_LINK_SESSION.json")
    check(links["passed"] and links["internal_links_created_resolved_and_contained"] == 25 and links["external_runtime_junctions_not_recreated"] == 2, "Link acceptance differs")
    check(session["restored_initial_stopped_state"] and len([e for e in session["events"] if "--exec" in e["argv"]]) == 1, "WSL maintenance not bounded/restored")
    fixture = links["POSIX_fixture"]
    check(fixture["actual_delivery_permission_function_tested"] and fixture["script_mode"] == "0o755" and fixture["regular_mode"] == "0o644" and fixture["fixed_fixture_script_execution_exit"] == 0, "POSIX policy fixture failed")
    check(not fixture["restored_NTFS_tree_POSIX_modes_or_ACLs_certified"] and not links["target_Linux_server_permissions_GPU_environment_or_training_validated"], "Target permissions overstated")
    relocated = tool.load(PHASE / "RELOCATED_CHECKS.json")
    check(relocated["passed"] and len(relocated["cases"]) == 5 and all(not r["numerical_modules_loaded"] and r["required_paths_all_in_new_workspace"] for r in relocated["cases"]), "Relocated path contracts failed")
    check(len(relocated["restored_git_read_only_checks"]) == 2 and all(r["repository_root_is_restored_tree"] for r in relocated["restored_git_read_only_checks"]), "Restored Git context not relocatable")
    old_code = {(r["root"], r["path"]): r for r in tool.rows(PHASE / "before/rap-main/docs/code/ENTRYPOINTS.jsonl")}
    code = tool.rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    check(len(old_code) == 905 and len(code) == 906, "Code coverage differs")
    check([r for r in code if (r["root"], r["path"]) in old_code and r["sha256"] != old_code[(r["root"], r["path"])]["sha256"]] == [], "Existing source/config changed")
    for row in code:
        file_record(roots[row["root"]] / row["path"], row)
    check(sum(r["syntax_error"] is not None for r in code) == 1, "New code syntax error")
    check({r["id"] for r in code if r["default_dispatch_allowed"]} == {r["id"] for r in old_code.values() if r["default_dispatch_allowed"]}, "Default dispatch changed")
    old_ast = ast.parse((PHASE / "used/delivery-longpath.py").read_text(encoding="utf-8"))
    new_ast = ast.parse((REPO / "scripts/migration/delivery.py").read_text(encoding="utf-8"))
    def nodes(tree):
        return {n.name: ast.dump(n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    before_nodes, after_nodes = nodes(old_ast), nodes(new_ast)
    for name in ("safe_relative", "native_absolute", "mapped", "validate_rows", "HashReader", "layer_controls", "restore_layer", "check_files", "apply_links"):
        check(before_nodes[name] == after_nodes[name], "Executed restore core differs from published tool: " + name)
    check(tool.sha(PHASE / "used/delivery-longpath.py") == base["used_tool_sha256"], "Used tool binding differs")
    check(tool.sha(REPO / "scripts/migration/delivery.py") == tool.sha(PHASE / "updates/scripts/migration/delivery.py") == tool.sha(package / "tools/delivery.py"), "Published/offline tool mismatch")
    validation = PHASE / "validation"
    validation.mkdir(exist_ok=True)
    def run(name, argv):
        r = subprocess.run(argv, cwd=REPO / "docs", env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True, text=True, encoding="utf-8", timeout=60)
        for stream in ("stdout", "stderr"):
            (validation / (name + "." + stream + ".txt")).write_bytes(getattr(r, stream).encode("utf-8"))
        check(r.returncode == 0, name + " failed: " + r.stderr[-1500:])
        return r
    tested = run("delivery-tests", [sys.executable, "-X", "utf8", "-I", "-B", str(PHASE / "test_delivery.py")])
    check("Ran 9 tests" in tested.stderr, "Unexpected delivery test count")
    run("code-index", [sys.executable, "-X", "utf8", "-I", "-B", str(REPO / "scripts/maintenance/index_code_entries.py"), "--check"])
    print("Relative links, POSIX fixture, 5 path contracts, Git, 906 code roles and 9 tests passed", flush=True)

    state = tool.load(REPO / "docs/CURRENT_STATE.json")
    old_state = tool.load(PHASE / "before/rap-main/docs/CURRENT_STATE.json")
    check(state["research"] == old_state["research"] and not state["migration"]["server_selected"] and not state["migration"]["server_migration_complete"], "Research/server scope changed")
    for name, value in old_state["preservation_holds"].items():
        check(state["preservation_holds"][name] == value, "Prior hold changed: " + name)
    check(state["next_step"]["stage"] == "TARGET_SELECTION_AND_REMAINING_ACCEPTANCE" and not state["next_step"]["automatic_deploy_training_or_research_authorized"], "Unauthorized next action")
    renderer_spec = importlib.util.spec_from_file_location("final_state_renderer", REPO / "scripts/maintenance/render_current_state.py")
    renderer = importlib.util.module_from_spec(renderer_spec)
    renderer_spec.loader.exec_module(renderer)
    check(renderer.render(state) == (REPO / "docs/CURRENT_STATE.md").read_text(encoding="utf-8"), "State rendering differs")
    link_count, deferred = 0, []
    docs = [roots[r["root"]] / r["path"] for r in authority if r["path"].endswith(".md") and "/evidence/" not in r["path"]]
    docs += [PHASE / "REPORT_CN.md", PHASE / "AUTHORITY.md"]
    for document in docs:
        for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", document.read_text(encoding="utf-8")):
            target = unquote(match.group(1).strip().strip("<>").split("#")[0])
            if not target or re.match(r"^[a-z]+://|^mailto:", target):
                continue
            resolved = (document.parent / target).resolve()
            if resolved == PHASE / "CHECKS.json":
                deferred.append(resolved)
            else:
                check(resolved.exists(), "Broken current link: " + str(document) + " -> " + target)
            link_count += 1
    for root in ("rap-main", "rap-slam", "workspace-root"):
        check((roots[root] / "AGENTS.md").stat().st_size <= (16384 if root == "rap-main" else 8192), "AGENTS too large")
    frozen = {(r["root"], r["path"]): r for r in tool.rows(PHASE / "PROJECT_FILES.jsonl")}
    allowed = {(r["root"], r["path"]) for r in authority}
    metadata_checks, git_time_matches = 0, []
    for identity, row in frozen.items():
        path = tool.native_absolute(roots[row["root"]] / row["path"])
        stat = path.lstat()
        check(not (getattr(stat, "st_file_attributes", 0) & 0x400) and path.is_file(), "Original file missing/type changed")
        if identity not in allowed:
            same = stat.st_size == row["bytes"] and stat.st_mtime_ns == row["mtime_ns"]
            if not same and row["path"].startswith(".git/"):
                check(stat.st_size == row["bytes"] and tool.sha(path) == row["sha256"], "Original Git byte change")
                git_time_matches.append({"root": row["root"], "path": row["path"], "sha256": row["sha256"], "original_mtime_ns": row["mtime_ns"], "observed_mtime_ns": stat.st_mtime_ns})
            else:
                check(same, "Unregistered original metadata change: " + str(identity))
        metadata_checks += 1
    (PHASE / "FINAL_GIT_TIMESTAMP_BYTE_CHECKS.json").write_bytes((json.dumps(git_time_matches, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    prior = {}
    for date, name in (("2026-11-03", "migration-preflight-01"), ("2026-11-03", "migration-audit-01"), ("2026-11-03", "context-index-01"),
                       ("2026-11-04", "code-paths-01"), ("2026-11-04", "environment-readiness-01"), ("2026-11-04", "assets-package-01"), ("2026-11-04", "meeting-lineage-01")):
        folder = REPO / "docs/maintenance" / date / name
        relative = folder.relative_to(REPO).as_posix()
        check(tool.sha(folder / "DELIVERY_SEAL.json") == frozen[("rap-main", relative + "/DELIVERY_SEAL.json")]["sha256"], "Old phase seal changed")
        entries = tool.load(folder / "DELIVERY_SEAL.json")["files"]
        for r in entries:
            expected = frozen[("rap-main", relative + "/" + r["path"])]
            check(expected["sha256"] == r["sha256"] and expected["bytes"] == r["bytes"], "Old sealed source not in restored project")
        prior[name] = len(entries)
    scientific = 0
    for name in ("identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"):
        folder = REPO / "docs/maintenance/2026-11-03" / name
        relative = folder.relative_to(REPO).as_posix()
        check(tool.sha(folder / "DELIVERY_SEAL.json") == frozen[("rap-main", relative + "/DELIVERY_SEAL.json")]["sha256"], "Scientific seal changed")
        for r in tool.load(folder / "DELIVERY_SEAL.json")["files"]:
            expected = frozen[("rap-main", relative + "/" + r["path"])]
            check(expected["sha256"] == r["sha256"] and expected["bytes"] == r["bytes"], "Scientific sealed byte chain changed")
            scientific += 1
    check(scientific == 2047, "Scientific seal scope differs")
    # Reuse only the sealed native metadata-reader function, not the A1 audit driver.
    import base64
    import ctypes
    from ctypes import wintypes
    source_tree = ast.parse((REPO / "docs/maintenance/2026-11-03/migration-audit-01/audit_assets.py").read_text(encoding="utf-8"))
    node = next(n for n in source_tree.body if isinstance(n, ast.FunctionDef) and n.name == "reparse_data")
    namespace = {"ctypes": ctypes, "wintypes": wintypes, "Path": Path, "base64": base64, "hashlib": __import__("hashlib")}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "sealed_reparse_reader_only", "exec"), namespace)
    original_links = tool.load(REPO / "docs/maintenance/2026-11-04/assets-package-01/SOURCE_LINKS_RAW.json")
    for row in original_links:
        observed = namespace["reparse_data"](roots[row["root"]] / row["path"])
        check(observed["raw_sha256"] == row["raw_sha256"], "Original reparse buffer changed")
    result = {"passed": True, "stage": "A7_LOCAL_PROJECT_AND_CURRENT_CONTROL_ACCEPTANCE_WITH_TARGET_HOLDS", "client_local_date": "2026-11-05", "timezone": "Asia/Shanghai",
              "observed_utc": datetime.now(timezone.utc).isoformat(), "before_files_sha256_verified": 77, "current_authority_files_sha256_verified": 81,
              "base_files_restored": 111629, "base_unique_objects_and_volume_hashes_verified": 98854, "base_volumes_full_hash_verified": 30,
              "delta_files_restored_and_fresh_source_byte_checked": 1072, "delta_objects_verified": 833, "delta_volumes_full_hash_verified": 1,
              "full_project_files_fresh_post_restore_rehash": 112682, "full_project_bytes_fresh_post_restore_rehash": 135095691259,
              "superseded_base_versions_preserved_and_rehashed": 19, "superseded_current_control_versions_preserved": len(controls["applied"]["superseded_versions_preserved"]),
              "late_git_files_snapshotted_and_restored_without_attribution": len(late_git), "original_reparse_buffers_freshly_matched": len(original_links),
              "restored_relative_internal_links_created_and_resolved": 25, "external_personal_runtime_junctions_not_recreated": 2,
              "bounded_WSL_filesystem_sessions": 1, "WSL_restored_initial_stopped_state": True, "POSIX_permission_function_fixture_passed": True,
              "actual_Linux_target_permissions_owners_ACLs_or_server_validated": False, "relocated_path_contracts_without_numeric_imports": 5,
              "restored_Git_heads_and_repository_roots_verified": 2, "delivery_tests_passed": 9, "current_code_role_records": 906,
              "existing_code_config_files_byte_unchanged": 905, "production_or_old_maintenance_or_training_source_changed": False,
              "current_navigation_links_checked": link_count, "original_file_metadata_checks": metadata_checks,
              "git_timestamp_differences_byte_verified": len(git_time_matches), "prior_seals_bound_to_freshly_rehashed_project": prior,
              "scientific_seal_entries_bound_to_freshly_rehashed_project": scientific, "research_state_unchanged": True,
              "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1, "PGC1_partial_accuracies_interpreted": False,
              "model_GPU_training_or_new_research_runs": 0, "install_download_deploy_or_external_transfer_performed": False,
              "source_originals_deleted_or_moved": False, "A4_A5_A6_and_target_holds_retained": True,
              "final_evidence_tar_and_master_acceptance_follow_seal_and_are_recorded_outside_phase": True,
              "server_selected": False, "server_migration_complete": False, "next_stage": "TARGET_SELECTION_AND_REMAINING_ACCEPTANCE"}
    (PHASE / "CHECKS.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    check(all(p.exists() for p in deferred), "Final check link missing")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
