"""List/check meeting assets and prepare a new portable authoring workspace."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil

REPO = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Unsafe relative path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or not parsed.parts or any(p in {"", ".", ".."} for p in value.split("/")):
        raise ValueError("Unsafe relative path")
    return Path(*parsed.parts)


def source_path(row, roots):
    if row["root"] not in roots:
        raise ValueError("Unknown asset root")
    root = Path(roots[row["root"]]).resolve()
    path = root / safe_relative(row["path"])
    current = path
    while current != root:
        stat = current.lstat()
        if current.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise ValueError("Refusing to follow a source reparse point")
        current = current.parent
    if not path.is_file():
        raise ValueError("Asset is not an ordinary file")
    return path


def validate(row, roots):
    path = source_path(row, roots)
    if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
        raise ValueError("Asset changed: " + row["root"] + ":" + row["path"])
    return path


def normalized_notes_script(original):
    # Preserve the historical content body; replace only module/image/output plumbing.
    old = '} from "docx";'
    new = '} = createRequire(import.meta.url)("./vendor/docx.cjs");'
    if original.count('import {\n  AlignmentType') != 1 or original.count(old) != 1:
        raise ValueError("Unexpected historical note-builder import")
    text = original.replace('import {\n  AlignmentType', 'const {\n  AlignmentType', 1).replace(old, new, 1)
    text = 'import { createRequire } from "node:module";\nimport { fileURLToPath } from "node:url";\n' + text
    text = text.replace('const T = String.raw;', 'const bundleRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");', 1)
    for name, relative in [
        ("deckImage", "rap-main/working files/weekly_20261101/review_v3/page-3.png"),
        ("mechanismImage", "rap-main/working files/decks/rap_slam_weekly-b5533638/media/mcv1_mechanism.png")]:
        lines = [line for line in text.splitlines() if line.startswith("const " + name + " = T`")]
        if len(lines) != 1:
            raise ValueError("Unexpected historical image binding")
        text = text.replace(lines[0], 'const ' + name + ' = path.join(bundleRoot, ' + json.dumps(relative) + ');', 1)
    guard = 'if (!outputPath) throw new Error("Usage: node create_weekly_script.js /absolute/path/output.docx");'
    if text.count(guard) != 1:
        raise ValueError("Unexpected output guard")
    text = text.replace(guard, guard + '\nif (fs.existsSync(outputPath)) throw new Error("Output already exists");', 1)
    return text


def prepare(records, family, roots, destination, execute=False):
    selected = [r for r in records if r["family"] == family and r["role"] != "scientific_or_data_history_opaque_preserved"]
    if not selected:
        raise ValueError("Unknown or empty family")
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError("Destination must be new; no overwrite or implicit resume")
    # Never create authoring copies inside a historical source directory.
    for row in selected:
        source = Path(roots[row["root"]]).resolve() / safe_relative(row["path"])
        if destination == source or destination.is_relative_to(source.parent):
            raise ValueError("Destination overlaps historical source")
    result = {"family": family, "files_selected": len(selected), "bytes_selected": sum(r["bytes"] for r in selected),
              "opaque_data_and_results_copied": False, "destination": str(destination), "executed": execute,
              "scientific_or_builder_execution": False, "final_export_or_visual_QA_certified": False}
    if not execute:
        return result
    # Validate every source before any destination creation.
    validated = [(r, validate(r, roots)) for r in selected]
    destination.mkdir(parents=True)
    for row, source in validated:
        target = destination / row["root"] / safe_relative(row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != row["sha256"]:
            raise ValueError("Copy checksum mismatch")
    if family == "meeting-20261101":
        authoring = destination / "authoring"
        (authoring / "vendor").mkdir(parents=True)
        copied_root = destination / "rap-main"
        original = copied_root / "working files/weekly_20261101/create_weekly_script.js"
        module = copied_root / "working files/weekly_20261101/node_modules/docx/index.js"
        (authoring / "build_notes.mjs").write_bytes(normalized_notes_script(original.read_text(encoding="utf-8")).encode("utf-8"))
        shutil.copyfile(module, authoring / "vendor/docx.cjs")
        result["portable_notes_recipe_prepared"] = True
        result["vendored_module_sha256"] = sha(module)
        result["vendored_module_original_release_or_license_provenance_reauthenticated"] = False
    (destination / "PREPARE_RECEIPT.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    (destination / "SOURCE_MANIFEST.jsonl").write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in selected).encode("utf-8"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["list", "check", "prepare"])
    parser.add_argument("--catalog-root", type=Path, default=REPO / "docs/meetings")
    parser.add_argument("--rap-root", type=Path, default=REPO)
    parser.add_argument("--reports-root", type=Path, default=Path(os.environ.get("RAP_REPORTS_ROOT", str(REPO.parent / "RAP-SLAM-report"))))
    parser.add_argument("--family")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--execute", action="store_true", help="Copy to a new workspace; never run builders")
    args = parser.parse_args()
    catalog = load(args.catalog_root / "CATALOG.json")
    records = rows(args.catalog_root / "FILES.jsonl")
    roots = {"rap-main": args.rap_root, "reports": args.reports_root}
    if args.operation == "list":
        result = [{k: r[k] for k in ("id", "date", "state", "files")} for r in catalog["families"]]
    elif args.operation == "check":
        selected = [r for r in records if args.family is None or r["family"] == args.family]
        if not selected:
            raise ValueError("Unknown family")
        for row in selected:
            validate(row, roots)
        result = {"passed": True, "files_raw_sha256_checked": len(selected), "builders_executed": False}
    else:
        if not args.family or args.destination is None:
            parser.error("prepare requires --family and --destination")
        result = prepare(records, args.family, roots, args.destination, args.execute)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
