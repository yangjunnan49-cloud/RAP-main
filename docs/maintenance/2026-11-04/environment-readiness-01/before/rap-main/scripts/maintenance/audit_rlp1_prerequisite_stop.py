"""Independently validate preserved partial weak-label evidence and stop only."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp1_attempt03_common as r
import rlp1_validation_math as v
from validate_rlp1_weak_preflight import compare_labels

A=r.B/'prerequisite-stop-audit'


def freeze():
    assert not (r.WEAK/'bank_seal.json').exists()
    r.validated(r.ENG);r.check(r.ENG);r.check_seal(r.ENG);r.check(r.WEAK)
    completed=sorted((r.WEAK/'bank').glob('*.npz'))
    assert len(completed)==14
    real=[p for p in completed if p.name[0].isdigit()]
    assert [p.name for p in real]==['00_000200.npz','05_000200.npz','06_000200.npz']
    selected=[row for row in c.read(r.WEAK/'freeze.json')['rows'] if row['seq'] in ('00','05','06')]
    extra=completed+[r.WEAK/'freeze.json',r.B/'FAILURE_attempt03_weak_preflight_bank.json',
        r.ENG/'freeze.json',r.ENG/'bank_seal.json',r.ENG/'validation.json',r.ENG/'validation_seal.json',
        Path(__file__).with_name('rlp1_attempt03_common.py'),Path(__file__).with_name('rlp1_validation_math.py'),
        Path(__file__).with_name('validate_rlp1_weak_preflight.py')]
    extra += [r.ENG/'bank'/f"{r.stem(row)}_J.npz" for row in selected]
    r.freeze(A,selected,__file__,__file__,gt=True,extra_files=extra,
        purpose='Independent audit of completed partial files; no completion/retry of failed bank',
        original_stage_incomplete=True)
    (A/'bank').mkdir()
    c.save(A/'bank.json',dict(utc=c.now(),partial_files={str(p):c.sha(p) for p in completed},
        original_weak_stage_incomplete=True,training=False))
    r.seal(A);r.finish('stop_audit_freeze');print('Partial-evidence stop audit frozen',flush=True)


def validate():
    f=r.check(A);r.check_seal(A);r.check(r.WEAK);r.validated(r.ENG)
    metadata=c.read(A/'bank.json');maximum=0.;solver=0.;gradient=0.;synthetic=0;rows=[]
    for path,digest in metadata['partial_files'].items():
        assert c.sha(Path(path))==digest
        if not Path(path).name.startswith('synthetic'):continue
        synthetic+=1
        with np.load(path,allow_pickle=False) as z:
            if 'poses' in z:
                maximum=max(maximum,compare_labels(z,v.labels(z['points'],z['poses'])))
            elif 'weights' in z:
                if 'rank1' in path:
                    try:v.weighted_horn(z['source'],z['target'],z['weights'])
                    except AssertionError:pass
                    else:raise AssertionError('Independent rank1 rejection failed')
                else:
                    T,gap=v.weighted_horn(z['source'],z['target'],z['weights'])
                    delta=max(float(abs(T-z['pose']).max()),float(abs(T-z['expected']).max()))
                    solver=max(solver,delta);assert delta<1e-8
                    assert abs(gap-float(z['gap']))<1e-10
            elif 'proper' in z:
                rotations=np.array([v.quaternion_rotation(A0.T)[0] for A0 in z['raw']])
                assert abs(rotations-z['proper']).max()<1e-10
            elif 'C' in z:
                recovered=np.array([np.linalg.inv(z['C'])@P@z['C'] for P in z['camera']])
                assert abs(recovered-z['expected']).max()<1e-10 and abs(recovered-z['recovered']).max()<1e-10
            elif 'gradient' in z:
                source,target,W=z['source'],z['target'],z['W'];mass=W.sum()
                cx=W.sum(0)@source/mass;cy=W.sum(1)@target/mass
                R,gap=v.quaternion_rotation((source-cx).T@W.T@(target-cy))
                assert abs(R-z['R']).max()<1e-8 and abs(cy-R@cx-z['t']).max()<1e-8
                assert np.isfinite(z['gradient']).all() and abs(z['gradient']).max()>0
                for ii,jj in ((0,0),(1,2),(30,20)):
                    values=[]
                    for sign in (-1,1):
                        ww=W.copy();ww[ii,jj]+=sign*1e-5;m=ww.sum()
                        a=ww.sum(0)@source/m;b=ww.sum(1)@target/m
                        rotation,_=v.quaternion_rotation((source-a).T@ww.T@(target-b))
                        values.append((rotation**2).sum()+((b-rotation@a)**2).sum())
                    delta=abs((values[1]-values[0])/2e-5-z['gradient'][ii,jj]);gradient=max(gradient,float(delta))
                    assert delta<1e-6
    for row in f['rows']:
        path=r.WEAK/'bank'/f"{r.stem(row)}.npz"
        with np.load(path,allow_pickle=False) as z, np.load(r.ENG/'bank'/f"{r.stem(row)}_J.npz",allow_pickle=False) as original:
            assert np.array_equal(z['points'],original['points'])
            expected=v.labels(z['points'],v.gt_selected(c.DATA,row))
            maximum=max(maximum,compare_labels(z,expected))
            counts={f'{a}{b}':dict(positive=int((z[f'class_{a}{b}']==1).sum()),unmatched=int((z[f'class_{a}{b}']==2).sum()),ignored=int((z[f'class_{a}{b}']==0).sum())) for a in range(3) for b in range(3) if a!=b}
            rows.append(dict(seq=row['seq'],t=row['t'],counts=counts,coverage_gate=all(x['positive']>=20 for x in counts.values())))
        print('Independent partial label evidence',row['seq'],{key:value['positive'] for key,value in counts.items()},flush=True)
        r.cap()
    assert synthetic==11 and len(rows)==3
    assert rows[0]['coverage_gate'] and rows[1]['coverage_gate'] and not rows[2]['coverage_gate']
    assert rows[2]['counts']['02']['positive']==15 and rows[2]['counts']['20']['positive']==15
    assert not (r.WEAK/'bank'/'07_000200.npz').exists()
    assert all(not path.exists() for path in (r.FULL,r.LAB,r.FIT,r.EVAL))
    r.pass_validation(A,dict(decision='VALIDATED_PREREQUISITE_STOP_INSUFFICIENT_WEAK_LABEL_COVERAGE',
        partial_real_windows=3,unprocessed_real_windows=['07_000200'],rows=rows,synthetic_npzs=11,
        maximum_label_and_truth_delta=maximum,maximum_horn_solver_delta=solver,
        maximum_selected_finite_difference_gradient_delta=gradient,
        original_weak_bank_complete=False,original_weak_stage_validated=False,
        no_fit_or_accuracy_conclusion=True,training_updates=0,**r.usage()))
    r.finish('stop_audit_validation');print('Independent prerequisite stop VALIDATED',maximum,flush=True)


if __name__=='__main__':
    try:{'freeze':freeze,'validate':validate}[sys.argv[1]]()
    except Exception as ex:r.fail('stop_audit_'+sys.argv[1],ex);raise
