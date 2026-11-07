import hashlib,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
root=Path.cwd();base=root/'docs/maintenance/2026-10-28';out=base/'records-update-01'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def save(n,o):
 with (out/n).open('x',encoding='utf-8') as f:json.dump(o,f,indent=2,ensure_ascii=False)
scopes=['continuation-01','kitti-access-page-request-01','kitti-registration-page-request-01','image-archive-admission-01','image-packet-verification-01','visual-runtime-readiness-01','visual-environment-census-01','opencv-metadata-request-01','vision-runtime-install-01','vision-runtime-resume-01','camera-frustum-support-01','camera-observation-continuation-01','vision-runtime-local-01']
verified=[];members=set()
for name in scopes:
 d=base/name;seal=d/'DELIVERY_SEAL.json';obj=json.loads(seal.read_text(encoding='utf-8-sig'))
 for e in obj['files']:
  p=d/e['path'];assert p.resolve().is_relative_to(d.resolve());assert p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'].lower(),str(p);members.add(str(p.resolve()))
 verified.append({'scope':name,'seal_sha256':sha(seal),'entries_verified':len(obj['files'])})
additive=[]
for rel in ['continuation-01/ACCOUNT_03.json','continuation-01/CURRENT_HANDOFF.md','continuation-01/ADDITIVE_DELIVERY_CHECKS.json','continuation-01/CAMERA_ADMISSION_DECISION.md','camera-observation-continuation-01/ACCOUNT_03_ADDITIVE.json','vision-runtime-local-01/ACCOUNT_ADDITIVE.json','vision-runtime-local-01/NEXT_PLAN_ADDITIVE.md']:
 p=base/rel;assert p.is_file();additive.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'role':'Additive after the original delivery seal; independently bound here'})
save('SOURCE_INDEX.json',{'final_seals':verified,'later_additives':additive,'all_original_files_preserved':True})
phase=base/'PHASE_RECORD.md';assert not phase.exists(),'Preserve an existing day phase record'
phase.write_text('''# 2026-10-28 阶段记录快照

记录基准：北京时间14:41:58。最新交接为 records-update-01/CURRENT_HANDOFF.md，事实状态为 records-update-01/CURRENT_STATE.json。后续工作应另建追加记录，保留已封存阶段原件。

1. 官方访问/注册说明核查完成；注册下载指南和完整273帧成员清单建立。用户随后提供下载完成的灰度图像ZIP。
2. IA1/IP1完成档案全哈希、全部273帧ZIP/PNG/完整灰度解码及尺寸核查；P0–P3精确一致、时间表逐字节一致。新包没有Tr，原外参和独立出处/真值认证限制仍在。200配对无筛选。
3. CF1完成200配对/400方向的有限视野上界检查；00/08原75正例分别15/42对双向宽松上界为零。只属源LiDAR投影支持，不是实际匹配、可见性、错误标签或拒绝器。补充读出时序更正保留。
4. 现有运行时缺少OpenCV；固定软件元数据核查完成。完整GET及另批Range均以超时失败关闭，未安装，原失败/部分文件/限额保留。
5. 用户后来提供完整固定wheel。OVL1本地哈希/ZIP、独立目录离线无依赖安装及经典API/工厂检查通过；原生cv2为5.0.0、发行版5.0.0.93，沿用NumPy2.3.5，未改原RAP/SLAM环境。
6. 视觉匹配、位姿估计、新RAP训练均未开展。下一步仅计划实现和冻结完整200配对普通SIFT/本质矩阵5DoF对照及控制/评估隔离；无平移尺度或RAP增量结果。
7. 本次仅文档更新与封存核验，不自动续跑实验。研究UNRESOLVED/论文PAUSED，旧训练噪声失败与所有停止/上限不变。当前额度1%可用，前窗口97%可用后实际边界未观察，禁止反推耗尽或自动重置续跑。没有Git写入、外联、调度或goal-status动作。
''',encoding='utf-8')
agent=root/'AGENTS.md';before=agent.read_bytes();backup=out/'AGENTS.before.md';assert not backup.exists();backup.write_bytes(before)
header='''# October28 records consolidated, documentary request COMPLETE

Owner requests only "做好更新和记录". Read docs/maintenance/2026-10-28/records-update-01/CURRENT_HANDOFF.md, CURRENT_STATE.json, REPORT_CN.md and CHECKS.json; day snapshot docs/maintenance/2026-10-28/PHASE_RECORD.md. This is a documentary update, not numerical admission or renewed until-quota execution. Current1%/ordinaryTRUE/reset1793187718 followed06:41:58UTC is availability only; previous last97%/ordinaryTRUE has no later actual boundary observation. No inferred reset cause or automatic reset resume.

Actual273 camera0 images/all200pairs are complete; ZIP/PNG/full decode and supplied P0-P3/time associations PASS. New archive lacksTr/independent physical source authentication. CF1 all400directions uses measured dimensions; original75positive-pair both-zero generous-upper counts00=15,08=42. This is projected source-LiDAR support only, not actual visibility/correspondence/incorrectness or an absence veto. All old source/trajectory/training caps and negative results remain.

Local pinned wheel43,825,962bytes/SHA829717b6a95554f273e49e357cee3b3a2a26b6f4842fbc1bed2b45bdd8f87e0e admits offline isolated OpenCV5.0.0(distribution5.0.0.93) with existingNumPy2.3.5. API/factory checks PASS; existing environments unchanged. Both earlier network failures remain CLOSED failed; missing-runtime prose is historical only. Do not rerun download/install hosts.

No actual image matching/pose estimation/new RAP training has run. Next task is complete reviewable ordinary SIFT/calibrated-essential5DoF baseline implementation, controls, source/resource freeze and prediction-before-reference-evaluation separation; no metric scale/full6DoF/RAP increment claim or automatic experiment. SR1 approximately1.98% fitting-only loss decrease/all4noisecellsFAIL, HFIT0INCOMPLETE/original2GiB stop and all other old failures/caps unchanged. ResearchUNRESOLVED/manuscriptPAUSED. No new scientific computation/installation/WSL startup/default/production/Git/outreach/scheduler/goal-status action this update. Exact prior AGENTS bytes backed up/retained below; source seals and later additives are distinguished.

---

'''.encode('utf-8');agent.write_bytes(header+before);assert agent.read_bytes()[len(header):]==backup.read_bytes()
save('AGENTS_UPDATE_PROOF.json',{'before_sha256':sha(backup),'after_sha256':sha(agent),'prior_bytes':len(before),'prefix_bytes':len(header),'prior_bytes_exact_suffix':True})
now=datetime.now(timezone.utc);elapsed=(now-datetime(2026,10,28,6,41,58,tzinfo=timezone.utc)).total_seconds();assert elapsed<=600
save('CHECKS.json',{'utc':now.isoformat(),'Asia_Shanghai':now.astimezone(timezone(timedelta(hours=8))).isoformat(),'status':'COMPLETE_DOCUMENTARY_RECORDS_UPDATE','inclusive_seconds':elapsed,'cap_seconds':600,'cap_pass':True,'verified_final_seals':len(verified),'verified_manifest_entries':sum(x['entries_verified'] for x in verified),'unique_verified_member_paths':len(members),'separately_bound_additive_records':len(additive),'all_hashes_and_lengths_match':True,'original_sealed_files_modified':False,'prior_agents_exact_suffix':True,'day_phase_record_created_without_overwrite':True,'day_phase_sha256':sha(phase),'new_image_model_training_run':False,'new_network_install_or_WSL_start':False,'main_HEAD':'4055d929c594b0033aafc6eed339c910369eef55','tracked_dirty_paths':['.gitignore','AGENTS.md'],'new_experiment_admitted_or_scheduled':False})
files=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json'];assert sum(e['bytes'] for e in files)<8*1024**2
save('DELIVERY_SEAL.json',{'files':files,'external_snapshot':{'path':str(phase),'sha256':sha(phase)},'future_updates_should_be_additive':True})
print(json.dumps({'verified_seals':len(verified),'verified_entries':sum(x['entries_verified'] for x in verified),'unique_members':len(members),'additives':len(additive),'records_files':len(files),'seconds':elapsed,'all_pass':True}))