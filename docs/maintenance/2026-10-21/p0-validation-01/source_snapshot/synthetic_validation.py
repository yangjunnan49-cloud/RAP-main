"""Exercise the actual adapted metric loop with two wholly synthetic cells."""
import json,hashlib,types
from pathlib import Path
import numpy as np
import validation_core as c
import metrics_adapted as metric
def run():
    root=c.OUT/'synthetic_fixture';root.mkdir()
    data=root/'dataset';(data/'poses').mkdir(parents=True);(data/'sequences/00').mkdir(parents=True)
    n=1001;gt=np.tile(np.eye(4),(n,1,1));i=np.arange(n);gt[:,0,3]=i;gt[:,1,3]=10*np.sin(i/100);gt[:,2,3]=2*np.sin(i/50)
    np.savetxt(data/'poses/00.txt',gt[:,:3].reshape(n,12),fmt='%.17g')
    (data/'sequences/00/calib.txt').write_text('Tr: 1 0 0 0 0 1 0 0 0 0 1 0\n')
    def save(p,x):
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
    raw=lambda s,j:root/f'synthetic_{j:06d}.bin'
    hashes={str(raw('00',j)):hashlib.sha256(str(j).encode()).hexdigest() for j in i}
    save(root/'freeze.json',dict(raw_files=hashes))
    chain=hashlib.sha256()
    for j in i:chain.update(f"{j} {hashes[str(raw('00',j))]}\n".encode())
    schedule=[]
    for k,scale in [('exact',1.),('scaled',1.001)]:
        cell=dict(key=k,sequence='00',mode='G',scheduler='S',repeat=1);schedule.append(cell)
        folder=root/'bank02'/k;folder.mkdir(parents=True);est=gt.copy();est[:,0,3]*=scale
        np.save(folder/'poses.npy',est);np.save(folder/'frame_timing.npy',np.ones((n,5))*.001)
        save(folder/'source_binding.json',dict(source_frame_ids=list(range(n)),map_consumed_frames={'0':list(range(n))},consumed_ordered_hash_chain=chain.hexdigest(),frontend_reference_max=0.))
        save(folder/'execution.json',dict(fine_seconds=0.,closures=0,local_maps=1));save(folder/'worker_exit.json',dict(wall_seconds=1.,peak_RSS_bytes=1024))
    save(root/'schedule.json',dict(cells=schedule))
    # The isolated fixture stubs only the seal's campaign-count admission; two cells
    # intentionally traverse the complete real metric/hash/segment loop twice.
    files={str(p.relative_to(root/'bank02')):c.sha(p) for p in (root/'bank02').rglob('*') if p.is_file()}
    save(root/'bank_seal02.json',dict(cells=72,utc='2000-01-01T00:00:00Z',files=files))
    import validate_scan_level_graph as independent
    independent.DATA=data
    c.d=types.SimpleNamespace(BASE=root)
    metric.BASE=root;metric.r=types.SimpleNamespace(DATA=data,raw=raw)
    metric.verify=lambda:None;metric.cap=lambda:None;metric.save=save
    rows,segments,maximum=metric.evaluate_rows()
    assert len(rows)==2 and segments>0 and rows[0]['ate']<1e-8 and rows[1]['ate']>.01
    # Exercise sealed-byte corruption rejection through the actual same function.
    with (root/'bank02/exact/poses.npy').open('ab') as f:f.write(b'corruption-probe')
    rejected=False
    try:metric.evaluate_rows()
    except AssertionError:rejected=True
    assert rejected
    save(c.OUT/'SYNTHETIC_CHECKS.json',dict(passed=True,real_dataset_GT_reads=0,real_predictions_decoded=0,metric_rows=rows,independent_segments=segments,maximum_metric_delta=maximum,corrupt_seal_rejected=rejected,fixture_count_admission_stub=72,actual_fixture_cells=2))
    print('Synthetic two-cell actual metric loop and corruption rejection PASS',segments,maximum,flush=True)
