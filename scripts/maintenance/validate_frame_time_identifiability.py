"""Independent exact FTI0 equations, no import of runner algebra helpers."""
import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'docs/maintenance/2026-10-14/frame-time-identifiability-01'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for body in iter(lambda: stream.read(65536), b''):
            h.update(body)
    return h.hexdigest()


def matrix(values):
    return tuple(tuple(Fraction(x) for x in row) for row in values)


def product(a,b):
    result = []
    columns = list(zip(*b))
    for row in a:
        result.append(tuple(sum(x*y for x,y in zip(row,column)) for column in columns))
    return tuple(result)


def inverse(a):
    rows = []
    for i in range(3):
        row = tuple(a[j][i] for j in range(3))
        rows.append(row+(-sum(row[j]*a[j][3] for j in range(3)),))
    return tuple(rows)+((Fraction(0),Fraction(0),Fraction(0),Fraction(1)),)


def validate():
    f, w = read(BASE/'freeze.json'), read(BASE/'witness.json')
    assert sha(BASE/'witness.json') == read(BASE/'witness_seal.json')['sha256']
    for path,row in f['files'].items():
        assert sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes']
    t = w['timestamp_structure']
    rows = []
    with Path(t['path']).open() as stream:
        for line in stream:
            if line.strip():
                value = Decimal(line.strip())
                assert value.is_finite()
                rows.append(value)
    deltas = set()
    for i in range(1,len(rows)):
        assert rows[i] > rows[i-1]
        deltas.add(rows[i]-rows[i-1])
    assert len(rows) == t['rows'] == 36924
    assert str(rows[0]) == t['first'] and str(rows[-1]) == t['last']
    assert len(deltas) == t['distinct_increments']
    assert t['strictly_increasing'] and t['exact_arithmetic_grid'] == (len(deltas)==1)
    assert t['increment_values'] == (sorted(map(str,deltas)) if len(deltas)<=8 else None)
    assert not t['physical_origin_or_rate_authenticated']
    a = w['sensor_ambiguity']
    base = list(map(matrix,a['base']))
    alternate = list(map(matrix,a['alternate']))
    q = matrix(a['fixed_extrinsic'])
    gauge = list(map(matrix,w['world_gauge']['transformed']))
    identity = matrix([[int(i==j) for j in range(4)] for i in range(4)])
    for i in range(4):
        assert base[i][0][3] == i and base[i][1][3] == i*i and base[i][2][3] == 0
        assert alternate[i] == product(base[i],q)
        assert tuple(r[3] for r in base[i][:3]) == tuple(r[3] for r in alternate[i][:3])
        assert gauge[i] == product(q,base[i]) and gauge[i][1][3] == 0
        for candidate in (base[i],alternate[i],gauge[i]):
            assert product(candidate,inverse(candidate)) == identity
    assert any(t[2][3] != 0 for t in gauge)
    for i in range(3):
        relative = product(inverse(base[i]),base[i+1])
        changed = product(inverse(alternate[i]),alternate[i+1])
        same = product(inverse(gauge[i]),gauge[i+1])
        assert relative == matrix(a['base_relatives'][i]) == same
        assert changed == matrix(a['alternate_relatives'][i])
        assert changed == product(product(inverse(q),relative),q)
        assert tuple(r[:3] for r in changed[:3]) != tuple(r[:3] for r in relative[:3])
        assert tuple(r[3] for r in changed[:3]) != tuple(r[3] for r in relative[:3])
        assert same == matrix(w['world_gauge']['transformed_relatives'][i])
    clock = w['clock_ambiguity']
    nominal,offset,rate = [list(map(Fraction,clock[key])) for key in ('nominal','offset','rate_scaled')]
    assert nominal == [Fraction(i,10) for i in range(4)]
    assert all(b-a == 7 and c == 2*a for a,b,c in zip(nominal,offset,rate))
    for times in (nominal,offset,rate):
        assert all(b>a for a,b in zip(times,times[1:]))
    p = w['point_time_ambiguity']
    assert len(p['XYZI']) == len(p['time_A']) == len(p['time_B']) == 4
    assert all(len(row)==4 for row in p['XYZI']) and p['time_A'] != p['time_B']
    for key,denominator in (('time_A',100),('time_B',50)):
        assert list(map(Fraction,p[key])) == [Fraction(i,denominator) for i in range(4)]
    assert not p['real_times_assigned'] and not clock['actual_clock_fault_claim']
    assert w['controls']==4 and w['new_model_solver_fit_or_pose_metric_calls']==0
    for key in ('real_reference_pose_or_point_coordinates_read','chosen_new_calibration_or_reference',
                'physical_truth_or_09_cause_identified'):
        assert not w[key]
    result = dict(passed=True, frozen_identities=len(f['files']), controls=4,
        synthetic_poses=12, timestamp_rows=36924, all_rational_equations_exact=True,
        actual_timestamp_structure=t, no_real_frame_or_clock_fault_identified=True,
        decision=w['decision'])
    with (BASE/'validation.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(result),flush=True)
