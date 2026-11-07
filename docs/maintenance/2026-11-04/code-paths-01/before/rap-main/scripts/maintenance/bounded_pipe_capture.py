"""Synthetic-only controller with separate pre-reserved native exit envelope."""
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path
from bounded_evidence_journal import Journal, IO_FAILURE


def capture(folder,fixture,mode):
    started=time.monotonic()
    writer=Journal(folder,2048,{1:256,2:128,3:128,4:256})
    writer.append(4,json.dumps(dict(event='launch',mode=mode),sort_keys=True).encode())
    process=None;native=None;reason=None;signalled=False;kill_at=None
    observed={2:0,3:0};stored={2:0,3:0};eof={2:False,3:False}
    selector=selectors.DefaultSelector()
    try:
        process=subprocess.Popen([sys.executable,'-B',str(fixture),mode],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            bufsize=0,start_new_session=True)
        selector.register(process.stdout,selectors.EVENT_READ,2)
        selector.register(process.stderr,selectors.EVENT_READ,3)
        deadline=started+(0.25 if mode=='timeout' else 3.0)
        while native is None or selector.get_map():
            now=time.monotonic()
            if reason is None and now>=deadline:
                reason='timeout';writer.status=IO_FAILURE
            if reason is not None and native is None:
                if not signalled:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                    signalled=True;kill_at=now+0.25
                elif kill_at is not None and now>=kill_at:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    kill_at=None
            for key,_ in selector.select(0.02):
                channel=key.data
                body=os.read(key.fileobj.fileno(),64)
                if not body:
                    eof[channel]=True;selector.unregister(key.fileobj);key.fileobj.close()
                    continue
                observed[channel]+=len(body)
                if reason is None:
                    try:writer.append(channel,body)
                    except BufferError:reason='log_overflow'
                    else:stored[channel]+=len(body)
            if native is None:
                pid,status,usage=os.wait4(process.pid,os.WNOHANG)
                if pid:
                    process.returncode=os.waitstatus_to_exitcode(status)
                    native=dict(pid=pid,wait_status=status,exit_code=process.returncode,
                        peak_RSS_bytes=usage.ru_maxrss*1024,
                        user_seconds=usage.ru_utime,system_seconds=usage.ru_stime)
        if native['exit_code']!=0 and reason is None:
            reason='nonzero_exit';writer.status=IO_FAILURE
        assert native['peak_RSS_bytes']<=64*2**20 and all(eof.values())
        writer.close()
        receipt=dict(mode=mode,native=native,reason=reason,termination_requested=signalled,
            observed_bytes=observed,stored_bytes=stored,
            discarded_observed_bytes={k:observed[k]-stored[k] for k in observed},
            EOF_observed=eof,wall_seconds=time.monotonic()-started,
            admitted=reason is None and native['exit_code']==0,
            full_intended_flood_output_claim=False,
            journal_cap=2048,terminal_reserved_bytes=1024,cooperating_file_envelope=3072)
        body=(json.dumps(receipt,sort_keys=True,allow_nan=False)+'\n').encode()
        assert len(body)<=1024
        with (Path(folder)/'exit.json').open('xb') as stream:stream.write(body)
        return receipt
    finally:
        selector.close()
        if process is not None and native is None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            pid,status,usage=os.wait4(process.pid,0)
            process.returncode=os.waitstatus_to_exitcode(status)
        if process is not None:
            for stream in (process.stdout,process.stderr):
                if stream is not None and not stream.closed:stream.close()
        writer.close()
