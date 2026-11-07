"""One fixed source/report audit, not a general scientific-admission engine."""
import ast, datetime, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
BASE='docs/maintenance/'
SOURCES=[
 BASE+'2026-10-24/continuation-01/NEXT_PLAN.md',
 BASE+'2026-10-24/continuation-01/RESULTS_REPORT.md',
 BASE+'2026-10-24/continuation-01/TRANSFORM_CONVENTION.md',
 BASE+'2026-10-24/real-interface-02/run01/real/RESULTS.json',
 BASE+'2026-10-24/output-contract-01/run02/verify/RESULTS.json',
 BASE+'2026-10-16/regx-interface-contract-01/inputs/INDEX.json',
 BASE+'2026-10-16/regx-interface-contract-01/inputs/case-000/manifest.json',
 BASE+'2026-10-16/regx-interface-contract-01/inputs/case-001/manifest.json',
 BASE+'2026-10-16/regx-interface-contract-01/BUILD.json',
 BASE+'2026-10-16/regx-reference-package-01/PACKAGE_PLAN.json',
 BASE+'2026-10-16/regx-reference-package-01/REPORT.md',
 BASE+'2026-10-16/regx-reference-code-01/REPORT.md',
 'scripts/maintenance/regx_interface_contract_execution02.py',
 BASE+'2026-10-23/reference-admission-01/REPORT.md',
 BASE+'2026-10-23/reference-counterexample-01/REPORT.md',
 BASE+'2026-10-15/joint-mechanism-assessment-01/REPORT.md',
 BASE+'2026-10-14/physical-source-role-feasibility-01/REPORT.md',
 BASE+'2026-10-14/poss-exposure-lineage-01/REPORT.md',
 BASE+'2026-10-14/continuation-handoff-05/AUTHENTICATION_DEPENDENCIES.md',
 BASE+'2026-10-14/continuation-handoff-05/NEXT_SCIENCE_DESIGN.md',
 BASE+'2026-10-14/continuation-handoff-05/DECISION_MATRIX.md',
 BASE+'2026-10-15/joint-mechanism-assessment-01/AUTHOR_REQUEST_READY_TO_SEND.md']

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def write(n,obj):
    with (ROOT/n).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)
def read_sources():
    assert len(SOURCES)<=24
    data={name:(REPO/name).read_bytes() for name in SOURCES}
    assert sum(map(len,data.values()))<=512*1024
    return data
def freeze():
    data=read_sources()
    write('SOURCE_FREEZE.json',dict(files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in data.items()},
        helper_sha256=sha(Path(__file__).read_bytes()),protocol_sha256=sha((ROOT/'PROTOCOL.md').read_bytes()),
        source_count=len(data),source_bytes=sum(map(len,data.values()))))

def audit():
    seal=json.loads((ROOT/'SOURCE_FREEZE.json').read_text())
    assert sha(Path(__file__).read_bytes())==seal['helper_sha256']
    assert sha((ROOT/'PROTOCOL.md').read_bytes())==seal['protocol_sha256']
    data=read_sources()
    for name,b in data.items(): assert seal['files'][name]==dict(bytes=len(b),sha256=sha(b))
    def obj(s): return json.loads(data[BASE+s])
    index=obj('2026-10-16/regx-interface-contract-01/inputs/INDEX.json')
    manifests=[obj('2026-10-16/regx-interface-contract-01/inputs/'+n) for n in index['cases']]
    assert index['cases']==['case-000/manifest.json','case-001/manifest.json']
    counts=[[v['points'] for v in m['views']] for m in manifests]
    assert counts==[[11250,11372],[11250,11313,11372]]
    build=obj('2026-10-16/regx-interface-contract-01/BUILD.json')
    assert build['case_view_counts']==list(map(len,counts))==[2,3]
    assert build['case_point_counts']==list(map(sum,counts))==[22622,33935]
    assert build['source_world_files']==3
    assert build['physical_alignment_authenticated'] is False
    plan=obj('2026-10-16/regx-reference-package-01/PACKAGE_PLAN.json')
    assert plan['scene']=='OutdoorScan/paris_02'
    assert [r['path'] for r in plan['files'] if r['path'].endswith('.ply')]==[
        'OutdoorScan/paris_02/000.ply','OutdoorScan/paris_02/001.ply','OutdoorScan/paris_02/002.ply']
    tree=ast.parse(data['scripts/maintenance/regx_interface_contract_execution02.py'])
    assertions=[ast.unparse(n.test) for n in ast.walk(tree) if isinstance(n,ast.Assert)]
    assert any('[913, 914]' in s for s in assertions)
    real=obj('2026-10-24/real-interface-02/run01/real/RESULTS.json')
    verify=obj('2026-10-24/output-contract-01/run02/verify/RESULTS.json')
    total=sum(map(sum,counts))
    assert total==56557==real['counters']['point_occurrences_submitted']
    assert real['counters']['RAP_calls_completed']==2
    assert real['counters']['private_reference_reads']==0
    assert verify['normalization_coordinate_checks']==60000
    prepared=[r['counts'] for r in verify['cases']]
    assert prepared==[[4000,4000],[4000,4000,4000]]
    assert sum(map(sum,prepared))*3==60000
    assert len(verify['exports'])==sum(map(len,counts))==5
    write('SAMPLING_UNITS.json',dict(passed=True,case_records=2,source_scene_count=1,
        scene=plan['scene'],source_file_count=3,source_file_vertex_records=33935,
        source_file_vertex_record_basis='C0 three-source BUILD plus public case001 counts, report-confirmed source ordering; not a new raw read or unique physical-return count',
        public_view_occurrences=5,public_point_occurrences=total,prepared_point_occurrences=20000,
        normalization_coordinate_checks=60000,estimated_case_local_matrices=5,
        independent_acquisition_sessions='UNKNOWN',independent_confirmation_scenes_admitted=0,
        shared_source_names_from_B1_report=['000.ply','002.ply'],
        shared_source_mapping_independently_recensused=False,
        metadata_or_output_rows_are_not_independent_scene_samples=True))
    queries=[
      ('regx_reference','2026-10-23/reference-admission-01/REPORT.md','Both existing cases are exposed'),
      ('regx_shared_views','2026-10-16/regx-reference-package-01/REPORT.md','二者全部保留'),
      ('regx_physical','2026-10-16/regx-reference-package-01/REPORT.md','不构成独立实测真值'),
      ('regx_direction','2026-10-16/regx-reference-code-01/REPORT.md','T是world→view'),
      ('kitti_exposure','2026-10-14/physical-source-role-feasibility-01/REPORT.md','KITTI00-05 remains exposed'),
      ('kitti_unlabelled','2026-10-14/physical-source-role-feasibility-01/REPORT.md','11-21 raw availability'),
      ('poss_configured','2026-10-14/poss-exposure-lineage-01/REPORT.md','configured range alone'),
      ('poss_missing','2026-10-14/continuation-handoff-05/AUTHENTICATION_DEPENDENCIES.md','5269-6749 is missing'),
      ('demo_physical','2026-10-15/joint-mechanism-assessment-01/REPORT.md','how that'),
      ('mechanism_not_novel','2026-10-15/joint-mechanism-assessment-01/REPORT.md','not a new algorithmic contribution'),
      ('cycles_not_accuracy','2026-10-15/joint-mechanism-assessment-01/REPORT.md','Cycle closure derived'),
      ('no_more_prereq','2026-10-14/continuation-handoff-05/NEXT_SCIENCE_DESIGN.md','Stop extra prototype expansion'),
      ('source_before_acquisition','2026-10-14/continuation-handoff-05/AUTHENTICATION_DEPENDENCIES.md','Before external retrieval'),
      ('outreach_unsent','2026-10-15/joint-mechanism-assessment-01/AUTHOR_REQUEST_READY_TO_SEND.md','No email/draft/API message has been sent')]
    citations=[]
    for claim,suffix,needle in queries:
        name=BASE+suffix;lines=data[name].decode('utf-8-sig').splitlines()
        hits=[(i+1,s) for i,s in enumerate(lines) if needle in s]
        assert len(hits)==1,(claim,hits)
        line,text=hits[0]
        citations.append(dict(claim=claim,path=name,line=line,source_sha256=sha(data[name]),literal_line=text,
            authority='existing bounded local report, not independent physical authentication'))
    write('CLAIM_CITATIONS.json',dict(claims=citations,claims_verified=len(citations),source_files_verified=len(data),
        physical_reference_admitted=False,new_raw_private_weight_or_model_reads=0))
    for name,b in data.items(): assert (REPO/name).read_bytes()==b
    write('RESULTS.json',dict(status='SOURCE_ROLE_AND_SAMPLING_UNIT_REVIEW_COMPLETE',passed=True,
        source_files=len(data),source_bytes=sum(map(len,data.values())),source_citations=len(citations),
        physical_efficacy_admitted=False,confirmation_cohort_admitted=False,new_mechanism_demonstrated=False,
        scientific_next_step='OWNER_SUPPLIED_SOURCE_RECORD_AND_ROLE_MECHANISM_REVIEW',
        no_raw_private_weight_model_geometry_fit_metric_or_acquisition=True,
        no_historical_global_exposure_census=True,original_research='UNRESOLVED',manuscript='PAUSED'))
    print(json.dumps(dict(passed=True,sources=len(data),claims=len(citations),scenes=1,view_occurrences=5)))

if __name__=='__main__':
    if sys.argv[1:] == ['freeze']: freeze()
    elif sys.argv[1:] == ['audit']: audit()
    else: raise SystemExit('use freeze or audit')
