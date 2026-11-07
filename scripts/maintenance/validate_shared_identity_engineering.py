"""Independent NumPy validation for the frozen SID1 GT-free engineering bank.

No neural model, dataset ground truth, projector, or bank runner is imported.
The immutable SID0 validator supplies independent Horn quaternion equations.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from validate_shared_identity_equations import (
    horn, inverse, transform, sha256, read_json, host_path, sealed_path,
    solve_horn, peak_rss_bytes, utc_now,
)


def check_close(actual, expected, tolerance):
    actual, expected = np.asarray(actual), np.asarray(expected)
    assert actual.shape == expected.shape, (actual.shape, expected.shape)
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    delta = float(np.max(np.abs(actual - expected))) if actual.size else 0.
    assert delta <= tolerance, (delta, tolerance)
    return delta


def check_exact(actual, expected):
    actual, expected = np.asarray(actual), np.asarray(expected)
    assert actual.dtype == expected.dtype and actual.shape == expected.shape
    assert np.array_equal(actual, expected)
    return 0.


def check_rotation(pose, tolerance):
    pose = np.asarray(pose)
    assert pose.shape == (4, 4) and np.isfinite(pose).all()
    check_close(pose[3], [0., 0., 0., 1.], tolerance)
    check_close(pose[:3, :3].T @ pose[:3, :3], np.eye(3), tolerance)
    assert abs(float(np.linalg.det(pose[:3, :3])) - 1.) <= tolerance


def independent_native(condition, raw, counts):
    """Normalized clean points and poses from independently fitted raw rows."""
    condition = np.asarray(condition, dtype=np.float64)
    raw = np.asarray(raw, dtype=np.float64)
    counts = np.asarray(counts, dtype=np.int64)
    assert condition.shape == raw.shape == (int(counts.sum()), 3)
    offsets = np.concatenate([[0], np.cumsum(counts)])
    clean = np.empty_like(raw)
    poses = []
    for start, stop in zip(offsets[:-1], offsets[1:]):
        pose, _, _ = horn(condition[start:stop], raw[start:stop])
        clean[start:stop] = transform(pose, condition[start:stop])
        poses.append(pose)
    return clean, np.asarray(poses)


def metric_decode(normalized_poses, centers, scale):
    poses = np.asarray(normalized_poses, dtype=np.float64).copy()
    centers = np.asarray(centers, dtype=np.float64)
    assert centers.shape == (len(poses), 3) and np.isfinite(scale) and scale > 0.
    for index, pose in enumerate(poses):
        pose[:3, 3] = scale * pose[:3, 3] - pose[:3, :3] @ centers[index]
    return poses


def original_noise_step(clean, noise, t, dt):
    """Match the frozen float32 arithmetic before next frozen-model call."""
    clean = np.asarray(clean, dtype=np.float32)
    noise = np.asarray(noise, dtype=np.float32)
    return np.float32(1. - t + dt) * clean + np.float32(t - dt) * noise


CAPS = np.array([2000, 1000, 1000, 2000, 1000, 1000], dtype=np.int64)
LAYOUTS = {"L": [0, 1, 2, 3], "R": [0, 3, 4, 5], "U": list(range(6))}
EXPECTED = [("00", "00_24_629", [24, 21, 18, 629, 627, 624]),
            ("00", "00_210_1656", [210, 205, 199, 1656, 1653, 1650]),
            ("08", "08_569_1554", [569, 566, 563, 1554, 1551, 1548]),
            ("08", "08_583_802", [583, 580, 577, 802, 798, 792])]
ARM_KEYS = ("raw", "clean", "state_before", "state_after", "velocity", "noise", "parts", "relative_poses")


def local_path(value):
    text = str(value).replace("\\", "/")
    path = Path(text)
    if path.exists():
        return path
    if text.startswith("/mnt/") and len(text) > 7 and text[6] == "/":
        return Path(text[5].upper() + ":/" + text[7:])
    return host_path(text)


def load_npz(path, keys=None):
    with np.load(path, allow_pickle=False) as saved:
        selected = saved.files if keys is None else keys
        # Only explicitly whitelisted fields are loaded from parent banks.
        assert not any("gt" in key.lower() or "truth" in key.lower() or "error" in key.lower() for key in selected)
        result = {key: saved[key] for key in selected}
    for value in result.values():
        if value.dtype.kind in "bifu":
            assert np.isfinite(value).all()
    return result


def expected_files(pair):
    names = [pair + "_input", pair + "_old_native"]
    for arm in ("I", "P", "C", "U"):
        names.extend([pair + "_" + arm, pair + "_" + arm + "_repeat", pair + "_" + arm + "_dummy"])
    names.extend(pair + "_C_s" + str(step) for step in range(5))
    names.extend(pair + "_native_" + window for window in ("L", "R", "U"))
    names.extend([pair + "_F", pair + "_PF"])
    return {"bank/" + name + ".npz" for name in names}


def check_provenance(directory):
    freeze = read_json(directory / "freeze.json")
    assert freeze["stage"] == "D1"
    assert freeze["counts"] == CAPS.tolist() and freeze["layouts"] == LAYOUTS
    assert len(freeze["pairs"]) == 4
    assert [(row["seq"], row["pair"], [scan["id"] for scan in row["scans"]]) for row in freeze["pairs"]] == EXPECTED
    assert any(local_path(path).resolve() == Path(__file__).resolve() for path in freeze["files"])
    for path, digest in freeze["files"].items():
        assert sha256(local_path(path)) == digest, path
    manifest = read_json(directory / "manifest.json")
    assert manifest["stage"] == "D1" and manifest["pairs"] == freeze["pairs"]
    assert manifest["counts"] == CAPS.tolist() and manifest["layouts"] == LAYOUTS
    assert manifest["input_whitelist"] == ["points", "cond", "centers", "scale", "counts", "noise"]
    assert manifest["feature_whitelist"] == ["features"]
    assert manifest["native_whitelist"] == ["end_point_trajectory", "trajectory"]
    assert sha256(directory / "manifest.json") in freeze["files"].values()
    freeze_hash = sha256(directory / "freeze.json")
    seal = read_json(directory / "bank_seal.json")
    assert seal["stage"] == "D1" and seal["freeze_sha256"] == freeze_hash
    assert seal["bank_sha256"] == sha256(directory / "bank.json")
    expected = set().union(*(expected_files(pair) for _, pair, _ in EXPECTED))
    assert set(seal["files"]) == expected and len(expected) == 96
    for relative, digest in seal["files"].items():
        assert sha256(sealed_path(directory, relative)) == digest, relative
    actual = {path.relative_to(directory).as_posix() for path in (directory / "bank").glob("*.npz")}
    assert actual == expected
    bank = read_json(directory / "bank.json")
    assert bank["stage"] == "D1" and len(bank["rows"]) == 4
    assert [(row["seq"], row["pair"]) for row in bank["rows"]] == [(seq, pair) for seq, pair, _ in EXPECTED]
    assert bank["dataset_gt_read"] is False and bank["pose_accuracy_computed"] is False
    for row in bank["rows"]:
        assert set(row["files"]) == expected_files(row["pair"]) and len(row["files"]) == 24
        assert row["primary_neural_calls"] == {"I": 10, "P": 10, "C": 10, "U": 5, "F": 0, "PF": 0}
        assert row["standalone_neural_calls"] == {"F": 10, "PF": 10}
    checkpoint = bank["checkpoint"]
    assert checkpoint["rap_keys"] == 344 and checkpoint["descriptor_keys"] == 58
    assert checkpoint["strict"] is True and checkpoint["weights_only"] is True
    for filename, key in (("rap_model_12.ckpt", "rap_sha256"), ("mini_spinnet_t.pth", "descriptor_sha256")):
        matches = [digest for path, digest in freeze["files"].items() if Path(str(path).replace("\\", "/")).name == filename]
        assert len(matches) == 1 and matches[0] == checkpoint[key]
    return freeze, bank, seal, freeze_hash, sha256(directory / "bank_seal.json")


def source_binding_seal(directory, freeze_hash, seal_hash):
    path = directory / "source_binding_validation.json"
    source = read_json(path)
    seal = read_json(directory / "source_binding_seal.json")
    assert source["passed"] is True and source["freeze_sha256"] == freeze_hash
    assert source["bank_seal_sha256"] == seal_hash
    assert seal["validation_sha256"] == sha256(path)
    assert seal["freeze_sha256"] == freeze_hash and seal["bank_seal_sha256"] == seal_hash
    assert len(source["rows"]) == 4
    return source


def cache_checks(cache, row):
    old = load_npz(local_path(row["old_inputs"]), ["points", "cond", "centers", "scale", "counts", "noise"])
    features = load_npz(local_path(row["features"]), ["features"])["features"]
    check_exact(cache["points"], old["points"])
    check_exact(cache["features"], features)
    check_close(cache["counts"], CAPS, 0.)
    check_close(old["counts"], CAPS, 0.)
    check_close(cache["ids"], [scan["id"] for scan in row["scans"]], 0.)
    assert cache["points"].shape == (8000, 3) and cache["features"].shape == (8000, 32)
    assert old["noise"].ndim == 3 and old["noise"].shape[1:] == (8000, 3)
    check_exact(cache["old_noise"], old["noise"][0])
    for scan in row["scans"]:
        assert local_path(scan["path"]).stem == f'{int(scan["id"]):06d}'
        assert sha256(local_path(scan["path"])) == scan["sha256"]
    point_parts = np.split(cache["points"], np.cumsum(CAPS)[:-1])
    feature_parts = np.split(cache["features"], np.cumsum(CAPS)[:-1])
    delta = 0.
    for window, ids in LAYOUTS.items():
        pp = [point_parts[i].astype(np.float64) for i in ids]
        counts = CAPS[ids]
        counts_key = window + "_counts"
        check_close(cache[counts_key], counts, 0.)
        check_exact(cache[window + "_features"], np.concatenate([feature_parts[i] for i in ids]))
        centers = np.asarray([p.mean(axis=0) for p in pp])
        anchor = int(np.argmax(counts))
        scale = 1.5 * float(np.max(np.abs(pp[anchor] - centers[anchor])))
        delta = max(delta, check_close(cache[window + "_centers"], centers, 1e-10),
                    check_close([float(cache[window + "_scale"])], [scale], 1e-10))
        cond = np.concatenate([(p - center) / scale for p, center in zip(pp, centers)]).astype(np.float32)
        delta = max(delta, check_close(cache[window + "_cond"], cond, 5e-7))
        # Validate the physical input center conversion independently in meters.
        original = np.concatenate(pp)
        expanded_centers = np.concatenate([np.tile(center, (len(p), 1)) for p, center in zip(pp, centers)])
        delta = max(delta, check_close(cache[window + "_cond"].astype(np.float64) * scale + expanded_centers,
                                      original, 5e-4))
    for key in ("cond", "centers", "scale", "counts"):
        check_exact(cache["U_" + key], old[key])
    for window in ("L", "R"):
        assert cache["noise_" + window].shape == (6000, 3) and cache["noise_" + window].dtype == np.float32
    check_exact(cache["noise_U"], np.concatenate([cache["noise_L"], cache["noise_R"][4000:]]))
    return delta


def metric_factors(cache, raw):
    """Build repeated canonical rows without the D1 runner or projector."""
    points = np.split(cache["points"].astype(np.float64), np.cumsum(CAPS)[:-1])
    visits = [(w, i) for w, ids in enumerate((LAYOUTS["L"], LAYOUTS["R"])) for i in ids]
    offsets = np.r_[0, np.cumsum([len(points[i]) for _, i in visits])]
    raw = np.asarray(raw, dtype=np.float64)
    assert raw.shape == (12000, 3)
    factors = []
    for index, (window, scan) in enumerate(visits):
        sl = slice(int(offsets[index]), int(offsets[index+1]))
        factors.append(dict(index=index, window=window, scan=scan, p=points[scan],
                            ordered_p=points[scan], Y=raw[sl]*float(cache[("L", "R")[window]+"_scale"]),
                            slice=sl))
    return factors, visits, offsets


def joint_checks(cache, raw, saved):
    factors, visits, offsets = metric_factors(cache, raw)
    assert set(saved) >= {"points", "point_counts", "factor_scans", "factor_windows",
                          "factor_rows", "factor_offsets", "scales", "centers", "cond",
                          "raw", "clean", "native_clean", "native_T", "G", "Z", "G_trace",
                          "Z_trace", "objective_trace", "shared_objective_trace", "converged", "sweeps", "rel"}
    check_exact(saved["points"], cache["points"].astype(np.float64))
    check_exact(saved["point_counts"], CAPS)
    check_exact(saved["factor_scans"], [i for _,i in visits])
    check_exact(saved["factor_windows"], [w for w,_ in visits])
    check_exact(saved["factor_offsets"], offsets)
    check_exact(saved["factor_rows"], np.concatenate([np.arange(CAPS[i]) for _,i in visits]))
    check_exact(saved["scales"], [cache["L_scale"],cache["R_scale"]])
    check_exact(saved["centers"], np.concatenate([cache["L_centers"],cache["R_centers"]]))
    check_exact(saved["cond"], np.concatenate([cache["L_cond"],cache["R_cond"]]))
    check_exact(saved["raw"], np.asarray(raw,dtype=np.float64))
    gauges, poses, trace, fits, minima, shared, gtrace, ztrace = solve_horn(factors, 2, 6)
    assert bool(saved["converged"]) and int(saved["sweeps"]) == len(trace)-1 <= 64
    maxima = [check_close(saved["objective_trace"],trace,1e-7),
              check_close(saved["shared_objective_trace"],shared,1e-7),
              check_close(saved["G_trace"],np.stack([[entry[w] for w in range(2)] for entry in gtrace]),1e-7),
              check_close(saved["Z_trace"],np.stack([[entry[i] for i in range(6)] for entry in ztrace]),1e-7)]
    for w in range(2):
        check_rotation(saved["G"][w],1e-10)
        maxima.append(check_close(saved["G"][w],gauges[w],1e-7))
    for i in range(6):
        check_rotation(saved["Z"][i],1e-10)
        maxima.append(check_close(saved["Z"][i],poses[i],1e-7))
    native = np.empty_like(raw,dtype=np.float64)
    clean = np.empty_like(raw,dtype=np.float64)
    for f in factors:
        w,i,sl = f["window"],f["scan"],f["slice"]
        scale = float(cache[("L","R")[w]+"_scale"])
        local = fits[(w,i)]
        maxima.append(check_close(saved["native_T"][f["index"]],local,1e-7))
        native[sl] = transform(local,f["p"])/scale
        clean[sl] = transform(inverse(gauges[w])@poses[i],f["p"])/scale
    maxima.append(check_close(saved["native_clean"],native,1e-7))
    maxima.append(check_close(saved["clean"],clean,1e-7))
    expected = inverse(poses[0])@poses[3]
    maxima.append(check_close(saved["rel"],expected,1e-7))
    if "rel01" in saved:
        maxima.append(check_close(saved["rel01"],inverse(poses[0])@poses[1],1e-7))
    return max(maxima), expected, clean


def arm_checks(cache, arm, arr, freeze):
    n=8000 if arm=="U" else 12000
    assert arr["noise"].shape==(n,3) and arr["noise"].dtype==np.float32
    for key in ("raw","clean","state_before","state_after","velocity"):
        assert arr[key].shape==(5,n,3) and arr[key].dtype==np.float32
    expected_noise=cache["noise_U"] if arm=="U" else np.concatenate([cache["noise_L"],cache["noise_R"]])
    check_exact(arr["noise"],expected_noise)
    check_exact(arr["state_before"][0],expected_noise)
    max_state=0.
    for step in range(5):
        t=1-step*.2
        if step: check_exact(arr["state_before"][step],arr["state_after"][step-1])
        max_state=max(max_state,check_close(arr["raw"][step],
                     arr["state_before"][step]-np.float32(t)*arr["velocity"][step],freeze["gates"]["state_recurrence_tol"]),
                     check_close(arr["state_after"][step],
                     original_noise_step(arr["clean"][step],arr["noise"],t,.2),freeze["gates"]["state_recurrence_tol"]))
    windows=("U",) if arm=="U" else ("L","R")
    native_clean=[];native_parts=[];max_clean=0.;max_pose=0.
    for wi,w in enumerate(windows):
        sl=slice(None) if w=="U" else slice(6000*wi,6000*(wi+1))
        cond=cache[w+"_cond"]; counts=cache[w+"_counts"]
        for step in range(5):
            clean,poses=independent_native(cond,arr["raw"][step,sl],counts)
            if arm in ("I","U"):
                max_clean=max(max_clean,check_close(arr["clean"][step,sl],clean,freeze["gates"]["native_normalized_clean_tol"]))
            elif arm=="P":
                # CPU native uses canonical metric p, not float32 normalized q.
                points=np.split(cache["points"].astype(np.float64),np.cumsum(CAPS)[:-1])
                ids=LAYOUTS[w];out=[];off=np.r_[0,np.cumsum(counts)]
                for j,i in enumerate(ids):
                    yy=arr["raw"][step,sl][off[j]:off[j+1]].astype(np.float64)*float(cache[w+"_scale"])
                    pose,_,_=horn(points[i],yy)
                    out.append(transform(pose,points[i])/float(cache[w+"_scale"]))
                max_clean=max(max_clean,check_close(arr["clean"][step,sl],np.concatenate(out),freeze["gates"]["cast_clean_tol"]))
            if step==4:
                native_parts.append(metric_decode(poses,cache[w+"_centers"],float(cache[w+"_scale"])))
    expected_parts=np.concatenate(native_parts)
    max_pose=check_close(arr["parts"],expected_parts,freeze["gates"]["native_metric_pose_tol"])
    expected_rels=[]
    for w,poses in zip(windows,native_parts):
        other=1 if w=="R" else 3
        expected_rels.append(inverse(poses[0])@poses[other])
    max_pose=max(max_pose,check_close(arr["relative_poses"],expected_rels,freeze["gates"]["native_metric_pose_tol"]))
    return dict(max_state_delta=max_state,max_native_clean_delta=max_clean,max_native_pose_delta=max_pose)


def pose_difference(a,b):
    e=inverse(a)@b
    t=float(np.linalg.norm(e[:3,3]))
    angle=float(np.degrees(np.arccos(np.clip((np.trace(e[:3,:3])-1)/2,-1,1))))
    return dict(max_entry=float(np.max(np.abs(a-b))),translation_m=t,rotation_deg=angle)


def validate(directory):
    started=time.monotonic()
    freeze,bank,seal,freeze_hash,seal_hash=check_provenance(directory)
    source=source_binding_seal(directory,freeze_hash,seal_hash)
    summaries=[]; max_delta=0.; responses=0; max_native_clean=0.;max_native_pose=0.
    for meta in freeze["pairs"]:
        pair=meta["pair"]
        cache=load_npz(directory/"bank"/(pair+"_input.npz"))
        max_delta=max(max_delta,cache_checks(cache,meta))
        old=load_npz(local_path(meta["old_native"]),["end_point_trajectory","trajectory"])
        replay=load_npz(directory/"bank"/(pair+"_old_native.npz"))
        check_exact(replay["raw"],old["end_point_trajectory"])
        check_exact(replay["state_after"],old["trajectory"])
        arms={};checks={}
        for arm in ("I","P","C","U"):
            arr=load_npz(directory/"bank"/(pair+"_"+arm+".npz"))
            arms[arm]=arr;checks[arm]=arm_checks(cache,arm,arr,freeze)
            max_native_clean=max(max_native_clean,checks[arm]["max_native_clean_delta"])
            max_native_pose=max(max_native_pose,checks[arm]["max_native_pose_delta"])
            for kind in ("repeat","dummy"):
                again=load_npz(directory/"bank"/(pair+"_"+arm+"_"+kind+".npz"))
                for key in ARM_KEYS:
                    check_exact(arr[key],again[key])
                if arm=="C":
                    for key in ("joint_relative_pose","joint_G","joint_Z"):check_exact(arr[key],again[key])
                assert len(again)==len(arr)
        for w in ("L","R","U"):
            native=load_npz(directory/"bank"/(pair+"_native_"+w+".npz"))
            arr=arms["U"] if w=="U" else arms["I"]
            sl=slice(None) if w=="U" else slice(0,6000) if w=="L" else slice(6000,12000)
            check_exact(native["raw"],arr["raw"][:,sl]);check_exact(native["state_after"],arr["state_after"][:,sl])
        cmax=0.;csolutions=[]
        for step in range(5):
            solution=load_npz(directory/"bank"/(pair+f"_C_s{step}.npz"))
            delta,rel,clean=joint_checks(cache,arms["C"]["raw"][step],solution)
            cmax=max(cmax,delta)
            check_exact(arms["C"]["clean"][step],solution["clean"].astype(np.float32))
            csolutions.append(solution)
        check_close(arms["C"]["joint_relative_pose"],csolutions[-1]["rel"],freeze["gates"]["double_pose_tol"])
        check_close(arms["C"]["joint_G"],csolutions[-1]["G"],freeze["gates"]["double_pose_tol"])
        check_close(arms["C"]["joint_Z"],csolutions[-1]["Z"],freeze["gates"]["double_pose_tol"])
        terminal={}
        for name,parent in (("F","I"),("PF","P")):
            value=load_npz(directory/"bank"/(pair+"_"+name+".npz"))
            delta,rel,_=joint_checks(cache,arms[parent]["raw"][-1],value)
            cmax=max(cmax,delta);terminal[name]=value
        max_delta=max(max_delta,cmax)
        policy_clean=float(np.max(np.abs(arms["P"]["clean"]-arms["I"]["clean"])))
        policy_raw=float(np.max(np.abs(arms["P"]["raw"][1:]-arms["I"]["raw"][1:])))
        policy_vel=float(np.max(np.abs(arms["P"]["velocity"][1:]-arms["I"]["velocity"][1:])))
        policy_pose=max(float(np.max(np.abs(a-b))) for a,b in zip(arms["P"]["relative_poses"],arms["I"]["relative_poses"]))
        raw_floor=10*max(freeze["gates"]["raw_normalized_floor"],policy_raw,policy_clean,checks["I"]["max_native_clean_delta"])
        vel_floor=10*max(freeze["gates"]["raw_normalized_floor"],policy_vel,checks["I"]["max_native_clean_delta"])
        pose_floor=10*max(freeze["gates"]["pose_floor"],policy_pose,checks["I"]["max_native_pose_delta"])
        raw_effect=float(np.max(np.abs(arms["C"]["raw"][1:]-arms["P"]["raw"][1:])))
        vel_effect=float(np.max(np.abs(arms["C"]["velocity"][1:]-arms["P"]["velocity"][1:])))
        c_rel=csolutions[-1]["rel"]
        diff_F=pose_difference(c_rel,terminal["F"]["rel"])
        diff_PF=pose_difference(c_rel,terminal["PF"]["rel"])
        admitted=raw_effect>raw_floor and vel_effect>vel_floor and diff_F["max_entry"]>pose_floor and diff_PF["max_entry"]>pose_floor
        responses+=int(admitted)
        summaries.append(dict(pair=pair,identity_checks=checks,max_horn_delta=cmax,
            numeric_policy=dict(clean=policy_clean,raw=policy_raw,velocity=policy_vel,pose_max_entry=policy_pose),
            response=dict(raw_effect=raw_effect,raw_floor=raw_floor,velocity_effect=vel_effect,velocity_floor=vel_floor,
                          final_vs_F=diff_F,final_vs_PF=diff_PF,pose_floor=pose_floor,admitted=admitted),
            union_difference=pose_difference(c_rel,arms["U"]["relative_poses"][0])))
        assert time.monotonic()-started+float(bank["wall_s"])+float(source["wall_s"]) <= freeze["limits"]["wall_s"]
    # All source/bank identities are rechecked after interpretation.
    check_provenance(directory);source_binding_seal(directory,freeze_hash,seal_hash)
    elapsed=time.monotonic()-started
    rss=max(peak_rss_bytes(),int(bank["peak_rss_bytes"]),int(source["peak_rss_bytes"]))
    gpu=max(int(bank["peak_allocated_bytes"]),int(source["peak_allocated_bytes"]))
    total=elapsed+float(bank["wall_s"])+float(source["wall_s"])
    assert total<=freeze["limits"]["wall_s"] and rss<=freeze["limits"]["rss_bytes"] and gpu<=freeze["limits"]["gpu_bytes"]
    artifact=sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())
    assert artifact<=freeze["limits"]["artifact_bytes"]
    output=dict(stage="D1",utc=utc_now(),passed=True,
        decision="ENGINEERING_FEEDBACK_RESPONSE" if responses==freeze["gates"]["response_cases_required"] else "NO_FOUR_PAIR_FEEDBACK_RESPONSE",
        response_cases=responses,required=freeze["gates"]["response_cases_required"],
        rows=summaries,max_independent_delta=max_delta,max_native_clean_delta=max_native_clean,max_native_pose_delta=max_native_pose,
        bank_wall_s=float(bank["wall_s"]),source_binding_wall_s=float(source["wall_s"]),validator_wall_s=elapsed,
        combined_wall_s=total,peak_rss_bytes=rss,peak_allocated_bytes=gpu,artifact_bytes_before_validation=artifact,
        freeze_sha256=freeze_hash,bank_seal_sha256=seal_hash,source_binding_sha256=sha256(directory/"source_binding_validation.json"),
        dataset_gt_read=False,pose_accuracy_computed=False,originality_established=False)
    target=directory/"validation.json"
    assert not target.exists()
    target.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    assert sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())<=freeze["limits"]["artifact_bytes"]
    print(json.dumps({k:output[k] for k in ("decision","response_cases","max_independent_delta","combined_wall_s","artifact_bytes_before_validation")}))
    return output


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,default=Path(__file__).resolve().parents[2]/"docs/maintenance/2026-10-06/shared-identity-engineering-01")
    validate(parser.parse_args().directory)
