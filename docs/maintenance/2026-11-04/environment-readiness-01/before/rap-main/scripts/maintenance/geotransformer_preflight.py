"""Prospective synthetic-only official GeoTransformer compatibility checks."""
import hashlib, json, sys, tarfile, time, os, resource
from pathlib import Path
import numpy as np
B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/geotransformer-feasibility-01')
S=B/'official-source'; EXP=S/'experiments/geotransformer.kitti.stage5.gse.k3.max.oacl.stage2.sinkhorn'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x') as f: json.dump(x,f,indent=2,allow_nan=False)
def identities():
    files=[B/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_geotransformer_preflight.py'),B/'geotransformer-kitti.pth.tar',B/'source.tar.gz',B/'extension_build_v2.json',B/'recovery_acquisition.json']
    for folder in ['official-source','isolated-python','compat-extensions','dependency-wheels']:
        files += [p for p in (B/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
    files += [B/'extension-build-v2/rap_geotransformer_ext.so']
    return sorted(set(files))
def verify():
    f=json.loads((B/'preflight_freeze.json').read_text())
    assert f['files']=={str(p):sha(p) for p in identities()}
def freeze():
    assert not (B/'preflight_results.json').exists()
    import torch,scipy,open3d
    # Exact official archive and the one portable include change.
    manifest={}
    with tarfile.open(B/'source.tar.gz') as ar:
        for m in ar.getmembers():
            if not m.isfile(): continue
            rel='/'.join(Path(m.name).parts[1:]); body=ar.extractfile(m).read()
            assert (S/rel).read_bytes()==body,rel
            manifest[rel]=hashlib.sha256(body).hexdigest()
    assert set(manifest)=={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}
    for p in (B/'compat-extensions').rglob('*'):
        if not p.is_file(): continue
        orig=S/'geotransformer/extensions'/p.relative_to(B/'compat-extensions')
        expected=orig.read_bytes()
        if str(p.relative_to(B/'compat-extensions'))=='common/torch_helper.h':
            expected=expected.replace(b'#include <ATen/cuda/CUDAContext.h>',b'// Unused CUDAContext include omitted for the CPU-only extension build.')
        assert p.read_bytes()==expected
    checkpoint=B/'geotransformer-kitti.pth.tar'
    assert checkpoint.stat().st_size==102131979
    save(B/'source_manifest.json',manifest)
    save(B/'preflight_freeze.json',dict(files={str(p):sha(p) for p in identities()},torch=torch.__version__,numpy=np.__version__,scipy=scipy.__version__,open3d=open3d.__version__,cuda=torch.version.cuda))
    print('synthetic preflight frozen',len(identities()),flush=True)
def setup():
    import torch
    sys.path[:0]=[str(B/'isolated-python'),str(S),str(EXP),str(B/'extension-build-v2')]
    import rap_geotransformer_ext as ext
    sys.modules['geotransformer.ext']=ext
    from config import make_cfg
    from model import create_model
    from geotransformer.utils.data import registration_collate_fn_stack_mode
    from geotransformer.utils.torch import to_cuda
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    torch.set_float32_matmul_precision('highest'); torch.manual_seed(7351)
    return torch,make_cfg(),create_model,registration_collate_fn_stack_mode,to_cuda
def run():
    verify(); start=time.monotonic()
    (B/'INCOMPLETE').write_text('Synthetic compatibility pending independent validation\n')
    torch,cfg,create,collate,to_cuda=setup()
    model=create(cfg).cuda().eval()
    ckpt=torch.load(B/'geotransformer-kitti.pth.tar',map_location='cpu',weights_only=True)
    assert isinstance(ckpt,dict) and 'model' in ckpt
    loaded=model.load_state_dict(ckpt['model'],strict=True)
    from scipy.spatial.transform import Rotation
    rng=np.random.default_rng(7351); src=rng.uniform(-25,25,(2000,3)).astype('float32')
    T=np.eye(4,dtype='float32'); T[:3,:3]=Rotation.from_euler('xyz',[7,-4,17],degrees=True).as_matrix(); T[:3,3]=[2,-1,.4]
    ref=(src@T[:3,:3].T+T[:3,3]).astype('float32')
    from geotransformer.modules.registration import weighted_procrustes
    fitted=weighted_procrustes(torch.tensor(src,device='cuda'),torch.tensor(ref,device='cuda'),return_transform=True).cpu().numpy()
    assert np.max(np.abs(fitted-T))<=1e-4
    outputs=[]; elapsed=[]
    dummies=[np.eye(4,dtype='float32'),np.eye(4,dtype='float32'),np.eye(4,dtype='float32')]; dummies[1][:3,3]=[400,-300,200]
    torch.cuda.reset_peak_memory_stats()
    for dummy in dummies:
        t=time.monotonic()
        data=collate([dict(ref_points=ref,src_points=src,ref_feats=np.ones((len(ref),1),dtype='float32'),src_feats=np.ones((len(src),1),dtype='float32'),transform=dummy)],5,.3,1.275,[128]*5)
        output=None
        with torch.inference_mode(): output=model(to_cuda(data))
        torch.cuda.synchronize(); elapsed.append(time.monotonic()-t)
        keep=['estimated_transform','ref_corr_points','src_corr_points','corr_scores','ref_node_corr_indices','src_node_corr_indices','matching_scores','gt_node_corr_indices']
        outputs.append({k:output[k].cpu().numpy() for k in keep})
        assert time.monotonic()-start<600 and torch.cuda.max_memory_allocated()/2**30<6
        print('synthetic forward complete',len(outputs),elapsed[-1],flush=True)
    dest=B/'synthetic-bank'; dest.mkdir()
    np.savez(dest/'geometry.npz',src=src,ref=ref,known=T,fitted=fitted,points=data['points'][0].cpu().numpy(),lengths=data['lengths'][0].cpu().numpy(),neighbors=data['neighbors'][0].cpu().numpy(),subpoints=data['points'][1].cpu().numpy(),sublengths=data['lengths'][1].cpu().numpy())
    for i,out in enumerate(outputs): np.savez(dest/f'forward-{i}.npz',**out)
    invariant={}
    for k in outputs[0]:
        if k.startswith('gt_'): continue
        assert all(o[k].shape==outputs[0][k].shape for o in outputs)
        invariant[k]=float(max(np.max(np.abs(o[k]-outputs[0][k])) if o[k].size else 0 for o in outputs[1:]))
        assert invariant[k]<=1e-6,k
    verify()
    save(B/'preflight_results.json',dict(strict_load=True,missing_keys=list(loaded.missing_keys),unexpected_keys=list(loaded.unexpected_keys),model_state_keys=len(ckpt['model']),checkpoint_top_keys=list(ckpt),known_transform_max_error=float(np.max(np.abs(fitted-T))),invariance=invariant,forward_wall_s=elapsed,wall_s=time.monotonic()-start,peak_gpu_gib=torch.cuda.max_memory_allocated()/2**30,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,bank_files={str(p.relative_to(dest)):sha(p) for p in dest.iterdir()}))
    print('synthetic preflight ready for independent validation',flush=True)
if __name__=='__main__': {'freeze':freeze,'run':run}[sys.argv[1]]()
