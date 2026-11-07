"""Post-hoc, read-only F2 error-axis audit for strategy planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

MAIN = Path(__file__).resolve().parents[2]
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
OUT = MAIN / "docs/maintenance/2026-09-28/strategy-decision-01/error_axes.json"
GT = {
    "00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
    "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUT.exists()
    files = [Path(__file__).resolve()]
    result = {"scope": "post-hoc observed development; source-frame error vector, no method selection", "sequences": {}}
    for seq in ("00", "08"):
        files += [F2 / seq / "records.json", F2 / seq / "evaluator_only_decisions.json", GT[seq]]
        records = read(F2 / seq / "records.json")
        decisions = read(F2 / seq / "evaluator_only_decisions.json")
        gt = np.load(GT[seq], allow_pickle=False)
        rows = []
        for old in decisions:
            pair = f'{seq}_{old["source_i"]}_{old["source_j"]}'
            n = old["methods"]["N"]
            selected = [r for r in records if r["pair"] == pair and r["arm"] == "N" and r["generation"] == n["generation"]]
            assert len(selected) == 1
            truth = np.linalg.inv(gt[old["source_i"]]) @ gt[old["source_j"]]
            error = np.linalg.inv(truth) @ np.asarray(selected[0]["T"])
            v = error[:3, 3]
            assert abs(np.linalg.norm(v) - n["RTE_m"]) < 1e-6
            rows.append({"pair": pair, "stratum": old["stratum"], "native_K4_unavailable": not old["methods"]["N-OR4"]["strict"],
                         "native_incorrect_accepted": n["incorrect_accepted"],
                         "source_frame_translation_error_xyz_m": v.tolist(), "RTE_m": float(np.linalg.norm(v)),
                         "RRE_deg": n["RRE_deg"]})
        groups = {}
        for name, subset in {
            "K4_unavailable_positive": [r for r in rows if r["stratum"] != "confuser" and r["native_K4_unavailable"]],
            "incorrect_accepted": [r for r in rows if r["native_incorrect_accepted"]],
        }.items():
            v = np.asarray([r["source_frame_translation_error_xyz_m"] for r in subset])
            groups[name] = {"count": len(subset), "median_abs_xyz_m": np.median(np.abs(v), axis=0).tolist(),
                            "mean_xyz_m": np.mean(v, axis=0).tolist(),
                            "largest_abs_axis_counts_xyz": np.bincount(np.argmax(np.abs(v), axis=1), minlength=3).tolist(),
                            "RTE_le_2m": sum(r["RTE_m"] <= 2 for r in subset),
                            "RRE_le_5deg": sum(r["RRE_deg"] <= 5 for r in subset)}
        result["sequences"][seq] = {"groups": groups, "rows": rows}
    result["input_sha256"] = {str(p): sha(p) for p in files}
    with OUT.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print({s: v["groups"] for s, v in result["sequences"].items()})


if __name__ == "__main__":
    main()
