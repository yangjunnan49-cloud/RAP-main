"""Hash-lock C2 amendment before the summary is finalized."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import c2_feature_channel as c2

BASE = c2.BASE


def main():
    assert not (BASE / "amendment_freeze.json").exists()
    assert not (BASE / "summary.json").exists()
    assert (BASE / "INCOMPLETE").exists()
    c2.verify()
    seal = g0.read(BASE / "bank_seal.json")
    assert g0.sha(BASE / "bank.json") == seal["sha256"]
    files = [BASE / "PROTOCOL.md", BASE / "AMENDMENT_01.md",
             BASE / "freeze.json", BASE / "bank.json", BASE / "bank_seal.json",
             BASE / "outcomes.json", Path(__file__).resolve(),
             Path(c2.__file__).resolve(),
             Path(__file__).resolve().parent / "validate_c2_feature_channel.py",
             Path(__file__).resolve().parent / "c2_evaluate_v2.py",
             Path(__file__).resolve().parent / "validate_c2_feature_channel_v2.py"]
    assert all(p.is_file() for p in files)
    g0.save_new(BASE / "amendment_freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "files": {str(p): g0.sha(p) for p in files},
        "reason": "fixed-index ordinary count seven, absolute response threshold six retained",
    })
    print("C2 amendment frozen", len(files), "files", flush=True)


if __name__ == "__main__":
    main()
