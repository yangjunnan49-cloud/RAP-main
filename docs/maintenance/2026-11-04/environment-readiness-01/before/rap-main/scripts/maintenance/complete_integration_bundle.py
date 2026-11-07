"""Complete every parent-proof member in the integration ZIP; no numeric work."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,json,hashlib,zipfile
import finalize_weekly_supplement as f
r=f.r;BASE=f.BASE;AD=BASE.parent/'e0-odometry-adapter-component-01'
def run():
    used=sum(max([r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0]) for d in (BASE/'supervision').glob('*') if d.is_dir())
    used+=1.1554576+r.read(BASE/'WINDOWS_SUPPLEMENT_CHECKS.json')['wall_seconds'];left=300-used;assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original delivery cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        with zipfile.ZipFile(BASE/'fixed_E0_integration_components_20261020.zip') as z:entries={n:z.read(n) for n in z.namelist() if n!='BUNDLE_SHA256.json'}
        # Include all adapter proof members by its seal, rather than an incomplete hand-maintained list.
        seal=r.read(AD/'DELIVERY_SEAL.json')
        for p,h in seal['files'].items():assert r.sha(AD/p)==h;entries['adapter_proof/'+p]=(AD/p).read_bytes()
        for prefix in ('adapter_proof/','anchor_component/'):
            parent=json.loads(entries[prefix+'DELIVERY_SEAL.json'])
            for p,h in parent['files'].items():assert hashlib.sha256(entries[prefix+p]).hexdigest()==h
        entries['BUNDLE_SHA256.json']=json.dumps(dict(files={n:hashlib.sha256(b).hexdigest() for n,b in entries.items()}),indent=2).encode()
        zp=BASE/'fixed_E0_integration_components_complete_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for n,b in entries.items():z.writestr(n,b)
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for n,b in entries.items():assert z.read(n)==b
        r.save(BASE/'INTEGRATION_COMPLETE_CHECKS.json',dict(utc=r.now(),passed=True,files={str(zp):r.sha(zp),str(AD/'DELIVERY_SEAL.json'):r.sha(AD/'DELIVERY_SEAL.json')},
            archive_members=len(entries),both_parent_proof_seals_fully_present_and_verified=True,source_scope_note_added=True,previous_bundle_preserved=True,new_numeric_calls=0))
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=64*2**20
        print('Complete integration archive and both parent seals verified',len(entries),zp.stat().st_size,flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:
        signal.alarm(0);r.save(BASE/'supervision/bundle_complete/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='bundle_complete';run()
