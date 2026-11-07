"""Continue the audit after binding a Conda directory-origin pip to its sealed metadata."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time
import traceback

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('original_recheck', ROOT / 'recheck_server.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
WORK, CLOUD, PYTHON = c.WORK, c.CLOUD, c.PYTHON

def main():
    assert not (ROOT / 'FUNCTIONAL_CONTINUATION_STARTED.json').exists()
    pins = json.loads((ROOT / 'PINS.json').read_bytes())
    packages = json.loads((ROOT / 'PACKAGES_RESULT.json').read_bytes())
    tree = json.loads((ROOT / 'RESTORED_TREE_RESULT.json').read_bytes())
    assert packages['passed'] and tree['passed']
    assert tree['observed_modes'] == {'0o644': tree['files_freshly_rehashed']}
    original = json.loads((ROOT / 'environment-inventory.stdout.txt').read_text())
    assert not original['differences'] and original['extra_installed'] == {'pip': '26.2.2'}
    assert original['unparsed_direct_references'] == ['pip @ file:///home/task_179258895095150/croot/pip_1792588990593/work']
    attempt = ROOT / 'attempt-01-inventory-parser'
    attempt.mkdir()
    for name in ('RECHECK_FAILURE.json', 'environment-inventory.stdout.txt', 'environment-inventory.stderr.txt'):
        shutil.move(str(ROOT / name), str(attempt / name))
    c.save('FUNCTIONAL_CONTINUATION_STARTED.json', dict(started_utc=c.utc(),
        reason='Conda pip directory origin needs the original sealed version and direct_url binding',
        environment_or_original_assets_modified=False, whole_byte_checks_reused_without_repetition=True))
    environment = {key: value for key, value in os.environ.items() if not key.startswith('RAP_')}
    environment.update(PYTHONDONTWRITEBYTECODE='1', WANDB_MODE='disabled', WANDB_DISABLED='true',
        HF_HUB_OFFLINE='1', MPLBACKEND='Agg', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    inventory = '''import importlib.metadata as m,json,sys
from pathlib import Path
from urllib.parse import urlsplit,unquote
from packaging.utils import parse_wheel_filename,canonicalize_name
assert sys.version_info[:3]==(3,10,20)
base=Path('/root/autodl-fs/rap-transfer-20261106/A8-environment-20261106')
expected={}; directory_origins=[]
for line in (base/'logs/pip-freeze.log').read_text().splitlines():
 if '==' in line:
  name,version=line.split('==',1); expected[canonicalize_name(name)]=version
 elif ' @ ' in line:
  name,url=line.split(' @ ',1); name=canonicalize_name(name)
  wheel=unquote(Path(urlsplit(url).path).name)
  if wheel.endswith('.whl'): expected[name]=str(parse_wheel_filename(wheel)[1])
  else:
   candidates=[json.loads(p.read_text()) for p in (base/'conda-meta').glob('*.json')]
   candidates=[r for r in candidates if canonicalize_name(r['name'])==name]
   assert len(candidates)==1
   direct=json.loads(m.distribution(name).read_text('direct_url.json'))
   assert direct['url']==url and direct.get('dir_info')=={}
   expected[name]=candidates[0]['version']
   directory_origins.append(dict(package=name,version=expected[name],direct_url_matches=True,source='sealed Conda metadata'))
observed={canonicalize_name(d.metadata['Name']):d.version for d in m.distributions()}
differences=[dict(package=k,expected=v,observed=observed.get(k)) for k,v in expected.items() if observed.get(k)!=v]
result=dict(passed=not differences,python=sys.version,expected_versions=len(expected),differences=differences,
 extra_installed={k:v for k,v in observed.items() if k not in expected},directory_origins=directory_origins)
print(json.dumps(result)); assert not differences
'''
    raw, _ = c.command('environment-inventory-02', [PYTHON, '-I', '-B', '-c', inventory], 90,
        dict(environment, CUDA_VISIBLE_DEVICES=''))
    c.save('ENVIRONMENT_INVENTORY.json', json.loads(raw))
    site = Path('/root/autodl-tmp/rap-envs/rap-20261106/lib/python3.10/site-packages')
    for row in pins['gtsam']:
        assert c.digest(c.member(site, row['path'])) == row['sha256'], row['path']
    native = site / 'pytorch3d/_C.cpython-310-x86_64-linux-gnu.so'
    assert c.digest(native) == pins['native_extension_sha256']
    c.save('NATIVE_BYTES.json', dict(passed=True, original_gtsam_runtime_members_matched=len(pins['gtsam']),
        pytorch3d_native_extension_sha256=c.digest(native)))
    rap, slam = WORK / 'RAP-main', WORK / 'RAP-SLAM'
    config, dataset = rap / 'config/runtime.example.json', WORK / 'Datasets/data_odometry_velodyne/dataset'
    cases = [(task, [task, '--paths', str(config), '--input', str(rap / 'demo_example_data'),
        '--run-id', 'recheck-20261107-' + task, '--check']) for task in ('sample', 'demo', 'features')]
    cases.append(('slam', ['slam', '--paths', str(config), '--real-root', str(dataset.parent),
        '--run-id', 'recheck-20261107-slam', '--check', '--', '--source', 'real', '--real-seq', '00',
        '--real-start', '0', '--real-end', '10', '--real-apply-calib']))
    cases.append(('evaluate', ['evaluate', '--paths', str(config), '--poses-dir',
        str(rap / 'docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam/poses'),
        '--dataset-root', str(dataset), '--sequences', '00', '--method-label', 'migration-recheck-only',
        '--run-id', 'recheck-20261107-evaluate', '--check']))
    for task, args in cases:
        raw, _ = c.command('paths-' + task, [PYTHON, '-I', '-B', str(rap / 'scripts/run.py'), *args],
            45, dict(environment, CUDA_VISIBLE_DEVICES=''))
        plan = json.loads(raw)
        assert not plan['errors'] and not Path(plan['output']).exists()
        assert all(Path(row['path']).resolve().is_relative_to(WORK) for row in plan['required_paths'])
    c.save('PATH_CHECKS.json', dict(passed=True, tasks=[case[0] for case in cases], executed=False))
    cpu = rap / 'scripts/environment/cpu_probe.py'
    assert c.digest(cpu) == pins['cpu_harness_sha256']
    c.command('cpu-probe', [PYTHON, '-I', '-B', str(cpu), '--rap-root', str(rap), '--slam-root', str(slam),
        '--output', str(ROOT / 'CPU_PROBE.json')], 180, dict(environment, CUDA_VISIBLE_DEVICES=''))
    assert json.loads((ROOT / 'CPU_PROBE.json').read_bytes())['cpu_import_gate_passed']
    processes, _ = c.command('gpu-processes-before', ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
        '--format=csv,noheader'], 30, environment)
    assert not processes.strip(), 'GPU busy; defer without interrupting other tasks'
    gpu_start = time.monotonic()
    c.command('gpu-extension', [PYTHON, '-I', '-B', str(ROOT / 'gpu_extension_probe.py')], 90, environment)
    assert c.digest(ROOT / 'gpu_model_probe.py') == pins['gpu_harness_sha256']
    c.save('SMOKE_INPUTS.json', pins['smoke_inputs'])
    c.command('gpu-model', [PYTHON, '-I', '-B', str(ROOT / 'gpu_model_probe.py'), '--workspace', str(WORK),
        '--inputs', str(ROOT / 'SMOKE_INPUTS.json'), '--output', str(ROOT / 'GPU_MODEL_PROBE.json')],
        max(1, int(600 - (time.monotonic() - gpu_start))), environment)
    assert json.loads((ROOT / 'GPU_MODEL_PROBE.json').read_bytes())['passed']
    for row in pins['authority']['current_files']:
        assert c.digest(WORK / pins['layout'][row['root']] / row['path']) == row['sha256']
    extra = json.loads((ROOT / 'ADDITIONAL_SERVER_FILES.json').read_bytes())
    c.save('RECHECK_RESULT.json', dict(completed_utc=c.utc(), passed=True,
        package_files_rehashed=packages['files_freshly_rehashed'], package_bytes_rehashed=packages['bytes_freshly_read'],
        restored_files_rehashed=tree['files_freshly_rehashed'], restored_bytes_rehashed=tree['bytes_freshly_read'],
        internal_links_verified=25, external_personal_junctions_absent=2, current_authority_files=83,
        five_path_contracts_passed=True, CPU_import_gate_passed=True, GPU_extension_and_one_pair_IO_passed=True,
        additional_server_files=len(extra['ordinary_files']), additional_server_links=len(extra['additional_links']),
        first_parser_failure_preserved='attempt-01-inventory-parser', environment_changed=False,
        original_assets_or_prior_A8_receipts_overwritten=False, training_or_resume_validated=False,
        research_or_accuracy_comparison=False, original_provenance_holds_closed=False))
    print((ROOT / 'RECHECK_RESULT.json').read_text())

if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        c.save('FUNCTIONAL_RECHECK_FAILURE.json', dict(failed_utc=c.utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise
