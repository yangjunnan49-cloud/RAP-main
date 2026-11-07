"""Independent read-only closure identities and repository/process metadata."""
import hashlib, json, pathlib, subprocess, time, resource
root=pathlib.Path(__file__).resolve().parents[2]
today=root/'docs/maintenance/2026-10-16'
base=today/'continuation-handoff-09'
start=time.monotonic()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(65536): h.update(b)
    return h.hexdigest()
counts={}
for scope in ('regx-reference-package-01','regx-reference-code-01','ray-consistency-ranking-01'):
    folder=today/scope
    seal=json.loads((folder/'DELIVERY_SEAL.json').read_text(encoding='utf-8-sig'))
    for name,item in seal['files'].items():
        p=folder/name
        assert p.stat().st_size==item['bytes'] and digest(p)==item['sha256'],str(p)
    assert len(seal['files'])==seal['entries']
    counts[scope]=seal['entries']
sibling=root.parent/'RAP-SLAM'
def git(*args): return subprocess.check_output(['git','-c','core.safecrlf=false','-C',str(sibling),*args],text=True).strip()
repo=dict(HEAD=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_dirty=git('diff','--name-only').splitlines())
assert repo['HEAD']=='6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6'
assert repo['branch']=='codex/e0-f1-20260926'
assert set(repo['tracked_dirty'])=={'rap_slam/'+x+'.py' for x in ('loop_closure','odometry','pose_graph','rap_backend','real_dataset')}|{'scripts/'+x+'.py' for x in ('build_s1_features','eval_map_consistency','eval_paper_metrics','run_pipeline')}
names={'acquire_regx_reference_package.ps1','acquire_regx_reference_code.ps1','regx_package_native_control.ps1','regx_reference_code_control.ps1','validate_regx_reference_package.py','validate_regx_reference_package_layout02.py','audit_regx_reference_code.py'}
matches=[];unreadable=[];processes=0;argv=0
for p in pathlib.Path('/proc').iterdir():
    if not p.name.isdigit():continue
    processes+=1
    try: args=[s.decode(errors='replace') for s in (p/'cmdline').read_bytes().split(b'\0') if s]
    except (OSError,PermissionError):unreadable.append(p.name);continue
    argv+=len(args)
    if any(pathlib.PurePath(a).name in names for a in args):matches.append(p.name)
assert not matches
result=dict(independent_seals_match=counts,sibling_repository=repo,scoped_worker_pids=matches,
            Linux_processes=processes,argv_checked=argv,unreadable_pids=unreadable,
            scope='exact script argument basenames; no unrelated-task absence claim',
            bookkeeping_child_seconds=time.monotonic()-start,maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            new_network_model_pose_payload=False)
with (base/'LINUX_CHECKS.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
