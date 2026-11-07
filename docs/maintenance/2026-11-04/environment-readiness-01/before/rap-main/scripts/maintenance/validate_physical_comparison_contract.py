"""Independent PCC0 archive-header and source-role validator."""
import ast
import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/physical-comparison-contract-01'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as stream:
        for body in iter(lambda:stream.read(131072),b''):h.update(body)
    return h.hexdigest()

def validate():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert sha(BASE/'contract_audit.json')==read(BASE/'audit_seal.json')['sha256']
    a=read(BASE/'contract_audit.json');count=members=0
    for bank in a['banks']:
        assert len(bank['rows'])==204
        for actual,row in zip(bank['rows'],f['rows']):
            assert [actual[k] for k in ('seq','t','role')]==[row[k] for k in ('seq','t','role')]
            assert sha(actual['path'])==actual['sha256']==a['selected_current_bank_hashes'][actual['path']]
            with zipfile.ZipFile(actual['path']) as z:
                assert sorted(z.namelist())==[m['name'] for m in actual['members']]
                shapes={m['name']:m['shape'] for m in actual['members']}
                if bank['stage']=='full-bank':
                    for name,shape in [('points.npy',[3000,3]),('features.npy',[3000,32]),
                        ('J_tokens.npy',[3000,512]),('I_tokens.npy',[3000,512]),
                        ('J_pose.npy',[4,4]),('I_pose.npy',[4,4])]:
                        assert shapes[name]==shape
                    evaluation=row['role']=='exposed_evaluation'
                    assert ('G3_pose.npy' in shapes)==evaluation
                    assert ('KISS_pose.npy' in shapes)==(evaluation and int(row['seq']) in (7,9,10))
                else:
                    assert bank['stage']=='pose-targets' and shapes['angular_truth.npy']==[3,4,4]
                for m in actual['members']:
                    with z.open(m['name']) as stream:
                        prefix=stream.read(8)
                        assert prefix[:6]==bytes([147])+b'NUMPY'
                        wide=prefix[6]!=1
                        n=int.from_bytes(stream.read(4 if wide else 2),'little')
                        assert 0<n<65536
                        text=stream.read(n).decode('utf-8' if prefix[6]==3 else 'latin1')
                        header=ast.literal_eval(text.strip())
                    info=z.getinfo(m['name'])
                    assert list(header['shape'])==m['shape'] and header['descr']==m['dtype']
                    assert header['fortran_order']==m['fortran_order']
                    assert (info.file_size,info.compress_size,info.CRC)==(m['uncompressed_bytes'],m['compressed_bytes'],m['CRC'])
                    assert header['descr'][1] in 'fiub'
                    members+=1
            count+=1
    slam=ROOT.parent/'RAP-SLAM'
    metadata_files=0
    for key,root in [('POSS_metadata',slam/'data/poss/dataset'),('sibling_KITTI_metadata',slam/'data/kitti/dataset')]:
        seqs=sorted(n for n in os.listdir(root/'sequences') if os.path.isdir(root/'sequences'/n))
        assert seqs==[r['sequence'] for r in a[key]]
        for r in a[key]:
            folder=root/'sequences'/r['sequence'];p=folder/'velodyne'
            names=os.listdir(p) if os.path.isdir(p) else []
            independent=sorted([[n,os.stat(p/n).st_size] for n in names if n.endswith('.bin') and os.path.isfile(p/n)])
            assert independent==r['names_and_sizes']
            assert sorted(os.listdir(folder))==r['directory_entries']
            metadata_files+=len(independent)
    hist=read(ROOT/'docs/maintenance/2026-09-11/full-poss-01/pipeline/source_frames.json')
    current={int(Path(n).stem) for n,_ in a['POSS_metadata'][0]['names_and_sizes']}
    assert set(hist['source_frame_ids'])<=current and len(hist['source_frame_ids'])==1419
    for r in a['POSS_tables']:
        assert sha(r['path'])==r['sha256']
        text=Path(r['path']).read_text()
        assert sum(bool(s.strip()) for s in text.splitlines())==r['nonempty_rows']
        if r['text'] is not None:assert text==r['text']
    canonical={r['sequence']:dict(r['names_and_sizes']) for r in read(ROOT/'docs/maintenance/2026-10-14/physical-source-role-feasibility-01/scan_metadata.json')['records']}
    for r in a['sibling_KITTI_metadata']:
        original=canonical.get(r['sequence'],{})
        assert r['canonical_names_sizes_match']==all(original.get(n)==b for n,b in r['names_and_sizes'])
        assert not r['byte_identity_or_independent_acquisition_established']
    summaries=a['summary'];assert summaries['role_counts']==dict(fit=144,development=12,exposed_evaluation=48)
    assert len({p for row in f['rows'] for p in row['paths']})==612
    assert count==408 and not summaries['independent_confirmation_established']
    assert not summaries['full_pipeline_equal_work_established'] and not summaries['numerical_array_values_read']
    result=dict(passed=True,decision=summaries['decision'],frozen_identities=len(f['files']),
        current_NPZ_files=count,independent_member_headers=members,
        additional_scan_metadata_files=metadata_files,summary=summaries,
        old_numerical_validator_replayed=False,new_metric_or_head=False)
    with (BASE/'validation.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result),flush=True)
