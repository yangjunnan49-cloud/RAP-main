"""Independent byte rehash and bounded engineering revalidation; no asset writes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import stat
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
WORK = Path('/root/autodl-tmp/rap-workspace-20261106')
CLOUD = Path('/root/autodl-fs/rap-transfer-20261106')
OLD = Path('/root/autodl-tmp/rap-migration-20261106')
PYTHON = '/root/autodl-tmp/rap-envs/rap-20261106/bin/python'
BLOCK = 8 * 1024 * 1024

def utc():
    return datetime.now(timezone.utc).isoformat()

def save(name, value):
    temporary = ROOT / (name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(ROOT / name)

def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(BLOCK), b''):
            result.update(chunk)
    return result.hexdigest()

def member(root, relative):
    name = PurePosixPath(relative)
    assert not name.is_absolute() and '..' not in name.parts and '\\' not in relative
    target = root.joinpath(*name.parts)
    assert target.resolve().is_relative_to(root.resolve()), relative
    return target

def verify_one(root, row):
    result = dict(path=row['path'], expected_sha256=row['sha256'], expected_bytes=row['bytes'], passed=False)
    try:
        path = member(root, row['path'])
        initial = path.lstat()
        assert stat.S_ISREG(initial.st_mode) and initial.st_size == row['bytes'], 'Type or size differs'
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
            before = os.fstat(stream.fileno())
            value, count = hashlib.sha256(), 0
            for block in iter(lambda: stream.read(BLOCK), b''):
                value.update(block)
                count += len(block)
            after = os.fstat(stream.fileno())
        final = path.lstat()
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        stable = signature(initial) == signature(before) == signature(after) == signature(final)
        result.update(observed_sha256=value.hexdigest(), observed_bytes=count,
            mode=oct(stat.S_IMODE(final.st_mode)), uid=final.st_uid, gid=final.st_gid, stable_during_read=stable)
        result['passed'] = stable and count == row['bytes'] and value.hexdigest() == row['sha256']
    except Exception as exc:
        result['error'] = repr(exc)
    return result

def rehash(name, root, rows):
    start, total, completed, mismatches, modes = time.monotonic(), 0, 0, [], Counter()
    groups, group_bytes = Counter(), Counter()
    with gzip.open(ROOT / (name + '_FILES.jsonl.gz'), 'wt', encoding='utf-8') as stream:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(verify_one, root, row): row for row in rows}
            last = 0
            for future in as_completed(futures):
                row, result = futures[future], future.result()
                stream.write(json.dumps(result, ensure_ascii=False) + '\n')
                completed += 1
                total += result.get('observed_bytes', 0)
                group = row['path'].split('/')[0]
                groups[group] += 1
                group_bytes[group] += result.get('observed_bytes', 0)
                modes[result.get('mode', 'UNREAD')] += 1
                if not result['passed']:
                    mismatches.append(result)
                if time.monotonic() - last > 10 or completed == len(rows):
                    last = time.monotonic()
                    save(name + '_STATUS.json', dict(observed_utc=utc(), files_read=completed,
                        expected_files=len(rows), bytes_read=total, mismatches=len(mismatches)))
    result = dict(completed_utc=utc(), passed=not mismatches, files_freshly_rehashed=completed,
        bytes_freshly_read=total, mismatches=mismatches, observed_modes=dict(modes),
        group_files=dict(groups), group_bytes=dict(group_bytes), elapsed_seconds=time.monotonic() - start,
        fully_atomic_filesystem_snapshot=False)
    save(name + '_RESULT.json', result)
    return result

def command(name, argv, timeout, environment):
    started = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True, text=True, timeout=timeout)
    (ROOT / (name + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (ROOT / (name + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    assert result.returncode == 0, name + ' failed; see original logs'
    return result.stdout, time.monotonic() - started

def main():
    assert not (ROOT / 'STARTED.json').exists(), 'This audit attempt already exists'
    pins_raw = (ROOT / 'PINS.json').read_bytes()
    assert hashlib.sha256(pins_raw).hexdigest() == sys.argv[1], 'Untrusted local expectations'
    pins = json.loads(pins_raw)
    assert digest(ROOT / 'EXPECTED_TREE.jsonl.gz') == pins['expected_tree_sha256']
    with gzip.open(ROOT / 'EXPECTED_TREE.jsonl.gz', 'rt', encoding='utf-8') as stream:
        tree = [json.loads(line) for line in stream]
    assert len(tree) == len({row['path'] for row in tree}) == pins['expected_tree_files']
    assert sum(row['bytes'] for row in tree) == pins['expected_tree_bytes']
    save('STARTED.json', dict(started_utc=utc(), hostname=socket.gethostname(), pid=os.getpid(),
        scope='FRESH_COMPLETE_BYTE_RECHECK_AND_BOUNDED_ENGINEERING_IO', local_pins_sha256=sys.argv[1],
        production_files_or_original_receipts_written=False, new_research_or_training=False))
    with ThreadPoolExecutor(max_workers=2) as outer:
        packages = outer.submit(rehash, 'PACKAGES', CLOUD, pins['packages'])
        restored = outer.submit(rehash, 'RESTORED_TREE', WORK, tree)
        package_result, tree_result = packages.result(), restored.result()
    assert package_result['passed'] and tree_result['passed'], 'Byte differences retained; no automatic replacement'
    assert tree_result['observed_modes'] == {'0o644': len(tree)}, 'Restored file mode differs from declared policy'
    roots = {key: WORK / value for key, value in pins['layout'].items()}
    links = []
    for row in pins['links']:
        path = roots[row['root']] / row['path']
        if row['action'] == 'relative_internal':
            assert path.is_symlink() and os.readlink(path) == row['relative_target']
            target = roots[row['target_asset']['root']] / row['target_asset']['path']
            assert path.resolve(strict=True) == target.resolve(strict=True)
            assert path.resolve().is_relative_to(WORK)
            links.append(dict(path=str(path.relative_to(WORK)), action='relative_internal', passed=True))
        else:
            assert not os.path.lexists(path), 'Personal external junction unexpectedly exists'
            links.append(dict(path=str(path.relative_to(WORK)), action='external_absent', passed=True))
    assert Counter(row['action'] for row in links) == {'relative_internal': 25, 'external_absent': 2}
    save('LINKS.json', dict(passed=True, links=links))
    expected = {row['path'] for row in tree}
    expected_links = {row['path'] for row in links if row['action'] == 'relative_internal'}
    extras, other_links = [], []
    for directory, dirs, files in os.walk(WORK, followlinks=False):
        for name in list(dirs):
            path = Path(directory) / name
            if path.is_symlink():
                dirs.remove(name)
                relative = path.relative_to(WORK).as_posix()
                if relative not in expected_links:
                    other_links.append(dict(path=relative, target=os.readlink(path)))
        for name in files:
            path = Path(directory) / name
            relative = path.relative_to(WORK).as_posix()
            if relative in expected or relative in expected_links:
                continue
            if path.is_symlink():
                other_links.append(dict(path=relative, target=os.readlink(path)))
            else:
                info = path.lstat()
                extras.append(dict(path=relative, bytes=info.st_size, sha256=digest(path), mode=oct(stat.S_IMODE(info.st_mode))))
    save('ADDITIONAL_SERVER_FILES.json', dict(ordinary_files=extras, additional_links=other_links,
        deleted_or_overwritten=False, classification_required=True))
    authority = []
    for row in pins['authority']['current_files']:
        path = roots[row['root']] / row['path']
        assert digest(path) == row['sha256']
        authority.append(dict(root=row['root'], path=row['path'], passed=True))
    save('AUTHORITY.json', dict(passed=True, current_files=83, files=authority))
    environment = {key: value for key, value in os.environ.items() if not key.startswith('RAP_')}
    environment.update(PYTHONDONTWRITEBYTECODE='1', WANDB_MODE='disabled', WANDB_DISABLED='true',
        HF_HUB_OFFLINE='1', MPLBACKEND='Agg', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    command('pip-check', [PYTHON, '-I', '-B', '-m', 'pip', 'check'], 120, dict(environment, CUDA_VISIBLE_DEVICES=''))
    inventory = '''import importlib.metadata as m,json,re,sys
from pathlib import Path
from urllib.parse import urlsplit,unquote
from packaging.utils import parse_wheel_filename,canonicalize_name
expected={}
unparsed=[]
for line in Path('/root/autodl-fs/rap-transfer-20261106/A8-environment-20261106/logs/pip-freeze.log').read_text().splitlines():
 if '==' in line:
  name,version=line.split('==',1); expected[canonicalize_name(name)]=version
 elif ' @ ' in line:
  name,url=line.split(' @ ',1)
  wheel=unquote(Path(urlsplit(url).path).name)
  if wheel.endswith('.whl'): expected[canonicalize_name(name)]=str(parse_wheel_filename(wheel)[1])
  else: unparsed.append(line)
observed={canonicalize_name(d.metadata['Name']):d.version for d in m.distributions()}
differences=[dict(package=k,expected=v,observed=observed.get(k)) for k,v in expected.items() if observed.get(k)!=v]
result=dict(passed=not differences,python=sys.version,expected_versions=len(expected),differences=differences,
 extra_installed={k:v for k,v in observed.items() if k not in expected},unparsed_direct_references=unparsed)
print(json.dumps(result))
assert not differences and not unparsed
'''
    inventory_raw, _ = command('environment-inventory', [PYTHON, '-I', '-B', '-c', inventory], 90,
        dict(environment, CUDA_VISIBLE_DEVICES=''))
    save('ENVIRONMENT_INVENTORY.json', json.loads(inventory_raw))
    site = Path('/root/autodl-tmp/rap-envs/rap-20261106/lib/python3.10/site-packages')
    for row in pins['gtsam']:
        assert digest(member(site, row['path'])) == row['sha256'], row['path']
    native = site / 'pytorch3d/_C.cpython-310-x86_64-linux-gnu.so'
    assert digest(native) == pins['native_extension_sha256']
    save('NATIVE_BYTES.json', dict(passed=True, original_gtsam_runtime_members_matched=len(pins['gtsam']),
        pytorch3d_native_extension_sha256=digest(native)))
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
        raw, _ = command('paths-' + task, [PYTHON, '-I', '-B', str(rap / 'scripts/run.py'), *args],
            45, dict(environment, CUDA_VISIBLE_DEVICES=''))
        plan = json.loads(raw)
        assert not plan['errors'] and not Path(plan['output']).exists()
        assert all(Path(row['path']).resolve().is_relative_to(WORK) for row in plan['required_paths'])
    save('PATH_CHECKS.json', dict(passed=True, tasks=[case[0] for case in cases], executed=False))
    cpu = rap / 'scripts/environment/cpu_probe.py'
    assert digest(cpu) == pins['cpu_harness_sha256']
    command('cpu-probe', [PYTHON, '-I', '-B', str(cpu), '--rap-root', str(rap), '--slam-root', str(slam),
        '--output', str(ROOT / 'CPU_PROBE.json')], 180, dict(environment, CUDA_VISIBLE_DEVICES=''))
    assert json.loads((ROOT / 'CPU_PROBE.json').read_bytes())['cpu_import_gate_passed']
    gpu_processes, _ = command('gpu-processes-before', ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
        '--format=csv,noheader'], 30, environment)
    assert not gpu_processes.strip(), 'GPU busy; bounded GPU acceptance deferred without interrupting other tasks'
    gpu_start = time.monotonic()
    command('gpu-extension', [PYTHON, '-I', '-B', str(ROOT / 'gpu_extension_probe.py')], 90, environment)
    assert digest(ROOT / 'gpu_model_probe.py') == pins['gpu_harness_sha256']
    save('SMOKE_INPUTS.json', pins['smoke_inputs'])
    command('gpu-model', [PYTHON, '-I', '-B', str(ROOT / 'gpu_model_probe.py'), '--workspace', str(WORK),
        '--inputs', str(ROOT / 'SMOKE_INPUTS.json'), '--output', str(ROOT / 'GPU_MODEL_PROBE.json')],
        max(1, int(600 - (time.monotonic() - gpu_start))), environment)
    assert json.loads((ROOT / 'GPU_MODEL_PROBE.json').read_bytes())['passed']
    # Re-read core authority after the model probe to detect control-file drift.
    for row in pins['authority']['current_files']:
        assert digest(roots[row['root']] / row['path']) == row['sha256']
    result = dict(completed_utc=utc(), passed=True, package_files_rehashed=package_result['files_freshly_rehashed'],
        package_bytes_rehashed=package_result['bytes_freshly_read'],
        restored_files_rehashed=tree_result['files_freshly_rehashed'], restored_bytes_rehashed=tree_result['bytes_freshly_read'],
        internal_links_verified=25, external_personal_junctions_absent=2, current_authority_files=83,
        five_path_contracts_passed=True, CPU_import_gate_passed=True, GPU_extension_and_one_pair_IO_passed=True,
        additional_server_files=len(extras), additional_server_links=len(other_links),
        original_assets_or_prior_receipts_overwritten=False, training_or_resume_validated=False,
        research_or_accuracy_comparison=False, original_provenance_holds_closed=False,
        disk_usage_bytes={str(p): dict(zip(('total', 'used', 'free'), shutil.disk_usage(p)))
            for p in (Path('/root/autodl-tmp'), Path('/root/autodl-fs'))})
    save('RECHECK_RESULT.json', result)
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        save('RECHECK_FAILURE.json', dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc(),
            original_assets_overwritten=False, training_started=False))
        raise
