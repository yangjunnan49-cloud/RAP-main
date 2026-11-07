"""Independent NJC0 union-find audit; no runner imports or numerical arrays."""
import ast,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-connectivity-01'
OLD=ROOT/'docs/maintenance/2026-10-05/online-geotransformer-01'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),parse_int=str,parse_float=str)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while True:
            b=f.read(65536)
            if not b:break
            h.update(b)
    return h.hexdigest()
def run():
    frozen=read(BASE/'freeze.json')
    for name,row in frozen['files'].items():assert Path(name).stat().st_size==int(row['bytes']) and sha(name)==row['sha256']
    observed=read(BASE/'topology.json');attempts=read(OLD/'input-bank/attempts.json');rebuilt=[];eligible=0;edges_total=0;attempt_total=0;cache_keys=set()
    for record,s,count in zip(observed['sequences'],('00','05','06','07','09','10'),(12,12,12,12,10,0)):
        day='2026-09-26/e0-frontend-01' if s in ('00','05','06') else '2026-09-27/e0-heldout-01'
        src=ROOT/'docs/maintenance'/day/f'full-{s}-A';rows=read(src/'accepted_loops.json')
        edges=[dict(i=int(r['i']),j=int(r['j']),measurement_id=r['measurement_id']) for r in rows]
        aa=[r for r in attempts[s] if r['status']=='accepted']
        assert edges==[dict(i=int(r['i']),j=int(r['j']),measurement_id=r['selected_measurement_id']) for r in aa] and len(edges)==count
        parent={i:i for e in edges for i in (e['i'],e['j'])};degree={i:0 for i in parent}
        def find(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for e in edges:
            a,b=e['i'],e['j'];parent[find(a)]=find(b);degree[a]+=1;degree[b]+=1
        groups={}
        for i in sorted(parent):groups.setdefault(find(i),[]).append(i)
        groups=sorted(groups.values(),key=lambda g:min(g));components=[]
        for nodes in groups:
            ee=[e for e in edges if e['i'] in nodes];assert all(e['j'] in nodes for e in ee)
            raw_hashes={frozen['raw_identities'][f'{s}/{i:06d}']['sha256'] for i in nodes}
            accepted=len(nodes)>=3 and len(ee)>=2 and len(raw_hashes)>=3
            components.append(dict(nodes=nodes,edges=ee,distinct_raw_SHA256=len(raw_hashes),eligible=accepted,
                degree={str(i):degree[i] for i in nodes},cycle_rank=len(ee)-len(nodes)+1))
            eligible+=accepted
            for i in nodes:
                key=f'{s}/{i:06d}';cache_keys.add(key);cache=observed['caches'][key];p=Path(cache['path'])
                assert sha(p)==cache['sha256']
                with p.open('rb') as stream:
                    prefix=stream.read(8);assert prefix[:6]==b'\x93NUMPY'
                    width=2 if prefix[6:]==b'\x01\x00' else 4;assert prefix[6:] in (b'\x01\x00',b'\x02\x00')
                    length=int.from_bytes(stream.read(width),'little');header=ast.literal_eval(stream.read(length).decode('latin1'));offset=stream.tell()
                assert header['descr']=='<f4' and header['fortran_order'] is False and header['shape'][1]==3
                assert list(header['shape'])==[int(x) for x in cache['shape']] and offset==int(cache['header_payload_offset'])
                assert p.stat().st_size==offset+12*header['shape'][0]
                raw=frozen['raw_identities'][key];assert sha(raw['path'])==raw['sha256']==cache['raw']['sha256']
        assert sum(degree.values())==2*len(edges)
        expected=dict(sequence=s,attempts=len(attempts[s]),accepted_loops=count,unique_loop_views=len(parent),components=components,eligible_components=sum(c['eligible'] for c in components))
        assert json.loads(json.dumps(expected),parse_int=str)==record
        rebuilt.append(expected);edges_total+=len(edges);attempt_total+=len(attempts[s])
    assert edges_total==58 and attempt_total==71 and eligible==int(observed['eligible_components'])
    assert set(observed['caches'])==cache_keys
    result=dict(passed=True,sequences=6,attempts=71,accepted_loops=58,loop_endpoint_caches=len(cache_keys),
      eligible_components=eligible,independent_union_find_matches=True,no_numeric_pose_or_coordinate_values_parsed=True,
      model_or_solver_or_pose_metric_calls=0,eligibility_is_not_efficacy_admission=True)
    with (BASE/'validation.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=='__main__':run()
