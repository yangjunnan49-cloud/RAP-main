"""External lease watchdog for a separate owned synthetic worker group."""
import hashlib, json, os, resource, signal, subprocess, sys, time, uuid
from pathlib import Path
from identity import record, stop, validate
ROOT = Path(__file__).resolve().parent
folder = Path(sys.argv[1]); case = sys.argv[2]
cap = float(sys.argv[3]); initial_scope = float(sys.argv[4]); scope_cap = 1320.0
start = time.monotonic(); last_reply_at = start; last_host_stage = 0.; last_host_scope = initial_scope
worker = None; worker_identity = None; last_lease = None; peak_group_rss = 0; count = 0
if os.getpgrp() != os.getpid():
    os.setsid()


def write(name, value):
    path = folder / name; temp = path.with_suffix('.tmp')
    with temp.open('x') as output:
        json.dump(value, output, indent=2)
    os.rename(temp, path)


def signalled(*_):
    raise RuntimeError('host_owned_stop')


signal.signal(signal.SIGTERM, signalled)
write('runner_owned.json', record(os.getpid(), Path(__file__)))


def check_bounds():
    global peak_group_rss
    now = time.monotonic()
    if max(now-start, last_host_stage+now-last_reply_at) >= cap:
        raise RuntimeError('linux_or_host_stage_deadline')
    if max(initial_scope+now-start, last_host_scope+now-last_reply_at) >= scope_cap:
        raise RuntimeError('whole_scope_close_reserve')
    group_rss = 0
    if worker is not None:
        pids = [worker.pid]
        owned = folder / 'grandchild_owned.json'
        if owned.exists():
            pids.append(json.loads(owned.read_text())['pid'])
        for pid in pids:
            status = Path(f'/proc/{pid}/status')
            if status.exists():
                for line in status.read_text().splitlines():
                    if line.startswith('VmRSS:'):
                        group_rss += int(line.split()[1]) * 1024
    peak_group_rss = max(peak_group_rss, group_rss)
    if group_rss > (32 if case == 'rss_fault' else 4096) * 2**20:
        raise RuntimeError('observed_worker_group_RSS_cap')


ok = False; error = None; cleanup_error = None; stopped_at = None
try:
    freeze = json.loads((folder.parent / 'SOURCE_FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        if case == 'source_binding' and name == 'worker.py':
            expected = '0' * 64
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest().upper() == expected.upper(), 'source_binding_mismatch:' + name
    while True:
        check_bounds()
        if worker is not None and worker.poll() is not None:
            assert worker.returncode == 0, 'worker_nonzero_exit'
            ok = True
            break
        nonce = uuid.uuid4().hex; prefix = f'{count:05d}_{nonce}'; begin = time.monotonic()
        write(prefix + '_request.json', dict(nonce=nonce, sequence=count, linux_elapsed=begin-start))
        response = folder / (prefix + '_response.json')
        while not response.exists():
            check_bounds()
            if time.monotonic()-begin > 2:
                raise RuntimeError('host_lease_expired')
            time.sleep(.02)
        reply = json.loads(response.read_text())
        assert reply['nonce'] == nonce and reply['sequence'] == count, 'nonce_or_sequence_mismatch'
        assert reply['headroom_bytes'] >= 12*2**30, 'host_memory_guard'
        assert time.monotonic()-begin <= 2, 'stale_response'
        last_host_stage = reply['stage_elapsed']; last_host_scope = reply['scope_elapsed']
        last_reply_at = time.monotonic(); last_lease = last_reply_at; count += 1
        check_bounds()
        if worker is None:
            worker = subprocess.Popen(['/root/miniconda3/envs/rap-inference/bin/python', '-B', str(ROOT / 'worker.py'), str(folder), case],
                start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='0'))
            worker_identity = record(worker.pid, ROOT / 'worker.py')
            write('worker_owned.json', worker_identity)
        time.sleep(.1)
except BaseException as caught:
    error = str(caught); stopped_at = time.monotonic()
finally:
    try:
        if worker is not None:
            if worker.poll() is None:
                stop(worker_identity, 'worker')
                try:
                    worker.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    stop(worker_identity, 'worker', signal.SIGKILL); worker.wait(timeout=1)
            else:
                worker.wait()
    except BaseException as caught:
        cleanup_error = str(caught); ok = False
    write('runner_exit.json', dict(success=ok, error=error, cleanup_error=cleanup_error,
        elapsed=time.monotonic()-start, accepted_leases=count, worker_launched=worker is not None,
        worker_return_code=worker.returncode if worker is not None else None,
        stop_after_last_accepted_reply=(stopped_at-last_lease if stopped_at and last_lease else None),
        peak_worker_group_RSS_bytes=peak_group_rss,
        parent_peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        synthetic=False, real_public_operability=True, payload_counters_in_worker_exit=True))
sys.exit(0 if ok else 2)
