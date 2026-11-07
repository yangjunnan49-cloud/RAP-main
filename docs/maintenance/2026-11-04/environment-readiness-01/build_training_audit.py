"""Record training-chain findings with current source hashes and AST line references."""
import ast
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def source(path, symbols=()):
    absolute = REPO / path
    raw = absolute.read_bytes()
    refs = {}
    if path.endswith(".py"):
        tree = ast.parse(raw.decode("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in symbols:
                refs.setdefault(node.name, []).append({"line": node.lineno, "end_line": node.end_lineno})
    return {"asset": "rap-main:" + path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "symbols": refs}


def main():
    references = [source("rectified_point_flow/modeling.py", ("training_step", "validation_step", "configure_optimizers", "on_save_checkpoint", "on_load_checkpoint", "loss", "_compute_flow_target")),
                  source("rectified_point_flow/data/datamodule.py", ("DynamicBatchSampler", "RandomSampledDataset", "setup", "train_dataloader", "on_train_epoch_start", "set_epoch")),
                  source("rectified_point_flow/data/dataset.py", ("_determine_split_type", "_load_fragments_from_folder", "_load_fragments_from_hdf5")),
                  source("rectified_point_flow/utils/checkpoint.py", ("load_checkpoint_for_module", "get_rng_state", "set_rng_state")),
                  source("rectified_point_flow/utils/training.py", ("setup_wandb_resume", "setup_loggers")),
                  source("rectified_point_flow/utils/optimizers.py", ("build_muon_with_aux_adam",)),
                  *[source(p) for p in ("sample.py", "config/RAP_inference.yaml", "config/trainer/main.yaml", "config/data/data_tmp.yaml", "config/loggers/wandb.yaml", "config/model/optimizer/muon.yaml")]]
    entries = [json.loads(line) for line in (REPO / "docs/code/ENTRYPOINTS.jsonl").read_text(encoding="utf-8").splitlines()]
    fit = []
    for entry in entries:
        if not entry["default_dispatch_allowed"]:
            continue
        root = REPO if entry["root"] == "rap-main" else REPO.parent / "RAP-SLAM"
        tree = ast.parse((root / entry["path"]).read_text(encoding="utf-8"))
        fit += [{"asset": entry["id"], "line": n.lineno} for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "fit"]
    assert fit == []
    findings = [
        {"id": "TRAIN_ENTRY_MISSING", "state": "BLOCKS_TRAINING_READINESS", "evidence": ["six maintained entry files have no fit calls", "sample.py executes trainer.test with checkpointing disabled"]},
        {"id": "TRAIN_ROOT_CONFIG_NOT_ADMITTED", "state": "BLOCKS_TRAINING_READINESS", "evidence": ["no maintained training root config", "your_dataset_name placeholders", "experiment_name interpolation required"]},
        {"id": "DATA_SPLIT_ADMISSION_PENDING_A5", "state": "BLOCKS_DATA_SPECIFIC_TRAINING", "evidence": ["standard/random fallback exists", "data provenance, membership, leakage and counts not examined in A4"]},
        {"id": "MUON_MISSING_UNPINNED", "state": "CONFIRMED_MISSING_DEFAULT_TRAINING_DEPENDENCY", "evidence": ["CPU_PROBE.json: muon_training_dependency ModuleNotFoundError", "Git source in old installer is unpinned"]},
        {"id": "WARM_START_NOT_RESUME", "state": "IMPLEMENTATION_AND_VALIDATION_REQUIRED", "evidence": ["checkpoint helper extracts state_dict only", "no Trainer.fit ckpt_path entry", "W&B ID is not optimizer/step restoration"]},
        {"id": "SAMPLER_EPOCH_AND_DDP", "state": "STATIC_RISK_NOT_RUNTIME_FAILURE_CLAIM", "evidence": ["custom rank sharding", "default seed=0 and drop_last=True", "RandomSampledDataset update occurs in custom DataModule epoch hook", "Lightning itself updates samplers; full interaction untested"]},
        {"id": "CHECKPOINT_MONITOR_TIMING", "state": "STATIC_RISK_REQUIRES_VALIDATION", "evidence": ["validation every 10 epochs", "save-on-train-epoch-end monitor configuration", "tiny fixture may yield zero batches with drop_last"]},
        {"id": "EXACT_RESUME_AND_TARGET", "state": "NOT_VALIDATED", "evidence": ["RNG hooks exist", "no tested worker/rank/sampler resume contract", "no GPU/model/training or clean rebuild execution in A4"]}
    ]
    result = {"training_chain_validated": False, "training_calls_performed": 0, "model_instances_created": 0,
              "maintained_entry_files_examined": 6, "fit_calls_in_maintained_entries": fit, "source_references": references,
              "findings": findings, "automatic_training_or_scientific_route_resumption_authorized": False,
              "separate_implementation_scope": "Dedicated training entry and root config; explicit fresh/warm-start/resume; data admission; pinned optimizer; optimizer/checkpoint/resume engineering validation"}
    (PHASE / "TRAINING_AUDIT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"findings": len(findings), "source_references": len(references), "fit_calls_in_maintained_entries": 0}))


if __name__ == "__main__":
    main()
