"""Post-outcome oracle-input cost accounting; no optimization or gain claim."""
import os
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[name]='1'
from pathlib import Path
import numpy as np
import rotation_protected_map_pilot as run
import validate_shared_plane_map_pilot as direct

BASE=run.BASE/'objective-diagnosis-01'


def diagnose():
    run.verify();assert run.read(run.BASE/'validation.json')['passed']
    files=[Path(__file__),run.BASE/'POSTHOC_DIAGNOSIS_SCOPE.md',run.BASE/'freeze.json',run.BASE/'bank_seal.json',run.BASE/'results.json',run.BASE/'validation.json']
    files+=list((run.BASE/'bank').iterdir())
    files+=[run.old.DATA/f'poses/{s}.txt' for s in run.SEQUENCES]+[run.old.DATA/f'sequences/{s}/calib.txt' for s in run.SEQUENCES]
    BASE.mkdir()
    run.save(BASE/'freeze.json',dict(utc=run.utc(),files={str(p):run.sha(p) for p in files},post_outcome=True,oracle_inputs=True,
             optimizer_calls=0,performance_gain_claim=False))
    rows={};cost_delta=fd_delta=0.
    for seq in run.SEQUENCES:
        z=np.load(run.BASE/f'bank/{seq}.npz',allow_pickle=False)
        stats={name:z[name] for name in run.FIELDS};masks=dict(train=~z['holdout'],holdout=z['holdout'])
        points=[z[f'points_{i}'] for i in range(16)];labels=[z[f'label_{i}'] for i in range(16)]
        truth=run.old.gt(seq)[z['frames']]
        reference=np.array([run.old.alg.proper(t) for t in np.linalg.inv(truth[0])@truth]);reference[0]=np.eye(4)
        native=z['B'];shapes={}
        for source,poses in (('O',native),('reference',reference)):
            local=poses.copy();local[:8]=np.linalg.inv(poses[0])@poses[:8];local[8:]=np.linalg.inv(poses[-1])@poses[8:]
            local[0]=np.eye(4);local[-1]=np.eye(4);shapes[source]=local
        conditions={}
        for shape,name in (('O','Oshape'),('reference','reference_shape')):
            for position,tag in (('native','native_placement'),('reference','reference_translation')):
                endpoint=native[-1].copy()
                if position=='reference':endpoint[:3,3]=reference[-1,:3,3]
                poses=shapes[shape].copy();poses[8:]=endpoint@shapes[shape][8:];poses[-1]=endpoint
                if shape=='O' and position=='native':poses=native.copy()
                conditions[name+'__'+tag]=poses
        poses=shapes['reference'].copy();poses[8:]=reference[-1]@shapes['reference'][8:];poses[-1]=reference[-1]
        conditions['reference_shape__full_reference_placement']=poses
        case={}
        for name,poses in conditions.items():
            values={}
            explicit=direct.direct_planes(points,labels,poses,len(stats['counts']))
            for part,mask in masks.items():
                moment=run.cv.geometry(run.cv.subset(stats,mask),poses)
                variance=np.maximum([p[1][0] for p,keep in zip(explicit,mask) if keep],0.)
                rms=float(np.sqrt(np.mean(variance)));values[part+'_rms_m']=moment['rms_m']
                cost_delta=max(cost_delta,abs(rms-moment['rms_m']))
            if name!='reference_shape__full_reference_placement':
                train=run.cv.subset(stats,masks['train']);gradient=run.translation.system(train,poses,poses)[1]
                displacement=poses[-1,:3,:3].T@(reference[-1,:3,3]-poses[-1,:3,3]);length=float(np.linalg.norm(displacement))
                values.update(translation_gradient_body=gradient.tolist(),distance_to_reference_translation_m=length)
                if length>1e-12:
                    direction=displacement/length;slope=float(gradient@direction)
                    plus,minus=poses.copy(),poses.copy();shift=poses[-1,:3,:3]@(direction*1e-5)
                    plus[8:,:3,3]+=shift;minus[8:,:3,3]-=shift
                    vp=direct.direct_planes(points,labels,plus,len(stats['counts']));vm=direct.direct_planes(points,labels,minus,len(stats['counts']))
                    cp=.5*np.mean([max(p[1][0],0.) for p,keep in zip(vp,masks['train']) if keep])/run.plane.GEOMETRY_SIGMA**2
                    cm=.5*np.mean([max(p[1][0],0.) for p,keep in zip(vm,masks['train']) if keep])/run.plane.GEOMETRY_SIGMA**2
                    fd=(cp-cm)/2e-5;fd_delta=max(fd_delta,abs(fd-slope))
                    values.update(cost_slope_towards_reference_per_m=slope,independent_directional_fd=fd)
            case[name]=values
        rows[seq]=case
    assert cost_delta<1e-8 and fd_delta<1e-4
    run.save(BASE/'results.json',dict(utc=run.utc(),rows=rows,post_outcome=True,oracle_inputs=True,optimizer_calls=0,performance_gain_claim=False))
    run.save(BASE/'validation.json',dict(passed=True,explicit_point_cost_max_delta=cost_delta,selected_directional_fd_max_delta=fd_delta,
             conditions=15,physical_causal_identification=False))
    for path,digest in run.read(BASE/'freeze.json')['files'].items():assert run.sha(path)==digest
    run.save(BASE/'output_seal.json',dict(files={p.name:run.sha(p) for p in BASE.iterdir()},optimizer_calls=0,primary_CV2_outcome_unchanged=True))
    print('CV2 zero-optimizer diagnosis', {s:{k:[v['train_rms_m'],v['holdout_rms_m'],v.get('cost_slope_towards_reference_per_m')] for k,v in r.items()} for s,r in rows.items()},flush=True)


if __name__=='__main__':run.record_stage('posthoc_objective_diagnosis',diagnose)
