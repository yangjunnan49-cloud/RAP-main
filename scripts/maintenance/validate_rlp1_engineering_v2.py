"""Independent RLP1 raw/descriptor/noise/grouping/Horn/RNG validator."""
import numpy as np
import local_motion_common as c
import rlp1_attempt02_common as r
from validate_local_motion_source_binding import reconstruct
from validate_local_motion_feasibility_v2 import normalize,decode


def validate():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    f=r.check(r.ENG);seal=r.check_seal(r.ENG)
    assert len(seal['files'])==16 and len(f['full_manifest'])==204
    assert f['full_manifest']==r.rows() and r.runtime()==f['runtime']
    model=FeatureExtractor(model_config=dict(num_points_per_patch=512,is_aligned_to_global_z=True,des_r=5.),
        des_r=5.,is_aligned_to_global_z=True,checkpoint_path=None,device='cuda').model
    weights=torch.load(c.MAIN/'weights/mini_spinnet_t.pth',map_location='cpu',weights_only=True)
    desc={k[5:]:v for k,v in weights.items() if k.startswith('Desc.')}
    assert len(desc)==58 and set(desc)==set(model.state_dict())
    assert all(torch.isfinite(v).all() for v in desc.values())
    model.load_state_dict(desc,strict=True);model.eval();torch.cuda.reset_peak_memory_stats()
    maximum=0.;records=[]
    bank=c.read(r.ENG/'bank.json')
    for row,record in zip(f['rows'],bank['rows']):
        stem=r.stem(row)
        loaded={}
        for mode in ('J','I','R','P'):
            with np.load(r.ENG/'bank'/f'{stem}_{mode}.npz',allow_pickle=False) as z:
                loaded[mode]={key:z[key] for key in z.files}
        j=loaded['J']; i=loaded['I']
        for part,path in enumerate(row['paths']):
            points=reconstruct(path)
            assert np.array_equal(points,j['points'][part*1000:(part+1)*1000])
            tt=torch.tensor(points,device='cuda').unsqueeze(0)
            with c.rng(row['seed']),torch.no_grad():
                features=model(pts=tt,kpts=tt.clone(),des_r=5.,is_aligned_to_global_z=True)['desc'].squeeze(0).cpu().numpy()
            assert np.array_equal(features,j['features'][part*1000:(part+1)*1000])
        with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda').cpu().numpy()
        assert np.array_equal(noise,j['noise'])
        cond,scale,centers,counts=normalize(np.split(j['points'],3))
        assert np.array_equal(cond,j['cond']) and np.array_equal(counts,j['counts'])
        assert abs(scale-float(j['scale']))<1e-12 and abs(centers-j['centers']).max()<1e-12
        for mode,metadata in zip(('J','I','R','P'),record['modes']):
            z=loaded[mode]; groups=1 if mode=='J' else 3
            assert all(np.isfinite(value).all() for value in z.values())
            assert z['tokens'].dtype==np.float32 and z['tokens'].shape==(3,1000,512)
            for key in ('points','features','noise','cond','scale','centers','counts','scan_ids','seed'):
                assert np.array_equal(z[key],j[key]),key
            assert np.array_equal(z['tokens'],z['hook_tokens'])
            actual=noise.copy()
            if mode=='P': actual[2000:]+=np.float32(1.)
            assert np.array_equal(actual,z['actual_noise']) and np.array_equal(actual,z['flow_inputs'][0])
            assert np.array_equal(z['flow_inputs'][1:],z['trajectory'][:-1])
            expected_times=np.repeat(np.array([[1.],[.8],[.6],[.4],[.2]],np.float32),groups,1)
            assert np.array_equal(z['flow_times'],expected_times)
            expected=dict(cond_coord=cond,local_features=j['features'],anchor_indices=np.arange(3000)<1000,
                scales=np.repeat(np.array([scale],np.float32),groups),
                cu_seqlens_part=np.array([0,1000,2000,3000],np.int32),
                cu_seqlens_batch=np.array([0,3000],np.int32) if groups==1 else np.array([0,1000,2000,3000],np.int32))
            for key,value in expected.items(): assert np.array_equal(z['hook_'+key],value),key
            parts=decode(dict(cond=cond,raw=z['end_point_trajectory'][-1],centers=centers,counts=counts,scale=scale))
            pose=np.linalg.solve(parts[0],parts[1])
            delta=max(float(abs(parts-z['parts']).max()),float(abs(pose-z['pose']).max()))
            maximum=max(maximum,delta);assert delta<1e-8
            with torch.random.fork_rng(devices=[0]):
                torch.set_rng_state(torch.tensor(z['rng_before_cpu'],dtype=torch.uint8))
                torch.cuda.set_rng_state(torch.tensor(z['rng_before_cuda'],dtype=torch.uint8),0)
                torch.rand(groups,device='cuda')
                assert np.array_equal(torch.get_rng_state().numpy(),z['rng_after_cpu'])
                assert np.array_equal(torch.cuda.get_rng_state(0).cpu().numpy(),z['rng_after_cuda'])
            assert metadata['hooked_flow_calls']==5 and metadata['outer_rng_restored']
            assert metadata['parameters_and_modes_unchanged'] and metadata['before']==metadata['after']
        for key in loaded['R']: assert np.array_equal(loaded['R'][key],i[key]),key
        for key in ('trajectory','end_point_trajectory','flow_inputs'):
            assert np.array_equal(loaded['P'][key][:,:2000],i[key][:,:2000])
        assert np.array_equal(loaded['P']['tokens'][:2],i['tokens'][:2])
        with np.load(r.TR/'bank'/f'{stem}_N.npz',allow_pickle=False) as old, \
             np.load(r.TR/'bank'/f'{stem}_E.npz',allow_pickle=False) as old_tokens:
            for key in ('points','features','noise','cond','scale','centers','counts','parts','pose','trajectory','end_point_trajectory'):
                assert np.array_equal(j[key],old[key])
            assert np.array_equal(j['tokens'],old_tokens['tokens'])
        records.append(dict(seq=row['seq'],t=row['t'],groups_and_five_states_exact=True,
            source_descriptors_noise_exact=True,repeat_and_third_noise_independence_exact=True))
        r.cap();print('RLP1 independent engineering validation',row['seq'],flush=True)
    assert len(records)==4 and bank['checkpoint']['rap_keys']==344 and bank['checkpoint']['descriptor_keys']==58
    assert bank['checkpoint']['strict'] and bank['checkpoint']['weights_only']
    r.pass_validation(r.ENG,dict(decision='PASS_INDEPENDENT_CONTEXT_ENGINEERING',rows=records,
        source_scans=12,points=12000,descriptor_values=384000,independent_pose_max_delta=maximum,
        gt_read=False,flow_inference_rerun=False,training=False,**r.usage()))
    r.finish('engineering_validation')
    print('RLP1 engineering VALIDATED',maximum,flush=True)


if __name__=='__main__':
    try: validate()
    except Exception as ex:
        r.fail('engineering_validation',ex)
        raise

