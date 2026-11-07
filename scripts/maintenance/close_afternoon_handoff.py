"""Afternoon source identity/available-evidence handoff; standard library, no replay."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATE=ROOT/'docs/maintenance/2026-10-13';BASE=DATE/'continuation-handoff-02';START=time.monotonic()
def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
latest=read(DATE/'shadow-conditioned-fit-pilot-01/freeze.json');assert len(latest['files'])==1312;identities=dict(latest['files']);refs=0;dossiers=[];children=[]
for name,filename,count in [('activated-adapter-derivatives-01','DELIVERY_SEAL.json',149),('shadow-sampler-extraction-01','DELIVERY_SEAL.json',97),('shadow-conditioned-fit-pilot-01','AVAILABLE_DELIVERY_SEAL.json',576)]:
    folder=DATE/name;seal=read(folder/filename);assert len(seal['files'])==count
    for x in seal['files']:
        q=(folder/x['path'].replace(chr(92),'/')).resolve();assert folder.resolve() in q.parents and sha(q)==x['sha256'];identities[str(q)]=x['sha256'];refs+=1
    identities[str(folder/filename)]=sha(folder/filename);dossiers.append(dict(name=name,seal=filename,entries=count,status=read(folder/'STATUS.json')))
    for q in (folder/'supervision').glob('*/child_exit.json'):
        child=read(q);host=read(q.parent/'exit.json');assert child['full_resource_capture'] and host['exit_code']==(0 if child['success'] else 1)
        children.append(dict(folder=name,stage=q.parent.name,success=child['success'],seconds=child['wall_seconds'],host_exit=host['exit_code']))
assert refs==822 and len(children)==13 and sum(x['success'] for x in children)==12
for q,h in identities.items():assert sha(q)==h,q
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==latest['repositories'] and len(repos['main']['tracked_status'])==2 and len(repos['slam']['tracked_status'])==9
for q in [DATE/'shadow-conditioned-fit-pilot-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert q.exists()
assert not (DATE/'shadow-conditioned-fit-pilot-01/prediction_seal.json').exists() and not (DATE/'shadow-conditioned-fit-pilot-01/results.json').exists()
snapshot=BASE/'source_snapshot';snapshot.mkdir()
for q in (ROOT/'AGENTS.md',DATE/'PHASE_RECORD.md',Path(__file__)):(snapshot/q.name).write_bytes(q.read_bytes())
save(BASE/'IDENTITY_CHECKS.json',dict(passed=True,latest_frozen_identities=1312,unique_frozen_plus_available_paths=len(identities),available_delivery_references=refs,files=identities,repositories=repos,original_and_new_INCOMPLETE_markers_preserved=True,no_all_history_replay=True))
save(BASE/'CHECKS.json',dict(passed=True,dossiers=dossiers,afternoon_children=children,afternoon_children_count=13,afternoon_success_count=12,retained_artifact_failure_count=1,afternoon_scientific_seconds=sum(x['seconds'] for x in children),actual_retained_shadow_updates=40,optimizer_API_calls=0,HFIT_comparison_INCOMPLETE=True,no_heldout_noise_metrics=True,all_task_scientific_children_exited=True,scientific_replay=False))
save(BASE/'STATUS.json',dict(utc=now(),status='READ_ONLY_AFTERNOON_STOP_HANDOFF_COMPLETE',ADR0_SAR0_complete=True,HFIT0='INCOMPLETE_ARTIFACT_CAP',next='DESIGN_ONLY_LOSSLESS_STORAGE',real_system_expansion_admitted=False,commit_or_sync=False))
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_neural_or_numerical_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,setup_RSS_unknown=True))
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()];save(BASE/'DELIVERY_SEAL.json',dict(status='READ_ONLY_AFTERNOON_STOP_HANDOFF_COMPLETE',files=files,entries=len(files)))
print(json.dumps(dict(status='READ_ONLY_AFTERNOON_STOP_HANDOFF_COMPLETE',unique_identity_paths=len(identities),available_delivery_references=refs,scientific_children=13,scientific_seconds=sum(x['seconds'] for x in children),handoff_deliveries=len(files)),indent=2))
