import numpy as np
import overlap_core01 as p
BASE=p.BASE;r=p.r;read=p.read;save=p.save;sha=p.sha;now=p.now;verify=p.verify;cap=p.cap
def evaluate_rows():
    verify();seal=read(BASE/'bank_seal.json');assert seal['cells']==72
    for p,h in seal['files'].items():assert sha(BASE/'bank'/p)==h,p
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    import validate_scan_level_graph as v
    started=now();assert seal['utc']<started;dest=BASE/'evaluation';dest.mkdir();rows=[];maximum=0.;segments=0
    for cell in read(BASE/'schedule.json')['cells']:
        key=cell['key'];s=cell['sequence'];t=np.load(BASE/'bank'/key/'poses.npy');binding=read(BASE/'bank'/key/'source_binding.json');n=len(t);assert binding['source_frame_ids']==list(range(n))
        assert sorted(i for group in binding['map_consumed_frames'].values() for i in group)==list(range(n))
        f=read(p.d.BASE/'freeze.json');chain=hashlib.sha256()
        for i in range(n):chain.update(f"{i} {f['raw_files'][str(r.raw(s,i))]}\n".encode())
        assert binding['consumed_ordered_hash_chain']==chain.hexdigest()
        tr=_read_calib_transform(str(r.DATA/f'sequences/{s}/calib.txt'));ti=np.linalg.inv(tr);gt=np.asarray(load_gt_poses(str(r.DATA/f'poses/{s}.txt'),str(r.DATA/f'sequences/{s}/calib.txt'),apply_calib=True));assert gt.shape==t.shape
        ids=list(range(n));li=epm.evaluate_pair(list(gt),list(t),ids);ca=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),ids)
        a=dict(ate=li['ape_aligned_rmse'],ter=ca['kitti_ter_pct'],rer=ca['kitti_rer_deg100m'],segments=ca['kitti_segments'])
        cg=v.load(r.DATA/f'poses/{s}.txt');ct=v.calibration(s);seg=v.segments(cg,ct@t@np.linalg.inv(ct));segments+=len(seg);assert len(seg)==len(ca['kitti_segment_records'])
        b=dict(ate=v.horn_rmse(np.linalg.inv(ct)@cg@ct,t),ter=float(np.mean([p['translation_fraction'] for p in seg])*100),rer=float(np.mean([p['rotation_rad_per_m'] for p in seg])*180/np.pi*100),segments=len(seg))
        for k in a:maximum=max(maximum,abs(a[k]-b[k]));assert abs(a[k]-b[k])<=1e-8
        for p,q in zip(seg,ca['kitti_segment_records']):
            for k in ('first','last','source_first','source_last','length_m'):assert p[k]==q[k]
            for k in ('translation_fraction','rotation_rad_per_m','speed_mps'):maximum=max(maximum,abs(p[k]-q[k]));assert abs(p[k]-q[k])<=2e-10
        save(dest/f'{key}_segments.json',ca['kitti_segment_records']);execution=read(BASE/'bank'/key/'execution.json');receipt=read(BASE/'bank'/key/'worker_exit.json');tm=np.load(BASE/'bank'/key/'frame_timing.npy')
        rows.append(dict(**cell,**a,frames=n,worker_seconds=receipt['wall_seconds'],RSS_bytes=receipt['peak_RSS_bytes'],fine_seconds=execution['fine_seconds'],closures=execution['closures'],local_maps=execution['local_maps'],
            frame_service_time=dict(median=float(np.median(tm[:,-1])),p95=float(np.quantile(tm[:,-1],.95)),p99=float(np.quantile(tm[:,-1],.99)),maximum=float(np.max(tm[:,-1])),over100ms=int(np.sum(tm[:,-1]>.1))),frontend_reference_max=binding['frontend_reference_max']))
        cap()
    return rows,segments,maximum
