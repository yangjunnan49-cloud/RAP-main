"""Read-only owner closeout proof; no UI, account query, WSL or numerical stage."""
import hashlib,json
from pathlib import Path
CLOSE=Path(__file__).resolve().parent
ROOT=CLOSE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    digest=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()
def verify():
    count=0;size=0
    for scope in ('identity-evidence-01','stereo-source-01','stereo-support-01','stereo-alias-01','windows-lease-01'):
        folder=ROOT/scope
        for entry in read(folder/'DELIVERY_SEAL.json')['files']:
            path=folder/entry['path']
            assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],str(path)
            count+=1;size+=entry['bytes']
    assert count==2047 and size==297738079
    for scope in ('stereo-source-01','stereo-support-01','stereo-support-01/integration02','stereo-alias-01','windows-lease-01'):
        for entry in read(ROOT/scope/'SOURCE_FREEZE.json')['files']:
            path=Path(entry['path'])
            assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],str(path)
    groups=read(ROOT/'stereo-support-01/GROUP_COVERAGE.json')
    def group(name,sequence='all'):
        return next(row for row in groups['groups'] if row['group']==name and row['sequence']==sequence)
    assert (group('all200')['eligible'],group('positive')['eligible'])==(141,109)
    assert [group('oldunique27',s)['eligible'] for s in ('00','08')]==[18,3]
    assert not groups['target_coverage_screen'] and not groups['candidate_scoring_admitted']
    audit=read(ROOT/'stereo-support-01/integration02/audit/RESULT.json')
    assert audit['passed'] and audit['scalar_disparity_sample_checks']==10682 and audit['independent_covariance_checks']==400
    packet=read(ROOT/'stereo-support-01/integration02/packet/RESULT.json')
    assert (packet['byte_reused_maps'],packet['newly_computed_maps'])==(135,138)
    failure=read(ROOT/'stereo-support-01/packet/HOST_EXIT.json')
    assert not failure['passed'] and 'PermissionError' in failure['error'] and failure['owned_child_reaped']
    stages=[ROOT/'stereo-source-01'/s for s in ('controls','packet','audit')]
    stages += [ROOT/'stereo-support-01'/s for s in ('controls','packet')]
    stages += [ROOT/'stereo-support-01/integration02'/s for s in ('controls','packet','audit')]
    stages += [ROOT/'stereo-alias-01/controls']
    assert len(stages)==9 and all(read(stage/'HOST_EXIT.json')['owned_child_reaped'] for stage in stages)
    guard=read(ROOT/'windows-lease-01/RESULT.json')
    assert guard['passed'] and guard['all_owned_hosts_reaped'] and len(guard['cases'])==8
    assert sum(case['child_launched'] for case in guard['cases'])==6
    assert all(case['expected_outcome_passed'] and (case['child_reaped'] if case['child_launched'] else True) for case in guard['cases'])
    proof=read(CLOSE/'AUTHORITY_PROOF.json')
    previous=Path(proof['previous_backup']).read_bytes()
    actual=Path(proof['authority_path']).read_bytes()
    assert sha(proof['authority_path'])==proof['current_sha256']
    assert actual[proof['prefix_bytes']:]==previous and sha(proof['previous_backup'])==proof['previous_sha256']
    old_proof=read(ROOT/'AUTHORITY_UPDATE_PROOF.json')
    assert sha(proof['previous_backup'])==old_proof['current_sha256']
    older=Path(old_proof['previous_backup']).read_bytes()
    assert previous[old_proof['prefix_bytes']:]==older
    active=read(ROOT/'identity-evidence-01/AUTHORITY_UPDATE_ACTIVE.json')
    original=(ROOT/'identity-evidence-01/authority_before/RAP-main.AGENTS.md').read_bytes()
    assert older[active['prefix_bytes']:]==original
    assert sha(proof['parent_path'])==proof['parent_sha256']==old_proof['parent_current_sha256']
    account=read(ROOT/'ACCOUNT_STATUS.json')
    assert not account['ordinaryUsageAllowed'] and account['primary']['usedPercent']==83 and account['secondary']['usedPercent']==100
    assert not account['five_hour_exhaustion_observed'] and not account['availability_refreshed_during_owner_closeout']
    assert not account['automatic_reset_resume'] and not account['queued_work'] and account['owner_requested_round_close']
    assert sha(ROOT/'ACCOUNT_STATUS.json')==sha(CLOSE/'LAST_ACCOUNT_TOOL_OBSERVATION.json')
    stale=read(CLOSE/'before/ACCOUNT_STATUS.json')
    assert stale['ordinaryUsageAllowed'] and stale['primary']['usedPercent']==76 and stale['secondary']['usedPercent']==99
    for seal_path in (CLOSE/'DELIVERY_SEAL.json',ROOT/'DELIVERY_SEAL.json'):
        if seal_path.exists():
            for entry in read(seal_path)['files']:
                path=seal_path.parent/entry['path']
                assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],str(path)
    return dict(passed=True,prior_sealed_files_verified=count,prior_sealed_bytes_verified=size,source_freezes_match=True,old_failures_and_caps_preserved=True,all9_study_children_reaped=True,all6_WLC_workers_and8_hosts_reaped=True,complete_authority_suffix_chain_exact=True,account_boundary_restored_from_actual_transcript=True,five_hour_exhaustion_claim=False,new_account_query=False,new_numerical_or_UI_work=False,round_status='CLOSED_BY_OWNER',research='UNRESOLVED',manuscript='PAUSED')
if __name__=='__main__':print(json.dumps(verify(),indent=2))
