import hashlib, json, os, resource, signal, struct, subprocess, sys, time
from pathlib import Path
from boundary_contract import artifact, compare, verify
from recorder import Recorder

ROOT = Path(__file__).resolve().parent
folder = Path(sys.argv[1]); case = sys.argv[2]
start = time.monotonic(); checks = []; child = None


def stopped(*_):
    raise RuntimeError('owned_worker_stop')


signal.signal(signal.SIGTERM, stopped)


def expect(name, condition):
    assert condition, name
    checks.append(dict(name=name, passed=True))


def fixtures():
    binding = dict(source=hashlib.sha256((ROOT / 'recorder.py').read_bytes()).hexdigest(), runtime='stdlib-stub')
    recorder = Recorder(binding)
    points = bytearray(struct.pack('<6f', 1, 2, 3, 4, 5, 6))
    original = bytes(points); token = object(); observed = []
    def fn(value):
        observed.append(value)
        return token
    capture = lambda: {'points': artifact(points, 'f4', [2, 3], 'little', 'prepared_input')}
    returned = recorder.call('map.integrate', fn, (points,), capture,
                             lambda result: {'return': artifact(b'\x01', 'u1', [1], 'na', 'output')})
    expect('argument_identity', observed[0] is points)
    expect('return_identity', returned is token)
    expect('input_bytes_unchanged', bytes(points) == original)
    expect('exactly_one_underlying_call', len(observed) == 1)
    expect('before_after_order', [e['boundary'] for e in recorder.events] == ['map.integrate:before', 'map.integrate:after'])
    failure = ValueError('original-stub-exception'); count = []
    def raises(value):
        count.append(value)
        raise failure
    try:
        recorder.call('detector', raises, (points,), capture, lambda _: {})
    except ValueError as caught:
        expect('original_exception_identity', caught is failure)
    else:
        raise AssertionError('Exception was swallowed')
    expect('exception_call_not_retried', len(count) == 1)
    expect('exception_event_after_input', [e['boundary'] for e in recorder.events[-2:]] == ['detector:before', 'detector:exception'])
    direct = bytearray(points); wrapped = bytearray(points)
    def mutate(value):
        value[0] ^= 1
        return value
    direct_return = mutate(direct)
    wrapped_return = recorder.call('natural_mutation', mutate, (wrapped,),
        lambda: {'points': artifact(wrapped, 'f4', [2, 3], 'little', 'prepared_input')},
        lambda _: {'changed': artifact(wrapped, 'f4', [2, 3], 'little', 'output')})
    expect('natural_callee_mutation_matches_direct', direct == wrapped)
    expect('mutation_return_identity', direct_return is direct and wrapped_return is wrapped)
    expect('pre_mutation_snapshot_retained', recorder.events[-2]['components']['points']['sha256'] == hashlib.sha256(original).hexdigest())
    recording_failure = RuntimeError('synthetic-capture-failure'); uncalled = []
    def bad_capture():
        raise recording_failure
    try:
        recorder.call('never_run', lambda: uncalled.append(True), (), bad_capture, lambda _: {})
    except RuntimeError as caught:
        expect('recording_failure_propagates', caught is recording_failure)
    expect('failed_pre_capture_never_calls_callee', not uncalled)
    expect('call_count_tracks_real_calls', recorder.calls == 3)
    sealed = recorder.sealed(); verify(sealed)
    expect('equal_records_do_not_claim_complete_state', compare(sealed, sealed)['status'] == 'recorded_bytes_equal_native_state_unknown')
    (folder / 'STUB_CONTROLS.json').write_text(json.dumps(dict(passed=True, checks=checks, events=sealed), indent=2))


ok = False; error = None
try:
    fixtures()
    if case == 'observer_loss':
        child = subprocess.Popen([sys.executable, '-B', str(ROOT / 'grandchild.py'), str(folder)])
    if case == 'rss_fault':
        allocation = bytearray(64 * 2**20)
    time.sleep(1.5 if case == 'normal' else 60)
    ok = True
except BaseException as exc:
    error = str(exc)
finally:
    if child is not None:
        try:
            child.wait(timeout=1)
        except subprocess.TimeoutExpired:
            child.terminate(); child.wait(timeout=1)
    (folder / 'worker_exit.json').write_text(json.dumps(dict(success=ok, error=error,
        elapsed=time.monotonic()-start, controls=len(checks), max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        native_imports=0, raw_reads=0, GT_reads=0, new_predictions=0)))
sys.exit(0 if ok else 2)
