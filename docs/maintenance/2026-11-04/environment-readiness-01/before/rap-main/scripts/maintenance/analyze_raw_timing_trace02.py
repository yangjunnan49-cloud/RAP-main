"""Fixed ideal FIFO analysis of all36 sealed timing traces, no new predictions."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,heapq
from pathlib import Path
import numpy as np
import raw_input_system06 as d
BASE=d.BASE;DEST=BASE/'timing_analysis02';SUP=d.SUP
def fifo(a,b,arrival):
    n=len(a);front=np.empty(n);back=np.empty(n);beg=np.empty(n);x=y=0.
    for i in range(n):
        x=max(float(arrival[i]),x)+float(a[i]);front[i]=x
        beg[i]=max(x,y);y=beg[i]+float(b[i]);back[i]=y
    assert np.all(np.diff(front)>=0) and np.all(np.diff(back)>=0)
    assert np.all(beg>=front) and np.all(back>=beg)
    # Events for waiting packets only, half-open [front_complete, map_start).
    events=[]
    for x,y in zip(front,beg):
        if x<y:events.extend(((float(x),1),(float(y),-1)))
    count=maximum=0
    for _,delta in sorted(events,key=lambda t:(t[0],t[1])):
        count+=delta;assert count>=0;maximum=max(maximum,count)
    assert count==0
    # Independent binary-search query of all readiness/start boundaries.
    times=np.unique(np.r_[front,beg]);independent=np.searchsorted(front,times,side='right')-np.searchsorted(beg,times,side='right')
    assert int(independent.max(initial=0))==maximum
    return back,maximum
def serial(duration,arrival):
    out=[];x=0.
    for ar,dur in zip(arrival,duration):x=max(x,float(ar))+float(dur);out.append(x)
    return np.asarray(out)
def summary(fin,ar):
    z=fin-ar
    return dict(frames=len(z),last_complete_seconds=float(fin[-1]),latency_seconds=dict(median=float(np.median(z)),p95=float(np.quantile(z,.95)),p99=float(np.quantile(z,.99)),maximum=float(z.max()),over100ms=int(np.sum(z>.1))))
def run():
    ok=False;error=None;peak=0
    remaining=d.CAP-d.used();limit=min(120.-max(d.read(SUP/'timing_analysis'/n)['wall_seconds'] for n in ('child_exit.json','exit.json')),remaining);assert limit>1
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('analysis/original cumulative cap')));signal.alarm(max(1,int(limit)))
    try:
        d.verify();assert d.read(BASE/'FINAL_NATIVE_CHECKS.json')['passed'];DEST.mkdir()
        protocol=BASE/'TIMING_ANALYSIS_PROTOCOL.md';d.save(DEST/'SOURCE_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),protocol,BASE/'bank_seal06.json',BASE/'OPERATIONAL_RESULTS.json')},remaining_shared_seconds=remaining,subcap_seconds=limit,new_predictions=0))
        a=np.array([2.,1.,3.]);b=np.array([1.,4.,1.]);ar=np.zeros(3);f,q=fifo(a,b,ar);assert np.array_equal(f,[3.,7.,8.]) and q==1
        a=np.array([1.,1.,1.]);b=np.array([4.,4.,4.]);f,q=fifo(a,b,np.zeros(3));assert np.array_equal(f,[5.,9.,13.]) and q==2
        assert np.array_equal(serial(np.array([3.,2.,4.]),np.array([0.,10.,10.])),[3.,12.,16.])
        d.save(DEST/'SYNTHETIC.json',dict(passed=True,fixed_hand_derived_fixtures=3))
        seal=d.read(BASE/'bank_seal06.json');rows=[];maximum_error=0.
        for cell in d.read(BASE/'freeze.json')['schedule']:
            p=BASE/'bank06'/cell['key']/'frame_timing.npy';assert d.sha(p)==seal['files'][str(p.relative_to(BASE/'bank06'))]
            tm=np.load(p);a=tm[:,:3].sum(1);b=tm[:,3];total=tm[:,4];e=float(np.max(abs(a+b-total)));assert e<=1e-9;maximum_error=max(maximum_error,e)
            item=dict(**cell,frames=len(tm),source_timing_sha256=d.sha(p),stage_A_seconds=float(a.sum()),stage_B_seconds=float(b.sum()),measured_frame_total_seconds=float(total.sum()),scenarios={})
            for name,arrivals in [('unpaced',np.zeros(len(tm))),('synthetic10Hz',np.arange(len(tm))*.1)]:
                sf=serial(total,arrivals);pf,q=fifo(a,b,arrivals)
                assert np.all(pf<=sf+1e-9)
                if name=='unpaced':assert abs(sf[-1]-total.sum())<=1e-8
                item['scenarios'][name]=dict(serial=summary(sf,arrivals),ideal_FIFO=summary(pf,arrivals),maximum_waiting_map_packets=q,ideal_overlap_gain_fraction=float(1-pf[-1]/sf[-1]))
            rows.append(item)
        aggregates={}
        for mode in ('G','K'):
            rr=[x for x in rows if x['mode']==mode];assert len(rr)==18
            aggregates[mode]=dict(cells=len(rr),frames=sum(x['frames'] for x in rr),stage_A_seconds=sum(x['stage_A_seconds'] for x in rr),stage_B_seconds=sum(x['stage_B_seconds'] for x in rr),
                unpaced_serial_seconds=sum(x['scenarios']['unpaced']['serial']['last_complete_seconds'] for x in rr),unpaced_ideal_FIFO_seconds=sum(x['scenarios']['unpaced']['ideal_FIFO']['last_complete_seconds'] for x in rr),
                synthetic10Hz_maximum_queue=max(x['scenarios']['synthetic10Hz']['maximum_waiting_map_packets'] for x in rr),
                synthetic10Hz_serial_over100ms=sum(x['scenarios']['synthetic10Hz']['serial']['latency_seconds']['over100ms'] for x in rr),
                synthetic10Hz_ideal_FIFO_over100ms=sum(x['scenarios']['synthetic10Hz']['ideal_FIFO']['latency_seconds']['over100ms'] for x in rr),
                synthetic10Hz_maximum_serial_latency=max(x['scenarios']['synthetic10Hz']['serial']['latency_seconds']['maximum'] for x in rr),synthetic10Hz_maximum_ideal_FIFO_latency=max(x['scenarios']['synthetic10Hz']['ideal_FIFO']['latency_seconds']['maximum'] for x in rr))
        result=dict(utc=d.now(),cells=36,source_frame_occurrences=sum(x['frames'] for x in rows),maximum_timing_partition_delta=maximum_error,all_synthetic_and_independent_queue_checks_passed=True,rows=rows,aggregates=aggregates,
            measured_parallel_speedup=False,zero_IPC_and_contention_assumption=True,actual_parallel_runtime_UNKNOWN=True,no_online10Hz_claim=True,new_predictions=0,new_GT_metrics=0)
        d.save(DEST/'RESULTS.json',result)
        text='# 固定耗时轨迹的理想FIFO分析\n\n这是一项调度算术，不是并行性能实测。全部36单元/73776帧调用纳入；两模式使用同一分区和两个预定到达场景。\n\n|模式|A准备/前端秒|B地图秒|未限速串行帧秒|理想FIFO秒|合成10Hz串行>100ms帧|理想FIFO>100ms帧|理想最大排队帧|理想最大延迟ms|\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
        for m,x in aggregates.items():text+=f"|{m}|{x['stage_A_seconds']:.3f}|{x['stage_B_seconds']:.3f}|{x['unpaced_serial_seconds']:.3f}|{x['unpaced_ideal_FIFO_seconds']:.3f}|{x['synthetic10Hz_serial_over100ms']}|{x['synthetic10Hz_ideal_FIFO_over100ms']}|{x['synthetic10Hz_maximum_queue']}|{x['synthetic10Hz_maximum_ideal_FIFO_latency']*1000:.3f}|\n"
        text+='\nA为读盘/哈希+预处理/输入审计+独立E0前端，B为原生地图/闭环；K的E0时钟仅包含近零计时开销。串行输入是每帧实测总耗时，额外等待计入合成到达延迟；它不同于原报告的单帧循环耗时。固定合成到达为每100ms一帧，并非实测传感器时钟。理想队列只统计准备完毕而地图尚未开始的包，不等于实际内存或包含正在处理的帧。\n\n所有分区、FIFO单调/完整顺序、串行累计与事件队列均校验通过，3个手算fixture先于真实耗时分析。测量发生于串行共享机器，重叠下的核竞争、IPC、缓存、数组拷贝、进口/日志/最终细图和输出未知或未建模。不能据此宣称在线10Hz或实测加速；完整原始系统指标和各失败保护不变。\n\n若理想模型仍有超期，它不能支撑严格每帧100ms期限；可以另行定义有限的运行时等价工程验证，但须先冻结接口/顺序/等价门槛、资源及强串行对照。此分析不自动启动原始扫描重放/新求解器/参数调整。\n'
        (DEST/'REPORT.md').write_text(text,encoding='utf-8')
        assert sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file())<=8*2**20
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;assert peak<=256*2**20;d.cap()
        d.save(DEST/'DELIVERY_SEAL.json',dict(utc=d.now(),files={str(p.relative_to(DEST)):d.sha(p) for p in DEST.rglob('*') if p.is_file()}))
        print('All36 timing traces checked',aggregates,flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc();d.save(BASE/'TIMING_ANALYSIS02_FAILURE.json',dict(utc=d.now(),error=error))
    finally:
        signal.alarm(0);d.save(SUP/'timing_analysis02/child_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0,no_new_predictions=True))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='timing_analysis02';run()
