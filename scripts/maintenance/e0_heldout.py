"""Fixed E0 O/A and KISS-SLAM held-out-system confirmation orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / "RAP-SLAM"
DATA = MAIN.parent / "Datasets/data_odometry_velodyne/dataset"
BASE = MAIN / "docs/maintenance/2026-09-27/e0-heldout-01"
E0 = MAIN / "docs/maintenance/2026-09-26/e0-frontend-01"
HC = MAIN / "docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam"
COUNTS = {"07": 1101, "09": 1591, "10": 1201}
KISS = Path("/root/venvs/kiss-slam-hc1/bin/kiss_slam_pipeline")
KISS_PIP = Path("/root/venvs/kiss-slam-hc1/bin/pip")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_new(path: Path, obj) -> None:
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def local_e0_path(wsl_path: str) -> Path:
    assert "/githouse/" in wsl_path
    return MAIN.parent / wsl_path.split("/githouse/", 1)[1]


def source_files() -> list[Path]:
    old = read(E0 / "freeze.json")["sources"]
    paths = []
    for name, expected in old.items():
        path = local_e0_path(name)
        assert sha256(path) == expected, f"E0 source changed: {path}"
        paths.append(path)
    paths += [
        Path(__file__).resolve(),
        MAIN / "scripts/maintenance/validate_e0_heldout.py",
        BASE / "PROTOCOL.md",
        E0 / "development_baseline_v2.json",
        E0 / "freeze.json",
        HC / "config/default_config.yaml",
        HC / "env/pip_freeze.txt",
    ]
    return sorted(set(paths))


def input_files() -> list[Path]:
    files = []
    for seq, n in COUNTS.items():
        directory = DATA / "sequences" / seq
        scans = sorted((directory / "velodyne").glob("*.bin"))
        assert len(scans) == n
        assert [p.name for p in scans] == [f"{i:06d}.bin" for i in range(n)]
        files.extend(scans)
        files.extend((DATA / "poses" / f"{seq}.txt", directory / "calib.txt", directory / "times.txt"))
    return files


def freeze() -> None:
    assert not (BASE / "freeze.json").exists()
    assert KISS.is_file() and KISS_PIP.is_file()
    installed = subprocess.check_output([str(KISS_PIP), "freeze"], text=True)
    archived = (HC / "env/pip_freeze.txt").read_text(encoding="utf-8")
    assert installed.strip().splitlines() == archived.strip().splitlines(), "KISS environment changed"
    sources = {str(p): sha256(p) for p in source_files()}
    inputs = {str(p): sha256(p) for p in input_files()}
    save_new(BASE / "freeze.json", {
        "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "E0-H1: 07/09/10 held out from E0 selection; earlier data-only exposure declared",
        "sources": sources,
        "inputs": inputs,
        "e0_source_identity_equal": True,
        "kiss_environment_equal_hc": True,
    })
    print(f"freeze: {len(sources)} sources, {len(inputs)} inputs", flush=True)


def check_freeze(raw: bool = False) -> None:
    frozen = read(BASE / "freeze.json")
    for name, expected in frozen["sources"].items():
        assert sha256(Path(name)) == expected, f"source changed: {name}"
    if raw:
        for name, expected in frozen["inputs"].items():
            assert sha256(Path(name)) == expected, f"input changed: {name}"


def command(seq: str, arm: str) -> list[str]:
    cmd = read(E0 / "command-00.json")
    def replace_after(option: str, value: str) -> None:
        cmd[cmd.index(option) + 1] = value
    replace_after("--output", str(BASE / f"full-{seq}-{arm}"))
    replace_after("--real-seq", seq)
    replace_after("--real-end", str(COUNTS[seq] - 1))
    cmd = [("--apply-kitti-205" if arm == "A" else "--no-apply-kitti-205")
           if x in ("--apply-kitti-205", "--no-apply-kitti-205") else x for x in cmd]
    assert cmd[cmd.index("--output") + 1].endswith(f"full-{seq}-{arm}")
    return cmd


def run() -> None:
    check_freeze()
    marker = BASE / "INCOMPLETE"
    marker.write_text("E0-H1 running\n", encoding="utf-8")
    started = time.monotonic()
    for seq in COUNTS:
        for arm in ("O", "A"):
            assert time.monotonic() - started < 7200
            dest = BASE / f"full-{seq}-{arm}"
            assert not dest.exists()
            cmd = command(seq, arm)
            save_new(BASE / f"command-{seq}-{arm}.json", cmd)
            with (BASE / f"full-{seq}-{arm}.log").open("x", encoding="utf-8") as log:
                subprocess.run(cmd, cwd=SLAM, stdout=log, stderr=subprocess.STDOUT,
                               timeout=max(1, 7200 - (time.monotonic() - started)), check=True)
            print(f"full {seq} {arm} complete", flush=True)
        run_dir = BASE / f"kiss-{seq}"
        run_dir.mkdir(exist_ok=False)
        cmd = [str(KISS), str(DATA), "--dataloader", "kitti", "--sequence", seq]
        save_new(BASE / f"command-kiss-{seq}.json", cmd)
        with (BASE / f"kiss-{seq}.log").open("x", encoding="utf-8") as log:
            subprocess.run(cmd, cwd=run_dir, stdout=log, stderr=subprocess.STDOUT,
                           timeout=max(1, 7200 - (time.monotonic() - started)), check=True)
        poses = list(run_dir.rglob(f"{seq}_poses_kitti.txt"))
        assert len(poses) == 1, poses
        save_new(BASE / f"kiss-{seq}-pose.json", {"path": str(poses[0]), "sha256": sha256(poses[0])})
        print(f"kiss {seq} complete", flush=True)
    save_new(BASE / "execution.json", {
        "wall_s": time.monotonic() - started,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    })
    check_freeze(raw=True)
    print("all trajectories complete; independent evaluation pending", flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
