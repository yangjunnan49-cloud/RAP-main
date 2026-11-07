"""Independent scalar MC1 verification; no runner or project algorithm imports."""
from pathlib import Path
import hashlib,json,math,re,resource,time
import numpy as np
MAIN=Path(__file__).resolve().parents[2];BASE=MAIN/'docs/maintenance/2026-10-07/measurement-source-audit-01'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
f=read(BASE/'freeze.json')
for p,h in f['files'].items():assert sha(p)==h,p
assert sha(BASE/'census.json')==read(BASE/'census_seal.json')['sha256']
data=read(BASE/'census.json');start=time.perf_counter();count=0;delta=0.
for s,n in f['sequences'].items():
    root=MAIN/f"docs/maintenance/{'2026-09-26/e0-frontend-01' if s in ('00','05','06') else '2026-09-27/e0-heldout-01'}/full-{s}-A"
    p=np.loadtxt(root/'odom_poses.txt').reshape(-1,3,4);kf=read(root/'keyframes.json');meta=read(root/'source_frames.json');r=data['rows'][s]
    assert len(p)==r['scans']==n and meta['source_frame_ids']==list(range(n))
    steps=[];turns=[];expected=[0];path=angle=0.
    for i in range(1,n):
        d=math.sqrt(sum((float(p[i,k,3])-float(p[i-1,k,3]))**2 for k in range(3)))
        a=math.atan2(float(p[i,1,0]),float(p[i,0,0]));b=math.atan2(float(p[i-1,1,0]),float(p[i-1,0,0]))
        rot=abs((a-b+math.pi)%(2*math.pi)-math.pi);steps.append(d);turns.append(rot);path+=d;angle+=rot
        if path>6 or angle>math.radians(12):expected.append(i);path=angle=0.
    if expected[-1]!=n-1:expected.append(n-1)
    assert kf==expected and len(kf)==r['keyframes']
    intervals=r['intervals'];assert len(intervals)==len(kf)-1
    for e,(a,b) in zip(intervals,zip(kf[:-1],kf[1:])):
        values={'path_m':math.fsum(steps[a:b]),'absolute_yaw_deg':math.degrees(math.fsum(turns[a:b])),'scan_span':b-a}
        assert e['a']==a and e['b']==b
        for name,value in values.items():error=abs(value-e[name]);delta=max(delta,error);assert error<1e-9
        if meta.get('timestamps') is not None:assert abs(meta['timestamps'][b]-meta['timestamps'][a]-e['elapsed_s'])<1e-10
        assert e['terminal_forced']==(b==n-1 and values['path_m']<=6 and values['absolute_yaw_deg']<=12);count+=1
    for name,field in [('span_summary','scan_span'),('path_summary','path_m'),('yaw_summary','absolute_yaw_deg')]:
        a=sorted(e[field] for e in intervals)
        def percentile(q):
            pos=(len(a)-1)*q;lo=math.floor(pos);hi=math.ceil(pos);return a[lo]+(a[hi]-a[lo])*(pos-lo)
        values=dict(min=a[0],median=percentile(.5),p95=percentile(.95),max=a[-1])
        assert all(abs(values[k]-r[name][k])<1e-9 for k in values)
    events={};starts=[];ends=[]
    for line in (root/'verification_measurements.jsonl').open():
        event=re.match(r'\{"event":\s*"([^"]+)"',line)[1];events[event]=events.get(event,0)+1
        if event=='candidate_started':
            v=json.loads(line);starts.append(dict(i=v['i'],j=v['j'],attempt_id=v['attempt_id']))
        if event=='candidate_finished':
            v=json.loads(line);ends.append(dict(attempt_id=v['attempt_id'],status=v['status']))
    assert events==r['events'] and starts==r['started'] and ends==r['finished']
    assert len(starts)==len(ends) and [x['attempt_id'] for x in starts]==[x['attempt_id'] for x in ends]
    edges=read(root/'accepted_loops.json');endpoints=sorted(set([x['i'] for x in edges]+[x['j'] for x in edges]))
    assert endpoints==r['loop_endpoints'] and len(edges)==r['accepted_edges']
    assert len(endpoints)/len(kf)==r['loop_endpoint_fraction']
assert count==sum(r['keyframes']-1 for r in data['rows'].values())
assert sum(r['accepted_edges'] for r in data['rows'].values())==58
assert sum(len(r['started']) for r in data['rows'].values())==71
wall=time.perf_counter()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
assert wall<=120 and rss<=2**30
save(BASE/'validation.json',dict(passed=True,intervals=count,max_motion_delta=delta,wall_s=wall,peak_rss_bytes=rss,
    gt_read=False,source_id_binding=True,original_keyframes_exact=True,original_attempts=71,accepted_edges=58))
save(BASE/'validation_seal.json',dict(sha256=sha(BASE/'validation.json'),census_sha256=sha(BASE/'census.json')))
(BASE/'INCOMPLETE').unlink();print('MC1 independent passed',count,'intervals, delta',delta,flush=True)
