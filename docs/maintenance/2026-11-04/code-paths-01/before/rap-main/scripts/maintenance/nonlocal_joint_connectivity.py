"""NJC0 ID-only nonlocal observation topology; no numerical scientific imports."""
import ast,hashlib,json,struct,subprocess,sys
from collections import defaultdict,deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-connectivity-01'
OLD=ROOT/'docs/maintenance/2026-10-05/online-geotransformer-01'
SGC=ROOT/'docs/maintenance/2026-10-12/scan-level-graph-feasibility-01'
SEQS=('00','05','06','07','09','10')
COUNTS=(12,12,12,12,10,0)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),parse_float=str,parse_int=str)
def integer(x):
    assert isinstance(x,str) and x.isdecimal(),repr(x)
    return int(x)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(name,value):
    data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())+len(data)<7*2**20
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
def source(s):
    day='2026-09-26/e0-frontend-01' if s in SEQS[:3] else '2026-09-27/e0-heldout-01'
    return ROOT/'docs/maintenance'/day/f'full-{s}-A'
def repositories():
    out={}
    for name,p in (('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')):
        def git(*args):return subprocess.check_output(['git','--no-optional-locks','-c',f'safe.directory={p}','-C',str(p),*args],text=True).strip()
        out[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
    return out
def header(p):
    with p.open('rb') as f:
        assert f.read(6)==b'\x93NUMPY';version=f.read(2);assert version in (b'\x01\x00',b'\x02\x00')
        n=struct.unpack('<H' if version[0]==1 else '<I',f.read(2 if version[0]==1 else 4))[0]
        raw=f.read(n);assert len(raw)==n and n<=65536
        h=ast.literal_eval(raw.decode('latin1'));offset=f.tell()
    assert set(h)=={'descr','fortran_order','shape'} and h['descr']=='<f4' and not h['fortran_order']
    assert len(h['shape'])==2 and h['shape'][1]==3 and 0<h['shape'][0]<=4000
    assert p.stat().st_size==offset+h['shape'][0]*12
    return dict(shape=list(h['shape']),dtype=h['descr'],fortran_order=False,header_payload_offset=offset,coordinate_payload_decoded=False)
def verify():
    f=read(BASE/'freeze.json')
    for name,row in f['files'].items():
        p=Path(name);assert p.stat().st_size==integer(row['bytes']) and sha(p)==row['sha256'],name
    assert repositories()==f['repositories']
    return f
def freeze():
    prior=read(ROOT/'docs/maintenance/2026-10-15/continuation-handoff-06/IDENTITY_CHECKS.json')
    old=read(OLD/'freeze.json');sgc=read(SGC/'freeze.json');inputs=read(OLD/'input_seal.json')
    assert sha(OLD/'freeze.json')==inputs['freeze_sha256']
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_nonlocal_joint_connectivity.py'),
      Path(__file__).with_name('run_nonlocal_joint_connectivity.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),OLD/'freeze.json',OLD/'input_seal.json',SGC/'freeze.json',
      ROOT/'docs/maintenance/2026-10-15/continuation-handoff-07/DELIVERY_SEAL.json']
    paths += [Path(p) for p in prior['retained_markers']]
    for s in SEQS:
        for name in ('accepted_loops.json','keyframes.json','source_frames.json'):
            p=source(s)/name;assert sha(p)==sgc['files'][str(p)];paths.append(p)
    raw={}
    for name,h in inputs['files'].items():
        p=OLD/'input-bank'/name;assert sha(p)==h;paths.append(p)
        if name.endswith('.npy'):
            s,filename=name.split('/');i=int(filename.split('.')[0]);q=ROOT.parent/f'Datasets/data_odometry_velodyne/dataset/sequences/{s}/velodyne/{i:06d}.bin'
            assert sha(q)==old['files'][str(q)];paths.append(q);raw[f'{s}/{i:06d}']=dict(path=str(q),sha256=sha(q),bytes=q.stat().st_size)
    assert len(raw)==98
    repos=repositories();assert repos==prior['repositories']
    paths=sorted(set(paths));files={str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in paths}
    for p in paths:
        if p.suffix in ('.py','.ps1') and ROOT in p.parents:
            target=BASE/'source_snapshot'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(p.read_bytes())
    save('freeze.json',dict(files=files,repositories=repos,raw_identities=raw,source_sequences=SEQS,prior_markers=len(prior['retained_markers'])))
    save('INCOMPLETE',dict(pending='complete topology and independent validator',scope='NJC0'))
    print(json.dumps(dict(frozen_identities=len(files),raw_input_files=len(raw))),flush=True)
def topology():
    f=verify();attempts=read(OLD/'input-bank/attempts.json');all_attempts=0;total_edges=0;rows=[];caches={}
    for s,count in zip(SEQS,COUNTS):
        records=read(source(s)/'accepted_loops.json');assert len(records)==count
        aa=attempts[s];all_attempts+=len(aa)
        accepted=[r for r in aa if r['status']=='accepted']
        edges=[dict(i=integer(r['i']),j=integer(r['j']),measurement_id=r['measurement_id']) for r in records]
        expected=[dict(i=integer(r['i']),j=integer(r['j']),measurement_id=r['selected_measurement_id']) for r in accepted]
        assert edges==expected and len({(e['i'],e['j']) for e in edges})==count
        assert len({e['measurement_id'] for e in edges})==count and all(e['i']<e['j'] for e in edges)
        keys={integer(i) for i in read(source(s)/'keyframes.json')}
        frames=read(source(s)/'source_frames.json')['source_frame_ids']
        adjacency=defaultdict(set)
        for e in edges:
            for i in (e['i'],e['j']):
                assert i in keys and integer(frames[i])==i
                name=f'{s}/{i:06d}';p=OLD/'input-bank'/f'{name}.npy'
                if name not in caches:caches[name]=dict(path=str(p),sha256=sha(p),**header(p),raw=f['raw_identities'][name])
            adjacency[e['i']].add(e['j']);adjacency[e['j']].add(e['i'])
        remaining=set(adjacency);components=[]
        while remaining:
            first=min(remaining);queue=deque([first]);nodes={first};remaining.remove(first)
            while queue:
                for nxt in sorted(adjacency[queue.popleft()]):
                    if nxt in remaining:remaining.remove(nxt);nodes.add(nxt);queue.append(nxt)
            nodes=sorted(nodes);ee=[e for e in edges if e['i'] in nodes]
            hashes={caches[f'{s}/{i:06d}']['raw']['sha256'] for i in nodes}
            eligible=len(nodes)>=3 and len(ee)>=2 and len(hashes)>=3
            components.append(dict(nodes=nodes,edges=ee,distinct_raw_SHA256=len(hashes),eligible=eligible,
                degree={str(i):len(adjacency[i]) for i in nodes},cycle_rank=len(ee)-len(nodes)+1))
        assert sum(len(c['edges']) for c in components)==len(edges)
        rows.append(dict(sequence=s,attempts=len(aa),accepted_loops=count,unique_loop_views=len(adjacency),components=components,
            eligible_components=sum(c['eligible'] for c in components)))
        total_edges+=len(edges)
    assert all_attempts==71 and total_edges==58
    save('topology.json',dict(sequences=rows,caches=caches,all_attempts=71,accepted_loops=58,
        eligible_components=sum(r['eligible_components'] for r in rows),eligible_is_not_inference_admission=True,
        numeric_pose_coordinate_or_error_parses=0,neural_or_solver_calls=0,raw_or_cache_coordinate_decodes=0))
    verify();print(json.dumps(dict(accepted_loops=58,eligible_components=sum(r['eligible_components'] for r in rows),loop_endpoint_caches=len(caches))),flush=True)
if __name__=='__main__':{'freeze':freeze,'topology':topology}[sys.argv[1]]()
