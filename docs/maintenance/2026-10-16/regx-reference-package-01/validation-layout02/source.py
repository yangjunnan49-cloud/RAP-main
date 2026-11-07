"""RegX-B1 stdlib-only identity/header/schema audit; no coordinate decoding."""
import ast
import hashlib
import json
import pathlib
import resource
import struct
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/maintenance/2026-10-16/regx-reference-package-01'
START = time.monotonic()

def save(name, obj):
    with (BASE / 'validation-layout02' / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while b := f.read(65536):
            h.update(b)
    return h.hexdigest()

def run():
    plan = json.loads((BASE / 'PACKAGE_PLAN.json').read_text())
    admitted = json.loads((BASE / 'transfer-01/ADMITTED.json').read_text())
    transfer = BASE / 'transfer-01'
    assert len(admitted['files']) == len(plan['files']) == 8
    bodies = {}
    checks = []
    for expected, actual in zip(plan['files'], admitted['files']):
        assert expected['path'] == actual['path']
        path = transfer / actual['body_file']
        assert path.parent == transfer and path.stat().st_size == expected['bytes']
        digest = sha(path)
        assert digest == actual['SHA256']
        if expected['LFS_SHA256']:
            assert digest == expected['LFS_SHA256']
            method = 'published LFS SHA256 payload identity; catalog Git OID is pointer'
        else:
            h = hashlib.sha1(('blob ' + str(path.stat().st_size) + '\0').encode('ascii'))
            with path.open('rb') as f:
                while b := f.read(65536):
                    h.update(b)
            assert h.hexdigest() == expected['Git_blob_SHA1'] == actual['payload_Git_blob_SHA1']
            method = 'published Git blob SHA1 and length; local SHA256 separately retained'
        bodies[expected['path']] = path
        checks.append(dict(path=expected['path'], bytes=path.stat().st_size, SHA256=digest, method=method))
    ledger = [json.loads(s) for s in (transfer / 'requests.jsonl').read_text().splitlines()]
    starts = [x['request'] for x in ledger if x['event'] == 'request_start']
    ends = [x['request'] for x in ledger if x['event'] == 'request_end']
    assert len(starts) == len(ends)
    all_body_bytes = 0
    for a, b in zip(starts, ends):
        assert (a['file_index'], a['hop']) == (b['file_index'], b['hop'])
        assert b['error'] is None and b['status'] in (200, 301, 302, 303, 307, 308)
        size = (transfer / b['body_file']).stat().st_size
        assert size == b['body_bytes'] and b['total_body_bytes_before'] == all_body_bytes
        all_body_bytes += size
        assert b['total_body_bytes_after'] == all_body_bytes
    assert all_body_bytes == admitted['all_body_bytes'] <= 8388608
    assert sum(x['bytes'] for x in checks) == 8162857
    ply = []
    for name in ('000.ply', '001.ply', '002.ply'):
        path = bodies[plan['scene'] + '/' + name]
        lines = []
        with path.open('rb') as f:
            while True:
                line = f.readline(4096)
                assert line and len(line) < 4096
                lines.append(line.decode('ascii').rstrip('\r\n'))
                assert f.tell() < 16384
                if lines[-1] == 'end_header':
                    offset = f.tell()
                    break
        assert lines[0] == 'ply' and any(s.startswith('format ') for s in lines)
        ply.append(dict(file=name, header_lines=lines, header_bytes=offset,
                        payload_bytes_not_decoded=path.stat().st_size-offset))
    npy = bodies[plan['scene'] + '/connection_graph.npy']
    with npy.open('rb') as f:
        assert f.read(6) == b'\x93NUMPY'
        version = tuple(f.read(2))
        assert version[0] in (1, 2, 3)
        n = struct.unpack('<H' if version[0] == 1 else '<I', f.read(2 if version[0] == 1 else 4))[0]
        assert n < 4096
        header = ast.literal_eval(f.read(n).decode('latin1'))
        data_offset = f.tell()
    assert header['shape'] == (3, 3) and header['descr'] in ('<f8', '>f8', '=f8')
    assert npy.stat().st_size - data_offset == 72
    order_rows = [line.split() for line in bodies[plan['scene'] + '/connection_graph_order.txt'].read_text().splitlines()]
    assert order_rows == [['0', '000.ply'], ['1', '001.ply'], ['2', '002.ply']]
    order = [row[1] for row in order_rows]
    assert order == ['000.ply', '001.ply', '002.ply']
    graph_text = bodies[plan['scene'] + '/connection_graph.txt'].read_text()
    assert len(graph_text.splitlines()) == 3 and all(len(s.split()) == 3 for s in graph_text.splitlines())
    # Text tokens retained as strings. No overlap calculation or scene selection.
    source_metadata = bodies[plan['scene'] + '/metadata.yaml'].read_text()
    records = []; record_count = 0; scene_count = 0
    with bodies['regx_multiview_samples_v2.jsonl'].open(encoding='utf-8') as f:
        for line_number, line in enumerate(f, 1):
            assert line.strip()
            obj = json.loads(line, parse_float=str, parse_int=str,
                             parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
            assert isinstance(obj, dict)
            record_count += 1
            if obj.get('scene') != plan['scene']:
                continue
            scene_count += 1
            inputs = obj['inputs']; assert isinstance(inputs, list)
            files = []; reference_schema = []
            for view in inputs:
                name = view['point_cloud_file']; assert name in order
                files.append(name)
                pose = view['transformation_matrix']
                assert isinstance(pose, list) and len(pose) == 4
                assert all(isinstance(row, list) and len(row) == 4 and all(isinstance(x, str) for x in row) for row in pose)
                reference_schema.append(dict(file=name, shape=[4, 4], numeric_tokens='strings, not evaluated',
                    reference_token_SHA256=hashlib.sha256(json.dumps(pose, separators=(',', ':')).encode()).hexdigest(),
                    input_keys=sorted(view)))
            assert len(set(files)) == len(files)
            records.append(dict(line=line_number, keys=sorted(obj), input_files=files,
                reference_schema=reference_schema, complete_three_view=(len(files) == 3 and set(files) == set(order))))
    assert scene_count and any(r['complete_three_view'] for r in records)
    dossier_bytes = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert dossier_bytes < 32*1024*1024
    acquisition = json.loads((BASE / 'acquisition_execution.json').read_text())
    assert acquisition['native_exit_code'] == 0 and acquisition['native_child_cap_pass']
    assert acquisition['Windows_seconds_to_observer_snapshot'] + time.monotonic()-START < 900
    save('VALIDATION.json', dict(status='VALIDATED_FIXED_AUTHOR_PACKAGE_AND_REFERENCE_SCHEMA_ONLY',
        checks=checks, requests=len(ends), redirect_requests=len(ends)-8,
        all_response_body_bytes=all_body_bytes, body_margin=8388608-all_body_bytes,
        JSONL_records=record_count, exact_scene_records=scene_count, records=records,
        ply_headers=ply, npy_header=header, npy_data_not_decoded=True,
        order=order, graph_text_tokens_evaluated=False, source_metadata_text=source_metadata,
        dossier_bytes_before_report=dossier_bytes, no_coordinate_decode=True,
        no_pose_arithmetic=True, no_model_training_solver=True,
        original_demo_authentication=False, surveyed_physical_truth='NOT ESTABLISHED',
        training_exclusion='NOT ESTABLISHED', all_scene_records_retained=True))
    print(json.dumps(dict(records=record_count, exact_scene_records=scene_count,
                          three_view=sum(r['complete_three_view'] for r in records),
                          all_response_body_bytes=all_body_bytes)))

error = None
try:
    run()
except BaseException:
    error = traceback.format_exc()
    print(error, flush=True)
finally:
    elapsed = time.monotonic()-START
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    save('validation_child_exit.json', dict(success=error is None, error=error,
        child_seconds=elapsed, maxrss_bytes=rss, memory_cap_bytes=536870912,
        memory_cap_pass=rss <= 536870912, coordinate_decode=False, GPU=0))
if error:
    raise SystemExit(1)
