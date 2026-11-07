"""Verify A3 paths, source succession, metadata, and preserved phase seals."""
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
A2 = REPO / "docs/maintenance/2026-11-03/context-index-01"
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


def file_record(path, expected):
    check(path.stat().st_size == expected["bytes"] and sha(path) == expected["sha256"], "File changed: " + str(path))


def run(name, argv, expected=0, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("RAP_")}
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(argv, cwd=cwd or REPO / "docs", capture_output=True, text=True, encoding="utf-8", timeout=90, env=env)
    folder = PHASE / "validation"
    folder.mkdir(exist_ok=True)
    (folder / (name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (folder / (name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    check(result.returncode == expected, f"{name}: {result.returncode} != {expected}: {result.stderr[-1500:]}")
    return {"name": name, "argv": argv, "cwd": str(cwd or REPO / "docs"), "exit_code": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()}


def main():
    baseline = load(PHASE / "BASELINE.json")
    before = {(r["root"], r["path"]): r for r in baseline["backups"]}
    for r in before.values():
        file_record(PHASE / r["backup"], r)
    for r in load(A2 / "AUTHORITY_PROOF.json")["current_files"]:
        check(before[(r["root"], r["path"])]["sha256"] == r["sha256"], "A2 authority chain gap")
    proof = load(PHASE / "AUTHORITY_PROOF.json")
    for r in proof["current_files"]:
        file_record(ROOTS[r["root"]] / r["path"], r)
    changed = []
    for r in baseline["source_files"]:
        path = ROOTS[r["root"]] / r["path"]
        if sha(path) != r["sha256"]:
            changed.append(r["root"] + ":" + r["path"])
    check(set(changed) == {"rap-main:sample.py", "rap-main:demo.py", "rap-slam:scripts/run_pipeline.py", "rap-slam:rap_slam/rap_backend.py"}, "Unapproved source changes")
    succession = load(PHASE / "SOURCE_SUCCESSION.json")
    for r in succession["changed_existing_sources"]:
        check(sha(PHASE / r["before"]) == r["before_sha256"], "Old source lost")
        check(sha(ROOTS[r["root"]] / r["path"]) == r["after_sha256"], "New source differs")
    py = [sys.executable, "-I", "-B"]
    unit = run("unit-tests", py + [str(REPO / "tests/test_runtime_paths.py")])
    check("Ran 14 tests" in (PHASE / "validation/unit-tests.stderr.txt").read_text(encoding="utf-8"), "Unexpected test count")
    run("behavior", py + [str(PHASE / "verify_behavior.py")])
    check(load(PHASE / "BEHAVIOR_CHECKS.json")["passed"], "Behavior checks failed")
    run("code-index", py + [str(REPO / "scripts/maintenance/index_code_entries.py"), "--check"])
    code = rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    check(len(code) == 896, "Code coverage differs")
    syntax_errors = [r for r in code if r["syntax_error"]]
    check(len(syntax_errors) == 1 and syntax_errors[0]["sha256"] == "06f2f553d322581b203d8fd8abf7e565b6f520229d055403ee78801bd8655ad9", "New syntax failure")
    active = [r for r in code if r["default_dispatch_allowed"]]
    check(len(active) == 6 and not any(r["absolute_machine_reference_lines"] for r in active), "Current entry has personal path")
    for r in code:
        if r["role"] in {"current_entry", "current_maintenance"} or r["root"] + ":" + r["path"] in changed:
            compile((ROOTS[r["root"]] / r["path"]).read_text(encoding="utf-8"), r["id"], "exec")

    guard = py + [str(PHASE / "guard_cli.py")]
    launch = str(REPO / "scripts/run.py")
    profile = str(REPO / "config/runtime.example.json")
    input_dir = str(REPO / "demo_example_data/map_kitti")
    checks = []
    for task in ("sample", "demo", "features"):
        checks.append(run(task + "-paths", guard + [launch, task, "--paths", profile, "--input", input_dir,
                                                     "--run-id", "a3-path-check-never-executed", "--check"]))
    checks.append(run("sample-missing-default", guard + [launch, "sample", "--input", input_dir,
                                                        "--run-id", "a3-missing-never-executed", "--check"], expected=2))
    missing_plan = load(PHASE / "validation/sample-missing-default.stdout.txt")
    check(any("RAP checkpoint" in e and "rap_model.ckpt" in e for e in missing_plan["errors"]), "Wrong missing-file diagnosis")
    checks.append(run("slam-paths", guard + [launch, "slam", "--run-id", "a3-path-check-never-executed", "--check", "--", "--skip-loop-closure"], cwd=REPO / "dataset_process"))
    pipeline = str(ROOTS["rap-slam"] / "scripts/run_pipeline.py")
    checks.append(run("pipeline-help", guard + [pipeline, "--help"]))
    output = PHASE / "THIS_OUTPUT_MUST_NOT_EXIST"
    checks.append(run("pipeline-missing-map", guard + [pipeline, "--skip-loop-closure", "--map", str(PHASE / "NO_SUCH_MAP.ply"),
                                                       "--output", str(output)], expected=1))
    check(not output.exists(), "Preflight created output")
    for item in checks:
        stderr = (PHASE / "validation" / (item["name"] + ".stderr.txt")).read_text(encoding="utf-8")
        check("A3_NUMERICAL_IMPORT_GUARD_PASS" in stderr, "Numerical import guard missing")
    (PHASE / "CLI_CHECKS.json").write_text(json.dumps({"passed": True, "checks": checks, "model_or_arrays_loaded": False}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = load(REPO / "docs/CURRENT_STATE.json")
    old_state = load(PHASE / "before/rap-main/docs/CURRENT_STATE.json")
    check(state["research"] == old_state["research"] and state["preservation_holds"] == old_state["preservation_holds"], "Research/gaps changed")
    check(state["migration"]["A3"].startswith("COMPLETE_") and state["next_step"]["stage"] == "A4", "Wrong current stage")
    spec = importlib.util.spec_from_file_location("a3_current_renderer", REPO / "scripts/maintenance/render_current_state.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    check(renderer.render(state) == (REPO / "docs/CURRENT_STATE.md").read_text(encoding="utf-8"), "State rendering differs")
    for root in ("rap-main", "rap-slam", "workspace-root"):
        bound = 16384 if root == "rap-main" else 8192
        check((ROOTS[root] / "AGENTS.md").stat().st_size <= bound, "AGENTS too large")
    markdown = [ROOTS[r["root"]] / r["path"] for r in proof["current_files"] if r["path"].endswith(".md") and "/evidence/" not in r["path"]]
    markdown += [PHASE / "REPORT_CN.md", PHASE / "AUTHORITY.md"]
    links = 0
    deferred_receipt_links = []
    for document in markdown:
        for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", document.read_text(encoding="utf-8")):
            target = unquote(match.group(1).strip().strip("<>").split("#")[0])
            if not target or re.match(r"^[a-z]+://|^mailto:", target):
                continue
            resolved = (document.parent / target).resolve()
            if resolved == PHASE / "CHECKS.json":
                # This verifier creates its own receipt only after all other checks pass.
                deferred_receipt_links.append(resolved)
            else:
                check(resolved.exists(), "Broken current link: " + str(document) + " -> " + target)
            links += 1
    prior = {}
    for folder in (REPO / "docs/maintenance/2026-11-03/migration-preflight-01", A1, A2):
        entries = load(folder / "DELIVERY_SEAL.json")["files"]
        for r in entries:
            file_record(folder / r["path"], r)
        prior[folder.name] = len(entries)
    scientific = 0
    for scope in ("identity-evidence-01", "stereo-source-01", "stereo-support-01", "stereo-alias-01", "windows-lease-01"):
        folder = REPO / "docs/maintenance/2026-11-03" / scope
        for r in load(folder / "DELIVERY_SEAL.json")["files"]:
            file_record(folder / r["path"], r)
            scientific += 1
    check(scientific == 2047, "Scientific entry count changed")

    # Verify all A1 physical identities; reparse entries are never dereferenced.
    hashes = {r["root"] + ":" + r["path"]: r for r in rows(A1 / "HASHES.jsonl")}
    allowed = {r["root"] + ":" + r["path"] for r in proof["current_files"]}
    original_metadata, original_source, git_files, timestamp_only = 0, 0, 0, []
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
                observed = sha(path)
                check(stat.st_size == r["bytes"] and observed == h["sha256"], "Git bytes changed: " + asset)
                git_files += 1
                if not same:
                    timestamp_only.append({"asset": asset, "sha256": observed, "bytes": stat.st_size,
                                           "original_mtime_ns": h["mtime_ns"], "observed_mtime_ns": stat.st_mtime_ns})
            else:
                check(same, "Unexpected original metadata change: " + asset)
            if Path(r["path"]).suffix.lower() in suffixes:
                check(sha(path) == h["sha256"], "Unapproved original source/config change: " + asset)
                original_source += 1
        original_metadata += 1
    for root in ("rap-main", "rap-slam"):
        old_git = load(A1 / "git" / root / "STATE.json")
        git = ROOTS[root] / ".git"
        ref = (git / "HEAD").read_text().strip()
        check(ref == "ref: refs/heads/" + old_git["branch"], "Branch changed")
        check((git / ref[5:]).read_text().strip() == old_git["head"], "HEAD changed")
    # Current proof must still match after all check-only subprocesses.
    for r in proof["current_files"]:
        file_record(ROOTS[r["root"]] / r["path"], r)
    result = {"passed": True, "stage": "A3_COMPLETE_ENTRY_PATH_REFACTOR_WITH_STATIC_BEHAVIOR_CHECKS",
              "before_files_verified": len(before), "baseline_code_config_files": len(baseline["source_files"]),
              "changed_existing_sources": changed, "other_baseline_sources_sha256_unchanged": 883,
              "code_role_records": len(code), "known_preserved_historical_syntax_errors": syntax_errors,
              "current_files_sha256_verified": len(proof["current_files"]), "current_navigation_links_verified": links,
              "unit_tests_passed": 14, "unit_test_run": unit, "guarded_cli_checks_passed": len(checks),
              "behavior_checks": load(PHASE / "BEHAVIOR_CHECKS.json"), "prior_phase_seals_sha256_verified": prior,
              "scientific_seal_entries_sha256_verified": scientific, "original_regular_file_metadata_checked": original_metadata,
              "other_original_source_config_sha256_unchanged": original_source, "git_files_sha256_unchanged": git_files,
              "git_timestamp_only_byte_verified": timestamp_only, "git_branch_heads_and_index_unchanged": True,
              "PGC1_partial_accuracies_interpreted": False, "WSL_GPU_model_training_or_research_started": False,
              "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
              "target_environment_numerical_execution_validated": False, "next_stage": "A4", "server_migration_complete": False}
    (PHASE / "CHECKS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check(all(path.is_file() for path in deferred_receipt_links), "Final receipt link missing")
    display = dict(result)
    display["known_preserved_historical_syntax_errors"] = len(syntax_errors)
    display["git_timestamp_only_byte_verified"] = len(timestamp_only)
    print(json.dumps(display, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
