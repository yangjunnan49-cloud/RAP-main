"""Prospective audit-only read-set correction for skipped completed pairs."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, obj):
    with (ROOT / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


assert not (ROOT / 'AUDIT_IOFIX_FREEZE.json').exists()
assert not (ROOT / 'runtime03/audit').exists() and not (ROOT / 'runtime03/audit.PREFLIGHT.json').exists()
for name in ('SOURCE_FREEZE.json', 'RUNTIME03_FREEZE.json'):
    for e in json.loads((ROOT / name).read_text())['files']:
        assert sha(ROOT / e['path']) == e['sha256']
inputs = json.loads((ROOT / 'PREDICTION_INPUTS.json').read_text())
partials = json.loads((ROOT / 'RUNTIME03_PARTIAL_INDEX.json').read_text())['entries']
preserved = {e['record']['key'] for e in partials}
remaining = [r for r in inputs['pairs'] if r['key'] not in preserved]
assert len(remaining) == 193 and preserved == {r['key'] for r in inputs['pairs'][:7]}
required = {(r['sequence'], r[f].zfill(6)) for r in remaining for f in ('source_i', 'source_j')}
index = json.loads((ROOT / 'features/INDEX.json').read_text())
paths = [str(ROOT / 'features' / e['cache']) for e in index if (e['sequence'], e['frame']) in required]
paths += [e['path'] for e in inputs['calibrations']] + [e['path'] for e in partials]
save('AUDIT_EXPECTED_READS.json', {'paths': paths, 'required_remaining_feature_caches': len(required),
    'calibrations': 2, 'preserved_evidence_reads': 7,
    'derived_only_from_frozen_pair_membership_and_resume_rule': True,
    'reference_metrics_or_actual_audited_read_log_used_to_select_paths': False})
source = (ROOT / 'audit_runtime03.py').read_text()
before = "    allowed = {normalize(lib.ROOT / 'features' / e['cache']) for e in feature_index} | {normalize(e['path']) for e in inputs['calibrations']}"
after = "    allowed = {normalize(p) for p in lib.load(lib.ROOT / 'AUDIT_EXPECTED_READS.json')['paths']}"
assert source.count(before) == 1
header = "\nfor item in lib.load(lib.ROOT / 'AUDIT_IOFIX_FREEZE.json')['files']:\n    assert lib.sha(lib.ROOT / item['path']) == item['sha256']\n"
changed = source.replace(before, after).replace('\nOUT = ', header + '\nOUT = ', 1)
assert changed.replace(after, before).replace(header, '', 1) == source
with (ROOT / 'audit_runtime03_iofix.py').open('x', encoding='utf-8', newline='\n') as f:
    f.write(changed)
ast.parse(changed)
host = (ROOT / 'host_runtime03.ps1').read_text()
changed_host = host.replace("ValidateSet('probe','predict','evaluate','audit')", "ValidateSet('audit')")
changed_host = changed_host.replace("'SOURCE_FREEZE.json','RUNTIME03_FREEZE.json'", "'SOURCE_FREEZE.json','RUNTIME03_FREEZE.json','AUDIT_IOFIX_FREEZE.json'")
changed_host = changed_host.replace("audit='audit_runtime03.py'", "audit='audit_runtime03_iofix.py'")
with (ROOT / 'host_audit_iofix.ps1').open('x', encoding='utf-8', newline='\n') as f:
    f.write(changed_host)
save('AUDIT_IOFIX_PROOF.json', {'original_audit_sha256': sha(ROOT / 'audit_runtime03.py'),
    'new_audit_sha256': sha(ROOT / 'audit_runtime03_iofix.py'), 'exact_reverse_transform_recovers_source': True,
    'change': 'Actual required reads are remaining-193 feature caches plus two P0 and seven retained evidence files; five caches used only by preserved pairs need not be read again',
    'all_273_feature_caches_still_sealed_and_audited': True, 'scientific_functions_or_metrics_changed': False,
    'audit_not_previously_launched': True, 'original_180s_audit_cap_unchanged': True})
names = ['prepare_audit_iofix.py', 'AUDIT_EXPECTED_READS.json', 'AUDIT_IOFIX_PROOF.json', 'audit_runtime03_iofix.py', 'host_audit_iofix.ps1']
save('AUDIT_IOFIX_FREEZE.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'files': [{'path': n, 'bytes': (ROOT/n).stat().st_size, 'sha256': sha(ROOT/n)} for n in names]})
print('Audit-only exact read-set correction frozen from pair membership; no reference metric inspected')
