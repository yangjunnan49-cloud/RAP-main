"""Freeze and generate SID0 synthetic equation cases; never opens real scans."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
from shared_identity_projector import apply, inverse, project, unpack

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/maintenance/2026-10-06/shared-identity-equations-01'
SEED = 20261006
TOL = 1e-9
KINDS = ('single','one_shared','consistent','conflict','gauge','common_gauge','scale','permutation','idempotent','unique_residual')


def write_json(p, data):
    p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def peak_rss():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class Info(ctypes.Structure):
            _fields_ = [('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
        info = Info(); info.cb = ctypes.sizeof(info)
        get_process = ctypes.windll.kernel32.GetCurrentProcess
        get_process.restype = wintypes.HANDLE
        get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
        get_memory.argtypes = (wintypes.HANDLE,ctypes.POINTER(Info),wintypes.DWORD)
        get_memory.restype = wintypes.BOOL
        if not get_memory(get_process(),ctypes.byref(info),info.cb):
            raise OSError('GetProcessMemoryInfo failed')
        return int(info.PeakWorkingSetSize)
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024


def pose(rng, angle=.3, shift=.5):
    axis = rng.normal(size=3); axis /= np.linalg.norm(axis)
    a = rng.uniform(-angle,angle)
    K = np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    T = np.eye(4); T[:3,:3] += np.sin(a)*K+(1-np.cos(a))*(K@K)
    T[:3,3] = rng.normal(size=3)*shift
    return T


def assemble(points, layout, Ts, perturbations, scales, centers, row_orders=None):
    counts = np.array([len(p) for p in points],dtype=np.int64)
    scans,windows,rows,offsets,conds,raws,perts,transforms = [],[],[],[0],[],[],[],[]
    f = 0
    for w, ids in enumerate(layout):
        for i in ids:
            row = np.arange(counts[i]) if row_orders is None else row_orders[f]
            pp = points[i][row]; pert = perturbations[f][row]
            y = apply(Ts[f],pp)+pert
            scans.append(i); windows.append(w); rows.append(row); offsets.append(offsets[-1]+len(row))
            conds.append((pp-centers[f])/scales[w]); raws.append(y/scales[w]); perts.append(pert); transforms.append(Ts[f]); f += 1
    return dict(points=np.concatenate(points),point_counts=counts,factor_scans=np.array(scans),factor_windows=np.array(windows),
                factor_rows=np.concatenate(rows),factor_offsets=np.array(offsets),scales=np.array(scales),centers=np.array(centers),
                cond=np.concatenate(conds),raw=np.concatenate(raws),analytic_T=np.array(transforms),perturbation=np.concatenate(perts))


def geometry(trial):
    rng = np.random.default_rng(SEED+trial)
    points = [rng.normal(size=(n,3))*[1.4,.9,.5]+[i*.2,0,0] for i,n in enumerate((17,19,13,11))]
    if trial >= 16:
        for p in points: p[:,2] = 0
    Z = np.array([pose(rng) for _ in points]); G = np.array([np.eye(4),pose(rng)])
    return rng,points,Z,G


def make_base(trial, kind):
    rng,points,Z,G = geometry(trial)
    layout = [[0,1,2,3]] if kind == 'single' else [[0,2],[0,1,3]] if kind == 'one_shared' else [[0,2,1],[0,1,3]]
    Ts,perts,centers = [],[],[]
    for w,ids in enumerate(layout):
        for i in ids:
            T = inverse(G[w]) @ Z[i]
            if kind == 'conflict' and w == 1 and i == 1:
                D = np.eye(4); a = .025
                D[:3,:3] = [[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]]
                D[:3,3] = [.12,-.05,.02]; T = D@T
            Ts.append(T)
            perts.append(rng.normal(size=points[i].shape)*(.003 if kind in ('single','one_shared','conflict') else 0))
            centers.append(rng.normal(size=3)*2)
    data = assemble(points,layout,Ts,perts,[1.7,3.2][:len(layout)],centers)
    data['synthetic_Z'] = Z; data['synthetic_G'] = G
    data['trial'] = np.array(trial)
    return data


def variant(base, kind, trial, result):
    data = {k:v.copy() for k,v in base.items()}
    factors = unpack(base); rng = np.random.default_rng(SEED+1000+trial)
    if kind in ('gauge','common_gauge'):
        H = np.array([pose(rng,.6,2) for _ in base['scales']])
        if kind == 'common_gauge': H[1] = H[0]
        data['gauge_changes'] = H
        for j,f in enumerate(factors):
            w,sl = f['w'],f['sl']
            data['raw'][sl] = apply(H[w],f['y'])/data['scales'][w]
            data['analytic_T'][j] = H[w]@base['analytic_T'][j]
            data['perturbation'][sl] = base['perturbation'][sl]@H[w,:3,:3].T
    elif kind == 'scale':
        data['scales'] = np.array([.7,6.3]); data['centers'] = rng.normal(size=data['centers'].shape)*7
        for j,f in enumerate(factors):
            data['raw'][f['sl']] = f['y']/data['scales'][f['w']]
            data['cond'][f['sl']] = (f['p']-data['centers'][j])/data['scales'][f['w']]
    elif kind == 'unique_residual':
        for j,f in enumerate(factors):
            if f['i'] in (2,3):
                extra = rng.normal(size=f['p'].shape)*50
                data['perturbation'][f['sl']] += extra
                data['raw'][f['sl']] += extra/data['scales'][f['w']]
    elif kind == 'idempotent':
        data['raw'] = result['clean'].copy()
        for j,f in enumerate(factors):
            data['analytic_T'][j] = inverse(result['G'][f['w']])@result['Z'][f['i']]
        data['perturbation'][:] = 0
    elif kind == 'permutation':
        order = np.array([5,3,1,4,0,2])
        fsnew = [factors[j] for j in order]
        chunks = [f['sl'] for f in fsnew]
        permrows = [rng.permutation(len(f['p'])) for f in fsnew]
        for name in ('raw','cond','perturbation','factor_rows'):
            data[name] = np.concatenate([base[name][sl][r] for sl,r in zip(chunks,permrows)])
        for name in ('factor_scans','factor_windows','centers','analytic_T'):
            data[name] = base[name][order].copy()
        data['factor_offsets'] = np.r_[0,np.cumsum([len(f['p']) for f in fsnew])]
    return data


def special(kind):
    rng = np.random.default_rng(SEED+2000)
    if kind.startswith('tree'):
        points = [rng.normal(size=(11+i,3)) for i in range(5)]
        layout = [[0,1],[1,2],[2,3,4]] if kind == 'tree_chain' else [[0,1,2],[0,3],[0,4]]
        Z = [pose(rng) for _ in points]; G = [np.eye(4),pose(rng),pose(rng)]
        Ts = [inverse(G[w])@Z[i] for w,ids in enumerate(layout) for i in ids]
        perts = [rng.normal(size=points[i].shape)*.004 for ids in layout for i in ids]
        return assemble(points,layout,Ts,perts,[1.2,2.7,.8],np.zeros((len(Ts),3)))
    if kind == 'wrong_consistent':
        p = np.vstack([np.eye(3),-np.eye(3)])
        points = [p.copy() for _ in range(4)]; Z = np.tile(np.eye(4),(4,1,1)); Z[1,0,3] = 2
        Ts = [Z[i] for ids in ([0,2,1],[0,1,3]) for i in ids]
        data = assemble(points,[[0,2,1],[0,1,3]],Ts,[np.zeros_like(p) for _ in Ts],[1.,2.],np.zeros((6,3)))
        data['synthetic_truth_rel'] = np.eye(4); return data
    data = make_base(0,'single')
    if kind == 'disconnected':
        _,points,Z,G = geometry(0); layout = [[0,2],[1,3]]
        Ts = [inverse(G[w])@Z[i] for w,ids in enumerate(layout) for i in ids]
        return assemble(points,layout,Ts,[np.zeros_like(points[i]) for ids in layout for i in ids],[1.,2.],np.zeros((4,3)))
    n = int(data['point_counts'][0]); sl = slice(0,n)
    if kind in ('coincident','collinear'):
        data['points'][sl] = 0
        if kind == 'collinear': data['points'][sl,0] = np.linspace(-1,1,n)
        data['cond'][sl] = (data['points'][sl]-data['centers'][0])/data['scales'][0]
        data['perturbation'][sl] = 0
        data['raw'][sl] = apply(data['analytic_T'][0],data['points'][sl])/data['scales'][0]
    elif kind == 'collapsed_target':
        y = np.zeros((n,3)); data['perturbation'][sl] = y-apply(data['analytic_T'][0],data['points'][sl]); data['raw'][sl] = y
    elif kind == 'reflected_ambiguous':
        p = np.vstack([np.eye(3),-np.eye(3)])
        points = [p.copy() for _ in range(4)]; T = np.eye(4)
        R = np.diag([-1.,1.,1.]); perts = [p@R.T-p,np.zeros_like(p),np.zeros_like(p),np.zeros_like(p)]
        data = assemble(points,[[0,1,2,3]],[T.copy() for _ in points],perts,[1.],np.zeros((4,3)))
    return data


def toy(kind):
    p = np.vstack([np.eye(3),-np.eye(3)])
    data = assemble([p,p],[[0,1],[0,1]],[np.eye(4)]*4,[np.zeros_like(p)]*4,[1.,1.],np.zeros((4,3)))
    bias = np.array([1.,3.]); noise = np.zeros_like(data['raw']); stateC=noise.copy(); stateI=noise.copy()
    baseY = data['raw'].copy()
    for f in unpack(data):
        if f['i'] == 1: baseY[f['sl'],0] += bias[f['w']]
    saved = {arm+'_'+name:[] for arm in ('C','I') for name in ('raw','clean','state','velocity','rel')}
    results = []
    for t in (1.,.5):
        for arm,state in (('C',stateC),('I',stateI)):
            if kind == 'toy_state_dependent':
                Y = data['raw'].copy()
                for w in range(2):
                    fs = [f for f in unpack(data) if f['w']==w]
                    r = state[fs[1]['sl']].mean(0)-state[fs[0]['sl']].mean(0)
                    Y[fs[1]['sl'],0] += bias[w]+r[0]**2
                velocity = (state-Y)/t
            else:
                velocity = -baseY
                Y = state-t*velocity
            item = {k:v.copy() for k,v in data.items()}; item['raw'] = Y
            result = project(item)
            clean = result['clean'] if arm == 'C' else result['native_clean']
            # I relative is window0's native anchor pair, never joint pose.
            relative = result['rel'] if arm == 'C' else inverse(result['native_T'][0])@result['native_T'][1]
            for name,val in (('raw',Y),('clean',clean),('state',state),('velocity',velocity),('rel',relative)):
                saved[arm+'_'+name].append(val.copy())
            state[:] = (1-t+.5)*clean+(t-.5)*noise
            if arm == 'C': finalC = result; finalInput = item
            else: finalF = result
    for key,vals in saved.items(): finalInput[key] = np.array(vals)
    finalInput.update(times=np.array([1.,.5]),bias=bias,noise=noise,F_clean=finalF['clean'],F_rel=finalF['rel'],
                      C_final_state=stateC,I_final_state=stateI)
    # Bind final raw analytic inputs explicitly; only pure translations used.
    finalInput['analytic_T'] = np.tile(np.eye(4),(4,1,1))
    finalInput['perturbation'] = finalInput['raw']-data['raw']
    return finalInput,finalC


def inventory():
    rows = []
    for trial in range(32):
        for kind in KINDS:
            row = dict(id=f'{trial:02d}_{kind}',kind=kind,trial=trial)
            if kind in ('gauge','common_gauge','scale','permutation','idempotent','unique_residual'): row['reference_id'] = f'{trial:02d}_conflict'
            rows.append(row)
    for kind in ('tree_chain','tree_star','wrong_consistent','coincident','collinear','collapsed_target','reflected_ambiguous','disconnected','toy_constant_velocity','toy_state_dependent'):
        row = dict(id=kind,kind=kind)
        if kind in ('coincident','collinear','collapsed_target','reflected_ambiguous','disconnected'): row['expected_error'] = 'undefined_fit'
        rows.append(row)
    return rows


def maxdelta(a,b): return float(np.max(np.abs(a-b)))


def check(data,result,kind,base=None,base_result=None):
    assert bool(result['converged']), '64-sweep nonconvergence'
    for T in np.concatenate([result['G'],result['Z'],result['native_T']]):
        assert maxdelta(T[:3,:3].T@T[:3,:3],np.eye(3)) <= 1e-10
        assert abs(np.linalg.det(T[:3,:3])-1) <= 1e-10
    assert np.all(np.diff(result['objective_trace']) <= 1e-10), 'objective increase'
    if kind in ('single','one_shared','tree_chain','tree_star','consistent'):
        assert maxdelta(result['clean'],result['native_clean']) <= TOL, 'native reduction'
    if kind == 'conflict':
        native_rel = inverse(result['native_T'][0])@result['native_T'][2]
        assert maxdelta(result['rel'],native_rel) > 1e-5, 'gauge-only effect'
        assert result['shared_objective_trace'][-1] <= result['shared_objective_trace'][0]+1e-10
    if kind in ('scale','permutation','unique_residual','idempotent'):
        assert maxdelta(result['rel'],base_result['rel']) <= TOL, kind+' relative identity'
        if kind == 'unique_residual':
            assert maxdelta(result['G_trace'],base_result['G_trace']) <= TOL
            assert maxdelta(result['shared_objective_trace'],base_result['shared_objective_trace']) <= TOL
        if kind == 'idempotent': assert maxdelta(result['clean'],data['raw']) <= TOL
    if kind in ('gauge','common_gauge'):
        H = data['gauge_changes']
        assert maxdelta(result['rel'],base_result['rel']) <= TOL
        assert maxdelta(result['Z'],H[0]@base_result['Z']) <= TOL
        assert maxdelta(result['G'][1],H[0]@base_result['G'][1]@inverse(H[1])) <= TOL
        for f in unpack(data):
            y = base_result['clean'][f['sl']]*base['scales'][f['w']]
            assert maxdelta(result['clean'][f['sl']]*data['scales'][f['w']],apply(H[f['w']],y)) <= TOL
    if kind == 'wrong_consistent':
        assert result['shared_objective_trace'][-1] <= 1e-20
        assert abs(result['rel'][0,3]-2) <= TOL
    if kind.startswith('toy'):
        expected = 3. if kind == 'toy_state_dependent' else 2.
        expectedF = 3.25 if kind == 'toy_state_dependent' else 2.
        assert abs(result['rel'][0,3]-expected) <= TOL
        assert abs(data['F_rel'][0,3]-expectedF) <= TOL
        if kind == 'toy_state_dependent': assert maxdelta(data['C_raw'][1],data['I_raw'][1]) > .1


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'freeze.json').exists(): raise RuntimeError('freeze already exists')
    manifest = dict(stage='SID0',seed=SEED,trials=32,fullrank_trials=list(range(16)),planar_trials=list(range(16,32)),
                    case_inventory=inventory(),point_counts=[17,19,13,11],synthetic_only=True)
    write_json(OUT/'manifest.json',manifest)


def freeze():
    if (OUT/'freeze.json').exists(): raise RuntimeError('freeze already exists')
    manifest = json.loads((OUT/'manifest.json').read_text())
    names = [OUT/'PROTOCOL.md',OUT/'manifest.json']+[ROOT/'scripts/maintenance'/n for n in ('shared_identity_projector.py','shared_identity_equations.py','validate_shared_identity_equations.py')]
    design = ROOT/'docs/maintenance/2026-10-06/shared-identity-design-01'
    names += [design/n for n in ('PLAN.md','RESEARCH_REPORT.md','PRIOR_ART.md','SOURCE_AUDIT.json')]
    names.append(Path(sys.executable))
    identities = [dict(path=str(p.resolve()),sha256=sha(p),size=p.stat().st_size) for p in names]
    write_json(OUT/'freeze.json',dict(stage='SID0',created_utc=stamp(),sources=identities,case_inventory=manifest['case_inventory'],
               runtime=dict(python_version=sys.version,numpy_version=np.__version__,python_executable=sys.executable),
               limits=dict(cpu_seconds=120,rss_bytes=1073741824,artifact_bytes=20000000),
               tolerances=dict(points=TOL,poses=TOL,rotations=1e-10,fit_uniqueness=1e-12,shared_objective_stop=1e-12,max_sweeps=64)))


def bank():
    frozen = json.loads((OUT/'freeze.json').read_text())
    for item in frozen['sources']:
        assert sha(Path(item['path'])) == item['sha256'], 'source identity changed'
    if (OUT/'bank.json').exists() or (OUT/'cases').exists(): raise RuntimeError('bank cannot overwrite previous output')
    (OUT/'INCOMPLETE').write_text('SID0 bank and independent validation are not complete.\n')
    (OUT/'cases').mkdir()
    started = time.perf_counter(); rows = []; references = {}; maxima = {}
    try:
        for item in frozen['case_inventory']:
            row = dict(item); kind = item['kind']; trial = item.get('trial')
            base=base_result=None
            if trial is not None:
                if kind in ('single','one_shared','consistent','conflict'): data=make_base(trial,kind)
                else:
                    base,base_result=references[item['reference_id']]
                    data=variant(base,kind,trial,base_result)
                result=None
            elif kind.startswith('toy'): data,result=toy(kind)
            else: data=special(kind); result=None
            data['case_id']=np.array(item['id']); data['kind']=np.array(kind)
            if 'expected_error' in item:
                from shared_identity_projector import UndefinedFit
                try: project(data)
                except UndefinedFit as exc: data['observed_error']=np.array(str(exc))
                else: raise AssertionError('expected degeneracy not rejected')
            else:
                result=project(data) if result is None else result
                check(data,result,kind,base,base_result)
                data.update(result)
                if kind == 'conflict': references[item['id']]=({k:v.copy() for k,v in data.items() if k not in result},result)
                maxima[item['id']]=dict(sweeps=int(result['sweeps']),shared_start=float(result['shared_objective_trace'][0]),shared_end=float(result['shared_objective_trace'][-1]))
            relative='cases/'+item['id']+'.npz'; row['file']=relative
            np.savez_compressed(OUT/relative,**data); rows.append(row)
            assert time.perf_counter()-started <= 120, 'CPU cap'
            assert peak_rss() <= 1073741824, 'RSS cap'
        wall=time.perf_counter()-started
        artifact=sum(p.stat().st_size for p in (OUT/'cases').glob('*.npz'))
        assert artifact <= 20000000, 'artifact cap'
        write_json(OUT/'bank.json',dict(stage='SID0',freeze_sha256=sha(OUT/'freeze.json'),rows=rows,wall_seconds=wall,peak_rss_bytes=peak_rss(),artifact_bytes=artifact))
        write_json(OUT/'runner_checks.json',dict(case_count=len(rows),per_case=maxima,wall_seconds=wall))
        files=[OUT/'bank.json']+sorted((OUT/'cases').glob('*.npz'))
        write_json(OUT/'bank_seal.json',dict(stage='SID0',created_utc=stamp(),freeze_sha256=sha(OUT/'freeze.json'),files=[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p),size=p.stat().st_size) for p in files]))
        print(json.dumps(dict(stage='SID0_BANK_SEALED',cases=len(rows),wall_seconds=wall,peak_rss_bytes=peak_rss(),artifact_bytes=artifact)))
    except Exception as exc:
        write_json(OUT/'FAILURE.json',dict(stage='BANK_FAILED',error=repr(exc),completed_cases=len(rows),active_case=item['id'],wall_seconds=time.perf_counter()-started))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('prepare','freeze','bank')); args=parser.parse_args()
    {'prepare':prepare,'freeze':freeze,'bank':bank}[args.stage]()
