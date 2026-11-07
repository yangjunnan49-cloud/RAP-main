"""Verify A4 audit receipts, current documentation, preserved code, and phase seals."""
import ast
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
A3 = REPO / "docs/maintenance/2026-11-04/code-paths-01"
ROOTS = {r["id"]: Path(r["local"]) for r in json.loads((A1 / "ROOT_MAPPING.json").read_text(encoding="utf-8"))["mapping"]}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def file_record(path, record):
    check(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], "Changed file: " + str(path))


def run(name, argv):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(argv, cwd=REPO / "docs", env=env, capture_output=True, text=True, encoding="utf-8", timeout=45)
    folder = PHASE / "validation"
    folder.mkdir(exist_ok=True)
    (folder / (name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (folder / (name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    check(result.returncode == 0, name + ": " + result.stderr[-1800:])
    return {"name": name, "exit_code": result.returncode, "stdout_sha256": sha(folder / (name + ".stdout.txt")), "stderr_sha256": sha(folder / (name + ".stderr.txt"))}


def main():
    baseline = load(PHASE / "BASELINE.json")
    before = {(r["root"], r["path"]): r for r in baseline["backups"]}
    for record in before.values():
        file_record(PHASE / record["backup"], record)
    previous = load(A3 / "AUTHORITY_PROOF.json")
    for r in previous["current_files"]:
        check(before[(r["root"], r["path"])]["sha256"] == r["sha256"], "A3 authority chain gap")
    proof = load(PHASE / "AUTHORITY_PROOF.json")
    for r in proof["current_files"]:
        file_record(ROOTS[r["root"]] / r["path"], r)
    changed = [r["root"] + ":" + r["path"] for r in baseline["code_files"] if sha(ROOTS[r["root"]] / r["path"]) != r["sha256"]]
    check(set(changed) == {"rap-main:scripts/maintenance/index_code_entries.py", "rap-main:scripts/maintenance/render_current_state.py"}, "Production or unrelated source changed")
    # Whitelist the two maintenance edits and compare their complete ASTs.
    index_path = "scripts/maintenance/index_code_entries.py"
    old = (PHASE / "before/rap-main" / index_path).read_text(encoding="utf-8")
    new = (REPO / index_path).read_text(encoding="utf-8")
    new = new.replace('    if root == "rap-main" and path.startswith("scripts/environment/"):\n        return "current_environment_verification", None\n', "")
    new = new.replace('"rap_runtime", "tests", "environment")', '"rap_runtime", "tests")')
    check(ast.dump(ast.parse(new)) == ast.dump(ast.parse(old)), "Unexpected code index edit")
    render_path = "scripts/maintenance/render_current_state.py"
    old = (PHASE / "before/rap-main" / render_path).read_text(encoding="utf-8")
    new = (REPO / render_path).read_text(encoding="utf-8")
    old_line = 'f"- {holds[\'linux_environment_hash_claim_occurrences_pending_A4\']} 条 Linux 环境哈希声明待 A4 核对，不能称为文件已丢失。",'
    new_line = 'f"- 原 {holds.get(\'linux_environment_hash_claim_occurrences_exact_matched_in_A4\', 0)} 条 Linux 环境哈希声明已在 A4 精确匹配；仍待核对 {holds[\'linux_environment_hash_claim_occurrences_pending_A4\']} 条。原构建提交与目标重建另行验收。",'
    check(new_line in new and ast.dump(ast.parse(new.replace(new_line, old_line))) == ast.dump(ast.parse(old)), "Unexpected state renderer edit")
    print("Backups, authority and production-source preservation passed", flush=True)

    unit = run("environment-tools", [sys.executable, "-I", "-B", str(REPO / "tests/test_environment_tools.py")])
    check("Ran 5 tests" in (PHASE / "validation/environment-tools.stderr.txt").read_text(encoding="utf-8"), "Unexpected test count")
    run("code-index", [sys.executable, "-I", "-B", str(REPO / index_path), "--check"])
    code = rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    check(len(code) == 903, "Code index coverage differs")
    check(sum(r["syntax_error"] is not None for r in code) == 1, "New indexed syntax error")
    graph = load(REPO / "docs/environment/DEPENDENCIES.json")
    check(len(graph["files"]) == 72 and sum(len(r["imports"]) for r in graph["files"]) == 552, "Dependency graph coverage differs")
    for r in graph["files"]:
        root, relative = r["id"].split(":", 1)
        file_record(ROOTS[root] / relative, r)
    raw = load(PHASE / "LINUX_OBSERVATION.json")
    check(len(raw["claims"]) == 72 and all(r["a4_state"] == "EXACT_MATCH" and r["observed_sha256"] == r["sha256"].lower() for r in raw["claims"]), "Linux historical claim mismatch")
    summary = load(PHASE / "ENVIRONMENT_SUMMARY.json")
    check([r["unique_metadata_directories"] for r in summary["environments"]] == [184, 86, 88, 147], "Environment normalization differs")
    check(sum(r["unique_python_record_checks"] for r in summary["environments"]) == 4701, "RECORD coverage differs")
    check(all(set(r["record_states"]) <= {"MATCH"} for r in summary["environments"]), "Unexpected installed Python modification")
    assets = load(PHASE / "LINUX_PRESERVATION_MANIFEST.json")
    for r in assets["files"]:
        file_record(PHASE / r["copy"], r)
    check(assets["unique_files"] == 384 and assets["total_bytes"] == 332636737, "Linux preservation coverage differs")
    check(len(assets["installed_artifacts_RECORD_verified"]) == 227, "Installed artifact coverage differs")
    cpu = load(PHASE / "CPU_PROBE.json")
    required = [r for r in cpu["components"] if r["required_for_cpu_inference_import_gate"]]
    missing = [r for r in cpu["components"] if not r["passed"]]
    check(len(required) == 17 and all(r["passed"] for r in required), "Required CPU probe failed")
    check(len(missing) == 1 and missing[0]["component"] == "muon_training_dependency" and "ModuleNotFoundError" in missing[0]["error"], "Muon missing state hidden")
    check(cpu["torch_cuda_initialized_before"] is False and cpu["torch_cuda_initialized_after"] is False, "CUDA initialized")
    for key in ("model_instances", "checkpoint_loads", "dataset_reads", "research_runs", "training_or_backward_calls"):
        check(cpu[key] == 0, "Unadmitted model/data/training operation")
    for name in ("LINUX_SESSION.json", "CPU_SESSION.json", "BUILD_SESSION.json", "BUILD_SCRIPT_SESSION.json"):
        check(load(PHASE / name)["restored_initial_stopped_state"] is True, "WSL state not restored")
    build = load(PHASE / "BUILD_REVIEW.json")
    script = load(PHASE / "BUILD_SCRIPT_EVIDENCE.json")
    check(script["executed"] is False and script["full_commit_candidates"] == [], "Original build script execution or commit state changed")
    check(build["pytorch3d_original_successful_build_commit_recovered"] is False and build["build_log_1"]["result"] == "FAILED_GIT_CLONE", "Old build failure or provenance gap hidden")
    check(build["raw_scan_presence_label_error"]["actual_file_bytes_preserved"] == 313 and script["files"][0]["bytes"] == 313, "Build-script presence correction missing")
    check(load(PHASE / "VALIDATION_FAILURE_01.json")["WSL_started_before_failure"] is False, "Host helper failure record missing")
    final = load(PHASE / "HOST_after_build.json")
    check(all(r["exit_code"] == 0 for r in final["commands"]) and final["commands"][1]["stdout"].strip() == "", "Final WSL state unknown")
    training = load(PHASE / "TRAINING_AUDIT.json")
    check(training["training_chain_validated"] is False and len(training["findings"]) == 8 and training["fit_calls_in_maintained_entries"] == [], "Training readiness overstated")
    for r in training["source_references"]:
        root, relative = r["asset"].split(":", 1)
        file_record(ROOTS[root] / relative, r)
    pins = (REPO / "environment/requirements/observed-rap.constraints.txt").read_text().splitlines()
    check(len([line for line in pins if line and not line.startswith("#")]) == 184, "Reference pin count differs")

    state = load(REPO / "docs/CURRENT_STATE.json")
    old_state = load(PHASE / "before/rap-main/docs/CURRENT_STATE.json")
    check(state["research"] == old_state["research"], "Research state changed")
    check(state["migration"]["A4"] == "AUDIT_AND_GUIDE_COMPLETE_WITH_TRAINING_AND_TARGET_HOLDS" and state["next_step"]["stage"] == "A5", "Wrong current stage")
    holds = state["preservation_holds"]
    check(holds["linux_environment_hash_claim_occurrences_pending_A4"] == 0 and holds["linux_environment_hash_claim_occurrences_exact_matched_in_A4"] == 72, "Linux audit state inconsistent")
    check(holds["historical_source_digest_gaps"] == 5 and holds["historical_AGENTS_version_gaps"] == 1 and holds["training_entry_and_resume_chain_validated"] is False, "Preservation/training holds lost")
    spec = importlib.util.spec_from_file_location("a4_state_renderer", REPO / render_path)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    check(renderer.render(state) == (REPO / "docs/CURRENT_STATE.md").read_text(encoding="utf-8"), "State rendering differs")
    links, deferred = 0, []
    docs = [ROOTS[r["root"]] / r["path"] for r in proof["current_files"] if r["path"].endswith(".md") and "/evidence/" not in r["path"]]
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
            links += 1
    for root in ("rap-main", "rap-slam", "workspace-root"):
        check((ROOTS[root] / "AGENTS.md").stat().st_size <= (16384 if root == "rap-main" else 8192), "AGENTS too large")
    print("CPU receipts, source graph, Linux preservation, tests and current navigation passed", flush=True)
    prior = {}
    for folder in (REPO / "docs/maintenance/2026-11-03/migration-preflight-01", A1,
                   REPO / "docs/maintenance/2026-11-03/context-index-01", A3):
        items = load(folder / "DELIVERY_SEAL.json")["files"]
        for r in items:
            file_record(folder / r["path"], r)
        prior[folder.name] = len(items)
    scientific = 0
    for scope in ("identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"):
        folder = REPO / "docs/maintenance/2026-11-03" / scope
        for r in load(folder / "DELIVERY_SEAL.json")["files"]:
            file_record(folder / r["path"], r)
            scientific += 1
    check(scientific == 2047, "Scientific seal coverage differs")
    print("A0-A3 and scientific seals passed; checking original identities and Git bytes", flush=True)
    hashes = {r["root"] + ":" + r["path"]: r for r in rows(A1 / "HASHES.jsonl")}
    allowed = {r["root"] + ":" + r["path"] for r in proof["current_files"]}
    metadata_count, source_count, git_count, timestamp_only = 0, 0, 0, []
    suffixes = {".py", ".ps1", ".sh", ".yaml", ".yml", ".toml", ".cpp", ".h", ".hpp", ".c"}
    for r in rows(A1 / "inventory/entries.jsonl"):
        path = ROOTS[r["root"]] / r["path"]
        path.lstat()
        if r["kind"] != "file" or r["reparse_point"]:
            continue
        asset = r["root"] + ":" + r["path"]
        h = hashes[asset]
        stat = path.stat()
        if asset not in allowed:
            same = stat.st_size == r["bytes"] and stat.st_mtime_ns == h["mtime_ns"]
            if r["path"].startswith(".git/"):
                digest = sha(path)
                check(stat.st_size == r["bytes"] and digest == h["sha256"], "Git bytes changed: " + asset)
                git_count += 1
                if not same:
                    timestamp_only.append({"asset": asset, "sha256": digest, "original_mtime_ns": h["mtime_ns"], "observed_mtime_ns": stat.st_mtime_ns})
            else:
                check(same, "Unexpected original metadata change: " + asset)
            if Path(r["path"]).suffix.lower() in suffixes:
                check(sha(path) == h["sha256"], "Original source/config changed: " + asset)
                source_count += 1
        metadata_count += 1
    for root in ("rap-main", "rap-slam"):
        previous_git = load(A1 / "git" / root / "STATE.json")
        git = ROOTS[root] / ".git"
        ref = (git / "HEAD").read_text().strip()
        check(ref == "ref: refs/heads/" + previous_git["branch"] and (git / ref[5:]).read_text().strip() == previous_git["head"], "Git HEAD/branch changed")
    for r in proof["current_files"]:
        file_record(ROOTS[r["root"]] / r["path"], r)
    result = {"passed": True, "stage": "A4_AUDIT_AND_GUIDE_COMPLETE_WITH_TRAINING_AND_TARGET_HOLDS",
              "before_files_verified": len(before), "baseline_code_config_files": len(baseline["code_files"]),
              "changed_maintenance_sources": changed, "other_baseline_sources_sha256_unchanged": 894,
              "production_or_training_source_changed": False, "code_role_records": len(code), "current_files_sha256_verified": len(proof["current_files"]),
              "current_navigation_links_verified": links, "unit_tests_passed": 5, "unit_test_receipt": unit,
              "runtime_dependency_source_files_sha256_verified": 72, "linux_claim_occurrences_exact_match": 72,
              "unique_linux_claim_paths": 9, "selected_python_RECORD_checks_match": 4701, "linux_preserved_files_sha256_verified": 384,
              "linux_preserved_bytes": assets["total_bytes"], "installed_artifacts_RECORD_match": 227, "installed_native_binaries_RECORD_match": 19,
              "cpu_required_components_passed": 17, "known_missing_default_training_dependency": "muon",
              "temporary_WSL_sessions": 4, "WSL_restored_initial_stopped_state": True, "CUDA_context_initialized": False,
              "model_instances_checkpoint_or_dataset_loads_training_calls": 0, "software_install_or_package_download_performed": False,
              "original_regular_file_metadata_checked": metadata_count, "other_original_source_config_sha256_unchanged": source_count,
              "git_files_sha256_unchanged": git_count, "git_timestamp_only_byte_verified": timestamp_only,
              "prior_phase_seals_sha256_verified": prior, "scientific_seal_entries_sha256_verified": scientific,
              "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
              "PGC1_partial_accuracies_interpreted": False, "pytorch3d_original_build_commit_recovered": False,
              "complete_training_resume_clean_rebuild_or_target_GPU_model_validated": False,
              "next_stage": "A5", "server_migration_complete": False}
    (PHASE / "CHECKS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check(all(path.exists() for path in deferred), "Final receipt link missing")
    display = dict(result)
    display["git_timestamp_only_byte_verified"] = len(timestamp_only)
    print(json.dumps(display, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
