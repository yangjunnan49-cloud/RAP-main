"""Verify DPA3 artifacts and preserve production/history before focused commit."""
import ast
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
W=Path('/root/autodl-tmp/rap-workspace-20261106');A=W/'RAP-main';R=A/'docs/maintenance/2026-11-10/dpa3-support-01';P=R.with_name('dpa2-cross-anchor-01');D=R.with_name('dpa1-profile-01')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
b=read(R/'BEFORE.json');assert all(sha(R/'before'/p)==h for p,h in b['files'].items())
prod=read(P/'SOURCE_HASHES.json')['production_preserved'];assert len(prod)==22 and all(sha(W/p)==h for p,h in prod.items())
assert sha(P/'ARTIFACT_MANIFEST.json')==b['DPA2_manifest_sha256']
assert all(sha(P/p)==h for p,h in read(P/'ARTIFACT_MANIFEST.json').items())
assert all(sha(D/p)==h for p,h in read(D/'ARTIFACT_MANIFEST.json').items())
assert all(sha(Path(p))==h for p,h in read(D/'EXPERIMENT_SEAL.json').items())
n=0
for rel,entry in read(D/'CLOSEOUT_CHECKS.json')['old_seals'].items():
 p=W/rel;assert sha(p)==entry['sha256'];data=read(p);files=data.get('files',data)
 assert all(sha(Path(path))==h for path,h in files.items());n+=len(files)
assert n==115
frozen=read(R/'freeze.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
allowed={'a','b','na','nb','final','f_d0','f_j0','r_d0','r_j0'};total=0
for name,entry in frozen['inputs'].items():
 p=R/'inputs'/name;assert sha(p)==entry['sha256'];assert p.stat().st_size<=4*2**20;total+=p.stat().st_size
 for parent,meta in entry['parents'].items():assert sha(Path(parent))==meta['sha256']
 with zipfile.ZipFile(p) as z:
  assert set(z.namelist())=={k+'.npy' for k in allowed}
  assert all(hashlib.sha256(z.read(member)).hexdigest()==meta['sha256'] for member,meta in entry['members'].items())
assert total==9342732<16*2**20
x=read(R/'results/RESULTS.json');ind=read(R/'INDEPENDENT_CHECKS.json');sup=read(R/'real-supervision.json');val=read(R/'validation-supervision.json')
assert ind['passed'] and ind['checks']['Gram_matrices']==32 and ind['checks']['saved_distances']==8
assert x['NN_queries']==x['raw_reads']==x['forbidden_array_reads']==x['model_ICP_training_calls']==0
assert not x['scipy_torch_open3d_imported'] and set(x['loaded_members'])==allowed
for s in [sup,val]:assert s['passed'] and s['wall_s']<30 and s['observed_peak_RSS_bytes']+s['supervisor_peak_RSS_bytes']<2*2**30
assert sup['final_output_bytes']==83740<4*2**20
assert read(R/'preflight.json')['passed'] and len(read(R/'synthetic.json')['checks'])==10
state=read(A/'docs/CURRENT_STATE.json');oldstate=read(R/'before/RAP-main/docs/CURRENT_STATE.json');assert state['preservation_holds']==oldstate['preservation_holds']
assert all(state['research'][k]==oldstate['research'][k] for k in oldstate['research'] if k!='last_research_closeout')
spec=importlib.util.spec_from_file_location('render',A/'scripts/maintenance/render_current_state.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);assert mod.render(state)==(A/'docs/CURRENT_STATE.md').read_text()
for p in R.glob('*.py'):ast.parse(p.read_text())
svg=(R/'support_diagnostics.svg').read_text();clean=(R/'support_diagnostics.clean.svg').read_text();ET.fromstring(svg);ET.fromstring(clean);assert ''.join(svg.split())==''.join(clean.split())
git={}
for repo in ['RAP-main','RAP-SLAM']:
 cwd=W/repo;head=subprocess.check_output(['git','-C',str(cwd),'rev-parse','HEAD'],text=True).strip()
 assert head==b['git'][repo]['head'] and sha(cwd/'.git/index')==b['git'][repo]['index_sha256']
 assert not subprocess.check_output(['git','-C',str(cwd),'diff','--cached','--name-only'],text=True)
 diff=subprocess.run(['git','-C',str(cwd),'-c','core.whitespace=cr-at-eol','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stdout[:2000]
 git[repo]={'head_before_planned_commit':head,'index_unchanged_before_planned_commit':True,'branch':subprocess.check_output(['git','-C',str(cwd),'branch','--show-current'],text=True).strip()}
current={}
for rel in b['files']:
 target=R/'after'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/rel,target);current[rel]=sha(target)
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if 'python' in cmd.split(' ',1)[0] and any(s in cmd for s in ['support_algebra.py run','supervise.py run','verify_algebra.py']):active.append({'pid':int(p.name),'cmd':cmd})
assert not active
(R/'SOURCE_HASHES.json').write_text(json.dumps({'production_preserved':prod,'current_entry_snapshots':current},indent=2)+'\n')
(R/'FIGURE_REVIEW.json').write_text(json.dumps({'reviewed':True,'four_pairs_and_both_directions_present':True,'native_target_frames_not_pooled':True,'no_physical_correctness_claim':True,'clean_svg_whitespace_only_and_valid_XML':True},indent=2)+'\n')
checks={'passed':True,'observed_utc':datetime.now(timezone.utc).isoformat(),'before_backups_verified':8,'production_files_preserved':22,'production_modified':0,'old_seals':9,'old_seal_entries':n,'DPA1_DPA2_artifacts_preserved':True,'whitelist_input_files':4,'whitelist_input_bytes':total,'forbidden_members_absent':True,'NN_queries':0,'raw_reads':0,'reference_array_reads':0,'model_ICP_training_calls':0,'independent_checks':ind['checks'],'synthetic_checks':10,'resource_controls':4,'unexpected_execution_failures':0,'real_wall_s':sup['wall_s'],'validation_wall_s':val['wall_s'],'real_peak_RSS_bytes':sup['observed_peak_RSS_bytes'],'result_bytes':sup['final_output_bytes'],'current_state_render_exact':True,'research_holds_unchanged':True,'scientific_promotion':False,'source_status':'UNKNOWN_RETAINED','root_regression_rerun':False,'root_regression_reason':'All 22 production files unchanged; new diagnostic has bounded synthetic/numerical verification.','git':git,'active_jobs':active,'commit_planned':'ONE_FOCUSED_RAP_MAIN_COMMIT','commit_scope':['docs/maintenance/2026-11-10/dpa3-support-01/','docs/experiments/DPA3.md'],'push_executed':False,'next_step':'DPA4_CONTROLLED_STRUCTURE_IDENTIFIABILITY_DRAFT_NOT_EXECUTED'}
(R/'CLOSEOUT_CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
manifest={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p!=R/'ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts}
(R/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k!='git'},indent=2))
