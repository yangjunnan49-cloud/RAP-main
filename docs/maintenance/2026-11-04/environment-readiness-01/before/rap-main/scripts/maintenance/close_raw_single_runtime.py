"""Close the failed R0 portability attempt without inventing system metrics."""
import time
START=time.monotonic()
import sys,resource,traceback
from pathlib import Path
import raw_system_integration03 as d
BASE=d.BASE
def run():
    ok=False;err=None
    try:
        d.verify();assert not (BASE/'bank_seal03.json').exists();assert not (BASE/'results03.json').exists()
        rows=[]
        for p in sorted((BASE/'bank03').glob('*/worker_exit.json')):
            row=d.read(p);rows.append(dict(cell=p.parent.name,**row))
        assert len(rows)==2 and sum(x['success'] for x in rows)==1
        costs=[]
        for p in d.SUP.glob('*/child_exit.json'):
            x=d.read(p);vals=[x['wall_seconds']]+[d.read(p.with_name(n))['wall_seconds'] for n in ('exit.json','wrapper_exit.json') if p.with_name(n).exists()]
            costs.append(dict(stage=p.parent.name,success=x['success'],enclosing_seconds=max(vals),peak_RSS_bytes=x['peak_RSS_bytes']))
        charged=sum(x['enclosing_seconds'] for x in costs);assert charged<7200
        d.save(BASE/'R0_STATUS.json',dict(utc=d.now(),status='CLOSED_INCOMPLETE_SINGLE_RUNTIME_FRONTEND_CORRESPONDENCE_FAILED',planned_cells=36,complete_cells=1,failed_cells=1,unlaunched_cells=34,
            GT_numeric_reads=0,new_ATE_or_ter_results=False,old_G_results_unchanged=True,new_runtime_or_tolerance_rescue_in_R0=False))
        d.save(BASE/'R0_COST_SNAPSHOT.json',dict(utc=d.now(),stages=costs,charged_seconds_before_closing=charged,nested_worker_seconds_not_added=True,workers=rows,shared_campaign_cap_seconds=7200,old_LMB_cap_reset=False))
        text=f'''# R0单运行时集成：前端不对应，完整比较未完成

已停止，保留1条成功K00和1条失败G00；36单元计划尚有34条未启动。G00最大矩阵元素差0.5582816188113293>冻结1e-5。没有新ATE/ter、完整系统比较、三重复稳定性结论。旧缓存G六序列结果和所有未通过保护项保持。

预启动时间戳七位小数解析失败在0真实worker时保留，以03格式兼容修复，原2s/12GiB保护未变。真实run03在G00检查失败后停止；其519.9071704s外层时间覆盖K156.042587468s与G361.905888616s，不重复相加。关闭前科学调用累计{charged:.9f}s，后续关闭/证书/工程工作仍计入同一个7200s活动账本，不重置。

两个环境kiss_icp1.3.0 Python源和配置一致，但NumPy分别1.26.4/2.2.6、Python及原生ABI不同。固定合成点库中，原校正源码乘法/和的中间dtype分别float32/float64，9992/30009个最终float32分量不同，max7.62939453125e-6。该观察解释了为何“源码相同”不能保证数值输入相同；它没有单独证明真实0.5583差异的唯一原因。

原G检查发生在序列结束、诊断数组保存之前，故失败G没有可复核的完整O/轨迹数组，只有错误/日志/收据；不补造。后续接口工作须在条件断言前保存新产生诊断数组。K00完整数组/源绑定/图/时间保留；未读取其精度，不按结果挑选它。

S1另行冻结原float32输入算术证书，核对全部12296帧准备点字节，不能追溯改判R0。若后续选择保留原E0完整运行时的双阶段接口，应另行冻结数据契约与来源，所有成本沿用原7200s而非重新给额度。没有调整角度、范围、权重、模型、阈值或参考。没有生产/默认/安装/Git/外联/调度/目标状态变更。
'''
        with (BASE/'R0_REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
        target=BASE/'R0_CLOSURE_SEAL.json';d.save(target,dict(utc=d.now(),files={str(p.relative_to(BASE)):d.sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p!=target and not (p.parent==d.SUP and p.name.startswith('host_latest')) and 'close_r0' not in p.parts}))
        print('R0 closed incomplete; no GT metrics; existing charged',charged,flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:d.save(d.SUP/'close_r0/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='close_r0';run()
