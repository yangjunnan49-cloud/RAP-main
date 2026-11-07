"""Read-only diagnostic of serialized GT rotations in failed FDI validator."""
import numpy as np
import flow_directional_information as h
import flow_directional_response as f
from validate_flow_directional_information_v2 import truth,tangent
if __name__=='__main__':
    gt={s:truth(s) for s in ['00','08']}; old={r['key']:r for r in f.read(h.B/'results-v2.json')['rows']}
    for r in h.selection()[:5]:
        with np.load(h.B/'bank'/f"{r['key']}.npz",allow_pickle=False) as a: T=a['full'][-1]
        G=np.linalg.solve(gt[r['seq']][r['i']],gt[r['seq']][r['j']]); Q=np.linalg.solve(T,G); u,_,v=np.linalg.svd(Q[:3,:3]); P=Q.copy(); P[:3,:3]=u@np.diag([1,1,np.linalg.det(u@v)])@v
        e=tangent(Q)/f.D; ep=tangent(P)/f.D; ref=np.array(old[r['key']]['e_normalized'])
        print(r['key'],'serialized_R_orthogonality',np.max(np.abs(Q[:3,:3].T@Q[:3,:3]-np.eye(3))),'raw_log_delta',np.max(np.abs(e-ref)),'SO3_projected_delta',np.max(np.abs(ep-ref)),flush=True)
