"""Independent D1 raw-to-input, direct descriptor and fixed-noise replay.

Never imports the D1 runner, uses backend preprocess, opens GT, or runs flow.
"""
from __future__ import annotations
import contextlib,hashlib,json,random,resource,time
from pathlib import Path
import numpy as np
import local_motion_common as c

BASE=c.MAIN/'docs/maintenance/2026-10-06/shared-identity-engineering-01'
CAPS=[2000,1000,1000,2000,1000,1000]


def save(p,data):
    assert not p.exists(),str(p)
    p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def verify():
    frozen=c.read(BASE/'freeze.json');seal=c.read(BASE/'bank_seal.json')
    assert seal['freeze_sha256']==c.sha(BASE/'freeze.json')
    assert seal['bank_sha256']==c.sha(BASE/'bank.json')
    for name,h in frozen['files'].items(): assert c.sha(name)==h,name
    for name,h in seal['files'].items(): assert c.sha(BASE/name)==h,name
    return frozen,seal


@contextlib.contextmanager
def seeded(s):
    import torch
    py,npstate=random.getstate(),np.random.get_state()
    with torch.random.fork_rng(devices=[0]):
        random.seed(s);np.random.seed(s);torch.manual_seed(s);torch.cuda.manual_seed_all(s)
        try: yield
        finally: random.setstate(py);np.random.set_state(npstate)


def point_reconstruction(path,n):
    import open3d as o3d
    xyz=np.fromfile(path,dtype=np.float32).reshape(-1,4)[:,:3]
    xyz=xyz[np.linalg.norm(xyz,axis=1)>=1.5]
    x,y,z=xyz.T;rho=np.hypot(x,y);safe=rho>1e-6;a=np.deg2rad(.205)
    corrected=xyz.copy()
    corrected[:,0]=np.where(safe,x*np.cos(a)-(x*z/np.maximum(rho,1e-6))*np.sin(a),x)
    corrected[:,1]=np.where(safe,y*np.cos(a)-(y*z/np.maximum(rho,1e-6))*np.sin(a),y)
    corrected[:,2]=np.where(safe,z*np.cos(a)+rho*np.sin(a),z)
    cloud=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(corrected.astype(np.float64))).voxel_down_sample(.4)
    cloud,_=cloud.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.5)
    p=np.asarray(cloud.points,dtype=np.float32)
    if len(p)>n: p=p[np.random.default_rng(42).choice(len(p),n,replace=False)]
    assert len(p)==n
    return p


def validate():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    from rap_slam.rap_precision import ieee_matmul
    f,seal=verify();assert torch.cuda.is_available()
    started=time.monotonic();rows=[]
    with seeded(42):
        model=FeatureExtractor(model_config=dict(num_points_per_patch=512,is_aligned_to_global_z=True,des_r=5.),
            des_r=5.,is_aligned_to_global_z=True,checkpoint_path=None,device='cuda').model
    weights=torch.load(c.MAIN/'weights/mini_spinnet_t.pth',map_location='cpu',weights_only=True)
    desc={k[5:]:v for k,v in weights.items() if k.startswith('Desc.')}
    assert len(desc)==58 and set(desc)==set(model.state_dict())
    assert all(desc[k].shape==v.shape and desc[k].dtype==v.dtype and torch.isfinite(desc[k]).all() for k,v in model.state_dict().items())
    model.load_state_dict(desc,strict=True);model.eval();torch.cuda.reset_peak_memory_stats()
    for row in f['pairs']:
        with np.load(BASE/'bank'/f"{row['pair']}_input.npz",allow_pickle=False) as z:
            points=z['points'];features=z['features'];noiseL=z['noise_L'];noiseR=z['noise_R'];noiseU=z['noise_U']
        pp=[point_reconstruction(e['path'],n) for e,n in zip(row['scans'],CAPS)]
        assert np.array_equal(np.concatenate(pp),points)
        feature_list=[]
        # ONE original pair RNG stream: direct model calls consume patch shuffle.
        with seeded(row['parent_seed']),ieee_matmul(),torch.inference_mode():
            for p in pp:
                tensor=torch.tensor(p,device='cuda').unsqueeze(0)
                direct=model(pts=tensor,kpts=tensor.clone(),des_r=5.,is_aligned_to_global_z=True)['desc'].squeeze(0).cpu().numpy()
                assert direct.shape==(len(p),32) and np.isfinite(direct).all() and np.any(direct)
                feature_list.append(direct)
        assert np.array_equal(np.concatenate(feature_list),features)
        for w,expected in [('L',noiseL),('R',noiseR)]:
            with seeded(row['noise_seeds'][w]): actual=torch.randn((6000,3),device='cuda').cpu().numpy()
            assert np.array_equal(actual,expected)
        assert np.array_equal(noiseU,np.concatenate([noiseL,noiseR[4000:]]))
        rows.append(dict(pair=row['pair'],scan_count=6,points=8000,feature_values=256000,
            source_point_delta=0.,source_feature_delta=0.,noise_delta=0.))
        assert time.monotonic()-started+c.read(BASE/'bank.json')['wall_s']<=f['limits']['wall_s']
        print('D1 independent source/noise exact',row['pair'],flush=True)
    verify();elapsed=time.monotonic()-started;bank=c.read(BASE/'bank.json')
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    gpu=torch.cuda.max_memory_allocated()
    assert elapsed+bank['wall_s']<=f['limits']['wall_s'] and rss<=f['limits']['rss_bytes'] and gpu<=f['limits']['gpu_bytes']
    output=dict(stage='D1',utc=c.now(),passed=True,rows=rows,raw_scan_instances=24,points=32000,feature_values=1024000,
        descriptor_state_keys=58,weights_only=True,strict=True,wall_s=elapsed,peak_rss_bytes=rss,peak_allocated_bytes=gpu,
        freeze_sha256=c.sha(BASE/'freeze.json'),bank_seal_sha256=c.sha(BASE/'bank_seal.json'),
        dataset_gt_read=False,flow_inference=False,backend_preprocess_used=False)
    save(BASE/'source_binding_validation.json',output)
    save(BASE/'source_binding_seal.json',dict(stage='D1',utc=c.now(),validation_sha256=c.sha(BASE/'source_binding_validation.json'),
        freeze_sha256=c.sha(BASE/'freeze.json'),bank_seal_sha256=c.sha(BASE/'bank_seal.json')))
    print('D1 source validation PASS',round(elapsed,3),flush=True)


if __name__=='__main__': validate()
