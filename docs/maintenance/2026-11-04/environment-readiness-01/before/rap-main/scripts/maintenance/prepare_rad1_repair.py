"""Prepare disclosed RAD1 degeneracy repair before evaluator GT is read."""
from pathlib import Path
import json

MAIN=Path(__file__).resolve().parents[2]
ROOT=MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01'
SLAM=MAIN.parent/'RAP-SLAM'
NEW=ROOT/'attempt-02'
assert not (ROOT/'outcomes.json').exists()
assert not NEW.exists()
NEW.mkdir()
source=(ROOT/'measurement_association_source.py').read_text()
source=source.replace('u, _, vt = np.linalg.svd(a.T @ b)', '''u, spectrum, vt = np.linalg.svd(a.T @ b)
    sign = 1 if np.linalg.det(vt.T @ u.T) >= 0 else -1
    # Twice this quantity is the Horn objective's top eigenvalue gap.
    gap = 2*(spectrum[1]+sign*spectrum[2])
    if spectrum[0] <= 1e-12 or gap <= 1e-6*spectrum[0]:
        return None''')
(NEW/'measurement_association_source.py').write_text(source)
(SLAM/'scripts/measurement_association_v2.py').write_text(source)
driver=(MAIN/'scripts/maintenance/raw_association_decoder.py').read_text()
driver=driver.replace("BASE = MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01'", "BASE = MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01/attempt-02'")
driver=driver.replace('import measurement_association as alg','import measurement_association_v2 as alg')
driver=driver.replace('validate_raw_association_decoder.py','validate_raw_association_decoder_v2.py')
driver=driver.replace("SLAM/'scripts/measurement_association.py'", "SLAM/'scripts/measurement_association_v2.py'")
driver=driver.replace("files.append(BASE/'manifest.json')", "files += [BASE/'manifest.json',BASE.parent/'freeze.json',BASE.parent/'bank_seal.json',BASE.parent/'FAILURE_validation_bank.json',BASE.parent/'AMENDMENT_01.md']")
driver=driver.replace("assert alg.fit(line,line) is None and alg.fit(line[:2],line[:2]) is None", """assert alg.fit(line,line) is None and alg.fit(line[:2],line[:2]) is None
    triangle=np.array([[0.,0,0],[1,0,0],[0,1,0]])
    crossed_source=np.repeat(triangle,3,axis=0);crossed_target=np.tile(triangle,(3,1))
    assert alg.fit(crossed_source,crossed_target) is None""")
driver=driver.replace('p,line=line,duplicate=duplicate', 'p,line=line,crossed_source=crossed_source,crossed_target=crossed_target,duplicate=duplicate')
(MAIN/'scripts/maintenance/raw_association_decoder_v2.py').write_text(driver)
validator=(MAIN/'scripts/maintenance/validate_raw_association_decoder.py').read_text()
validator=validator.replace("BASE=MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01'", "BASE=MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01/attempt-02'")
validator=validator.replace('_,vectors=np.linalg.eigh(N);w,x,y,z=vectors[:,-1]', '''values,vectors=np.linalg.eigh(N)
    scale=np.linalg.svd(S,compute_uv=False)[0]
    if scale<=1e-12 or values[-1]-values[-2]<=1e-6*scale:return None
    w,x,y,z=vectors[:,-1]''')
validator=validator.replace("assert horn(z['line'],z['line']) is None and horn(z['line'][:2],z['line'][:2]) is None", """assert horn(z['line'],z['line']) is None and horn(z['line'][:2],z['line'][:2]) is None
            assert horn(z['crossed_source'],z['crossed_target']) is None""")
(MAIN/'scripts/maintenance/validate_raw_association_decoder_v2.py').write_text(validator)
protocol=(ROOT/'PROTOCOL.md').read_text()
protocol=protocol.replace('# RAD1:', '# RAD1 attempt-02:')
protocol=protocol.replace('Fit original source->target points by proper unweighted Kabsch.', '''Before every fit, additionally reject a nonunique/ill-conditioned proper
rotation objective. Let s0>=s1>=s2 be cross-covariance singular values and
sign=det(V U^T). Reject s0<=1e-12 or Horn top eigengap
2*(s1+sign*s2)<=1e-6*s0. The independent Horn implementation checks the
actual top two eigenvalues. The relative1e-6 degeneracy tolerance is inherited
from the original fit's rank check; it is not selected using GT.
Fit original source->target points by proper unweighted Kabsch.''')
protocol=protocol.replace('nondegenerate wrong2m observation mismatch', 'individually noncollinear but cross-covariance-degenerate rejection,\nnondegenerate wrong2m observation mismatch')
protocol+='\n## Disclosed implementation repair\n\nRead ../AMENDMENT_01.md and ../FAILURE_validation_bank.json. Original freeze,\nall200 NPZs and all original sources remain unchanged and INCOMPLETE. This\nversion repairs an omitted rigid-objective uniqueness check in every arm.\nIt reruns all200 pairs; no old prediction is silently replaced or reused as\na repaired result. All cohorts, associations, budgets, selectors, scientific\ngates and evaluator remain unchanged. GT has not been parsed before repair.\nFreeze the amendment and original freeze/bank-seal/failure identities too.\n'
(NEW/'PROTOCOL.md').write_text(protocol)
(NEW/'STATUS.json').write_text(json.dumps(dict(stage='RAD1',attempt=2,status='PREPARING_NOT_FROZEN',gt_read=False),indent=2)+'\n')
print('Separate attempt-02 sources prepared; scientific gates unchanged')
