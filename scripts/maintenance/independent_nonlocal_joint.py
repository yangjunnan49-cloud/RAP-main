"""NJE0 independent brute-force geometry, decoder and reference verification."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01';DATA=ROOT.parent/'Datasets/data_odometry_velodyne/dataset'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):
    d=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):d.update(block)
    return d.hexdigest()
def loadposes(path):
    rows=np.loadtxt(path);out=np.repeat(np.eye(4)[None],len(rows),axis=0);out[:,:3,:]=rows.reshape(-1,3,4);return out
frozen=read(BASE/'freeze.json');seal=read(BASE/'PREDICTION_SEAL.json')
for name,row in frozen['files'].items():assert digest(name)==row['sha256']
for name,row in seal['files'].items():assert digest(BASE/name)==row['sha256']
receipt_seal=read(BASE/'supervision/seal/exit.json');receipt_metrics=read(BASE/'supervision/metrics/launch.json')
assert receipt_seal['utc_end']<receipt_metrics['utc_start']
inputs=np.load(BASE/'inputs.npz',allow_pickle=False);scores=[];metrics=[];decoder=[];candidate_count=0;edge_count=0
for group in frozen['groups']:
    s=group['sequence'];geom=read(BASE/f'geometry_{s}.json');native=read(BASE/f'neural_{s}.json')
    for method in ('G','W'):
        for edge in geom['work'][method]['all_pairs']:
            suffix='_q' if method=='G' else '_full';p=inputs[f'{s}_{edge["i"]}'+suffix].astype(float);q=inputs[f'{s}_{edge["j"]}'+suffix].astype(float)
            for candidate in edge['candidates']:
                t=np.asarray(candidate['T']);z=q@t[:3,:3].T+t[:3,3];forward=np.full(len(q),np.inf);reverse=np.full(len(p),np.inf)
                # Full candidate matrix in bounded blocks, no KDTree or primary helper.
                for a in range(0,len(q),256):
                    distance=cdist(z[a:a+256],p,metric='sqeuclidean');forward[a:a+256]=distance.min(1);reverse=np.minimum(reverse,distance.min(0))
                score=float((np.minimum(forward,6.25).mean()+np.minimum(reverse,6.25).mean())/2)
                support=float(min(np.mean(forward<=6.25),np.mean(reverse<=6.25)))
                scores.append(abs(score-candidate['score']));assert abs(score-candidate['score'])<1e-8 and abs(support-candidate['support'])<1e-12
                candidate_count+=1
    # Independent reconstruction from saved native normalized fits and view centers.
    def parts(filename,ids):
        z=np.load(BASE/filename,allow_pickle=False);result=[]
        for k,i in enumerate(ids):
            a=z[f'part{k}_native'];b=a.copy();b[:3,3]=inputs[f'{s}_scale'][0]*a[:3,3]-a[:3,:3]@inputs[f'{s}_{i}_center']
            assert np.max(abs(b-z[f'part{k}_meter']))<1e-12;result.append(b)
        return result
    joint=parts(native['joint_work']['fit_file'],group['nodes']);lookup=dict(zip(group['nodes'],joint))
    for k,edge in enumerate(group['edges']):
        a,b=parts(native['pair_work'][k]['fit_file'],[edge['i'],edge['j']]);pair=np.linalg.solve(a,b)
        j=np.linalg.solve(lookup[edge['i']],lookup[edge['j']]);ep=float(np.max(abs(pair-np.asarray(native['outputs']['P'][k]['T']))));ej=float(np.max(abs(j-np.asarray(native['outputs']['J'][k]['T']))))
        # Primary transpose inverse vs general matrix solve: float32 rotation tolerance.
        assert max(ep,ej)<1e-3;decoder.extend([ep,ej]);edge_count+=1
    gt=loadposes(DATA/'poses'/f'{s}.txt');calib=DATA/'sequences'/s/'calib.txt';tr=np.eye(4)
    entry=next(l for l in calib.read_text().splitlines() if l.startswith('Tr:'));tr[:3]=np.fromstring(entry.split(':',1)[1],sep=' ').reshape(3,4)
    truth=np.stack([np.linalg.solve(tr,t@tr) for t in gt])
    source='2026-09-26/e0-frontend-01' if s in ('00','05','06') else '2026-09-27/e0-heldout-01'
    odom=loadposes(ROOT/'docs/maintenance'/source/f'full-{s}-A/odom_poses.txt');outputs={**geom['outputs'],**native['outputs']}
    # Exact stored odometry control uses transpose form on rounded saved rotations.
    old=[]
    for e in group['edges']:
        a,b=odom[e['i']],odom[e['j']];v=np.eye(4);v[:3,:3]=a[:3,:3].T@b[:3,:3];v[:3,3]=a[:3,:3].T@(b[:3,3]-a[:3,3]);old.append(dict(**e,T=v.tolist()))
    outputs['O']=old
    saved=read(BASE/'metrics.json')['rows']
    for method,rows in outputs.items():
        for e in rows:
            reference=np.linalg.solve(truth[e['i']],truth[e['j']]);p=np.asarray(e['T']);rte=float(np.linalg.norm(reference[:3,3]-p[:3,3]));rre=float(np.degrees(Rotation.from_matrix(reference[:3,:3].T@p[:3,:3]).magnitude()))
            row=next(x for x in saved if x['sequence']==s and x['method']==method and x['i']==e['i'] and x['j']==e['j'])
            te=abs(rte-row['RTE']);re=abs(rre-row['RRE_deg']);assert te<1e-8 and re<1e-3;metrics.append((te,re))
result=dict(passed=True,geometry_candidates_bruteforce_checked=candidate_count,geometry_score_max_error=max(scores),original_edges_decoded=edge_count,decoder_max_error=max(decoder),reference_metric_rows=len(metrics),RTE_max_error=max(a for a,b in metrics),RRE_max_error_deg=max(b for a,b in metrics),prediction_seal_before_reference_stage=True,model_reruns=0)
with (BASE/'independent_validation.json').open('x') as out:json.dump(result,out,indent=2)
print(json.dumps(result),flush=True)
