"""Render the completed controlled mechanism comparison without new queries."""
import csv,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());x=read(R/'results/RESULTS.json');v=read(R/'INDEPENDENT_CHECKS.json');sup=read(R/'real-supervision.json')
rows=[]
for row in x['cases']:
 e=next(z for z in v['cases'] if z['case']==row['case'])
 for cand in row['candidates']:
  for d in ['forward','reverse']:rows.append(dict(case=row['case'],group=e['group'],density=e['density'],expected=e['expected'],candidate=cand['index'],direction=d,**{k:cand[d][k] for k in ['nn_mean','plane_huber','block_score','source_count','gate_count','mutual_count','normal_median_deg']}))
with (R/'SCORES.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
methods=['plane_huber','nn_mean','block_score'];names=['Inlier plane mean','All-source NN mean','Spatial block prototype']
fig,axs=plt.subplots(1,2,figsize=(10.8,4.8),layout='constrained',gridspec_kw={'width_ratios':[1,1.55]})
correct=[v['summary'][m]['identified_correct'] for m in methods];abstain=[v['summary'][m]['abstained'] for m in methods]
axs[0].barh(np.arange(3),correct,color='#167d9a',label='Identified true candidate');axs[0].barh(np.arange(3),abstain,left=correct,color='#dce4e8',label='Abstained')
axs[0].set_yticks(np.arange(3),names,fontsize=9);axs[0].set(xlim=(0,8),xlabel='Controlled cases',title='No gain over the strong NN baseline');axs[0].legend(loc='lower left',fontsize=8)
arr=np.array([[1 if e['methods'][m]['label']=='identified_correct' else 0 if e['methods'][m]['label']=='abstained' else 2 for m in methods] for e in v['cases']])
axs[1].imshow(arr,cmap=ListedColormap(['#dce4e8','#167d9a','#c04d49']),vmin=0,vmax=2,aspect='auto')
for i in range(8):
 for j in range(3):axs[1].text(j,i,'true' if arr[i,j]==1 else 'abstain',ha='center',va='center',color='white' if arr[i,j]==1 else '#233842',fontsize=9)
axs[1].set_xticks(np.arange(3),['Plane','NN','Block']);axs[1].set_yticks(np.arange(8),[e['group'].replace('_',' ')+' / '+e['density'] for e in v['cases']],fontsize=9)
axs[1].set_title('Four identifiable and four source-ambiguous controls')
fig.suptitle('DPA4: stop this spatial block recipe',fontsize=14);fig.supxlabel('Analytic mechanism tests only; no real-data accuracy or method promotion.',fontsize=10)
fig.savefig(R/'mechanism_comparison.png',dpi=170);fig.savefig(R/'mechanism_comparison.svg');plt.close(fig)
p=R/'mechanism_comparison.svg';(R/'mechanism_comparison.clean.svg').write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
lines=['# DPA4受控结构试验与停止决策','','2026-11-10，Asia/Shanghai。用户授权继续决策与执行、更新交接并一次提交和推送。本阶段实际执行完成；研究 **UNRESOLVED**，论文 **PAUSED**，没有真实数据准确率或新方法晋升。','',
'## 决策','','**停止本次空间分块支持配方，不进入真实数据扩展。** 8个固定受控例中，空间分块原型与普通最近点全源均距基线均为4例正确区分、4例弃权、0错误/歧义强判；没有强几何以上的新增可辨识例。点到面内点均值只有2例正确区分、6例弃权，原型多出的2例只是击败较弱基线，不能当创新或RAP增量。','',
'完全重复和源锚点缺失的4例在全部主机制中均弃权，符合当前仅使用源可见几何的部分重叠合同。目标中的额外未观测结构不作负证据；反向统计没有用于选择。因此这里的“观测等价”限于规定的源可见证据，不是已建立传感器视锥/射线模型。','',
'可见唯一锚点的2例中，别名候选仍匹配重复核心，其锚点距离超过.75m而被点到面内点支持丢弃，导致内点均值无法区分；普通全源NN已保留该证据并区分，分块没有新信息。不由此认证互惠/法线/谱安全，也不据控制结果调整真实阈值。','',
'优化探索在此收束：DPA1–3发现局部目标锚定/结构身份局限，DPA4未给出强基线以上的新机制。不再换尺度、阈值、样本或重复构造救活此配方；后续科研需要不同且可独立验证的观测/结构证据。项目下一可执行重点为梳理和集成验收既有22份未提交工程修改，先交付可复核的工程基线，避免把机制负结果包装成科学进展。具体范围见NEXT_ENGINEERING_REVIEW.md，仅后续计划，本轮未改生产代码或开启训练。','',
'## 实验与验证','','输入为纯解析3正交面片、重复单元及可见/缺失锚点，8例、每例2固定候选。均匀与源y面重复采样形成密度不均对照，重复采样不增加独立物理点。真实变换、物理点ID及组别仅给事后评价器，几何scorer只读取a/b/na/nb/candidates，未读评价身份。候选顺序和点顺序seed311固定打乱。','',
f"生成8个输入共27,983字节；真实执行32次静态NN、墙钟{sup['wall_s']:.3f}秒、峰值RSS约{sup['observed_peak_RSS_bytes']/2**20:.1f}MiB、结果{sup['final_output_bytes']:,}字节。0KITTI/raw/真实NPZ读取、RAP/ICP/训练/优化更新/生产改动。CPU单线程/CUDA不可见，AS≤2GiB−64MiB、CPU25秒/墙钟30秒、输出≤4MiB。",
'', '9项合成预检、4类资源负例、独立96项分数、32组保存距离、28组Gram谱及8例物理身份核查通过。独立核查不追加NN；最近点实现只在合成小例与穷举距离核对。无意外运行失败，预期预算负例保留。所有生成器、打分器、评价器、输入和规则在真实执行前冻结，未调参或补例。','',
'## 全部选择结果','','![机制对照](mechanism_comparison.png)','','主选择均只用前向源可见几何；None为稳定带内无法区分/弃权。数值带不是安全接纳门槛。','','| 例 | 结构/密度 | 预期 | 真候选索引 | 点到面 | NN强基线 | 分块 |','| --- | --- | --- | ---: | --- | --- | --- |']
for e in v['cases']:
 labels=[e['methods'][m]['label'] for m in methods]
 lines.append(f"| {e['case']} | {e['group']} / {e['density']} | {e['expected']} | {e['physical_true_index']} | {' | '.join(labels)} |")
lines+=['','## 全部前向原始分数','','完整双向32组记录见SCORES.csv和results/RESULTS.json；下表保留全部16个候选前向分数与支持，不删掉锚点缺失或密度变体。单位NN为m、Huber为m²，分块为无量纲，不跨指标比较绝对值。','','| 例 | 候选 | NN均距 | 内点Huber均值 | 分块 | 内点/源数 | 互惠 |','| --- | ---: | ---: | --- | ---: | --- | ---: |']
for row in x['cases']:
 for c in row['candidates']:
  d=c['forward'];plane='null' if d['plane_huber'] is None else f"{d['plane_huber']:.10g}"
  lines.append(f"| {row['case']} | {c['index']} | {d['nn_mean']:.10g} | {plane} | {d['block_score']:.10g} | {d['gate_count']}/{d['source_count']} | {d['mutual_count']} |")
lines+=['','## 交接、保全与发布范围','','原8入口先备份，22生产文件原字节保持，DPA1–3及9旧seal/115登记核验不改。真实来源/处理版本/物理参考未知、训练未准入、03开发暴露、SSC1/PGC1停止/七份部分准确率未解释读取、official MAC未运行保持。纯解析控制不是训练包，不修复真实来源缺口。','',
'本轮仅一次聚焦RAP-main提交本目录和docs/experiments/DPA4.md；已有生产修改与聚合导航继续保留未提交，提交中after/存日期快照。推送指定origin/chore/autodl-history-20261107，初始远端12f72996…，快进包含此前DPA2和DPA3已提交历史及本轮提交，不强推、不修改另一仓库远端。提交/推送实际hash收据在阶段外保存，避免第二次提交自引用。','',
'主入口HANDOFF_CN.md；计算/预检/评价脚本、独立结果、所有源输入、冻结/监督收据及SCORES.csv均在本目录。CLOSEOUT_CHECKS记录科学/生产保全，PRECOMMIT_CHECKS记录提交审阅，ARTIFACT_MANIFEST记录精确产物字节。原SVG字节保留，clean.svg只去行尾空格。','']
(R/'REPORT_CN.md').write_text('\n'.join(lines));print('Built DPA4 report, full score CSV and mechanism comparison figure')
