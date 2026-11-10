"""Preserve prior work and review the one-commit fast-forward publishing scope."""
import ast
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
W=Path('/root/autodl-tmp/rap-workspace-20261106');A=W/'RAP-main';R=A/'docs/maintenance/2026-11-10/dpa4-structure-01';D=R.with_name('dpa1-profile-01');P=R.with_name('dpa3-support-01')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=read(R/'BEFORE.json');assert all(sha(R/'before'/p)==h for p,h in b['files'].items())
prod=read(P/'SOURCE_HASHES.json')['production_preserved'];assert len(prod)==22 and all(sha(W/p)==h for p,h in prod.items())
for directory in [D,R.with_name('dpa2-cross-anchor-01'),P]:assert all(sha(directory/p)==h for p,h in read(directory/'ARTIFACT_MANIFEST.json').items())
assert all(sha(Path(p))==h for p,h in read(D/'EXPERIMENT_SEAL.json').items())
n=0
for rel,entry in read(D/'CLOSEOUT_CHECKS.json')['old_seals'].items():
 p=W/rel;assert sha(p)==entry['sha256'];x=read(p);files=x.get('files',x);assert all(sha(Path(path))==h for path,h in files.items());n+=len(files)
assert n==115
frozen=read(R/'freeze.json');assert all(sha(R/p)==h for p,h in frozen['files'].items());assert all(sha(R/'inputs'/p)==e['sha256'] for p,e in frozen['inputs'].items());assert sha(R/'EVALUATION_ONLY.json')==frozen['evaluation_only_sha256']
x=read(R/'results/RESULTS.json');v=read(R/'INDEPENDENT_CHECKS.json');s=read(R/'real-supervision.json')
assert v['passed'] and v['score_checks']==96 and v['saved_distance_checks']==32 and v['Gram_groups']==28 and v['truth_identity_checks']==8
assert v['decision']=='STOP_THIS_BLOCK_SCORE_RECIPE' and v['new_correct_over_nn_cases']==[]
assert all(v['summary'][m]=={'identified_correct':4,'identified_wrong':0,'abstained':4,'ambiguous_forced':0} for m in ['nn_mean','block_score'])
assert x['NN_queries']==32 and not x['evaluation_truth_read_by_scorer'] and x['real_data_reads']==x['model_ICP_training_calls']==0
for name in ['real-supervision.json','generation-supervision.json','validation-supervision.json']:
 q=read(R/name);assert q['passed'] and q['wall_s']<30 and q['observed_peak_RSS_bytes']+q['supervisor_peak_RSS_bytes']<2*2**30 and q['final_output_bytes']<4*2**20
assert read(R/'preflight.json')['passed'] and len(read(R/'synthetic.json')['checks'])==9
state=read(A/'docs/CURRENT_STATE.json');old=read(R/'before/RAP-main/docs/CURRENT_STATE.json');assert state['preservation_holds']==old['preservation_holds']
assert all(state['research'][k]==old['research'][k] for k in old['research'] if k!='last_research_closeout')
spec=importlib.util.spec_from_file_location('render',A/'scripts/maintenance/render_current_state.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);assert mod.render(state)==(A/'docs/CURRENT_STATE.md').read_text()
for p in R.glob('*.py'):ast.parse(p.read_text())
svg=(R/'mechanism_comparison.svg').read_text();clean=(R/'mechanism_comparison.clean.svg').read_text();ET.fromstring(svg);ET.fromstring(clean);assert ''.join(svg.split())==''.join(clean.split())
git={}
for repo in ['RAP-main','RAP-SLAM']:
 cwd=W/repo;head=subprocess.check_output(['git','-C',str(cwd),'rev-parse','HEAD'],text=True).strip();assert head==b['git'][repo]['head'] and sha(cwd/'.git/index')==b['git'][repo]['index_sha256']
 assert not subprocess.check_output(['git','-C',str(cwd),'diff','--cached','--name-only'],text=True)
 chk=subprocess.run(['git','-C',str(cwd),'-c','core.whitespace=cr-at-eol','diff','--check'],capture_output=True,text=True);assert chk.returncode==0,chk.stdout[:1000]
 git[repo]={'head_before_planned_commit':head,'index_unchanged_before_planned_commit':True}
remote=subprocess.check_output(['git','remote','get-url','--push','origin'],cwd=A,text=True).strip();assert remote=='git@ssh.github.com:yangjunnan49-cloud/RAP-main.git'
branch='refs/heads/chore/autodl-history-20261107';remotehead=subprocess.check_output(['git','ls-remote','origin',branch],cwd=A,text=True).split()[0]
assert remotehead=='12f72996b5a9790857039a5fcc1e019dc33608c1'
subprocess.run(['git','merge-base','--is-ancestor',remotehead,'HEAD'],cwd=A,check=True)
previous=subprocess.check_output(['git','rev-list','--reverse',remotehead+'..HEAD'],cwd=A,text=True).splitlines();assert previous==['f505c74c33874d1d7da78c1a570d0643520304aa','4081ddcad78235a2953d680eacc0b18719ebd066']
paths=subprocess.check_output(['git','diff','--name-only',remotehead,'HEAD'],cwd=A,text=True).splitlines()
assert all(p.startswith(('docs/maintenance/2026-11-10/dpa2-cross-anchor-01/','docs/maintenance/2026-11-10/dpa3-support-01/')) or p in ['docs/experiments/DPA2.md','docs/experiments/DPA3.md'] for p in paths)
plan={'remote':'origin','url':remote,'branch':branch,'remote_head_before':remotehead,'previous_pending_commits':previous,'previous_pending_paths_reviewed':len(paths),'new_commits_this_turn':1,'expected_pushed_commit_count':3,'force':False,'RAP_SLAM_push':False,'production_changes_included':False}
(R/'PUSH_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
current={}
for rel in b['files']:
 target=R/'after'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/rel,target);current[rel]=sha(target)
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if 'python' in cmd.split(' ',1)[0] and any(k in cmd for k in ['mechanism.py run','supervise.py run','verify_mechanism.py']):active.append({'pid':int(p.name),'cmd':cmd})
assert not active
(R/'SOURCE_HASHES.json').write_text(json.dumps({'production_preserved':prod,'current_entry_snapshots':current},indent=2)+'\n')
(R/'FIGURE_REVIEW.json').write_text(json.dumps({'reviewed':True,'all_cases_and_three_methods_present':True,'mechanism_only_no_real_accuracy_claim':True,'clean_svg_valid_whitespace_only':True},indent=2)+'\n')
checks={'passed':True,'observed_utc':datetime.now(timezone.utc).isoformat(),'before_backups_verified':8,'production_preserved':22,'production_modified':0,'old_seals':9,'old_seal_entries':n,'DPA1_DPA2_DPA3_artifacts_preserved':True,'cases':8,'queries':32,'real_data_reads':0,'score_checks':96,'saved_distance_checks':32,'Gram_groups':28,'identity_cases':8,'new_block_over_nn_correct':0,'stop_decision':'STOP_THIS_BLOCK_SCORE_RECIPE','synthetic_cases':9,'resource_controls':4,'unexpected_execution_failures':0,'wall_s':s['wall_s'],'result_bytes':s['final_output_bytes'],'current_state_render_exact':True,'research_holds_unchanged':True,'scientific_promotion':False,'source_status':'UNKNOWN_RETAINED','root_regression_rerun':False,'root_regression_reason':'22 production files unchanged; new bounded diagnostic independently validated.','git':git,'active_jobs':active,'commit_planned':'ONE_FOCUSED_RAP_MAIN_COMMIT','push_planned':'ONE_FAST_FORWARD_ORIGIN_PUSH_INCLUDING_TWO_PRIOR_DIAGNOSTICS','next_step':'ENGINEERING_BASELINE_INTEGRATION_REVIEW_PLAN_NOT_EXECUTED'}
(R/'CLOSEOUT_CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
m={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p!=R/'ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts};(R/'ARTIFACT_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k!='git'},indent=2));print('Push plan reviewed:',json.dumps(plan))
