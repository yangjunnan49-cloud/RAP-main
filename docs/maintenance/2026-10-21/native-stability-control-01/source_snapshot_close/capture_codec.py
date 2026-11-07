"""Bounded typed-byte descriptors and streaming immutable event-chain format."""
import hashlib, json, math
MAX_ARRAY = 16 * 2**20
MAX_EVENTS = 20000


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def describe(body, dtype, shape, endian, strides, role, type_tag='array'):
    sizes = {'f4':4, 'f8':8, 'i4':4, 'i8':8, 'u1':1, 'u4':4, 'u8':8, 'b1':1}
    if dtype not in sizes or role not in {'input', 'output', 'prepared', 'derived', 'state'}:
        raise ValueError('unsupported descriptor dtype/role')
    if len(shape) > 4 or any(type(x) is not int or x < 0 for x in shape):
        raise ValueError('invalid shape')
    count = math.prod(shape) * sizes[dtype]
    if count > MAX_ARRAY or len(body) != count:
        raise ValueError('array byte cap or length mismatch')
    if endian not in {'little', 'big', 'na'} or len(strides) != len(shape):
        raise ValueError('explicit layout required')
    return dict(dtype=dtype, shape=shape, endian=endian, strides=strides, role=role,
                type=type_tag, order='C_logical', nbytes=count,
                sha256=hashlib.sha256(body).hexdigest())


class Writer:
    def __init__(self, path, binding, frame_ref):
        self.file = path.open('x'); self.binding = binding; self.frame_ref = frame_ref
        self.previous = digest(binding); self.index = 0; self.bytes = 0
        self.file.write(canonical(dict(header=binding)).decode()+'\n')

    def append(self, boundary, phase, components):
        if self.index >= MAX_EVENTS:
            raise RuntimeError('event cap')
        event = dict(index=self.index, frame=self.frame_ref[0], boundary=boundary,
                     phase=phase, components=components, native_state='UNKNOWN')
        row = dict(previous=self.previous, event=event)
        row['seal'] = digest(row)
        line = canonical(row).decode()+'\n'
        self.file.write(line); self.previous = row['seal']; self.index += 1; self.bytes += len(line)

    def close(self):
        self.file.close()
        return dict(events=self.index, final_seal=self.previous, bytes=self.bytes)


def read_verified(path):
    with path.open() as source:
        header = json.loads(next(source))['header']; previous = digest(header)
        for index, line in enumerate(source):
            row = json.loads(line); seal = row.pop('seal')
            if row['previous'] != previous or row['event']['index'] != index or digest(row) != seal:
                raise ValueError('event chain corrupt')
            previous = seal
            yield header, row['event']
