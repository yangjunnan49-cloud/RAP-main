"""Build a provenance registry from the verified M0 snapshot, never guessed logs."""
import ast
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = ROOT / ".maintenance-archive/2026-09-09-m0"
OUT = ROOT / "docs/maintenance/2026-09-09"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace-generated", action="store_true",
                        help="Replace only the derived registry, never archived inputs")
    args = parser.parse_args()
    if (SNAP / "INCOMPLETE").exists():
        raise RuntimeError("Snapshot is incomplete")
    manifest = json.loads((SNAP / "manifest.json").read_text())
    summary = json.loads((SNAP / "summary.json").read_text())
    by_path = {r["archived_path"]: r for r in manifest}
    def artifact(rel):
        r = by_path[f"files/RAP-SLAM/{rel}"]
        return {"source": r["source"], "archive": r["archived_path"],
                "sha256": r["sha256"], "bytes": r["bytes"]}
    script = SNAP / "files/RAP-SLAM/scripts/eval_calibrated_weighting.py"
    node = next(n for n in ast.parse(script.read_text()).body
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GOLDENS" for t in n.targets))
    goldens = ast.literal_eval(node.value)
    audit = json.loads((SNAP / "files/original-audit/audit_results.json").read_text())
    runs = []
    for name, (odom, kfs, loops, source, seq, nms) in goldens.items():
        summary_rel = str(Path(odom).parent / "summary.json")
        sp = SNAP / "files/RAP-SLAM" / summary_rel
        saved = json.loads(sp.read_text()) if sp.exists() else None
        config = saved.get("config") if saved else None
        r = {"run_id": f"legacy-{name}", "status": "preserved_legacy_not_repaired",
             "source_registry": "scripts/eval_calibrated_weighting.py:GOLDENS at 6d3f2d2",
             "trajectory": artifact(odom), "keyframes": artifact(kfs), "edges": artifact(loops),
             "saved_config": config, "saved_config_artifact": artifact(summary_rel) if saved else None,
             "physical_dataset": "POSS" if name.startswith("poss") else "KITTI",
             "physical_sequence": config.get("real_seq") if config else ("00" if source == "poss" else seq),
             "source_frame_range": [config.get("real_start"), config.get("real_end")] if config else None,
             "source_frame_stride": config.get("real_stride") if config else None,
             "source_id_provenance": "configured range; no persisted per-frame identity certificate" if config else "unknown: live files use arrival indices; full source mapping not persisted",
             "historical_inference_commit": None, "historical_checkpoint_sha256": None,
             "historical_environment_lock": None,
             "historical_seed": config.get("seed") if config else None,
             "maintenance_replay": {"code_head": summary["RAP-SLAM"]["head"],
                 "method": "saved edges and odometry, no RAP inference rerun",
                 "loop_weighting": "relfloor", "robust_kernel": "huber", "nms_width": nms,
                 "metric": "first-pose-normalized APE RMSE in meters",
                 "evidence": audit["goldens"][name]},
             "paper_use": "legacy reference only until affected geometry and evaluation findings are resolved"}
        runs.append(r)
    groups = {}
    for r in manifest:
        parts = Path(r["archived_path"]).parts
        if len(parts) > 3 and parts[1] == "RAP-SLAM" and parts[2].startswith("output"):
            g = groups.setdefault(parts[2], {"files": 0, "bytes": 0})
            g["files"] += 1
            g["bytes"] += r["bytes"]
    historical_configs = []
    for r in manifest:
        if r["archived_path"].startswith("files/RAP-SLAM/output") and r["archived_path"].endswith("/summary.json"):
            obj = json.loads((SNAP / r["archived_path"]).read_text())
            if isinstance(obj, dict) and isinstance(obj.get("config"), dict):
                historical_configs.append({"artifact": r["archived_path"], "sha256": r["sha256"],
                                           "config": obj["config"], "protocol_status": "historical_config_not_inferred_from_current_defaults"})
    checkpoints = [{**r, "training_membership": "unknown", "historical_run_binding": "unknown",
                    "provenance": "local installed file; download recipe in historical handoff is not proof of exact training membership"}
                   for r in manifest if r["archived_path"].startswith("files/weights/")
                   and Path(r["archived_path"]).suffix in (".ckpt", ".pth", ".pt", ".safetensors")]
    record = {"schema_version": 1, "snapshot": str(SNAP), "snapshot_summary": summary,
              "null_semantics": "unknown or not persisted; never inferred from a current default",
              "golden_runs": runs, "output_artifact_inventory": groups,
              "inventory_note": "Output directory groups are artifact collections, not necessarily independent runs; all file identities are in preservation_manifest.json",
              "historical_config_records": historical_configs, "checkpoints": checkpoints,
              "remaining_provenance_work": ["recover live source timestamps/frame IDs if evidence exists",
                  "bind historical inference commits, exact checkpoint hashes and seeds where recoverable",
                  "define a repaired paper protocol after M2/M3; do not treat saved mixed protocols as one method"]}
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "experiment_registry.json").open("w" if args.replace_generated else "x") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    print(json.dumps({"goldens": len(runs), "artifact_groups": len(groups),
                      "saved_configs": len(historical_configs), "checkpoints": len(checkpoints)}))


if __name__ == "__main__":
    main()
