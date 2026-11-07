"""Bounded cross-dataset precision check on three saved KITTI-06 pairs."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import torch

ROOT = Path('/mnt/e/githouse/RAP-SLAM')
sys.path.insert(0,str(ROOT))
from rap_slam.rap_backend import RAPBackend

def main():
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
    product=ROOT/'output_prods/kitti06'
    source=product/'accepted_loops.json'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    cfg=json.loads((product/'summary.json').read_text())['config']
    edges=json.loads(source.read_text())[:3]
    scans={}; inputs=[]
    for frame in sorted({e[k] for e in edges for k in ['i','j']}):
        path=Path(cfg['real_root'])/f"dataset/sequences/06/velodyne/{frame:06d}.bin"
        raw=np.fromfile(path,dtype=np.float32).reshape(-1,4)[:,:3]
        scans[frame]=raw[np.linalg.norm(raw,axis=1)>=1.5]
        inputs.append(dict(source_frame_id=frame,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    model=RAPBackend()
    weights=[]
    for path in [model.ckpt_path,model.spinnet_ckpt]:
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        weights.append(dict(path=path,sha256=h.hexdigest()))
    rows=[]
    for e in edges:
        for arm in ['fresh_tf32_legacy','ieee_repaired']:
            torch.manual_seed(42); np.random.seed(42)
            torch.set_float32_matmul_precision('high')
            function=model.register if arm=='ieee_repaired' else lambda a,b:RAPBackend.register.__wrapped__(model,a,b)
            t,d=function(scans[e['i']],scans[e['j']])
            r=t[:3,:3]
            ortho=float(np.max(abs(r.T@r-np.eye(3))))
            det=float(abs(np.linalg.det(r)-1))
            assert torch.get_float32_matmul_precision()=='high'
            if arm=='ieee_repaired':assert max(ortho,det)<1e-5
            rows.append(dict(arm=arm,source_frame_ids=[e['i'],e['j']],orthogonality=ortho,det_error=det,T_rel=t.tolist(),diagnostics=d))
            print(arm,e['i'],e['j'],ortho,flush=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    report=dict(status='passed',parent_run_id='legacy-kitti06_off',seed_per_pair=42,
                preprocessing='raw KITTI XYZ, minimum range 1.5 m; backend defaults; no 0.205-degree correction',
                scope='Numerical comparison on saved accepted pair identities; not a candidate recall or full SLAM rerun',
                inputs=inputs,weights=weights,rows=rows,source_edges_sha256=before)
    (out/'results.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__': main()
