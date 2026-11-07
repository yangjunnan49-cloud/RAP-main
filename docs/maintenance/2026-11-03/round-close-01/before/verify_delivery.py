"""Read-only delivery/authority verification; never starts UI, WSL or numerics."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def verify():
    scopes=('identity-evidence-01','stereo-source-01','stereo-support-01','stereo-alias-01','windows-lease-01')
    files=0;bytecount=0
    for scope in scopes:
        folder=ROOT/scope
        for e in read(folder/'DELIVERY_SEAL.json')['files']:
            p=folder/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],str(p)
            files+=1;bytecount+=e['bytes']
    for scope in ('stereo-source-01','stereo-support-01','stereo-support-01/integration02','stereo-alias-01','windows-lease-01'):
        for e in read(ROOT/scope/'SOURCE_FREEZE.json')['files']:
            assert Path(e['path']).stat().st_size==e['bytes'] and sha(e['path'])==e['sha256'],e['path']
    gc=read(ROOT/'stereo-support-01/GROUP_COVERAGE.json')
    def group(name,seq='all'):return next(r for r in gc['groups'] if r['group']==name and r['sequence']==seq)
    assert group('all200')['eligible']==141 and group('positive')['eligible']==109
    assert [group('oldunique27',s)['eligible'] for s in ('00','08')]==[18,3]
    assert not gc['target_coverage_screen'] and not gc['candidate_scoring_admitted']
    audit=read(ROOT/'stereo-support-01/integration02/audit/RESULT.json')
    assert audit['passed'] and audit['scalar_disparity_sample_checks']==10682 and audit['independent_covariance_checks']==400
    assert read(ROOT/'stereo-source-01/packet/RESULT.json')['new_right_images_decoded']==273
    assert read(ROOT/'stereo-alias-01/controls/RESULT.json')['depth_support_and_rank_insufficient_for_identity']
    original=read(ROOT/'stereo-support-01/packet/HOST_EXIT.json');assert not original['passed'] and original['owned_child_reaped'] and 'PermissionError' in original['error']
    packet=read(ROOT/'stereo-support-01/integration02/packet/RESULT.json');assert (packet['byte_reused_maps'],packet['newly_computed_maps'])==(135,138)
    stage_paths=[ROOT/'stereo-source-01'/s for s in ('controls','packet','audit')]+[ROOT/'stereo-support-01'/s for s in ('controls','packet')]+[ROOT/'stereo-support-01/integration02'/s for s in ('controls','packet','audit')]+[ROOT/'stereo-alias-01/controls']
    assert len(stage_paths)==9
    for stage in stage_paths:assert read(stage/'HOST_EXIT.json')['owned_child_reaped']
    guard=read(ROOT/'windows-lease-01/RESULT.json');assert guard['passed'] and len(guard['cases'])==8 and guard['all_owned_hosts_reaped']
    assert all(c['expected_outcome_passed'] and (c['child_reaped'] if c['child_launched'] else True) for c in guard['cases'])
    proof=read(ROOT/'AUTHORITY_UPDATE_PROOF.json')
    previous=Path(proof['previous_backup']).read_bytes();actual=Path(proof['path']).read_bytes()
    assert sha(proof['path'])==proof['current_sha256'] and actual[proof['prefix_bytes']:]==previous
    active=read(ROOT/'identity-evidence-01/AUTHORITY_UPDATE_ACTIVE.json')
    base=(ROOT/'identity-evidence-01/authority_before/RAP-main.AGENTS.md').read_bytes()
    assert previous[active['prefix_bytes']:]==base
    assert sha('E:/githouse/AGENTS.md')==proof['parent_current_sha256']
    return dict(passed=True,sealed_files_verified=files,sealed_bytes_verified=bytecount,source_freezes_match=True,all9_study_children_reaped=True,all6_WLC_workers_and8_hosts_reaped=True,original_failure_preserved=True,cached_maps_exact=True,authority_previous_suffixes_exact=True,research='UNRESOLVED',numerical_or_UI_work_restarted=False)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
