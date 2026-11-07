"""Verify, update additive authority and close the finite round before quota."""
import ast,datetime,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;REPO=ROOT.parents[3]
OLD=DAY.parent/'2026-10-24'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8'))
for n,h in freeze['files'].items():assert sha(ROOT/n)==h
assert sha(Path(freeze['proposal_path']))==freeze['proposal_sha256']
assert sha(Path(freeze['source_pointer_path']))==freeze['source_pointer_sha256']
prior_path=OLD/'continuation-02/CLOSED_SCOPES_WITH_SOURCE_REQUEST.json'
prior=json.loads(prior_path.read_text(encoding='utf-8'));assert prior['scope_count']==12
for r in prior['scopes']:assert sha(OLD/r['scope']/'COSTS_FINAL.json')==r['sha256']
packages={
 'delivery-audit-01/RAP_public_functional_20261024.zip':'BBF7FCB2A87DBA232666F4B4B6D269A55460E2E39960E4BBD6A5996FBD254A85',
 'pose-convention-01/RAP_5_case_local_matrices_20261024.zip':'C7A1C4411ACB59A5994D58637D3A8F6C1D9D71186A18A3103A3549D41DD83AAB',
 'handoff-03/RAP_20261024_source_review_and_figures.zip':'3095B9068E67B034C4B32661F61E56D6BD7DBD9E8DC433A1F934C6DD83DB4BDD'}
for n,h in packages.items():assert sha(OLD/n)==h
code=json.loads((OLD/'real-interface-02/CODE_BINDINGS.json').read_text(encoding='utf-8'))
for r in code:assert sha(Path(r['path']))==r['sha256']
result=json.loads((ROOT/'run01/RESULTS.json').read_text(encoding='utf-8'))
host=json.loads((ROOT/'run01/HOST_EXIT.json').read_text(encoding='utf-8'))
worker=json.loads((ROOT/'run01/WORKER_EXIT.json').read_text(encoding='utf-8'))
assert result['passed'] and worker['success'] and host['exit_code']==0 and host['no_live_owned_process']
assert result['requests']==len(worker['all_request_rows'])==1
assert sum(r['body_bytes'] for r in worker['all_request_rows'])==result['cumulative_delivered_body_bytes']==12443
assert result['redirects_followed']==result['hyperlinks_followed']==result['retries']==0
assert sha(ROOT/'run01'/result['final_body'])==result['final_body_sha256']
assert host['elapsed_seconds']<120 and worker['elapsed_seconds']<60
assert max(host['observed_native_peak_working_set_bytes'],worker['peak_working_set_bytes'])<=134217728
pre=json.loads((ROOT/'run01/PREFLIGHT.json').read_text(encoding='utf-8'))
assert pre['headroom_bytes']>=12884901888 and pre['query_seconds']<=2
for r in worker['all_request_rows']:
    assert r['EOF'] and r['status']==200
    assert not any(k.lower() in ('cookie','authorization') for k in r['request_headers'])
    assert sha(ROOT/'run01'/r['body_file'])==r['body_sha256']
platform=json.loads((ROOT/'PLATFORM_CHECKS.json').read_text(encoding='utf-8'))
assert platform['passed'] and platform['WSL_started_by_this_round'] is False and platform['observed_Stopped'] is True
classifier=DAY.parent/'2026-10-23/account-boundary-02'
cf=json.loads((classifier/'SOURCE_FREEZE.json').read_text(encoding='utf-8'))
assert sha(classifier/'account_classifier.py')==cf['account_classifier.py']
sys.path.insert(0,str(classifier))
from account_classifier import classify,extract
account_raw=json.loads((ROOT/'PRE_CLOSE_ACCOUNT_OBSERVATION.json').read_text(encoding='utf-8'))
account=classify(extract(account_raw['usage_tool_result']),1792911572)
assert account['ordinaryUsageAllowed'] is True and account['usedPercent']<100 and account['status']=='ACTIVE'
write(ROOT/'ACCOUNT_CLASSIFICATION.json',dict(classification=account,
    following_clock=account_raw['following_clock'],round_closure='OWNER_REQUESTED_PRE_QUOTA_CLOSEOUT',
    account_exhaustion_observed=False,account_active_does_not_mean_round_pending=True))
pending=OLD/'continuation-02/AWAITING_SOURCE_AUTHORIZATION.json'
write(ROOT/'AUTHORIZATION_RESOLUTION.json',dict(old_pending_record=str(pending.relative_to(REPO)),
    old_pending_record_sha256=sha(pending),old_record_unchanged=True,
    superseded_for_fixed_project_page_only=True,actual_owner_authorization='AUTHORIZATION.json',
    authorized_read_completed=True,requests=1,linked_objects_not_authorized_or_read=True,
    current_owner_direction='CLOSEOUT_DIRECTION.json',pending_real_computation=False,pending_permission_question=False))
previous=(REPO/'AGENTS.md').read_bytes()
with (ROOT/'AGENTS.before.md').open('xb') as f:f.write(previous)
header='''# October25 authorized upstream source read and pre-quota closeout

Owner authorized the exact fixed ParisLuco3D project page, then explicitly requested closing this round before the5h quota is exhausted. Read docs/maintenance/2026-10-25/upstream-page-01/REPORT.md, FINAL_STATUS.json and NEXT_PLAN.md. PP1 completes one GET/12443 application body bytes/HTTP200/EOF,0 redirects/links/retries/linked downloads. Main HTML SHA256 B8A828DD1DCFD039A565E191EFE19DE79389C02F8812413017DD3BE0B5034A59. Transport3.380245/120s, worker2.0/60s and29573120-byte peak pass the frozen limits; original fresh12GiB/2s host gate retained, owned process exited. Prior awaiting-page authorization is superseded only by this dated authorization/result; old files remain unchanged.

The captured page establishes the upstream dataset's cross-domain LiDAR-perception role and points details to readme/creation paper. It does not authenticate the exact3RegX derivative mapping, physical registration/reference/frame/timing quality, reserved cohort or checkpoint exclusion. No links were followed; no raw/private/reference/model/pose/fit/metric work. Physical efficacy NOT_ADMITTED, research UNRESOLVED/manuscript PAUSED, every old family/cap/failure/stop remains.

This round is CLOSED by owner direction before quota exhaustion; current actual quota/finite cost and ZIP verification are in FINAL_STATUS/COSTS_FINAL/ZIP_CHECKS. Pre-close13%/ordinaryTRUE/reset1792911572 at02:04:52UTC is NOT exhaustion. No blanket renewed until-exhaustion request, pending payload/permission, automatic reset resume or scheduler/goal-status change. WSL was not started and remains observedStopped; E VHD/backup/Junction and.wslconfig are retained, direct boot without link untested. Local HEADs/source hashes/12previous closed costs/3immutable ZIPs match; no Git/default/production/install/outreach change. All earlier AGENTS bytes follow verbatim and are backed up locally.

---

'''
with (ROOT/'AGENTS_ADDED_HEADER.md').open('x',encoding='utf-8') as f:f.write(header)
(REPO/'AGENTS.md').write_bytes(header.encode()+previous)
assert (REPO/'AGENTS.md').read_bytes().endswith(previous)
phase=DAY/'PHASE_RECORD.md'
phase_before=phase.read_bytes() if phase.exists() else b''
if phase_before:
    with (ROOT/'PHASE_RECORD.before.md').open('xb') as f:f.write(phase_before)
phase_add=b'''# October25 finite authorized source read and owner closeout

The owner explicitly authorized only the fixed project-page envelope, then requested closing before5h quota exhaustion. PP1 one GET/12443bytes/HTTP200/identity UTF-8/EOF,0redirects/links/retries. Raw body SHA256 B8A828DD1DCFD039A565E191EFE19DE79389C02F8812413017DD3BE0B5034A59. Transport3.380245/120s, worker2.0/60s,29573120-byte native self-peak<128MiB, fresh12GiB/2s guard and nonce lease pass. No other object or credential/cookie use. Original response cookie headers remain local; archive derivatives redact their values.

Four page claims bound to captured text lines. Upstream perception-evaluation role obtained; exact RegX derivative/reference/acquisition/units/time/pose-quality mapping and independent cohort remain unauthenticated. No linked readme/paper/data or real model/metric/pose work admitted. Physical efficacy NOT_ADMITTED, research UNRESOLVED/manuscript PAUSED; all old caps/failures/stops remain.

Twelve previous closed costs,three immutable packages and original source/config hashes match; AGENTS update additive with byte-exact backup. WSL not started, observedStopped, E image/backup/Junction/configuration retained; direct boot without link untested. HEADs unchanged/no remote check. Round closes on owner's pre-quota instruction, not exhaustion. Pre-close13%/ordinaryTRUE at02:04:52UTC; FINAL_STATUS governs final receipt. No pending payload/permission or automatic reset continuation; no scheduler/goal-status change.
'''
phase.write_bytes(phase_before+(b'\n\n' if phase_before else b'')+phase_add)
write(ROOT/'CLOSE_CHECKS.json',dict(passed=True,prior_closed_costs_verified=12,
    prior_immutable_package_hashes=packages,source_config_hashes_verified=len(code),
    original_source_runtime_freeze_matches=True,transport_bounds_and_complete_body_pass=True,
    no_live_owned_process=True,platform_passed=True,old_AGENTS_verbatim_suffix=True,
    old_AGENTS_sha256=hashlib.sha256(previous).hexdigest().upper(),
    no_actual_account_limit_observed=True,no_pending_payload_or_permission=True))
for p in ROOT.rglob('*.json'):json.loads(p.read_text(encoding='utf-8'))
for p in ROOT.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
def sanitized(v):
    if isinstance(v,list):
        if len(v)==2 and isinstance(v[0],str) and v[0].lower()=='set-cookie':return [v[0],'[REDACTED: response cookie not used]']
        return [sanitized(x) for x in v]
    if isinstance(v,dict):return {k:sanitized(x) for k,x in v.items()}
    return v
sources={}
for p in ROOT.rglob('*'):
    if not p.is_file() or p.name in ('AGENTS.before.md','PHASE_RECORD.before.md'):continue
    if 'ACCOUNT_OBSERVATION' in p.name:continue
    if p.suffix=='.zip':continue
    sources[str(p.relative_to(REPO)).replace('\\','/')]=p
sources[str(phase.relative_to(REPO)).replace('\\','/')]=phase
manifest={};payloads={}
for name,p in sorted(sources.items()):
    raw=p.read_bytes();data=raw
    if p.suffix=='.json':
        obj=json.loads(raw.decode('utf-8'));redacted=sanitized(obj)
        if redacted!=obj:data=json.dumps(redacted,indent=2).encode('utf-8')
    payloads[name]=data
    manifest[name]=dict(source_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest().upper(),
        archived_bytes=len(data),archived_sha256=hashlib.sha256(data).hexdigest().upper(),
        response_cookie_values_redacted=(data!=raw))
target=ROOT/'RAP_20261025_authorized_source_closeout.zip'
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in payloads.items():z.writestr(name,data)
    z.writestr('MANIFEST.json',json.dumps(dict(files=manifest,raw_cookie_receipts_remain_local_unchanged=True,
        raw_account_ID_receipts_and_historical_AGENTS_backup_excluded=True,
        final_cost_and_status_are_separate_post_verification_companions=True),indent=2))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None and set(z.namelist())==set(manifest)|{'MANIFEST.json'}
    for name,row in manifest.items():
        data=z.read(name);assert len(data)==row['archived_bytes'] and hashlib.sha256(data).hexdigest().upper()==row['archived_sha256']
        assert sha(sources[name])==row['source_sha256']
write(ROOT/'ZIP_CHECKS.json',dict(passed=True,file=target.name,bytes=target.stat().st_size,sha256=sha(target),
    members=len(manifest)+1,all_names_CRC_and_SHA256_verified=True,
    originals_unchanged=True,response_cookie_derivatives_explicitly_redacted=True))
elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime(2026,10,25,1,59,30,tzinfo=datetime.timezone.utc)).total_seconds()
write(ROOT/'COSTS_FINAL.json',dict(status='AUTHORIZED_PAGE_READ_AND_OWNER_REQUESTED_PRE_QUOTA_CLOSEOUT_COMPLETE',
    documentary_wrapper_elapsed_seconds=elapsed,documentary_wrapper_cap_seconds=600,
    budget_status='PASS' if elapsed<600 else 'FAIL',transport_whole_attempt_seconds=host['elapsed_seconds'],
    transport_whole_attempt_cap_seconds=120,worker_elapsed_seconds=worker['elapsed_seconds'],worker_cap_seconds=60,
    all_preparation_read_analysis_update_pack_verification_included=True,old_caps_reset=False))
write(ROOT/'FINAL_STATUS.json',dict(status='CLOSED_OWNER_REQUESTED_BEFORE_QUOTA_EXHAUSTION',
    latest_supplied_account_classification=account,following_clock=account_raw['following_clock'],
    actual_account_exhaustion_observed=False,owner_until_exhaustion_instruction_superseded_by_prequota_closeout=True,
    pending_real_computation=False,pending_external_acquisition=False,pending_permission_question=False,
    no_automatic_reset_resume=True,scheduler_or_goal_status_changed=False,
    fixed_page_authorization_fulfilled=True,source_reference_admission='PHYSICAL_EFFICACY_NOT_ADMITTED',
    research='UNRESOLVED',manuscript='PAUSED',WSL_started=False,WSL_observed_Stopped=True,
    E_VHD_backup_Junction_retained=True,final_finite_cost='COSTS_FINAL.json',delivery_verification='ZIP_CHECKS.json'))
all_files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in ROOT.rglob('*') if p.is_file() and p.name!='DELIVERY_SEAL.json'}
size=sum(r['bytes'] for r in all_files.values());assert size<=2097152
write(ROOT/'DELIVERY_SEAL.json',dict(files=all_files,total_dossier_bytes_before_this_small_seal=size,
    output_cap_bytes=2097152,old_costs_and_failures_unchanged=True,round_closed=True))
assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())<=2097152
print(json.dumps(dict(closed=True,wrapper_seconds=elapsed,transport_seconds=host['elapsed_seconds'],
    ZIP_bytes=target.stat().st_size,ZIP_sha256=sha(target),ZIP_members=len(manifest)+1,
    quota_usedPercent=account['usedPercent'],ordinaryUsageAllowed=account['ordinaryUsageAllowed'])))
