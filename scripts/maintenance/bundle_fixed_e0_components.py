"""Final source-equivalent component bundle and ledger supplement."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,hashlib,json,zipfile
from pathlib import Path
import finalize_weekly_supplement as f
r=f.r;BASE=f.BASE;AD=BASE.parent/'e0-odometry-adapter-component-01'
def run():
    used=sum(max([r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0]) for d in (BASE/'supervision').glob('*') if d.is_dir())
    used+=1.1554576+r.read(BASE/'WINDOWS_SUPPLEMENT_CHECKS.json')['wall_seconds'];left=300-used;assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original delivery cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        for p,h in r.read(AD/'FREEZE.json')['files'].items():assert r.sha(p)==h
        assert r.read(AD/'INTERFACE_CHECKS.json')['passed']
        n=r.read(AD/'supervision/adapter_portability/child_exit.json');w=r.read(AD/'supervision/adapter_portability/exit.json');assert n['success'] and w['exit_code']==0
        old=r.read(BASE/'COST_SUPPLEMENT.json')['LMB_total_seconds'];charged=max(n['wall_seconds'],w['wall_seconds']);total=old+charged;assert total<=1800
        r.save(BASE/'COST_FINAL_SUPPLEMENT.json',dict(utc=r.now(),prior_LMB_total_seconds=old,adapter_portability_enclosing_seconds=charged,LMB_total_seconds=total,
            original_LMB_cap_seconds=1800,LMB_remaining_seconds=1800-total,adapter_peak_RSS_bytes=n['peak_RSS_bytes'],GPU_calls=0,new_accuracy_metrics=0,
            combined_scientific_dossier_bytes=sum(p.stat().st_size for b in (f.x.OLD,f.x.BASE,f.CAP,AD) for p in b.rglob('*') if p.is_file())))
        assert r.read(BASE/'COST_FINAL_SUPPLEMENT.json')['combined_scientific_dossier_bytes']<=128*2**20
        r.save(AD/'STATUS.json',dict(utc=r.now(),status='COMPLETE_EXACT_CLASS_PORTABILITY_ONLY',AST_class_exact=True,native_interface_passed=True,new_accuracy_metrics=False))
        r.save(AD/'DELIVERY_SEAL.json',dict(utc=r.now(),files={str(p.relative_to(AD)):r.sha(p) for p in AD.rglob('*') if p.is_file() and p.name!='DELIVERY_SEAL.json'}))
        entries={}
        with zipfile.ZipFile(BASE/'anchor_fine_component_complete_20261020.zip') as z:
            for name in z.namelist():entries['anchor_component/'+name]=z.read(name)
        entries['fixed_odometry.py']=(AD/'fixed_odometry.py').read_bytes();entries['README.md']=(BASE/'INTEGRATION_COMPONENTS.md').read_bytes()
        for name in ('FREEZE.json','INTERFACE_CHECKS.json','STATUS.json','README.md','DELIVERY_SEAL.json'):entries['adapter_proof/'+name]=(AD/name).read_bytes()
        for p in (AD/'supervision').rglob('*'):
            if p.is_file():entries['adapter_proof/'+str(p.relative_to(AD))]=p.read_bytes()
        # The parent adapter seal names fixed_odometry.py too: include its original relative placement in its proof directory.
        entries['adapter_proof/fixed_odometry.py']=(AD/'fixed_odometry.py').read_bytes()
        entries['BUNDLE_SHA256.json']=json.dumps(dict(files={p:hashlib.sha256(b).hexdigest() for p,b in entries.items()}),indent=2).encode()
        zp=BASE/'fixed_E0_integration_components_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,body in entries.items():z.writestr(name,body)
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for name,body in entries.items():assert z.read(name)==body
        paths=[zp,BASE/'COST_FINAL_SUPPLEMENT.json',BASE/'INTEGRATION_COMPONENTS.md',AD/'DELIVERY_SEAL.json',Path(__file__)]
        r.save(BASE/'INTEGRATION_BUNDLE_SEAL.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},ZIP_members_verified=len(entries),prior_supplement_seals_unchanged=True))
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=64*2**20
        print('Integration bundle verified',len(entries),'members; LMB total',total,'remaining',1800-total,flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:
        signal.alarm(0);r.save(BASE/'supervision/bundle_components/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='bundle_components';run()
