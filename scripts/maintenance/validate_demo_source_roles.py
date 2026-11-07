"""Independent DSR0 inventory/header/citation and scoped-reference validator."""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-15/demo-source-role-01'
DATA=ROOT/'demo_example_data'


def read(q):return json.loads(Path(q).read_text())


def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as inp:
        for block in iter(lambda:inp.read(65536),b''):h.update(block)
    return h.hexdigest()


def validate():
    f=read(BASE/'freeze.json');a=read(BASE/'headers_and_roles.json')
    for name,row in f['files'].items():assert sha(name)==row['sha256'] and os.stat(name).st_size==row['bytes']
    names=sorted(str((Path(folder)/n).relative_to(DATA)) for folder,_,files in os.walk(DATA) for n in files)
    assert names==sorted(f['inventory'])==sorted(r['path'] for r in a['files'])
    for name,row in read(BASE/'audit_seal.json')['files'].items():
        assert sha(BASE/name)==row['sha256'] and (BASE/name).stat().st_size==row['bytes']
    scenes={}
    for r in a['files']:
        q=DATA/r['path'];assert sha(q)==r['sha256'] and q.stat().st_size==r['bytes']
        with q.open('rb') as stream:body=stream.read(r['header_bytes'])
        assert len(body)<=65536 and body==r['raw_header'].encode('ascii')
        assert hashlib.sha256(body).hexdigest()==r['header_SHA256']
        lines=body.splitlines()
        if q.suffix=='.ply':
            assert lines[0]==b'ply' and lines[-1]==b'end_header'
            assert b'end_header' not in lines[:-1]
            count=next(int(t.split()[2]) for t in lines if t.split()[:2]==[b'element',b'vertex'])
        else:
            assert lines[-1].split()[0]==b'DATA' and not any(t.split()[:1]==[b'DATA'] for t in lines[:-1])
            count=next(int(t.split()[1]) for t in lines if t.split()[:1]==[b'POINTS'])
        assert count==r['declared_points'] and not r['coordinate_payload_decoded']
        scenes.setdefault(str(Path(r['path']).parent),Counter())[q.suffix]+=1
    assert len(names)==a['complete_local_files'] and len(scenes)==a['complete_local_scenes']
    assert Counter(Path(n).suffix for n in names)==a['extensions']
    assert sum((DATA/n).stat().st_size for n in names)==a['total_bytes']
    assert {r['scene'] for r in a['scenes']}==set(scenes)
    for row in a['scenes']:
        counts=scenes[row['scene']]
        assert row['files']==sum(counts.values()) and row['demo_PLY_files']==counts['.ply'] and row['PCD_files']==counts['.pcd']
        assert row['role'].endswith('UNAUTHENTICATED_NOT_UNTOUCHED')
    citations=read(BASE/'source_citations.json')['citations'];assert len(citations)==7
    for c in citations:
        q=ROOT/c['path'];assert sha(q)==c['source_SHA256']
        lines=q.read_text().splitlines(keepends=True)
        assert ''.join(lines[c['line_start']-1:c['line_end']])==c['excerpt']
        fn=[n for n in ast.walk(ast.parse(q.read_text())) if isinstance(n,ast.FunctionDef) and n.name==c['function']]
        assert len(fn)==1 and fn[0].lineno==c['line_start'] and fn[0].end_lineno==c['line_end']
    loader=next(c['excerpt'] for c in citations if c['function']=='_load_from_folder')
    dictnodes=[n for n in ast.walk(ast.parse('class Wrapper:\n'+''.join('    '+line+'\n' for line in loader.splitlines()))) if isinstance(n,ast.Dict)]
    gt_values=[value for d in dictnodes for key,value in zip(d.keys,d.values) if isinstance(key,ast.Constant) and key.value=='pointclouds_gt']
    assert len(gt_values)==1 and isinstance(gt_values[0],ast.Name) and gt_values[0].id=='pcs'
    assert a['scoped_external_reference_sidecar_files']==0 and set(a['extensions'])=={'.ply','.pcd'}
    for k in ('all_history_access_complete','author_RegX_scene_byte_link_established','checkpoint_training_exclusion_established',
        'demo_clouds_wrong_or_unregistered_established','new_cohort_or_efficacy_admitted'):assert not a[k]
    assert a['point_payload_or_GT_or_model_calls']==0
    assert s.repositories()==f['repositories']
    result=dict(passed=True,frozen_identities=len(f['files']),complete_files=len(names),
        complete_scenes=len(scenes),total_bytes=a['total_bytes'],citations=len(citations),
        default_demo_PLY_scenes=sum(counts['.ply']>0 for counts in scenes.values()),
        PCD_only_scenes=sorted(name for name,counts in scenes.items() if counts['.ply']==0),
        independent_hash_header_population_and_reference_contract=True,decision=a['decision'])
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result),flush=True)
