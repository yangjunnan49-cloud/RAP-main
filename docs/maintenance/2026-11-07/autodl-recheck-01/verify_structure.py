"""Verify sealed source directories and classify additional server evidence."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parent
WORK = Path('/root/autodl-tmp/rap-workspace-20261106')
CLOUD = Path('/root/autodl-fs/rap-transfer-20261106')
OLD = Path('/root/autodl-tmp/rap-migration-20261106')
pins = json.loads((ROOT / 'PINS.json').read_bytes())
path = CLOUD / 'A7-20261104/FINAL_DIRECTORIES.jsonl'
row = next(r for r in pins['packages'] if r['path'] == 'A7-20261104/FINAL_DIRECTORIES.jsonl')
assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
directories = [json.loads(line) for line in path.read_bytes().splitlines()]
results, groups = [], Counter()
for row in directories:
    target = WORK / pins['layout'][row['root']] / row['path']
    assert target.resolve().is_relative_to(WORK)
    info = target.lstat()
    assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o755, str(target)
    groups[row['root']] += 1
    results.append(dict(path=str(target.relative_to(WORK)), passed=True))
additional = json.loads((ROOT / 'ADDITIONAL_SERVER_FILES.json').read_bytes())
prefix = 'RAP-main/docs/maintenance/2026-11-06/autodl-migration-01/remote/'
classified, unresolved = [], []
for row in additional['ordinary_files']:
    if row['path'].startswith(prefix):
        reference = OLD / row['path'][len(prefix):]
        if reference.is_file() and not reference.is_symlink():
            value = hashlib.sha256(reference.read_bytes()).hexdigest()
            if value == row['sha256']:
                classified.append(dict(row, classification='A8_raw_receipt_or_executed_source_copy', matches_reference=True))
                continue
            if row['path'] == prefix + 'LIVE_STATUS.json':
                classified.append(dict(row, classification='A8_in_progress_status_snapshot', matches_reference=False,
                    explanation='The preserved status snapshot predates the later live status; final success has separate receipts.'))
                continue
    unresolved.append(row)
value = dict(observed_utc=datetime.now(timezone.utc).isoformat(),
    passed=not unresolved and not additional['additional_links'],
    source_directories_verified=len(results), directory_policy='0755', source_root_counts=dict(groups),
    additional_files_classified=len(classified), classified_files=classified,
    unresolved_additional_files=unresolved, unexpected_links=additional['additional_links'],
    deleted_or_overwritten=False, original_Linux_owner_or_ACL_authenticated=False)
with (ROOT / 'STRUCTURE_AND_EXTRAS.json').open('x', encoding='utf-8') as output:
    json.dump(value, output, ensure_ascii=False, indent=2)
    output.write('\n')
print(json.dumps({key: val for key, val in value.items() if key not in {'classified_files'}},ensure_ascii=False))
