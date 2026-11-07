"""Final read-only identity checks, no experiment computation or inference."""
import json,hashlib,importlib.util,subprocess
from pathlib import Path
M=Path('/mnt/e/githouse/RAP-main'); D=M/'docs/maintenance/2026-10-05'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''): h.update(part)
    return h.hexdigest()
count=0; experiments={}
for name in ['dense-propagation-screen-01','joint-loop-oracle-01','geotransformer-feasibility-01','online-geotransformer-01','online-geometry-consistency-01']:
    b=D/name; status=read(b/'STATUS.json'); assert status['stage']=='VALIDATED' and not (b/'INCOMPLETE').exists()
    artifact=read(b/'artifact_hashes.json'); files=artifact.get('files',artifact)
    for p,h in files.items(): assert sha(b/p)==h,(name,p); count+=1
    for f in b.glob('*freeze.json'):
        for p,h in read(f)['files'].items(): assert sha(p)==h,(name,p); count+=1
    experiments[name]=dict(stage=status['stage'],decision=status.get('decision'),validation_passed=read(b/'validation.json')['passed'])
# Preserve all directly reused old validated audit dependencies and banks.
old=M/'docs/maintenance/2026-09-29/system-opportunity-audit-01'
for p,h in read(old/'freeze.json')['files'].items(): assert sha(p)==h,p; count+=1
for p,h in read(old/'bank_seal.json')['files'].items(): assert sha(old/'attempt-01'/p)==h,p; count+=1
for dirname,folder,sealname in [('dense-propagation-screen-01','attempt-01','bank_seal.json'),('joint-loop-oracle-01','attempt-01','bank_seal.json'),('online-geotransformer-01','input-bank','input_seal.json'),('online-geotransformer-01','prediction-bank','bank_seal.json'),('online-geometry-consistency-01','evaluation-01','distance_seal.json')]:
    b=D/dirname; root=b/folder; seal=read(b/sealname)
    assert set(seal['files'])=={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    for p,h in seal['files'].items(): assert sha(root/p)==h,(dirname,p); count+=1
absence={n:importlib.util.find_spec(n) is None for n in ['easydict','einops','ipdb','geotransformer']}; assert all(absence.values())
heads={name:subprocess.check_output(['git','-c',f'safe.directory={M.parent/name}','-C',str(M.parent/name),'rev-parse','HEAD'],text=True).strip() for name in ['RAP-main','RAP-SLAM']}
assert heads['RAP-main'].startswith('4055d92') and heads['RAP-SLAM'].startswith('6d3f2d2')
record=dict(passed=True,identity_checks=count,experiments=experiments,global_packages_still_absent=absence,heads=heads,utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
with (D/'CONTINUATION_INTEGRITY.json').open('x') as f: json.dump(record,f,indent=2)
print(json.dumps(record,indent=2))
