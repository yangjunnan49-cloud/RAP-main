"""DMF/LMB delivery figures and finite close; no solver or model calls."""
import time
START=time.monotonic()
import json
import hashlib
import resource
import sys
from pathlib import Path
from datetime import datetime,timezone
MAIN=Path(__file__).resolve().parents[2]
ROOT=MAIN/'docs/maintenance/2026-10-20'
BASE=ROOT/'weekly-system-handoff-01'
DMF=ROOT/'direct-matching-factors-01'; LMB=ROOT/'e0-local-map-bundle-01'
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def write(p,t):
    with Path(p).open('x',encoding='utf-8') as f:f.write(t)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def costs(folder):
    rows=[]
    for p in sorted((folder/'supervision').glob('*/child_exit.json')):
        n=read(p); w=read(p.with_name('exit.json')) if p.with_name('exit.json').exists() else {}
        rows.append(dict(stage=p.parent.name,success=n['success'],error=n.get('error'),native_seconds=n['wall_seconds'],
            enclosing_seconds=max(n['wall_seconds'],w.get('wall_seconds',0)),peak_RSS_bytes=n['peak_RSS_bytes'],windows_exit=w.get('exit_code')))
    return dict(stages=rows,enclosing_seconds=sum(r['enclosing_seconds'] for r in rows),peak_RSS_bytes=max((r['peak_RSS_bytes'] for r in rows),default=0),
        artifact_bytes_before_closing_records=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()),GPU_calls=0,observer_and_native_process_tree_full_peak='UNKNOWN')
def plot():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sys.path.insert(0,str(MAIN/'scripts/maintenance')); import validate_scan_level_graph as v
    assert read(DMF/'metric_validation.json')['passed']; result=read(DMF/'results.json')
    fig,axes=plt.subplots(2,2,figsize=(12,9)); colors=dict(B='#64748b',Q='#e49c26',D='#176b96',M='#16835c')
    for col,s in enumerate(('00','05')):
        gt=v.load(v.DATA/f'poses/{s}.txt'); tr=v.calibration(s); gt=np.linalg.inv(tr)@gt@tr; y=gt[:,:3,3]
        ax=axes[0,col]; ax.plot(y[:,0],y[:,1],color='black',lw=1,label='Reference')
        arms=['B','Q','D']; values={a:result['rows'][s][a]['ate'] for a in arms}
        if (LMB/'validation.json').exists() and read(LMB/'validation.json')['passed']:
            arms.append('M'); values['M']=read(LMB/'results.json')['rows'][s]['M']['ate']
        for a in arms:
            t=np.load((LMB if a=='M' else DMF)/f'bank/{s}/{a}.npy'); x=t[:,:3,3]
            xx=x-x.mean(0); yy=y-y.mean(0); u,_,vt=np.linalg.svd(xx.T@yy); d=np.diag([1.,1.,np.linalg.det(vt.T@u.T)]); rot=vt.T@d@u.T; aligned=xx@rot.T+y.mean(0)
            ax.plot(aligned[:,0],aligned[:,1],color=colors[a],lw=.85,label=a)
        ax.set_title(f'Sequence {s}: each trajectory rigidly aligned'); ax.axis('equal'); ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)'); ax.legend(frameon=False,ncol=3)
        bar=axes[1,col]; bars=bar.bar(arms,[values[a] for a in arms],color=[colors[a] for a in arms]); bar.bar_label(bars,fmt='%.3f',padding=3)
        bar.set_ylim(0,max(values.values())*1.2); bar.set_ylabel('Aligned LiDAR ATE (m), lower is better'); bar.set_title(f'Sequence {s}: validated saved metrics'); bar.grid(axis='y',alpha=.15)
    fig.suptitle('Fixed E0 system engineering screen | 2026-10-20\nB current RAP graph; Q frozen geometry; D direct geometry; M optional local-map bundle',fontsize=12)
    fig.tight_layout(rect=[0,0,1,.94]); fig.savefig(BASE/'system_comparison.png',dpi=170); plt.close(fig)
    save(BASE/'figure_sources.json',dict(utc=now(),DMF_results_sha256=sha(DMF/'results.json'),DMF_bank_seal_sha256=sha(DMF/'bank_seal.json'),
        optional_LMB_validation_sha256=sha(LMB/'validation.json') if (LMB/'validation.json').exists() else None,scope='Visualization of validated saved predictions/metrics; no solver/model'))
def close():
    assert read(DMF/'metric_validation.json')['passed']; result=read(DMF/'results.json'); bank=read(DMF/'bank_validation.json'); validation=read(DMF/'metric_validation.json')
    cr={'DMF':costs(DMF),'LMB':costs(LMB)}; save(BASE/'COSTS.json',cr)
    gate=result['gate']; state='PASS' if gate['passed'] else 'COMPLETE_NEGATIVE'; lines=[]
    save(DMF/'STATUS.json',dict(utc=now(),status=state,numerical_validation_passed=True,scientific_gate_passed=gate['passed'],latest_full_pipeline='2026-10-11'))
    if (DMF/'INCOMPLETE').exists(): (DMF/'INCOMPLETE').unlink()
    lmb_status='PREPARED_NOT_EXECUTED'
    if (LMB/'validation.json').exists():
        lmb_status='PASS' if read(LMB/'validation.json')['scientific_gate_passed'] else 'COMPLETE_NEGATIVE'
        if (LMB/'INCOMPLETE').exists(): (LMB/'INCOMPLETE').unlink()
    elif (LMB/'supervision').exists(): lmb_status='INCOMPLETE_SEE_PRESERVED_RECEIPTS'
    save(LMB/'STATUS.json',dict(utc=now(),status=lmb_status))
    save(BASE/'CLOSURE_SOURCES.json',dict(utc=now(),sources={str(p):sha(p) for p in [Path(__file__),MAIN/'scripts/maintenance/direct_matching_factors.py',MAIN/'scripts/maintenance/validate_direct_matching_factors.py',MAIN/'scripts/maintenance/e0_local_map_bundle.py']}))
    for s in ('00','05'):
        for a in ('B','Q','D'):
            row=result['rows'][s][a]; lines.append(f"| {s} | {a} | {row['ate']:.9f} | {row['ter']:.9f} | {row['rer']:.9f} |")
    failed=[k for k,v in gate['tests'].items() if not v]
    extra='The local-map alternative is prepared but has no executed efficacy result.\n'
    if (LMB/'validation.json').exists():
        lv=read(LMB/'validation.json'); lr=read(LMB/'results.json'); extra='LMB0 independent evaluation completed. Scientific conjunction: '+str(lv['scientific_gate_passed'])+'.\n\n'
        extra+='| Sequence | M ATE m | M ter % | M rer deg/100m |\n| --- | ---: | ---: | ---: |\n'
        for s in ('00','05'):
            z=lr['rows'][s]['M']; extra+=f"| {s} | {z['ate']:.9f} | {z['ter']:.9f} | {z['rer']:.9f} |\n"
    elif (LMB/'supervision').exists():
        extra='LMB0 is incomplete. Its executed stage receipts and any preserved failures are listed in COSTS.json. No accuracy result is inferred.\n'
    report=f'''# October20 system engineering advance

DMF0 status: **{state}**. The owner selected system metrics/deliverables and authorized continuation in the current five-hour window. This is a new fixed-E0 stored-observation graph comparison, not a new complete raw-frontend/model pipeline benchmark. The original research objective remains unresolved.

## What was decided and executed

The KISS archive comparison found different graph units (00/05:33/20 map nodes versus670/374 E0 keyframes), source-reset and weighting semantics, and no explicit raw-membership sidecar in the inspected exports. It does not identify the cause of the whole-system gap or permit a causal graph transplant. See ../direct-matching-factors-01/COMPONENT_DECISION.md.

DMF0 froze115 sources/inputs, passed synthetic and independent SciPy/brute-force derivatives, then generated both whole sequences on all24 admitted loops. B uses the existing pose constraints. Q compresses the declared physical cost once, retaining its linear term and constant. D rematches/relinearizes the same censored symmetric point-to-point cost in the joint graph. Initial Q/D objective, gradient and curvature agree. E0 motion, graph nodes, admissions, physical support and propagation are fixed. No old stopped family is reopened.

| Sequence | Arm | ATE m | ter % | rer deg/100m |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(lines)}

Failed prospective tests: {', '.join(failed) if failed else 'none'}.

A lower geometry objective is not a trajectory improvement. Only the frozen conjunction determines promotion. Any exact negative stops without point/radius/kernel/weight/iteration rescue. This result does not reject all direct factors or establish physical ground truth.

## Validation

The complete prediction bank sealed before numerical reference access. All initial and final loop matching objectives were reconstructed using independent brute-force queries. Initial directed-query count:{bank['independent_initial_directed_queries']}; maximum relative algebra discrepancy:{bank['maximum_relative_algebra_error']:.6g}. Separate Horn alignment and KITTI segment equations validate{validation['independent_segments']} segment records, maximum metric discrepancy{validation['maximum_metric_delta']:.6g}. Nonlinear optimizers and raw preprocessing are not independently reimplemented. Source/raw/cache identities and full frame membership limits are explicit in the protocols.

The first full-bank validator was deliberately interrupted after1002.0574736 enclosing seconds in repeated filesystem guards. Its original failure/source/receipt remain. Validation02 changed only guard frequency, passed a textual equivalence assertion for all neighbour mathematics, reused the sealed bank and completed in38.1853699 enclosing seconds. Both attempts and the guard diagnostic remain charged under the original1800s cap. See AMENDMENT_01 and VALIDATION02_FREEZE; no numerical tolerance or gate changed.

## Local-map alternative

{extra}
## Cost and interpretation

DMF measured enclosing stages:{cr['DMF']['enclosing_seconds']:.6f}s; maximum Linux child RSS:{cr['DMF']['peak_RSS_bytes']}bytes. LMB measured enclosing stages:{cr['LMB']['enclosing_seconds']:.6f}s; maximum participating Python RSS:{cr['LMB']['peak_RSS_bytes']}bytes. Nested native/parent clocks are not added. Dossier sizes and stage/exit details are in COSTS.json. Host observer/setup/process-tree full peaks remain unknown; no all-native memory certificate follows. The original sandbox null-cast headroom was invalid; the later real guard passed. All historical source, numerical and resource failures remain retained.

The latest complete raw-system benchmark remains October11 unless a later explicitly documented complete pipeline is executed. These00/05 results are exposed development evidence. RAP-specific increment, independent scenes/pretraining exclusion and physical reference authenticity are not supplied. No production/default/model/reference edit, installation, outreach, Git mutation, scheduler or goal-status change.

Account state is recorded separately in ACCOUNT_FINAL.json; a negative result or a reading below100% is not exhaustion. No automatic reset continuation.
'''
    write(BASE/'REPORT.md',report)
    entry=f'October20 owner-authorized system advance: DMF0 {state}; fixed E0/all24loops00/05 B/Q/D stored-graph screen independently validated. See docs/maintenance/2026-10-20/weekly-system-handoff-01/REPORT.md and COSTS.json. Instrumentation-only validator repair retained both attempts under original cap. Lower geometry cost is not efficacy; old stops/caps/seals and official references remain. LMB0 {lmb_status}; details and any retained failures in its own dossier. Latest full raw-system benchmark remainsOct11; original research goal unresolved. Account boundary is separate, no automatic reset continuation/outreach/Git mutation/goal status change.'
    p=MAIN/'AGENTS.md'; old=p.read_bytes(); cut=old.index(b'\n')+1; new=old[:cut]+b'\n'+entry.encode('utf-8')+b'\n'+old[cut:]; p.write_bytes(new)
    phase=ROOT/'PHASE_RECORD.md'; previous=phase.read_bytes(); phase.write_bytes(previous+('\n\n# Phase record — October20 system advance\n\n'+entry+'\n').encode('utf-8'))
    save(BASE/'HANDOFF_UPDATE_CHECKS.json',dict(utc=now(),old_AGENTS_sha256=hashlib.sha256(old).hexdigest(),new_AGENTS_sha256=sha(p),
        old_AGENTS_body_preserved=new[cut+len(b'\n'+entry.encode('utf-8')+b'\n'):]==old[cut:],old_phase_prefix_preserved=phase.read_bytes().startswith(previous)))
    # New delivery identities only; no historical seal is rewritten.
    for folder in (DMF,LMB):
        if folder==LMB and not (LMB/'freeze.json').exists(): continue
        target=folder/'DELIVERY_SEAL.json'
        save(target,dict(utc=now(),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p!=target}))
    save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),files={str(p.relative_to(BASE)):sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and 'supervision' not in p.parts and p.name!='DELIVERY_SEAL.json'}))
    print('Delivered and handoff updated',state,flush=True)
def run(stage):
    ok=False; err=None
    try:
        {'plot':plot,'close':close}[stage](); assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<2*2**30; ok=True
    except BaseException as e:
        err=repr(e); raise
    finally:
        save(BASE/'supervision'/stage/'child_exit.json',dict(utc=now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
if __name__=='__main__': run(sys.argv[1])
