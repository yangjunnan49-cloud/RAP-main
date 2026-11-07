"""NOC3 frozen CPU control conditioning experiment and delivery."""
import inspect
import json
import resource
import signal
import sys
import time
from pathlib import Path
import numpy as np
import scipy
import torch
import local_motion_common as c
import native_pose_fit as previous
import rigid_metric_control as m
import rigid_control_reference as ref

BASE=c.MAIN/'docs/maintenance/2026-10-10/rigid-control-conditioning-01'
START=None


def load(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k].copy() for k in z.files}
def usage():
    assert not torch.cuda.is_initialized(),'GPU forbidden'
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        GPU_used=False,artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()))
def ledger(): return c.read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
def cap():
    u=usage();assert sum(x['wall_seconds'] for x in ledger())+u['wall_seconds']<=600
    assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=64*2**20
def finish(stage,success=True,**kw):
    if success: cap()
    (BASE/'RESOURCE_LOG.json').write_text(json.dumps(ledger()+[dict(stage=stage,success=success,utc=c.now(),**usage(),**kw)],indent=2,allow_nan=False)+'\n')
def old_deliveries():
    folders=(previous.n.OLD,previous.n.BASE,previous.BASE,previous.BASE/'delivery-correction-01');counts=[]
    for folder,count in zip(folders,(103,188,53,5)):
        s=c.read(folder/'DELIVERY_SEAL.json');assert len(s['files'])==count
        for row in s['files']: assert c.sha(folder/row['path'])==row['sha256'],row['path']
        counts.append(count)
    return counts
def check():
    f=c.read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert c.sha(p)==h,p
    assert f['settings']==m.SETTINGS and f['cases']==list(m.CASES)
    assert f['runtime']==dict(torch=torch.__version__,numpy=np.__version__,scipy=scipy.__version__,threads=torch.get_num_threads())
    assert torch.get_num_threads()==1 and not torch.cuda.is_initialized()
    return f
def freeze():
    old_deliveries();f=previous.check();repos=previous.n.noc.git_state();assert repos==f['repositories']
    files=dict(f['files']);sources=[Path(__file__).with_name(name) for name in (
        'rigid_control_conditioning.py','rigid_metric_control.py','rigid_control_reference.py','validate_rigid_control_conditioning.py')]
    extra=sources+[BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',Path(inspect.getfile(torch.optim.LBFGS)),
        previous.BASE/'freeze.json',previous.BASE/'DELIVERY_SEAL.json',previous.BASE/'delivery-correction-01/DELIVERY_SEAL.json',
        previous.BASE/'bank/synthetic_fixture.npz',previous.BASE/'bank/control/fit.json',previous.BASE/'validation_control.json']
    for p in extra: files[str(p)]=c.sha(p)
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in sources: (snap/p.name).write_bytes(p.read_bytes())
    c.save(BASE/'freeze.json',dict(files=files,repositories=repos,cases=list(m.CASES),settings=m.SETTINGS,
        primary_cases=['SCALED_DIRECT','SCALED_DECODE'],gate=dict(t_m=.005,R_deg=.05,scaled_gradient_max=1e-5),
        runtime=dict(torch=torch.__version__,numpy=np.__version__,scipy=scipy.__version__,threads=1),
        limits=dict(wall_seconds=600,RSS_bytes=2*2**30,artifact_bytes=64*2**20,GPU_allowed=False)))
    (BASE/'INCOMPLETE').write_text('NOC3 frozen; prerequisites/controls/validation pending.\n')
    c.status(BASE,'frozen',status='AUTHORIZED_FROZEN');finish('freeze');print('NOC3 frozen',len(files),flush=True)
def preflight():
    check();source=previous.BASE/'bank/synthetic_fixture.npz';(BASE/'fixture.npz').write_bytes(source.read_bytes());z=load(BASE/'fixture.npz')
    probes={'zero':np.zeros((2,6)), 'probe':np.array([[.1,-.1,.05,.02,.01,-.015],[-.1,.05,.03,-.01,.02,.015]]), 'reference':m.physical_reference(z)}
    entries=[];arrays={};maximum_cost=maximum_grad=maximum_fd=maximum_pose=0
    for label,value in probes.items():
        p=torch.tensor(value,dtype=torch.float64,requires_grad=True);grads={};costs={}
        q=m.endpoints(z,p).detach().numpy();independent=ref.output(z,value)
        assert abs(q-independent).max()<1e-12
        T,shape=ref.decode(z,q);direct=ref.poses(value);pd=float(abs(T-direct).max());assert pd<1e-10;maximum_pose=max(maximum_pose,pd)
        reference_cost=ref.direct_cost(z,value);fd=ref.gradient(z,value)
        for route in ('DIRECT','DECODE'):
            cost=m.cost(z,p,route);g=torch.autograd.grad(cost,p)[0].detach().numpy();costs[route]=float(cost.detach());grads[route]=g
            cd=abs(costs[route]-reference_cost);assert cd<1e-7;maximum_cost=max(maximum_cost,cd)
            d=float(abs(g-fd).max());assert np.all(abs(g-fd)<=np.maximum(5e-5,abs(g)*1e-6));maximum_fd=max(maximum_fd,d)
            arrays[f'{label}_{route}_gradient']=g
        gd=float(abs(grads['DIRECT']-grads['DECODE']).max());assert gd<=max(1e-6,abs(grads['DIRECT']).max()*1e-7);maximum_grad=max(maximum_grad,gd)
        if label=='reference': assert max(costs.values())<1e-8
        entries.append(dict(probe=label,costs=costs,FD_max_delta=float(max(abs(grads[a]-fd).max() for a in grads)),route_gradient_max_delta=gd))
        arrays[label+'_parameters']=value
    hessians={};summary=[]
    for name in m.CASES:
        d=m.units(name);route=name.split('_')[1]
        H=torch.autograd.functional.hessian(lambda u:m.cost(z,u*d,route),torch.zeros(2,6,dtype=torch.float64)).reshape(12,12).detach().numpy()
        assert np.isfinite(H).all() and abs(H-H.T).max()<1e-5
        e=np.linalg.eigvalsh((H+H.T)/2);assert e.min()>1e-8
        hessians[name]=H;arrays[name+'_hessian']=H
        summary.append(dict(case=name,eigenvalues=e.tolist(),condition_number=float(e.max()/e.min())))
    hd=[]
    for mode in ('RAW','SCALED'):
        a=hessians[mode+'_DIRECT'];d=float(abs(a-hessians[mode+'_DECODE']).max());assert d<=max(1e-5,abs(a).max()*1e-7);hd.append(d)
    np.savez(BASE/'preflight.npz',**arrays)
    c.save(BASE/'preflight.json',dict(passed=True,probes=entries,hessian_summary=summary,route_hessian_max_deltas=hd,
        max_cost_delta=maximum_cost,max_gradient_delta=maximum_grad,max_FD_delta=maximum_fd,max_Horn_pose_delta=maximum_pose))
    c.save(BASE/'preflight_seal.json',dict(files={name:c.sha(BASE/name) for name in ('fixture.npz','preflight.npz','preflight.json')}))
    finish('preflight');print('NOC3 preflight passed',summary,flush=True)
def preflight_check():
    s=c.read(BASE/'preflight_seal.json')
    for p,h in s['files'].items(): assert c.sha(BASE/p)==h,p
    assert c.read(BASE/'preflight.json')['passed']
def run():
    check();preflight_check();z=load(BASE/'fixture.npz');bank=BASE/'bank';bank.mkdir();summary=[]
    for name in m.CASES:
        folder=bank/name;folder.mkdir();a,state=m.solve(z,name,cap)
        np.savez(folder/'trace.npz',**a);c.save(folder/'optimizer_state.json',state)
        assert state['n_iter']<=20 and state['func_evals']==len(a['trace_cost'])<=40
        c.save(folder/'seal.json',dict(files={p.name:c.sha(p) for p in folder.iterdir() if p.is_file()}))
        summary.append(dict(case=name,iterations=state['n_iter'],closure_evaluations=state['func_evals']))
        print('NOC3',name,'accepted iterations',state['n_iter'],'closures',state['func_evals'],flush=True);cap()
    c.save(BASE/'bank.json',dict(conditions=summary,controls=4,no_native_or_model_calls=True))
    c.save(BASE/'bank_seal.json',dict(files={str(p.relative_to(BASE)):c.sha(p) for p in sorted(bank.rglob('*')) if p.is_file()},
        manifest_sha256=c.sha(BASE/'bank.json'),freeze_sha256=c.sha(BASE/'freeze.json')))
    finish('four_controls');print('NOC3 all controls sealed',flush=True)
def bank_check():
    s=c.read(BASE/'bank_seal.json');assert c.sha(BASE/'bank.json')==s['manifest_sha256'] and c.sha(BASE/'freeze.json')==s['freeze_sha256']
    for p,h in s['files'].items(): assert c.sha(BASE/p)==h,p
def evaluate():
    check();bank_check();z=load(BASE/'fixture.npz');records=[]
    for name in m.CASES:
        a=load(BASE/'bank'/name/'trace.npz');P,shape=ref.decode(z,a['final_output']);err=ref.metrics(z,P)
        R=a['final_rotations'];proper=float(abs(R.transpose(0,2,1)@R-np.eye(3)).max())<1e-10 and abs(np.linalg.det(R)-1).max()<1e-10
        scaled_grad=a['final_gradient']/a['units']*m.units('SCALED_DIRECT').numpy();stationarity=float(abs(scaled_grad).max())
        tests=dict(pose=all(e['t_m']<=.005 and e['R_deg']<=.05 for e in err),stationarity=stationarity<=1e-5,
            proper=bool(proper),finite_cost=bool(np.isfinite(a['final_cost'])))
        state=c.read(BASE/'bank'/name/'optimizer_state.json')
        records.append(dict(case=name,errors=err,final_cost=float(a['final_cost']),scaled_gradient_max=stationarity,
            tests=tests,passed=all(tests.values()),iterations=state['n_iter'],closure_evaluations=state['func_evals']))
    passed=all(x['passed'] for x in records if x['case'].startswith('SCALED'))
    decision='FIXED_ANCHOR_METRIC_CONTROL_FEASIBLE' if passed else 'NO_FIXED_ANCHOR_METRIC_CONTROL_CONJUNCTION'
    c.save(BASE/'results.json',dict(records=records,primary_conjunction=passed,decision=decision))
    c.save(BASE/'results_seal.json',dict(results_sha256=c.sha(BASE/'results.json'),bank_seal_sha256=c.sha(BASE/'bank_seal.json')))
    finish('evaluate');print('NOC3 evaluated',decision,records,flush=True)
def close():
    f=check();old=old_deliveries();preflight_check();bank_check();v=c.read(BASE/'validation.json');assert v['passed']
    vs=c.read(BASE/'validation_seal.json');assert c.sha(BASE/'validation.json')==vs['validation_sha256']
    assert c.sha(BASE/'results_seal.json')==vs['results_seal_sha256']
    result=c.read(BASE/'results.json');rs=c.read(BASE/'results_seal.json');assert c.sha(BASE/'results.json')==rs['results_sha256']
    repos=previous.n.noc.git_state();assert repos==f['repositories'];rows=ledger();assert all(x['success'] for x in rows)
    wall=sum(x['wall_seconds'] for x in rows);rss=max(x['peak_RSS_bytes'] for x in rows);assert wall<=600 and rss<=2*2**30
    c.save(BASE/'RESOURCE_AUDIT.json',dict(stages=rows,combined_recorded_wall_seconds=wall,peak_RSS_bytes=rss,
        all_attempted_RSS_captured=True,all_failed_stages_counted=True,GPU_used=False,limits=f['limits'],caps_pass=True,
        exclusions=['module imports','WSL startup','design/docs','final identity/seal bookkeeping'],production_latency=False))
    c.save(BASE/'REPOSITORY_STATE.json',dict(repositories=repos,heads_branches_tracked_sets_preserved=True,no_commit_or_sync=True))
    c.save(BASE/'CHECKS.json',dict(freeze_entries=len(f['files']),old_delivery_entries_unchanged=old,
        RAP_checkpoint_hashed_not_loaded=True,no_GPU_model_native_or_real_calls=True,validation=v))
    table=[]
    for row in result['records']:
        e=row['errors'];table.append(f"| {row['case']} | {row['iterations']} / {row['closure_evaluations']} | {e[0]['t_m']:.9g} / {e[1]['t_m']:.9g} | {e[0]['R_deg']:.9g} / {e[1]['R_deg']:.9g} | {row['scaled_gradient_max']:.9g} | {row['passed']} |")
    h=c.read(BASE/'preflight.json')['hessian_summary'];htext='; '.join(f"{x['case']} {x['condition_number']:.6f}" for x in h)
    status='VALIDATED_CONTROL_DIAGNOSTIC_COMPLETE';decision=result['decision']
    report=f'''# NOC3: fixed-anchor rigid-control feasibility

{status}; decision **{decision}**. Owner said "请继续推进下一步". Four predeclared CPU float64 controls completed and independently checked. Primary scaled DIRECT/DECODE conjunction: **{result['primary_conjunction']}**. This is supervised known-transform control feasibility, not RAP fitting or a pose-estimation/system performance candidate.

## Executed controls

Same NOC2 three1000-point synthetic fixture. Descriptors/noises are unused. Anchor pose identity, twelve physical translation(m)/rotation-vector(rad) parameters, all initialized zero. Proper rotation is matrix_exp(skew). DIRECT applies NOC2's same metric/chordal loss to the parameters; DECODE constructs measured-coordinate rigid outputs and runs the unchanged NOC2 SVD loss. SCALED uses fixed .05m/.2deg unit preconditioning; RAW uses physical solver coordinates. Each condition gets one fixed L-BFGS invocation, max20 iterations/max40 closure calls/strong-Wolfe, no clipping or weight decay. Trials are retained; final accepted state defines the gate, no best-step/arm fallback.

| Condition | Iterations / closures | Final t part1/2(m) | Final R part1/2(deg) | Scaled gradient max | Full condition |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(table)}

Both SCALED conditions must pass t<=.005m/R<=.05deg on both moving parts, properness, finite loss and scaled-variable gradient<=1e-5. RAW cases are fixed descriptive comparators. Hessian condition numbers at identity: {htext}. Unit preconditioning changes solver coordinates; identity/reference/observations and objective are fixed. Relative cost routes' value/gradient/Hessian agreement is numerical evidence for this exact smooth rigid family, not every neural output or fp16 gradient.

## Audit and limits

Zero/probe/reference representability, anchor/properness, all12 physical gradients at each of three probes and12x12 Hessians are retained in preflight. Independent scipy rotation and Horn quaternion decode reconstruct every trial/final pose/output/cost; all12 gradients at every trial are compared with independent central differences. Full optimization replay reproduces all four traces, accepted outputs and optimizer states exactly using the same frozen source/torch optimizer. This is deterministic full replay, not an independently implemented L-BFGS algorithm. Max independent cost {v['max_cost_delta']:.3g}, gradient {v['max_gradient_FD_delta']:.3g}, Horn pose {v['max_pose_delta']:.3g}; optimizer trace replay {v['replay_max_delta']:.3g}. No model, GPU or native fitting/inference, descriptor extraction, real/nearby windows or new prediction census. Optimization uses reference supervision; this is a numerical control and cannot establish physical accuracy or generalization.

NOC2 affine final20.442/19.929mm remains a fixed-budget prerequisite stop. This round changes control family, gauge, precision, optimizer and solver-unit preconditioning; it cannot assign NOC2's failure uniquely to one of those changes. Comparisons within these four conditions address scaling and decoding only under this new fixed family/solver. Passing cannot retroactively amend NOC2 or prove an adapted RAP sampler converges. No rates/steps/init/gate/window rescue.

## Resources and preservation

{len(rows)} recorded successful stages total{wall:.6f}s, peak RSS{rss/2**30:.6f}GiB;600s/2GiB/64MiB CPU-only caps pass, all attempted RSS captured. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Artifact bytes finalized in DELIVERY_SEAL. No failed execution stage or implementation repair.

{len(f['files'])} source/input freeze entries. NOC0/NOC1/NOC2 original/corrected delivery counts{old} unchanged. Original model/config/checkpoint and sibling helpers retained; both HEADs/branches/two and nine tracked dirty sets preserved. Only isolated maintenance/docs and mutable handoffs. No model/checkpoint load, acquisition/install, production/default/backbone-source/manuscript edit, official metric/reference replacement, trajectory, commit or Git sync. Old stops/seals/physical/reference/time/site/checkpoint unknowns persist. Conventional proper geometry/L-BFGS credited, no original mechanism or system gain.
'''
    (BASE/'REPORT.md').write_text(report)
    plan=('The metric fixed-anchor rigid controls and both loss routes pass the prospective feasibility conjunction. Next DESIGN_ONLY: a distinct tiny same-capacity native velocity-versus-pose comparison with zero-update fp16 gradient/clipping/parameter-step preflight and fresh-noise gates, reset from frozen original parameters. Preserve NOC2 as stopped; do not resume its affine/AdamW gate or infer that these CPU pose parameters transfer optimizer feasibility to443904 neural parameters. Primary actual unmodified five-step sampler outcomes remain mandatory, rather than low first-endpoint loss. A concrete new optimizer/gradient-scale/resource scope must be frozen before updates; no such native fit/protocol is executed/frozen here.' if result['primary_conjunction'] else
        'The fixed scaled rigid-control conjunction fails. Stop this exact four-condition control/solver construction, retain all routes and trials, and review independent gradients/curvature/accepted-state stationarity before any native fitting. No step/rate/init/threshold rescue or real/nearby expansion; any distinct design requires new prospective scope.')
    (BASE/'NEXT_ROUND_PLAN.md').write_text('# Next decision after NOC3\n\n'+plan+'\n')
    (BASE/'HANDOFF.md').write_text(f'# NOC3 handoff\n\n{status}; {decision}. Read REPORT/PROTOCOL/OWNER_SCOPE/NEXT_ROUND_PLAN/STATUS/CHECKS/RESOURCE_AUDIT/REPOSITORY_STATE/DELIVERY_SEAL, freeze/source_snapshot/fixture/preflight/seal/four-control bank/seal/results/seal/validation/seal. Independent geometry/FD and full deterministic shared-source L-BFGS replay; no native or model call. Next native proposal is design only. NOC2 stop and all historical identities remain.\n')
    (BASE/'INCOMPLETE').unlink();c.status(BASE,'complete',status=status,decision=decision,primary_conjunction=result['primary_conjunction'],native_updates=0,model_calls=0)
    size=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file());assert size<=64*2**20
    entries=[dict(path=str(p.relative_to(BASE)),sha256=c.sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
    c.save(BASE/'DELIVERY_SEAL.json',dict(status=status,decision=decision,files=entries,artifact_bytes_before_seal=size,recorded_wall_seconds=wall,caps_pass=True))
    print('NOC3 CLOSED',decision,'entries',len(entries),'wall',wall,'bytes',size,flush=True)


if __name__=='__main__':
    START=time.monotonic();stage=sys.argv[1]
    def alarm(signum,frame): raise TimeoutError('NOC3 remaining combined wall exhausted')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(max(1,int(600-sum(x['wall_seconds'] for x in ledger()))))
    try: {'freeze':freeze,'preflight':preflight,'run':run,'evaluate':evaluate,'close':close}[stage]()
    except Exception as ex:
        if stage!='close':
            finish(stage,False,error=repr(ex));c.save(BASE/f'FAILURE_{stage}.json',dict(error=repr(ex),**usage()));c.status(BASE,'failure',status='INCOMPLETE',error=repr(ex))
        raise
    finally: signal.alarm(0)
