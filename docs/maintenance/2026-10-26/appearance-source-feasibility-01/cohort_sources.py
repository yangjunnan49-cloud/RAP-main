"""Camera-member metadata from the complete existing cohort; no payload decode."""
import ctypes
import datetime
import hashlib
import json
import time
from pathlib import Path

START = time.monotonic()
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
PRIOR = REPO / 'docs/maintenance/2026-09-27/f2-structured-dev-01'
TREES = (
    Path('E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences'),
    Path('E:/githouse/RAP-SLAM/data/kitti/dataset/sequences'))


def lexical(path):
    assert path.stat().st_size < 1048576
    return json.loads(path.read_text(encoding='utf-8'), parse_int=str, parse_float=str,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


freeze = lexical(PRIOR / 'freeze.json')
pairs = []
members = set()
sources = []
for seq in ('00', '08'):
    path = PRIOR / f'inputs_{seq}.json'
    digest = sha(path)
    assert digest == freeze['inputs'][seq]
    rows = lexical(path)
    assert len(rows) == 100
    sources.append(dict(path=str(path), bytes=path.stat().st_size, sha256=digest))
    for row in rows:
        assert row['sequence'] == seq
        i, j = row['source_i'], row['source_j']
        assert isinstance(i, str) and isinstance(j, str) and i.isdecimal() and j.isdecimal()
        pairs.append(dict(key=row['key'], sequence=seq, source_i=i, source_j=j))
        members.update(((seq, i.zfill(6)), (seq, j.zfill(6))))
assert len(pairs) == 200 and len({row['key'] for row in pairs}) == 200
inventory = []
for tree in TREES:
    assert tree.is_dir()
    sequences = sorted(p for p in tree.iterdir() if p.is_dir())
    assert [p.name for p in sequences] == [str(n).zfill(2) for n in range(22)]
    rows = []
    for directory in sequences:
        rows.append(dict(sequence=directory.name,
            image_dirs={name: (directory / name).is_dir()
                        for name in ('image_0', 'image_1', 'image_2', 'image_3')},
            labels_dir=(directory / 'labels').is_dir(),
            calib_file_exists=(directory / 'calib.txt').is_file(),
            times_file_exists=(directory / 'times.txt').is_file()))
    inventory.append(dict(root=str(tree), sequences=rows,
        expected_anchor_camera0_existing=sum((tree / seq / 'image_0' / (frame + '.png')).is_file()
                                            for seq, frame in members)))
write('COHORT_CAMERA_MEMBERS.json', dict(
    input_sources=sources, pairs=pairs,
    camera0_members=[dict(sequence=seq, frame=frame,
        archive_member=f'dataset/sequences/{seq}/image_0/{frame}.png')
        for seq, frame in sorted(members)],
    point_image_pose_payload_reads=0, numeric_motion_or_reference_decoding=False,
    selection='All200 existing input pairs, identifiers only; no outcome/stratum/reference selection'))
write('LOCAL_INVENTORY.json', inventory)
write('RESULTS.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    decision='STANDARD_LOCAL_CAMERA_PAYLOAD_ABSENT_SOURCE_REQUIRED',
    complete_pairs=len(pairs), unique_anchor_frames=len(members),
    known_trees=len(TREES), sequences_per_tree=22,
    camera0_existing_by_tree=[r['expected_anchor_camera0_existing'] for r in inventory],
    source_identities_match=True, numeric_tokens_read_as_strings=True,
    point_image_pose_payload_reads=0, new_metrics_or_model_calls=0,
    elapsed_seconds=time.monotonic() - START,
    absence_scope='Only named standard directories and expected member paths in two known trees',
    independent_scene_or_acquisition_claim=False))
print(json.dumps(dict(pairs=len(pairs), camera0_members=len(members),
                     existing=[r['expected_anchor_camera0_existing'] for r in inventory])))
