import datetime as dt
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


for e in load(ROOT/'SOURCE_FREEZE.json')['files']:assert sha(ROOT/e['path'])==e['sha256']
for e in load(ROOT/'controls/SEAL.json')['files']:assert sha(ROOT/'controls'/e['path'])==e['sha256']
rows=load(ROOT/'controls/ROWS.json');receipt=load(ROOT/'controls/HOST_EXIT.json');assert receipt['passed'] and receipt['no_live_owned_process']
missing=[r for r in rows if r['historical_N_category']=='proposal_unavailable'];assert len(missing)==64 and not any(r['PnP_pose'] for r in missing)
now=dt.datetime.now(dt.timezone.utc);seconds=(now-dt.datetime(2026,10,28,12,55,44,tzinfo=dt.timezone.utc)).total_seconds();assert seconds<900
with (ROOT/'REPORT.md').open('x',encoding='utf-8') as f:f.write('''# MR1 complete categorical result: no new missing-proposal ID covered by PnP

All200 pair IDs and all native-N partitions/strata are retained. PR1's17 camera-metric outputs comprise15 historically correct-accepted00 IDs and two correct-rejected00 IDs. None is in the old64 missing-correct-proposal IDs (00:23;08:41), and none is a selection-miss ID. All17 were already ER1 camera5DoF output IDs. This is an exposed ID join, not a direct pose-metric comparison with old native-N/corrected-LiDAR geometry.

PR1 has14 in the pre-frozen camera R5/d15 bin;13 overlap ER1's23 and one does not. That extra bin ID is historically correct-rejected, not proposal-unavailable. A post-hoc union would be an oracle set calculation using supplied-reference errors, not an operational fusion rule. Do not construct a selector from it or declare RAP gain.

The depth observations produce metric-camera estimates for a limited already-supported00 region, not new coverage of the original missing-proposal failure.27/40 old correct-accepted IDs also lack PnP output (8 of23 in00,all17 in08); absence is not a safe rejection rule. Both camera methods fail to supply08 evidence in this cohort. All200/no-evidence/confuser and exact frame/metric roles remain.

No new point, pixel, pose solver/model/training or angle/error metric was computed. This result does not justify automatic RAP training/coupling or parameter/model/subset rescue. Retain the ordinary-camera engineering deliverables and complete a source-level public raw-input/frame/API admission review before any integration. In raw coordinates, supplied extrinsics permit the declared affine action Tr_j^-1*Tcam*Tr_i; the old point-dependent correction is not a constant SE3, and the existing custom normalization contract is not authentication of a canonical RAP input/output API. Review existing real backend source, not a new unrelated normalization prototype. ResearchUNRESOLVED/manuscriptPAUSED; all old failures/caps remain.
''')
save('CLOSE_CHECKS.json',{'utc':now.isoformat(),'complete_pairs':200,'historical_missing_proposals':64,'PnP_outputs_in_missing_IDs':0,
    'inclusive_seconds':seconds,'cap_seconds':900,'cap_pass':True,'worker_receipt':receipt,'no_new_scientific_payload':True})
files=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()]
save('DELIVERY_SEAL.json',{'utc':now.isoformat(),'files':files})
print('MR1 sealed; no PnP coverage among64 missing IDs')
