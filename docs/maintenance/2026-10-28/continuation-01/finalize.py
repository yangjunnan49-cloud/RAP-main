import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
root=Path.cwd();base=root/'docs/maintenance/2026-10-28';out=base/'continuation-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checked=[]
for name in ['kitti-access-page-request-01','kitti-registration-page-request-01']:
 d=base/name;s=d/'DELIVERY_SEAL.json';j=json.loads(s.read_text(encoding='utf-8-sig'))
 for e in j['files']:
  p=d/e['path'];assert p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'].lower(),str(p)
 checked.append({'scope':name,'seal_sha256':sha(s),'files_verified':len(j['files']),'closed_checks':json.loads((d/'CLOSE_CHECKS.json').read_text(encoding='utf-8-sig'))})
(out/'CLOSED_SOURCE_SCOPES.json').write_text(json.dumps({'all_match':True,'scopes':checked},indent=2)+'\n',encoding='utf-8')
agent=root/'AGENTS.md';old=agent.read_bytes();backup=out/'AGENTS.before.md';assert not backup.exists();backup.write_bytes(old)
header='''# October28 official access clarified; registration/download packet READY

Owner explicitly says "请继续推进", then confirms no KITTI account and asks for help preparing registration/download steps. Read docs/maintenance/2026-10-28/continuation-01/REGISTRATION_AND_DOWNLOAD_CN.md, REPORT.md and CURRENT_HANDOFF.md. New direct human continuation, not automatic reset resume; latest20%/ordinaryTRUE/reset1793169166 followed01:38:40UTC is NOT exhaustion. Prior October26 explicit usage-limit auto-review failure now recorded additively; its final account/addendum write did not execute. Earlier ACTIVE text is historical only.

KAP1 and KRP1 separately authorized exact anonymous official access/registration HTMLs:1GET each/9705+8411bodybytes/200/EOF, no redirect/link/form/cookie/credential/account/email/data action. Complete sources112.8221084/900s and92.1779502/900s; transport3.3376743/1.9115745s, conservative peaks29913088/29847552bytes. Fresh12GiB/2s gates PASS, children exit0/reaped; source seals verify55entries. Original local recovery100.6429924/1200s checks17 old delivery entries; old files unchanged.

Official policy requires download registration and intended use; first stage plus email activation suffices for download, no leaderboard application needed. Public form fields and2-3sentence purpose verified. Chinese guide and editable truthful English purpose ready; personal name/organization/URL/institutional email/password must be supplied privately by owner on site. Personal-email acceptance and actual activation/download success UNKNOWN. No account submission, email/activation, terms acceptance or22GB download authorized by this preparation.

Complete required-camera packet:273 unique image0anchors (00=157,08=116) for all200 existing F2 pairs, derived from sealed metadata without outcome/support filtering or image/point/reference decode. Expected archive prefix/dimensions not yet checked. Next dependency is human account activation and legitimate local image archive/directory plus source record, followed by bounded member/dimension/calibration/time inspection before a separately frozen experiment. Do not fill available quota with unrelated prototypes, re-ask the absent local-path question, guess endpoints or run old stages.

Conditional camera/ordinary-geometry/RAP-initializer/no-evidence fallback strategy unchanged; intrinsic correction remains point-direction-dependent, not global SE(3). SR1 approximately1.98% fitting loss decrease/all four noise cells FAIL, all old failures/caps/stops and missing RegX provenance unchanged. Research UNRESOLVED/manuscript PAUSED. No WSL startup/environment/default/production/install/Git/outreach/scheduler/goal-status change. Existing E image/backup/Junction retained; no fresh infrastructure claim. Prior AGENTS exact bytes backed up and retained below; no automatic reset continuation.

---

'''.encode('utf-8')
agent.write_bytes(header+old);assert agent.read_bytes()[len(header):]==backup.read_bytes();(out/'AGENTS_UPDATE_PROOF.json').write_text(json.dumps({'before_sha256':sha(backup),'after_sha256':sha(agent),'prior_bytes':len(old),'prefix_bytes':len(header),'prior_bytes_exact_suffix':True},indent=2)+'\n',encoding='utf-8')
now=datetime.now(timezone.utc);origin=datetime(2026,10,28,1,37,25,tzinfo=timezone.utc);elapsed=(now-origin).total_seconds();assert elapsed<=600
(out/'DELIVERY_CHECKS.json').write_text(json.dumps({'utc':now.isoformat(),'documentary_origin_utc':origin.isoformat(),'cap_seconds':600,'inclusive_seconds':elapsed,'cap_pass':True,'source_sealed_entries_verified':sum(e['files_verified'] for e in checked),'required_camera_members':273,'no_registration_or_data_action':True,'old_agents_suffix_exact':True,'current_exhaustion_observed':False},indent=2)+'\n',encoding='utf-8')
entries=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json'];assert sum(p['bytes'] for p in entries)<8*1024**2;(out/'DELIVERY_SEAL.json').write_text(json.dumps({'files':entries,'registration_download_preparation_complete':True,'human_account_and_image_source_still_required':True},indent=2)+'\n',encoding='utf-8');print(json.dumps({'source_entries_verified':sum(e['files_verified'] for e in checked),'delivery_files':len(entries),'delivery_seconds':elapsed,'agents_suffix_exact':True}))