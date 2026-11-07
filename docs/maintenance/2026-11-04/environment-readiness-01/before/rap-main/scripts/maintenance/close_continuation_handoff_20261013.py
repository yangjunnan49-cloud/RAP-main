"""Final standard-library identity/source handoff; no numerical/model imports."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATE=ROOT/'docs/maintenance/2026-10-13';BASE=DATE/'continuation-handoff-01';START=time.monotonic()
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
names=[('native-backward-reproducibility-02',110),('attention-operator-diagnosis-01',55),('native-math-reproducibility-01',142),('native-precision-control-01',169),('native-double-tail-control-01',118),('native-shadow-step-control-01',70)]
latest=read(DATE/names[-1][0]/'freeze.json');assert len(latest['files'])==980;identities=dict(latest['files']);deliveries=[];children=[]
for name,count in names:
    folder=DATE/name;seal=read(folder/'DELIVERY_SEAL.json');assert len(seal['files'])==count and not (folder/'INCOMPLETE').exists()
    for x in seal['files']:
        p=(folder/x['path'].replace(chr(92),'/')).resolve();assert folder.resolve() in p.parents and sha(p)==x['sha256'];identities[str(p)]=x['sha256']
    identities[str(folder/'DELIVERY_SEAL.json')]=sha(folder/'DELIVERY_SEAL.json')
    status=read(folder/'STATUS.json');audit=read(folder/'RESOURCE_AUDIT.json');assert audit['passed']
    for childfile in sorted((folder/'supervision').glob('*/child_exit.json')):
        child=read(childfile);host=read(childfile.parent/'exit.json');assert child['full_resource_capture'] and host['exit_code']==(0 if child['success'] else 1)
        children.append(dict(folder=name,stage=childfile.parent.name,success=child['success'],seconds=child['wall_seconds'],Windows_exit=host['exit_code']))
    deliveries.append(dict(folder=name,entries=count,delivery_sha256=sha(folder/'DELIVERY_SEAL.json'),status=status,resource=audit))
for p,h in identities.items():assert sha(p)==h,p
repos={}
for name,p in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==latest['repositories'];assert len(repos['main']['tracked_status'])==2 and len(repos['slam']['tracked_status'])==9
markers=[ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE'];assert all(p.exists() for p in markers)
assert len(children)==27 and sum(x['success'] for x in children)==26
snapshot=BASE/'source_snapshot';snapshot.mkdir()
for p in (ROOT/'AGENTS.md',DATE/'PHASE_RECORD.md',Path(__file__)):(snapshot/p.name).write_bytes(p.read_bytes())
save(BASE/'IDENTITY_CHECKS.json',dict(utc=now(),passed=True,latest_frozen_identities=980,unique_frozen_plus_delivery_paths=len(identities),delivery_references=664,files=identities,repositories=repos,old_markers={str(p):sha(p) for p in markers},mutable_handoff_snapshots=True,all_history_replay=False))
save(BASE/'CHECKS.json',dict(utc=now(),passed=True,deliveries=deliveries,new_scientific_children=children,new_children_count=27,new_success_count=26,new_prefreeze_failure_count=1,
    new_scientific_seconds=sum(x['seconds'] for x in children),all_task_scientific_children_completed=True,retained_updates=0,fit_iterations=0,actual_signed_shadow_parameter_steps=8,optimizer_API_calls=0,
    original_native_fitting_INCOMPLETE=True,full_system_benchmark_unchanged=True,scientific_validation_replayed=False,all_history_caps_amended=False))
save(BASE/'STATUS.json',dict(utc=now(),status='READ_ONLY_CONTINUATION_IDENTITY_HANDOFF_COMPLETE',six_scientific_dossiers_complete=True,positive_scope='fixed-prefix double shadow derivative/descent witnesses only',next='DESIGN_ONLY',fit_admitted=False,commit_or_sync=False))
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_neural_or_numerical_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,setup_RSS_unknown=True))
files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(BASE.rglob('*')) if p.is_file()];save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status='READ_ONLY_CONTINUATION_IDENTITY_HANDOFF_COMPLETE',files=files,entries=len(files)))
print(json.dumps(dict(status='READ_ONLY_CONTINUATION_IDENTITY_HANDOFF_COMPLETE',unique_identity_paths=len(identities),delivery_references=664,new_scientific_children=27,new_scientific_seconds=sum(x['seconds'] for x in children),handoff_deliveries=len(files)),indent=2))
