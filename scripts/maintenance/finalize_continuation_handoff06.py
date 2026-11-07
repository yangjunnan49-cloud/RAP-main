"""Seal independent verification and unsent dependency-request supplements."""
import ast
import json
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
DAY=ROOT/'docs/maintenance/2026-10-15'
BASE=DAY/'continuation-handoff-06'


def main():
    independent=s.read(BASE/'WINDOWS_FINAL_VERIFICATION.json')
    metadata=s.read(BASE/'WINDOWS_METADATA_VERIFICATION.json')
    assert independent['passed'] and metadata['passed']
    assert independent['frozen_available_delivery_paths']==552 and independent['retained_markers']==10
    assert metadata['catalog_point_files']==3243 and metadata['LFS_exact_matches']==metadata['nonLFS_size_matches']==0
    manifest=s.read(BASE/'DEMO_MEMBER_REQUEST.json')
    assert len(manifest['members'])==manifest['member_count']==156 and manifest['total_bytes']==478400579
    assert not manifest['sent_externally']
    paths=[BASE/n for n in ('WINDOWS_FINAL_VERIFICATION.json','WINDOWS_METADATA_VERIFICATION.json',
        'DEMO_MEMBER_REQUEST.json','AUTHOR_DATA_REQUEST_DRAFT.md')]
    sources=[ROOT/'scripts/maintenance'/n for n in ('verify_continuation_handoff06.ps1',
        'verify_official_demo_catalog_windows.ps1')]+[Path(__file__),ROOT/'AGENTS.md',DAY/'PHASE_RECORD.md']
    snap=BASE/'late_source_snapshot';snap.mkdir()
    for q in sources:
        target=snap/q.name
        with target.open('xb') as out:out.write(q.read_bytes())
        paths.append(target)
    checked=[]
    for folder in (DAY/'public-release-identity-01',DAY/'demo-source-role-01',
                   DAY/'release-backend-attribution-01',DAY/'official-demo-metadata-01'):
        for q in folder.rglob('*.py'):
            ast.parse(q.read_text());checked.append(str(q))
    validation=BASE/'LATE_CHECKS.json'
    with validation.open('x',encoding='utf-8') as out:
        json.dump(dict(passed=True,independent_verification=independent,
            independent_catalog_verification=metadata,Python_snapshot_AST_checks=len(checked),
            no_new_scientific_or_network_payload=True,ordinary_preparation_RSS='UNKNOWN',
            original_12_entry_handoff_seal_not_modified=True),out,indent=2);out.write('\n')
    paths.append(validation)
    seal=dict(files=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=s.sha(q)) for q in paths],
        scope='Independent verification and unsent dependency request, separate from original12-entry seal')
    with (BASE/'FINAL_VERIFICATION_SEAL.json').open('x',encoding='utf-8') as out:json.dump(seal,out,indent=2);out.write('\n')
    for row in s.read(BASE/'DELIVERY_SEAL.json')['files']:
        q=BASE/row['path'];assert s.sha(q)==row['sha256'] and q.stat().st_size==row['bytes']
    print(json.dumps(dict(supplement_entries=len(paths),snapshot_Python_AST_checks=len(checked),original_handoff_entries=12)),flush=True)


if __name__=='__main__':main()
