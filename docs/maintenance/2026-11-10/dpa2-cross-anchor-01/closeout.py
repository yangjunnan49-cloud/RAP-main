"""Verify preservation, then freeze a focused DPA2 commit payload."""
import ast
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
W=Path('/root/autodl-tmp/rap-workspace-20261106');A=W/'RAP-main';R=A/'docs/maintenance/2026-11-10/dpa2-cross-anchor-01';P=R.with_name('dpa1-profile-01')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=read(R/'BEFORE.json');assert all(sha(R/'before'/p)==h for p,h in before['files'].items())
prod=read(P/'SOURCE_HASHES.json')['production_preserved'];assert len(prod)==22 and all(sha(W/p)==h for p,h in prod.items())
old=read(P/'CLOSEOUT_CHECKS.json');n=0
for rel,rec in old['old_seals'].items():
 p=W/rel;assert sha(p)==rec['sha256'];data=read(p);files=data.get('files',data)
 assert all(sha(Path(p))==h for p,h in files.items());n+=len(files)
assert n==115
assert all(sha(P/p)==h for p,h in read(P/'ARTIFACT_MANIFEST.json').items())
assert all(sha(Path(p))==h for p,h in read(P/'EXPERIMENT_SEAL.json').items())
frozen=read(R/'freeze.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
assert all(sha(R/'inputs'/p)==e['sha256'] for p,e in frozen['inputs'].items())
ind=read(R/'INDEPENDENT_CHECKS.json');sup=read(R/'real-supervision.json');x=read(R/'results/RESULTS.json')
assert ind['passed'] and ind['loss_checks']==64 and ind['saved_distance_checks']==16
assert sup['passed'] and sup['wall_s']<60 and sup['observed_peak_RSS_bytes']+sup['supervisor_peak_RSS_bytes']<2*2**30
assert x['queries']==16 and x['original_raw_reads']==x['new_model_ICP_training_calls']==0
assert sup['final_output_bytes']==3869438<8*2**20
assert read(R/'preflight.json')['passed'] and len(read(R/'synthetic.json')['checks'])==8
for p in x['pairs']:
 for d in ['forward','reverse']:
  for key in ['full_preference','intersection_preference']:
   assert p[d][key]==(['T0','T1'] if p['role']=='low' else ['T0','T0'])
state=read(A/'docs/CURRENT_STATE.json');previous=read(R/'before/RAP-main/docs/CURRENT_STATE.json')
assert state['preservation_holds']==previous['preservation_holds']
assert all(state['research'][k]==previous['research'][k] for k in previous['research'] if k!='last_research_closeout')
spec=importlib.util.spec_from_file_location('render',A/'scripts/maintenance/render_current_state.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
assert mod.render(state)==(A/'docs/CURRENT_STATE.md').read_text()
for p in R.glob('*.py'):ast.parse(p.read_text())
git={}
for repo in ['RAP-main','RAP-SLAM']:
 cwd=W/repo
 head=subprocess.check_output(['git','-C',str(cwd),'rev-parse','HEAD'],text=True).strip()
 assert head==before['git'][repo]['head'] and sha(cwd/'.git/index')==before['git'][repo]['index_sha256']
 assert not subprocess.check_output(['git','-C',str(cwd),'diff','--cached','--name-only'],text=True)
 subprocess.run(['git','-C',str(cwd),'-c','core.whitespace=cr-at-eol','diff','--check'],check=True)
 git[repo]={'head_before_planned_commit':head,'index_unchanged_before_planned_commit':True,'branch':subprocess.check_output(['git','-C',str(cwd),'branch','--show-current'],text=True).strip()}
current={}
for rel in before['files']:
 target=R/'after'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/rel,target);current[rel]=sha(target)
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if 'python' in cmd.split(' ',1)[0] and any(s in cmd for s in ['cross_anchor.py run','supervise.py run']):active.append({'pid':int(p.name),'cmd':cmd})
assert not active
(R/'SOURCE_HASHES.json').write_text(json.dumps({'production_preserved':prod,'current_entry_snapshots':current},indent=2)+'\n')
(R/'FIGURE_REVIEW.json').write_text(json.dumps({'reviewed':True,'four_pairs_present':True,'intersection_mean_and_correspondence_rows_labeled':True,'row_minimum_not_truth_label':True,'full_64_values_in_report':True},indent=2)+'\n')
checks={'passed':True,'observed_utc':datetime.now(timezone.utc).isoformat(),'before_backups_verified':8,'production_preserved':22,'production_modified':0,'old_seals':9,'old_seal_entries':n,'DPA1_all_artifacts_and_experiments_preserved':True,
'queries':16,'loss_checks':64,'saved_distance_checks':16,'raw_reads':0,'model_ICP_training_calls':0,'wall_s':sup['wall_s'],'peak_RSS_bytes':sup['observed_peak_RSS_bytes'],'output_bytes':sup['final_output_bytes'],
'synthetic_checks':8,'resource_negative_controls':4,'unexpected_execution_failures':0,'current_state_render_exact':True,'research_holds_unchanged':True,'scientific_promotion':False,'source_status':'UNKNOWN_RETAINED','root_regression_rerun':False,'root_regression_reason':'All 22 production files unchanged; bounded diagnostic validated separately.','git':git,'active_jobs':active,'commit_planned':'ONE_FOCUSED_RAP_MAIN_COMMIT','commit_scope':['docs/maintenance/2026-11-10/dpa2-cross-anchor-01/','docs/experiments/DPA2.md'],'push_authorized_or_executed':False,'next_step':'DPA3_CURRENT_POSE_SUPPORT_ALGEBRA_DRAFT_NOT_EXECUTED'}
(R/'CLOSEOUT_CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
manifest={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts}
(R/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k!='git'},indent=2))
