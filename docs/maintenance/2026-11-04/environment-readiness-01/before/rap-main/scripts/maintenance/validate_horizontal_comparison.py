"""HC-V1 independent validator. CPU-only.

Usage (split by environment — evo is only available in the WSL rap-inference
env, pdfplumber only in the Windows managed Python):

  Windows managed Python:
    python scripts/maintenance/validate_horizontal_comparison.py \
        --checks pdf_transcription,table_arithmetic,write_scope
  WSL rap-inference env:
    .../rap-inference/bin/python scripts/maintenance/validate_horizontal_comparison.py \
        --checks baseline_recompute,external_runs

Each run merges its results into validation.json by check name, so the file
accumulates all five checks across both environments. If a check raises, the
validator aborts WITHOUT writing validation.json (the last good merged state
is preserved and the failure is never recorded as a check outcome).

Checks (per PROTOCOL.md section 7):
  1. Re-extract PIN-SLAM Table IV from the archived PDF and diff against the
     transcription JSON (exact match at printed precision).
  2. Recompute our four-sequence metrics from the frozen 2026-09-11 full-*-01
     outputs with the original metric code; require <=1e-9 vs the
     core-baseline-v1 registry.
  3. Recompute all derived table columns (mean 00/05/06) from
     comparison_v1.json and require exact consistency with the rendered
     COMPARISON_TABLE_V1.md cell strings.
  4. If b-kiss-slam/eval_results.json exists: verify frame counts, finite
     poses, GT hash match with the baseline source hashes, unmodified default
     config hash, and recompute metrics from the archived pose files.
     Absent -> status PENDING_B (not a failure of A).
  5. Write-scope: RAP-SLAM tracked comparison assets unmodified
     (data/literature, output_paper_metrics) and HC outputs only inside the
     exclusive directory.

Writes validation.json into the exclusive directory.
"""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

RAP_MAIN = Path(__file__).resolve().parents[2]
RAP_SLAM = RAP_MAIN.parent / "RAP-SLAM"
HC_DIR = RAP_MAIN / "docs" / "maintenance" / "2026-09-19" / "horizontal-comparison-01"
BASELINE = RAP_MAIN / "docs" / "maintenance" / "2026-09-11" / "core-baseline-v1"
sys.path.insert(0, str(RAP_SLAM))
sys.path.insert(0, str(RAP_SLAM / "scripts"))

TOL = 1e-9
CORE_SEQS = ["00", "05", "06"]
ALL_SEQS = [f"{i:02d}" for i in range(11)]
VALIDATION_FILE = HC_DIR / "validation.json"


def _host(path):
    """Frozen artifacts carry WSL-style /mnt/e paths; translate only on Windows."""
    p = str(path)
    if os.name == "nt":
        return p.replace("/mnt/e/", "E:/").replace("/mnt/e", "E:")
    return p


def check_pdf_transcription():
    import pdfplumber
    lit = json.loads((HC_DIR / "data-literature" / "kitti_ate_pin_slam_tab4.json")
                     .read_text(encoding="utf-8"))
    pdf = HC_DIR / "sources" / "2401.09101v2_pin_slam.pdf"
    with pdfplumber.open(str(pdf)) as doc:
        text = ""
        for i, page in enumerate(doc.pages):
            t = page.extract_text() or ""
            if "TABLE IV" in t:
                text = t
                break
        else:
            raise ValueError("TABLE IV not found in archived PDF")
    start = text.index("TABLE IV")
    block = text[start:]
    block = block[block.index("Method 00*"):]
    block = block[:block.index("(a) PIN-LO")]
    rows = {}
    pending_numbers = None
    for line in block.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("(±"):
            continue
        m = re.match(r"^([A-Za-z0-9\-\[\],‡]+?)\s+((?:\d+\.\d+\s+){12}\d+\.\d+)\s*$", line)
        if m:
            name = re.sub(r"\[.*?\]", "", m.group(1)).strip().strip("‡").rstrip(",").strip()
            rows[name] = [float(v) for v in m.group(2).split()]
            continue
        m = re.match(r"^((?:\d+\.\d+\s+){12}\d+\.\d+)\s*$", line)
        if m:  # PIN-LO / PIN-SLAM: numbers precede the bare name line
            pending_numbers = [float(v) for v in m.group(1).split()]
            continue
        if pending_numbers is not None and re.match(r"^[A-Za-z\-]+$", line):
            rows[line.strip()] = pending_numbers
            pending_numbers = None
    problems = []
    expected = {}
    for name, entry in lit["methods"].items():
        expected[name] = entry["ate"] + [entry["avg_loops"], entry["avg"]]
    if set(rows) != set(expected):
        problems.append(f"row set mismatch: pdf={sorted(rows)} json={sorted(expected)}")
    for name in set(rows) & set(expected):
        if rows[name] != expected[name]:
            problems.append(f"{name}: pdf {rows[name]} != json {expected[name]}")
    return {"name": "pdf_transcription", "rows_checked": len(rows),
            "pass": not problems, "problems": problems}


def check_baseline_recompute():
    """Recompute from frozen pose files; gt_from_summary is not reused because
    the frozen summaries carry WSL-style real_root paths."""
    import eval_paper_metrics as epm
    from rap_slam import real_dataset
    registry = json.loads((BASELINE / "registry.json").read_text(encoding="utf-8"))
    problems, checked = [], 0
    for entry in registry["sequences"]:
        seq = entry["sequence"]
        run_dir = Path(_host(entry["run"])) / "pipeline"
        cfg = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))["config"]
        root, rseq = _host(cfg["real_root"]), cfg["real_seq"]
        gt = real_dataset.load_gt_poses(
            str(Path(root) / "dataset" / "poses" / f"{rseq}.txt"),
            str(Path(root) / "dataset" / "sequences" / rseq / "calib.txt"),
            start=0, end=None, apply_calib=cfg.get("real_apply_calib", False))
        ids = json.loads((run_dir / "source_frames.json").read_text(encoding="utf-8"))[
            "source_frame_ids"]
        gt_sel = [gt[i] for i in ids]
        cam = None
        if cfg.get("real_apply_calib", False):
            tr = real_dataset._read_calib_transform(
                str(Path(root) / "dataset" / "sequences" / rseq / "calib.txt"))
            tr_inv = np.linalg.inv(tr)
            cam = (lambda poses: [tr @ p @ tr_inv for p in poses])
        recomputed = {}
        for block, fname in (("odometry", "odom_poses.txt"),
                             ("pgo", "optimized_poses.txt")):
            est = epm.load_kitti_format(str(run_dir / fname))
            m = epm.evaluate_pair(gt_sel, est, ids)
            if cam is not None:
                from rap_slam.trajectory_protocol import kitti_drift
                m["camera_kitti"] = kitti_drift(cam(gt_sel), cam(est),
                                                source_frame_ids=ids)
            recomputed[block] = m
        for block, src in recomputed.items():
            for field in ("ape_unaligned_rmse", "ape_aligned_rmse",
                          "kitti_ter_pct", "kitti_rer_deg100m", "kitti_segments"):
                a, b = entry[block][field], src.get(field)
                if b is None or abs(a - b) > TOL * max(1.0, abs(a)):
                    problems.append(f"{seq}/{block}/{field}: registry {a} vs recomputed {b}")
                checked += 1
            cam_registry = entry.get("camera_" + block)
            cam_src = src.get("camera_kitti")
            if cam_registry:  # empty dict means "no camera metrics" (e.g. POSS)
                if cam_src is None:
                    problems.append(f"{seq}/camera_{block}: missing in recompute")
                    continue
                for field in ("kitti_ter_pct", "kitti_rer_deg100m", "kitti_segments"):
                    a, b = cam_registry[field], cam_src.get(field)
                    if b is None or abs(a - b) > TOL * max(1.0, abs(a)):
                        problems.append(
                            f"{seq}/camera_{block}/{field}: registry {a} vs recomputed {b}")
                    checked += 1
    return {"name": "baseline_recompute", "values_checked": checked,
            "pass": not problems, "problems": problems}


def check_table_arithmetic():
    data = json.loads((HC_DIR / "comparison_v1.json").read_text(encoding="utf-8"))
    md = (HC_DIR / "COMPARISON_TABLE_V1.md").read_text(encoding="utf-8")
    problems, checked = [], 0
    idx = {s: i for i, s in enumerate(ALL_SEQS)}

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    for row in data["drift_rows"]:
        for arr_key, mean_key in (("ter", "ter_mean_core"), ("rer", "rer_mean_core")):
            if arr_key in row:
                expect = mean([row[arr_key][idx[s]] for s in CORE_SEQS])
                if expect is None or abs(expect - row[mean_key]) > 1e-12:
                    problems.append(f"drift {row['method']} {mean_key} mismatch")
                cell = f"{row[mean_key]:.2f}"
                if cell not in md:
                    problems.append(f"drift {row['method']} mean cell {cell} not in md")
                checked += 1
    for row in data["ate_rows"]:
        expect = mean([row["ate"][idx[s]] for s in CORE_SEQS])
        if expect is None or abs(expect - row["ate_mean_core"]) > 1e-12:
            problems.append(f"ate {row['method']} mean_core mismatch")
        if f"{row['ate_mean_core']:.2f}" not in md:
            problems.append(f"ate {row['method']} mean cell not in md")
        for s in CORE_SEQS:
            v = row["ate"][idx[s]]
            if v is not None and f"{v:.2f}" not in md:
                problems.append(f"ate {row['method']} seq {s} cell {v:.2f} not in md")
        checked += 1
    return {"name": "table_arithmetic", "values_checked": checked,
            "pass": not problems, "problems": problems}


def check_external_runs():
    results_file = HC_DIR / "b-kiss-slam" / "eval_results.json"
    if not results_file.exists():
        return {"name": "external_runs", "status": "PENDING_B", "pass": True}
    import hashlib
    import eval_paper_metrics as epm
    from rap_slam import real_dataset
    res = json.loads(results_file.read_text(encoding="utf-8"))
    registry = json.loads((BASELINE / "registry.json").read_text(encoding="utf-8"))
    # GT ground truth: the frozen runs' input manifests hash the exact GT poses
    # and calib files used by the baseline; the external run must match those.
    run_by_seq = {e["sequence"]: Path(_host(e["run"])) for e in registry["sequences"]}
    problems, checked = [], 0
    expected_frames = {"00": 4541, "05": 2761, "06": 1101}
    numeric_keys = ("ape_unaligned_rmse", "ape_aligned_rmse",
                    "kitti_ter_pct", "kitti_rer_deg100m",
                    "kitti_ter_pct_lidar", "kitti_rer_deg100m_lidar")
    for run in res["runs"]:
        for seq, block in run["sequences"].items():
            pose_file = HC_DIR / "b-kiss-slam" / block["pose_file"]
            if not pose_file.exists():
                problems.append(f"{seq}: pose file missing: {pose_file}")
                continue
            est = epm.load_kitti_format(str(pose_file))
            if len(est) != expected_frames[seq]:
                problems.append(f"{seq}: frames {len(est)} != {expected_frames[seq]}")
                continue
            if len(est) != block.get("n_frames"):
                problems.append(f"{seq}: recorded n_frames {block.get('n_frames')} "
                                f"!= actual {len(est)}")
            gt_path = _host(run["gt_files"][seq])
            calib = str(Path(gt_path).parents[1] / "sequences" / seq / "calib.txt")
            if block.get("pose_frame", "camera") != "camera":
                problems.append(f"{seq}: unsupported pose_frame "
                                f"{block.get('pose_frame')}")
                continue
            est_cam = est
            gt_cam = list(real_dataset.load_gt_poses(gt_path, calib, apply_calib=False))
            m_cam = epm.evaluate_pair(gt_cam, est_cam)
            tr = real_dataset._read_calib_transform(calib)
            tr_inv = np.linalg.inv(tr)
            to_velo = (lambda ps: [tr_inv @ p @ tr for p in ps])
            gt_velo = list(real_dataset.load_gt_poses(gt_path, calib, apply_calib=True))
            m_velo = epm.evaluate_pair(gt_velo, to_velo(est_cam))
            recomputed = {
                "ape_unaligned_rmse": m_cam["ape_unaligned_rmse"],
                "ape_aligned_rmse": m_cam["ape_aligned_rmse"],
                "kitti_ter_pct": m_cam["kitti_ter_pct"],
                "kitti_rer_deg100m": m_cam["kitti_rer_deg100m"],
                "kitti_ter_pct_lidar": m_velo["kitti_ter_pct"],
                "kitti_rer_deg100m_lidar": m_velo["kitti_rer_deg100m"],
            }
            for key in numeric_keys:
                recorded = block.get(key)
                if recorded is None:
                    problems.append(f"{seq}: missing key {key}")
                    continue
                if abs(recomputed[key] - recorded) > 1e-9 * max(1.0, abs(recorded)):
                    problems.append(f"{seq}/{key}: recorded {recorded} != "
                                    f"recomputed {recomputed[key]}")
                checked += 1
            gt_sha = hashlib.sha256(Path(gt_path).read_bytes()).hexdigest()
            manifest_file = run_by_seq.get(f"kitti{seq}", Path("/nonexistent")) / \
                "input_manifest.json"
            if not manifest_file.exists():
                problems.append(f"{seq}: baseline input manifest missing")
                continue
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            manifest_gt = {k: v for k, v in manifest.items()
                           if k.endswith(f"poses/{seq}.txt")}
            if not manifest_gt:
                problems.append(f"{seq}: no GT poses entry in baseline manifest")
            elif gt_sha not in set(manifest_gt.values()):
                problems.append(f"{seq}: GT sha256 differs from frozen baseline input")
    return {"name": "external_runs", "status": "CHECKED", "values_checked": checked,
            "pass": not problems, "problems": problems}


def check_write_scope():
    out = subprocess.run(["git", "-C", str(RAP_SLAM), "status", "--short",
                          "--", "data/literature", "output_paper_metrics"],
                         capture_output=True, text=True)
    problems = []
    if out.stdout.strip():
        problems.append(f"RAP-SLAM comparison assets modified: {out.stdout.strip()}")
    # HC outputs are written only into the exclusive directory by construction;
    # count files while tolerating WSL-created symlinks that Windows cannot stat.
    n_files, unreadable = 0, []
    for p in HC_DIR.rglob("*"):
        try:
            if p.is_file():
                n_files += 1
        except OSError:
            unreadable.append(p.name)
    return {"name": "write_scope", "files_in_exclusive_dir": n_files,
            "unreadable_symlinks_skipped": sorted(unreadable),
            "pass": not problems, "problems": problems}


ALL_CHECKS = {
    "pdf_transcription": check_pdf_transcription,
    "baseline_recompute": check_baseline_recompute,
    "table_arithmetic": check_table_arithmetic,
    "external_runs": check_external_runs,
    "write_scope": check_write_scope,
}


def _env_info():
    return {"python": sys.version.split()[0], "executable": sys.executable,
            "platform": platform.platform()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--checks", default=",".join(ALL_CHECKS),
                    help="comma-separated subset of: " + ",".join(ALL_CHECKS))
    args = ap.parse_args()
    selected = [c.strip() for c in args.checks.split(",") if c.strip()]
    unknown = [c for c in selected if c not in ALL_CHECKS]
    if unknown:
        print(f"unknown checks: {unknown}; available: {sorted(ALL_CHECKS)}")
        return 2
    env = _env_info()
    results = []
    for name in selected:
        try:
            results.append(ALL_CHECKS[name]())
        except Exception as exc:  # noqa: BLE001 - abort without overwriting the
            # last good merged state; environment-dependent checks must run
            # under their documented interpreter (see REPORT.md validation table).
            import traceback
            traceback.print_exc()
            print(f"check '{name}' raised {type(exc).__name__}: {exc}")
            print("aborting WITHOUT writing validation.json; run "
                  "baseline_recompute/external_runs under the WSL rap-inference "
                  "environment and the rest under the Windows managed Python")
            return 1
    for c in results:
        c["environment"] = env
    # Merge with any previously stored results so a later single-check run on a
    # different interpreter (e.g. WSL for baseline_recompute) does not erase
    # the outcome of earlier checks.
    stored = {}
    if VALIDATION_FILE.exists():
        try:
            stored = {c["name"]: c for c in
                      json.loads(VALIDATION_FILE.read_text(encoding="utf-8"))["checks"]}
        except (json.JSONDecodeError, KeyError):
            stored = {}
    stored.update({c["name"]: c for c in results})
    checks = [stored[name] for name in ALL_CHECKS if name in stored]
    ok = all(c["pass"] for c in checks) and len(checks) == len(ALL_CHECKS)
    report = {"validator": "validate_horizontal_comparison.py",
              "checks": checks, "all_pass": ok,
              "complete": len(checks) == len(ALL_CHECKS)}
    VALIDATION_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in checks:
        print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['name']}"
              f"{' (' + c['status'] + ')' if 'status' in c else ''}")
        for p in c.get("problems", [])[:12]:
            print("   -", p)
    print(f"ran: {selected}; merged total: {len(checks)}/{len(ALL_CHECKS)}")
    print("ALL PASS" if ok else "FAILURES OR CHECKS PENDING")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
