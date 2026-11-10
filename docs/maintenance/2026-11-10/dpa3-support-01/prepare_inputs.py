"""Back up navigation and copy only allowed NPY members, without numeric imports."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile
W=Path('/root/autodl-tmp/rap-workspace-20261106');A=W/'RAP-main';P=A/'docs/maintenance/2026-11-10/dpa2-cross-anchor-01';R=P.with_name('dpa3-support-01')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
assert not R.exists();R.mkdir()
for rel in ['docs/AGENTS.md','docs/maintenance/AGENTS.md','docs/maintenance/2026-11-10/AGENTS.md']:
 assert not (A/rel).exists(),f'Read additional instructions first: {rel}'
parent_manifest=read(P/'ARTIFACT_MANIFEST.json');assert all(sha(P/p)==h for p,h in parent_manifest.items())
assert read(P/'CLOSEOUT_CHECKS.json')['passed']
entries=['AGENTS.md','RAP-main/AGENTS.md','RAP-SLAM/AGENTS.md','RAP-main/docs/CURRENT_STATE.json','RAP-main/docs/CURRENT_STATE.md','RAP-main/docs/experiments/README.md','RAP-main/docs/experiments/RESIDUAL_02.md','RAP-main/docs/CONVENTIONS.md']
before={}
for rel in entries:
 target=R/'before'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/rel,target);before[rel]=sha(target)
git={}
for repo in ['RAP-main','RAP-SLAM']:
 cwd=W/repo
 assert not subprocess.check_output(['git','-C',str(cwd),'diff','--cached','--name-only'],text=True)
 git[repo]={'head':subprocess.check_output(['git','-C',str(cwd),'rev-parse','HEAD'],text=True).strip(),'index_sha256':sha(cwd/'.git/index'),'status':subprocess.check_output(['git','-C',str(cwd),'status','--short'],text=True)}
(R/'BEFORE.json').write_text(json.dumps({'files':before,'git':git,'DPA2_manifest_sha256':sha(P/'ARTIFACT_MANIFEST.json')},indent=2)+'\n')
(R/'inputs').mkdir();records={};roles={}
# IDs and roles only. Never copy or decode a reference pose.
for pid,role,event in [('02_001825_004400','low','02_12_29'),('02_001875_004450','low','02_12_29'),('02_003350_004625','high','02_22_30'),('02_003400_004575','high','02_22_30')]:
 out=R/'inputs'/f'{pid}.npz';members={};parents={}
 with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as dst:
  for source,allowed in [(P/'inputs'/f'{pid}.npz',['a','b','na','nb','final']),(P/'results'/f'{pid}-queries.npz',['f_d0','f_j0','r_d0','r_j0'])]:
   assert sha(source)==parent_manifest[str(source.relative_to(P))];parents[str(source)]={'sha256':sha(source),'members_read':allowed}
   with zipfile.ZipFile(source) as src:
    for key in allowed:
     name=key+'.npy';payload=src.read(name)
     entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o644<<16
     dst.writestr(entry,payload);members[name]={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)}
 records[out.name]={'sha256':sha(out),'bytes':out.stat().st_size,'members':members,'parents':parents,'pair':pid,'role':role,'event_group':event}
(R/'INPUTS.json').write_text(json.dumps({'files':records,'numeric_arrays_decoded_during_copy':0,'forbidden_members_read':0,'original_raw_reads':0,'source_status':'UNKNOWN_RETAINED','role':'EXPOSED_DEVELOPMENT'},indent=2)+'\n')
print('Created DPA3 stage, backed up 8 entries, copied allowed members only:',sum(x['bytes'] for x in records.values()),'bytes')
