"""Static review only. Never import/execute the acquired viewer or its dependencies."""
import ast
import hashlib
import json
import pathlib
import resource
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/maintenance/2026-10-16/regx-reference-code-01'
START = time.monotonic()

def save(name, obj):
    with (BASE / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write('\n')

def run():
    plan = json.loads((BASE / 'PACKAGE_PLAN.json').read_text())
    admitted = json.loads((BASE / 'transfer-01/ADMITTED.json').read_text())
    assert len(plan['files']) == len(admitted['files']) == 1
    rec = admitted['files'][0]
    source = BASE / 'transfer-01' / rec['body_file']
    data = source.read_bytes()
    assert len(data) == plan['files'][0]['bytes'] == 39369
    digest = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(b'blob 39369\0' + data).hexdigest()
    assert digest == rec['SHA256']
    assert blob == rec['payload_Git_blob_SHA1'] == plan['files'][0]['Git_blob_SHA1']
    text = data.decode('utf-8')
    tree = ast.parse(text)  # Syntax tree only; no imports or code execution.
    functions = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert all(n in functions for n in ('get', '_render', 'predict_from_transforms', 'edge_errors', 'overlap_matrix'))
    lines = text.splitlines()
    expected = {
        614: 'world = [cache.get(scene_dir / f, budget) for f in files]',
        618: 'T = np.asarray(t["transformation_matrix"], dtype=np.float64)',
        619: 'inputs.append((T[:3, :3] @ p.T).T + T[:3, 3])',
        235: 'anchor = np.linalg.inv(P[0] @ T[0])',
        240: 'M = anchor @ (Pi @ Ti)',
        255: 'T = [np.linalg.inv(np.asarray(inp["transformation_matrix"], dtype=np.float64))',
        264: 'if max(M[i, j], M[j, i]) < threshold:',
        268: 'gt_rel = np.linalg.inv(T[i]) @ T[j]',
        269: 'pr_rel = np.linalg.inv(pred[i]) @ pred[j]',
        640: 'scene_scale = float((np.vstack(world).max(0) - np.vstack(world).min(0)).max())',
    }
    for line, statement in expected.items():
        assert lines[line-1].strip() == statement
    assert functions['_render'].lineno <= 614 < functions['_render'].end_lineno
    assert functions['edge_errors'].lineno <= 255 < functions['edge_errors'].end_lineno
    ledger = [json.loads(x) for x in (BASE / 'transfer-01/requests.jsonl').read_text().splitlines()]
    ends = [x['request'] for x in ledger if x['event'] == 'request_end']
    assert len(ends) == 2 and [r['status'] for r in ends] == [307, 200]
    total = 0
    for r in ends:
        size = (BASE / 'transfer-01' / r['body_file']).stat().st_size
        assert size == r['body_bytes'] and not r['error']
        total += size
    assert total == admitted['all_body_bytes'] == 39678 <= 65536
    native = json.loads((BASE / 'acquisition_execution.json').read_text())
    assert native['native_exit_code'] == 0 and native['native_child_cap_pass']
    assert native['Windows_seconds_to_observer_snapshot'] + time.monotonic()-START < 300
    dossier = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert dossier < 2*1024*1024
    save('STATIC_AUDIT.json', dict(status='VALIDATED_PINNED_VIEWER_AUGMENTATION_REFERENCE_DIRECTION_DOC_CONFLICT',
        file_SHA256=digest, Git_blob_SHA1=blob, body_bytes=total, body_cap_margin=65536-total,
        source_lines=len(lines), function_spans={n: [functions[n].lineno, functions[n].end_lineno] for n in ('get', '_render', 'predict_from_transforms', 'edge_errors', 'overlap_matrix')},
        exact_citations={str(k): v for k, v in expected.items()},
        AST_only=True, downloaded_code_executed=False, point_or_pose_values_decoded=False,
        source_role='PLY loaded as world; JSON T applied world->perturbed view; inverse T used as reference pose',
        README_conflict='B1 pinned README151 describes input->world; viewer615-619 and255 use opposite direction',
        canonical_batch_runtime_identity='NOT AUTHENTICATED BY VIEWER',
        physical_alignment_truth='NOT INDEPENDENTLY AUTHENTICATED',
        efficacy_admission=False, dossier_bytes_before_report=dossier))
    print(json.dumps(dict(Git_blob_SHA1=blob, all_body_bytes=total, AST_only=True, downloaded_code_executed=False)))

error = None
try:
    run()
except BaseException:
    error = traceback.format_exc()
    print(error, flush=True)
finally:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    save('audit_child_exit.json', dict(success=error is None, error=error,
        child_seconds=time.monotonic()-START, maxrss_bytes=rss, memory_cap_pass=rss <= 536870912,
        downloaded_code_executed=False, GPU=0))
if error:
    raise SystemExit(1)
