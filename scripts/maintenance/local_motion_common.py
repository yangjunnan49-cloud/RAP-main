"""Isolated causal local-motion study utilities; no production loader calls."""
import collections
import hashlib
import importlib
import json
import random
import sys
import typing
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / 'RAP-SLAM'
DATA = MAIN.parent / 'Datasets/data_odometry_velodyne/dataset'
DATE = MAIN / 'docs/maintenance/2026-10-05'
PREFLIGHT = DATE / 'local-motion-feasibility-01'
SCREEN = DATE / 'local-motion-screen-01'
F2 = MAIN / 'docs/maintenance/2026-09-27/f2-structured-dev-01'
C1 = MAIN / 'docs/maintenance/2026-09-28/c1-descriptor-information-01'
SEQS = dict(zip(('00','05','06','07','09','10'),(4541,2761,1101,1101,1591,1201)))
sys.path[:0] = [str(MAIN),str(SLAM),str(MAIN/'dataset_process')]

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    d=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): d.update(b)
    return d.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def status(base,stage,**kw):
    (base/'STATUS.json').write_text(json.dumps(dict(stage=stage,utc=now(),**kw),indent=2)+'\n')
def source(s):
    date,folder=('2026-09-26','e0-frontend-01') if s in ('00','05','06') else ('2026-09-27','e0-heldout-01')
    return MAIN/f'docs/maintenance/{date}/{folder}/full-{s}-A'
def raw(s,i): return DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def seed(s,t): return int.from_bytes(hashlib.sha256(f'LMF1|{s}|{t}'.encode()).digest()[:4],'big')
def census():
    rows=[]; exclusions=[]
    for s,n in SEQS.items():
        m=read(source(s)/'source_frames.json'); ts=np.loadtxt(DATA/'sequences'/s/'times.txt')
        assert m['source_frame_ids']==list(range(n)) and len(ts)==n and np.all(np.diff(ts)>0)
        assert np.array_equal(ts,np.array(m['timestamps']))
        for t in range(0,n,200):
            if t<2:
                exclusions.append(dict(seq=s,t=t,reason='two past scans unavailable')); continue
            ids=[t-1,t,t-2]
            paths=[raw(s,i) for i in ids]
            assert all(p.is_file() for p in paths)
            assert all(m['scan_files'][i]==str(p) for i,p in zip(ids,paths))
            rows.append(dict(seq=s,t=t,ids=ids,paths=[str(p) for p in paths],
                             times=[float(ts[i]) for i in ids],seed=seed(s,t)))
    return dict(rows=rows,exclusions=exclusions,rule='t in range(0,N,200); exclude t<2; input order [t-1,t,t-2]')

def safe_weights(path):
    """Reuse C2's explicit reviewed allowlist; never disable weights_only."""
    import torch
    from omegaconf.base import ContainerMetadata, Metadata
    from omegaconf.listconfig import ListConfig
    from omegaconf.nodes import AnyNode
    reconstruct=importlib.import_module('numpy._core.multiarray')._reconstruct
    allowed=[(reconstruct,'numpy._core.multiarray._reconstruct'),np.ndarray,np.dtype,
             np.dtypes.UInt32DType,ListConfig,ContainerMetadata,AnyNode,Metadata,
             int,typing.Any,dict,list,collections.defaultdict]
    observed=sorted(torch.serialization.get_unsafe_globals_in_checkpoint(path))
    expected=sorted(['builtins.dict','builtins.list','builtins.int','collections.defaultdict',
                     'omegaconf.listconfig.ListConfig','numpy.dtype','omegaconf.nodes.AnyNode',
                     'numpy._core.multiarray._reconstruct','omegaconf.base.ContainerMetadata',
                     'typing.Any','numpy.ndarray','omegaconf.base.Metadata'])
    assert observed==expected,observed
    with torch.serialization.safe_globals(allowed):
        obj=torch.load(path,map_location='cpu',weights_only=True)
    assert isinstance(obj,dict) and isinstance(obj['state_dict'],dict)
    return obj['state_dict'],observed

def make_backend():
    import hydra
    import torch
    from rap_slam.rap_backend import RAPBackend
    from dataset_process.extract_sample_features import FeatureExtractor
    b=RAPBackend.__new__(RAPBackend)
    b.device=torch.device('cuda'); b.seed=42; b.voxel_size=.4
    b.remove_outliers=True; b.max_points_per_scan=1000; b.feature_extractor=None
    with hydra.initialize_config_dir(config_dir=str(MAIN/'config'),version_base='1.3'):
        cfg=hydra.compose(config_name='RAP_inference',overrides=['model=rap_12',
              'model.inference_sampling_steps=5','model.rigidity_forcing=true',
              'model.n_generations=1','model.save_results=false'])
    assert cfg.model.flow_model_ckpt is None and cfg.model.encoder_ckpt is None
    b.model=hydra.utils.instantiate(cfg.model)
    weights,globals_=safe_weights(MAIN/'weights/rap_model_12.ckpt')
    expected=b.model.state_dict()
    assert set(weights)==set(expected)
    assert all(weights[k].shape==v.shape and weights[k].dtype==v.dtype and
               bool(torch.isfinite(weights[k]).all()) for k,v in expected.items())
    b.model.load_state_dict(weights,strict=True)
    b.model.to(b.device).eval()
    b.feature_extractor=FeatureExtractor(model_config=dict(num_points_per_patch=512,
        is_aligned_to_global_z=True,des_r=5.),des_r=5.,is_aligned_to_global_z=True,
        checkpoint_path=None,device='cuda')
    desc_all=torch.load(MAIN/'weights/mini_spinnet_t.pth',map_location='cpu',weights_only=True)
    desc={k[5:]:v for k,v in desc_all.items() if k.startswith('Desc.')}
    de=b.feature_extractor.model.state_dict()
    assert set(desc)==set(de)
    assert all(desc[k].shape==v.shape and desc[k].dtype==v.dtype and
               bool(torch.isfinite(desc[k]).all()) for k,v in de.items())
    b.feature_extractor.model.load_state_dict(desc,strict=True)
    return b,dict(rap_keys=len(weights),descriptor_keys=len(desc),strict=True,
                  weights_only=True,unsafe_globals=globals_,rap_sha256=sha(MAIN/'weights/rap_model_12.ckpt'),
                  descriptor_sha256=sha(MAIN/'weights/mini_spinnet_t.pth'))

@contextmanager
def rng(seed_value):
    import torch
    py=random.getstate(); npstate=np.random.get_state()
    with torch.random.fork_rng(devices=[0]):
        random.seed(seed_value); np.random.seed(seed_value); torch.manual_seed(seed_value)
        torch.cuda.manual_seed_all(seed_value)
        try: yield
        finally: random.setstate(py); np.random.set_state(npstate)

def batch(b,points,features):
    from rap_slam.structured_motion import build_batch
    return build_batch(b,points,features)
def generate(b,bb,noise):
    import torch
    from rap_slam.rap_precision import ieee_matmul
    with ieee_matmul(),torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
        r=b.model.sample_rectified_flow(bb,None,x_1=noise,return_tarjectory=True)
    torch.cuda.synchronize()
    return {k:v.detach().float().cpu().numpy() for k,v in r.items()}
def rigid(x,y):
    x=np.asarray(x,dtype=np.float64); y=np.asarray(y,dtype=np.float64)
    u,_,vt=np.linalg.svd((x-x.mean(0)).T@(y-y.mean(0)))
    r=vt.T@np.diag([1,1,np.linalg.det(vt.T@u.T)])@u.T
    T=np.eye(4); T[:3,:3]=r; T[:3,3]=y.mean(0)-r@x.mean(0); return T
def decode(cond,end,centers,counts,scale):
    cuts=np.r_[0,np.cumsum(counts)]; parts=[]
    for k,(a,z) in enumerate(zip(cuts[:-1],cuts[1:])):
        T=rigid(cond[a:z],end[a:z]); T[:3,3]=scale*T[:3,3]-T[:3,:3]@centers[k]; parts.append(T)
    return np.array(parts)
def transform(x,T): return x@T[:3,:3].T+T[:3,3]
def icp(target,source,initial=None):
    """Fixed point-to-point 3m NN gate, 30 iterations, no learned/GT pose."""
    T=np.eye(4) if initial is None else initial.copy(); tree=cKDTree(target); records=[]
    for k in range(30):
        q=transform(source,T); d,ids=tree.query(q); keep=d<=3.
        if keep.sum()<20: raise ValueError('ICP correspondence shortage')
        step=rigid(q[keep],target[ids[keep]]); T=step@T
        records.append([int(keep.sum()),float(d[keep].mean())])
        if np.max(np.abs(step-np.eye(4)))<1e-7: break
    return T,records
def geometric(points):
    pair,trace2=icp(points[0],points[1]); support,traces=icp(points[0],points[2])
    localmap=np.concatenate([points[0],transform(points[2],support)])
    multi,trace3=icp(localmap,points[1],pair)
    return dict(G2=pair,G3=multi,support=support),dict(G2=trace2,G3=trace3,support=traces)
def get_points(b,row):
    from rap_slam.real_dataset import load_scans
    points=[]; features=[]
    for i,path in zip(row['ids'],row['paths']):
        x,_=load_scans(str(Path(path).parent),start=i,end=i,min_range=1.5,kitti205=True)
        with rng(row['seed']): p,f=b.preprocess(x[0],max_points=1000)
        assert len(p)==1000 and f.shape==(1000,32) and np.isfinite(f).all() and np.any(f)
        points.append(p);features.append(f)
    return points,features
def inference_row(b,row):
    import torch
    points,features=get_points(b,row); outputs={}; poses={}; arrays={}
    with rng(row['seed']): noise=torch.randn((3000,3),device=b.device)
    for name,num in [('R3',3),('R2',2)]:
        bb,scale,centers,counts=batch(b,points[:num],features[:num])
        raw=generate(b,bb,noise[:num*1000]); cond=bb['pointclouds'].cpu().numpy()
        parts=decode(cond,raw['end_point_trajectory'][-1],centers,counts,scale)
        poses[name]=np.linalg.inv(parts[0])@parts[1]
        for k,v in dict(cond=cond,scale=scale,centers=centers,counts=counts,parts=parts,**raw).items(): arrays[name+'_'+k]=v
    geo,trace=geometric(points); poses.update(geo)
    arrays.update(points=np.concatenate(points),features=np.concatenate(features),noise=noise.cpu().numpy())
    for k,v in poses.items(): arrays[k+'_pose']=v
    return arrays,trace

def frozen_sources():
    paths=[MAIN/'scripts/maintenance/local_motion_common.py',SLAM/'rap_slam/rap_backend.py',
           SLAM/'rap_slam/rap_precision.py',SLAM/'rap_slam/structured_motion.py',SLAM/'rap_slam/real_dataset.py',
           MAIN/'scripts/maintenance/c2_feature_channel.py',MAIN/'weights/rap_model_12.ckpt',MAIN/'weights/mini_spinnet_t.pth']
    paths+=list((MAIN/'rectified_point_flow').rglob('*.py'))+list((MAIN/'dataset_process').rglob('*.py'))+list((MAIN/'config').rglob('*.yaml'))
    for s in SEQS:
        paths += [source(s)/'source_frames.json',DATA/'sequences'/s/'times.txt']
    return paths
def check_freeze(base):
    f=read(base/'freeze.json')
    for p,d in f['files'].items(): assert sha(p)==d,p
    return f
def seal(base):
    paths=sorted((base/'bank').glob('*.npz'))
    save(base/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(base/'freeze.json'),
        files={str(p.relative_to(base)):sha(p) for p in paths},results_sha256=sha(base/'bank.json')))
def check_seal(base):
    s=read(base/'bank_seal.json'); assert sha(base/'freeze.json')==s['freeze_sha256'] and sha(base/'bank.json')==s['results_sha256']
    assert s['files']=={str(p.relative_to(base)):sha(p) for p in sorted((base/'bank').glob('*.npz'))}
    return s
