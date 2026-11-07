"""CV2 independent explicit raw geometry, rotation invariance and cohort metrics."""
import os
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import numpy as np
from scipy.spatial.transform import Rotation
import rotation_protected_map_pilot as run
import validate_cross_visit_map_pilot as prior
import validate_shared_plane_map_pilot as planes


def raw(seq,frame):
    p=np.fromfile(run.old.rawpath(seq,int(frame)),np.float32).reshape(-1,4)[:,:3].astype(np.float64)
    assert np.isfinite(p).all()
    distance=np.sqrt(np.einsum('ij,ij->i',p,p));p=p[(distance>=1.5)&(distance<=80.)]
    q=p.copy();horizontal=np.hypot(p[:,0],p[:,1]);good=horizontal>1e-6
    c,s=np.cos(.205*np.pi/180),np.sin(.205*np.pi/180)
    q[good,:2]=p[good,:2]*(c-p[good,2:3]/horizontal[good,None]*s)
    q[good,2]=p[good,2]*c+horizontal[good]*s
    key=np.floor(q/.5).astype(np.int64)
    order=np.lexsort((np.arange(len(key)),key[:,2],key[:,1],key[:,0]))
    first=np.r_[True,np.any(key[order][1:]!=key[order][:-1],axis=1)]
    q=q[order[first]]
    return q[np.linspace(0,len(q)-1,6000,dtype=np.int64)] if len(q)>6000 else q


def explicit_cost(points,labels,poses,mask):
    result=planes.direct_planes(points,labels,poses,len(mask))
    values=[max(p[1][0],0.) for p,keep in zip(result,mask) if keep]
    return .5*float(np.mean(values))/run.plane.GEOMETRY_SIGMA**2


def bank():
    frozen=run.verify()
    for name,digest in run.read(run.BASE/'bank_seal.json')['files'].items():
        assert run.sha(run.BASE/'bank'/name)==digest
    summary=run.read(run.BASE/'bank/summary.json')
    raw_delta=moment=geometry=fd_max=pose_delta=cv1_delta=0.
    points_checked=0;valid_T=0;supported_cases=0
    for seq,row in summary.items():
        binding=frozen['bindings'][seq];z=np.load(run.BASE/f'bank/{seq}.npz',allow_pickle=False)
        source_frames=run.read(run.old.source(seq)/'source_frames.json')['source_frame_ids']
        permutation=[7]+list(range(7))+list(range(8,16));bound=[binding['raw'][i] for i in permutation]
        assert z['nodes'].tolist()==[r['node'] for r in bound] and z['frames'].tolist()==[source_frames[r['node']] for r in bound]
        native=np.repeat(np.eye(4)[None],16,axis=0);native[:,:3]=np.loadtxt(run.old.source(seq)/'odom_poses.txt').reshape(-1,3,4)[z['nodes']]
        assert np.array_equal(native,z['native_absolute'])
        projected=np.array([prior.proper(t) for t in native]);saved_z=prior.proper(np.array(binding['selected']['T_rel']))
        assert np.max(abs(projected-z['proper_absolute']))<1e-12 and np.max(abs(saved_z-z['Z']))<1e-12
        o=np.stack([np.linalg.solve(projected[0],t) for t in projected]);b=o.copy()
        b[8:]=np.stack([saved_z@np.linalg.solve(projected[-1],t) for t in projected[8:]])
        pose_delta=max(pose_delta,float(np.max(abs(o-z['O']))),float(np.max(abs(b-z['B']))))
        points=[]
        for i,frame in enumerate(z['frames']):
            expected=raw(seq,frame);actual=z[f'points_{i}'];assert expected.shape==actual.shape
            raw_delta=max(raw_delta,float(np.max(abs(expected-actual))));points.append(actual);points_checked+=len(actual)
        labels=[z[f'label_{i}'] for i in range(16)];stats={name:z[name] for name in run.FIELDS};count=len(stats['counts'])
        direct=planes.direct_planes(points,labels,z['B'],count)
        for k,key in enumerate(z['keys']):
            assert stats['counts'][k,:8].sum()>0 and stats['counts'][k,8:].sum()>0
            assert np.sum(stats['counts'][k]>0)>=3 and stats['counts'][k].sum()>=40
            payload=f"CV1|{seq}|{binding['selected']['i']}|{binding['selected']['j']}|2|"+','.join(str(int(x)) for x in key)
            number=int(hashlib.sha256(payload.encode()).hexdigest()[:8],16)
            assert number==int(z['hash_integers'][k]) and bool(number%4==0)==bool(z['holdout'][k])
            center,values,normal=direct[k]
            assert values[0]/max(values.sum(),1e-15)<.025+1e-12 and values[1]>.005-1e-12 and values[0]<=.015+1e-12
            for i,p in enumerate(points):
                q=p[labels[i]==k];assert len(q)==stats['counts'][k,i]
                if not len(q):continue
                assert len(q)>=6
                moment=max(moment,float(np.max(abs(q.mean(0)-stats['means'][k,i]))),float(np.max(abs(q.T@q/len(q)-stats['seconds'][k,i]))))
                world=q@z['B'][i,:3,:3].T+z['B'][i,:3,3]
                assert np.all(np.floor(world/2.).astype(np.int64)==key)
                assert abs(normal@(world.mean(0)-center))<=.20+1e-12
        masks=dict(train=~z['holdout'],holdout=z['holdout'])
        for part,mask in masks.items():
            coverage=stats['counts'][mask].sum(0).astype(int).tolist()
            assert coverage==row[part]['per_scan_points'] and int(mask.sum())==row[part]['patches']
            normals=np.array([x[2] for x,keep in zip(direct,mask) if keep])
            if len(normals):assert np.max(abs(np.linalg.eigvalsh(normals.T@normals/len(normals))-row[part]['normal_scatter_eigenvalues']))<1e-8
            for visit,ids in enumerate((range(8),range(8,16))):
                assert sum(coverage[i] for i in ids)==row[part]['per_visit_points'][visit]
                assert sum(coverage[i]>0 for i in ids)==row[part]['per_visit_contributing_scans'][visit]
        supported=row['train']['patches']>=10 and min(row['train']['per_visit_contributing_scans'])>=3 and min(row['train']['per_visit_points'])>=100 and row['holdout']['patches']>=5
        assert bool(supported)==row['supported']
        supported_cases+=supported
        for arm in ('O','B','F','T') if supported else ('O','B'):
            pose=z[arm]
            assert np.max(abs(pose[0]-np.eye(4)))<1e-12
            assert np.max(abs(pose[:,:3,:3].transpose(0,2,1)@pose[:,:3,:3]-np.eye(3)))<1e-10
            assert np.min(np.linalg.det(pose[:,:3,:3]))>.9999999999
            if not supported:continue
            direct_pose=planes.direct_planes(points,labels,pose,count)
            for part,mask in masks.items():
                variance=np.maximum([p[1][0] for p,keep in zip(direct_pose,mask) if keep],0.)
                geometry=max(geometry,float(np.max(abs(variance-row['geometry'][arm][part]['per_patch_variance_m2']))),
                             abs(float(np.sqrt(np.mean(variance)))-row['geometry'][arm][part]['rms_m']))
            if arm in ('F','T'):
                trace=row['traces'][arm];assert len(trace)==24 and all(t['after']<=t['before']+1e-12 for t in trace)
                cost=.5*np.mean([max(p[1][0],0.) for p,keep in zip(direct_pose,masks['train']) if keep])/run.plane.GEOMETRY_SIGMA**2
                assert abs(cost-trace[-1]['after'])<1e-8
                correction=prior.shape_correction(z['B'],pose)
                assert correction['internal_translation_m']<=1e-9 and correction['internal_rotation_deg']<=1e-8
                for name,value in correction.items():
                    if name=='valid':continue
                    assert abs(value-row['corrections'][arm][name])<1e-9
                if arm=='F':
                    assert correction['valid']==row['corrections'][arm]['valid'] and row['corrections'][arm]['fixed_shape_valid']
                else:
                    assert np.array_equal(z['B'][:,:3,:3],pose[:,:3,:3]) and row['corrections'][arm]['rotation_byte_identical']
                    angle=float(np.max(Rotation.from_matrix(z['B'][:,:3,:3].transpose(0,2,1)@pose[:,:3,:3]).magnitude())*180/np.pi)
                    assert angle<=1e-8 and abs(angle-row['corrections'][arm]['max_scan_rotation_change_deg'])<1e-10
                    assert bool(correction['endpoint_translation_m']<=5.)==row['corrections'][arm]['valid']
                    valid_T+=row['corrections'][arm]['valid']
        if not supported:
            assert 'F' not in z and 'T' not in z;continue
        train=run.cv.subset(stats,masks['train']);g=run.translation.system(train,z['B'],z['T'])[1]
        for axis in range(3):
            delta=np.zeros(3);delta[axis]=1e-6
            plus,minus=z['T'].copy(),z['T'].copy();shift=z['B'][-1,:3,:3]@delta
            plus[8:,:3,3]+=shift;minus[8:,:3,3]-=shift
            numeric=(explicit_cost(points,labels,plus,masks['train'])-explicit_cost(points,labels,minus,masks['train']))/2e-6
            fd_max=max(fd_max,abs(numeric-g[axis]))
        if seq=='00':
            historical=np.load(run.cv.BASE/'attempt-02/bank/case.npz',allow_pickle=False)
            for name in ('counts','means','seconds','keys','O','B','F','frames','nodes','holdout','hash_integers'):
                if np.issubdtype(z[name].dtype,np.floating):cv1_delta=max(cv1_delta,float(np.max(abs(z[name]-historical[name]))))
                else:assert np.array_equal(z[name],historical[name])
            assert cv1_delta<1e-10
        print('CV2 explicit bank checked',seq,count,flush=True)
    assert raw_delta<1e-10 and moment<1e-10 and geometry<1e-8 and fd_max<1e-4 and pose_delta<1e-10
    run.save(run.BASE/'bank_validation.json',dict(passed=True,supported_cases=int(supported_cases),valid_T_predictions=int(valid_T),
             raw_scans=48,retained_points=points_checked,independent_raw_max_delta=raw_delta,moment_max_delta=moment,
             explicit_geometry_max_delta=geometry,selected_real_translation_gradient_fd=fd_max,
             source_pose_binding_max_delta=pose_delta,old_CV1_00_array_max_delta=cv1_delta,
             rotation_byte_identity_checked=True,new_numeric_gt_parsed=False,full_optimizer_replay=False,independent_rejected_feature_census=False))


def metrics(seq,z,arm):
    camera=np.repeat(np.eye(4)[None],16,axis=0);camera[:,:3]=np.loadtxt(run.old.DATA/f'poses/{seq}.txt').reshape(-1,3,4)[z['frames']]
    tr=np.eye(4);line=next(s for s in (run.old.DATA/f'sequences/{seq}/calib.txt').read_text().splitlines() if s.startswith('Tr:'))
    tr[:3]=np.fromstring(line.split(':')[1],sep=' ').reshape(3,4)
    truth=np.stack([np.linalg.solve(tr,t@tr) for t in camera]);reference=np.stack([np.linalg.solve(truth[0],t) for t in truth])
    pose=z[arm];e=np.linalg.solve(reference[-1],pose[-1])
    return dict(joint_aligned_ate_m=planes.horn_ate(pose[:,:3,3],reference[:,:3,3]),endpoint_translation_m=float(np.linalg.norm(e[:3,3])),
                endpoint_rotation_deg=prior.angle(e),visits={name:prior.local_metrics(truth,pose,ids) for name,ids in (('A',list(range(8))),('B',[15]+list(range(8,15))))})


def evaluate():
    run.verify();result=run.read(run.BASE/'results.json');summary=run.read(run.BASE/'bank/summary.json')
    assert result['bank_seal_sha256']==run.sha(run.BASE/'bank_seal.json')
    maximum=0.;primary=[]
    for seq,row in result['rows'].items():
        if not row['supported']:continue
        z=np.load(run.BASE/f'bank/{seq}.npz',allow_pickle=False);independent={}
        for arm,recorded in row['arms'].items():
            m=metrics(seq,z,arm);independent[arm]=m
            for name in ('joint_aligned_ate_m','endpoint_translation_m','endpoint_rotation_deg'):maximum=max(maximum,abs(m[name]-recorded[name]))
            for visit in ('A','B'):
                for name,value in m['visits'][visit].items():maximum=max(maximum,float(np.max(abs(np.array(value)-recorded['visits'][visit][name]))))
        for candidate,baseline in (('F','B'),('T','B'),('T','F')):
            c,b=independent[candidate],independent[baseline];recorded=row['changes'][candidate+'vs'+baseline]
            ga=1-c['joint_aligned_ate_m']/b['joint_aligned_ate_m'];gt=1-c['endpoint_translation_m']/b['endpoint_translation_m'];gr=c['endpoint_rotation_deg']-b['endpoint_rotation_deg']
            safety=True
            for visit in ('A','B'):
                cm,bm=c['visits'][visit],b['visits'][visit]
                values=dict(ate_gain=1-cm['aligned_position_ate_m']/bm['aligned_position_ate_m'],translation_gain=1-cm['relative_translation_rmse_m']/bm['relative_translation_rmse_m'],
                            rotation_regression_deg=cm['relative_rotation_mean_deg']-bm['relative_rotation_mean_deg'])
                safety &= values['ate_gain']>=-.05 and values['translation_gain']>=-.05 and values['rotation_regression_deg']<=.02
                for name,value in values.items():assert abs(value-recorded['visit_changes'][visit][name])<1e-8
            ratio=summary[seq]['geometry'][candidate]['holdout']['rms_m']/summary[seq]['geometry'][baseline]['holdout']['rms_m']
            for name,value in (('joint_ate_gain',ga),('endpoint_translation_gain',gt),('endpoint_rotation_regression_deg',gr),('holdout_rms_ratio',ratio)):
                assert abs(value-recorded[name])<1e-8
            assert recorded['visit_safety']==bool(safety) and recorded['denominators_positive']
            if candidate=='T' and baseline=='B':primary.append(dict(seq=seq,ga=ga,gt=gt,gr=gr,safety=bool(safety),ratio=ratio))
    assert maximum<1e-8
    all_valid=len(primary)==3 and all(summary[m['seq']]['corrections']['T']['valid'] for m in primary)
    if all_valid:
        checks=dict(all_three_supported_valid=True,joint_ate_improved_cases=sum(m['ga']>0 for m in primary),endpoint_t_improved_cases=sum(m['gt']>0 for m in primary),
                    paired_improved_cases=sum(m['ga']>0 and m['gt']>0 for m in primary),mean_fractional_joint_ate_gain=float(np.mean([m['ga'] for m in primary])),
                    mean_fractional_endpoint_t_gain=float(np.mean([m['gt'] for m in primary])),joint_ate_safety=all(m['ga']>=-.05 for m in primary),
                    endpoint_t_safety=all(m['gt']>=-.05 for m in primary),rotation_invariance=all(summary[m['seq']]['corrections']['T']['rotation_byte_identical'] and
                    summary[m['seq']]['corrections']['T']['max_scan_rotation_change_deg']<=1e-8 and abs(m['gr'])<=1e-8 for m in primary),
                    visit_safety=all(m['safety'] for m in primary),holdout_safety=all(m['ratio']<=1.01 for m in primary))
        checks['eligible']=bool(checks['paired_improved_cases']>=2 and checks['mean_fractional_joint_ate_gain']>=.05 and checks['mean_fractional_endpoint_t_gain']>=.05 and
                                checks['joint_ate_safety'] and checks['endpoint_t_safety'] and checks['rotation_invariance'] and checks['visit_safety'] and checks['holdout_safety'])
    else:checks=dict(all_three_supported_valid=False,eligible=False)
    assert set(checks)==set(result['primary_gate'])
    for name,value in checks.items():
        if isinstance(value,float):assert abs(value-result['primary_gate'][name])<1e-8
        else:assert value==result['primary_gate'][name]
    run.save(run.BASE/'validation.json',dict(passed=True,independent_metric_max_delta=maximum,complete_primary_conjunction_checked=True,
             eligible=checks['eligible'],full_optimizer_replay=False,full_sequence_metric_claim=False))
    (run.BASE/'INCOMPLETE').unlink()
    print('CV2 independent metrics/gates',maximum,checks,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('bank','evaluate'))
    stage=parser.parse_args().stage;run.record_stage('validate_'+stage,globals()[stage])
