import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
report = ROOT / "docs/maintenance/2026-10-20/raw-input-contract-01"
rows = json.loads((report / "results06.json").read_text(encoding="utf-8"))["rows"]
seqs = ["00", "05", "06", "07", "09", "10"]
metrics = ["ate", "ter", "rer"]
means = {}
for mode in ["G", "K"]:
    means[mode] = {m: sum(r[m] for r in rows if r["mode"] == mode) / 18 for m in metrics}
print("MEANS", json.dumps(means, indent=2))
for m in metrics:
    print("MEAN_IMPROVEMENT", m, (means["K"][m] - means["G"][m]) / means["K"][m] * 100)
for seq in seqs:
    values = {}
    for m in metrics:
        g = sum(r[m] for r in rows if r["mode"] == "G" and r["sequence"] == seq) / 3
        k = sum(r[m] for r in rows if r["mode"] == "K" and r["sequence"] == seq) / 3
        values[m] = {"G": g, "K": k, "improvement_pct": (k-g)/k*100}
    print(seq, json.dumps(values))
ops = json.loads((report / "OPERATIONAL_RESULTS.json").read_text(encoding="utf-8"))["modes"]
for mode in ["G", "K"]:
    c = ops[mode]["summed_frame_clock_columns"]
    prep = sum(c[:3])
    native = c[3]
    total = c[4]
    print("CLOCK", mode, {"prep": prep, "native": native, "total": total, "prep_pct": prep/total*100, "native_pct": native/total*100})
print("P99_REDUCTION_TO_100MS", (137.36283260928756-100)/137.36283260928756*100)
print("E0H1_ATE", (1.2177-0.7215)/1.2177*100)
print("E0H1_TER", (0.9595-0.5056)/0.9595*100)
