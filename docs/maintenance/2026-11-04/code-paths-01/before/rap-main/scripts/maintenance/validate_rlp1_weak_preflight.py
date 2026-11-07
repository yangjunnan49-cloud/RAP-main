"""Independent labels, frame convention, Horn and gradient prerequisites."""
import numpy as np
import local_motion_common as c
import rlp1_attempt03_common as r
import rlp1_validation_math as v


def compare_labels(actual,expected):
    maximum=0.
    for key,val in expected.items():
        if key.startswith(('positive','class','support')):assert np.array_equal(actual[key],val),key
        else:
            finite=np.isfinite(val)
            assert np.array_equal(finite,np.isfinite(actual[key])),key
            delta=float(abs(actual[key][finite]-val[finite]).max()) if finite.any() else 0.
            maximum=max(maximum,delta);assert delta<1e-10,(key,delta)
    return maximum


def validate():
    f=r.check(r.WEAK);seal=r.check_seal(r.WEAK);r.validated(r.ENG)
    maximum=0.;rows=[];solver_max=0.
    for path in sorted((r.WEAK/'bank').glob('synthetic_*.npz')):
        with np.load(path,allow_pickle=False) as z:
            if 'poses' in z:
                maximum=max(maximum,compare_labels(z,v.labels(z['points'],z['poses'])))
            elif 'weights' in z:
                if 'rank1' in path.name:
                    try:v.weighted_horn(z['source'],z['target'],z['weights'])
                    except AssertionError:pass
                    else:raise AssertionError('Independent rank1 rejection failed')
                else:
                    T,gap=v.weighted_horn(z['source'],z['target'],z['weights'])
                    delta=float(abs(T-z['pose']).max());solver_max=max(solver_max,delta);assert delta<1e-8
                    assert abs(T-z['expected']).max()<1e-8 and abs(gap-float(z['gap']))<1e-10
            elif 'proper' in z:
                rotations=np.array([v.quaternion_rotation(A.T)[0] for A in z['raw']])
                assert abs(rotations-z['proper']).max()<1e-10
            elif 'C' in z:
                recovered=np.array([np.linalg.inv(z['C'])@P@z['C'] for P in z['camera']])
                assert abs(recovered-z['expected']).max()<1e-10
                assert abs(recovered-z['recovered']).max()<1e-10
            elif 'gradient' in z:
                source,target,W=z['source'],z['target'],z['W'];mass=W.sum()
                cx=W.sum(0)@source/mass;cy=W.sum(1)@target/mass
                R,gap=v.quaternion_rotation((source-cx).T@W.T@(target-cy))
                assert abs(R-z['R']).max()<1e-8 and abs(cy-R@cx-z['t']).max()<1e-8
                assert np.isfinite(z['gradient']).all() and abs(z['gradient']).max()>0
                # Central finite differences independently check selected W gradients.
                for ii,jj in ((0,0),(1,2),(30,20)):
                    values=[]
                    for sign in (-1,1):
                        ww=W.copy();ww[ii,jj]+=sign*1e-5;m=ww.sum()
                        a=ww.sum(0)@source/m;b=ww.sum(1)@target/m
                        rot,_=v.quaternion_rotation((source-a).T@ww.T@(target-b))
                        values.append((rot**2).sum()+((b-rot@a)**2).sum())
                    numerical=(values[1]-values[0])/2e-5
                    assert abs(numerical-z['gradient'][ii,jj])<1e-6
    for row in f['rows']:
        poses=v.gt_selected(c.DATA,row)
        with np.load(r.WEAK/'bank'/f"{r.stem(row)}.npz",allow_pickle=False) as z, \
             np.load(r.ENG/'bank'/f"{r.stem(row)}_J.npz",allow_pickle=False) as source:
            assert np.array_equal(z['points'],source['points'])
            maximum=max(maximum,compare_labels(z,v.labels(z['points'],poses)))
            counts={f'{a}{b}':dict(positive=int((z[f'class_{a}{b}']==1).sum()),unmatched=int((z[f'class_{a}{b}']==2).sum()),ignored=int((z[f'class_{a}{b}']==0).sum())) for a in range(3) for b in range(3) if a!=b}
            assert all(x['positive']>=20 for x in counts.values())
            record=next(x for x in c.read(r.WEAK/'bank.json')['rows'] if x['seq']==row['seq'])
            assert counts==record['counts'];rows.append(dict(seq=row['seq'],counts=counts))
        r.cap();print('RLP1 independent weak-label validation',row['seq'],flush=True)
    gradients=c.read(r.WEAK/'bank.json')['gradient_checks']
    assert len(gradients)==4 and all(np.isfinite(x['loss']) for x in gradients)
    r.pass_validation(r.WEAK,dict(decision='PASS_WEAK_LABEL_AND_SOLVER_PREFLIGHT',rows=rows,
        maximum_label_and_truth_delta=maximum,maximum_solver_delta=solver_max,
        weak_physical_identity_verified=False,training_updates=0,**r.usage()))
    r.finish('weak_preflight_validation');print('RLP1 weak-label preflight VALIDATED',maximum,flush=True)


if __name__=='__main__':
    try:validate()
    except Exception as ex:r.fail('weak_preflight_validation',ex);raise

