import hashlib, json, os, signal, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent


def record(pid, script):
    return dict(pid=pid, pgid=os.getpgid(pid),
        start_ticks=Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
        script=str(script.resolve()), script_sha256=hashlib.sha256(script.read_bytes()).hexdigest())


def validate(value, role):
    expected = ROOT / {'runner': 'lease_runner02.py', 'worker': 'native_stage.py'}[role]
    proc = Path(f'/proc/{value["pid"]}')
    if not proc.exists():
        return False
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    if stat[0] == 'Z':
        return False
    assert stat[19] == value['start_ticks'], 'start_tick_mismatch'
    assert value['pid'] == value['pgid'] == os.getpgid(value['pid']), 'group_mismatch'
    assert value['script'] == str(expected.resolve()), 'script_path_mismatch'
    assert value['script_sha256'] == hashlib.sha256(expected.read_bytes()).hexdigest(), 'script_hash_mismatch'
    assert str(expected.resolve()).encode() in (proc / 'cmdline').read_bytes(), 'command_mismatch'
    return True


def stop(value, role, sig=signal.SIGTERM):
    if validate(value, role):
        os.killpg(value['pgid'], sig)
        return True
    return False
