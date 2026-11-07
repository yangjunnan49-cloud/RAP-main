"""Record acquisition hints from existing local scripts/logs without contacting URLs."""
import hashlib
import json
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def main():
    roots = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM"}
    claims = []
    for root, relative in (("rap-slam", "scripts/download_poss_segment.py"), ("rap-slam", "scripts/download_spires.sh"),
                           ("rap-main", "scripts/download_weights_and_demo_data.sh")):
        source = roots[root] / relative
        raw = source.read_bytes()
        links = []
        for i, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            for value in re.findall(r"https?://[^\s\"'<>]+", line):
                links.append({"line": i, "url_text_as_written": value})
        claims.append({"source_asset": root + ":" + relative, "source_sha256": hashlib.sha256(raw).hexdigest(), "url_claims": links,
                       "source_executed_or_URL_contacted_in_A5": False, "physical_file_origin_authenticated": False})
    source = roots["rap-slam"] / "data/poss/download_b.log"
    raw = source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    historical_log = {"source_asset": "rap-slam:data/poss/download_b.log", "sha256": hashlib.sha256(raw).hexdigest(),
                      "declared_files_to_fetch": 2751 if text.startswith("2751 files to fetch") else None,
                      "declared_final_marker": "DONE" if text.rstrip().endswith("DONE") else None,
                      "historical_declaration_not_new_download_or_provider_integrity_proof": True}
    value = {"claims_from_local_acquisition_scripts": claims, "historical_download_log": historical_log,
             "new_downloads_or_source_authentication": False, "PGC1_or_raw_OXTS_route_resumed": False}
    (PHASE / "SOURCE_CLAIMS.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"local_script_sources": len(claims), "URLs_contacted": 0, "historical_POSs_log_files_declared": historical_log["declared_files_to_fetch"]}))


if __name__ == "__main__":
    main()
