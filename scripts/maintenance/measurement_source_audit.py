"""MC1 read-only census, never parses generation labels or evaluator GT."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,re,resource,time,traceback
import numpy as np
MAIN=Path(__file__).resolve().parents[2];SLAM=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-10-07/measurement-source-audit-01'
PARENT=MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01'
SEQS={'00':4541,'05':2761,'06':1101,'07':1101,'09':1591,'10':1201}
def source(s):return MAIN/f"docs/maintenance/{'2026-09-26/e0-frontend-01' if s in ('00','05','06') else '2026-09-27/e0-heldout-01'}/full-{s}-A"
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
def freeze():
    assert not (BASE/'freeze.json').exists()
    assert read(PARENT/'validation.json')['passed']
    old=read(PARENT/'freeze.json')['files']
    files=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_measurement_source_audit.py'),PARENT/'freeze.json',PARENT/'validation.json']
    for s in SEQS:
        for name in ['odom_poses.txt','keyframes.json','source_frames.json','verification_measurements.jsonl','accepted_loops.json','run_manifest.json']:
            p=source(s)/name
            if str(p) in old:assert sha(p)==old[str(p)]
            files.append(p)
    files += [SLAM/'rap_slam'/x for x in ['pose_graph.py','keyframes.py','odometry.py','scan_context.py','loop_closure.py','verification_log.py','measurement.py']]
    files.append(SLAM/'scripts/run_pipeline.py')
    package=Path(importlib.util.find_spec('kiss_icp').origin).parent
    files += [package/x for x in ['kiss_icp.py','registration.py','mapping.py','threshold.py']]
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in files},sequences=SEQS,gt_read=False))
    (BASE/'INCOMPLETE').write_text('MC1 independent validation pending\n')
    print('MC1 frozen',len(files),'identities',flush=True)
def describe(a):return dict(min=float(np.min(a)),median=float(np.median(a)),p95=float(np.quantile(a,.95)),max=float(np.max(a)))
def census():
    verify();start=time.perf_counter();rows={}
    for s,n in SEQS.items():
        root=source(s);p=np.loadtxt(root/'odom_poses.txt').reshape(-1,3,4);assert len(p)==n
        kf=read(root/'keyframes.json');meta=read(root/'source_frames.json');ids=np.asarray(meta['source_frame_ids']);assert np.array_equal(ids,np.arange(n))
        config=read(root/'run_manifest.json')['config'];assert config['kf_trans']==6 and config['kf_rot']==12
        steps=np.linalg.norm(np.diff(p[:,:,3],axis=0),axis=1);yaw=np.arctan2(p[:,1,0],p[:,0,0]);turn=np.abs((np.diff(yaw)+np.pi)%(2*np.pi)-np.pi)
        stamps=meta.get('timestamps');intervals=[]
        for a,b in zip(kf[:-1],kf[1:]):
            path=float(steps[a:b].sum());angular=float(np.rad2deg(turn[a:b].sum()))
            intervals.append(dict(a=a,b=b,scan_span=int(ids[b]-ids[a]),path_m=path,absolute_yaw_deg=angular,
                elapsed_s=None if stamps is None else float(stamps[b]-stamps[a]),terminal_forced=bool(b==n-1 and path<=6 and angular<=12)))
        events={};started=[];finished=[]
        for line in (root/'verification_measurements.jsonl').open():
            event=re.match(r'\{"event":\s*"([^"]+)"',line)[1];events[event]=events.get(event,0)+1
            if event not in ('candidate_started','candidate_finished'):continue
            v=json.loads(line)
            if event=='candidate_started':started.append(dict(i=v['i'],j=v['j'],attempt_id=v['attempt_id']))
            else:finished.append(dict(attempt_id=v['attempt_id'],status=v['status']))
        edges=read(root/'accepted_loops.json');endpoints=sorted({int(e[x]) for e in edges for x in ('i','j')})
        assert set(endpoints)<=set(kf)
        rows[s]=dict(scans=n,keyframes=len(kf),intervals=intervals,span_summary=describe([x['scan_span'] for x in intervals]),
            path_summary=describe([x['path_m'] for x in intervals]),yaw_summary=describe([x['absolute_yaw_deg'] for x in intervals]),
            elapsed_summary=None if stamps is None else describe([x['elapsed_s'] for x in intervals]),
            rotation_before_translation=sum(x['absolute_yaw_deg']>12 and x['path_m']<=6 for x in intervals),
            terminal_forced=sum(x['terminal_forced'] for x in intervals),events=events,started=started,finished=finished,
            accepted_edges=len(edges),loop_endpoints=endpoints,loop_endpoint_fraction=len(endpoints)/len(kf),
            covariance_saved=False,map_correlations_saved=False,complete_retrieval_exposure_saved=False)
    verify();wall=time.perf_counter()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    assert wall<=120 and rss<=2**30
    save(BASE/'census.json',dict(utc=now(),rows=rows,wall_s=wall,peak_rss_bytes=rss,gt_read=False,optimization=False))
    save(BASE/'census_seal.json',dict(utc=now(),sha256=sha(BASE/'census.json'),freeze_sha256=sha(BASE/'freeze.json')))
    print('MC1 census',sum(r['keyframes'] for r in rows.values()),'keyframes',flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','census']);a=parser.parse_args()
    try:globals()[a.stage]()
    except Exception as e:
        p=BASE/f'FAILURE_{a.stage}.json'
        if not p.exists():save(p,dict(error=repr(e),traceback=traceback.format_exc()))
        raise
