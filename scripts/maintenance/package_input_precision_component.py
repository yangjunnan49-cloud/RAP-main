"""Package a byte-certified arithmetic component; no registration/GT."""
import time
START=time.monotonic()
import os,sys,resource,subprocess,traceback,zipfile,json,hashlib,shutil,ast
from pathlib import Path
import certify_raw_input_contract as c
d=c.d;BASE=c.BASE;SUP=c.SUP
def run():
    ok=False;err=None
    try:
        assert c.used()<7200;certificate=d.read(BASE/'INPUT_CERTIFICATE.json');assert certificate['passed'];dest=BASE/'input_precision_component';dest.mkdir()
        shutil.copy2(BASE/'legacy_f32_correction.py',dest/'legacy_f32_correction.py');shutil.copy2(c.R0/'synthetic_runtime_points.npy',dest/'synthetic_points.npy');shutil.copy2(c.R0/'synthetic_corrected_RAP.npy',dest/'expected_original_f32.npy')
        for label in ('RAP','KISS'):shutil.copy2(c.R0/f'correction_runtime_{label}.json',dest/f'observed_runtime_{label}.json')
        d.save(dest/'REAL_INPUT_CERTIFICATE_SUMMARY.json',certificate)
        original=d.r.SLAM/'rap_slam/real_dataset.py';text=original.read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='kitti_vertical_correction');(dest/'reference_function.py').write_text('import numpy as np\n\n'+ast.get_source_segment(text,node)+'\n',encoding='utf-8')
        script='''"""Local fixture check. Requires an existing NumPy environment; installs nothing."""
from pathlib import Path
import hashlib
import numpy as np
from legacy_f32_correction import legacy_f32_correction
base=Path(__file__).resolve().parent
p=np.load(base/'synthetic_points.npy',allow_pickle=False)
expected=np.load(base/'expected_original_f32.npy',allow_pickle=False)
actual=legacy_f32_correction(p)
assert actual.dtype==np.float32 and actual.shape==expected.shape
assert hashlib.sha256(actual.tobytes(order='C')).digest()==hashlib.sha256(expected.tobytes(order='C')).digest()
print('PASS',np.__version__,actual.shape,'exact original float32 bytes')
'''
        (dest/'validate_fixture.py').write_text(script,encoding='utf-8')
        readme='''# Explicit original-float32 KITTI correction component

Run `python -B validate_fixture.py` in an existing NumPy environment. No installation or data acquisition occurs. `legacy_f32_correction` accepts only Nx3 float32 points, reproducing the original E0 source correction's observed NumPy1.26 intermediate float32 arithmetic. Same0.205degree and near-vertical rule. The fixture contains10003 synthetic points and the actual original-runtime prepared output; full output bytes must match, including signed zero.

Validated on the two documented existing NumPy1.26.4/2.2.6 runtimes. The real certificate covers12296 original frames/1514179545 point occurrences/4542538635 XYZ components, matching every prepared count/hash in source order. Real raw/reference files are not distributed in this package. SHA equality establishes input byte correspondence, not physical sensor/reference authenticity, per-beam timing or training exclusion.

Apply this only to the original E0 frontend role. The old G map branch and native K reader retain their separate original numerical semantics. The frozen physical parameters do not change. This is a source compatibility component, not a new SLAM method or accuracy result. Existing KISS native ABI/backend behavior must still pass its original source-pose correspondence test. The original failed R0 run and individual G protections remain.

`reference_function.py` is the original source snapshot for reading, not a replacement for this explicit function under NumPy2. `observed_runtime` records the measured intermediate dtype difference. Future NumPy/platform versions need their own contract check; no universal floating-point equivalence is claimed.
'''
        (dest/'README.md').write_text(readme,encoding='utf-8')
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';receipts=[]
        for exe in ('/root/miniconda3/envs/rap-inference/bin/python',d.r.KISS):
            p=subprocess.run([exe,'-u','-B',str(dest/'validate_fixture.py')],env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0;receipts.append(dict(executable=exe,stdout=p.stdout,stderr=p.stderr,returncode=p.returncode))
        d.save(dest/'FIXTURE_CHECKS.json',dict(passed=True,runs=receipts,new_registration_calls=0,original_source_sha256=d.sha(original),certified_component_sha256=d.sha(BASE/'legacy_f32_correction.py')))
        d.save(dest/'FILE_SHA256.json',dict(files={str(p.relative_to(dest)):d.sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}))
        zp=BASE/'input_precision_component_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(dest.rglob('*')):
                if p.is_file():z.write(p,arcname=str(p.relative_to(dest)))
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for name,h in json.loads(z.read('FILE_SHA256.json'))['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
        d.save(BASE/'PRECISION_PACKAGE_CHECKS.json',dict(utc=d.now(),passed=True,zip_sha256=d.sha(zp),zip_bytes=zp.stat().st_size,source_contract_document_sha256=d.sha(BASE/'NUMERICAL_INPUT_CONTRACT.md'),new_registration_calls=0))
        c.cap();ok=True;print('Portable precision component checks PASS in both NumPy versions',zp.stat().st_size,flush=True)
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:d.save(SUP/'package_precision/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0,shared_R0_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='package_precision';run()
