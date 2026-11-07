"""Complete raw-core reporting/figures/pose export from sealed validated results."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,zipfile,hashlib,json
from pathlib import Path
import numpy as np
import raw_input_system04 as d
BASE=d.BASE;SUP=d.SUP;R0=d.R0
def used():return d.used()
def costs():
    rows=[]
    for root in (R0,BASE):
        for p in sorted((root/'supervision').glob('*/child_exit.json')):
            x=d.read(p);values=[x['wall_seconds']]
            for name in ('exit.json','wrapper_exit.json'):
                if p.with_name(name).exists():values.append(d.read(p.with_name(name))['wall_seconds'])
            rows.append(dict(scope=root.name,stage=p.parent.name,success=x['success'],enclosing_seconds=max(values),reported_Python_RSS=x['peak_RSS_bytes']))
    return rows
def run():
    left=7200-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('shared campaign cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        d.verify();result=d.read(BASE/'results04.json');audit=d.read(BASE/'binding_audit.json');assert result['independent_validation_passed'] and audit['passed']
        seal=d.read(BASE/'bank_seal04.json')
        for p,h in seal['files'].items():assert d.sha(BASE/'bank04'/p)==h
        d.save(BASE/'DELIVERY_SOURCE_BINDING.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),BASE/'results04.json',BASE/'binding_audit.json',BASE/'bank_seal04.json',BASE/'S1_EXECUTION_FREEZE.json')}))
        rows=result['rows'];stats={};per=result['per_sequence'];means=result['means']
        for mode in ('G','K'):
            selected=[x for x in rows if x['mode']==mode];wall=0.;latency=[];serialization=0.;fine=0.;column_sums=np.zeros(5)
            for row in selected:
                key=row['key'];receipt=d.read(SUP/'run04'/key/'controller_exit.json');wall+=receipt['wall_seconds'];tm=np.load(BASE/'bank04'/key/'frame_timing.npy');latency.extend(tm[:,-1]);column_sums+=tm.sum(0)
                ex=d.read(BASE/'bank04'/key/'execution.json');serialization+=ex['serialization_seconds'];fine+=ex['fine_seconds']
            stats[mode]=dict(cells=len(selected),frames=sum(x['frames'] for x in selected),enclosing_cell_seconds=wall,batch_frames_per_second=sum(x['frames'] for x in selected)/wall,
                frame_seconds=dict(median=float(np.median(latency)),p95=float(np.quantile(latency,.95)),p99=float(np.quantile(latency,.99)),maximum=float(np.max(latency)),over100ms=int(np.sum(np.asarray(latency)>.1))),
                summed_frame_clock_columns=column_sums.tolist(),serialization_seconds=serialization,fine_and_source_check_seconds=fine,maximum_successful_worker_RSS_bytes=max(x['RSS_bytes'] for x in selected))
        d.save(BASE/'OPERATIONAL_RESULTS.json',dict(utc=d.now(),modes=stats,clock_columns=['read_hash','preprocess_and_input_audit','E0_frontend_G_only','native_process_scan','frame_total'],
            frame_clock_excludes_outside_loop_logging_and_cap_checks=True,cell_wall_includes_all_interpreter_import_validation_outputs=True,first_K_retained_once=True,cold_OS_cache_not_certified=True,guaranteed_online_10Hz=False))
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(3,1,figsize=(12,10));ix=np.arange(6);colors={'G':'#16835c','K':'#d99b26'}
        for ax,k,label in zip(axes,('ate','ter','rer'),('Aligned LiDAR ATE (m)','KITTI camera ter (%)','KITTI camera rer (degree / 100 m)')):
            for j,m in enumerate(('G','K')):
                values=[per[s][m][k]['mean'] for s in d.SEQS];std=[per[s][m][k]['std'] for s in d.SEQS];bars=ax.bar(ix+(j-.5)*.32,values,.32,yerr=std,capsize=3,color=colors[m],label=m);ax.bar_label(bars,fmt='%.3f',padding=4,fontsize=9)
            ax.set_xticks(ix,d.SEQS);ax.set_ylabel(label);ax.grid(axis='y',alpha=.18);ax.set_ylim(0,max(per[s][m][k]['maximum'] for s in d.SEQS for m in ('G','K'))*1.2)
            ax.set_title(f"Six-sequence mean: G {means['G'][k]:.6f}; K {means['K'][k]:.6f}",fontsize=11)
        axes[0].legend(frameon=False,ncol=2);fig.suptitle('Complete fresh-raw trajectory core | three process repeats per sequence\nError bars: process-repeat SD; all six exposed development sequences',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(BASE/'raw_core_metrics.png',dpi=170);plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(12,4.5));bars=axes[0].bar(['G','K'],[stats[m]['batch_frames_per_second'] for m in ('G','K')],color=[colors[m] for m in ('G','K')]);axes[0].bar_label(bars,fmt='%.2f',padding=4);axes[0].set_ylim(0,max(stats[m]['batch_frames_per_second'] for m in ('G','K'))*1.2);axes[0].set_ylabel('Batch frames / enclosing cell second');axes[0].set_title('Fresh process + all core work + minimal outputs')
        labels=['median','p95','p99','maximum'];xx=np.arange(4)
        for j,m in enumerate(('G','K')):axes[1].bar(xx+(j-.5)*.32,[1000*stats[m]['frame_seconds'][k] for k in labels],.32,color=colors[m],label=m)
        axes[1].set_xticks(xx,labels);axes[1].set_yscale('log');axes[1].set_ylabel('Measured frame processing time (ms, log)');axes[1].set_title('Tail latency; final correction reported separately');axes[1].legend(frameon=False);fig.tight_layout();fig.savefig(BASE/'raw_core_operations.png',dpi=170);plt.close(fig)
        table='|序列|G ATE m|K ATE m|G ter %|K ter %|G rer|K rer|\n|---|---:|---:|---:|---:|---:|---:|\n'
        for s in d.SEQS:table+='|'+s+'|'+ '|'.join(f'{per[s][m][k]["mean"]:.9f}' for k in ('ate','ter','rer') for m in ('G','K'))+'|\n'
        table+='|平均|'+ '|'.join(f'{means[m][k]:.9f}' for k in ('ate','ter','rer') for m in ('G','K'))+'|\n'
        failures=[k for k,v in result['safety'].items() if not v];stagecost=costs();charged=sum(x['enclosing_seconds'] for x in stagecost)
        d.save(BASE/'CAMPAIGN_COSTS_SNAPSHOT.json',dict(utc=d.now(),stages=stagecost,enclosing_seconds_before_delivery_stage=charged,original_shared_cap_seconds=7200,old_LMB_1073_9382182_unchanged=True,nested_native_worker_clocks_not_added=True))
        text=f'''# S1完整原始扫描轨迹核心：配对三重复结果

实际完成36单元：G/K各六序列各三次，合计73776帧调用。首次R0完整K00按预先约定保留一次，其余35条新计算；失败R0 G不计入精度、其成本完整计入活动账本。所有G每次从原始扫描重新计算E0，不输入旧缓存位姿或资格测试位姿。

{table}

新平均目标通过：{result['primary_passed']}，判据{result['primary']}。逐序列保护通过：{result['safety_passed']}；失败项{', '.join(failures) if failures else '无'}。这些是新的完整raw-core结果，不追溯修改旧G/DMF负结果，也不自动改默认。所有序列均暴露，09完整保留；三次进程重复不是三个独立场景或统计显著性保证。

![完整原始扫描指标](raw_core_metrics.png)

## 实际运行代价

|模式|单元数|完整帧数|完整cell秒数|批处理帧/秒|p95帧ms|p99帧ms|最大帧ms|成功worker峰值bytes|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''
        for m in ('G','K'):
            s=stats[m];text+=f"|{m}|{s['cells']}|{s['frames']}|{s['enclosing_cell_seconds']:.6f}|{s['batch_frames_per_second']:.3f}|{s['frame_seconds']['p95']*1000:.3f}|{s['frame_seconds']['p99']*1000:.3f}|{s['frame_seconds']['maximum']*1000:.3f}|{s['maximum_successful_worker_RSS_bytes']}|\n"
        text+=f'''
![吞吐与尾延迟](raw_core_operations.png)

cell秒数覆盖新解释器启动/导入、原始读盘/哈希、预处理、实际前端、地图/全部闭环、细图、源检查与最小输出。G额外证明输出与K原生细图文件不字节相同，serialization另记；frame时钟不含循环外日志/资源检查，fine含源对应检查。原生CLI的大地图PLY/占据图/可视化副产物对两模式均未执行，不能把这里FPS当完整CLI副产物导出速度。fresh process不是冷文件系统，未清缓存/重启/停止其他任务；第一K早于输入证书阶段，其缓存状态也未声称与其余完全一致。平均吞吐不保证在线10Hz，尾延迟/最终纠正需单独看。包装器/观察器/全部原生进程树峰值没有统一OS级认证。

## 数值输入与验证

R0首次同源码/包配置移植失败，E0矩阵差0.5583>1e-5，保留其不完整和所有失败。原校正的中间dtype随既有NumPy版本变化。S1显式恢复原E0 float32算术，全部12296扫描/1514179545准备点/4542538635坐标分量按帧计数和SHA一致；六条资格轨迹与源E0最大差<=5.73e-11。新G每次仍重算前端、核对准备字节及原1e-5条件，没有改角度/范围/体素/权重/阈值/种子/求解器。地图分支保留原NumPy2校正，K保留原生读取/校正/细图。精度兼容组件可独立复核，不代表所有NumPy/ABI行为普遍相同。

所有36预测先封存，后读GT。独立源/图审计覆盖{audit['source_frame_occurrences']}源帧调用、全部重置区间/粗图边端点/无直接扫描尾节点和G锚点；不使用四舍五入图位姿修复参考。独立Horn/KITTI复核{result['independent_segments']}段，最大差{result['maximum_metric_delta']:.6g}。非线性优化器和完整原始预处理不是独立重写，逐回波体素谱系/物理真实性/训练排除仍未知。

## 成本与边界

R0+S1所有失败、字节证书、前端资格检查、实际运行和验证共用原7200s；交付前累计{charged:.6f}s，当前交付阶段后再追加实际收据，不重复加内部父子clock。原LMB1073.9382182/1800s及其他历史预算不变。4GiB数值Python/256MiB共同dossier/GPU0/原12GiB启动保护保持。

这里增加的是完整原始扫描SLAM轨迹核心的实测对比，不是新RAP算法/增量。历史October11的36次RAP/KISS完整CLI参考未被覆盖，其副产物/成本范围不同。B默认配置、安装环境、生产/模型/参考/论文/Git/外联/调度/目标状态均未改。原科研目标未解决。账户边界单独按实际工具事实记录，不自动重置续跑。
'''
        with (BASE/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
        # Standard unaligned pose exports: all modes, all repeats, all frames.
        export=BASE/'trajectory_exports';export.mkdir()
        for row in rows:
            t=np.load(BASE/'bank04'/row['key']/'poses.npy');p=export/f'{row["key"]}_lidar.txt';np.savetxt(p,t[:,:3,:].reshape(-1,12),fmt='%.17g');assert np.max(abs(np.loadtxt(p).reshape(-1,3,4)-t[:,:3,:]))<=1e-8
        d.save(export/'RESULTS.json',result);d.save(export/'OPERATIONAL_RESULTS.json',d.read(BASE/'OPERATIONAL_RESULTS.json'));d.save(export/'FILE_SHA256.json',dict(files={str(p.relative_to(export)):d.sha(p) for p in export.rglob('*') if p.is_file()}))
        zp=BASE/'raw_core_GK_36_poses_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(export.rglob('*')):
                if p.is_file():z.write(p,arcname=str(p.relative_to(export)))
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for name,h in json.loads(z.read('FILE_SHA256.json'))['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
        d.save(BASE/'STATUS.json',dict(utc=d.now(),status='COMPLETE_RAW_TRAJECTORY_CORE_PAIRED_THREE_REPEATS',primary_passed=result['primary_passed'],safety_passed=result['safety_passed'],old_trials_not_revised=True,default_changed=False,new_RAP_efficacy=False))
        d.save(BASE/'DELIVERY_SEAL.json',dict(utc=d.now(),files={str(p.relative_to(BASE)):d.sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json' and 'supervision' not in p.parts},old_R0_closure_seal_sha256=d.sha(R0/'R0_CLOSURE_SEAL.json')))
        d.cap();ok=True;print('Raw-core delivery complete',means,stats,flush=True)
    except BaseException as e:err=repr(e);traceback.print_exc();d.save(BASE/'FAILURE_delivery.json',dict(utc=d.now(),error=err))
    finally:
        signal.alarm(0);d.save(SUP/'deliver/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0,shared_R0_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='deliver';run()
