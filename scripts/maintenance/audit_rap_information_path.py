"""Read-only RAP source/weight identity audit; never unpickles checkpoint."""
from __future__ import annotations

import hashlib
import json
import pickletools
import sys
import zipfile
from pathlib import Path

import hydra

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SLAM = ROOT.parent / "RAP-SLAM"
OUT = ROOT / "docs/maintenance/2026-09-29/rap-information-path-audit-01"
CKPT = ROOT / "weights/rap_model_12.ckpt"


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    sources = [Path(__file__), ROOT / "README.md", ROOT / "demo.py",
               ROOT / "config/RAP_inference.yaml", ROOT / "config/model/rap_12.yaml",
               ROOT / "config/model/flow_model/point_cloud_dit_12.yaml",
               ROOT / "dataset_process/extract_sample_features.py",
               ROOT / "rectified_point_flow/data/dataset.py",
               ROOT / "rectified_point_flow/modeling.py",
               ROOT / "rectified_point_flow/flow_model/point_cloud_dit.py",
               ROOT / "rectified_point_flow/flow_model/layer.py",
               ROOT / "rectified_point_flow/flow_model/embedding.py",
               ROOT / "rectified_point_flow/utils/checkpoint.py",
               SLAM / "rap_slam/rap_backend.py",
               SLAM / "scripts/structured_motion_dev.py",
               CKPT, ROOT / "weights/mini_spinnet_t.pth"]
    with hydra.initialize_config_dir(config_dir=str(ROOT / "config"), version_base="1.3"):
        cfg = hydra.compose(config_name="RAP_inference", overrides=["model=rap_12",
            "model.inference_sampling_steps=5", "model.rigidity_forcing=true",
            "model.n_generations=1", "model.save_results=false"])
    model = hydra.utils.instantiate(cfg.model)
    expected = set(model.state_dict().keys())
    with zipfile.ZipFile(CKPT) as z:
        names = [n for n in z.namelist() if n.endswith("/data.pkl")]
        assert len(names) == 1
        # pickletools only parses opcode bytes; it does not instantiate objects.
        tokens = [arg for op, arg, _ in pickletools.genops(z.read(names[0]))
                  if isinstance(arg, str)]
    stored = set(t for t in tokens if t.startswith("flow_model."))
    layer_ids = sorted({int(t.split(".")[2]) for t in stored
                        if t.startswith("flow_model.transformer_layers.")
                        and t.split(".")[2].isdigit()})
    result = {
        "scope": "read-only local RAP information path identity audit",
        "checkpoint_parse": "zipfile + pickletools opcode strings only; no unpickle or execution",
        "file_sha256": {str(p): sha(p) for p in sources},
        "checkpoint_bytes": CKPT.stat().st_size,
        "config_flow_layers": int(cfg.model.flow_model.num_layers),
        "config_flow_embed_dim": int(cfg.model.flow_model.embed_dim),
        "config_local_feat_dim": int(cfg.model.flow_model.local_feat_dim),
        "config_scale_emb_on": bool(cfg.model.flow_model.scale_emb_on),
        "config_local_feat_concat_on": bool(cfg.model.flow_model.local_feat_concat_on),
        "model_state_keys": len(expected),
        "checkpoint_flow_strings": len(stored),
        "matched_expected_key_strings": len(expected & stored),
        "checkpoint_layer_indices": layer_ids,
        "missing_expected_key_strings": sorted(expected-stored),
        "limitation": "Pickle opcode strings also contain module paths; this is a name-presence check only, not tensor shape/value, strict loading or training provenance validation.",
    }
    assert layer_ids == list(range(12))
    assert not expected - stored
    out = OUT / "source_identity_audit.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: result[k] for k in ("model_state_keys", "checkpoint_flow_strings",
          "matched_expected_key_strings", "checkpoint_layer_indices",
          "missing_expected_key_strings")})


if __name__ == "__main__":
    main()
