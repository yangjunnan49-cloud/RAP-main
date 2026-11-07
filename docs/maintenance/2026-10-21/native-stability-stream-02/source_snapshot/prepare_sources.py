"""Prepare N2 from retained N1 sources; no numerical/native imports or payload."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'native_stability_control_01'
CHUNK=ROOT.parent/'chunk_hash_feasibility_01'
OUT=ROOT.parents[1]/'outputs/native_stability_stream_20261021'


def write(name,text):
    (ROOT/name).write_text(text)


def once(text,old,new):
    assert text.count(old)==1,(old,text.count(old))
    return text.replace(old,new)


write('stream_hash.py',(CHUNK/'stream_hash.py').read_text())
text=(OLD/'capture_codec.py').read_text().replace('import hashlib, json, math','import gzip, hashlib, json, math')
text=once(text,"self.file = path.open('x')","self.file = gzip.open(path,'xt',compresslevel=1)")
text=once(text,'with path.open() as source:',"with gzip.open(path,'rt') as source:")
write('capture_codec.py',text)
text=(OLD/'bindings.py').read_text().replace('outputs/native_stability_control_20261021','outputs/native_stability_stream_20261021')
text=text.replace("S1 = Path(","BANK = ROOT.parents[1] / 'outputs/native_stability_control_20261021/frontend'\nS1 = Path(")
write('bindings.py',text)
text=(OLD/'native_observer.py').read_text();tree=ast.parse(text)
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='array')
lines=text.splitlines(keepends=True)
lines[node.lineno-1:node.end_lineno]=["def array(value, role, multiset=False):\n    return stream_array(value, role, multiset=False)\n"]
text=''.join(lines).replace('from capture_codec import describe','from capture_codec import describe\nfrom stream_hash import array as stream_array')
text=once(text,"recorded['paired_rows'] = array(np.concatenate([points, normals], axis=1), 'output', True)","# No concatenation or secondary row sorting in N2.")
needle='        original_icp = o3d.t.pipelines.registration.icp'
insert="""        from kiss_icp.pybind import kiss_icp_pybind as native_icp
        original_downsample = native_icp._voxel_down_sample
        def downsample(*args, **kwargs):
            if kwargs:
                raise RuntimeError('Unexpected voxel downsample keyword boundary')
            return observer.invoke('KISS_voxel_down_sample', original_downsample, args)
        native_icp._voxel_down_sample = downsample
        original_icp = o3d.t.pipelines.registration.icp"""
text=once(text,needle,insert)
write('native_observer.py',text)
text=(OLD/'native_stage.py').read_text()
node=next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name=='frontend')
lines=text.splitlines(keepends=True);del lines[node.lineno-1:node.end_lineno];text=''.join(lines)
text=text.replace('OUT, S1, core,','OUT, S1, BANK, core,')
text=text.replace('<= 8*2**20','<= 14*2**20').replace("bank=OUT/'frontend'","bank=BANK")
text=text.replace("'probe_events.jsonl'","'probe_events.jsonl.gz'").replace("'events.jsonl'","'events.jsonl.gz'")
text=once(text,"expect('secondary_multiset_preserves_duplicates_and_exact_row_bytes', a['row_multiset_sha256'] == b['row_multiset_sha256'])",
               "expect('secondary_multiset_omitted', 'row_multiset_sha256' not in a and 'row_multiset_sha256' not in b)")
text=once(text,'    observer.install()\n    native_points',"    observer.install()\n    from kiss_icp.voxelization import voxel_down_sample\n    sampled=voxel_down_sample(np.asarray([[1.,2.,3.],[2.,3.,4.]],dtype=np.float64),.1)\n    expect('native_voxel_downsample_capture',sampled.ndim==2 and sampled.shape[1]==3)\n    native_points")
text=text.replace("'front':frontend,",'')
text=once(text,"binding=dict(input_bindings=", "binding=dict(schema='N2_streaming_no_multiset',input_bindings=")
write('native_stage.py',text)
text=(OLD/'identity02.py').read_text().replace("'runner': 'lease_runner02.py'","'runner': 'lease_runner.py'")
write('identity.py',text)
write('stop_identity.py',(OLD/'stop_identity02.py').read_text().replace('from identity02 import','from identity import'))
text=(OLD/'lease_runner02.py').read_text().replace('from identity02 import','from identity import').replace("'SOURCE_FREEZE02.json'","'SOURCE_FREEZE.json'")
text=text.replace('scope_cap = 1620.0','scope_cap = 1620.0').replace('> 8*2**20','> 14*2**20')
write('lease_runner.py',text)
text=(OLD/'host02.ps1').read_text().replace('native_stability_control_20261021','native_stability_stream_20261021').replace('native_stability_control_01','native_stability_stream_02')
text=text.replace('lease_runner02.py','lease_runner.py').replace('stop_identity02.py','stop_identity.py')
write('host.ps1',text)
report=dict(N1_sources_unchanged=True,N1_closed_status_sha256=hashlib.sha256((OLD.parents[1]/'outputs/native_stability_control_20261021/COSTS_FINAL.json').read_bytes()).hexdigest(),
    old_observer_sha256=hashlib.sha256((OLD/'native_observer.py').read_bytes()).hexdigest(),
    chunk_hash_sha256=hashlib.sha256((CHUNK/'stream_hash.py').read_bytes()).hexdigest(),
    copied_hash_sha256=hashlib.sha256((ROOT/'stream_hash.py').read_bytes()).hexdigest(),
    new_frontend_generation_removed=True,original_numeric_calls_retained=True,changes='streaming-only fingerprints,gzip,upstream native downsample interception,paths; no source algorithm changes')
(OUT/'PREPARATION.json').write_text(json.dumps(report,indent=2))
