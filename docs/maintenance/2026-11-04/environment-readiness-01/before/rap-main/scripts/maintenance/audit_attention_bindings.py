"""CPU-only exact AOD input and per-Q/K/V difference binding proof."""
import signal,time,sys,traceback
import attention_operator_diagnosis as r
stage='audit';r.START=time.monotonic();ok=False;error=None
used=sum(r.read(p)['wall_seconds'] for p in r.SUP.glob('*/child_exit.json'))
signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('AOD remaining cap')));signal.alarm(max(1,int(600-used)))
try:
    import numpy as np
    r.verify();extra=r.read(r.BASE/'INPUT_AUDIT_FREEZE.json')
    for path,h in extra['files'].items():assert r.sha(r.MAIN/path)==h,path
    assert extra['original_freeze_sha256']==r.sha(r.BASE/'freeze.json')
    records=[]
    for arm in ('V','P'):
        with np.load(r.PRIOR/f'traces/{arm}_full1/hooks.npz') as old,np.load(r.BASE/f'bank/{arm}_input.npz') as inputs:
            assert np.array_equal(old['transformer_layers.11.global_qkv_proj|output'],inputs['raw'])
            assert np.array_equal(old['transformer_layers.11.global_out_proj|input'],inputs['saved_out'])
            assert np.array_equal(old['transformer_layers.11.global_out_proj|scaled_gradient'],inputs['go'])
        with np.load(r.BASE/f'bank/{arm}_default1.npz') as first: reference=first['normalized'].copy()
        for backend in ('default','math'):
            with np.load(r.BASE/f'bank/{arm}_{backend}1.npz') as a,np.load(r.BASE/f'bank/{arm}_{backend}2.npz') as b:
                assert np.array_equal(reference,a['normalized']) and np.array_equal(reference,b['normalized'])
                component=[]
                for k in range(3):
                    delta=a['normalized_gradient'][:,k].astype(float)-b['normalized_gradient'][:,k].astype(float)
                    component.append(dict(component=('Q','K','V')[k],different=int(np.count_nonzero(delta)),max_abs=float(np.max(abs(delta)))))
                records.append(dict(arm=arm,backend=backend,normalized_inputs_byteexact=True,components=component))
        r.cap()
    r.save(r.BASE/'INPUT_BINDING_AUDIT.json',dict(passed=True,archived_raw_projection_GO_exact=True,all_normalized_inputs_exact=True,records=records,operator_reruns=0))
    r.cap();ok=True;print('Exact archived inputs/all normalized QKV binding proof passes',records,flush=True)
except BaseException as ex:
    error=repr(ex);traceback.print_exc();r.save(r.BASE/'FAILURE_audit.json',dict(error=error,**r.usage()))
finally:
    signal.alarm(0);r.save(r.SUP/'audit/child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**r.usage()))
if not ok:sys.exit(1)
