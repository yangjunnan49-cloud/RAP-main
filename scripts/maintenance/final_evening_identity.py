"""Read-only evening identity/process/repository closure; stdlib only."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATE=ROOT/'docs/maintenance/2026-10-15';BASE=DATE/'continuation-handoff-08'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def path(s):
    if s.startswith('E:\\'):return Path('/mnt/e/'+s[3:].replace('\\','/'))
    return Path(s)
def save(name,obj):
    with (BASE/name).open('x') as f:json.dump(obj,f,indent=2)
files={};references=0
def add(name,row):
    global references
    p=path(name);r=dict(bytes=int(row['bytes']),sha256=row['sha256']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
    assert str(p) not in files or files[str(p)]==r
    files[str(p)]=r;references+=1
prior=read(DATE/'continuation-handoff-07/IDENTITY_CHECKS.json')
for p,r in prior['files'].items():add(p,r)
scopes={}
for folder in ('nonlocal-joint-connectivity-01','nonlocal-joint-comparison-01'):
    b=DATE/folder;f=read(b/'freeze.json');seal=read(b/'DELIVERY_SEAL.json')
    for p,r in f['files'].items():add(p,r)
    for p,r in seal['files'].items():add(str(b/p),r)
    add(str(b/'DELIVERY_SEAL.json'),dict(bytes=(b/'DELIVERY_SEAL.json').stat().st_size,sha256=sha(b/'DELIVERY_SEAL.json')))
    scopes[folder]=dict(frozen=len(f['files']),delivery_entries=seal['entries'],dossier_bytes=sum(p.stat().st_size for p in b.rglob('*') if p.is_file()))
for name in ('CPU_VARIANT_BINDING.json','INDEPENDENT_BINDING.json'):
    binding=read(DATE/'nonlocal-joint-comparison-01'/name)
    for p,r in binding['files'].items():add(str(ROOT/p),r)
oldseal=read(DATE/'continuation-handoff-07/DELIVERY_SEAL.json')
for r in oldseal['files']:add(str(DATE/'continuation-handoff-07'/r['path']),r)
markers=read(DATE/'continuation-handoff-06/IDENTITY_CHECKS.json')['retained_markers']
for name in markers:assert path(name).is_file() and str(path(name)) in files
repos={}
for label,p in (('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')):
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-c',f'safe.directory={p}','-C',str(p),*a],text=True).strip()
    repos[label]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==read(DATE/'nonlocal-joint-comparison-01/freeze.json')['repositories']
owned_names={'nonlocal_joint_connectivity.py','run_nonlocal_joint_connectivity.py','validate_nonlocal_joint_connectivity.py',
 'nonlocal_joint_comparison.py','nonlocal_joint_comparison_cpu02.py','run_nonlocal_joint_comparison.py','run_nonlocal_joint_comparison_cpu02.py',
 'validate_nonlocal_joint_comparison.py','independent_nonlocal_joint.py','run_independent_nonlocal_joint.py'}
census=dict(processes=0,readable_command_lines=0,argv=0,empty_command_lines=0,raced_departures=0,unreadable=0,scoped_owned_matches=[])
for p in Path('/proc').iterdir():
    if not p.name.isdecimal():continue
    census['processes']+=1
    try:raw=(p/'cmdline').read_bytes()
    except FileNotFoundError:census['raced_departures']+=1;continue
    except PermissionError:census['unreadable']+=1;continue
    args=[a.decode(errors='replace') for a in raw.split(b'\0') if a]
    if not args:census['empty_command_lines']+=1;continue
    census['readable_command_lines']+=1;census['argv']+=len(args)
    if any(Path(a).name in owned_names for a in args) and Path(args[0]).name.startswith('python'):
        census['scoped_owned_matches'].append(dict(pid=int(p.name),argv=args))
assert not census['scoped_owned_matches']
save('PROCESS_CENSUS_LINUX.json',dict(**census,scope='Exact listed NJC/NJE interpreter arguments only; no unrelated task absence claim'))
attempts=[]
for folder in scopes:
    for p in (DATE/folder/'supervision').glob('*/child_exit.json'):
        child=read(p);win=read(p.with_name('exit.json'));assert win['exit_code']==(0 if child['success'] else 1)
        attempts.append(dict(scope=folder,stage=p.parent.name,child=child,Windows=win))
assert len(attempts)==12 and sum(a['child']['success'] for a in attempts)==11
for n in ('run_nonlocal_joint_comparison_cpu02.py','nonlocal_joint_comparison_cpu02.py','independent_nonlocal_joint.py','run_independent_nonlocal_joint.py','final_evening_identity.py','run_evening_verification.py'):
    src=ROOT/'scripts/maintenance'/n;dest=BASE/'source_snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(src.read_bytes())
    add(str(src),dict(bytes=src.stat().st_size,sha256=sha(src)));add(str(dest),dict(bytes=dest.stat().st_size,sha256=sha(dest)))
result=dict(passed=True,unique_verified_paths=len(files),identity_references=references,files=files,scopes=scopes,
  prior737_identities=len(prior['files']),prior_handoff07_entries=len(oldseal['files']),inherited_markers=len(markers),repositories=repos,
  scientific_attempts=12,successes=11,retained_prestart_failures=1,child_seconds=sum(a['child']['wall_seconds'] for a in attempts),
  Windows_seconds=sum(a['Windows']['wall_seconds'] for a in attempts),attempts=attempts,model_fit_pose_network_calls_in_verification=0,
  all_native_GPU_peak_certified=False,ordinary_setup_RSS='UNKNOWN',observer_full_lifetime_peak='UNKNOWN')
save('IDENTITY_CHECKS.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('files','attempts','repositories')}),flush=True)
