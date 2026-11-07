"""Descriptive saved-scalar decomposition for the next decision; no new trial."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parents[2]/'docs/maintenance/2026-10-20/weekly-system-handoff-01'
SRC=BASE.parent/'e0-local-map-six-01/results.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def run():
    used=0.
    for d in (BASE/'supervision').glob('*'):
        if d.is_dir():used+=max([read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0])
    if (BASE/'WINDOWS_DELIVERY_CHECKS.json').exists():used+=read(BASE/'WINDOWS_DELIVERY_CHECKS.json')['wall_seconds']
    left=300-used;assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original delivery cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        source=read(SRC);assert source['independent_validation_passed'];rows=source['rows'];groups={};contributions={};total=sum(z['B']['ate']-z['G']['ate'] for z in rows.values())
        for name,ids in [('original_targets',['00','05']),('remaining_four',['06','07','09','10']),('all_six',list(rows))]:
            means={a:{k:sum(rows[s][a][k] for s in ids)/len(ids) for k in ('ate','ter','rer')} for a in ('B','G','KISS')}
            groups[name]=dict(sequences=ids,means=means,G_ATE_gain_vs_B_pct=(1-means['G']['ate']/means['B']['ate'])*100,G_ATE_gain_vs_KISS_pct=(1-means['G']['ate']/means['KISS']['ate'])*100)
        for s,z in rows.items():
            delta=z['B']['ate']-z['G']['ate'];contributions[s]=dict(B_minus_G_ATE_m=delta,share_of_signed_total_pct=delta/total*100,G_minus_B_ter_pp=z['G']['ter']-z['B']['ter'])
        assert abs(sum(p['share_of_signed_total_pct'] for p in contributions.values())-100)<=1e-10
        assert all(abs(groups['all_six']['means'][a][k]-source['gate']['means'][a][k])<=1e-12 for a in ('B','G','KISS') for k in ('ate','ter','rer'))
        save(BASE/'STRATEGY_ANALYSIS.json',dict(descriptive_only=True,source_result_sha256=sha(SRC),sources={str(p):sha(p) for p in [Path(__file__),BASE/'STRATEGY_ANALYSIS_SCOPE.md']},groups=groups,contributions=contributions,new_trial_or_gate=False,primary_gate_unchanged=source['gate']))
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;ok=True
        print(json.dumps(dict(groups=groups,contributions=contributions)),flush=True)
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:
        signal.alarm(0);save(BASE/'supervision/strategy_analysis/child_exit.json',dict(success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='strategy_analysis';run()
