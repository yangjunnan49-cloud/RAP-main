"""Hash-lock C2 acceptance correction before corrected outputs."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import c2_feature_channel as c2

BASE = c2.BASE


def main():
    assert not (BASE / "amendment_02_freeze.json").exists()
    assert not (BASE / "outcomes_v3.json").exists()
    assert not (BASE / "summary_v3.json").exists()
    c2.verify()
    assert g0.read(BASE / "validation_v2.json")["passed"]
    files = [BASE / "PROTOCOL.md", BASE / "AMENDMENT_01.md", BASE / "AMENDMENT_02.md",
             BASE / "freeze.json", BASE / "amendment_freeze.json",
             BASE / "bank.json", BASE / "bank_seal.json", BASE / "outcomes.json",
             BASE / "summary.json", BASE / "validation_v2.json",
             Path(__file__).resolve(),
             Path(__file__).resolve().parent / "c2_correct_acceptance_v3.py",
             Path(__file__).resolve().parent / "validate_c2_acceptance_v3.py"]
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "amendment_02_freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "reason": "N0 true acceptance must bind to F2 gate N generation0, not selected R4",
        "files": {str(p): g0.sha(p) for p in files},
    })
    print("C2 acceptance amendment frozen", len(files), flush=True)


if __name__ == "__main__":
    main()
