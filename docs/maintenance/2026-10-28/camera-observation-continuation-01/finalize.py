import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
root=Path.cwd();base=root/'docs/maintenance/2026-10-28';out=base/'camera-observation-continuation-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();names=['image-archive-admission-01','image-packet-verification-01','visual-runtime-readiness-01','visual-environment-census-01','opencv-metadata-request-01','vision-runtime-install-01','vision-runtime-resume-01','camera-frustum-support-01'];verified=[]
for name in names:
 d=base/name;s=d/'DELIVERY_SEAL.json';j=json.loads(s.read_text(encoding='utf-8-sig'))
 for e in j['files']:
  p=d/e['path'];assert p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'].lower(),str(p)
 checks=json.loads((d/'CLOSE_CHECKS.json').read_text(encoding='utf-8-sig'));verified.append({'scope':name,'seal_sha256':sha(s),'verified_entries':len(j['files']),'close_checks':checks})
(out/'CLOSED_SCOPES.json').write_text(json.dumps({'all_match':True,'scopes':verified,'overlapping_times_not_summed':True},indent=2)+'\n',encoding='utf-8')
report=(out/'REPORT.md').read_text(encoding='utf-8')
for label,scope in [('VR1 RAP environment','visual-runtime-readiness-01'),('OVI1 fixed wheel GET','vision-runtime-install-01')]:
 c=json.loads((base/scope/'CLOSE_CHECKS.json').read_text(encoding='utf-8-sig'));report=re.sub(r'\|'+re.escape(label)+r'\|[^|]+\|',f"|{label}|{c['inclusive_seconds']} /{c['cap_seconds']}|",report)
(out/'REPORT.md').write_text(report,encoding='utf-8')
agent=root/'AGENTS.md';previous=agent.read_bytes();backup=out/'AGENTS.final.before.md';assert not backup.exists();backup.write_bytes(previous)
header='''# October28 complete actual-image admission and finite-frustum diagnostic; runtime source blocked

Read docs/maintenance/2026-10-28/camera-observation-continuation-01/REPORT.md, STATUS.json, CURRENT_HANDOFF.md and CLOSED_SCOPES.json. All eight finite scopes are closed; no image algorithm/model/solver/training is pending. Earlier RUNNING header/checkpoint is historical and superseded by actual closed receipts. Latest saved83%/ordinaryTRUE/reset1793169166 followed04:03:46UTC is NOT exhaustion; no automatic reset resume or quota-exhaustion claim.

Owner-provided grayZIP23166524501bytes/SHA94963792b9c48e37191583ba44608304713ae018a38735133f1435665f3ada12 has all273 required anchors. IP1 exact273PNGs/71725068bytes onE passZIP/chunkCRC/full grayscale decode;00=157at1241x376,08=116at1226x370. P0..P3 exact Decimal association and time tables byteexact4541/4071rows match old records. New archive lacksTr, no independent physical/source/checkpoint authentication or fresh cohort claim. All200 pairs retained.

CF1 new measured-dimension support complete200pairs/400directions/48742169point occurrences,5controls/independent affine routes/16000Decimal checks PASS. Center-domain2322211/generous-edge upper2327644 source-point occurrences. Original75positive-pair both-zero generous-upper counts00=15,08=42; all25confusers per sequence also retained/reported. This only bounds supplied-reference source-LiDAR projection inside both finite camera frames: not target identity/occlusion/texture/actual correspondence/incorrectness or image-only impossibility. No support-subset or veto rescue. Numeric47.141s/peak133931008bytes, inclusive453.7761832/900s. Supplementary timing correction preserves plan after arithmetic exit/before first result inspection; original primary bytes unchanged.

Known Windows/fourWSL runtimes lackcv2; WSL initialStopped restored. Approved OCM1 metadata succeeds. OVI1 one fixed43.8MBwheel GET times out at34603008bytes; separately approved OVR1 one fixed remainder Range also times out with0 new application body bytes. Both CLOSED failed/no install/API check, partials/requests/costs preserved; no third request or source/version fallback. Existing environments unchanged. Full requiredwheel SHA829717b6a95554f273e49e357cee3b3a2a26b6f4842fbc1bed2b45bdd8f87e0e. Human manual same-wheel local path is next dependency, not another image download. Latest human reply asks for explanation; it is not a completed local wheel receipt.

After local completewheel size/SHA admission, use the already authorized isolated no-dependency installation/API purpose under a new local-only scope; don't rerun failed download hosts or ask again for an already-authorized purpose. The SIFT/essential draft is not executed/admitted and only targets camera rotation/unit translation direction, not metric6DoF or old corrected-LiDAR native-N equivalence. Actual compatible APIs, complete implementation/controls and separate full-cohort freeze/admission still required. No automatic experiment from package approval.

Old SR1 approximately1.98% fitting-only decrease/all four noise cellsFAIL, native/HFIT0/NJE0/RLP2/BRF0/P0/provenance failures/caps remain. ResearchUNRESOLVED/manuscriptPAUSED. No existing-environment/default/production/Git/outreach/scheduler/goal-status changes; E VHD/backup/Junction retained. Exact preceding AGENTS bytes backed up and retained below; no unrelated prototype to fill unavailable-runtime dependency.

---

'''.encode('utf-8');agent.write_bytes(header+previous);assert agent.read_bytes()[len(header):]==backup.read_bytes();(out/'AGENTS_FINAL_PROOF.json').write_text(json.dumps({'before_sha256':sha(backup),'after_sha256':sha(agent),'prior_bytes':len(previous),'prefix_bytes':len(header),'prior_bytes_exact_suffix':True},indent=2)+'\n',encoding='utf-8')
now=datetime.now(timezone.utc);origin=datetime(2026,10,28,4,1,7,tzinfo=timezone.utc);elapsed=(now-origin).total_seconds();assert elapsed<=600
(out/'DELIVERY_CHECKS.json').write_text(json.dumps({'utc':now.isoformat(),'documentary_origin_utc':origin.isoformat(),'cap_seconds':600,'inclusive_seconds':elapsed,'cap_pass':True,'scope_seals_verified':len(verified),'scope_entries_verified':sum(r['verified_entries'] for r in verified),'new_scientific_scope_pending':False,'runtime_installed':False,'manual_complete_wheel_pending':True,'quota_exhaustion_observed':False},indent=2)+'\n',encoding='utf-8')
files=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json'];assert sum(f['bytes'] for f in files)<8*1024**2;(out/'DELIVERY_SEAL.json').write_text(json.dumps({'files':files,'later_account_receipts_are_additive':True},indent=2)+'\n',encoding='utf-8');print(json.dumps({'scopes_verified':len(verified),'scope_entries_verified':sum(r['verified_entries'] for r in verified),'delivery_files':len(files),'delivery_seconds':elapsed,'agents_suffix_exact':True}))