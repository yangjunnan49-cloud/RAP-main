"""FTI0 exact synthetic ambiguity witnesses and stored timestamp structure."""
import time
START = time.monotonic()
import json
import resource
import signal
import sys
import traceback
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path
import physical_source_role_feasibility as s

ROOT, SLAM = s.ROOT, s.SLAM
BASE = ROOT/'docs/maintenance/2026-10-14/frame-time-identifiability-01'
SUP = BASE/'supervision'
POSS = SLAM/'data/poss/dataset'
POP = ROOT/'docs/maintenance/2026-10-14/poss-outcome-provenance-01/layout-attempt-02'
read, sha = s.read, s.sha


def size():
    return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())


def save(name, value):
    data = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    assert size()+len(data) < 8*2**20
    with (BASE/name).open('xb') as stream:
        stream.write(data)


def freeze():
    paths = [BASE/n for n in ('OWNER_SCOPE.md', 'PROTOCOL.md')]
    paths += [Path(__file__), Path(__file__).with_name('validate_frame_time_identifiability.py'),
              Path(__file__).with_name('physical_source_role_feasibility.py'),
              Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [POSS/'sequences/00/times.txt', POSS/'sequences/00/calib_readme.txt',
              SLAM/'rap_slam/real_dataset.py', SLAM/'rap_slam/odometry.py']
    paths += [POP/n for n in ('REPORT.md', 'STATUS.json', 'CHECKS.json', 'DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance/2026-10-12/reference-physical-consistency-01'/n
              for n in ('REPORT.md', 'SOURCE_NOTES.md', 'DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance'/n for n in s.MARKERS]
    files = {str(p): dict(sha256=sha(p), bytes=p.stat().st_size) for p in paths}
    snap = BASE/'source_snapshot'
    snap.mkdir()
    for p in paths:
        if p.suffix in ('.py', '.ps1'):
            name = ('slam_' if SLAM in p.parents else 'main_')+p.name
            with (snap/name).open('xb') as stream:
                stream.write(p.read_bytes())
    save('freeze.json', dict(files=files, repositories=s.repositories(),
        caps=dict(Windows_seconds=300, RSS_bytes=128*2**20, GPU_bytes=0, whole_dossier_bytes=8*2**20)))
    save('INCOMPLETE', dict(scope='FTI0', pending='witness and independent validation'))
    print('FTI0 frozen', len(files), 'identities', flush=True)


def verify():
    f = read(BASE/'freeze.json')
    for path, row in f['files'].items():
        assert sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes']
    assert s.repositories() == f['repositories']
    return f


def mul(a, b):
    return [[sum((F(a[i][k])*F(b[k][j]) for k in range(4)), F(0))
             for j in range(4)] for i in range(4)]


def inv(a):
    b = [[F(i == j) for j in range(4)] for i in range(4)]
    for i in range(3):
        for j in range(3):
            b[i][j] = a[j][i]
        b[i][3] = -sum((F(a[j][i])*F(a[j][3]) for j in range(3)), F(0))
    return b


def serial(matrix):
    return [[str(F(x)) for x in row] for row in matrix]


def witness():
    verify()
    path = POSS/'sequences/00/times.txt'
    stamps = [Decimal(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    assert len(stamps) == 36924 and all(t.is_finite() for t in stamps)
    increments = [b-a for a, b in zip(stamps, stamps[1:])]
    positive = all(d > 0 for d in increments)
    assert positive
    grid = all(d == increments[0] for d in increments)
    timing = dict(path=str(path), rows=len(stamps), first=str(stamps[0]), last=str(stamps[-1]),
        strictly_increasing=positive, distinct_increments=len(set(increments)),
        increment_values=sorted(map(str, set(increments))) if len(set(increments)) <= 8 else None,
        exact_arithmetic_grid=grid, physical_origin_or_rate_authenticated=False)
    rz = [[0,-1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]]
    q = [[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]]
    poses = []
    rotation = [[int(i == j) for j in range(4)] for i in range(4)]
    for i in range(4):
        pose = [list(row) for row in rotation]
        pose[0][3], pose[1][3] = i, i*i
        poses.append(pose)
        rotation = mul(rotation, rz)
    changed = [mul(t, q) for t in poses]
    gauge = [mul(q, t) for t in poses]
    relative, alternate, gauged = [], [], []
    for i in range(3):
        a = mul(inv(poses[i]), poses[i+1])
        b = mul(inv(changed[i]), changed[i+1])
        c = mul(inv(gauge[i]), gauge[i+1])
        assert b == mul(mul(inv(q), a), q) and c == a
        assert [row[3] for row in a[:3]] != [row[3] for row in b[:3]]
        assert [row[:3] for row in a[:3]] != [row[:3] for row in b[:3]]
        relative.append(a)
        alternate.append(b)
        gauged.append(c)
    assert all([r[3] for r in a[:3]] == [r[3] for r in b[:3]] for a,b in zip(poses,changed))
    assert all(t[2][3] == 0 for t in poses)
    assert all(t[1][3] == 0 for t in gauge) and any(t[2][3] != 0 for t in gauge)
    nominal = [F(i,10) for i in range(4)]
    offset = [x+7 for x in nominal]
    rate = [2*x for x in nominal]
    assert [b-a for a,b in zip(nominal,nominal[1:])] == [b-a for a,b in zip(offset,offset[1:])]
    xyzi = [[1,0,0,1],[0,1,0,2],[-1,0,0,3],[0,-1,0,4]]
    point_a = [F(i,100) for i in range(4)]
    point_b = [F(i,50) for i in range(4)]
    assert point_a != point_b and len(xyzi) == len(point_a) == len(point_b)
    result = dict(decision='TRAJECTORY_SHAPE_AND_STORED_TIME_STRUCTURE_DO_NOT_AUTHENTICATE_PHYSICAL_CONVENTIONS',
        timestamp_structure=timing,
        sensor_ambiguity=dict(base=[serial(t) for t in poses], alternate=[serial(t) for t in changed],
            fixed_extrinsic=serial(q), base_relatives=[serial(t) for t in relative],
            alternate_relatives=[serial(t) for t in alternate], identical_world_position_trace=True),
        world_gauge=dict(transformed=[serial(t) for t in gauge],
            transformed_relatives=[serial(t) for t in gauged], relative_poses_unchanged=True),
        clock_ambiguity=dict(nominal=list(map(str,nominal)), offset=list(map(str,offset)),
            rate_scaled=list(map(str,rate)), actual_clock_fault_claim=False),
        point_time_ambiguity=dict(XYZI=xyzi, scan_stamp='0',
            time_A=list(map(str,point_a)), time_B=list(map(str,point_b)), real_times_assigned=False),
        controls=4, real_reference_pose_or_point_coordinates_read=False,
        chosen_new_calibration_or_reference=False, physical_truth_or_09_cause_identified=False,
        new_model_solver_fit_or_pose_metric_calls=0)
    save('witness.json', result)
    save('witness_seal.json', dict(path='witness.json', sha256=sha(BASE/'witness.json')))
    verify()
    print(json.dumps(dict(decision=result['decision'], timing=timing, controls=4)), flush=True)


def usage():
    return dict(wall_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0, artifact_bytes=size(),
        new_model_solver_fit_or_pose_metric_calls=0)


def run(stage):
    spent = sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'))
    assert spent < 300
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('FTI0 cap')))
    signal.alarm(max(1,int(300-spent)))
    ok,error = False,None
    try:
        if stage == 'freeze':
            freeze()
        elif stage == 'witness':
            witness()
        elif stage == 'validate':
            import validate_frame_time_identifiability as v
            v.validate()
        else:
            raise ValueError(stage)
        u = usage()
        assert u['peak_RSS_bytes'] <= 128*2**20 and u['artifact_bytes'] < 8*2**20
        if (SUP/'host_latest.json').exists():
            assert read(SUP/'host_latest.json')['headroom_bytes'] >= 4*2**30
        ok = True
    except BaseException as ex:
        error = repr(ex)
        traceback.print_exc()
        save('FAILURE_'+stage+'.json', dict(error=error, **usage()))
    finally:
        signal.alarm(0)
        save('supervision/'+stage+'/child_exit.json',
             dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    run(sys.argv[1])
