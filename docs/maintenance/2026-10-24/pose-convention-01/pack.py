"""Annotate existing pose exports only; no numerical transform operation."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent
source=DAY/'output-contract-01/run02/verify';r=json.loads((source/'RESULTS.json').read_text());assert len(r['exports'])==5
note=(DAY/'continuation-01/TRANSFORM_CONVENTION.md').read_bytes()
rows=[]
for e in r['exports']:
    p=source/e['file'];raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest().upper();assert digest==e['sha256']
    rows.append(dict(file=e['file'],bytes=len(raw),sha256=digest,case=e['case'],view=e['view'],direction='original_view_to_case_local_common',no_cross_case_gauge_alignment=True))
meta=dict(estimated_only=True,not_a_global_trajectory=True,case_groups={'case-000':[0,1],'case-001':[0,1,2]},input_units_not_independently_authenticated=True,files=rows)
archive=ROOT/'RAP_5_case_local_matrices_20261024.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('README.md',note);z.writestr('_MANIFEST.json',json.dumps(meta,indent=2))
    for row in rows:z.write(source/row['file'],row['file'])
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==7 and z.read('README.md')==note
    for row in rows:assert hashlib.sha256(z.read(row['file'])).hexdigest().upper()==row['sha256']
with (ROOT/'CHECKS.json').open('x') as f:json.dump(dict(passed=True,matrices_unchanged=5,members=7,ZIP_bytes=archive.stat().st_size,ZIP_sha256=hashlib.sha256(archive.read_bytes()).hexdigest().upper(),old_packages_untouched=True,new_pose_computations=0,case_local_frames_explicit=True),f,indent=2)
print((ROOT/'CHECKS.json').read_text())
