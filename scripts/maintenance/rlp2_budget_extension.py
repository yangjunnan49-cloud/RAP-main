"""Owner-approved isolated combined-time amendment; no scientific source edit."""
import json
import runpy
import sys
from pathlib import Path
import rlp2_common as r
import rlp1_common as original
import local_motion_common as c

AMEND = r.B / 'resource-amendment-01'
LIMIT = 6300
SCRIPTS = dict(predictions='rlp2_predictions.py', evaluation='rlp2_evaluate.py',
    validate_evaluation='validate_rlp2_evaluation.py', closure='rlp2_close_audit.py',
    delivery='rlp2_delivery.py')


def cap(stage_limit=3600):
    used = r.usage()
    prior = sum(x['wall_s'] for x in c.read(r.B / 'RESOURCE_LOG.json'))
    assert used['wall_s'] <= stage_limit, used
    assert prior + used['wall_s'] <= LIMIT, (prior, used)
    assert used['rss_gib'] <= 4 and used['gpu_gib'] <= 3 and used['artifact_bytes'] <= 4 * 2**30, used
    return used


def freeze():
    approval = c.read(AMEND / 'OWNER_AUTHORIZATION.json')
    assert approval['approved'] and approval['combined_limit_s'] == LIMIT
    dependencies = [Path(__file__), AMEND / 'OWNER_AUTHORIZATION.json', AMEND / 'AMENDMENT.md',
                    r.B / 'RESOURCE_EXTENSION_DRAFT.md', r.B / 'PROTOCOL.md',
                    Path(__file__).with_name('rlp2_common.py'),
                    Path(__file__).with_name('rlp1_common.py')]
    dependencies += [Path(__file__).with_name(name) for name in SCRIPTS.values()]
    dependencies += [r.FIT / f'{seed}_{arm}/validation_seal.json'
                    for seed in r.SEEDS for arm in ('D', 'I', 'J')]
    # Original controller must finish or stop before this log writer starts.
    original_log = c.read(r.B / 'RESOURCE_LOG.json')
    failures = [x for x in original_log if not x['passed']]
    assert len(failures) <= 1
    if failures:
        assert sum(x['wall_s'] for x in original_log) > 3600
        assert all(x['gpu_gib'] <= 3 and x['rss_gib'] <= 4 and x['artifact_bytes'] <= 4 * 2**30 for x in original_log)
    snapshots = AMEND / 'original-budget-snapshot'
    snapshots.mkdir()
    (snapshots / 'RESOURCE_LOG.json').write_text(json.dumps(original_log, indent=2) + '\n')
    (snapshots / 'STATUS.json').write_bytes((r.B / 'STATUS.json').read_bytes())
    for path in r.B.glob('FAILURE*'):
        (snapshots / path.name).write_bytes(path.read_bytes())
    overrides = {}
    for field in ('PRED', 'DIAG', 'EVAL'):
        base = getattr(r, field)
        if (base / 'bank').exists() and not (base / 'bank_seal.json').exists():
            overrides[field] = str(base / 'attempt-02')
        if (base / 'INCOMPLETE').exists():
            (snapshots / f'{field}_INCOMPLETE').write_bytes((base / 'INCOMPLETE').read_bytes())
    c.save(AMEND / 'PATHS.json', overrides)
    dependencies.append(AMEND / 'PATHS.json')
    c.save(AMEND / 'freeze.json', dict(utc=c.now(), approved=True, combined_limit_s=LIMIT,
        previous_combined_limit_s=3600, no_scientific_settings_changed=True,
        no_new_optimizer_or_backbone_inference=True, original_budget_failures=len(failures),
        files={str(p): c.sha(p) for p in sorted(set(dependencies))},
        original_snapshots={str(p.relative_to(AMEND)): c.sha(p) for p in snapshots.iterdir()}))
    r.finish('owner_resource_amendment_freeze')
    print('RLP2 owner-approved time amendment frozen', LIMIT, overrides, flush=True)


def apply():
    frozen = c.read(AMEND / 'freeze.json')
    assert frozen['approved'] and frozen['combined_limit_s'] == LIMIT
    for path, expected in frozen['files'].items():
        assert c.sha(path) == expected, path
    for name, path in c.read(AMEND / 'PATHS.json').items():
        setattr(r, name, Path(path))
    r.COMBINED_LIMIT = LIMIT
    r.RESOURCE_AMENDMENT = AMEND


if __name__ == '__main__':
    original.cap = cap
    r.cap = cap
    if sys.argv[1] == 'freeze':
        freeze()
    else:
        apply()
        name = sys.argv[1]
        assert name in SCRIPTS, 'Only remaining prediction/evaluation/closure scope is authorized'
        target = Path(__file__).with_name(SCRIPTS[name])
        sys.argv = [str(target)] + sys.argv[2:]
        runpy.run_path(str(target), run_name='__main__')
