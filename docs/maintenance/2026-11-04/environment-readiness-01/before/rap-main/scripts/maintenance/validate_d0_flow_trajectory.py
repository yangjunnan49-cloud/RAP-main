"""Independent D0 input, saved-checkpoint, geometry and decision audit."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.spatial import cKDTree

MAIN = Path(__file__).resolve().parents[2]
BASE = MAIN / "docs/maintenance/2026-09-28/d0-flow-trajectory-01"
F2 = MAIN / "docs/maintenance/2026-09-27/f2-structured-dev-01"
GT = {"00": MAIN / "docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy",
      "08": MAIN / "docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy"}
sys.path.insert(0, str(MAIN / "scripts/maintenance"))
import fullscan_global_baseline as g1
import v0_ray_visibility as v0


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def close(a, b, tol=1e-6):
    assert abs(float(a)-float(b)) <= tol, (a, b)


def torch_decode(cond, raw, counts, centers, scale):
    cuts = np.r_[0, np.cumsum(counts)]
    parts=[]
    for k in (0,3):
        x=torch.from_numpy(cond[cuts[k]:cuts[k+1]].astype(np.float64))
        y=torch.from_numpy(raw[cuts[k]:cuts[k+1]].astype(np.float64))
        xm,ym=x.mean(0),y.mean(0)
        u,_,vt=torch.linalg.svd((x-xm).T@(y-ym))
        d=torch.sign(torch.det(vt.T@u.T))
        r=vt.T@torch.diag(torch.stack([torch.ones_like(d),torch.ones_like(d),d]))@u.T
        t=ym-xm@r.T
        p=np.eye(4)
        p[:3,:3]=r.numpy()
        p[:3,3]=scale*t.numpy()-p[:3,:3]@centers[k]
        parts.append(p)
    return np.linalg.inv(parts[0])@parts[1]


def label(pose, truth):
    e=np.linalg.inv(truth)@pose
    r=e[:3,:3]
    rte=float(np.linalg.norm(e[:3,3]))
    skew=np.array([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])
    rre=float(np.degrees(np.arctan2(np.linalg.norm(skew)/2,
        np.clip((np.trace(r)-1)/2,-1,1))))
    return rte,rre


def geometry(target, source, pose):
    mapped=source@pose[:3,:3].T+pose[:3,3]
    da=cKDTree(target).query(mapped,k=1,workers=1)[0]
    db=cKDTree(mapped).query(target,k=1,workers=1)[0]
    return (float((np.mean(da<1)+np.mean(db<1))/2),float((np.mean(da)+np.mean(db))/2))


def main():
    assert not (BASE/"validation.json").exists() and not (BASE/"INCOMPLETE").exists()
    checks=0
    for name,digest in read(BASE/"freeze.json")["files"].items():
        assert sha(Path(name))==digest,name
        checks+=1
    bank=read(BASE/"bank.json")
    seal=read(BASE/"bank_seal.json")
    outcomes=read(BASE/"outcomes.json")
    summary=read(BASE/"summary.json")
    assert sha(BASE/"bank.json")==seal["sha256"]
    assert len(bank)==len(outcomes)==200
    assert seal["wall_s"]<=1200 and seal["peak_rss_gib"]<=4
    assert sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())<=50*1024**2
    checks+=4
    spots=0
    for seq in ("00","08"):
        parents=read(F2/seq/"evaluator_only_decisions.json")
        records=read(F2/seq/"records.json")
        gates=read(F2/seq/"gates.json")
        gt=np.load(GT[seq],allow_pickle=False)
        rows=[r for r in bank if r["sequence"]==seq]
        labels=[r for r in outcomes if r["sequence"]==seq]
        assert len(rows)==len(labels)==len(parents)==100
        for ix,(row,out,parent) in enumerate(zip(rows,labels,parents)):
            pair=f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            assert row["pair"]==out["pair"]==pair and out["stratum"]==parent["stratum"]
            native=sorted((r for r in records if r["pair"]==pair and r["arm"]=="N"),key=lambda r:r["generation"])
            assert len(native)==4 and [r["generation"] for r in native]==list(range(4))
            chosen=min(native,key=lambda r:(r["rigidity_rmse_m"],r["generation"]))["generation"]
            assert chosen==row["selected_generation"]
            truth=np.linalg.inv(gt[parent["source_i"]])@gt[parent["source_j"]]
            assert len(row["generations"])==len(out["grid"])==4
            oracle=[]
            for k,gen in enumerate(row["generations"]):
                assert gen["generation"]==k and len(gen["T_steps"])==len(gen["rigidity_steps_m"])==5
                close(np.mean(gen["rigidity_steps_m"]),native[k]["rigidity_rmse_m"])
                np.testing.assert_allclose(gen["T_steps"][4],native[k]["T"],atol=1e-4,rtol=0)
                assert gen["final_decode_delta"]<=1e-4
                for step,pose_list in enumerate(gen["T_steps"]):
                    pose=np.asarray(pose_list)
                    assert pose.shape==(4,4) and np.isfinite(pose).all()
                    assert np.max(np.abs(pose[:3,:3].T@pose[:3,:3]-np.eye(3)))<1e-8
                    close(np.linalg.det(pose[:3,:3]),1,1e-8)
                    rte,rre=label(pose,truth)
                    lab=out["grid"][k][step]
                    close(lab["RTE_m"],rte)
                    close(lab["RRE_deg"],rre)
                    assert lab["strict"]==(rte<=1 and rre<=5)
                    close(lab["clipped_error"],min(5,max(rte,rre/5)))
                    checks+=1
            oracle=[any(out["grid"][k][s]["strict"] for k in range(4)) for s in range(5)]
            assert out["step_oracle"]==oracle
            assert out["early_strict_steps"]==[s for s in range(4) if oracle[s]]
            assert oracle[4]==parent["methods"]["N-OR4"]["strict"]
            old=gates[pair]["N"][str(chosen)]
            close(row["selected_gates"]["final"]["overlap"],old["overlap_ratio"],1e-5)
            close(row["selected_gates"]["final"]["mean_dist"],old["mean_dist"],1e-5)
            for name,step in (("penultimate",3),("final",4)):
                gate=row["selected_gates"][name]
                assert gate["step"]==step
                np.testing.assert_allclose(gate["T"],row["generations"][chosen]["T_steps"][step],atol=1e-12,rtol=0)
                assert gate["accepted"]==(gate["overlap"]>=.7 and gate["mean_dist"]<=2.5)
                rte,rre=label(np.asarray(gate["T"]),truth)
                lab=out["selected"][name]
                close(lab["RTE_m"],rte);close(lab["RRE_deg"],rre)
                assert lab["strict"]==(rte<=1 and rre<=5)
                assert lab["accepted"]==gate["accepted"]
                assert lab["correct_accepted"]==(lab["strict"] and lab["accepted"])
                assert lab["incorrect_accepted"]==(not lab["strict"] and lab["accepted"])
            if ix in (0,25,50,75):
                folder=F2/seq/pair
                with np.load(folder/"inputs.npz",allow_pickle=False) as inp:
                    cond,counts,centers,scale=(inp[x] for x in ("cond","counts","centers","scale"))
                for k in range(4):
                    with np.load(folder/f"N{k}.npz",allow_pickle=False) as z:
                        raw=z["end_point_trajectory"]
                    for step in range(5):
                        p=torch_decode(cond,raw[step],counts,centers,float(scale))
                        np.testing.assert_allclose(p,row["generations"][k]["T_steps"][step],atol=1e-7,rtol=0)
                        spots+=1
                target_path,source_path=g1.pair_scans(seq,pair)
                g=v0.gate_backend()
                target=g.preprocess(g1.load_scan(target_path))[0]
                source=g.preprocess(g1.load_scan(source_path))[0]
                for name in ("penultimate","final"):
                    overlap,mean_dist=geometry(target,source,np.asarray(row["selected_gates"][name]["T"]))
                    close(overlap,row["selected_gates"][name]["overlap"],1e-10)
                    close(mean_dist,row["selected_gates"][name]["mean_dist"],1e-8)
                checks+=22
        pos=[r for r in labels if r["stratum"]!="confuser"]
        missing=[r for r in pos if not r["step_oracle"][4]]
        s=summary["sequences"][seq]
        assert len(pos)==75 and s["final_K4_unavailable"]==len(missing)
        assert s["oracle_strict_by_step"]==[sum(r["step_oracle"][step] for r in pos) for step in range(5)]
        assert s["transient_missing_final"]==[r["pair"] for r in missing if r["early_strict_steps"]]
        assert s["first_last_early_step"]=={r["pair"]:[min(r["early_strict_steps"]),max(r["early_strict_steps"])] for r in missing if r["early_strict_steps"]}
        for name in ("penultimate","final"):
            m=s["methods"][name]
            assert m["strict"]==sum(r["selected"][name]["strict"] for r in pos)
            assert m["correct_accepts"]==sum(r["selected"][name]["correct_accepted"] for r in pos)
            assert m["incorrect_accepts"]==sum(r["selected"][name]["incorrect_accepted"] for r in labels)
            assert m["confuser_accepts"]==sum(r["selected"][name]["accepted"] for r in labels if r["stratum"]=="confuser")
            close(m["clipped_error"],np.mean([r["selected"][name]["clipped_error"] for r in pos]))
        assert s["strict_gains"]==[r["pair"] for r in pos if r["selected"]["penultimate"]["strict"] and not r["selected"]["final"]["strict"]]
        assert s["strict_losses"]==[r["pair"] for r in pos if r["selected"]["final"]["strict"] and not r["selected"]["penultimate"]["strict"]]
        assert s["new_correct_accepts"]==[r["pair"] for r in pos if r["selected"]["penultimate"]["correct_accepted"] and not r["selected"]["final"]["correct_accepted"]]
        assert s["lost_correct_accepts"]==[r["pair"] for r in pos if r["selected"]["final"]["correct_accepted"] and not r["selected"]["penultimate"]["correct_accepted"]]
        assert s["newly_incorrect_accepts"]==[r["pair"] for r in labels if r["selected"]["penultimate"]["incorrect_accepted"] and not r["selected"]["final"]["incorrect_accepted"]]
        assert s["ordinary_strict_losses"]==[r["pair"] for r in pos if r["stratum"]=="ordinary" and r["selected"]["final"]["strict"] and not r["selected"]["penultimate"]["strict"]]
        for st,b in s["by_stratum"].items():
            ss=[r for r in labels if r["stratum"]==st]
            assert b["n"]==len(ss)==25
            assert b["oracle_by_step"]==[sum(r["step_oracle"][step] for r in ss) for step in range(5)]
            assert b["selected_step3_strict"]==sum(r["selected"]["penultimate"]["strict"] for r in ss)
            assert b["selected_final_strict"]==sum(r["selected"]["final"]["strict"] for r in ss)
        checks+=1
    a,b=summary["sequences"]["08"],summary["sequences"]["00"]
    ap,af=a["methods"]["penultimate"],a["methods"]["final"]
    bp,bf=b["methods"]["penultimate"],b["methods"]["final"]
    conditions={"transient_08":len(a["transient_missing_final"])>=5,
        "fixed_step3_08":ap["strict"]-af["strict"]>=5 and ap["correct_accepts"]-af["correct_accepts"]>=2,
        "accept_safety":not a["newly_incorrect_accepts"] and not b["newly_incorrect_accepts"],
        "00_guard":bp["strict"]-bf["strict"]>=-2,
        "ordinary_guard":len(a["ordinary_strict_losses"])<=1 and len(b["ordinary_strict_losses"])<=1,
        "cost":seal["wall_s"]<=1200 and seal["peak_rss_gib"]<=4 and sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())<=50*1024**2}
    assert summary["conditions"]==conditions
    decision="NO_TRANSIENT_CANDIDATE_EVIDENCE" if not conditions["transient_08"] else "CHECKPOINT_EXECUTABLE_SIGNAL" if all(conditions.values()) else "TRANSIENT_ONLY"
    assert summary["decision"]==decision
    checks+=2
    with (BASE/"validation.json").open("x",encoding="utf-8") as f:
        json.dump({"passed":True,"checks":checks,"spotcheck_poses":spots,
                   "decision":decision,"bank_sha256":seal["sha256"]},f,indent=2)
        f.write("\n")
    print("D0 validation passed",checks,"checks",spots,"spot poses",flush=True)


if __name__=="__main__":
    main()
