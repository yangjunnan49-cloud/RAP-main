"""Synthetic boundary signature prototype. Never imports or invokes native workloads."""
import hashlib
import json
import math

ROLES = {'prepared_input', 'derived_input', 'state', 'output'}
SIZES = {'f4': 4, 'f8': 8, 'u1': 1, 'u4': 4, 'i4': 4, 'i8': 8}
MAX_ARTIFACT = 65536
MAX_EVENTS = 256


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def artifact(data, dtype, shape, byteorder, role):
    if dtype not in SIZES or role not in ROLES:
        raise ValueError('unknown dtype or component role')
    if not isinstance(shape, (list, tuple)) or len(shape) > 4:
        raise ValueError('explicit shape with rank <= 4 required')
    if any(type(n) is not int or n < 0 for n in shape):
        raise ValueError('shape dimensions must be nonnegative integers')
    if byteorder not in ({'na'} if SIZES[dtype] == 1 else {'little', 'big'}):
        raise ValueError('explicit byte order required')
    expected = math.prod(shape) * SIZES[dtype]
    if expected > MAX_ARTIFACT:
        raise ValueError('synthetic artifact exceeds byte cap')
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError('explicit contiguous bytes required')
    if isinstance(data, memoryview) and not data.c_contiguous:
        raise ValueError('contiguous C byte layout required')
    snapshot = bytes(data)
    if len(snapshot) != expected:
        raise ValueError('shape and byte length disagree')
    return dict(dtype=dtype, shape=list(shape), byteorder=byteorder, order='C',
                role=role, nbytes=len(snapshot), sha256=hashlib.sha256(snapshot).hexdigest())


def validate_descriptor(value):
    required = {'dtype', 'shape', 'byteorder', 'order', 'role', 'nbytes', 'sha256'}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError('descriptor schema mismatch')
    dtype, shape = value['dtype'], value['shape']
    if dtype not in SIZES or value['role'] not in ROLES or value['order'] != 'C':
        raise ValueError('descriptor dtype/role/order invalid')
    if not isinstance(shape, list) or len(shape) > 4 or any(type(n) is not int or n < 0 for n in shape):
        raise ValueError('descriptor shape invalid')
    expected = math.prod(shape) * SIZES[dtype]
    if expected > MAX_ARTIFACT or type(value['nbytes']) is not int or value['nbytes'] != expected:
        raise ValueError('descriptor size invalid')
    if value['byteorder'] not in ({'na'} if SIZES[dtype] == 1 else {'little', 'big'}):
        raise ValueError('descriptor byteorder invalid')
    h = value['sha256']
    if not isinstance(h, str) or len(h) != 64 or any(c not in '0123456789abcdef' for c in h):
        raise ValueError('descriptor sha256 invalid')


def stream(binding, events):
    if not isinstance(binding, dict) or not binding:
        raise ValueError('nonempty source/runtime/config binding required')
    if len(events) > MAX_EVENTS:
        raise ValueError('event cap exceeded')
    rows = []
    seen = set()
    previous = digest({'binding': binding})
    for index, event in enumerate(events):
        if set(event) != {'id', 'boundary', 'components', 'state_coverage'}:
            raise ValueError('event schema mismatch')
        event_id = event['id']
        if type(event_id) is not str or not event_id or event_id in seen:
            raise ValueError('event IDs must be unique nonempty strings')
        seen.add(event_id)
        if event['state_coverage'] not in {'unobserved', 'recorded_only'}:
            raise ValueError('this prototype cannot certify complete native state')
        if not event['components'] or not isinstance(event['boundary'], str):
            raise ValueError('boundary and components required')
        for name, value in event['components'].items():
            if not isinstance(name, str) or not name:
                raise ValueError('component schema mismatch')
            validate_descriptor(value)
        # Freeze nested mutable dictionaries and bind both order and content.
        frozen = json.loads(canonical(event))
        row = dict(index=index, previous=previous, event=frozen)
        row['seal'] = digest(row)
        rows.append(row)
        previous = row['seal']
    return dict(binding=json.loads(canonical(binding)), events=rows, final_seal=previous)


def verify(value):
    if set(value) != {'binding', 'events', 'final_seal'}:
        raise ValueError('stream schema mismatch')
    original_events = [row['event'] for row in value['events']]
    if stream(value['binding'], original_events) != value:
        raise ValueError('stream seal, index, sequence or metadata changed')


def compare(left, right):
    verify(left)
    verify(right)
    if left['binding'] != right['binding']:
        return dict(status='incomparable_bindings')
    for index, (lrow, rrow) in enumerate(zip(left['events'], right['events'])):
        le, re = lrow['event'], rrow['event']
        if le == re:
            continue
        if any(le[k] != re[k] for k in ('id', 'boundary', 'state_coverage')):
            return dict(status='event_metadata_difference', first_index=index)
        names = sorted(set(le['components']) | set(re['components']))
        changed = [name for name in names if le['components'].get(name) != re['components'].get(name)]
        roles = {event['components'][name]['role'] for event in (le, re)
                 for name in changed if name in event['components']}
        if roles == {'output'}:
            status = 'output_difference_cause_unknown'
        elif roles == {'derived_input'}:
            status = 'derived_input_difference'
        elif roles == {'prepared_input'}:
            status = 'prepared_input_difference'
        else:
            status = 'recorded_state_or_mixed_difference'
        return dict(status=status, first_index=index, components=changed)
    if len(left['events']) != len(right['events']):
        return dict(status='event_count_difference', first_index=min(len(left['events']), len(right['events'])))
    return dict(status='recorded_bytes_equal_native_state_unknown')
