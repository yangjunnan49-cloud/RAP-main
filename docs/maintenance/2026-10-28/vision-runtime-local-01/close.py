import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
root=Path.cwd();d=root/'docs/maintenance/2026-10-28/vision-runtime-local-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();f=json.loads((d/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
for n,h in f['files'].items():assert sha(d/n)==h.lower()
assert json.loads((d/'API_RESULT.json').read_text())['passed'];assert json.loads((d/'LOCAL_WHEEL_RESULT.json').read_text())['passed']
agent=root/'AGENTS.md';old=agent.read_bytes();backup=d/'AGENTS.before.md';assert not backup.exists();backup.write_bytes(old)
header='''# October28 local OpenCV runtime admission COMPLETE, no visual experiment yet

Owner downloaded the requested complete wheel. Read docs/maintenance/2026-10-28/vision-runtime-local-01/REPORT.md, CURRENT_HANDOFF.md, LOCAL_WHEEL_RESULT.json, API_RESULT.json and CLOSE_CHECKS.json. Exact43825962bytes/SHA829717b6a95554f273e49e357cee3b3a2a26b6f4842fbc1bed2b45bdd8f87e0e andZIPsafety/CRC PASS. Offline no-index/no-deps install only into new project-local site-packages succeeds; no network, old-transfer retry, NumPy dependency update, existing Python/RAP/SLAM/PATH change.

Nativecv2 version5.0.0/distribution5.0.0.93, existing bundledNumPy2.3.5. SIFT/ORB/matcher factories andPnP/essential/recoverPose APIs/docstrings pass, oneCPUthread/OpenCLoff/Torchnotimported. Validation2.0710285s/peak62644224bytes,install2.1042768s/61706240bytes,probe0.7115014s/35471360bytes, fresh12GiB/2s gates PASS, childrenexit0/reaped. This new local success supersedes unavailable-runtime prose only; both original failed network scopes/partials/caps remain unchanged. Do not rerun installation host.

No image matching/pose solver/model/training has executed. Next actual task is implement/freeze/admit complete273image/200pair ordinary SIFT/calibrated-essential5DoF baseline with functional controls and sealed reference-free prediction before supplied-reference evaluation; draft alone and package approval do not admit it. No metric translation scale, corrected-LiDAR rigid equivalence, physical/generalization or RAP increment claim. Existing273-image/CF1 results and all old SR1/native/HFIT0/joint/equivalence/provenance failures/caps remain. ResearchUNRESOLVED/manuscriptPAUSED. Initial91%/ordinaryTRUE/reset1793169166 followed04:42:00UTC is not exhaustion; later additive receipts govern. No automatic reset resume/default/production/Git/outreach/scheduler/goal-status change. Exact preceding AGENTS bytes backed up/retained below.

---

'''.encode('utf-8');agent.write_bytes(header+old);assert agent.read_bytes()[len(header):]==backup.read_bytes();(d/'AGENTS_UPDATE_PROOF.json').write_text(json.dumps({'before_sha256':sha(backup),'after_sha256':sha(agent),'prior_bytes':len(old),'prefix_bytes':len(header),'prior_bytes_exact_suffix':True},indent=2)+'\n',encoding='utf-8')
now=datetime.now(timezone.utc);elapsed=(now-datetime(2026,10,28,4,42,tzinfo=timezone.utc)).total_seconds();size=sum(p.stat().st_size for p in d.rglob('*') if p.is_file());assert elapsed<=600 and size<1024**3
(d/'CLOSE_CHECKS.json').write_text(json.dumps({'utc':now.isoformat(),'status':'COMPLETE_LOCAL_ISOLATED_RUNTIME_API_ADMISSION','inclusive_seconds':elapsed,'cap_seconds':600,'cap_pass':True,'dossier_bytes':size,'dossier_cap_pass':True,'network_requests':0,'offline_install_pass':True,'classical_API_probe_pass':True,'image_feature_solver_model_calls':0,'no_live_owned_process':True,'old_failed_scopes_changed':False},indent=2)+'\n',encoding='utf-8')
files=[{'path':p.relative_to(d).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(d.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json'];(d/'DELIVERY_SEAL.json').write_text(json.dumps({'files':files,'later_account_receipts_are_additive':True},indent=2)+'\n',encoding='utf-8');print(json.dumps({'complete_runtime':True,'scope_seconds':elapsed,'sealed_entries':len(files),'dossier_bytes':size,'agents_suffix_exact':True}))