"""RLP2 independent full raw/descriptor/noise/binding/Horn/G3 validator."""
import sys
import numpy as np
import local_motion_common as c
import rlp2_common as r
from validate_local_motion_source_binding import reconstruct
from validate_local_motion_feasibility_v2 import normalize,decode,icp

def validate():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    f=r.check(r.FULL);r.check_seal(r.FULL);assert r.runtime()==f['runtime']
    bank=c.read(r.FULL/'bank.json');assert len(bank['rows'])==204 and not bank['gt_read']
    model=FeatureExtractor(model_config=dict(num_points_per_patch=512,is_aligned_to_global_z=True,des_r=5.),
        des_r=5.,is_aligned_to_global_z=True,checkpoint_path=None,device='cuda').model
    state=torch.load(c.MAIN/'weights/mini_spinnet_t.pth',map_location='cpu',weights_only=True)
    desc={k[5:]:v for k,v in state.items() if k.startswith('Desc.')};assert len(desc)==58
    model.load_state_dict(desc,strict=True);model.eval();torch.cuda.reset_peak_memory_stats()
    maximum=0.;records=[];geometric=0
    od={}
    for s in ('07','09','10'):
        q=np.loadtxt(c.source(s)/'odom_poses.txt').reshape(-1,3,4);od[s]=np.repeat(np.eye(4)[None],len(q),0);od[s][:,:3]=q
    for ix,(row,record) in enumerate(zip(f['rows'],bank['rows'])):
        assert all(row[k]==record[k] for k in row)
        with np.load(r.FULL/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as zz:z={k:zz[k] for k in zz.files}
        for p,path in enumerate(row['paths']):
            points=reconstruct(path);assert np.array_equal(points,z['points'][p*1000:(p+1)*1000])
            tensor=torch.tensor(points,device='cuda').unsqueeze(0)
            with c.rng(row['seed']),torch.no_grad():
                features=model(pts=tensor,kpts=tensor.clone(),des_r=5.,is_aligned_to_global_z=True)['desc'].squeeze(0).cpu().numpy()
            assert np.array_equal(features,z['features'][p*1000:(p+1)*1000])
        with c.rng(row['seed']):noise=torch.randn((3000,3),device='cuda').cpu().numpy()
        assert np.array_equal(noise,z['noise'])
        cond,scale,centers,counts=normalize(np.split(z['points'],3))
        assert np.array_equal(cond,z['cond']) and np.array_equal(counts,z['counts'])
        assert abs(scale-float(z['scale']))<1e-12 and abs(centers-z['centers']).max()<1e-12
        for arm,metadata in zip(('J','I'),record['modes']):
            groups=1 if arm=='J' else 3
            assert z[arm+'_tokens'].dtype==np.float32 and z[arm+'_tokens'].shape==(3,1000,512)
            assert metadata['passive_token_equal'] and metadata['outer_rng_restored']
            assert metadata['hooked_flow_calls']==5 and metadata['parameters_and_modes_unchanged']
            assert metadata['before']==metadata['after']
            assert np.array_equal(z[arm+'_flow_inputs'][0],noise)
            assert np.array_equal(z[arm+'_flow_inputs'][1:],z[arm+'_trajectory'][:-1])
            assert np.array_equal(z[arm+'_flow_times'],np.repeat(np.array([[1.],[.8],[.6],[.4],[.2]],np.float32),groups,1))
            expected=dict(cond_coord=cond,local_features=z['features'],anchor_indices=np.arange(3000)<1000,
                scales=np.repeat(np.array([scale],np.float32),groups),cu_seqlens_part=np.array([0,1000,2000,3000],np.int32),
                cu_seqlens_batch=np.array([0,3000],np.int32) if groups==1 else np.array([0,1000,2000,3000],np.int32))
            for key,value in expected.items():assert np.array_equal(value,z[arm+'_hook_'+key]),key
            parts=decode(dict(cond=cond,raw=z[arm+'_end_point_trajectory'][-1],centers=centers,counts=counts,scale=scale))
            pose=np.linalg.solve(parts[0],parts[1]);d=max(float(abs(parts-z[arm+'_parts']).max()),float(abs(pose-z[arm+'_pose']).max()))
            maximum=max(maximum,d);assert d<1e-8
            with torch.random.fork_rng(devices=[0]):
                torch.set_rng_state(torch.tensor(z[arm+'_rng_before_cpu'],dtype=torch.uint8))
                torch.cuda.set_rng_state(torch.tensor(z[arm+'_rng_before_cuda'],dtype=torch.uint8),0)
                torch.rand(groups,device='cuda')
                assert np.array_equal(torch.get_rng_state().numpy(),z[arm+'_rng_after_cpu'])
                assert np.array_equal(torch.cuda.get_rng_state(0).cpu().numpy(),z[arm+'_rng_after_cuda'])
        if row['role']=='exposed_evaluation':
            points=np.split(z['points'],3);two,tr2=icp(points[0],points[1]);support,trs=icp(points[0],points[2])
            merged=np.concatenate((points[0],points[2]@support[:3,:3].T+support[:3,3]));three,tr3=icp(merged,points[1],two)
            for name,pose,trace in (('G2',two,tr2),('support',support,trs),('G3',three,tr3)):
                d=float(abs(pose-z[name+'_pose']).max());maximum=max(maximum,d);assert d<1e-8
                assert np.asarray(trace).shape==np.asarray(record['icp_trace'][name]).shape
                assert abs(np.asarray(trace)-np.asarray(record['icp_trace'][name])).max()<1e-8
            if row['seq'] in od:
                expected=np.linalg.solve(od[row['seq']][row['t']-1],od[row['seq']][row['t']])
                d=float(abs(expected-z['KISS_pose']).max());maximum=max(maximum,d);assert d<1e-8
            geometric+=1
        records.append(dict(seq=row['seq'],t=row['t'],source_exact=True))
        r.cap()
        if ix%12==0 or ix==203:print('RLP2 independent source bank',ix+1,'/204',flush=True)
    r.pass_validation(r.FULL,dict(decision='PASS_COMPLETE_GT_FREE_FEATURE_BANK',windows=204,source_scans=612,
        processed_points=612000,descriptor_values=19584000,maximum_pose_delta=maximum,G3_windows=geometric,
        input_feature_noise_exact=True,GT_read=False,RAP_flow_rerun=False,rows=records,**r.usage()))
    r.finish('full_bank_validation');print('RLP2 full bank independently VALIDATED',maximum,flush=True)

if __name__=='__main__':
    try:validate()
    except Exception as ex:r.fail('full_bank_validation',ex);raise
