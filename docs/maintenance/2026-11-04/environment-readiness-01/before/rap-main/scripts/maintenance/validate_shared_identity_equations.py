"""Independent, NumPy-only validation of the frozen SID0 synthetic bank.

This file deliberately does not import the projector or the synthetic runner.
All rigid fits use Horn's quaternion eigenproblem, not the runner's Kabsch SVD.
No dataset, neural model, or dataset ground truth is opened.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


POINT_TOL = 1e-9
POSE_TOL = 1e-9
ROT_TOL = 1e-10
FIT_GAP_TOL = 1e-12


class InvalidFit(ValueError):
    """The proper rigid optimum is not uniquely defined."""


def read_json(path):
    with Path(path).open("r", encoding="utf-8-sig") as stream:
        return json.load(stream)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def transform(pose, points):
    return np.asarray(points) @ np.asarray(pose)[:3, :3].T + np.asarray(pose)[:3, 3]


def inverse(pose):
    out = np.eye(4, dtype=np.float64)
    out[:3, :3] = pose[:3, :3].T
    out[:3, 3] = -out[:3, :3] @ pose[:3, 3]
    return out


def rotation_check(pose):
    pose = np.asarray(pose, dtype=np.float64)
    assert pose.shape == (4, 4) and np.isfinite(pose).all()
    assert np.max(np.abs(pose[3] - [0., 0., 0., 1.])) <= ROT_TOL
    assert np.max(np.abs(pose[:3, :3].T @ pose[:3, :3] - np.eye(3))) <= ROT_TOL
    assert abs(float(np.linalg.det(pose[:3, :3])) - 1.) <= ROT_TOL


def horn(source, target, weights=None):
    """Weighted proper source-to-target fit; reject a nonunique optimum."""
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    if source.shape != target.shape or source.ndim != 2 or source.shape[1] != 3:
        raise InvalidFit("shape")
    if len(source) < 3 or not (np.isfinite(source).all() and np.isfinite(target).all()):
        raise InvalidFit("insufficient or nonfinite points")
    weights = np.ones(len(source), dtype=np.float64) if weights is None else np.asarray(weights, dtype=np.float64)
    if weights.shape != (len(source),) or not np.isfinite(weights).all() or np.any(weights <= 0):
        raise InvalidFit("invalid weights")
    weights = weights / weights.sum()
    pc = np.sum(source * weights[:, None], axis=0)
    yc = np.sum(target * weights[:, None], axis=0)
    s = (source - pc).T @ ((target - yc) * weights[:, None])
    xx, xy, xz = s[0]
    yx, yy, yz = s[1]
    zx, zy, zz = s[2]
    k = np.array([
        [xx + yy + zz, yz - zy, zx - xz, xy - yx],
        [yz - zy, xx - yy - zz, xy + yx, zx + xz],
        [zx - xz, xy + yx, -xx + yy - zz, yz + zy],
        [xy - yx, zx + xz, yz + zy, -xx - yy + zz],
    ], dtype=np.float64)
    values, vectors = np.linalg.eigh(k)
    gap = float(values[-1] - values[-2])
    if gap <= FIT_GAP_TOL * max(1., float(np.max(np.abs(values)))):
        raise InvalidFit("nonunique proper rigid optimum")
    w, x, y, z = vectors[:, -1]
    rotation = np.array([
        [1. - 2. * (y*y + z*z), 2. * (x*y - w*z), 2. * (x*z + w*y)],
        [2. * (x*y + w*z), 1. - 2. * (x*x + z*z), 2. * (y*z - w*x)],
        [2. * (x*z - w*y), 2. * (y*z + w*x), 1. - 2. * (x*x + y*y)],
    ])
    pose = np.eye(4)
    pose[:3, :3] = rotation
    pose[:3, 3] = yc - rotation @ pc
    rotation_check(pose)
    residual = target - transform(pose, source)
    minimum = float(np.sum(weights * np.sum(residual * residual, axis=1)))
    return pose, minimum, gap


def close(actual, expected, tolerance=POSE_TOL):
    actual = np.asarray(actual)
    expected = np.asarray(expected)
    assert actual.shape == expected.shape, (actual.shape, expected.shape)
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    delta = float(np.max(np.abs(actual - expected))) if actual.size else 0.
    assert delta <= tolerance, (delta, tolerance)
    return delta


def peak_rss_bytes():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
                 "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                 "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def factor_counts(factors):
    counts = {}
    for factor in factors:
        counts[factor["scan"]] = counts.get(factor["scan"], 0) + 1
    return counts


def independent_fits(factors):
    fits, minima = {}, {}
    for factor in factors:
        key = (factor["window"], factor["scan"])
        assert key not in fits
        fits[key], minima[key], _ = horn(factor["p"], factor["Y"])
    return fits, minima


def shared_scan_fit(scan, factors, gauges, counts):
    selected = [factor for factor in factors if factor["scan"] == scan]
    pp = np.concatenate([factor["p"] for factor in selected])
    yy = np.concatenate([transform(gauges[factor["window"]], factor["Y"]) for factor in selected])
    ww = np.concatenate([np.full(len(factor["p"]), 1. / (counts[scan] * len(factor["p"]))) for factor in selected])
    return horn(pp, yy, ww)[0]


def objective(factors, gauges, poses):
    counts = factor_counts(factors)
    cost = 0.
    for factor in factors:
        residual = transform(gauges[factor["window"]], factor["Y"]) - transform(poses[factor["scan"]], factor["p"])
        cost += float(np.sum(residual * residual)) / (counts[factor["scan"]] * len(factor["p"]))
    return cost


def profile_objective(factors, gauges, poses, minima=None):
    """Use independently minimized constants for all unique factors."""
    counts = factor_counts(factors)
    if minima is None:
        _, minima = independent_fits(factors)
    cost = 0.
    for factor in factors:
        scan = factor["scan"]
        key = (factor["window"], scan)
        if counts[scan] == 1:
            cost += minima[key]
        else:
            residual = transform(gauges[factor["window"]], factor["Y"]) - transform(poses[scan], factor["p"])
            cost += float(np.sum(residual * residual)) / (counts[scan] * len(factor["p"]))
    return cost


def shared_objective(factors, gauges, poses):
    counts = factor_counts(factors)
    return sum(float(np.sum((transform(gauges[f["window"]], f["Y"])
                           - transform(poses[f["scan"]], f["p"])) ** 2))
               / (counts[f["scan"]] * len(f["p"]))
               for f in factors if counts[f["scan"]] > 1)


def right_gauge_fit(factors, poses, counts, right):
    selected = [factor for factor in factors if factor["window"] == right and counts[factor["scan"]] > 1]
    source = np.concatenate([factor["Y"] for factor in selected])
    target = np.concatenate([transform(poses[factor["scan"]], factor["p"]) for factor in selected])
    weights = np.concatenate([np.full(len(factor["p"]), 1. / (counts[factor["scan"]] * len(factor["p"]))) for factor in selected])
    return horn(source, target, weights)[0]


def initial_right_gauge(factors, left, right):
    counts = factor_counts(factors)
    sources, targets, weights = [], [], []
    for factor in factors:
        if factor["window"] != right or counts[factor["scan"]] < 2:
            continue
        partner = next(f for f in factors if f["window"] == left and f["scan"] == factor["scan"])
        close(partner["p"], factor["p"], 0.)
        sources.append(factor["Y"])
        targets.append(partner["Y"])
        weights.append(np.full(len(factor["p"]), 1. / (counts[factor["scan"]] * len(factor["p"]))))
    return horn(np.concatenate(sources), np.concatenate(targets), np.concatenate(weights))[0]


def horn_two_window(factors, window_order, max_sweeps=64, change_tol=1e-12):
    """Independent mathematical reconstruction of the specified iteration.

    The algorithm is fixed by the prospectively frozen protocol; fits are
    obtained with a different numerical construction. Unique factors are
    never included in a gauge vote or evaluated with stale poses.
    """
    assert len(window_order) == 2
    left, right = window_order
    counts = factor_counts(factors)
    fits, minima = independent_fits(factors)
    shared = [scan for scan, count in counts.items() if count > 1]
    assert len(shared) >= 2
    gauges = {left: np.eye(4), right: initial_right_gauge(factors, left, right)}
    poses = {scan: shared_scan_fit(scan, factors, gauges, counts) for scan in shared}
    for factor in factors:
        if counts[factor["scan"]] == 1:
            poses[factor["scan"]] = gauges[factor["window"]] @ fits[(factor["window"], factor["scan"])]
    trace = [profile_objective(factors, gauges, poses, minima)]
    shared_trace = [shared_objective(factors, gauges, poses)]
    gauge_trace = [{w: gauges[w].copy() for w in window_order}]
    pose_trace = [{scan: pose.copy() for scan, pose in poses.items()}]
    converged = False
    for _ in range(max_sweeps):
        for scan in shared:
            poses[scan] = shared_scan_fit(scan, factors, gauges, counts)
        gauges[right] = right_gauge_fit(factors, poses, counts, right)
        for scan in shared:
            poses[scan] = shared_scan_fit(scan, factors, gauges, counts)
        for factor in factors:
            if counts[factor["scan"]] == 1:
                poses[factor["scan"]] = gauges[factor["window"]] @ fits[(factor["window"], factor["scan"])]
        value = profile_objective(factors, gauges, poses, minima)
        assert value <= trace[-1] + 1e-10 * max(1., trace[-1])
        trace.append(value)
        shared_trace.append(shared_objective(factors, gauges, poses))
        gauge_trace.append({w: gauges[w].copy() for w in window_order})
        pose_trace.append({scan: pose.copy() for scan, pose in poses.items()})
        if abs(shared_trace[-2] - shared_trace[-1]) <= change_tol * max(1., shared_trace[-2]):
            converged = True
            break
    if not converged:
        raise InvalidFit("nonconvergence")
    for factor in factors:
        if counts[factor["scan"]] == 1:
            poses[factor["scan"]] = gauges[factor["window"]] @ fits[(factor["window"], factor["scan"])]
    return gauges, poses, np.asarray(trace), fits, minima, np.asarray(shared_trace), gauge_trace, pose_trace


def horn_tree(factors, nw, ns):
    """Closed-form incidence propagation, with no iterative projector call."""
    assert len(factors) == nw + ns - 1
    fits, minima = independent_fits(factors)
    gauges, poses = {0: np.eye(4)}, {}
    changed = True
    while changed:
        changed = False
        for factor in factors:
            w, scan = factor["window"], factor["scan"]
            native = fits[(w, scan)]
            if w in gauges and scan not in poses:
                poses[scan] = gauges[w] @ native
                changed = True
            elif scan in poses and w not in gauges:
                gauges[w] = poses[scan] @ inverse(native)
                changed = True
    assert len(gauges) == nw and len(poses) == ns, "disconnected incidence"
    for factor in factors:
        close(poses[factor["scan"]], gauges[factor["window"]] @ fits[(factor["window"], factor["scan"])])
    return gauges, poses, fits, minima


def unpack_factors(arrays):
    points = np.asarray(arrays["points"], dtype=np.float64)
    counts = np.asarray(arrays["point_counts"], dtype=np.int64)
    scans = np.asarray(arrays["factor_scans"], dtype=np.int64)
    windows = np.asarray(arrays["factor_windows"], dtype=np.int64)
    rows = np.asarray(arrays["factor_rows"], dtype=np.int64)
    offsets = np.asarray(arrays["factor_offsets"], dtype=np.int64)
    scales = np.asarray(arrays["scales"], dtype=np.float64)
    centers = np.asarray(arrays["centers"], dtype=np.float64)
    assert points.shape == (int(counts.sum()), 3)
    assert counts.ndim == 1 and np.all(counts >= 3)
    nf, ns, nw = len(scans), len(counts), len(scales)
    assert windows.shape == (nf,) and centers.shape == (nf, 3)
    assert set(scans.tolist()) == set(range(ns)) and set(windows.tolist()) == set(range(nw))
    assert len(set(zip(windows.tolist(), scans.tolist()))) == nf
    assert offsets.shape == (nf + 1,) and offsets[0] == 0 and offsets[-1] == len(rows)
    assert np.all(np.diff(offsets) > 0) and np.all(scales > 0.) and np.isfinite(scales).all()
    point_offsets = np.concatenate([[0], np.cumsum(counts)])
    raw = np.asarray(arrays["raw"], dtype=np.float64) if "raw" in arrays else None
    if raw is not None:
        assert raw.shape == (len(rows), 3)
    factors = []
    maximum = 0.
    for index, (scan, window) in enumerate(zip(scans, windows)):
        start, stop = offsets[index:index+2]
        local = rows[start:stop]
        assert len(local) == counts[scan]
        assert np.array_equal(np.sort(local), np.arange(counts[scan]))
        p = points[point_offsets[scan] + local]
        order = np.argsort(local)
        factor = {"window": int(window), "scan": int(scan), "p": p[order],
                  "ordered_p": p, "slice": slice(int(start), int(stop)),
                  "order": order, "row_ids": local.copy(), "index": index}
        if raw is not None:
            factor["Y"] = (raw[start:stop] * scales[window])[order]
        factors.append(factor)
        if "cond" in arrays:
            expected = (p - centers[index]) / scales[window]
            maximum = max(maximum, close(arrays["cond"][start:stop], expected, POINT_TOL))
        if raw is not None and "analytic_T" in arrays:
            expected = transform(arrays["analytic_T"][index], p) + arrays["perturbation"][start:stop]
            maximum = max(maximum, close(raw[start:stop] * scales[window], expected, POINT_TOL))
    assert np.isfinite(points).all() and np.isfinite(centers).all()
    reached_windows, reached_scans = {0}, set()
    for _ in range(nw + ns):
        reached_scans |= {f["scan"] for f in factors if f["window"] in reached_windows}
        reached_windows |= {f["window"] for f in factors if f["scan"] in reached_scans}
    if len(reached_windows) != nw or len(reached_scans) != ns:
        raise InvalidFit("disconnected incidence")
    return factors, nw, ns, maximum


def solve_horn(factors, nw, ns):
    if len(factors) == nw + ns - 1:
        gauges, poses, fits, minima = horn_tree(factors, nw, ns)
        total = objective(factors, gauges, poses)
        shared = shared_objective(factors, gauges, poses)
        return (gauges, poses, np.asarray([total]), fits, minima,
                np.asarray([shared]), [gauges], [poses])
    assert nw == 2 and sum(count > 1 for count in factor_counts(factors).values()) == 2
    return horn_two_window(factors, [0, 1])


def validate_projected_case(arrays):
    factors, nw, ns, maximum = unpack_factors(arrays)
    gauges, poses, trace, fits, minima, shared_trace, gauge_trace, pose_trace = solve_horn(factors, nw, ns)
    assert bool(arrays["converged"]) and int(arrays["sweeps"]) == len(trace) - 1
    for w in range(nw):
        rotation_check(arrays["G"][w])
        maximum = max(maximum, close(arrays["G"][w], gauges[w]))
    maximum = max(maximum, close(arrays["G"][0], np.eye(4), ROT_TOL))
    for scan in range(ns):
        rotation_check(arrays["Z"][scan])
        maximum = max(maximum, close(arrays["Z"][scan], poses[scan]))
    maximum = max(maximum, close(arrays["objective_trace"], trace, POINT_TOL),
                  close(arrays["shared_objective_trace"], shared_trace, POINT_TOL))
    if "G_trace" in arrays:
        expected = np.stack([[row[w] for w in range(nw)] for row in gauge_trace])
        maximum = max(maximum, close(arrays["G_trace"], expected))
    if "Z_trace" in arrays:
        expected = np.stack([[row[scan] for scan in range(ns)] for row in pose_trace])
        maximum = max(maximum, close(arrays["Z_trace"], expected))
    counts = factor_counts(factors)
    for f in factors:
        w, scan, sl = f["window"], f["scan"], f["slice"]
        scale = float(arrays["scales"][w])
        native = fits[(w, scan)]
        rotation_check(arrays["native_T"][f["index"]])
        maximum = max(maximum, close(arrays["native_T"][f["index"]], native))
        expected_native = transform(native, f["ordered_p"]) / scale
        expected_clean = transform(inverse(gauges[w]) @ poses[scan], f["ordered_p"]) / scale
        maximum = max(maximum, close(arrays["native_clean"][sl], expected_native, POINT_TOL),
                      close(arrays["clean"][sl], expected_clean, POINT_TOL))
        # Independent normalized fit and physical decoding verifies the center
        # subtraction, known scaling and absence of an added output center.
        normfit = horn(np.asarray(arrays["cond"][sl]), np.asarray(arrays["raw"][sl]))[0]
        decoded = normfit.copy()
        decoded[:3, 3] = scale * normfit[:3, 3] - normfit[:3, :3] @ arrays["centers"][f["index"]]
        maximum = max(maximum, close(decoded, native))
        if counts[scan] == 1:
            maximum = max(maximum, close(poses[scan], gauges[w] @ native))
    if ns > 1:
        maximum = max(maximum, close(arrays["rel"], inverse(poses[0]) @ poses[1]))
    # Recompute full residual independently, then profile unique factors away.
    final_total = objective(factors, gauges, poses)
    maximum = max(maximum, close([final_total], [trace[-1]], POINT_TOL))
    if len(factors) != nw + ns - 1:
        maximum = max(maximum, close([profile_objective(factors, gauges, poses, minima)], [trace[-1]], POINT_TOL))
        next_gauges = {w: gauge.copy() for w, gauge in gauges.items()}
        next_gauges[1] = right_gauge_fit(factors, poses, counts, 1)
        next_poses = {}
        for scan, count in counts.items():
            if count > 1:
                next_poses[scan] = shared_scan_fit(scan, factors, next_gauges, counts)
            else:
                factor = next(f for f in factors if f["scan"] == scan)
                next_poses[scan] = next_gauges[factor["window"]] @ fits[(factor["window"], scan)]
        next_block_delta = max([float(np.max(np.abs(next_gauges[w] - gauges[w]))) for w in range(nw)]
                              + [float(np.max(np.abs(next_poses[scan] - poses[scan]))) for scan in range(ns)])
        next_profile = profile_objective(factors, next_gauges, next_poses, minima)
        assert next_profile <= trace[-1] + 1e-10 * max(1., trace[-1])
    else:
        next_block_delta, next_profile = 0., final_total
    return {"factors": factors, "nw": nw, "ns": ns, "G": gauges, "Z": poses,
            "fits": fits, "minima": minima, "trace": trace,
            "shared_trace": shared_trace, "max_delta": maximum,
            "next_block_max_pose_delta": next_block_delta,
            "next_profiled_objective": next_profile}


def host_path(path):
    path = str(path).replace("\\", "/")
    original = Path(path)
    if original.exists() or not (len(path) > 2 and path[1:3] == ":/"):
        return original
    return Path("/mnt") / path[0].lower() / path[3:]


def check_sources(directory):
    freeze_path = directory / "freeze.json"
    freeze = read_json(freeze_path)
    assert freeze["stage"] == "SID0"
    assert isinstance(freeze["sources"], list) and freeze["sources"]
    paths = [str(row["path"]) for row in freeze["sources"]]
    assert len(paths) == len(set(paths))
    for row in freeze["sources"]:
        path = host_path(row["path"])
        assert path.is_file() and path.stat().st_size == int(row["size"])
        assert sha256(path) == row["sha256"], str(path)
    manifest = read_json(directory / "manifest.json")
    assert manifest["case_inventory"] == freeze["case_inventory"]
    assert any(host_path(row["path"]).resolve() == (directory / "manifest.json").resolve() for row in freeze["sources"])
    assert any(host_path(row["path"]).resolve() == Path(__file__).resolve() for row in freeze["sources"])
    assert len({row["id"] for row in freeze["case_inventory"]}) == len(freeze["case_inventory"])
    return freeze, sha256(freeze_path)


def sealed_path(directory, relative):
    relative = Path(relative)
    assert not relative.is_absolute() and ".." not in relative.parts
    path = (directory / relative).resolve()
    assert path.is_relative_to(directory.resolve())
    return path


def check_bank(directory, freeze_hash):
    seal = read_json(directory / "bank_seal.json")
    assert seal["stage"] == "SID0" and seal["freeze_sha256"] == freeze_hash
    assert len({row["path"] for row in seal["files"]}) == len(seal["files"])
    for row in seal["files"]:
        path = sealed_path(directory, row["path"])
        assert path.is_file() and path.stat().st_size == int(row["size"])
        assert sha256(path) == row["sha256"], str(path)
        assert row["path"] == "bank.json" or (path.suffix == ".npz" and path.parent == (directory / "cases").resolve())
    assert "bank.json" in {row["path"] for row in seal["files"]}
    bank = read_json(directory / "bank.json")
    assert bank["stage"] == "SID0" and bank["freeze_sha256"] == freeze_hash
    expected = {"bank.json", *(row["file"] for row in bank["rows"])}
    assert expected == {row["path"] for row in seal["files"]}
    actual_npz = {path.relative_to(directory).as_posix() for path in (directory / "cases").glob("*.npz")}
    assert actual_npz == {row["file"] for row in bank["rows"]}
    return bank, seal, sha256(directory / "bank_seal.json")


def intrinsic_checks(arrays, result):
    """Check consequences using arrays rather than the runner's boolean rows."""
    kind = str(np.asarray(arrays["kind"]).item()).lower()
    maximum = result["max_delta"]
    if result["nw"] == 1 or len(result["factors"]) == result["nw"] + result["ns"] - 1:
        maximum = max(maximum, close(arrays["clean"], arrays["native_clean"], POINT_TOL))
    if any(word in kind for word in ("consistent", "idempot", "wrong")) and "conflict" not in kind:
        # Only exactly rigid/consistent fixtures promise zero objective.
        if np.max(np.abs(arrays.get("perturbation", np.zeros((1, 3))))) <= 1e-14:
            assert result["shared_trace"][-1] <= POINT_TOL ** 2 * 100.
            maximum = max(maximum, close(arrays["clean"], arrays["raw"], POINT_TOL))
    if "wrong" in kind:
        expected = np.eye(4)
        expected[0, 3] = 2.
        # If a synthetic truth is supplied, compare the relative prediction in
        # its frame. Otherwise this fixture defines identity as its truth.
        truth = arrays.get("truth_rel", arrays.get("synthetic_truth_rel", np.eye(4)))
        error = inverse(np.asarray(truth)) @ arrays["rel"]
        assert abs(float(np.linalg.norm(error[:3, 3])) - 2.) <= POINT_TOL
        assert result["shared_trace"][-1] <= POINT_TOL ** 2 * 100.
    if "conflict" in kind:
        rel = np.asarray(arrays["rel"])
        source_rels = []
        for w in range(result["nw"]):
            if (w, 0) in result["fits"] and (w, 1) in result["fits"]:
                source_rels.append(inverse(result["fits"][(w, 0)]) @ result["fits"][(w, 1)])
        assert len(source_rels) == 2
        assert max(float(np.max(np.abs(source - rel))) for source in source_rels) > 100. * POSE_TOL
    return maximum


def variant_checks(row, arrays, result, reference_arrays, reference):
    maximum = result["max_delta"]
    kind = row["kind"].lower()
    if any(word in kind for word in ("scale", "center", "permut")):
        for scan in range(result["ns"]):
            maximum = max(maximum, close(result["Z"][scan], reference["Z"][scan]))
        for w in range(result["nw"]):
            maximum = max(maximum, close(result["G"][w], reference["G"][w]))
        reference_factors = {(f["window"], f["scan"]): f for f in reference["factors"]}
        for f in result["factors"]:
            rf = reference_factors[(f["window"], f["scan"])]
            maximum = max(maximum, close(f["p"], rf["p"], 0.), close(f["Y"], rf["Y"], POINT_TOL))
    if "gauge" in kind:
        change = arrays.get("gauge_changes", arrays.get("gauge_change"))
        assert change is not None and np.asarray(change).shape == (result["nw"], 4, 4)
        if kind == "common_gauge":
            maximum = max(maximum, close(change[0], change[1], 0.))
        for w in range(result["nw"]):
            rotation_check(change[w])
            expected = change[0] @ reference["G"][w] @ inverse(change[w])
            maximum = max(maximum, close(result["G"][w], expected))
        for scan in range(result["ns"]):
            maximum = max(maximum, close(result["Z"][scan], change[0] @ reference["Z"][scan]))
        maximum = max(maximum, close(arrays["rel"], reference_arrays["rel"]))
    if "unique" in kind and any(word in kind for word in ("residual", "perturb")):
        counts = factor_counts(result["factors"])
        for w in range(result["nw"]):
            maximum = max(maximum, close(result["G"][w], reference["G"][w]))
        for scan, count in counts.items():
            if count > 1:
                maximum = max(maximum, close(result["Z"][scan], reference["Z"][scan]))
        maximum = max(maximum, close(result["shared_trace"], reference["shared_trace"]))
        assert len(result["trace"]) == len(reference["trace"])
    if kind == "idempotent":
        maximum = max(maximum, close(arrays["rel"], reference_arrays["rel"]),
                      close(arrays["clean"], arrays["raw"], POINT_TOL))
    return maximum


def toy_checks(row, arrays):
    """Reconstruct analytic velocities, raw proposals and original-noise flow."""
    factors, nw, ns, maximum = unpack_factors(arrays)
    assert (nw, ns, len(factors)) == (2, 2, 4)
    maximum = max(maximum, close(arrays["scales"], [1., 1.], 0.),
                  close(arrays["centers"], np.zeros((4, 3)), 0.),
                  close(arrays["times"], [1., .5], 0.),
                  close(arrays["bias"], [1., 3.], 0.),
                  close(arrays["noise"], np.zeros_like(arrays["raw"]), 0.))
    base = np.empty_like(arrays["raw"])
    constant_endpoints = np.empty_like(base)
    for f in factors:
        base[f["slice"]] = f["ordered_p"]
        constant_endpoints[f["slice"]] = f["ordered_p"]
        if f["scan"] == 1:
            constant_endpoints[f["slice"], 0] += arrays["bias"][f["window"]]
        maximum = max(maximum, close(np.mean(f["ordered_p"], axis=0), np.zeros(3), ROT_TOL))
    states = {"C": arrays["noise"].copy(), "I": arrays["noise"].copy()}
    final_input_i = None
    for step, t in enumerate((1., .5)):
        for arm in ("C", "I"):
            state = states[arm]
            maximum = max(maximum, close(arrays[arm + "_state"][step], state, POINT_TOL))
            if row["kind"] == "toy_state_dependent":
                proposal = base.copy()
                for w in range(nw):
                    anchor_a = next(f for f in factors if f["window"] == w and f["scan"] == 0)
                    anchor_b = next(f for f in factors if f["window"] == w and f["scan"] == 1)
                    r = np.mean(state[anchor_b["slice"]], axis=0) - np.mean(state[anchor_a["slice"]], axis=0)
                    proposal[anchor_b["slice"], 0] += float(arrays["bias"][w] + r[0] ** 2)
                velocity = (state - proposal) / t
            else:
                velocity = -constant_endpoints
                proposal = state - t * velocity
            maximum = max(maximum, close(arrays[arm + "_velocity"][step], velocity, POINT_TOL),
                          close(arrays[arm + "_raw"][step], proposal, POINT_TOL),
                          close(arrays[arm + "_raw"][step], state - t * velocity, POINT_TOL))
            item = dict(arrays)
            item["raw"] = proposal
            item.pop("analytic_T", None)
            item.pop("perturbation", None)
            current_factors, _, _, _ = unpack_factors(item)
            gauges, poses, _, fits, _, _, _, _ = solve_horn(current_factors, nw, ns)
            clean = np.empty_like(proposal)
            for f in current_factors:
                local_pose = inverse(gauges[f["window"]]) @ poses[f["scan"]] if arm == "C" else fits[(f["window"], f["scan"])]
                clean[f["slice"]] = transform(local_pose, f["ordered_p"])
            relative = inverse(poses[0]) @ poses[1] if arm == "C" else inverse(fits[(0, 0)]) @ fits[(0, 1)]
            maximum = max(maximum, close(arrays[arm + "_clean"][step], clean, POINT_TOL),
                          close(arrays[arm + "_rel"][step], relative))
            states[arm] = (1. - t + .5) * clean + (t - .5) * arrays["noise"]
            if arm == "I" and step == 1:
                final_input_i = (current_factors, gauges, poses)
    for arm in ("C", "I"):
        maximum = max(maximum, close(arrays[arm + "_final_state"], states[arm], POINT_TOL))
    final_factors, final_gauges, final_poses = final_input_i
    final_clean = np.empty_like(arrays["raw"])
    for f in final_factors:
        final_clean[f["slice"]] = transform(inverse(final_gauges[f["window"]]) @ final_poses[f["scan"]], f["ordered_p"])
    maximum = max(maximum, close(arrays["F_clean"], final_clean, POINT_TOL),
                  close(arrays["F_rel"], inverse(final_poses[0]) @ final_poses[1]))
    expected_c, expected_f = (3., 3.25) if row["kind"] == "toy_state_dependent" else (2., 2.)
    expected_c_pose, expected_f_pose = np.eye(4), np.eye(4)
    expected_c_pose[0, 3], expected_f_pose[0, 3] = expected_c, expected_f
    maximum = max(maximum, close(arrays["C_rel"][-1], expected_c_pose),
                  close(arrays["F_rel"], expected_f_pose))
    if row["kind"] == "toy_state_dependent":
        # Explicit synthetic noncommutation, with no correctness/truth claim.
        assert abs(float(arrays["F_rel"][0, 3] - arrays["C_rel"][-1, 0, 3])) > 100. * POSE_TOL
        assert float(np.max(np.abs(arrays["C_raw"][1] - arrays["I_raw"][1]))) > .1
    return maximum


def fixture_points(row, arrays):
    """Rebuild the frozen point geometries from seeds or analytic definitions."""
    if "trial" in row:
        trial = int(row["trial"])
        assert 0 <= trial < 32 and int(arrays["trial"]) == trial
        rng = np.random.default_rng(20261006 + trial)
        pp = [rng.normal(size=(n, 3)) * np.array([1.4, .9, .5]) + np.array([i * .2, 0., 0.])
              for i, n in enumerate((17, 19, 13, 11))]
        if trial >= 16:
            for p in pp:
                p[:, 2] = 0.
    elif row["kind"].startswith("tree"):
        rng = np.random.default_rng(20263006)
        pp = [rng.normal(size=(11 + i, 3)) for i in range(5)]
    elif row["kind"] in ("wrong_consistent", "reflected_ambiguous", "toy_constant_velocity", "toy_state_dependent"):
        p = np.concatenate([np.eye(3), -np.eye(3)])
        pp = [p.copy() for _ in range(2 if row["kind"].startswith("toy") else 4)]
    else:
        rng = np.random.default_rng(20261006)
        pp = [rng.normal(size=(n, 3)) * np.array([1.4, .9, .5]) + np.array([i * .2, 0., 0.])
              for i, n in enumerate((17, 19, 13, 11))]
        if row["kind"] in ("coincident", "collinear"):
            pp[0][:] = 0.
            if row["kind"] == "collinear":
                pp[0][:, 0] = np.linspace(-1., 1., len(pp[0]))
    maximum = close(arrays["points"], np.concatenate(pp), 0.)
    maximum = max(maximum, close(arrays["point_counts"], [len(p) for p in pp], 0.))
    return maximum


def validate(directory):
    started = time.perf_counter()
    directory = Path(directory).resolve()
    freeze, frozen_hash = check_sources(directory)
    bank, seal, bank_seal_hash = check_bank(directory, frozen_hash)
    # All hash/source/seal checks above finish before opening any point array.
    assert [{k: v for k, v in row.items() if k != "file"} for row in bank["rows"]] == freeze["case_inventory"]
    assert len(bank["rows"]) == 330
    limits, tolerances = freeze["limits"], freeze["tolerances"]
    assert limits == {"cpu_seconds": 120, "rss_bytes": 1073741824, "artifact_bytes": 20000000}
    assert tolerances == {"points": 1e-9, "poses": 1e-9, "rotations": 1e-10,
                          "fit_uniqueness": 1e-12, "shared_objective_stop": 1e-12, "max_sweeps": 64}
    references = {}
    rows = []
    maximum = 0.
    expected_errors = 0
    kinds = {}
    for row in bank["rows"]:
        with np.load(sealed_path(directory, row["file"]), allow_pickle=False) as saved:
            arrays = {key: saved[key] for key in saved.files}
        assert str(arrays["case_id"].item()) == row["id"] and str(arrays["kind"].item()) == row["kind"]
        for value in arrays.values():
            if value.dtype.kind in "bifu":
                assert np.isfinite(value).all()
        delta = fixture_points(row, arrays)
        if "expected_error" in row:
            assert str(arrays["observed_error"].item())
            try:
                factors, nw, ns, _ = unpack_factors(arrays)
                solve_horn(factors, nw, ns)
            except InvalidFit:
                expected_errors += 1
            else:
                raise AssertionError("independent fit failed to reject " + row["id"])
            rows.append({"id": row["id"], "kind": row["kind"], "independent_expected_rejection": True})
        else:
            result = validate_projected_case(arrays)
            delta = max(delta, intrinsic_checks(arrays, result))
            if "reference_id" in row:
                reference_arrays, reference = references[row["reference_id"]]
                delta = max(delta, variant_checks(row, arrays, result, reference_arrays, reference))
            if row["kind"].startswith("toy"):
                delta = max(delta, toy_checks(row, arrays))
            if row["kind"] == "conflict":
                references[row["id"]] = (arrays, result)
            rows.append({"id": row["id"], "kind": row["kind"], "independent_expected_rejection": False,
                         "max_independent_delta": delta, "sweeps": len(result["trace"]) - 1,
                         "independent_full_objective": float(result["trace"][-1]),
                         "independent_shared_objective": float(result["shared_trace"][-1]),
                         "next_block_max_pose_delta": result["next_block_max_pose_delta"],
                         "next_profiled_objective": result["next_profiled_objective"]})
        maximum = max(maximum, delta)
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
        assert time.perf_counter() - started + float(bank["wall_seconds"]) <= limits["cpu_seconds"]
        assert max(peak_rss_bytes(), int(bank["peak_rss_bytes"])) <= limits["rss_bytes"]
    assert expected_errors == 5
    expected_kinds = {kind: 32 for kind in ("single", "one_shared", "consistent", "conflict", "gauge", "common_gauge", "scale", "permutation", "idempotent", "unique_residual")}
    expected_kinds.update({kind: 1 for kind in ("tree_chain", "tree_star", "wrong_consistent", "coincident", "collinear", "collapsed_target", "reflected_ambiguous", "disconnected", "toy_constant_velocity", "toy_state_dependent")})
    assert kinds == expected_kinds
    # Verify provenance again to detect mutations during independent checking.
    check_sources(directory)
    check_bank(directory, frozen_hash)
    elapsed = time.perf_counter() - started
    rss = max(peak_rss_bytes(), int(bank["peak_rss_bytes"]))
    assert float(bank["wall_seconds"]) + elapsed <= limits["cpu_seconds"]
    assert rss <= limits["rss_bytes"]
    actual_npz_bytes = sum(sealed_path(directory, row["file"]).stat().st_size for row in bank["rows"])
    assert actual_npz_bytes == int(bank["artifact_bytes"])
    artifact_bytes = sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())
    assert artifact_bytes <= limits["artifact_bytes"]
    output = {"stage": "SID0", "created_utc": utc_now(), "passed": True,
              "decision": "PASS_SHARED_IDENTITY_EQUATION_PREFLIGHT",
              "freeze_sha256": frozen_hash, "bank_seal_sha256": bank_seal_hash,
              "case_count": len(rows), "expected_rejections": expected_errors,
              "kind_counts": kinds, "per_case": rows, "max_independent_delta": maximum,
              "max_next_block_pose_delta": max(row.get("next_block_max_pose_delta", 0.) for row in rows),
              "objective_stop_is_global_optimum_claim": False,
              "wall_seconds": elapsed, "combined_wall_seconds": float(bank["wall_seconds"]) + elapsed,
              "peak_rss_bytes": rss, "artifact_bytes_before_validation": artifact_bytes,
              "synthetic_only": True, "dataset_files_read": False, "dataset_gt_files_read": False,
              "model_inference": False, "fit_method": "weighted_Horn_quaternion_eigh_no_SVD",
              "runtime": {"python_version": sys.version, "numpy_version": np.__version__, "python_executable": sys.executable},
              "accuracy_or_originality_established": False}
    target = directory / "validation.json"
    assert not target.exists(), "independent validation cannot overwrite prior output"
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    assert sum(path.stat().st_size for path in directory.rglob("*") if path.is_file()) <= limits["artifact_bytes"]
    print(json.dumps({key: output[key] for key in ("decision", "case_count", "expected_rejections",
                     "max_independent_delta", "combined_wall_seconds", "peak_rss_bytes")}, allow_nan=False))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path,
                        default=Path(__file__).resolve().parents[2] / "docs/maintenance/2026-10-06/shared-identity-equations-01")
    args = parser.parse_args()
    validate(args.directory)
