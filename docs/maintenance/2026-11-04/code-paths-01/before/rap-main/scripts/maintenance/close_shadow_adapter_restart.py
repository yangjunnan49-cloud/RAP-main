"""SR1 standard-library final identity/resource/result closure."""
import hashlib,json,resource,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-25/shadow-adapter-restart-01'
START=time.monotonic()


def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def now():return datetime.now(timezone.utc).isoformat()
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')


f=read(BASE/'freeze.json');result=read(BASE/'results.json');validation=read(BASE/'validation.json')
fit=read(BASE/'fits/execution.json');backward=read(BASE/'backward/execution.json')
assert validation['passed'] and validation['complete_paired_traces']==51
assert validation['independent_Horn_part_fits']==765 and validation['sha256_files_checked']==357
assert not validation['conditional_noise_conjunction'] and fit['actual_retained_updates']==40
assert backward['passed'] and backward['backwards']==2 and backward['actual_retained_updates']==0
for q,h in f['files'].items():assert sha(q)==h,q
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
old=ROOT/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01'
assert (old/'INCOMPLETE').exists() and read(old/'FAILURE_predict.json')['artifact_bytes']==2156270857
for q in [ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',
    ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',
    ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE']:assert q.exists()

stages=['freeze','preflight','backward','fit','validate_fit','predict_resume',
    'evaluate_U','evaluate_V','evaluate_P','summarize']
receipts=[]
for stage in stages:
    child=read(BASE/'supervision'/stage/'child_exit.json')
    assert child['success'] and child['full_resource_capture'] and child['optimizer_calls']==0
    assert child['peak_RSS_bytes']<=6*2**30
    assert max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=8*2**30
    receipts.append(dict(stage=stage,child=child))
interrupted=[dict(stage='predict',outer_wall_seconds=300,child_exit=False,output_admitted=False),
    dict(stage='evaluate',attempt=1,outer_wall_seconds=300,child_exit=False,output_admitted=False),
    dict(stage='evaluate',attempt=2,outer_wall_seconds=300,child_exit=False,output_admitted=False)]
seconds=sum(x['child']['wall_seconds'] for x in receipts)+sum(x['outer_wall_seconds'] for x in interrupted)
assert seconds<1800
rss=max(x['child']['peak_RSS_bytes'] for x in receipts)
ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts)
gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
artifact=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file());assert artifact<=4*2**30
host_rows=[]
for q in (BASE/'supervision').glob('*/host_memory.jsonl'):
    host_rows += [json.loads(x) for x in q.read_text().splitlines() if x.strip()]
min_headroom=min(x['headroom_bytes'] for x in host_rows);assert min_headroom>=4*2**30
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),
    repositories=repos,old_markers_preserved=True,old_HFIT0_failure_unchanged=True,
    prediction_files_sha256_checked=357))
resource_audit=dict(passed=True,successful_scientific_children=len(receipts),
    interrupted_outer_attempts=interrupted,combined_seconds_including_interruptions=seconds,
    successful_child_seconds=sum(x['child']['wall_seconds'] for x in receipts),
    peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,
    artifact_bytes=artifact,artifact_cap_bytes=4*2**30,
    minimum_observed_host_headroom_bytes=min_headroom,host_memory_observations=len(host_rows),
    receipts=receipts,imports_included=True,early_null_shell_exit_records_preserved=True,
    prediction_recovery='42 existing complete cases retained; exactly 9 missing P cases generated',
    old_caps_and_failures_preserved=True)
save(BASE/'RESOURCE_AUDIT.json',resource_audit)
status=dict(utc=now(),status='VALIDATED_SHADOW_RESTART_COMPLETE_NO_MATERIAL_NOISE_CONJUNCTION',
    model_load_and_backward=True,fit_feasibility=True,complete_noise_comparison=True,
    conditional_noise_conjunction=False,actual_retained_updates=40,optimizer_API_calls=0,
    original_native_equivalence=False,real_or_system_gain_claim=False,old_HFIT0='INCOMPLETE')
save(BASE/'STATUS.json',status)
save(BASE/'CHECKS.json',dict(passed=True,model_preflight=True,backward_replay=True,
    fit_validation=True,complete_prediction_bank=True,independent_evaluation=True,
    conditional_noise_conjunction=False,old_failures_preserved=True,
    resource_caps_pass=True,partial_metrics_used=False))

lines=['# SR1 双精度影子 adapter 重启与完整噪声对照','',
    '**结论：模型加载、双精度反向和训练损失下降全部通过；完整 16 噪声对照未形成实质性增益。**','',
    '本实验是独立的合成影子函数验证，不是原始 native/AdamW 路径修复，也不证明新噪声、新场景、真实 SLAM 或物理泛化。旧 NOC4、HFIT0、RLP2、BRF0 失败与边界均保留。','',
    '## 模型与反向','',
    '- 两个独立模型均以 `weights_only=True` 严格加载，每个 344 个检查点张量匹配；443,904 个可训练值完成 float64 提升。',
    '- fit00/eval00 初始五步采样与 SAR0 逐字节一致；V/P 初始梯度与 DTC0 逐元素一致，全部为有限 float64，反向后参数未改变。',
    '- 初始 B=0 时 A 梯度为 0，B/MLP 梯度非零，符合结构预期。','',
    '## 小规模训练','',
    '| 臂 | 初始 loss | 20 次更新后 | 相对下降 | Armijo 通过 |','|---|---:|---:|---:|---:|']
for arm in ('V','P'):
    rows=[x for x in fit['records'] if x['arm']==arm];before=rows[0]['loss_before'];after=rows[-1]['loss_after']
    lines.append(f"| {arm} | {before:.12g} | {after:.12g} | {100*(before-after)/before:.6f}% | {sum(x['Armijo_pass'] for x in rows)}/20 |")
lines += ['', '40 次保留更新的参数数组、梯度、更新规则、损失项、局部 A/B 导数和 Armijo 条件均独立复核通过；优化器 API 调用为 0。','',
    '## 完整噪声对照','',
    'U/V20/P20 在 fit00 与全部 16 个既有 eval 噪声上的 51 例预测全部完成并先封存后评估。独立审计覆盖 357 个预测文件 SHA256、765 次 Horn 部件拟合及全部递推/精度转换关系。fit00 仅作诊断，不计入 16 噪声门禁。','',
    '| 臂/部件 | 基线均值 t (m) | 训练后均值 t (m) | 基线均值 R (deg) | 训练后均值 R (deg) | 联合不恶化/16 | 结果 |','|---|---:|---:|---:|---:|---:|---|']
for c in result['summary']['cells']:
    lines.append(f"| {c['arm']}/part{c['part']} | {c['B']['t']['mean']:.9g} | {c['A']['t']['mean']:.9g} | {c['B']['R']['mean']:.9g} | {c['A']['R']['mean']:.9g} | {c['joint_nonworse']} | 未通过 |")
lines += ['', '四个单元全部未通过：均值平移改善仅约 9–26 微米，未达到 10% 均值比或 5 mm 中位数增益；联合不恶化仅 3–5/16，低于要求的 12/16。完整结论为 `BOUNDED_SHADOW_FIT_COMPLETE_NO_SAFE_MATERIAL_NOISE_CONJUNCTION`，不进行步长、更新数、噪声或阈值补救。','',
    '## 中断与恢复','',
    '预测首次被外层 300 秒限制中断于 42 例；保留现场并固定已有文件哈希后，仅补齐缺少的 9 例 P。完整评估两次被外层 300 秒限制中断且无任何指标输出；随后按固定 U/V/P 臂分块，使用相同递推、Horn、位姿和门禁公式完成全量审计。早期三条 Windows 外壳空退出码记录同样保留；所有数值阶段均有成功子进程收据。未使用任何部分指标。','',
    '## 资源','',
    f"- 成功科学子进程 {len(receipts)} 个；成功子进程合计 {resource_audit['successful_child_seconds']:.6f} 秒，计入三次外部中断后保守合计 {seconds:.6f}/1800 秒。",
    f"- 峰值 RSS {rss} 字节（{rss/2**30:.3f} GiB）；GPU 分配/预留峰值 {ga}/{gr} 字节（{ga/2**30:.3f}/{gr/2**30:.3f} GiB），限额 8 GiB。",
    f"- 新档案 {artifact} 字节（{artifact/2**30:.3f} GiB）/4 GiB；旧 HFIT0 的 2 GiB 上限及失败不变。",
    f"- 主机提交内存最小观测余量 {min_headroom} 字节（{min_headroom/2**30:.3f} GiB）。",'',
    '本结果只支持“该双精度影子函数可在固定合成任务上拟合，但这次 20 次更新未获得安全的条件噪声收益”。研究原目标仍未解决，不据此恢复论文写作或真实场景扩展。']
(BASE/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(BASE/'NEXT_PLAN.md').write_text('# 后续边界\n\n本次固定 20 次更新/fit00/双精度影子策略已完成，噪声总门禁为负面。不得在同一证据上通过调步长、加更新、选噪声或改阈值宣称修复；不自动扩展到真实场景。任何后续工作需提出不同的科学假设和新的前瞻性对照协议。原始研究与论文状态不变。\n',encoding='utf-8')
assert (BASE/'INCOMPLETE').exists();(BASE/'INCOMPLETE').unlink()
save(BASE/'BOOKKEEPING.json',dict(utc=now(),standard_library_only=True,no_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()]
save(BASE/'DELIVERY_SEAL.json',dict(utc=now(),status=status['status'],decision=result['decision'],files=files,entries=len(files)))
print(json.dumps(dict(status=status['status'],deliveries=len(files),seconds=seconds,RSS=rss,
    GPU_allocated=ga,GPU_reserved=gr,artifact=artifact),indent=2))
