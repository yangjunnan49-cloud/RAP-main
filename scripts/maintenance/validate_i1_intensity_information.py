"""Independent full I1 input, binding, control and decision validation."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
SLAM = ROOT.parent / "RAP-SLAM"
F2 = ROOT / "docs/maintenance/2026-09-27/f2-structured-dev-01"
C1 = ROOT / "docs/maintenance/2026-09-28/c1-descriptor-information-01"
OUT = ROOT / "docs/maintenance/2026-09-29/i1-intensity-information-01"
GT = {"00": ROOT / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": ROOT / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def close(a, b, tol=1e-10):
    assert abs(a-b) < tol, (a, b)


def main():
    checks = 0
    for name, expected in read(OUT / "freeze.json")["files"].items():
        assert digest(Path(name)) == expected, name
        checks += 1
    manifest = read(OUT / "bank.json")
    seal = read(OUT / "bank_seal.json")
    assert len(manifest) == seal["rows"] == 200
    assert digest(OUT / "bank.json") == seal["sha256"]
    assert seal["gt_parsed"] is False
    checks += 3
    outputs = read(OUT / "pairs.json")
    assert len(outputs) == 200 and [x["pair"] for x in outputs] == [x["pair"] for x in manifest]
    checks += 1
    c1 = {r["pair"]: r for r in read(C1 / "pairs.json")}
    sys.path.insert(0, str(SLAM))
    from rap_slam.real_dataset import kitti_vertical_correction
    for seq in ("00", "08"):
        gt = np.load(GT[seq], allow_pickle=False)
        inputs = {r["key"]: r for r in read(F2 / f"inputs_{seq}.json")}
        for saved, reported in zip((x for x in manifest if x["pair"].startswith(seq+"_")),
                                   (x for x in outputs if x["pair"].startswith(seq+"_"))):
            pair = saved["pair"]
            assert digest(Path(saved["file"])) == saved["sha256"]
            inp = inputs[pair]
            with np.load(F2 / seq / pair / "inputs.npz", allow_pickle=False) as z:
                points = z["points"].astype(np.float64)
            with np.load(saved["file"], allow_pickle=False) as z:
                intensity, distances = z["intensities"], z["distances"]
            assert intensity.shape == distances.shape == (2, 2000)
            for role, idx, lo in ((0, 0, 0), (1, 3, 4000)):
                scan = inp["scans"][idx]
                raw = np.fromfile(scan["path"], dtype="<f4").reshape(-1, 4)
                assert digest(Path(scan["path"])) == scan["sha256"]
                keep = np.linalg.norm(raw[:, :3], axis=1) >= 1.5
                raw = raw[keep]
                cloud = kitti_vertical_correction(raw[:, :3]).astype(np.float32)
                d, n = cKDTree(cloud).query(points[lo:lo+2000])
                assert np.array_equal(intensity[role], raw[n, 3])
                assert np.max(np.abs(distances[role]-d)) < 1e-7
                close(saved["within_0p5"][role], np.count_nonzero(d <= .5)/2000)
                assert saved["distinct"][role] == len(np.unique(raw[n, 3]))
                close(saved["p95_m"][role], np.percentile(d, 95))
                checks += 6
            i, j = inp["source_i"], inp["source_j"]
            transform = np.linalg.solve(gt[i], gt[j])
            target = points[:2000]
            moved = points[4000:6000] @ transform[:3, :3].T + transform[:3, 3]
            distance, match = cKDTree(target).query(moved)
            eligible = distance <= 1.0
            n = int(eligible.sum())
            assert n == reported["eligible_points"] == c1[pair]["eligible_points"]
            close(reported["eligible_fraction"], n/2000)
            assert reported["stratum"] == c1[pair]["stratum"]
            assert reported["native_candidate_available"] == c1[pair]["native_candidate_available"]
            checks += 4
            if not n:
                assert reported["true_difference"] is None and reported["advantage"] is None
                continue
            true = np.abs(intensity[1, eligible].astype(np.float64)-intensity[0, match[eligible]].astype(np.float64)).mean()
            close(reported["true_difference"], true)
            radial = np.linalg.norm(target, axis=1)
            bin_index = np.digitize(radial, [20., 40., 60., 80.], right=False)
            control = []
            for k in range(16):
                seed = int(hashlib.sha256(("I1|"+pair+"|"+str(k)).encode()).hexdigest()[:16], 16)
                rng = np.random.default_rng(seed)
                mapping = np.arange(2000)
                for b in range(5):
                    members = np.where(bin_index == b)[0]
                    mapping[members] = rng.permutation(members)
                value = float(np.mean(np.abs(intensity[1, eligible].astype(np.float64)-intensity[0, mapping[match[eligible]]].astype(np.float64))))
                close(reported["control_differences"][k], value)
                control.append(value)
                checks += 1
            close(reported["control_mean_difference"], np.mean(control))
            close(reported["advantage"], np.mean(control)-true)
            checks += 3
    primary = [x for x in outputs if x["sequence"] == "08" and x["stratum"] != "confuser" and
               not x["native_candidate_available"] and x["eligible_fraction"] >= .1]
    s = read(OUT / "summary.json")
    assert len(primary) == s["primary"]["pairs"] == 33
    effects = [x["advantage"] for x in primary]
    close(s["primary"]["median_advantage"], np.median(effects))
    assert s["primary"]["positive_advantage_pairs"] == sum(x > 0 for x in effects)
    binding = all(min(r["within_0p5"]) >= .95 and min(r["distinct"]) >= 8 for r in manifest)
    assert s["binding_adequate"] == binding
    expected = "INCONCLUSIVE_INTENSITY_BINDING" if not binding else (
        "INTENSITY_INFORMATION_SIGNAL" if np.median(effects) >= .03 and sum(x > 0 for x in effects)*3 >= len(effects)*2
        else "NO_INTENSITY_INFORMATION_SIGNAL")
    assert s["decision"] == expected and s["bank_sha256"] == seal["sha256"]
    checks += 5
    with (OUT / "validation.json").open("x", encoding="utf-8") as f:
        json.dump({"passed": True, "checks": checks, "bank_sha256": seal["sha256"]}, f, indent=2)
        f.write("\n")
    print("I1 independent validation", checks, "checks")


if __name__ == "__main__":
    main()
