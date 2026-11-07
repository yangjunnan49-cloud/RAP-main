"""Read the documentary catalog without opening any experiment artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parents[2] / "docs/experiments/catalog.jsonl")
    parser.add_argument("--alias", help="Exact study alias, for example PGC1")
    parser.add_argument("--kind", help="Exact catalog kind")
    parser.add_argument("--text", help="Case-insensitive search in id, title, purpose and aliases")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    matches = []
    with args.catalog.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if args.alias and args.alias.casefold() not in [a.casefold() for a in row["aliases"]]:
                continue
            if args.kind and args.kind != row["kind"]:
                continue
            haystack = " ".join([row["id"], row["title"], row["purpose"] or "", *row["aliases"]]).casefold()
            if args.text and args.text.casefold() not in haystack:
                continue
            matches.append(row)
    if args.as_json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for row in matches:
            aliases = ",".join(row["aliases"]) or "-"
            print(f"{row['id']}\t{aliases}\t{row['execution_state'] or 'UNKNOWN_NOT_SUCCESS'}\t{row['kind']}")


if __name__ == "__main__":
    main()
