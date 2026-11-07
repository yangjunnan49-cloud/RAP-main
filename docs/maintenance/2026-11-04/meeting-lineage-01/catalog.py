"""Read existing Office packages and static authoring references; never run builders."""
from collections import Counter, defaultdict
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from pypdf import PdfReader

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A5 = REPO / "docs/maintenance/2026-11-04/assets-package-01"
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def save(name, value):
    (PHASE / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def asset(row):
    return row["root"] + ":" + row["path"]


def relationships(z, part):
    folder, name = posixpath.split(part)
    rel = folder + "/_rels/" + name + ".rels"
    if rel not in z.namelist():
        return {}
    result = {}
    for r in ET.fromstring(z.read(rel)):
        external = r.get("TargetMode") == "External"
        target = r.get("Target")
        result[r.get("Id")] = {"target": target if external else target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(folder, target)),
                                "external": external, "type": r.get("Type", "").rsplit("/", 1)[-1]}
    return result


def main():
    baseline = load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["roots"].items()}
    source = rows(PHASE / "SOURCE_FILES.jsonl")
    all_source = rows(A5 / "SOURCE_FILES.jsonl")
    by_digest = defaultdict(list)
    all_by_digest = defaultdict(list)
    for r in source:
        by_digest[r["sha256"]].append(asset(r))
    for r in all_source:
        all_by_digest[r["sha256"]].append(asset(r))
    artifacts, figure_edges, script_refs, dsl = [], [], [], []
    for r in source:
        path = roots[r["root"]] / r["path"]
        suffix = path.suffix.lower()
        aid = asset(r)
        if suffix in {".pptx", ".docx"}:
            entry = {"asset": aid, "sha256": r["sha256"], "bytes": r["bytes"], "format": suffix[1:],
                     "aliases_with_same_bytes": by_digest[r["sha256"]], "new_native_or_visual_QA_performed": False}
            with zipfile.ZipFile(path) as z:
                bad = z.testzip()
                assert bad is None, (aid, bad)
                entry["zip_CRC_passed"] = True
                if suffix == ".pptx":
                    presentation = ET.fromstring(z.read("ppt/presentation.xml"))
                    rels = relationships(z, "ppt/presentation.xml")
                    slides = []
                    for i, slide_id in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
                        part = rels[slide_id.get("{" + NS["r"] + "}id")]["target"]
                        tree = ET.fromstring(z.read(part))
                        relations = relationships(z, part)
                        notes = []
                        images = []
                        for rr in relations.values():
                            if rr["type"] == "notesSlide" and not rr["external"]:
                                notes.extend(t.text or "" for t in ET.fromstring(z.read(rr["target"])).findall(".//a:t", NS))
                            if rr["type"] == "image" and not rr["external"]:
                                raw = z.read(rr["target"])
                                digest = hashlib.sha256(raw).hexdigest()
                                aliases = all_by_digest[digest]
                                images.append({"part": rr["target"], "sha256": digest, "bytes": len(raw), "exact_external_file_aliases": aliases})
                                figure_edges.append({"artifact": aid, "slide": i, "media_part": rr["target"], "sha256": digest,
                                                     "source_file_byte_aliases": aliases, "scientific_or_pixel_semantics_certified": False})
                        slides.append({"number": i, "part": part, "text": [t.text or "" for t in tree.findall(".//a:t", NS)],
                                       "notes": notes, "images": images, "native_tables": len(tree.findall(".//a:tbl", NS)),
                                       "native_chart_relationships": sum(rr["type"] == "chart" for rr in relations.values()),
                                       "external_relationships": [rr for rr in relations.values() if rr["external"]]})
                    entry["active_slide_count"] = len(slides)
                    entry["slides"] = slides
                else:
                    tree = ET.fromstring(z.read("word/document.xml"))
                    texts = [t.text or "" for t in tree.findall(".//w:t", NS)]
                    entry["opening_text"] = texts[:12]
                    entry["word_page_count_from_app_properties_is_not_render_validation"] = None
                    if "docProps/app.xml" in z.namelist():
                        props = ET.fromstring(z.read("docProps/app.xml"))
                        pages = next((t.text for t in props if t.tag.endswith("}Pages")), None)
                        entry["word_page_count_from_app_properties_is_not_render_validation"] = pages
                    entry["external_relationships"] = [rr for rr in relationships(z, "word/document.xml").values() if rr["external"]]
                    for name in z.namelist():
                        if name.startswith("word/media/"):
                            raw = z.read(name)
                            digest = hashlib.sha256(raw).hexdigest()
                            figure_edges.append({"artifact": aid, "media_part": name, "sha256": digest,
                                                 "source_file_byte_aliases": all_by_digest[digest], "scientific_or_pixel_semantics_certified": False})
            artifacts.append(entry)
        elif suffix == ".pdf":
            reader = PdfReader(path)
            artifacts.append({"asset": aid, "sha256": r["sha256"], "bytes": r["bytes"], "format": "pdf",
                              "pages": len(reader.pages), "first_page_excerpt": (reader.pages[0].extract_text() or "")[:250] if reader.pages else "",
                              "new_native_or_visual_QA_performed": False})
        elif suffix == ".pptd":
            text = path.read_text(encoding="utf-8")
            pages = re.findall(r"^\s*-\s+(pages/[^\r\n]+\.page)\s*$", text, re.M)
            references = []
            for item in pages:
                page = path.parent / item
                assert page.is_file(), (aid, item)
                page_text = page.read_text(encoding="utf-8")
                for match in re.finditer(r"\bsrc:\s*([^,}\r\n]+)", page_text):
                    relative = match.group(1).strip().strip("\"'")
                    target = page.parent.parent / relative
                    references.append({"page": item, "literal": relative, "exists": target.is_file(),
                                       "sha256": sha(target) if target.is_file() else None})
            listed = set(pages)
            unused = [p.relative_to(path.parent).as_posix() for p in (path.parent / "pages").glob("*.page") if p.relative_to(path.parent).as_posix() not in listed]
            dsl.append({"asset": aid, "sha256": r["sha256"], "active_pages": pages, "active_page_count": len(pages),
                        "unlisted_pages_retained": unused, "image_references": references, "export_engine_rebuilt_or_certified": False})
        elif suffix in {".py", ".mjs", ".js", ".ps1", ".sh"} and "/node_modules/" not in r["path"] and "/benchmark/" not in r["path"]:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            imports = []
            if suffix == ".py":
                tree = ast.parse(text)
                imports = sorted({n.module or "." for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} |
                                 {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
            refs = [{"line": i, "text": line.strip()[:450]} for i, line in enumerate(text.splitlines(), 1)
                    if re.search(r"[CE]:[/\\]|/root/|/mnt/|node_modules|AppData|\.cache/|KIMI_DESKTOP", line)]
            script_refs.append({"asset": aid, "sha256": r["sha256"], "imports_static": imports,
                                "machine_or_runtime_reference_lines": refs, "executed_in_A6": False})
    save("ARTIFACT_STRUCTURE.json", artifacts)
    save("FIGURE_BYTE_LINKS.json", figure_edges)
    save("AUTHORING_SCRIPTS.json", script_refs)
    save("EDITABLE_DECKS.json", dsl)

    declared = []
    for name, field in [("docs/meeting_20260930/delivery_manifest.json", "outputs"),
                        ("docs/meeting_20261011/DELIVERY.json", "outputs"),
                        ("docs/meeting_20261018/.build/DELIVERY_CHECKS.json", "files")]:
        receipt = load(REPO / name)
        outputs = receipt[field]
        values = [{"path": k, **v} for k, v in outputs.items()] if isinstance(outputs, dict) else outputs
        for item in values:
            original = item["path"].replace("\\", "/")
            target = Path(original) if re.match(r"^[A-Z]:/", original) else (REPO / name).parent / original
            actual = sha(target)
            declared.append({"receipt": "rap-main:" + name, "asset": "rap-main:" + target.relative_to(REPO).as_posix(),
                             "expected_sha256": item["sha256"], "actual_sha256": actual, "matches": actual == item["sha256"]})
    assert len(declared) == 6 and all(r["matches"] for r in declared)
    save("DELIVERY_IDENTITY_CHECKS.json", declared)
    bindings = []
    refs = load(REPO / "docs/meeting_20260930/delivery_manifest.json")["sources"]
    refs += load(REPO / "docs/meeting_20261018/.build/content_sources.json")
    refs += [{"path": k, **v} for k, v in load(REPO / "docs/meeting_20261018/.build/reference_inventory.json")["files"].items()]
    for item in refs:
        digest = item.get("sha256")
        if not digest:
            continue
        literal = item["path"].replace("\\", "/")
        target = Path(literal) if re.match(r"^[A-Z]:/", literal) else REPO / literal
        match = target.is_file() and sha(target) == digest
        aliases = all_by_digest[digest]
        bindings.append({"historical_literal": literal, "expected_sha256": digest, "current_original_path_matches": match,
                         "exact_byte_aliases_in_A5_base": aliases, "state": "EXACT_ORIGINAL_PATH" if match else "EXACT_BYTE_ALIAS_AVAILABLE" if aliases else "UNRECOVERED_EXACT_BYTES",
                         "identity_independence_or_scientific_admission_certified": False})
    save("HISTORICAL_SOURCE_BINDINGS.json", bindings)
    borrow = load(REPO / "working files/decks/rap_slam_weekly-b5533638/.borrow.json")
    borrowed = REPO / "docs/meeting_20261025/rap_slam_weekly/rap_slam_weekly.pptx"
    discrepancies = [
        {"id": "SEP21_SLIDE_COUNT", "historical": "DELIVERY.md and builder say 8 pages", "observed_active_pptx_slides": next(a["active_slide_count"] for a in artifacts if a["asset"] == "rap-main:docs/meeting_20260921/rap_slam_meeting.pptx"),
         "action": "Keep original artifact and historical statement; no silent correction or delivery certification"},
        {"id": "NOV01_SOURCE_EXPORT_IDENTITY", "borrow_record_pptx_sha_prefix": borrow["pptxSha"], "current_pptx_sha256": sha(borrowed),
         "borrow_prefix_matches": sha(borrowed).startswith(borrow["pptxSha"]), "current_export_slides": 4, "editable_source_active_pages": 5,
         "action": "Nov01 editable source/notes are a separate candidate family; do not label the four-slide PPTX/PDF as its final export"},
        {"id": "UNLISTED_SOURCE_PAGES", "pages": ["pages/5_adapter.page", "pages/5_gaps.page"], "action": "Retain unlisted pages as historical alternatives, never append automatically"},
    ]
    save("VERSION_DISCREPANCIES.json", discrepancies)

    families = [
      {"id": "report-202607", "date": "2026-07", "topic": "阶段进展汇报", "state": "RETAINED_PDF_NO_FINAL_RECEIPT", "roots": ["reports:advisor_report"], "primary": ["reports:advisor_report/RAP-SLAM进展汇报_202607.pdf"]},
      {"id": "report-undated", "date": None, "topic": "早期项目演示编辑源", "state": "SOURCE_ONLY_DATE_UNCONFIRMED", "roots": ["reports:ppt"], "primary": []},
      {"id": "meeting-20260823", "date": "2026-08-23", "topic": "周汇报两版及知识点小抄", "state": "TWO_EXPORT_VARIANTS_FINAL_OWNER_CHOICE_UNCONFIRMED", "roots": ["reports:ppt_weekly_20260823"], "primary": ["reports:ppt_weekly_20260823/rap_slam_weekly.pptx", "reports:ppt_weekly_20260823/rap_slam_weekly_v2.pptx", "reports:ppt_weekly_20260823/汇报小抄_20260823.pdf"]},
      {"id": "meeting-20260921", "date": "2026-09-21", "topic": "组会与论文配套", "state": "HISTORIC_DELIVERY_WITH_SLIDE_COUNT_DISCREPANCY", "roots": ["rap-main:docs/meeting_20260921"], "primary": ["rap-main:docs/meeting_20260921/rap_slam_meeting.pptx", "rap-main:docs/meeting_20260921/paper/paper.pdf"]},
      {"id": "meeting-20260930", "date": "2026-09-30", "topic": "六页无实验编号汇报与口稿问答", "state": "FINAL_IDENTITY_MATCHES_HISTORIC_DELIVERY", "roots": ["rap-main:docs/meeting_20260930"], "primary": [r["asset"] for r in declared if "20260930/" in r["asset"]]},
      {"id": "meeting-20261011", "date": "2026-10-11", "topic": "完整系统比较与实验思路", "state": "FINAL_IDENTITY_MATCHES_HISTORIC_DELIVERY", "roots": ["rap-main:docs/meeting_20261011"], "primary": [r["asset"] for r in declared if "20261011/" in r["asset"]]},
      {"id": "meeting-20261018", "date": "2026-10-18", "delivery_closed": "2026-10-20", "topic": "十二页汇报与讲解问答", "state": "FINAL_IDENTITY_MATCHES_HISTORIC_DELIVERY", "roots": ["rap-main:docs/meeting_20261018"], "primary": [r["asset"] for r in declared if "20261018/" in r["asset"]]},
      {"id": "meeting-20261025", "date": "2026-10-25", "topic": "四页周报导出及原讲稿", "state": "RETAINED_EXPORTS_NOT_NOV01_SOURCE_FINAL", "roots": ["rap-main:docs/meeting_20261025"], "primary": ["rap-main:docs/meeting_20261025/rap_slam_weekly/rap_slam_weekly.pptx", "rap-main:docs/meeting_20261025/rap_slam_weekly/rap_slam_weekly.pdf", "rap-main:docs/meeting_20261025/rap_slam_weekly/RAP-SLAM组会汇报讲稿与术语说明.docx"]},
      {"id": "meeting-20261101", "date": "2026-11-01", "topic": "五页编辑源、图表与知识点讲稿", "state": "EDITABLE_SOURCE_AND_NOTES_EXPORT_NOT_BOUND_TO_FINAL_PPTX", "roots": ["rap-main:working files/decks", "rap-main:working files/weekly_20261101"], "primary": ["rap-main:working files/decks/rap_slam_weekly-b5533638/rap_slam_weekly.pptd", "rap-main:docs/meeting_20261025/rap_slam_weekly/RAP-SLAM周报知识点与汇报稿_2026-11-01.docx"]},
      {"id": "manuscript-archive", "date": None, "topic": "论文历史工程", "state": "HISTORICAL_ONLY_PAPER_CURRENTLY_PAUSED", "roots": ["reports:paper"], "primary": ["reports:paper/main.pdf"]},
    ]
    file_rows = []
    for r in source:
        aid = asset(r)
        if aid == "rap-main:docs/meeting_20261025/rap_slam_weekly/RAP-SLAM周报知识点与汇报稿_2026-11-01.docx":
            family = next(f for f in families if f["id"] == "meeting-20261101")
        else:
            owners = [f for f in families if any(aid.startswith(prefix + "/") for prefix in f["roots"])]
            assert len(owners) == 1, aid
            family = owners[0]
        suffix = PurePosixPath(r["path"]).suffix.lower()
        if aid in family["primary"]:
            role = "primary_recorded_artifact"
        elif "/benchmark/" in r["path"] or suffix in {".bin", ".npy", ".npz", ".ply", ".g2o"}:
            role = "scientific_or_data_history_opaque_preserved"
        elif suffix in {".pptx", ".docx", ".pdf"}:
            role = "alternative_or_QA_artifact_retained"
        elif suffix in {".py", ".js", ".mjs", ".ps1", ".sh"}:
            role = "vendored_module" if "/node_modules/" in r["path"] else "historical_builder_or_research_script_not_auto_executed"
        elif suffix in {".pptd", ".page", ".tex", ".bib"}:
            role = "editable_source"
        elif suffix in {".png", ".jpg", ".jpeg", ".svg"}:
            role = "figure_or_QA_image_retained"
        else:
            role = "support_evidence_or_build_record_retained"
        file_rows.append({**r, "family": family["id"], "role": role, "source_asset": aid})
    for f in families:
        members = [r for r in file_rows if r["family"] == f["id"]]
        f["files"] = len(members)
        f["bytes"] = sum(r["bytes"] for r in members)
        f["meeting_actually_held_certified"] = False
        f["new_scientific_or_training_admission"] = False
    save("CATALOG.json", {"schema_version": 1, "families": families, "ordinary_files": len(source), "source_bytes": baseline["logical_bytes"],
                           "known_delivery_hashes_matched": len(declared), "decks_with_final_receipt_identity": 3,
                           "source_or_artifact_lineage_is_not_new_scientific_validation": True})
    (PHASE / "FILES.jsonl").write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in file_rows).encode("utf-8"))
    save("SUMMARY.json", {"families": len(families), "source_files": len(source), "source_bytes": baseline["logical_bytes"],
          "artifacts_inspected": len(artifacts), "artifact_formats": dict(Counter(r["format"] for r in artifacts)),
          "figure_media_links": len(figure_edges), "figure_media_links_with_exact_file_alias": sum(bool(r["source_file_byte_aliases"]) for r in figure_edges),
          "editable_decks": len(dsl), "static_authoring_scripts": len(script_refs), "historical_source_bindings": len(bindings),
          "binding_states": dict(Counter(r["state"] for r in bindings)), "source_only_or_version_discrepancies_retained": True,
          "native_Office_export_model_training_or_new_research_runs": 0})
    print(json.dumps(load(PHASE / "SUMMARY.json"), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
