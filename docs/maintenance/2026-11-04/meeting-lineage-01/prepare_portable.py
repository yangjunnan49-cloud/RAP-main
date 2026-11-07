"""Exercise A6 copy-only authoring preparation without creating Office documents."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

PHASE = Path(__file__).resolve().parent
NODE = Path("C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")


def main():
    spec = importlib.util.spec_from_file_location("prepared_materials", PHASE / "updates/scripts/meetings/materials.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    baseline = tool.load(PHASE / "BASELINE.json")
    records = tool.rows(PHASE / "FILES.jsonl")
    roots = {k: Path(v) for k, v in baseline["roots"].items()}
    destination = PHASE / "portable/meeting-20261101"
    if destination.exists():
        # The initial source copies remain unchanged; refresh only the unsealed recipe.
        for row in tool.rows(destination / "SOURCE_MANIFEST.jsonl"):
            assert tool.sha(destination / row["root"] / row["path"]) == row["sha256"]
        result = tool.load(destination / "PREPARE_RECEIPT.json")
        original = roots["rap-main"] / "working files/weekly_20261101/create_weekly_script.js"
        (destination / "authoring/build_notes.mjs").write_bytes(tool.normalized_notes_script(original.read_text(encoding="utf-8")).encode("utf-8"))
    else:
        result = tool.prepare(records, "meeting-20261101", roots, destination, True)
    generated = destination / "authoring/build_notes.mjs"
    original = roots["rap-main"] / "working files/weekly_20261101/create_weekly_script.js"
    assert generated.read_text(encoding="utf-8").split("const palette =", 1)[1] == original.read_text(encoding="utf-8").split("const palette =", 1)[1]
    assert "E:\\githouse" not in generated.read_text(encoding="utf-8")
    syntax = subprocess.run([str(NODE), "--check", str(generated)], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert syntax.returncode == 0, syntax.stderr
    module = generated.parent / "vendor/docx.cjs"
    exports = subprocess.run([str(NODE), "-e", "const d=require(process.argv[1]); if(!['Document','Packer','ImageRun','Paragraph'].every(k=>typeof d[k]==='function'))process.exit(1);console.log('required exports available');", str(module)],
                             capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert exports.returncode == 0, exports.stderr
    (PHASE / "NODE_SYNTAX.stdout.txt").write_text(syntax.stdout + exports.stdout, encoding="utf-8")
    (PHASE / "NODE_SYNTAX.stderr.txt").write_text(syntax.stderr + exports.stderr, encoding="utf-8")
    result.update({"observed_utc": datetime.now(timezone.utc).isoformat(), "node_syntax_check_passed": True,
                   "vendored_module_import_check_passed": True, "notes_content_body_byte_text_unchanged": True,
                   "normalized_recipe_sha256": hashlib.sha256(generated.read_bytes()).hexdigest(),
                   "source_script_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                   "personal_cache_path_used_by_prepared_notes_recipe": False,
                   "builder_office_export_or_render_executed": False, "new_DOCX_or_PPTX_created": False,
                   "scientific_arrays_model_data_or_training_loaded": False, "native_pptd_export_runtime_ported_or_certified": False})
    (PHASE / "PORTABLE_PREPARATION.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
