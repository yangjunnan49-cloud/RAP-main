"""Read-only, safe-tensor audit of the RAP miniSpinNet checkpoint."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import torch


MAIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIN / "dataset_process"))
from utils.spinnet.patch_embedder import MiniSpinNet  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    checkpoint = MAIN / "weights" / "mini_spinnet_t.pth"
    output = (
        MAIN
        / "docs/maintenance/2026-09-28/conditioning-source-audit-01"
        / "checkpoint_audit.json"
    )
    if output.exists():
        raise FileExistsError(output)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(state, dict):
        raise TypeError(type(state))
    desc = {key[5:]: value for key, value in state.items() if key.startswith("Desc.")}
    model = MiniSpinNet(
        des_r=5.0, num_points_per_patch=512, is_aligned_to_global_z=True
    )
    expected = model.state_dict()
    absent = sorted(set(expected) - set(desc))
    excess = sorted(set(desc) - set(expected))
    wrong_shape = sorted(
        key for key in set(desc) & set(expected)
        if tuple(desc[key].shape) != tuple(expected[key].shape)
    )
    nonfinite = sorted(
        key for key, value in desc.items()
        if not bool(torch.isfinite(value).all())
    )
    if absent or excess or wrong_shape or nonfinite:
        raise AssertionError((absent, excess, wrong_shape, nonfinite))
    model.load_state_dict(desc, strict=True)
    result = {
        "scope": "safe read-only miniSpinNet checkpoint identity audit",
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint),
        "checkpoint_total_keys": len(state),
        "checkpoint_desc_keys": len(desc),
        "model_keys": len(expected),
        "missing_keys": absent,
        "unexpected_keys": excess,
        "wrong_shape_keys": wrong_shape,
        "nonfinite_keys": nonfinite,
        "strict_load_passed": True,
        "weights_only": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
