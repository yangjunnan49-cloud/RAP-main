"""Disclosed validator-only PFG1 repair, preserving frozen source and bank."""
from pathlib import Path
import json
MAIN=Path(__file__).resolve().parents[2];S=MAIN/'scripts/maintenance';ROOT=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';ATT=ROOT/'attempt-02'
ATT.mkdir()
failure=json.loads((ROOT/'FAILURE_validation_bank.json').read_text());assert failure['error']=='AssertionError()'
def write(p,text):
    with p.open('x',encoding='utf-8') as f:f.write(text)
driver=(S/'geometric_information_screen.py').read_text()
old="BASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';BANK=BASE/'bank';EV=BASE/'evaluation'"
new="ROOTBASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';BASE=ROOTBASE/'attempt-02';BANK=ROOTBASE/'bank';EV=BASE/'evaluation'"
assert old in driver;driver=driver.replace(old,new)
driver=driver.replace("Path(__file__).with_name('validate_geometric_information_screen.py')","Path(__file__).with_name('validate_geometric_information_screen_v2.py')")
driver=driver.replace("save(BASE/'freeze.json',dict(utc=utc(),files=", "files += [ROOTBASE/'freeze.json',ROOTBASE/'bank_seal.json',ROOTBASE/'FAILURE_validation_bank.json',ROOTBASE/'AMENDMENT_01.md'] + [p for p in BANK.rglob('*') if p.is_file()]\n    for p,h in read(ROOTBASE/'freeze.json')['files'].items():assert sha(p)==h,p\n    save(BASE/'freeze.json',dict(utc=utc(),files=")
driver=driver.replace("seal=read(BASE/'bank_seal.json')","seal=read(ROOTBASE/'bank_seal.json')")
driver=driver.replace("sha(BASE/'bank_seal.json')","sha(ROOTBASE/'bank_seal.json')")
driver=driver.replace("choices=['freeze','bank','evaluate']","choices=['freeze','evaluate']")
write(S/'geometric_information_screen_v2.py',driver)
validator=(S/'validate_geometric_information_screen.py').read_text()
old="BASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';BANK=BASE/'bank'"
new="ROOTBASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';BASE=ROOTBASE/'attempt-02';BANK=ROOTBASE/'bank'"
assert old in validator;validator=validator.replace(old,new)
validator=validator.replace("seal=read(BASE/'bank_seal.json')","seal=read(ROOTBASE/'bank_seal.json')")
validator=validator.replace("sha(BASE/'bank_seal.json')","sha(ROOTBASE/'bank_seal.json')")
validator=validator.replace("seal['freeze_sha256']==sha(BASE/'freeze.json')","seal['freeze_sha256']==sha(ROOTBASE/'freeze.json')")
old="y=inv[:3,:3]@p[pi]+inv[:3,3];n=nj[qj];rowsJ.append(np.r_[np.cross(n,y),-n])"
new="y=T[:3,:3].T@(p[pi]-T[:3,3]);n=nj[qj];rowsJ.append(np.r_[np.cross(n,y),-n])"
assert old in validator;validator=validator.replace(old,new)
validator=validator.replace("loopcount=0;rows={}","loopcount=0;rows={};max_serialized_orth_error=0.;max_rigid_inverse_delta=0.")
needle="iq_to_ip=closest(qp,p);"
extra="rigid=np.eye(4);rigid[:3,:3]=T[:3,:3].T;rigid[:3,3]=-T[:3,:3].T@T[:3,3]\n            orth=float(np.max(abs(T[:3,:3].T@T[:3,:3]-np.eye(3))));max_serialized_orth_error=max(max_serialized_orth_error,orth);assert orth<1e-5\n            assert np.max(abs(rigid-gtsam.Pose3(T).inverse().matrix()))<1e-12\n            max_rigid_inverse_delta=max(max_rigid_inverse_delta,float(np.max(abs(rigid-np.linalg.inv(T)))))\n            iq_to_ip=closest(qp,p);"
assert needle in validator;validator=validator.replace(needle,extra)
validator=validator.replace("trajectory_deltas=rows,wall_s=", "trajectory_deltas=rows,max_serialized_orth_error=max_serialized_orth_error,max_rigid_vs_matrix_inverse_delta=max_rigid_inverse_delta,wall_s=")
old="read(BASE/'freeze.json')['utc']<read(BANK/'execution.json')['started_utc']<read(BASE/'bank_seal.json')['utc']"
new="read(ROOTBASE/'freeze.json')['utc']<read(BANK/'execution.json')['started_utc']<read(ROOTBASE/'bank_seal.json')['utc']"
assert old in validator;validator=validator.replace(old,new)
validator=validator.replace("assert result['bank_validation_seal_sha256']==", "assert read(BASE/'freeze.json')['utc']<read(BASE/'bank_validation.json')['utc']\n    assert result['bank_validation_seal_sha256']==")
write(S/'validate_geometric_information_screen_v2.py',validator)
write(ROOT/'AMENDMENT_01.md',"""# PFG1 amendment01: independent rigid-inverse reconstruction

Before evaluator GT, the original independent bank validator failed on the
first00 edge's H comparison. Original170-identity freeze, algorithm/driver/
validator, complete bank/seal, failure and root INCOMPLETE remain immutable.

Diagnosis on the sealed inputs: native serialized R has orthogonality defect
3.478373e-7. General4x4 inverse differs from the frozen algorithm's rigid inverse
R^T(p-t), also used by native GTSAM Pose3.inverse. H max delta0.142773 and
relative normalized-entry delta2.724791e-6; rigid-transpose reconstruction
reproduces original H exactly. This is a validator convention mismatch on
rounded native matrices. These are nominal rigid-transform Jacobians; an exact
derivative interpretation at the nonorthogonal serialized matrix is not claimed.

Separate attempt-02 freezes new protocol/driver/validator plus every original
source/bank identity before retry. Only the validator's reverse-point inverse
changes to the frozen rigid inverse. All58 poses must have orthogonality error
below the existing1e-5 SE3 tolerance and reproduce native Pose3.inverse to1e-12;
record general-inverse disagreement. No bank/model rerun, eigenvalue/normal/
match change, tolerance relaxation, cohort, gate, pose or acceptance edit.

Evaluator driver v2 only redirects output and validation dependency to the
separate attempt. It cannot generate a replacement bank. Original matrices/
trajectories remain exactly sealed. Evaluation proceeds only after separately
frozen independent retry validation. No GT value has been used in this repair.
""")
write(ATT/'PROTOCOL.md',(ROOT/'PROTOCOL.md').read_text()+"""

## Attempt-02 validator-only repair

AMENDMENT_01 records the source/evaluator boundary and preserved failure.
Use the original complete bank unchanged. New freeze includes all original
bank/source hashes, amendment and separate v2 source. Independent rigid inverse
is R^T(p-t), verified against native Pose3 for every original loop, with the
existing1e-5 serialized-SE3 tolerance. No exact physical derivative/covariance
claim at a nonorthogonal rounded serialization. All previous numerical/scientific
gates unchanged. Root INCOMPLETE describes the invalid original validation;
only attempt-02 may supply a validated result. No replacement bank is generated.
""")
print('PFG1 validator-only attempt02 prepared; originals preserved')
