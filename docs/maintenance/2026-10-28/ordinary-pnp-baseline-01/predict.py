"""All200 PnP outputs, no reference/label reads."""
import codecs
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import pnp_lib

OUT=lib.ROOT/'predict'
try:
    frozen=lib.verify_freeze('prediction');lib.verify_seal(lib.ROOT/'controls')
    binding=lib.load(lib.ROOT/'PREDICTION_INPUTS.json');method=lib.load(lib.ROOT/'METHOD.json')
    cv2,np=lib.runtime()
    import numpy.ma
    for name in ('ascii','cp437','utf-8','latin-1'):codecs.lookup(name)
    lib.read_gate([e['path'] for e in binding['hypotheses']+binding['calibrations']],OUT)
    cameras={}
    for item in binding['calibrations']:
        assert lib.sha(item['path'])==item['sha256'];cameras[item['sequence']]=lib.camera(np,item['path'])
    records=[]
    for pair,item in zip(binding['pairs'],binding['hypotheses']):
        assert pair['key']==item['key'] and lib.sha(item['path'])==item['sha256']
        with np.load(item['path'],allow_pickle=False) as data:
            xyz,xy=data['unique_camera_xyz'],data['unique_target_xy']
        result,arrays=pnp_lib.estimate(cv2,np,xyz,xy,cameras[pair['sequence']],method,pair['key'])
        with (OUT/(pair['key']+'.npz')).open('xb') as f:np.savez(f,**arrays)
        records.append({**pair,**result,'evidence':pair['key']+'.npz'})
    assert len(records)==200
    lib.save(OUT/'PREDICTIONS.json',records)
    lib.complete(OUT,{'pairs':200,'poses':sum(r['status']=='POSE' for r in records),'source_freeze_sha256':frozen,
        'reference_or_label_payload_reads':0,'scope':'Numerical metric-camera estimate in supplied LiDAR units; source-depth identities are hypotheses'})
    print('PR1 predictions complete200/200; no reference read')
except BaseException as error:
    lib.failure(OUT,error);raise
