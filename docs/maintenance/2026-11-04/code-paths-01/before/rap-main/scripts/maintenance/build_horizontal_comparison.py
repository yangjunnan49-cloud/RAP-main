"""HC-V1 horizontal comparison table builder (descriptive, CPU-only).

Builds COMPARISON_TABLE_V1.md + comparison_v1.json for
docs/maintenance/2026-09-19/horizontal-comparison-01/ from:

  - our canonical numbers: core-baseline-v1 registry (2026-09-11 frozen
    full reruns, budget-12 defaults, no intrinsic angle correction);
  - ter/rer literature: RAP-SLAM/data/literature/kitti_baselines.json
    (read-only; transcribed 2026-08-22 with source labels);
  - aligned-ATE literature: PIN-SLAM T-RO Table IV verbatim transcription
    (this directory's data-literature/kitti_ate_pin_slam_tab4.json);
  - optional same-data external runs: b-kiss-slam/eval_results.json when
    present (added by part B; the builder is deterministic given inputs).

It never edits any input. Run from anywhere:

    python scripts/maintenance/build_horizontal_comparison.py
"""
import json
import sys
from pathlib import Path

RAP_MAIN = Path(__file__).resolve().parents[2]
HC_DIR = RAP_MAIN / "docs" / "maintenance" / "2026-09-19" / "horizontal-comparison-01"
REGISTRY = RAP_MAIN / "docs" / "maintenance" / "2026-09-11" / "core-baseline-v1" / "registry.json"
LIT_TER = RAP_MAIN.parent / "RAP-SLAM" / "data" / "literature" / "kitti_baselines.json"
LIT_ATE = HC_DIR / "data-literature" / "kitti_ate_pin_slam_tab4.json"
EXTERNAL_RESULTS = HC_DIR / "b-kiss-slam" / "eval_results.json"
P0_PAPER_METRICS = RAP_MAIN.parent / "RAP-SLAM" / "output_paper_metrics" / "paper_metrics.json"

CORE_SEQS = ["00", "05", "06"]          # our core-baseline coverage on KITTI
ALL_SEQS = [f"{i:02d}" for i in range(11)]
LOOP_SEQS = ["00", "02", "05", "06", "07", "08", "09"]


def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def fmt(v, nd=2, dash="–"):
    return dash if v is None else f"{v:.{nd}f}"


def load_inputs():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    lit_ter = json.loads(LIT_TER.read_text(encoding="utf-8"))
    lit_ate = json.loads(LIT_ATE.read_text(encoding="utf-8"))
    external = None
    if EXTERNAL_RESULTS.exists():
        external = json.loads(EXTERNAL_RESULTS.read_text(encoding="utf-8"))
    p0 = None
    if P0_PAPER_METRICS.exists():
        p0 = json.loads(P0_PAPER_METRICS.read_text(encoding="utf-8"))
    return registry, lit_ter, lit_ate, external, p0


def ours_by_seq(registry):
    """sequence label ('00'/'05'/'06'/'POSS-A') -> registry entry."""
    out = {}
    for e in registry["sequences"]:
        name = e["sequence"]  # poss / kitti06 / kitti05 / kitti00
        key = "POSS-A" if name == "poss" else name[-2:]
        out[key] = e
    return out


def build_comparison_json(registry, lit_ter, lit_ate, external, p0):
    ours = ours_by_seq(registry)

    def our_metric(seq, block, field):
        e = ours.get(seq)
        if e is None:
            return None
        return e[block].get(field)

    # --- Table 1/2: KITTI drift (camera frame for ours, literature as printed)
    drift_rows = []
    for name, m in lit_ter["methods"].items():
        row = {"method": name, "full": m["full"], "type": m["type"],
               "source": m["source"]}
        if "ter" in m:
            row["ter"] = m["ter"]
            row["ter_mean_core"] = mean([m["ter"][ALL_SEQS.index(s)] for s in CORE_SEQS])
        if "rer" in m:
            row["rer"] = m["rer"]
            row["rer_mean_core"] = mean([m["rer"][ALL_SEQS.index(s)] for s in CORE_SEQS])
        drift_rows.append(row)
    for label, block in (("ours odometry (core-baseline-v1)", "camera_odometry"),
                         ("ours full (core-baseline-v1)", "camera_pgo")):
        drift_rows.append({
            "method": label, "full": "RAP-SLAM corrected core baseline v1 "
            "(KISS-ICP POSS-tuned front-end + SC/proximity retrieval + RAP K=4 "
            "verification + relfloor+Huber PGO; no intrinsic angle correction)",
            "type": "slam" if "full" in label else "odometry",
            "source": "core-baseline-v1 registry (2026-09-11)",
            "ours": True,
            "ter": [our_metric(s, block, "kitti_ter_pct") if s in CORE_SEQS else None
                    for s in ALL_SEQS],
            "rer": [our_metric(s, block, "kitti_rer_deg100m") if s in CORE_SEQS else None
                    for s in ALL_SEQS],
            "ter_mean_core": mean([our_metric(s, block, "kitti_ter_pct") for s in CORE_SEQS]),
            "rer_mean_core": mean([our_metric(s, block, "kitti_rer_deg100m") for s in CORE_SEQS]),
        })

    if external is not None:
        short = external.get("short_label", external["method_label"])
        for run in external["runs"]:
            drift_rows.append({
                "method": short,
                "method_full": external["method_label"],
                "source": external["provenance"],
                "same_data_run": True,
                "type": "slam",
                "ter": [run["sequences"].get(s, {}).get("kitti_ter_pct")
                        if s in CORE_SEQS else None for s in ALL_SEQS],
                "rer": [run["sequences"].get(s, {}).get("kitti_rer_deg100m")
                        if s in CORE_SEQS else None for s in ALL_SEQS],
                "ter_mean_core": mean([run["sequences"].get(s, {}).get("kitti_ter_pct")
                                       for s in CORE_SEQS]),
                "rer_mean_core": mean([run["sequences"].get(s, {}).get("kitti_rer_deg100m")
                                       for s in CORE_SEQS]),
            })

    # --- Table 3: aligned ATE (Umeyama) — PIN-SLAM Tab. IV family + ours
    idx = {s: i for i, s in enumerate(lit_ate["seqs"])}
    ate_rows = []
    for name, m in lit_ate["methods"].items():
        ate_rows.append({
            "method": name + (" \u2021" if m["offline_pgo"] else ""),
            "source": lit_ate["source"],
            "ate": m["ate"],
            "avg_loops_printed": m["avg_loops"],
            "avg_printed": m["avg"],
            "ate_mean_core": mean([m["ate"][idx[s]] for s in CORE_SEQS]),
            "printed_precision": "decimeter",
        })
    ours_ate = {"method": "ours full (core-baseline-v1)",
                "source": "core-baseline-v1 registry (2026-09-11)",
                "ours": True, "printed_precision": "full precision",
                "ate": [our_metric(s, "pgo", "ape_aligned_rmse") if s in CORE_SEQS
                        else None for s in ALL_SEQS],
                "ate_mean_core": mean([our_metric(s, "pgo", "ape_aligned_rmse")
                                       for s in CORE_SEQS])}
    ate_rows.append(ours_ate)
    ate_rows.append({
        "method": "ours odometry (core-baseline-v1)",
        "source": "core-baseline-v1 registry (2026-09-11)",
        "ours": True, "printed_precision": "full precision",
        "ate": [our_metric(s, "odometry", "ape_aligned_rmse") if s in CORE_SEQS
                else None for s in ALL_SEQS],
        "ate_mean_core": mean([our_metric(s, "odometry", "ape_aligned_rmse")
                               for s in CORE_SEQS])})
    if external is not None:
        short = external.get("short_label", external["method_label"])
        for run in external["runs"]:
            row = {"method": short,
                   "method_full": external["method_label"],
                   "source": external["provenance"],
                   "same_data_run": True, "printed_precision": "full precision",
                   "ate": [run["sequences"].get(s, {}).get("ape_aligned_rmse")
                           for s in ALL_SEQS],
                   "ate_mean_core": mean([run["sequences"].get(s, {}).get("ape_aligned_rmse")
                                          for s in CORE_SEQS])}
            ate_rows.append(row)
    # flagged legacy context rows (live products, same metric code; 02 has loops)
    context = []
    if p0 is not None:
        live = p0.get("live", {})
        for seq, key in (("01", "step3_kitti01"), ("02", "step3_kitti02_current"),
                         ("03", "step3_kitti03"), ("04", "step3_kitti04")):
            entry = live.get(key, {}).get("pgo")
            if entry:
                context.append({"seq": seq, "product": key,
                                "ape_aligned_rmse": entry["ape_aligned_rmse"],
                                "note": "legacy live product, no true revisits"
                                        if seq in ("01", "03", "04") else
                                        "legacy live product, current-backend PGO rerun"})
    poss = ours.get("POSS-A")
    poss_block = None
    if poss is not None:
        poss_block = {
            "odometry_aligned": poss["odometry"]["ape_aligned_rmse"],
            "full_aligned": poss["pgo"]["ape_aligned_rmse"],
            "odometry_unaligned": poss["odometry"]["ape_unaligned_rmse"],
            "full_unaligned": poss["pgo"]["ape_unaligned_rmse"],
            "loops_accepted": poss["accepted"],
            "frames": poss["frames"],
            "note": "POSS (PKU campus, Velodyne-32e): no published baseline; "
                    "cross-sensor generalization set, LiDAR-frame drift in registry.",
        }
    return {
        "conventions": {
            "ter": "KITTI official all-segment mean relative translational drift "
                   "[%], 100-800 m subsegments (M2 v2 protocol); camera reference "
                   "frame for our KITTI rows; literature rows as printed by their "
                   "sources (MULLS family applies 0.2 deg and CT-ICP 0.205 deg "
                   "intrinsic angle correction; we apply none).",
            "rer": "rotational drift [deg/100 m], same protocol.",
            "ate": "APE translation RMSE [m] after SE(3) Umeyama alignment "
                   "(evo --align convention = PIN-SLAM Table IV convention). "
                   "Unaligned first-pose-anchored APE is reported separately in "
                   "the registry and never mixed into this table.",
            "mean_core": "mean over sequences 00/05/06 (our core-baseline "
                         "coverage), recomputed from the row values.",
        },
        "drift_rows": drift_rows,
        "ate_rows": ate_rows,
        "kitti_context_rows": context,
        "poss": poss_block,
        "coverage_note": "Core claims are limited to KITTI 00/05/06 (+POSS-A); "
                         "literature 00-10 averages are quoted verbatim and are "
                         "not same-coverage comparisons.",
    }


def render_md(data, lit_ate):
    out = []
    out.append("# RAP-SLAM horizontal comparison v1 (HC-V1)")
    out.append("")
    out.append("Ours: corrected core baseline v1 (2026-09-11 frozen full reruns, "
               "budget-12 defaults, no intrinsic angle correction). Front-end: "
               "KISS-ICP with a single POSS-tuned config (max_range 80 m, "
               "min_range 1.5 m, voxel 0.8 m) — weaker than published KISS-ICP. "
               "Full system adds Scan Context + proximity retrieval, RAP K=4 "
               "generative verification (overlap >= 0.7 & mean_dist <= 2.5 m), "
               "loop-edge NMS (w=10), relfloor+Huber GTSAM PGO.")
    out.append("")
    out.append("Coverage: our core-baseline sequences are KITTI 00/05/06 "
               "(+POSS-A). Literature 00–10 averages are verbatim quotes, not "
               "same-coverage comparisons; the `mean 00/05/06` column is "
               "recomputed over exactly those three sequences for every row.")
    out.append("")

    # --- Table 1 ter
    out.append("## Table 1 — KITTI relative translational drift ter [%] "
               "(camera frame; per sequence)")
    out.append("")
    header = "| method | " + " | ".join(ALL_SEQS) + " | mean 00/05/06 |"
    out.append(header)
    out.append("|" + "---|" * (len(ALL_SEQS) + 2))
    for r in data["drift_rows"]:
        if "ter" not in r:
            note = r["method"]
            out.append(f"| {note} (no per-seq ter) |" + " – |" * (len(ALL_SEQS) + 1))
            continue
        name = f"**{r['method']}**" if r.get("ours") or r.get("same_data_run") \
               else r["method"]
        cells = [fmt(v) for v in r["ter"]]
        bold = r.get("ours") or r.get("same_data_run")
        out.append(f"| {name} | " + " | ".join(cells) +
                   f" | **{fmt(r['ter_mean_core'])}** |" if bold
                   else f"| {name} | " + " | ".join(cells) +
                        f" | {fmt(r['ter_mean_core'])} |")
    out.append("")
    out.append("Literature sources and correction conventions: see "
               "`RAP-SLAM/data/literature/kitti_baselines.json` (accessed "
               "2026-08-22). ter is a local (<=800 m) drift metric; loop closure "
               "mainly improves global consistency (Table 3).")
    out.append("")

    # --- Table 2 rer
    out.append("## Table 2 — KITTI relative rotational drift rer [deg/100 m]")
    out.append("")
    out.append(header)
    out.append("|" + "---|" * (len(ALL_SEQS) + 2))
    for r in data["drift_rows"]:
        if "rer" not in r:
            continue
        name = f"**{r['method']}**" if r.get("ours") or r.get("same_data_run") \
               else r["method"]
        cells = [fmt(v) for v in r["rer"]]
        out.append(f"| {name} | " + " | ".join(cells) +
                   f" | {fmt(r['rer_mean_core'])} |")
    out.append("")

    # --- Table 3 aligned ATE
    out.append("## Table 3 — Global consistency: aligned ATE RMSE [m] "
               "(SE(3) Umeyama, evo `--align`)")
    out.append("")
    out.append("Literature rows are the verbatim PIN-SLAM T-RO 2024 Table IV "
               "family (decimeter precision, motion-compensated clouds; "
               "\u2021 = offline PGO; PIN-LO/PIN-SLAM are 10-run means). "
               "Their printed `Avg.*` (loop sequences) and `Avg.` columns are "
               "quoted verbatim after the per-sequence cells.")
    out.append("")
    out.append("| method | " + " | ".join(ALL_SEQS) +
               " | mean 00/05/06 | Avg.* (printed) | Avg. (printed) |")
    out.append("|" + "---|" * (len(ALL_SEQS) + 4))
    for r in data["ate_rows"]:
        name = f"**{r['method']}**" if r.get("ours") or r.get("same_data_run") \
               else r["method"]
        cells = [fmt(v) for v in r["ate"]]
        out.append(f"| {name} | " + " | ".join(cells) +
                   f" | {fmt(r['ate_mean_core'])} | " +
                   f"{fmt(r.get('avg_loops_printed'))} | "
                   f"{fmt(r.get('avg_printed'))} |")
    out.append("")
    out.append("Known transcription notes (kept verbatim, not corrected): "
               + "; ".join(lit_ate["known_transcription_notes"]))
    out.append("")
    if data["kitti_context_rows"]:
        out.append("### Flagged context rows (legacy live products, same metric "
                   "code; NOT core-baseline)")
        out.append("")
        out.append("| seq | product | aligned ATE [m] | note |")
        out.append("|---|---|---|---|")
        for c in data["kitti_context_rows"]:
            out.append(f"| {c['seq']} | {c['product']} | "
                       f"{fmt(c['ape_aligned_rmse'])} | {c['note']} |")
        out.append("")
    if data["poss"]:
        p = data["poss"]
        out.append("### POSS-A (ours only; no published baseline)")
        out.append("")
        out.append(f"frames {p['frames']}, loops accepted {p['loops_accepted']}; "
                   f"aligned ATE odometry {p['odometry_aligned']:.6f} -> "
                   f"full {p['full_aligned']:.6f} m; unaligned APE "
                   f"{p['odometry_unaligned']:.6f} -> {p['full_unaligned']:.6f} m. "
                   + p["note"])
        out.append("")
    return "\n".join(out)


def main():
    registry, lit_ter, lit_ate, external, p0 = load_inputs()
    data = build_comparison_json(registry, lit_ter, lit_ate, external, p0)
    md = render_md(data, lit_ate)
    (HC_DIR / "comparison_v1.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (HC_DIR / "COMPARISON_TABLE_V1.md").write_text(md, encoding="utf-8")
    print(f" wrote {HC_DIR / 'COMPARISON_TABLE_V1.md'}")
    print(f" wrote {HC_DIR / 'comparison_v1.json'}")
    print(f" drift rows: {len(data['drift_rows'])}, ate rows: {len(data['ate_rows'])}, "
          f"external: {'yes' if external else 'no'}")


if __name__ == "__main__":
    sys.exit(main())
