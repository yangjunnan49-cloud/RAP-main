"""Seal portable component and strategic documentary supplements, immutable originals."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,zipfile
from pathlib import Path
import e0_local_map_six as x
r=x.r
BASE=r.MAIN/'docs/maintenance/2026-10-20/weekly-system-handoff-01'
CAP=BASE.parent/'e0-anchor-capsule-01'
def run():
    used=0.
    for d in (BASE/'supervision').glob('*'):
        if d.is_dir():used+=max([r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0])
    used+=r.read(BASE/'WINDOWS_DELIVERY_CHECKS.json')['wall_seconds'];left=300-used;assert left>1
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original delivery cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        proof=r.read(CAP/'EQUIVALENCE.json');assert proof['passed'] and proof['all_six'] and all(row['maximum_matrix_delta']==0 for row in proof['rows'].values())
        for p,h in r.read(CAP/'FREEZE.json')['files'].items():assert r.sha(p)==h,p
        n=r.read(CAP/'supervision/capsule_equivalence/child_exit.json');w=r.read(CAP/'supervision/capsule_equivalence/exit.json');assert n['success'] and w['exit_code']==0
        old=r.read(BASE/'COSTS.json')['LMB_shared_account']['enclosing_seconds'];charged=max(n['wall_seconds'],w['wall_seconds']);total=old+charged;assert total<=1800
        size=sum(p.stat().st_size for b in (x.OLD,x.BASE,CAP) for p in b.rglob('*') if p.is_file());assert size<=128*2**20
        r.save(BASE/'COST_SUPPLEMENT.json',dict(utc=r.now(),original_C0_or_other_scope_caps_untouched=True,original_LMB_seconds=old,capsule_enclosing_seconds=charged,
            LMB_total_seconds=total,original_LMB_cap_seconds=1800,LMB_remaining_seconds=1800-total,LMB_combined_dossier_bytes_before_seal=size,
            capsule_peak_RSS_bytes=n['peak_RSS_bytes'],capsule_peak_native_tree='UNKNOWN',GPU_calls=0,overlapping_native_clock_not_added=True,
            original_COSTS_sha256=r.sha(BASE/'COSTS.json'),original_delivery_seal_sha256=r.sha(BASE/'DELIVERY_SEAL.json')))
        r.save(CAP/'STATUS.json',dict(utc=r.now(),status='COMPLETE_PORTABILITY_EQUIVALENCE_ONLY',AST_math_equivalence=True,complete_six_CLI_matrix_max=0,original_safety_failures_unchanged=True))
        r.save(CAP/'DELIVERY_SEAL.json',dict(utc=r.now(),files={str(p.relative_to(CAP)):r.sha(p) for p in sorted(CAP.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json'}))
        zp=BASE/'anchor_fine_component_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(CAP.rglob('*')):
                if p.is_file() and 'supervision' not in p.parts:z.write(p,arcname=str(p.relative_to(CAP)))
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for p in sorted(CAP.rglob('*')):
                if p.is_file() and 'supervision' not in p.parts:assert z.read(str(p.relative_to(CAP)))==p.read_bytes()
        paths=[BASE/n for n in ('NEXT_STRATEGY_CN.md','STRATEGY_ANALYSIS.json','STRATEGY_ANALYSIS_SCOPE.md','POST_DELIVERY_INDEX.md','COST_SUPPLEMENT.json','WINDOWS_DELIVERY_CHECKS.json','WINDOWS_VERIFICATION_SEAL.json')]
        paths += [zp,CAP/'DELIVERY_SEAL.json',Path(__file__),Path(__file__).with_name('validate_anchor_capsule.py'),CAP/'anchor_fine.py']
        r.save(BASE/'FINAL_SUPPLEMENT_SEAL.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},original_delivery_seal_sha256=r.sha(BASE/'DELIVERY_SEAL.json'),ZIP_member_bytes_verified=True))
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=64*2**20
        print('Supplement sealed; LMB total',total,'remaining',1800-total,'component ZIP',zp.stat().st_size,flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(BASE/'FAILURE_finalize_supplement.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(BASE/'supervision/finalize_supplement/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='finalize_supplement';run()
