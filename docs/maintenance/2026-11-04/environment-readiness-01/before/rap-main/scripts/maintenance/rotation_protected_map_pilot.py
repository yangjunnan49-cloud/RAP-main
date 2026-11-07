"""CV2 three-case fixed-rotation development pilot, immutable CV1 controls."""
import os
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import importlib.metadata
import json
import resource
import shutil
import time
import traceback
from pathlib import Path
import numpy as np
import cross_visit_map_pilot as cv
import cross_visit_map_attempt02 as rigid
import rotation_protected_map as translation

old,plane=cv.old,cv.plane
read,save,sha,utc=cv.read,cv.save,cv.sha,cv.utc
BASE=old.MAIN/'docs/maintenance/2026-10-09/rotation-protected-map-pilot-01'
SEQUENCES=('00','05','06')
FIELDS=('counts','means','seconds','keys')


def verify():
    frozen=read(BASE/'freeze.json')
    for path,digest in frozen['files'].items():
        assert sha(path)==digest,path
    for package,version in frozen['packages'].items():
        assert importlib.metadata.version(package)==version
    return frozen


def freeze():
    cv.previous.check_delivery(cv.BASE)
    bindings={}
    inputs=[]
    for seq in SEQUENCES:
        root=old.source(seq)
        rows=read(root/'accepted_loops.json')
        assert rows
        selected={name:rows[0][name] for name in ('i','j','T_rel','measurement_id')}
        keys=read(root/'keyframes.json')
        frames=read(root/'source_frames.json')['source_frame_ids']
        visits=[keys[keys.index(endpoint)-7:keys.index(endpoint)+1] for endpoint in (selected['i'],selected['j'])]
        assert all(len(g)==8 and g[-1]==e for g,e in zip(visits,(selected['i'],selected['j'])))
        assert not set(visits[0]).intersection(visits[1])
        raw=[dict(visit=v,node=int(k),frame=int(frames[k]),path=str(old.rawpath(seq,int(frames[k])))) for v,g in enumerate(visits) for k in g]
        assert len({x['path'] for x in raw})==16
        for row in raw:
            row.update(bytes=Path(row['path']).stat().st_size,sha256=sha(row['path']))
        bindings[seq]=dict(selected=selected,visits=visits,raw=raw,original_accepted_index=0)
        inputs += [root/name for name in ('accepted_loops.json','keyframes.json','source_frames.json','odom_poses.txt')]
        inputs += [old.DATA/f'poses/{seq}.txt',old.DATA/f'sequences/{seq}/calib.txt']
        inputs += [Path(row['path']) for row in raw]
    sources=[Path(__file__),Path(__file__).with_name('validate_rotation_protected_map_pilot.py'),BASE/'PROTOCOL.md',BASE/'algorithm_staging.py',
             old.SLAM/'scripts/rotation_protected_map.py',old.SLAM/'scripts/cross_visit_map_attempt02.py',
             old.SLAM/'scripts/shared_plane_map.py',old.SLAM/'scripts/measured_map_reoptimization.py',
             Path(cv.__file__),Path(old.__file__),Path(cv.previous.prior.__file__),Path(cv.previous.__file__),
             Path(__file__).with_name('validate_cross_visit_map_pilot.py'),Path(__file__).with_name('validate_shared_plane_map_pilot.py')]
    assert sha(BASE/'algorithm_staging.py')==sha(old.SLAM/'scripts/rotation_protected_map.py')
    snapshot=BASE/'source_snapshot'
    snapshot.mkdir()
    files=sources+inputs
    for i,source in enumerate(sources):
        target=snapshot/f'{i:02d}-{source.name}'
        shutil.copyfile(source,target)
        files.append(target)
    files += [cv.BASE/name for name in ('DELIVERY_SEAL.json','NEXT_ROUND_PLAN.md','STATUS.json')]
    files += [cv.BASE/'attempt-02'/name for name in ('freeze.json','preflight.json','bank_seal.json','bank_validation.json','validation.json','bank/case.npz','bank/summary.json')]
    save(BASE/'freeze.json',dict(utc=utc(),files={str(p):sha(p) for p in files},bindings=bindings,
         packages={p:importlib.metadata.version(p) for p in ('numpy','scipy')},new_numeric_gt_parsed=False,
         new_raw_coordinates_parsed=False,exposed_development=True,primary_sequences=SEQUENCES,
         cpu_wall_cap_s=1800,rss_cap_bytes=2*2**30,artifact_cap_bytes=512*2**20))
    (BASE/'INCOMPLETE').write_text('CV2 requires complete preflight/bank/decision validation\n')
    print('CV2 frozen',len(set(files)),'entries',{s:[b['selected']['i'],b['selected']['j']] for s,b in bindings.items()},flush=True)


def preflight():
    verify()
    assert read(cv.BASE/'attempt-02/preflight.json')['passed']
    rng=np.random.default_rng(202610090506)
    truth=np.repeat(np.eye(4)[None],6,axis=0)
    for i in range(1,6):
        truth[i]=rigid.retract(truth[i],np.r_[rng.normal(0,.04,3),rng.normal(0,1.,3)])
    world=[]
    for axis in range(3):
        p=rng.uniform(-3,3,(100,3));p[:,axis]=axis-1.;world.append(p)
    groups=[[(p-t[:3,3])@t[:3,:3] for t in truth] for p in world]
    stats=cv.previous.prior.stats_from_groups(groups)
    displaced=translation.move(truth,truth,np.array([.04,-.03,.02]),3)
    hc,gc=translation.system(stats,truth,displaced,3)
    hd,gd=cv.previous.prior.explicit_system(groups,displaced)
    m=translation.mapping(displaced,truth,3)
    dh,dg=float(np.max(abs(hc-m.T@hd@m))),float(np.max(abs(gc-m.T@gd)))
    assert dh<1e-8 and dg<1e-9
    fd=0.
    for axis in range(3):
        delta=np.zeros(3);delta[axis]=1e-6
        plus,minus=translation.move(displaced,truth,delta,3),translation.move(displaced,truth,-delta,3)
        numeric=(translation.cost(stats,plus)-translation.cost(stats,minus))/2e-6
        fd=max(fd,abs(numeric-gc[axis]))
    assert fd<1e-5
    exact,_,_=translation.optimize(stats,truth,3)
    recovered,_,_=translation.optimize(stats,displaced,3)
    noop,recovery=float(np.max(abs(exact-truth))),float(np.max(abs(recovered-truth)))
    assert noop<1e-8 and recovery<2e-5
    invariance=translation.correction(displaced,recovered,3)
    assert invariance['rotation_byte_identical'] and invariance['internal_translation_m']<1e-9
    planar=cv.previous.prior.stats_from_groups([groups[2]])
    body=truth[-1,:3,:3].T@np.array([.2,-.1,0.])
    blind=translation.move(truth,truth,body,3)
    blind_cost=translation.cost(planar,blind)
    blind_rank=int(np.linalg.matrix_rank(translation.system(planar,truth,blind,3)[0],tol=1e-7))
    assert blind_cost<1e-10 and blind_rank==1
    gauge=rigid.retract(np.eye(4),np.array([.1,-.03,.02,5.,-3.,2.]))
    gauge_delta=abs(translation.cost(stats,gauge@displaced)-translation.cost(stats,displaced))
    assert gauge_delta<1e-9
    save(BASE/'preflight.json',dict(passed=True,translation_explicit_hessian_delta=dh,translation_explicit_gradient_delta=dg,
         translation_fd=fd,perfect_noop_delta=noop,translation_recovery_delta=recovery,invariance=invariance,
         planar_translation_blind_cost=blind_cost,planar_translation_blind_rank=blind_rank,common_gauge_delta=gauge_delta,
         frozen_F_preflight_sha256=sha(cv.BASE/'attempt-02/preflight.json'),new_raw_coordinates_parsed=False,new_numeric_gt_parsed=False))
    print('CV2 preflight passed',dh,dg,fd,recovery,flush=True)


def split(keys,seq,i,j):
    text=[f'CV1|{seq}|{i}|{j}|2|'+','.join(str(int(x)) for x in key) for key in keys]
    numbers=np.array([int.from_bytes(hashlib.sha256(s.encode()).digest()[:4],'big') for s in text],np.uint32)
    return numbers%4==0,numbers


def bank():
    frozen=verify()
    assert read(BASE/'preflight.json')['passed']
    root=BASE/'bank';root.mkdir();summary={}
    for seq,binding in frozen['bindings'].items():
        permutation=[7]+list(range(7))+list(range(8,16))
        rows=[binding['raw'][i] for i in permutation]
        frames=np.array([r['frame'] for r in rows],np.int64);nodes=np.array([r['node'] for r in rows],np.int64)
        points=[old.process(seq,int(frame)) for frame in frames]
        native=old.poses(old.source(seq)/'odom_poses.txt')[nodes]
        proper=np.array([old.alg.proper(t) for t in native])
        native_z=np.array(binding['selected']['T_rel']);z=old.alg.proper(native_z)
        o=rigid.inverse(proper[0])@proper;o[0]=np.eye(4)
        initial=o.copy();initial[8:]=z@(rigid.inverse(proper[-1])@proper[8:]);initial[-1]=z
        full,info=plane.features(points,initial,2.)
        cross=(full['counts'][:,:8].sum(1)>0)&(full['counts'][:,8:].sum(1)>0)
        stats=cv.subset(full,cross);remap=np.full(len(cross),-1,np.int64);remap[cross]=np.arange(cross.sum())
        labels=[]
        for label in full['labels']:
            output=np.full(len(label),-1,np.int64);good=label>=0;output[good]=remap[label[good]];labels.append(output)
        held,numbers=split(stats['keys'],seq,binding['selected']['i'],binding['selected']['j'])
        train,test=cv.subset(stats,~held),cv.subset(stats,held)
        ti,hi=cv.describe(train,initial),cv.describe(test,initial)
        supported=bool(ti['patches']>=10 and min(ti['per_visit_contributing_scans'])>=3 and min(ti['per_visit_points'])>=100 and hi['patches']>=5)
        arrays={name:stats[name] for name in FIELDS}
        arrays.update({f'points_{i}':p for i,p in enumerate(points)});arrays.update({f'label_{i}':label for i,label in enumerate(labels)})
        arrays.update(O=o,B=initial,native_absolute=native,proper_absolute=proper,native_Z=native_z,Z=z,
                      frames=frames,nodes=nodes,holdout=held,hash_integers=numbers)
        row=dict(sequence=seq,endpoints=[binding['selected']['i'],binding['selected']['j']],supported=supported,
                 measurement_id=binding['selected']['measurement_id'],full_eligible=info,cross_visit_patches=int(cross.sum()),
                 train=ti,holdout=hi,retained_point_counts=list(map(len,points)),projection_max_delta=float(np.max(abs(native-proper))),
                 z_projection_max_delta=float(np.max(abs(native_z-z))),traces={},corrections={},geometry={})
        if supported:
            arrays['F'],row['traces']['F'],row['corrections']['F']=rigid.optimize(train,initial,'F')
            arrays['T'],row['traces']['T'],row['corrections']['T']=translation.optimize(train,initial)
            fc=row['corrections']['F'];fc['fixed_shape_valid']=bool(fc['internal_translation_m']<=1e-9 and fc['internal_rotation_deg']<=1e-8)
            fc['valid']=bool(fc['valid'] and fc['fixed_shape_valid'])
            for arm in ('O','B','F','T'):
                row['geometry'][arm]=dict(train=cv.geometry(train,arrays[arm]),holdout=cv.geometry(test,arrays[arm]))
        np.savez(root/f'{seq}.npz',**arrays);summary[seq]=row
        print('CV2 bank',seq,row['endpoints'],supported,ti['patches'],hi['patches'],row['corrections'],flush=True)
    save(root/'summary.json',summary)
    save(BASE/'bank_seal.json',dict(utc=utc(),freeze_sha256=sha(BASE/'freeze.json'),new_numeric_gt_parsed=False,
         files={p.name:sha(p) for p in root.iterdir()}))
    verify()


def gate(rows,summary):
    all_valid=len(rows)==3 and all('T' in row['arms'] and summary[seq]['corrections']['T']['valid'] and
                                    row['changes']['TvsB']['denominators_positive'] for seq,row in rows.items())
    result=dict(all_three_supported_valid=bool(all_valid))
    if not all_valid:
        result['eligible']=False;return result
    changes=[row['changes']['TvsB'] for row in rows.values()]
    result.update(joint_ate_improved_cases=sum(m['joint_ate_gain']>0 for m in changes),
                  endpoint_t_improved_cases=sum(m['endpoint_translation_gain']>0 for m in changes),
                  paired_improved_cases=sum(m['joint_ate_gain']>0 and m['endpoint_translation_gain']>0 for m in changes),
                  mean_fractional_joint_ate_gain=float(np.mean([m['joint_ate_gain'] for m in changes])),
                  mean_fractional_endpoint_t_gain=float(np.mean([m['endpoint_translation_gain'] for m in changes])),
                  joint_ate_safety=all(m['joint_ate_gain']>=-.05 for m in changes),endpoint_t_safety=all(m['endpoint_translation_gain']>=-.05 for m in changes),
                  rotation_invariance=all(summary[s]['corrections']['T']['rotation_byte_identical'] and summary[s]['corrections']['T']['max_scan_rotation_change_deg']<=1e-8 and
                                          abs(rows[s]['changes']['TvsB']['endpoint_rotation_regression_deg'])<=1e-8 for s in rows),
                  visit_safety=all(m['visit_safety'] for m in changes),holdout_safety=all(m['holdout_rms_ratio']<=1.01 for m in changes))
    result['eligible']=bool(result['paired_improved_cases']>=2 and result['mean_fractional_joint_ate_gain']>=.05 and result['mean_fractional_endpoint_t_gain']>=.05 and
                            result['joint_ate_safety'] and result['endpoint_t_safety'] and result['rotation_invariance'] and result['visit_safety'] and result['holdout_safety'])
    return result


def evaluate():
    verify();assert read(BASE/'bank_validation.json')['passed']
    summary=read(BASE/'bank/summary.json');rows={}
    for name,digest in read(BASE/'bank_seal.json')['files'].items():
        assert sha(BASE/'bank'/name)==digest
    for seq,data in summary.items():
        row=dict(arms={},changes={},supported=data['supported'])
        if data['supported']:
            z=np.load(BASE/f'bank/{seq}.npz',allow_pickle=False);truth=old.gt(seq)[z['frames']]
            row['arms']={arm:cv.metrics(truth,z[arm]) for arm in ('O','B','F','T')}
            for candidate,baseline in (('F','B'),('T','B'),('T','F')):
                ratio=data['geometry'][candidate]['holdout']['rms_m']/data['geometry'][baseline]['holdout']['rms_m']
                valid=data['corrections'][candidate]['valid'] and (baseline=='B' or data['corrections'][baseline]['valid'])
                change=cv.comparison(row['arms'][candidate],row['arms'][baseline],ratio,valid)
                change.pop('eligible');row['changes'][candidate+'vs'+baseline]=change
            print('CV2 outcomes',seq,{a:[m['joint_aligned_ate_m'],m['endpoint_translation_m'],m['endpoint_rotation_deg']] for a,m in row['arms'].items()},flush=True)
        rows[seq]=row
    save(BASE/'results.json',dict(utc=utc(),rows=rows,primary_gate=gate(rows,summary),bank_seal_sha256=sha(BASE/'bank_seal.json'),
         full_trajectory=False,independent_generalization=False,select_best_arm_after_gt=False))
    print('CV2 primary gate',gate(rows,summary),flush=True)


def record_stage(name,callback):
    start,failure=time.perf_counter(),None
    try:
        callback()
    except Exception as error:
        failure=repr(error);target=BASE/f'FAILURE_{name}.json'
        if not target.exists():save(target,dict(error=failure,traceback=traceback.format_exc()))
        raise
    finally:
        rows=read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        rows.append(dict(stage=name,utc=utc(),wall_s=time.perf_counter()-start,peak_rss_bytes=rss,passed=failure is None))
        (BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows,indent=2)+'\n')
        assert sum(r['wall_s'] for r in rows)<=1800 and rss<=2*2**30
        assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=512*2**20


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('freeze','preflight','bank','evaluate'))
    stage=parser.parse_args().stage;record_stage(stage,globals()[stage])
