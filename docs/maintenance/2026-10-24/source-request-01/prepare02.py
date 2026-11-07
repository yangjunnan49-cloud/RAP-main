"""Bind an already acquired upstream URL, without opening any socket."""
import csv,datetime,hashlib,io,json
from pathlib import Path
root=Path(__file__).resolve().parent;day=root.parent
repo=root.parents[3];old=day.parent/'2026-10-15/official-demo-metadata-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def write(n,v):
    with (root/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False)
expected=[
 (day.parent/'2026-10-16/regx-reference-package-01/transfer-01/06-01.body',555,'9597E5011197164C84913E3FBB276AE0706A984E88254212A27F15606DC828DF','127f60b32a67b2ab202537dc92b4970ce69508e9'),
 (old/'payload/007.body',17182,'708622BEDA10DE4AFC724247118B0D25D80CD993A3C197CE65088E5B047721AF','aed92202b2dab377a671c475c94093fca16c4600'),
 (old/'payload/008.body',11667,'64EFBFFA78F74868B3EC6D8AE7CD4FB5B33D4BD08C6843DD0361C89B62C5BE78','5ac6bf4f3f57b78f3506b2a3d2a7f44b37b85c31')]
frozen=[]
for p,n,h,g in expected:
    b=p.read_bytes();assert len(b)==n and sha(p)==h and blob(b)==g
    frozen.append(dict(path=str(p.relative_to(repo)),bytes=n,sha256=h,published_Git_blob_SHA1=g))
metadata=expected[0][0].read_text(encoding='utf-8');assert 'source_dataset: PARISLUCO' in metadata
rows=list(csv.reader(io.StringIO(expected[1][0].read_text(encoding='utf-8'))))
selected=[r for r in rows if r and r[0]=='PARISLUCO'];assert len(selected)==1
row=selected[0];assert row[2]=='https://npm3d.fr/parisluco3d'
assert row[4]=='sanchez2023arxiv-parisluco' and 'citation: '+row[4] in metadata
lines=expected[2][0].read_text(encoding='utf-8').splitlines()
hits=[(i+1,s) for i,s in enumerate(lines) if row[2] in s];assert len(hits)==1
write('SOURCE_POINTER.json',dict(passed=True,source_files=frozen,upstream_project_URL=row[2],
    dataset_token=row[0],published_name=row[1],citation_token=row[4],
    attribution_line=hits[0][0],attribution_literal=hits[0][1],
    source_pointer_authenticated_as_author_metadata=True,upstream_page_fetched=False,
    upstream_acquisition_or_physical_truth_authenticated=False,exact_RegX_to_upstream_crosswalk='UNKNOWN'))
write('REQUEST_PLAN.json',dict(status='PREPARED_AWAITING_EXPLICIT_OWNER_AUTHORIZATION',
    object=dict(method='GET',url=row[2],purpose='Read upstream dataset acquisition/reference description and identify original records'),
    allowed_hosts=['npm3d.fr','www.npm3d.fr'],HTTPS_only=True,max_requests=4,max_redirects=3,
    cumulative_delivered_body_cap_bytes=262144,whole_attempt_seconds=120,
    network_worker_deadline_seconds=60,output_dossier_cap_bytes=2097152,worker_RSS_cap_bytes=134217728,
    original_fresh_host_commit_guard_bytes=12884901888,host_guard_max_age_seconds=2,
    follow_links=False,PDF_or_archive_or_raw_or_pose_or_weight_or_script_acquisition=False,
    retries=False,credentials_or_cookies=False,install_or_outreach=False,
    EOF_and_identity_encoding_required_for_admission=True,
    request_and_every_response_header_body_prefix_and_failure_receipt_retained=True,
    body_budget_is_application_delivered_bytes_not_TLS_wire_or_internal_buffers=True,
    no_automatic_inference_or_efficacy_admission=True,
    separate_prospective_scope_required_after_authorization=True))
for p,n,h,g in expected:assert sha(p)==h
start=datetime.datetime(2026,10,24,7,32,30,tzinfo=datetime.timezone.utc)
elapsed=(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()
write('COSTS_FINAL.json',dict(status='EXACT_UPSTREAM_SOURCE_POINTER_AND_REQUEST_PREPARED_NO_NETWORK',
    elapsed_seconds=elapsed,cap_seconds=600,budget_status='PASS' if elapsed<=600 else 'FAIL',
    original_UTC_origin=start.isoformat(),network_requests=0,old_caps_reset=False))
print(json.dumps(dict(passed=True,source_files=3,url=row[2],network_requests=0,elapsed_seconds=elapsed)))
