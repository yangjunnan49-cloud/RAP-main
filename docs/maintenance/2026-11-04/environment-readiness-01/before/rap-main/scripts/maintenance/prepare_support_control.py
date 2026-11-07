"""SC-V1 data-only orchestration of frozen SLAM helpers; no RAP inference."""
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MAIN = Path('/mnt/e/githouse/RAP-main')
SLAM = Path('/mnt/e/githouse/RAP-SLAM')
OUT = MAIN / 'docs/maintenance/2026-09-14/support-control-01'
DATA = OUT / 'data'
sys.path[:0] = [str(SLAM), str(SLAM / 'scripts')]
import hl2_data_bridge as bridge
import validate_hl_v2_data as validator


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def pairhash(seq, i, j):
    return hashlib.sha256(f'SC-V1|kitti|{seq}|{i}|{j}'.encode()).hexdigest()


def select(rows):
    chosen = []
    counts = Counter()
    reasons = []
    for kind in bridge.STRATA:
        quota = 0
        for r in sorted((r for r in rows if r['stratum'] == kind),
                        key=lambda r: r['sampling_hash']):
            key = (r['sequence'], r['source_j'])
            reason = ('unsupported' if not r['supported'] else 'query_cap'
                      if counts[key] >= 3 else 'stratum_quota' if quota >= 25
                      else 'selected')
            reasons.append(dict(sequence=r['sequence'], source_i=r['source_i'],
                                source_j=r['source_j'], stratum=kind, reason=reason))
            if reason == 'selected':
                chosen.append(r)
                quota += 1
                counts[key] += 1
    return chosen, reasons


def main():
    start = time.monotonic()
    DATA.mkdir(exist_ok=False)
    (DATA / 'INCOMPLETE').write_text('SC0 data validation and membership pending\n')
    sources = [Path(__file__), SLAM/'scripts/hl2_data_bridge.py',
               SLAM/'scripts/validate_hl_v2_data.py', SLAM/'scripts/hl1_cohort_audit.py',
               SLAM/'scripts/hl0_preflight.py', SLAM/'rap_slam/rap_backend.py',
               SLAM/'rap_slam/odometry.py', SLAM/'rap_slam/keyframes.py',
               SLAM/'rap_slam/scan_context.py', SLAM/'rap_slam/real_dataset.py']
    initial = {str(p): sha(p) for p in sources}
    save(DATA/'declaration.json', dict(protocol_sha256=sha(OUT/'PROTOCOL.md'),
         declared_utc=datetime.now(timezone.utc).isoformat(), source_hashes=initial,
         order={'discovery':['07','10'], 'confirmation':['08','09']},
         hypotheses=0))
    bridge.OUT = DATA
    bridge.COUNTS['10'] = 1201
    bridge.pairhash = pairhash
    validator.OUT = DATA
    validator.pairhash = pairhash
    roles = {}
    for role, order in [('discovery', ['07','10']), ('confirmation', ['08','09'])]:
        rows, used = [], []
        for seq in order:
            if time.monotonic() - start >= 7200:
                raise RuntimeError('SC0 elapsed compute cap reached')
            bridge.run(seq)
            validator.validate(seq)
            used.append(seq)
            rows.extend(read(DATA/seq/'evaluator_sampling.json'))
            selected, reasons = select(rows)
            counts = {s:sum(r['stratum'] == s for r in selected) for s in bridge.STRATA}
            if sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file()) > 20*2**30:
                raise RuntimeError('SC0 artifact cap reached')
            if all(n >= 20 for n in counts.values()):
                break
        # Independent membership check using a separately ordered greedy pass.
        check, query_counts, stratum_counts = [], Counter(), Counter()
        priority = {s:i for i,s in enumerate(bridge.STRATA)}
        for r in sorted((r for r in rows if r['stratum'] in priority and r['supported']),
                        key=lambda r:(priority[r['stratum']], pairhash(r['sequence'],r['source_i'],r['source_j']))):
            key = (r['sequence'], r['source_j'])
            if stratum_counts[r['stratum']] < 25 and query_counts[key] < 3:
                check.append((r['sequence'], r['source_i'], r['source_j']))
                stratum_counts[r['stratum']] += 1
                query_counts[key] += 1
        assert check == [(r['sequence'],r['source_i'],r['source_j']) for r in selected]
        assert not ({r['sequence'] for r in selected} & {'00','02','05','06'})
        save(DATA/f'{role}_evaluator.json', selected)
        save(DATA/f'{role}_sampling_reasons.json', reasons)
        save(DATA/f'{role}_inputs.json', [{k:r[k] for k in
             ['sequence','source_i','source_j','support_i','support_j']} for r in selected])
        roles[role] = dict(sequences=used, selected=len(selected), counts=counts,
                          adequate=len(selected)>=60 and all(n>=10 for n in counts.values()),
                          candidate_count=len(rows), pooled_selection_independently_verified=True)
        print(role, json.dumps(roles[role]), flush=True)
    assert all(sha(p) == h for p,h in initial.items())
    declaration = read(DATA/'declaration.json')
    assert sha(OUT/'PROTOCOL.md') == declaration['protocol_sha256']
    sufficient = all(r['adequate'] for r in roles.values())
    save(DATA/'cohort_freeze.json', dict(protocol='SC-V1',
         frozen_utc=datetime.now(timezone.utc).isoformat(), roles=roles,
         adequate=sufficient, hypotheses_generated_before_freeze=0,
         hashes={p.name:sha(p) for p in DATA.glob('*_inputs.json')},
         evaluator_hashes={p.name:sha(p) for p in DATA.glob('*_evaluator.json')},
         protocol_sha256=declaration['protocol_sha256'], source_hashes=initial))
    save(DATA/'decision.json', dict(decision='READY_FOR_SC1' if sufficient else 'INCONCLUSIVE_DATA',
         roles=roles, hypotheses=0, training_started=False,
         neural_expansion='STOPPED', wall_s=time.monotonic()-start))
    for seq in {s for r in roles.values() for s in r['sequences']}:
        (DATA/seq/'INCOMPLETE').unlink()
    (DATA/'INCOMPLETE').unlink()
    save(DATA/'artifact_hashes.json', {str(p.relative_to(DATA)):sha(p)
         for p in sorted(DATA.rglob('*')) if p.is_file()})
    print('SC0 complete:', 'READY_FOR_SC1' if sufficient else 'INCONCLUSIVE_DATA', flush=True)


if __name__ == '__main__':
    main()
