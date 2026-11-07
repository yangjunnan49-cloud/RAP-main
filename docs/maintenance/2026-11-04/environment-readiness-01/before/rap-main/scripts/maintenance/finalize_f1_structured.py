"""Summarize validated F1 engineering artifacts without loop GT evaluation."""
import hashlib,json
from pathlib import Path
import numpy as np
BASE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-26/f1-structured-preflight-01')
def read(p):return json.loads(p.read_text())
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    validation=read(BASE/'validation.json');assert validation['passed']
    assert not (BASE/'attempt-01/INCOMPLETE').exists()
    records=read(BASE/'attempt-01/records.json');inputs=read(BASE/'inputs.json')
    local=read(BASE/'local_motion_evaluator_only.json')['rows']
    ordinary=inputs[-1]['key'];T=np.asarray(next(r['T'] for r in records if r['pair']==ordinary and r['arm']=='S'))
    sensitivity=[]
    for arm in ['Sminus','Splus']:
        row=next(r for r in records if r['pair']==ordinary and r['arm']==arm)
        delta=np.linalg.inv(T)@np.asarray(row['T']);r=delta[:3,:3]
        angle=np.degrees(np.arctan2(np.linalg.norm([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])/2,np.clip((np.trace(r)-1)/2,-1,1)))
        sensitivity.append(dict(arm=arm,translation_change_m=float(np.linalg.norm(delta[:3,3])),rotation_change_deg=float(angle)))
    save(BASE/'sensitivity.json',dict(pair=ordinary,changes=sensitivity,interpretation='Sensitivity only, no efficacy or GT loop accuracy evaluated'))
    lines=['# F1 structured-motion generation: engineering preflight','',f"Decision: **{validation['decision']}**.",'',
           'This is a four-pair engineering result on observed KITTI00 data. It is not an efficacy screen, novelty clearance or independent confirmation.','',
           '## Implementation and fixed controls','',
           'An isolated RAP-SLAM sampler retains six scan-specific partitions and projects each visit into a common short-motion group at each clean-endpoint step. Upstream RAP and production defaults were not edited; no hooks or monkeypatches were installed.',
           '', 'The four exact pairs are 24/629, 210/1656, 422/3496 and 956/3859. Each uses two 2000-point anchors and four 1000-point supports. Saved causal within-visit LiDAR motion is the only motion input; GT is loaded only by a separate post-generation local-motion evaluator.',
           '', '| Arm | Role | Points | Sampling wall sum over 4 pairs (s) |','|---|---|---:|---:|']
    for arm,role,n in [('N','Native six-part',8000),('F','Final-only group projection; extra cost after reusing N',8000),('S','Group projection at every step',8000),('P','Matched-point pooling, reused scan descriptors',8000),('A','Anchor-only reference, not equal-data',4000)]:
        wall=sum(r['wall_s'] for r in records if r['arm']==arm)
        lines.append(f'| {arm} | {role} | {n} | {wall:.6f} |')
    ex=validation['execution']
    lines+=['','All use K1/five Euler steps. N/F/S share identical points, descriptors, normalization and noise. Pooling changes normalization and partitioning while retaining the same points/descriptors. F timing is incremental projection cost, not standalone inference latency. Timings are engineering measurements, not a speed-superiority claim.','',
        '## Correctness and resources','',
        f"- Native sampler reproduction maximum endpoint/state delta: {validation['native_max_delta']:.9g}.",
        f"- Independent float64 projected-point maximum delta: {validation['max_independent_projected_delta']:.9g} normalized units.",
        f"- Independent decoded pose maximum matrix delta: {validation['max_independent_pose_delta']:.9g}.",
        f"- Independent projected local-motion maximum matrix residual: {validation['max_constraint_delta']:.9g}.",
        f"- Process wall including model loading and preprocessing: {ex['wall_s']:.3f}s; peak allocated: {ex['peak_allocated']/2**30:.3f}GiB; peak reserved: {ex['peak_reserved']/2**30:.3f}GiB.",
        '- Proper rotations, finite tensors, exact point budgets, normalization roundtrip, reordered replay and precision/RNG restoration checks passed.',
        '- Raw versus projected clean endpoints and noisy trajectories are explicitly saved. Zero constraint residual is enforced geometry, not registration confidence.','',
        '## Estimated-motion sensitivity','',
        'Fixed support-only perturbations on the ordinary pair: jointly +/-0.10m x translation and +/-1 degree yaw. Relative to unperturbed S:',
        '', '| Perturbation | Output translation change m | Output rotation change deg |','|---|---:|---:|']
    for r in sensitivity:lines.append(f"| {r['arm']} | {r['translation_change_m']:.6f} | {r['rotation_change_deg']:.6f} |")
    lines+=['',f"Evaluator-only local-motion error over16 supports: maximum translation {max(r['translation_m'] for r in local):.6f}m; maximum rotation {max(r['rotation_deg'] for r in local):.6f}deg.",
        '', 'These are sensitivity observations, not accuracy or robustness gains. No loop transform was scored against GT. No strength/layer/gate search or learned selector was run.',
        '', '## Next boundary','',
        'F1 establishes executability only. Freeze a separate F2 development protocol with exact cohort exposure, corrected-data convention, K4 seeds, decision margins, common gate, cost and strong comparator before any efficacy outcome. Fresh confirmation is still required. All previous HL/SC/PG stops persist; manuscript remains paused.']
    with (BASE/'REPORT.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    save(BASE/'final_artifact_hashes.json',{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file()})
    print('F1 report complete',validation['decision'])
if __name__=='__main__':main()
