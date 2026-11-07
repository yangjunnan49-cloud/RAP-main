"""Read-only final identity audit, with one SHA read per unique file."""
from pathlib import Path
import local_motion_common as c
import rlp2_common as r


def mounted(value):
    value = str(value).replace('\\', '/')
    if len(value) > 2 and value[1] == ':':
        value = '/mnt/' + value[0].lower() + value[2:]
    return Path(value)


cache = {}


def digest(path):
    path = mounted(path)
    if path not in cache:
        cache[path] = c.sha(path)
    return cache[path]


def stage(base):
    freeze = c.read(base / 'freeze.json')
    for path, expected in freeze['files'].items():
        assert digest(path) == expected, path
    seal = c.read(base / 'bank_seal.json')
    assert digest(base / 'freeze.json') == seal['freeze_sha256']
    manifest = seal.get('manifest', 'bank.json')
    assert digest(base / manifest) == seal.get('manifest_sha256', seal.get('results_sha256'))
    folder = seal.get('folder', 'bank')
    actual = {str(p.relative_to(base)): digest(p)
              for p in sorted((base / folder).rglob('*')) if p.is_file()}
    assert actual == seal['files'], base
    validation = c.read(base / 'validation.json')
    validated = c.read(base / 'validation_seal.json')
    assert validation['passed'] and not (base / 'INCOMPLETE').exists()
    for field, name in [('validation_sha256', 'validation.json'),
                        ('bank_seal_sha256', 'bank_seal.json'),
                        ('freeze_sha256', 'freeze.json')]:
        assert digest(base / name) == validated[field]
    return dict(stage=str(base.relative_to(c.MAIN)), freeze_identities=len(freeze['files']),
                bank_files=len(actual), validation_sha256=digest(base / 'validation.json'))


def historical_delivery(base):
    seal = c.read(base / 'DELIVERY_SEAL.json')
    checked, historical = 0, []
    for path, expected in seal['files'].items():
        pp = mounted(path)
        if pp.name in ('AGENTS.md', 'PHASE_RECORD.md'):
            historical.append(str(pp))
            continue
        assert digest(pp) == expected, path
        checked += 1
    return dict(stage=str(base.relative_to(c.MAIN)), sealed_files_checked=checked,
                mismatches=0, historical_mutable_handoff_entries=historical)


def run():
    stages = [r.NUM, r.FULL, r.LAB]
    stages += [r.FIT / f'{seed}_{arm}' for seed in r.SEEDS for arm in ('D', 'I', 'J')]
    stages += [r.PRED, r.DIAG, r.EVAL]
    checked = [stage(base) for base in stages]
    old = [historical_delivery(r.OLD), historical_delivery(r.DESIGN),
           historical_delivery(c.MAIN / 'docs/maintenance/2026-10-07/readout-supervision-design-01')]
    token = stage(c.MAIN / 'docs/maintenance/2026-10-07/joint-token-preflight-01')
    assert digest(r.HELPER) == digest(r.B / 'source_staging/motion_supervised_readout.py')
    failures = [x for x in c.read(r.B / 'RESOURCE_LOG.json') if not x['passed']]
    if failures:
        amendment = c.read(r.B / 'resource-amendment-01/freeze.json')
        assert amendment['approved'] and amendment['original_budget_failures'] == len(failures) == 1
    c.save(r.B / 'CLOSURE_CHECKS.json', dict(utc=c.now(), passed=True,
        scientific_stages=checked, historical_delivery_checks=old,
        original_TR0_stage=token, unique_files_hashed=len(cache),
        helper_matches_staging=True, RLP2_numeric_failures=0,
        original_budget_stops=len(failures),
        all_stage_markers_complete=True, **r.usage()))
    r.finish('closure_identity_audit')
    print('RLP2 closure identity audit PASS', len(checked), len(cache), flush=True)


if __name__ == '__main__':
    run()
