"""Independent raw-to-input binding and direct descriptor replay, GT-free."""
import resource
import sys
import time
from pathlib import Path
import numpy as np
import local_motion_common as c
B=c.PREFLIGHT/'attempt-02'

def freeze():
    c.check_freeze(B);c.check_seal(B);assert c.read(B/'validation.json')['passed']
    paths=[Path(__file__),B.parent/'SUPPLEMENT_01.md',B/'freeze.json',B/'bank_seal.json',B/'bank.json',B/'validation.json']
    c.save(B/'supplement_freeze.json',dict(utc=c.now(),files={str(p):c.sha(p) for p in paths}))

def verify():
    for p,d in c.read(B/'supplement_freeze.json')['files'].items():assert c.sha(p)==d,p
    c.check_freeze(B);c.check_seal(B)

def reconstruct(path):
    import open3d as o3d
    points=np.fromfile(path,dtype=np.float32).reshape(-1,4)[:,:3]
    points=points[np.linalg.norm(points,axis=1)>=1.5]
    x,y,z=points.T;rho=np.hypot(x,y);safe=rho>1e-6;a=np.deg2rad(.205)
    out=points.copy()
    out[:,0]=np.where(safe,x*np.cos(a)-(x*z/np.maximum(rho,1e-6))*np.sin(a),x)
    out[:,1]=np.where(safe,y*np.cos(a)-(y*z/np.maximum(rho,1e-6))*np.sin(a),y)
    out[:,2]=np.where(safe,z*np.cos(a)+rho*np.sin(a),z)
    cloud=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(out.astype(np.float64))).voxel_down_sample(.4)
    cloud,_=cloud.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.5)
    p=np.asarray(cloud.points,dtype=np.float32)
    if len(p)>1000:p=p[np.random.default_rng(42).choice(len(p),1000,replace=False)]
    assert len(p)==1000;return p

def validate():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    t=time.monotonic();verify()
    model=FeatureExtractor(model_config=dict(num_points_per_patch=512,is_aligned_to_global_z=True,des_r=5.),
        des_r=5.,is_aligned_to_global_z=True,checkpoint_path=None,device='cuda').model
    state=torch.load(c.MAIN/'weights/mini_spinnet_t.pth',map_location='cpu',weights_only=True)
    desc={k[5:]:v for k,v in state.items() if k.startswith('Desc.')}
    assert len(desc)==58 and all(torch.isfinite(v).all() for v in desc.values())
    model.load_state_dict(desc,strict=True);model.eval();torch.cuda.reset_peak_memory_stats()
    rows=[]
    for row in c.read(B/'bank.json')['rows']:
        if row['kind']!='local':continue
        with np.load(B/'bank'/f"local_{row['seq']}.npz",allow_pickle=False) as z:
            for k,path in enumerate(row['paths']):
                p=reconstruct(path);assert np.array_equal(p,z['points'][1000*k:1000*(k+1)])
                tensor=torch.tensor(p,device='cuda').unsqueeze(0)
                with c.rng(row['seed']),torch.no_grad():
                    f=model(pts=tensor,kpts=tensor.clone(),des_r=5.,is_aligned_to_global_z=True)['desc'].squeeze(0).cpu().numpy()
                assert np.isfinite(f).all() and np.any(f) and np.array_equal(f,z['features'][1000*k:1000*(k+1)])
            with c.rng(row['seed']):noise=torch.randn((3000,3),device='cuda').cpu().numpy()
            assert np.array_equal(noise,z['noise'])
        rows.append(dict(seq=row['seq'],scans=3,points=3000,point_feature_noise_max_delta=0.))
        print('source binding exact',row['seq'],flush=True)
    assert len(rows)==6;verify();elapsed=time.monotonic()-t
    bank=c.read(B/'bank.json');primary=c.read(B/'validation.json')
    total=bank['wall_s']+primary['validator_wall_s']+elapsed
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20
    size=sum(p.stat().st_size for p in c.PREFLIGHT.rglob('*') if p.is_file())
    assert total<1200 and max(rss,bank['peak_rss_gib'])<4 and size<100000000 and torch.cuda.max_memory_allocated()/2**30<12
    c.save(B/'source_binding_validation.json',dict(utc=c.now(),passed=True,raw_scans=18,points=18000,feature_values=576000,
        noise_rows=18000,rows=rows,gt_files_read=False,flow_inference_rerun=False,supplement_wall_s=elapsed,
        successful_bank_primary_and_supplement_wall_s=total,peak_rss_gib=max(rss,bank['peak_rss_gib']),artifact_bytes_before_report=size,
        note='Primary total_wall_s was sampled before its final identity recheck; total here uses its full validator_wall_s. No cap/gate changed.'))
if __name__=='__main__':{'freeze':freeze,'validate':validate}[sys.argv[1]]()
