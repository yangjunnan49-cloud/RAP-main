"""Export already-validated poses and scalar results; no GT or solver call."""
import hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
import validation_core as c
def run():
    c.verify();result=c.read(c.OUT/'RESULTS02.json');assert len(result['rows'])==72
    assert c.read(c.OUT/'binding_audit.json')['passed']
    assert c.read(c.OUT/'supervision/assess/process_exit.json')['success']
    lines=['**P0 独立验证结果：原预算失败保留，数值与性能分别判定**','',
        '已验证全部72组、六序列、三次重复；只读消费原封存预测，没有重跑原始扫描或求解器。',
        f"独立复核 {result['independent_segments']} 条 KITTI 分段，最大数值差 {result['maximum_metric_delta']:.12g}。来源/图审计覆盖147552帧调用。",'',
        '|模式|串行cell总秒|并行cell总秒|实测耗时减少|串行/并行FPS|18对等价|至少10%收益|各序列退化≤5%|技术门槛合取|',
        '|---|---:|---:|---:|---:|---|---|---|---|']
    for mode in ('G','K'):
        m=result['modes'][mode];g=m['qualification_gates']
        lines.append(f"|{mode}|{m['serial_enclosing_seconds']:.6f}|{m['parallel_enclosing_seconds']:.6f}|{m['time_reduction_percent']:.4f}%|{m['serial_batch_FPS']:.3f}/{m['parallel_batch_FPS']:.3f}|{g['all18_pair_equivalence']}|{g['aggregate_time_reduction_at_least10pct']}|{g['no_sequence_median_slowdown_over5pct']}|{m['qualified']}|")
    lines+=['','|序列|G串行ATE m|G并行ATE m|G并行/串行耗时中位比|K并行/串行耗时中位比|','|---|---:|---:|---:|---:|']
    for s in c.d.SEQS:
        per=result['per_sequence'][s]
        lines.append(f"|{s}|{per['G_S']['ate']['mean']:.9f}|{per['G_P']['ate']['mean']:.9f}|{result['modes']['G']['median_sequence_ratios'][s]:.6f}|{result['modes']['K']['median_sequence_ratios'][s]:.6f}|")
    lines+=['','完整72行、36对配对明细、全部指标/资源/CPU/等待数据见 RESULTS02.json。K的固有重复波动不放宽G判据。',
        '原P0仍为预算FAIL：9316.8147729/9000秒，且该值不含后续文档成本；本次验证不重置或追改原轮。上述“技术门槛合取”不代表原P0全部协议通过。',
        'S1的07ter/10rer失败及06/07/10 ATE退化保持；本次并行工程不能解决这些问题。无新RAP增量证据、默认修改或稳定在线10Hz声明。完整原生CLI地图/占据图副产物不在本测量范围。',
        '所有序列均已暴露；三次进程重复不等于独立泛化。完整原生进程树峰值仍未知，未认证等CPU预算。',
        '本次准备/监督失败与修复记录保留。审计数值成功，但首次外层观察器因共享文件替换冲突退出；恢复记录使用保守包围上界，不声称连续观察无缺口。后续监督器不再在子进程读取时替换共享指针。',
        '标准轨迹ZIP含全部72条未对齐LiDAR 3×4逐行文本；仅序列化封存poses.npy，不换坐标、不重新优化、不筛选重复。','']
    report='\n'.join(lines);(c.OUT/'REPORT_CN.md').write_text(report)
    member_hashes={};archive=c.OUT/'validated_72_trajectories_20261021.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        def put(name,b):member_hashes[name]=hashlib.sha256(b).hexdigest();z.writestr(name,b)
        for row in result['rows']:
            t=np.load(c.OLD/'bank02'/row['key']/'poses.npy');assert t.shape==(row['frames'],4,4) and np.isfinite(t).all()
            out=io.StringIO();np.savetxt(out,t[:,:3,:].reshape(len(t),12),fmt='%.17g');b=out.getvalue().encode()
            # Check exact double round-trip, including one-row dimensional stability.
            assert np.array_equal(np.loadtxt(io.BytesIO(b)).reshape(-1,3,4),t[:,:3,:])
            put('poses/'+row['key']+'.txt',b);c.cap()
        put('README.md',report.encode('utf-8'));put('RESULTS02.json',(c.OUT/'RESULTS02.json').read_bytes())
        for name in ('config_G.json','config_K.json','schedule.json','PROTOCOL.md','bank_seal02.json'):
            put(name,(c.OLD/name).read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(member_hashes) and len(set(z.namelist()))==len(member_hashes)
        for name,h in member_hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
    c.save(c.OUT/'TRAJECTORY_ZIP_CHECKS.json',dict(passed=True,members=len(member_hashes),trajectories=72,frame_occurrences=147552,all_text_double_roundtrips_exact=True,archive_sha256=c.sha(archive),member_sha256=member_hashes))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),constrained_layout=True)
    for ax,mode in zip(axes,('G','K')):
        seqs=c.d.SEQS;x=np.arange(len(seqs));per=result['per_sequence']
        ax.bar(x-.18,[per[s][mode+'_S']['controller_seconds']['mean'] for s in seqs],.36,label='Serial',color='#56758c')
        ax.bar(x+.18,[per[s][mode+'_P']['controller_seconds']['mean'] for s in seqs],.36,label='Parallel queue4',color='#e49d45')
        m=result['modes'][mode];ax.set(title=f"{mode}: time reduction {m['time_reduction_percent']:.2f}%",xlabel='KITTI sequence',ylabel='Mean complete cell time (s)',xticks=x,xticklabels=seqs)
        ax.legend(frameon=False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('All six exposed sequences / three repeats / original P0 budget FAIL retained')
    fig.savefig(c.OUT/'runtime_comparison.png',dpi=170);plt.close(fig)
    c.cap()
    print('Exported72 exact-roundtrip text poses; ZIP and scalar report verified',flush=True)
