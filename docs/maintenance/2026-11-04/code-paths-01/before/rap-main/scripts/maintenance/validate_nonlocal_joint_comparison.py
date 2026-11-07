"""Independent NJE0 saved-input/prediction/scalar validation; no model rerun."""
import hashlib,itertools,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    d=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):d.update(chunk)
    return d.hexdigest()
def checked_fit(x,y):
    # Separate rotation alignment API; no primary driver or native model import.
    ax=x.mean(0);ay=y.mean(0);r,_=Rotation.align_vectors(y-ay,x-ax)
    z=np.eye(4);z[:3,:3]=r.as_matrix();z[:3,3]=ay-z[:3,:3]@ax;return z
freeze=read(BASE/'freeze.json');inputs=np.load(BASE/'inputs.npz',allow_pickle=False);meta=read(BASE/'inputs.json');assert sha(BASE/'inputs.npz')==meta['inputs_sha256']
for row in meta['views']:
    s,i=row['sequence'],row['frame'];tag=f'{s}_{i}';original=np.load(row['cache'],allow_pickle=False)
    assert sha(row['cache'])==row['cache_sha256'] and np.array_equal(original,inputs[tag+'_full'])
    seed=int.from_bytes(hashlib.sha256(f'NJE0|{s}|{i}|rows'.encode()).digest()[:4],'big');rows=np.sort(np.random.default_rng(seed).choice(4000,1000,replace=False))
    assert np.array_equal(rows,inputs[tag+'_rows']) and np.array_equal(original[rows],inputs[tag+'_q'])
    noise_seed=int.from_bytes(hashlib.sha256(f'NJE0|{s}|{i}|noise'.encode()).digest()[:4],'big')
    assert noise_seed==row['noise_seed'] and np.array_equal(np.random.default_rng(noise_seed).standard_normal((1000,3)).astype(np.float32),inputs[tag+'_noise'])
    center=original[rows].astype(float).mean(0);assert np.array_equal(center,inputs[tag+'_center'])
    assert np.array_equal(((original[rows].astype(float)-center)/inputs[s+'_scale'][0]).astype(np.float32),inputs[tag+'_cond'])
available={'inputs_checked':29,'geometry_groups_checked':0,'native_predictions_available':(BASE/'neural.json').exists(),'metric_available':(BASE/'metrics.json').exists()}
for c in freeze['groups']:
    p=BASE/f'geometry_{c["sequence"]}.json'
    if not p.exists():continue
    g=read(p);expected=list(itertools.combinations(c['nodes'],2))
    for method in ('G','W'):
        pairs=g['work'][method]['all_pairs'];assert [(r['i'],r['j']) for r in pairs]==expected
        for r in pairs:
            assert len(r['candidates'])==(2 if method=='G' else 3)
            chosen=min(r['candidates'],key=lambda e:(e['score'],e['start']));assert r['T']==chosen['T'] and r['start']==chosen['start']
        for kind in ('d','s'):
            out=g['outputs'][method+kind];assert [(r['i'],r['j']) for r in out]==[(r['i'],r['j']) for r in c['edges']]
            for r in out:
                t=np.asarray(r['T']);assert np.isfinite(t).all() and np.max(abs(t[3]-[0,0,0,1]))<1e-12 and np.max(abs(t[:3,:3].T@t[:3,:3]-np.eye(3)))<1e-5
    available['geometry_groups_checked']+=1
if available['native_predictions_available']:
    seal=read(BASE/'PREDICTION_SEAL.json')
    for name,r in seal['files'].items():assert sha(BASE/name)==r['sha256'] and (BASE/name).stat().st_size==r['bytes']
    max_fit=0.;files=list(BASE.glob('*_fit.npz'));assert len(files)==36
    for file in files:
        with np.load(file,allow_pickle=False) as z:
            for k in range(len(z.files)//5):
                a=checked_fit(z[f'part{k}_cond'],z[f'part{k}_end']);err=float(np.max(abs(a-z[f'part{k}_horn'])));max_fit=max(max_fit,err);assert err<1e-4
                assert np.max(abs(a-z[f'part{k}_native']))<1e-3
    available['independent_fit_error']=max_fit
if available['metric_available']:
    m=read(BASE/'metrics.json');assert len(m['rows'])==256
    for method,means in m['means'].items():
        rows=[r for r in m['rows'] if r['method']==method];assert len(rows)==32
        for k,v in means.items():assert abs(sum(r[k] for r in rows)/32-v)<1e-10
    controls=('P','Ps','Gd','Gs','Wd','Ws');means=m['means'];gates=dict(aggregate_RTE=all(means['J']['RTE']<=.95*means[n]['RTE'] for n in controls),aggregate_RRE=all(means['J']['RRE_deg']<=means[n]['RRE_deg']+.05 for n in controls),every_group_RTE=all(g['means']['J']['RTE']<=min(g['means'][n]['RTE'] for n in controls)+.005 for g in m['groups']))
    assert gates==m['gates'] and all(gates.values())==m['engineering_admitted']
available.update(passed=True,full_comparison_complete=available['native_predictions_available'] and available['metric_available'],model_reruns=0)
with (BASE/'validation.json').open('x') as f:json.dump(available,f,indent=2)
print(json.dumps(available),flush=True)
