"""Resumable, pinned-host migration transport. Password exists only in memory."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import getpass
import hashlib
import json
import logging
import os
from pathlib import Path, PurePosixPath
import sys
from threading import Event, Lock, Thread
import time
import traceback

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
sys.path.insert(0, str(REPO / ".maintenance-archive/migration/ssh-client-runtime-20261106"))
import paramiko

HOST, PORT = "connect.weste.seetacloud.com", 23243
TRANSFER = "/root/autodl-fs/rap-transfer-20261106"
REMOTE = "/root/autodl-tmp/rap-migration-20261106"
EXPECTED_SHA = "4500e54e3a654533574a7db729817c8984c1144e4b918b7204b8d7abaa323ada"
LOCK, STOP = Lock(), Event()
PASSWORD = None


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    path = PHASE / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def connect():
    client = paramiko.SSHClient()
    client.load_host_keys(str(PHASE / "known_hosts"))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(HOST, port=PORT, username="root", password=PASSWORD, timeout=30,
                   banner_timeout=60, auth_timeout=30, allow_agent=False, look_for_keys=False, compress=True)
    client.get_transport().set_keepalive(30)
    return client


def remote_python(client, code):
    stdin, stdout, stderr = client.exec_command("/root/miniconda3/bin/python -B -", timeout=1800)
    stdin.write(code)
    stdin.channel.shutdown_write()
    raw, error = stdout.read(), stderr.read()
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError("Remote maintenance command failed: " + error.decode("utf-8", errors="replace")[-2000:])
    return json.loads(raw.decode("utf-8"))


def path_for(row):
    name = PurePosixPath(row["path"])
    if name.is_absolute() or ".." in name.parts or "\\" in row["path"]:
        raise ValueError("Unsafe transfer member")
    source = REPO / ".maintenance-archive/migration" / Path(*name.parts)
    assert source.resolve().is_relative_to((REPO / ".maintenance-archive/migration").resolve())
    return source, TRANSFER + "/" + row["path"]


def remote_hash(client, path, size):
    return remote_python(client, "import hashlib,json\np=" + repr(path) + "\nn=" + str(size) + "\nh=hashlib.sha256()\nwith open(p,'rb') as f:\n while n:\n  b=f.read(min(n,8388608))\n  if not b: raise ValueError('Short remote prefix')\n  h.update(b);n-=len(b)\nprint(json.dumps(h.hexdigest()))\n")


def local_prefix(path, size):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while size:
            block = stream.read(min(size, 8 * 1024 * 1024))
            if not block:
                raise ValueError("Short local prefix")
            value.update(block)
            size -= len(block)
    return value.hexdigest()


def upload(row):
    source, target = path_for(row)
    assert source.stat().st_size == row["bytes"]
    for attempt in range(8):
        client = None
        try:
            client = connect()
            with paramiko.SFTPClient.from_transport(client.get_transport(), window_size=64 * 1024 * 1024,
                                                    max_packet_size=262144) as sftp:
                sftp.get_channel().settimeout(120)
                try:
                    offset = sftp.stat(target).st_size
                    exists = True
                except FileNotFoundError:
                    offset, exists = 0, False
                if offset > row["bytes"]:
                    raise ValueError("Remote size exceeds sealed size: " + row["path"])
                if offset:
                    observed = remote_hash(client, target, offset)
                    expected = row["sha256"] if offset == row["bytes"] else local_prefix(source, offset)
                    if observed != expected:
                        raise ValueError("Remote prefix mismatch; retained without overwrite: " + row["path"])
                if offset != row["bytes"]:
                    with source.open("rb") as incoming, sftp.open(target, "r+" if exists else "w", bufsize=0) as outgoing:
                        incoming.seek(offset)
                        outgoing.seek(offset)
                        outgoing.set_pipelined(True)
                        for block in iter(lambda: incoming.read(1024 * 1024), b""):
                            outgoing.write(block)
                    assert sftp.stat(target).st_size == row["bytes"]
                    if remote_hash(client, target, row["bytes"]) != row["sha256"]:
                        raise ValueError("Final remote SHA256 mismatch: " + row["path"])
                with LOCK:
                    with (PHASE / "CLIENT_VERIFIED_FILES.jsonl").open("a", encoding="utf-8") as out:
                        out.write(json.dumps(dict(completed_utc=utc(), path=row["path"], bytes=row["bytes"],
                                                  sha256=row["sha256"], resumed_from_bytes=offset)) + "\n")
                print(json.dumps(dict(upload_file_verified=row["path"], bytes=row["bytes"])), flush=True)
                return
        except (ValueError, paramiko.BadHostKeyException, paramiko.AuthenticationException):
            raise
        except Exception as exc:
            with LOCK:
                with (PHASE / "CLIENT_RETRIES.jsonl").open("a", encoding="utf-8") as out:
                    out.write(json.dumps(dict(utc=utc(), path=row["path"], attempt=attempt + 1, error=repr(exc))) + "\n")
            if attempt == 7:
                raise
            time.sleep(min(60, 5 * (attempt + 1)))
        finally:
            if client:
                client.close()


def monitor():
    while not STOP.is_set():
        client = None
        try:
            client = connect()
            with client.open_sftp() as sftp:
                with sftp.open(REMOTE + "/file-acceptance/STATUS.json", "r") as stream:
                    value = json.loads(stream.read())
            value["client_observed_utc"] = utc()
            save("REMOTE_TRANSFER_STATUS.json", value)
            with (PHASE / "REMOTE_TRANSFER_EVENTS.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps(value, ensure_ascii=False) + "\n")
            print(json.dumps(value, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps(dict(status_poll_error=type(exc).__name__, utc=utc())), flush=True)
        finally:
            if client:
                client.close()
        STOP.wait(60)


def main():
    global PASSWORD
    if (PHASE / "CLIENT_STARTED.json").exists():
        raise RuntimeError("This client attempt already has a start receipt")
    raw = (PHASE / "EXPECTED_UPLOAD.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA
    expected = json.loads(raw)
    PASSWORD = getpass.getpass("SSH password (memory only): ")
    save("CLIENT_STARTED.json", dict(started_utc=utc(), pid=os.getpid(), host=HOST, port=PORT,
         expected_manifest_sha256=EXPECTED_SHA, password_persisted=False, host_key_policy="PINNED_REJECT_UNKNOWN",
         parallel_workers=4, reconnect_attempts_per_file=8, prefix_SHA256_required_before_resume=True))
    client = connect()
    try:
        complete = remote_python(client, """import pathlib,json,hashlib
p=pathlib.Path('/root/autodl-tmp/rap-migration-20261106/EXPECTED_UPLOAD.json')
assert hashlib.sha256(p.read_bytes()).hexdigest()==""" + repr(EXPECTED_SHA) + """
ready=[]
for r in json.loads(p.read_text())['files']:
 f=pathlib.Path('/root/autodl-fs/rap-transfer-20261106')/r['path']
 if not f.is_file() or f.stat().st_size!=r['bytes']: continue
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for block in iter(lambda:stream.read(8388608),b''): h.update(block)
 if h.hexdigest()!=r['sha256']: raise ValueError('Complete member hash differs: '+r['path'])
 ready.append(r['path'])
print(json.dumps(ready))
""")
    finally:
        client.close()
    save("CLIENT_INITIAL_VERIFIED.json", dict(verified_files=complete, count=len(complete), observed_utc=utc()))
    worker = Thread(target=monitor, daemon=True)
    worker.start()
    pending = [row for row in expected["files"] if row["path"] not in set(complete)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(upload, row) for row in pending]):
            future.result()
    save("CLIENT_UPLOAD_COMPLETE.json", dict(completed_utc=utc(), package_files=expected["file_count"],
         package_bytes=expected["bytes"], all_server_file_SHA256_checked=True))
    # Late A8 additions are prepared only after today's six-root byte audit.
    deadline = time.monotonic() + 48 * 3600
    while not (PHASE / "CONTROL_READY.json").exists():
        if time.monotonic() > deadline:
            raise TimeoutError("Late control package did not become ready")
        time.sleep(30)
    save("CLIENT_AWAITING_FINALIZATION.json", dict(observed_utc=utc(),
         note="Base upload complete; A8 control instructions are ready for the active coordinator"))
    print("BASE_UPLOAD_COMPLETE_A8_CONTROL_READY", flush=True)


if __name__ == "__main__":
    logging.getLogger("paramiko").setLevel(logging.ERROR)
    try:
        main()
    except BaseException as exc:
        save("CLIENT_FAILURE.json", dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise
    finally:
        STOP.set()
        PASSWORD = None
