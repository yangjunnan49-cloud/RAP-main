"""Small exclusive, bounded four-channel journal; not a pipeline integration."""
import hashlib
import struct
from pathlib import Path

HEADER = struct.Struct('<8sII')
FRAME = struct.Struct('<BI')
FOOTER = struct.Struct('<8sBQIQ32s3x')
MAGIC = b'RAPBEJ01'
END = b'RAPEND01'
COMPLETE, CAP_FAILURE, IO_FAILURE, INPUT_FAILURE = 1, 2, 3, 4


class Journal:
    def __init__(self, root, cap, channel_limits, inject_short=False):
        if type(cap) is not int or cap < HEADER.size+FOOTER.size or cap >= 2**32:
            raise ValueError('invalid cap')
        if set(channel_limits) != {1, 2, 3, 4} or any(type(v) is not int or v < 0 for v in channel_limits.values()):
            raise ValueError('invalid channel limits')
        self.path = Path(root)/'evidence.rdj'
        self.stream = self.path.open('xb', buffering=0)
        self.cap = cap
        self.limits = dict(channel_limits)
        self.channel_charged = {i: 0 for i in channel_limits}
        self.reserved = self.actual = self.records = 0
        self.digest = hashlib.sha256()
        self.status = COMPLETE
        self.closed = False
        self.inject_short = inject_short
        try:
            self._write_all(HEADER.pack(MAGIC, cap, 4))
        except BaseException:
            self.stream.close()
            self.closed = True
            raise

    def _write_all(self, data, body=False):
        cursor = 0
        while cursor < len(data):
            n = self.stream.write(data[cursor:])
            if n is None or n <= 0:
                raise OSError('write made no progress')
            if body:
                self.digest.update(data[cursor:cursor+n])
                self.actual += n
            cursor += n

    def append(self, channel, payload):
        if self.closed:
            raise RuntimeError('closed journal')
        if self.status != COMPLETE:
            raise RuntimeError('failed journal')
        if type(channel) is not int or channel not in self.limits or type(payload) is not bytes:
            self.status = INPUT_FAILURE
            raise ValueError('invalid record')
        encoded_length = FRAME.size+len(payload)
        if (len(payload) > self.limits[channel]-self.channel_charged[channel]
                or encoded_length > self.cap-HEADER.size-FOOTER.size-self.reserved):
            self.status = CAP_FAILURE
            raise BufferError('journal cap')
        self.reserved += encoded_length
        self.channel_charged[channel] += len(payload)
        frame = FRAME.pack(channel, len(payload))+payload
        try:
            if self.inject_short:
                self.inject_short = False
                self._write_all(frame[:3], body=True)
                raise OSError('injected short body write')
            self._write_all(frame, body=True)
            self.records += 1
        except BaseException:
            self.status = IO_FAILURE
            raise

    def close(self):
        if self.closed:
            return
        try:
            footer = FOOTER.pack(END, self.status, self.reserved, self.records,
                                 self.actual, self.digest.digest())
            self._write_all(footer)
        finally:
            self.stream.close()
            self.closed = True

    def observation(self):
        return dict(cap=self.cap, status=self.status, reserved_body_bytes=self.reserved,
            actual_body_bytes=self.actual, complete_records=self.records,
            channel_charged=self.channel_charged, closed=self.closed)
