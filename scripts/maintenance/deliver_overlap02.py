"""Report all72 frozen paired results and measured resource tradeoffs."""
import time
START=time.monotonic()
import sys,signal,traceback,zipfile,hashlib,csv,shutil
from pathlib import Path
import numpy as np
import overlap_core02 as p
BASE=p.BASE;SUP=p.SUP
def costs():
    rows=[]
    for folder in sorted(SUP.iterdir()):
        if not folder.is_dir():continue
        receipts={n:p.read(folder/n) for n in ('child_exit.json','exit.json','wrapper_exit.json') if (folder/n).exists()}
        if receipts:rows.append(dict(stage=folder.name,enclosing_seconds=max(x['wall_seconds'] for x in receipts.values()),receipts=receipts))
    return rows
def run():
    remaining=p.CAP-p.used();assert remaining>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('P0 cumulative cap')));signal.alarm(max(1,int(remaining)));ok=False;error=None
    try:
        p.verify();result=p.read(BASE/'RESULTS02.json');assert len(result['rows'])==72 and result['independent_metric_validation_passed'] and p.read(BASE/'binding_audit.json')['passed']
        seal=p.read(BASE/'bank_seal02.json');assert seal['cells']==72
        for name,h in seal['files'].items():assert p.sha(BASE/'bank02'/name)==h,name
        p.save(BASE/'DELIVERY_SOURCE_BINDING.json',dict(utc=p.now(),files={str(x):p.sha(x) for x in (Path(__file__),BASE/'RESULTS02.json',BASE/'binding_audit.json',BASE/'bank_seal02.json',BASE/'PROTOCOL.md',BASE/'BINDING02_SUPPLEMENT.md')}))
        rows=result['rows'];labels=['G_S','G_P','K_S','K_P'];per=result['per_sequence'];stats={}
        for label in labels:
            selected=[x for x in rows if x['mode']+'_'+x['scheduler']==label];assert len(selected)==18
            packet=np.concatenate([np.load(BASE/'bank02'/x['key']/'pipeline_timing.npy')[:,2] for x in selected]);wall=sum(x['controller_seconds'] for x in selected);cpu=sum(x['CPU_seconds'] for x in selected)
            stats[label]=dict(cells=18,frames=36888,enclosing_cell_seconds=wall,batch_FPS=36888/wall,CPU_seconds=cpu,CPU_seconds_per1000frames=cpu/36.888,maximum_individual_process_RSS_bytes=max(x['peak_process_RSS'] for x in selected),packet_age_seconds=dict(median=float(np.median(packet)),p95=float(np.quantile(packet,.95)),p99=float(np.quantile(packet,.99)),maximum=float(packet.max())))
        p.save(BASE/'OPERATIONAL_RESULTS.json',dict(utc=p.now(),modes=stats,unpaced_batch=True,packet_age_is_prepare_start_to_map_finish=True,packet_age_is_not_live_sensor_latency=True,no_equal_CPU_budget_claim=True,native_registration_max_num_threads=0,whole_native_tree_peak='UNKNOWN',synthetic_IPC_sender_peak='UNKNOWN',CPU_seconds_add_producer_only_for_P=True,nested_wall_not_added=True))
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        colors={'G_S':'#79b49b','G_P':'#147b57','K_S':'#ecc274','K_P':'#bd7f0b'};ix=np.arange(6)
        fig,axes=plt.subplots(2,1,figsize=(12,8))
        for j,label in enumerate(labels):
            vals=[per[s][label]['controller_seconds']['mean'] for s in p.d.SEQS];sd=[per[s][label]['controller_seconds']['std'] for s in p.d.SEQS];axes[0].bar(ix+(j-1.5)*.19,vals,.19,yerr=sd,capsize=2,label=label,color=colors[label])
            vals=[per[s][label]['CPU_seconds']['mean'] for s in p.d.SEQS];axes[1].bar(ix+(j-1.5)*.19,vals,.19,color=colors[label])
        axes[0].set_ylabel('Enclosing cell seconds');axes[0].set_title('Fresh interpreter + all raw-core work + minimal/proof outputs');axes[0].legend(ncol=4,frameon=False)
        axes[1].set_ylabel('Process CPU seconds (parent + P producer)');axes[1].set_title('Native automatic threads preserved; no equal-CPU-budget claim')
        for ax in axes:ax.set_xticks(ix,p.d.SEQS);ax.grid(axis='y',alpha=.18)
        fig.suptitle('P0 complete raw-core runtime overlap | all six sequences, three process repeats',fontsize=12);fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(BASE/'runtime_CPU.png',dpi=170);plt.close(fig)
        fig,axes=plt.subplots(2,1,figsize=(12,8))
        for j,label in enumerate(labels):
            vals=[per[s][label]['ate']['mean'] for s in p.d.SEQS];sd=[per[s][label]['ate']['std'] for s in p.d.SEQS];axes[0].bar(ix+(j-1.5)*.19,vals,.19,yerr=sd,capsize=2,label=label,color=colors[label])
            vals=[per[s][label]['ter']['mean'] for s in p.d.SEQS];sd=[per[s][label]['ter']['std'] for s in p.d.SEQS];axes[1].bar(ix+(j-1.5)*.19,vals,.19,yerr=sd,capsize=2,color=colors[label])
        axes[0].set_ylabel('Aligned LiDAR ATE (m)');axes[0].legend(ncol=4,frameon=False);axes[1].set_ylabel('KITTI camera ter (%)')
        for ax in axes:ax.set_xticks(ix,p.d.SEQS);ax.grid(axis='y',alpha=.18)
        fig.suptitle('All72 accuracy results | error bars: process-repeat SD, not independent scenes',fontsize=12);fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(BASE/'accuracy_all72.png',dpi=170);plt.close(fig)
        costrows=costs();charged=sum(x['enclosing_seconds'] for x in costrows);p.save(BASE/'COSTS_SNAPSHOT.json',dict(utc=p.now(),stages=costrows,charged_before_delivery=charged,original_P0_cap=9000,old_R0_S1_6762_0941485_unchanged=True))
        text='# P0：原始扫描串行与有界FIFO实测\n\n完整72单元：G/K ×串行S/双进程FIFO P ×六序列 ×三次新进程重复，共147552次源帧调用。旧S1结果不作新前端输入/成功计时样本。原首个P00因遗漏now元数据导入失败，原失败完整保留，限定导入修复后重算该唯一失败单元；原失败成本和全部准备仍在同一9000s。队列4、配置、数学、种子策略与所有门槛不变。\n\n'
        for mode in ('G','K'):
            q=result['modes'][mode];text+=f"{mode}资格通过：**{q['qualified']}**。完整cell总耗时S/P={q['serial_enclosing_seconds']:.6f}/{q['parallel_enclosing_seconds']:.6f}s，减少{q['time_reduction_percent']:.3f}%；批处理FPS={q['serial_batch_FPS']:.3f}/{q['parallel_batch_FPS']:.3f}。失败等价配对：{q['failed_equivalence_pairs']}。全部资格门槛：{q['qualification_gates']}。\n\n"
        text+='G与原生K分别判定，K的失败不放宽G。K00/09原本已有不稳定性，原因未知，没有改种子/线程数/数据以消除它。单独S/P结果不是新RAP增量或独立泛化证明。\n\n![运行时间与CPU](runtime_CPU.png)\n\n|模式|完整cell秒|批处理FPS|CPU秒/千帧|包年龄p99 ms|包年龄最大ms|单进程峰值bytes|\n|---|---:|---:|---:|---:|---:|---:|\n'
        for label,x in stats.items():text+=f"|{label}|{x['enclosing_cell_seconds']:.6f}|{x['batch_FPS']:.3f}|{x['CPU_seconds_per1000frames']:.3f}|{x['packet_age_seconds']['p99']*1000:.3f}|{x['packet_age_seconds']['maximum']*1000:.3f}|{x['maximum_individual_process_RSS_bytes']}|\n"
        text+='\ncell覆盖启动/导入、读盘/哈希/预处理/真实前端、地图全部闭环/细图/检查/最小输出及P实际spawn/IPC/等待。P两个数值进程；原max_num_threads=0自动策略保留，OMP/MKL/BLAS1不保证全部原生线程数，也不保证等CPU预算。CPU时间只在P加独立producer；嵌套wall永不相加。包年龄为准备开始到地图处理结束，包含队列等待，是未限速批输入下的实测年龄，不能当传感器在线延迟；frame服务时间求和也不是并行wall。大地图/占据图/可视化导出两者均未运行。原生完整进程树峰值与独立合成IPC发送者峰值UNKNOWN。\n\n![全72精度](accuracy_all72.png)\n\n|序列|G_S ATE|G_P ATE|K_S ATE|K_P ATE|G_S ter|G_P ter|K_S ter|K_P ter|\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
        for seq in p.d.SEQS:text+='|'+seq+'|'+'|'.join(f'{per[seq][label][k]["mean"]:.9f}' for k in ('ate','ter') for label in labels)+'|\n'
        text+='|平均|'+'|'.join(f'{result["means"][label][k]:.9f}' for k in ('ate','ter') for label in labels)+'|\n\n'
        for name,v in result['accuracy_comparisons'].items():text+=f"{name}平均目标={v['primary_passed']}；逐序列保护={v['safety_passed']}；失败项={[x for x,y in v['safety'].items() if not y]}。\n\n"
        text+=f"所有72预测先封存，后作源/图/IPC审计及GT指标。独立Horn/KITTI复核{result['independent_segments']}段，最大差{result['maximum_metric_delta']:.6g}。producer/consumer逐包hash/全帧顺序/原前端准备字节均检查；这是每次运行内的精确传输证明，独立新算的G位姿不声称跨运行逐位相同。地图预处理和非线性优化器不是独立重写，物理真实性/逐回波谱系/训练排除仍未知。\n\n交付前P0累计{charged:.6f}/9000s，当前交付与末次native检查后追加COSTS_FINAL，绝不重置旧账本。旧R0+S1已关闭6762.0941485/7200s保持，旧LMB1073.9382182/1800s等历史预算不变。4GiB单Python/256MiB dossier/GPU0/原12GiB单调时钟<=2s启动保护。\n\n这是系统工程验证，不自动改默认/生产/安装环境/模型/论文/参考/Git/外联/调度/目标状态，也不宣称稳定在线10Hz或新RAP效益。原科研目标仍未解决；实际账户边界单独记录，无自动重置续跑。\n"
        with (BASE/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
        export=BASE/'trajectory_exports';export.mkdir()
        for row in rows:
            a=np.load(BASE/'bank02'/row['key']/'poses.npy');out=export/f'{row["key"]}_lidar.txt';np.savetxt(out,a[:,:3,:].reshape(-1,12),fmt='%.17g');assert np.max(abs(np.loadtxt(out).reshape(-1,3,4)-a[:,:3,:]))<=1e-8
        p.save(export/'RESULTS.json',result);p.save(export/'OPERATIONAL_RESULTS.json',p.read(BASE/'OPERATIONAL_RESULTS.json'))
        (export/'README.md').write_text('''# P0 experimental raw-core72 poses
All6 sequences00/05/06/07/09/10, G/K, S(serial)/P(queue4 two processes), repeats1/2/3. Row i is original scan i,12 numbers: first3 rows of unaligned world-from-LiDAR4x4, meters. Append homogeneous row0 0 0 1. No aligned/camera poses exported. Metrics use aligned LiDAR ATE and calibrated camera KITTI ter/rer internally. Read RESULTS/REPORT for every qualification failure; no automatic default promotion or new RAP efficacy. Three process repeats are exposed scenes. Fresh process is not certified cold filesystem. P native auto threads preserved/no equal-CPU claim. Batch packet age is not live sensor latency/no guaranteed10Hz. Configs are used settings; raw data/GT/installers are not included. Full source/failure/cost provenance remains in companion repository report.
''',encoding='utf-8')
        for label in ('G','K'):shutil.copy2(BASE/f'config_{label}.json',export/f'CONFIG_{label}.json')
        with (export/'CELLS.csv').open('x',newline='',encoding='utf-8') as f:
            fields=['key','sequence','mode','scheduler','repeat','frames','ate','ter','rer','controller_seconds','CPU_seconds','peak_process_RSS'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:x[k] for k in fields} for x in rows)
        p.save(export/'FILE_SHA256.json',dict(files={str(x.relative_to(export)):p.sha(x) for x in export.rglob('*') if x.is_file()}))
        zp=BASE/'P0_raw_overlap_72poses_20261021.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for x in sorted(export.rglob('*')):
                if x.is_file():z.write(x,str(x.relative_to(export)))
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for name,h in p.read(export/'FILE_SHA256.json')['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
        p.cap();p.save(BASE/'STATUS.json',dict(utc=p.now(),status='COMPLETE_ALL72_EVALUATED',G_pipeline_qualified=result['modes']['G']['qualified'],K_pipeline_qualified=result['modes']['K']['qualified'],original_failed_run_retained=True,old_scopes_unchanged=True,defaults_changed=False,new_RAP_efficacy=False))
        p.save(BASE/'DELIVERY_SEAL.json',dict(utc=p.now(),files={str(x.relative_to(BASE)):p.sha(x) for x in sorted(BASE.rglob('*')) if x.is_file() and 'supervision' not in x.parts and x.name!='DELIVERY_SEAL.json'}));print('P0 complete report/plots/72trajectory archive',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc();p.save(BASE/'DELIVERY_FAILURE.json',dict(utc=p.now(),error=error))
    finally:signal.alarm(0);p.save(SUP/'deliver/child_exit.json',dict(utc=p.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**p.process_usage(),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='deliver';run()
