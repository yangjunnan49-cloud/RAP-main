"""POP0 exact AST layout correction; original failed evidence preserved."""
import time
START = time.monotonic()
import ast
import json
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s

ROOT, SLAM = s.ROOT, s.SLAM
OLD = ROOT / 'docs/maintenance/2026-10-14/poss-outcome-provenance-01'
BASE = OLD / 'layout-attempt-02'
SUP = BASE / 'supervision'
read, sha = s.read, s.sha


def size():
    return sum(p.stat().st_size for p in OLD.rglob('*') if p.is_file())


def save(path, value):
    body = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    assert size() + len(body) < 16*2**20
    with path.open('xb') as stream:
        stream.write(body)


def derive(path):
    tree = ast.parse(path.read_text())
    class Layout(ast.NodeTransformer):
        def __init__(self):
            self.columns = self.routes = 0
        def visit_Constant(self, node):
            if type(node.value) is int and node.value == 8:
                self.columns += 1
                return ast.copy_location(ast.Constant(12), node)
            if node.value == str(OLD.relative_to(ROOT)):
                self.routes += 1
                return ast.copy_location(ast.Constant(str(BASE.relative_to(ROOT))), node)
            return node
    edit = Layout()
    changed = edit.visit(tree)
    expected = 2 if path.name == 'poss_outcome_provenance.py' else 1
    assert edit.columns == expected and edit.routes == 1
    ast.fix_missing_locations(changed)
    return ast.unparse(changed)+'\n', dict(column_literals=expected, output_routes=1,
                                           no_other_AST_change=True)


def bind():
    original = read(OLD / 'freeze.json')
    assert not read(OLD / 'supervision/census/child_exit.json')['success']
    assert (OLD / 'INCOMPLETE').exists() and not (OLD / 'outcome_census.json').exists()
    files = dict(original['files'])
    for path, row in files.items():
        assert sha(path) == row['sha256']
    evidence = [dict(path=str(p.relative_to(OLD)), sha256=sha(p), bytes=p.stat().st_size)
                for p in sorted(OLD.rglob('*')) if p.is_file() and BASE not in p.parents]
    save(OLD / 'ORIGINAL_AVAILABLE_SEAL.json', dict(entries=len(evidence), files=evidence,
         status='TRAJECTORY_LAYOUT_ASSERTION_STOP_NO_NEW_METRICS'))
    extra = [Path(__file__), BASE / 'PROTOCOL.md', OLD / 'ORIGINAL_AVAILABLE_SEAL.json',
             SLAM / 'rap_slam/sequence.py', SLAM / 'scripts/run_pipeline.py']
    variants = {}
    snap = BASE / 'source_snapshot'
    snap.mkdir()
    for name in ('poss_outcome_provenance.py', 'validate_poss_outcome_provenance.py'):
        path = Path(__file__).with_name(name)
        text, changes = derive(path)
        target = snap / ('layout02_' + name)
        with target.open('x', encoding='utf-8') as stream:
            stream.write(text)
        extra.append(target)
        variants[name] = dict(original_path=str(path), path=str(target), changes=changes)
    for path in extra:
        files[str(path)] = dict(sha256=sha(path), bytes=path.stat().st_size)
    with (snap / Path(__file__).name).open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    save(BASE / 'freeze.json', dict(files=files, repositories=original['repositories'],
        caps=original['caps'], variants=variants, original_failure_retained=True,
        combined_cap_includes_original_attempts=True))
    save(BASE / 'INCOMPLETE', dict(scope='POP0_LAYOUT02', pending='census and validation'))
    print('POP0 layout02 frozen', len(files), 'identities', flush=True)


def check():
    f = read(BASE / 'freeze.json')
    for path, row in f['files'].items():
        assert sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes']
    for row in read(OLD / 'ORIGINAL_AVAILABLE_SEAL.json')['files']:
        assert sha(OLD / row['path']) == row['sha256']
    assert s.repositories() == f['repositories']
    return f


def execute(name, function):
    variant = check()['variants'][name]
    text, changes = derive(Path(variant['original_path']))
    assert changes == variant['changes'] and text == Path(variant['path']).read_text()
    namespace = dict(__name__='pop0_bound_layout02', __file__=variant['original_path'])
    exec(compile(text, variant['path'], 'exec'), namespace)
    namespace[function]()
    check()


def usage():
    return dict(wall_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0, artifact_bytes=size(),
        new_model_calls=0, new_solver_calls=0, new_fit_calls=0, new_pose_metric_calls=0)


def run(stage):
    spent = sum(read(p)['wall_seconds'] for q in (OLD/'supervision', SUP) for p in q.glob('*/exit.json'))
    assert spent < 600
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('POP0 combined cap')))
    signal.alarm(max(1, int(600-spent)))
    ok, error = False, None
    try:
        if stage == 'bind':
            bind()
        elif stage == 'census':
            execute('poss_outcome_provenance.py', 'census')
        elif stage == 'validate':
            execute('validate_poss_outcome_provenance.py', 'validate')
        else:
            raise ValueError(stage)
        u = usage()
        assert u['peak_RSS_bytes'] <= 512*2**20 and u['artifact_bytes'] < 16*2**20
        if (SUP/'host_latest.json').exists():
            assert read(SUP/'host_latest.json')['headroom_bytes'] >= 4*2**30
        ok = True
    except BaseException as ex:
        error = repr(ex)
        traceback.print_exc()
        save(BASE/('FAILURE_'+stage+'.json'), dict(error=error, **usage()))
    finally:
        signal.alarm(0)
        save(SUP/stage/'child_exit.json', dict(success=ok, error=error,
                                              full_resource_capture=True, **usage()))
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    run(sys.argv[1])
