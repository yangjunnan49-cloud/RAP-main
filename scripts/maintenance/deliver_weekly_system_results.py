"""Saved-result visualization, source-bound reporting and finite delivery checks."""
import time
START=time.monotonic()
import json,hashlib,sys,resource,signal,traceback
from pathlib import Path
from datetime import datetime,timezone
MAIN=Path(__file__).resolve().parents[2]
ROOT=MAIN/'docs/maintenance/2026-10-20'
BASE=ROOT/'weekly-system-handoff-01'
DMF=ROOT/'direct-matching-factors-01';LMB=ROOT/'e0-local-map-bundle-01';SIX=ROOT/'e0-local-map-six-01'
SEQS=('00','05','06','07','09','10')
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def write(p,x):
    with Path(p).open('x',encoding='utf-8') as f:f.write(x)
def costs(folder):
    rows=[]
    for p in sorted((folder/'supervision').glob('*/child_exit.json')):
        n=read(p);w=read(p.with_name('exit.json')) if p.with_name('exit.json').exists() else {}
        rows.append(dict(stage=p.parent.name,success=n['success'],error=n.get('error'),native_seconds=n['wall_seconds'],
            enclosing_seconds=max(n['wall_seconds'],w.get('wall_seconds',0)),peak_RSS_bytes=n['peak_RSS_bytes'],windows_exit=w.get('exit_code')))
    return dict(stages=rows,enclosing_seconds=sum(x['enclosing_seconds'] for x in rows),peak_RSS_bytes=max((x['peak_RSS_bytes'] for x in rows),default=0),
        artifact_bytes_before_close=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()),GPU_calls=0,full_native_process_tree_and_observer_peak='UNKNOWN')
def check():
    assert read(DMF/'metric_validation.json')['passed'] and read(LMB/'validation.json')['passed'] and read(SIX/'results.json')['independent_validation_passed']
    assert read(SIX/'results.json')['bank_sealed_before_GT']
    for folder,sealname,bank in ((DMF,'bank_seal.json','bank'),(LMB,'bank_seal.json','bank'),(LMB,'anchor_corrected_seal.json','anchor_corrected_bank'),(SIX,'bank_seal.json','bank')):
        for p,h in read(folder/sealname)['files'].items():assert sha(folder/bank/p)==h,p
    for folder in (DMF,LMB,SIX):
        for p,h in read(folder/'freeze.json')['files'].items():assert sha(p)==h,p
    assert read(SIX/'odometry_control.json')['independent_validation_passed']
    assert read(SIX/'odometry_control.json')['primary_gate_unchanged']==read(SIX/'results.json')['gate']
    for p,h in read(SIX/'ODOMETRY_CONTROL_FREEZE.json')['files'].items():assert sha(p)==h,p
    assert read(SIX/'rotation_control.json')['passed']
    assert read(SIX/'mechanism_audit.json')['primary_gate_unchanged']==read(SIX/'results.json')['gate']
    for n in ('ROTATION_CONTROL_FREEZE.json','MECHANISM_AUDIT_FREEZE.json'):
        for p,h in read(SIX/n)['files'].items():assert sha(p)==h,p
def plot():
    check();import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x=read(SIX/'results.json');colors={'B':'#64748b','KISS':'#d99b26','G':'#16835c'}
    fig,axes=plt.subplots(3,1,figsize=(12,11));ix=np.arange(6);w=.25
    for ax,k,label in zip(axes,('ate','ter','rer'),('Aligned LiDAR ATE (m)','KITTI camera ter (%)','KITTI camera rer (degree / 100 m)')):
        for j,a in enumerate(('B','KISS','G')):
            vals=[x['rows'][s][a][k] for s in SEQS];bars=ax.bar(ix+(j-1)*w,vals,w,color=colors[a],label=a)
            ax.bar_label(bars,fmt='%.3f',padding=2,fontsize=8)
        ax.set_xticks(ix,SEQS);ax.set_ylabel(label);ax.set_ylim(0,max(x['rows'][s][a][k] for s in SEQS for a in colors)*1.19);ax.grid(axis='y',alpha=.17)
        mean=x['gate']['means'];ax.set_title('Six-sequence mean: '+', '.join(f'{a} {mean[a][k]:.6f}' for a in colors),fontsize=11)
    axes[0].legend(frameon=False,ncol=3);axes[-1].set_xlabel('All six exposed development sequences; lower is better')
    fig.suptitle('Fixed E0 + corrected-anchor local-map bundle (G)\nB current E0/RAP; KISS archived three-repeat complete-system mean; G cached-E0 replay',fontsize=12)
    fig.tight_layout(rect=[0,0,1,.945]);fig.savefig(BASE/'six_sequence_comparison.png',dpi=170);plt.close(fig)
    sys.path.insert(0,str(MAIN/'scripts/maintenance'));import validate_scan_level_graph as v
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,s in zip(axes,('00','05')):
        gt=v.load(v.DATA/f'poses/{s}.txt');tr=v.calibration(s);gt=np.linalg.inv(tr)@gt@tr;y=gt[:,:3,3];ax.plot(y[:,0],y[:,1],c='black',lw=1,label='Reference')
        for a in ('B','G'):
            t=np.load(DMF/f'bank/{s}/B.npy') if a=='B' else np.load(LMB/f'anchor_corrected_bank/{s}/G.npy');p=t[:,:3,3];xx=p-p.mean(0);yy=y-y.mean(0)
            u,_,vt=np.linalg.svd(xx.T@yy);d=np.diag([1.,1.,np.linalg.det(vt.T@u.T)]);rot=vt.T@d@u.T;aligned=xx@rot.T+y.mean(0)
            ax.plot(aligned[:,0],aligned[:,1],color=colors[a],lw=.9,label=f"{a}: ATE {x['rows'][s][a]['ate']:.3f}m")
        ax.set_title(f'Sequence {s}: independent rigid alignment per trajectory');ax.set_xlabel('x (m)');ax.set_ylabel('y (m)');ax.axis('equal');ax.legend(frameon=False)
    fig.tight_layout();fig.savefig(BASE/'target_trajectories.png',dpi=170);plt.close(fig)
    save(BASE/'FIGURE_SOURCES.json',dict(utc=now(),files={str(p):sha(p) for p in (Path(__file__),SIX/'results.json',DMF/'bank_seal.json',LMB/'anchor_corrected_seal.json')},scope='Saved validated metrics/arrays only; no solver/model calls'))
def seal(folder):
    target=folder/'DELIVERY_SEAL.json';save(target,dict(utc=now(),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p!=target and not (folder==BASE and 'supervision' in p.parts)}))
def close():
    check();r=read(SIX/'results.json');g=r['gate'];means=g['means'];cr={k:costs(p) for k,p in (('DMF',DMF),('LMB_original',LMB),('LMB_extension',SIX))}
    combined=cr['LMB_original']['enclosing_seconds']+cr['LMB_extension']['enclosing_seconds'];assert combined<=1800 and cr['DMF']['enclosing_seconds']<=1800
    cr['LMB_shared_account']=dict(enclosing_seconds=combined,original_cap_seconds=1800,remaining_seconds=1800-combined,combined_dossier_bytes=sum(cr[k]['artifact_bytes_before_close'] for k in ('LMB_original','LMB_extension')))
    assert cr['LMB_shared_account']['combined_dossier_bytes']<=128*2**20
    save(BASE/'COSTS.json',cr)
    sixstate='COMPLETE_PRIMARY_AND_SAFETY_PASS' if g['deployable'] else ('COMPLETE_PRIMARY_SUCCESS_WITH_INDIVIDUAL_SAFETY_FAILURE' if g['primary_passed'] else 'COMPLETE_PRIMARY_SCREEN_FAILED')
    for folder,state in ((DMF,'COMPLETE_NEGATIVE'),(LMB,'COMPLETE_ORIGINAL_STRICT_CONJUNCTION_FAILED'),(SIX,sixstate)):
        save(folder/'STATUS.json',dict(utc=now(),status=state,numerical_validation_passed=True,latest_complete_raw_system_benchmark='2026-10-11'))
        if (folder/'INCOMPLETE').exists():(folder/'INCOMPLETE').unlink()
    table='|序列|B ATE m|KISS ATE m|G ATE m|B ter %|KISS ter %|G ter %|G rer deg/100m|\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
    for s in SEQS:
        z=r['rows'][s];table+=f"|{s}|{z['B']['ate']:.6f}|{z['KISS']['ate']:.6f}|{z['G']['ate']:.6f}|{z['B']['ter']:.6f}|{z['KISS']['ter']:.6f}|{z['G']['ter']:.6f}|{z['G']['rer']:.6f}|\n"
    table+='|平均|'+ '|'.join(f'{means[a][k]:.6f}' for k,arms in [('ate',('B','KISS','G')),('ter',('B','KISS','G')),('rer',('G',))] for a in arms)+'|\n'
    gain=(1-means['G']['ate']/means['KISS']['ate'])*100;failed=[k for k,v in g['safety'].items() if not v];harms=[s for s,v in g['ATE_harm_over5pct'].items() if v]
    conclusion='新主指标和逐序列保护检查均通过，具备下一次完整原始前端集成验证的依据；尚未改默认配置。' if g['deployable'] else ('G达到用户选定的六序列平均ATE/ter目标，但未通过额外的逐序列保护检查。作为实验性低ATE模式交付，保留B默认配置；不通过参数补救改判。' if g['primary_passed'] else '固定G未通过新的平均主指标，保留B默认配置，停止此构造的参数补救。')
    control=read(SIX/'odometry_control.json');om=control['means']['O'];cm=control['means']['G']
    report=f'''# 2026-10-20 系统推进交付

{conclusion}

用户选定“系统指标与可交付结果”，随后在看到00/05取舍后选定“ATE优先，ter至少不劣于KISS-SLAM”。新的六序列方案在其余四条轨迹生成前单独冻结；原DMF直接因子、原M以及原G对B的严格试验均保留未通过。新方案不追溯改判。原科研目标仍未解决。

## 六序列实际结果

固定同一个G模式处理00/05/06/07/09/10。00/05复用已封存G，其余四条一次生成；没有按真值逐序列选模式。KISS列为October11三个完整重复的逐标量均值。B与G共享固定E0前端，观察/闭环/后端组合不同。

{table}

G相对KISS平均ATE变化：降低{gain:.3f}%。主指标检查：{g['primary']}。逐序列ter/rer保护失败：{', '.join(failed) if failed else '无'}。ATE相对KISS退化超过5%的序列：{', '.join(harms) if harms else '无'}。完整rer和段数保存在六序列results.json。所有六序列均已用于开发，09完整保留；不存在独立泛化验证。

固定E0无闭环O的描述性强对照：六序列平均ATE {om['ate']:.6f}m、ter {om['ter']:.6f}%、rer {om['rer']:.6f}deg/100m；G对应{cm['ate']:.6f}m、{cm['ter']:.6f}%、{cm['rer']:.6f}deg/100m。这里O指原A运行的odom_poses，无闭环但保留+0.205度校正；不是历史文件名O所指的关闭校正变体。每条序列的O/B/G保存在odometry_control.json，独立复核{control['independent_segments']}段。该补充没有生成新预测或修改主判据。

![六序列比较](six_sequence_comparison.png)

![00与05轨迹](target_trajectories.png)

## 得到什么工程证据

DMF0对固定E0、全部24条已接纳00/05闭环比较B位姿约束、Q一次冻结的几何二次式、D反复匹配/线性化的直接几何因子。Q/D初始物理代价、梯度和曲率对齐；保持节点、运动、支持和拓扑。D均值ATE2.029163m，对照B2.024568m，ter/rer亦未满足冻结联合判据。结论是这个具体直接因子构造的完整负结果；没有权重/点数/半径补救，也不推广为所有直接因子不可能。详见DMF REPORT。

LMB0改变观察单元，采用已有KISS局部地图检索/几何/图优化组合，保持E0每帧运动输入。原M把00/05 ATE从2.754437/1.294699m降到0.887839/0.359070m，但00 ter相对B从0.518171%增至0.571054%，原严格判据失败。没有把低ATE改写成原试验通过。

另一个可复现的工程发现是细图没有保持实际粗图锚点。已知三地图锚点x=0/3.3/6.0，原生细图得到0/3.1/6.2。隔离修正G固定实际源帧锚点；解析平移、无操作、共同世界变换检查通过，真实地图体重建及锚点保持通过。G00/05 ATE0.887368/0.359419m、ter0.573657/0.321078%。原00 ter退化在细图前已存在，不能归因于该契约问题；修正也未使原对B判据通过。未改动已安装库或生产源码。

追加的非交换相对旋转检查通过：12帧无操作、相邻运动和共同世界变换最大误差分别5.89e-15、8.44e-15、1.07e-14。原平移夹具的共同世界旋转不等于验证了非平凡相对旋转；这次补充明确覆盖该缺口。

完整描述性审计覆盖全部20条地图闭环及每条序列全部有效官方段长，没有筛边或重求解。09/10零闭环时G与无闭环O的矩阵差仅1.77e-12/1.36e-12；10的rer保护失败来自共享前端相对KISS的既有差异。07唯一闭环连接源帧0/1048，测量相对参考误差0.300312m/0.284780度，优于未闭环O的0.734922m/0.684141度；但G在所有有效段长的平均ter均比O更高。这里是全局闭合与局部漂移的取舍，不是“明显错误闭环”的证明，也不支持新的拒绝阈值。详见MECHANISM_REPORT和完整mechanism_audit.json。

G的六序列意义是普通系统工程组合，不是RAP增量。局部地图支持、检索、接纳、节点尺度和后端联合变化，不能单独归因。保存逐地图直接帧成员、重置锚点、每次闭环查询和原始哈希；原生体素继承仅有保守源前缀，缺少逐回波谱系。已冻结选定Python/pybind源和版本，不认证全部传递原生库/物理真值/训练排除。

## 验证与资源

预测封存先于数值真值读取。DMF的独立暴力邻居/代数审计和Horn/KITTI指标通过；原LMB指标独立复核10178段，新的六序列B/G复核{r['independent_segments']}段，最大差{r['maximum_metric_delta']:.6g}。不是独立重写非线性求解器或完整原始预处理。

DMF首个验证器在重复文件系统保护检查上耗时过长，保留1002.0574736s中断记录、原源码/失败及修复等价检查。只变更保护检查频率的02验证器通过；两次和诊断都计入原1800s。DMF累计{cr['DMF']['enclosing_seconds']:.6f}s。LMB原试验、诊断、契约控制、G修正与四序列扩展共用原1800s，现累计{combined:.6f}s，余额{1800-combined:.6f}s。重叠父子时钟不相加。GPU调用0，原12GiB启动保护保留；参与Python进程峰值、逐阶段成本及文件体积见COSTS。观察器/启动/全部原生进程树峰值未知。

这次G重放使用缓存E0，没有重新运行整个原始前端，所以不能把地图耗时当完整系统速度；最新完整原始系统36次基准仍为October11。没有生产/默认/模型/参考/论文变更，没有安装、外联、Git变更、调度或目标状态操作。

## 下一步边界

{conclusion} 下一次工作必须围绕这里的完整六序列结论另行冻结强对照与资源，不按单条序列换模式，不重开历史停止族。若条件合格，完整原始前端集成和实际速度/内存是下一项可交付；若保护失败，先解释已保存观察和图的具体差异，不启动阈值、权重或点数搜索。

账户事实单独记录于ACCOUNT_FINAL.json及可能的后续ACCOUNT_STOP补充。低于100%的读数不代表耗尽，旧95%窗口也未观察到耗尽。无自动额度重置续跑。历史停止、封印及用户拒绝外联保持。
'''
    write(BASE/'REPORT.md',report)
    write(SIX/'REPORT.md',f'# Fixed-G six-sequence result\n\nPrimary passed: {g["primary_passed"]}. Safety passed: {g["safety_passed"]}. Promotion screen: {g["deployable"]}.\n\n'+table+'\n'+conclusion+'\n\nSee ../weekly-system-handoff-01/REPORT.md for source, validation, cost and interpretation. Original two-sequence failures remain.\n')
    write(LMB/'ANCHOR_COMPLETION.md','# Anchor correction completion supplement\n\nThe original REPORT predates real G evaluation. Sealed real G and independent metrics are now complete in anchor_results.json. All coarse anchors are preserved. G00/05 ATE0.887367688/0.359419080m, ter0.573656906/0.321078441%. The original strict conjunction remains FAILED. The later explicit owner objective admits only the separately frozen six-sequence comparison, not the old conditional plan. See ../e0-local-map-six-01 and ../weekly-system-handoff-01/REPORT.md.\n')
    write(BASE/'START_HERE.md','# 本轮交付入口\n\n先读 REPORT.md：六序列完整指标、两个负结果、锚点契约修正和下一步边界。COSTS.json给出不重置的原预算。新指标只适用于新的前瞻六序列方案，旧试验未通过保持。所有图来自封存预测和已独立验证的指标。完整原始系统基准仍为October11。账户边界见单独记录；原科研目标未完成。\n')
    save(BASE/'CLOSURE_SOURCES.json',dict(utc=now(),sources={str(p):sha(p) for p in [Path(__file__),MAIN/'scripts/maintenance/e0_local_map_six.py',SIX/'PROTOCOL.md',SIX/'OWNER_SCOPE.md',SIX/'results.json',LMB/'anchor_results.json',DMF/'metric_validation.json']}))
    entry=f'October20 system advance COMPLETE: owner prioritized system deliverables then explicitly ATE-first/ter-nonworse-than-KISS. DMF0 fixed direct-factor screen negative; original LMB M/G strict-against-B screens remain failed. Source-frame coarse-anchor contract correction passes synthetic/real checks; isolated fixed G six-sequence comparison primary={g["primary_passed"]}, safety={g["safety_passed"]}. G/KISS mean ATE {means["G"]["ate"]:.9f}/{means["KISS"]["ate"]:.9f}m, ter {means["G"]["ter"]:.9f}/{means["KISS"]["ter"]:.9f}%. Read docs/maintenance/2026-10-20/weekly-system-handoff-01/START_HERE.md and REPORT/COSTS for full per-sequence tradeoffs/decision. All6 exposed/09 retained; cached-E0 replay, no new complete raw-system benchmark or RAP increment. Latest full raw benchmark staysOct11. Original1800s LMB cap shared with extension, no reset; failures/seals/stops/source limits/outreach decline preserved. No production/default/library/Git/goal-status/scheduler change; original research goal unresolved. Account boundary recorded separately, no automatic reset resume.'
    p=MAIN/'AGENTS.md';old=p.read_bytes();cut=old.index(b'\n')+1;insert=b'\n'+entry.encode()+b'\n';new=old[:cut]+insert+old[cut:];p.write_bytes(new)
    phase=ROOT/'PHASE_RECORD.md';previous=phase.read_bytes();phase.write_bytes(previous+('\n\n# October20 system engineering advance\n\n'+entry+'\n').encode())
    save(BASE/'HANDOFF_UPDATE_CHECKS.json',dict(utc=now(),old_AGENTS_sha256=hashlib.sha256(old).hexdigest(),new_AGENTS_sha256=sha(p),old_AGENTS_body_preserved=new[cut+len(insert):]==old[cut:],old_phase_prefix_preserved=phase.read_bytes().startswith(previous)))
    for folder in (DMF,LMB,SIX,BASE):seal(folder)
    print('Finite delivery completed; primary',g['primary_passed'],'safety',g['safety_passed'],'LMB combined',combined,flush=True)
def run(stage):
    used=sum(max(read(p)['wall_seconds'],read(p.with_name('exit.json'))['wall_seconds'] if p.with_name('exit.json').exists() else 0) for p in (BASE/'supervision').glob('*/child_exit.json'))
    left=300-used;assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('delivery300s cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        {'plot_final':plot,'close_final':close}[stage]();assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=64*2**20;ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:
        signal.alarm(0);save(BASE/'supervision'/stage/'child_exit.json',dict(utc=now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':run(sys.argv[1])
