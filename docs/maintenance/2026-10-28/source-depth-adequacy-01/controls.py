import codecs
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib
import geometry

OUT = lib.ROOT/'controls'
try:
    lib.verify_freeze('controls')
    _, np = lib.runtime()
    import numpy.ma
    for codec in ('ascii','cp437','utf-8','latin-1'):
        codecs.lookup(codec)
    k = np.array([[100.,0.,5.],[0.,100.,5.],[0.,0.,1.]])
    tr = np.eye(4)
    xyz = np.array([[0.,0.,2.],[0.,0.,4.],[.04,0.,2.],[0.,0.,-1.],[1.,1.,1.],[np.nan,0.,1.]])
    uv, camera, index, grid = geometry.project(np,xyz,tr,k,11,11)
    checks = []
    checks.append(set(index)=={0,2})
    queries = np.array([[5.,5.],[5.,5.],[3.,5.],[2.999,5.],[7.,5.]])
    a,d,u = geometry.associate(np,queries,uv,camera,index,grid)
    checks.extend([int(index[a[0]])==0, a[0]==a[1],len(u)==2,a[2]>=0,a[3]==-1,int(index[a[4]])==2])
    checks.append(all(int(v)==geometry.dense(np,q,uv,camera,index) for q,v in zip(queries,a)))
    moved = np.eye(4);moved[0,3]=.02
    image2,_,_,_=geometry.project(np,np.array([[0.,0.,2.]]),moved,k,11,11)
    checks.append(np.allclose(image2,[[6.,5.]],atol=1e-14,rtol=0))
    cache = OUT/'cold.npz'
    with cache.open('xb') as f:
        np.savez(f,queries=queries)
    lib.read_gate([cache],OUT)
    with np.load(cache,allow_pickle=False) as z:
        again,_,_=geometry.associate(np,z['queries'],uv,camera,index,grid)
        checks.append(np.array_equal(again,a))
    denied=False
    try:
        (lib.ROOT/'INPUT_BINDING.json').read_bytes()
    except PermissionError:
        denied=True
    checks.append(denied)
    assert all(checks)
    lib.complete(OUT,{'control_count':len(checks),'controls':checks,'measured_point_or_reference_reads':0,'pose_solver_calls':0})
    print('SD1 synthetic controls PASS')
except BaseException as e:
    lib.failure(OUT,e)
    raise
