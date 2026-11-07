"""Document completed visual scopes and preserve the exact previous handoff."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DAY = ROOT.parent
REPO = ROOT.parents[3]
VR = DAY / 'visual-baseline-reachability-01'


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def text(p, value):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(value)


now = dt.datetime.now(dt.timezone.utc)
rows = load(VR/'controls/ROWS.json')
groups = load(VR/'controls/SUMMARY.json')['groups']
assert len(rows) == 200 and len(groups) == 19
unavailable = [r for r in rows if r['historical_N_category'] == 'proposal_unavailable']
assert len(unavailable) == 64 and sum(r['visual_joint_5_15'] for r in unavailable) == 1
accepted = [r for r in rows if r['historical_N_category'] == 'correct_accepted']
assert len(accepted) == 40 and sum(not r['visual_pose'] for r in accepted) == 21
receipt = load(VR/'controls/HOST_EXIT.json')
assert receipt['passed'] and receipt['no_live_owned_process']
inclusive = (now-dt.datetime(2026,10,28,7,22,18,tzinfo=dt.timezone.utc)).total_seconds()
assert inclusive < 900
text(VR/'REPORT.md', '''# Complete visual/historical-proposal categorical join

All200 existing pair IDs and19 complete groups are retained. Of64 historical native-N proposal-unavailable positives (00:23;08:41), camera5DoF emits only two outputs, both00. One of00's23 enters the pre-frozen5/15-degree bin; none of08's41 does. This is one ID intersection, not recovery of a missing metric6DoF/RAP pose. The frames, quantities and criteria remain distinct.

| Historical positive category |00 pairs / visual poses /5-15 bin|08 pairs / visual poses /5-15 bin|
|---|---|---|
| Correct accepted |23 /19 /15|17 /0 /0|
| Correct rejected |26 /8 /6|13 /0 /0|
| Selection miss |3 /1 /1|4 /0 /0|
| Correct proposal unavailable |23 /2 /1|41 /0 /0|

All25 confusers per sequence remain and yield no visual pose. All11 historical incorrect-accepted overlay IDs also have no visual pose, but21 of40 historically correct-accepted IDs likewise have no visual pose. Therefore lack of this visual evidence cannot be adopted as a safe old-registration veto or as an incorrectness label. These exposed categorical counts do not calibrate a classifier.

CF1 both-zero finite-frustum source-LiDAR upper support is84/200 (00:28;08:56, including confusers); original75 positives remain15/42. All30 visual outputs fall in the remaining116 IDs, but42 of00's72 and all44 of08's44 not-both-zero IDs still lack a visual pose. Projected source-LiDAR support is not measured visibility/correspondence or a sufficient visual-pose condition. Do not select that support subset or infer image-only impossibility.

The present result provides limited camera5DoF information on00, with only one strict-bin intersection among64 old missing-proposal IDs and no evidence on08. It does not justify training, RAP increment, a general rejector or an automatic system integration. A distinct source-depth-association feasibility question can determine whether a full-cohort ordinary PnP comparison is implementable; it must not claim true correspondences or metric pose recovery merely from nearest projected-point associations. Any such next numerical diagnostic needs a separate complete source/resource freeze and controls. No new pose solver is executed by this review.

Worker uses saved JSON only; no new angles/pose/feature/model/point/image computation. SOURCE_FREEZE binds all inputs/code. The prospective absolute-path host adaptation is separately bound in HOST_RUNNER_FREEZE; no worker/scientific changes or failed stage launch were needed. The copied launcher's 'VB1 controls PASS' string refers only to this folder's JSON join. Original VB1 remains failed. Research UNRESOLVED/manuscript PAUSED; old failures/caps/source limitations unchanged.
''')
save(VR/'CLOSE_CHECKS.json', {'utc':now.isoformat(),'complete_pairs':200,'groups':19,
    'inclusive_seconds':inclusive,'cap_seconds':900,'cap_pass':True,
    'worker_elapsed_seconds':receipt['elapsed_seconds'],'worker_peak_bytes':receipt['child_lifetime_peak_bytes'],
    'owned_child_reaped':True,'no_new_raw_image_pose_feature_model_computation':True})
files = [{'path':p.relative_to(VR).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(VR.rglob('*')) if p.is_file()]
save(VR/'DELIVERY_SEAL.json', {'utc':now.isoformat(),'files':files})
prior = (REPO/'AGENTS.md').read_bytes()
assert prior == (DAY/'visual-baseline-execution-01/AGENTS.before.md').read_bytes()
with (ROOT/'AGENTS.before.md').open('xb') as f:
    f.write(prior)
header = '''# October28 explicit continuation: complete actual-image baseline, limited reach

Owner explicitly renews project work until current5h quota exhaustion. Read docs/maintenance/2026-10-28/project-continuation-02/AUTHORITY.md, CLOSED_SCOPES.json, visual-essential-refinement-01/REPORT.md, STATUS.json, RESOURCE_AUDIT.json and DELIVERY_SEAL.json; visual-baseline-reachability-01/REPORT.md. Earlier documentary-only/no-actual-image-algorithm prose is historical. This current explicit request is not automatic reset resume. Latest saved66%/ordinaryTRUE/reset1793187718 followed07:20:18UTC is availability, not exhaustion; later actual account receipts govern. No inferred prior boundary/cause, scheduler or goal-status action.

Actual ER1 complete273 original images/all200 pairs: SIFT features, initial ordinary calibrated-essential and distinct robust5DoF refit predictions all sealed before supplied-reference evaluation.30/200 pose outputs, all00;08=0/100;170 explicit no-evidence. Frozen descriptive5/15-degree joint bin23/200,10/30 bin24/200. Refit slightly improves medians but worsens both means and adds no bin successes; no overall gain claim. Camera rotation/signed unit translation only, no metric scale/full metric6DoF/raw-corrected rigid equivalence/RAP increment/physical/generalization authentication.

Original VB1 synthetic raw-RANSAC outlier gate FAIL retained (rotation0.1131463deg vs0.1); CD1 analytic0.2deg/within1px certificate and13 interface controls complete, not a reversal. Distinct prospectively frozen ER1 robust refit passes23 controls with same fixture/seed/gates. Cold ASCII then NumPy.ma integration failures preserved; final cold full-path pass, seven complete NPZs byte-preserved/two+five early-return records reconstructed, only193 missing pairs computed. Original math/input/parameters/caps retained; metadata-assertion and audit-read-set corrections explicit. Full273cache/200pair audit passes6308 independent clear distance checks,6 ambiguous retained;200Decimal60 reference transforms,564 refit trace steps/720 independent costs. All owned children exited/reaped. Prediction all attempts+cold controls24.1268335/300s, scientific children72.9864813s, max successful peak326406144bytes; ER1 dossier~303.3MB/1GiB. Failed-child self-peaks UNKNOWN; original host-polled receipts retained.

VR1 complete200-ID categorical join: old native-N missing-correct-proposal64 IDs yield two visual outputs, only one in5/15 bin (00:1/23;08:0/41). This is an ID intersection, not metric-pose rescue. No visual pose also affects21/40 historically correct accepted IDs, so absence is not a rejection rule. All200/allstrata/confusers and CF1 source-LiDAR support roles retained. Source-depth-association feasibility may be prepared as a separate bounded no-pose diagnostic; it is not yet executed/admitted by this header. Do not rerun any closed source/download/install/visual stages or tune parameters/seeds/subsets to rescue them.

No new RAP training; SR1~1.98% fitting-only loss decrease/all4noiseFAIL, HFIT0INCOMPLETE/original2GiB stop and all old native/joint/equivalence/provenance failures/caps remain. ResearchUNRESOLVED/manuscriptPAUSED. No existing-environment/install/WSL startup/default/production/Git writes/outreach/scheduler/goal-status changes. Both repository HEADs and tracked2/9dirty sets inspected unchanged; remote sync unchecked. Earlier AGENTS exact bytes backed up in project-continuation-02 and retained verbatim below. Later additive current handoffs supersede this checkpoint only where actual receipts say so.

---

'''
(REPO/'AGENTS.md').write_bytes(header.encode('utf-8')+prior)
save(ROOT/'AGENTS_CHECKPOINT_PROOF.json', {'utc':now.isoformat(),'previous_bytes':len(prior),'previous_sha256':hashlib.sha256(prior).hexdigest(),
    'prior_exact_suffix_retained':(REPO/'AGENTS.md').read_bytes().endswith(prior),'new_sha256':sha(REPO/'AGENTS.md')})
text(DAY/'PHASE_RECORD_CONTINUATION_02.md', '''# 2026-10-28 explicit continuation, completed visual-baseline checkpoint

VB1 implementation/source/input freeze complete; sole raw-outlier control FAIL before real images. CD1 synthetic-only interface and consensus-certificate primary complete; later report explicitly additive. Distinct ER1 robust geometric refit complete:273 images,200 initial/final predictions sealed before supplied-reference evaluation,30 outputs/all00,23/200 in5/15 descriptive bin,08 none. Initial/refit means worsen, bins unchanged; no overall gain/RAP increment/metric scale. All failures, cold-import corrections, seven preserved outputs, resource caps and independent audits recorded in the ER1 report/seal.

VR1 complete saved-output categorical join: one strict-bin ID intersection among64 old missing-correct-proposal IDs;21/40 old correct-accepted IDs have no visual pose, so no absence veto. All200/strata/confusers/source-support distinctions retained. Research UNRESOLVED/manuscript PAUSED; no new training or old failure/cap reset. The old PHASE_RECORD.md snapshot is unchanged. Read project-continuation-02 and actual later scope/account receipts for current continuation; no automatic reset resume or background worker.
''')
print('VR1 sealed; exact previous AGENTS retained; visual checkpoint recorded')
